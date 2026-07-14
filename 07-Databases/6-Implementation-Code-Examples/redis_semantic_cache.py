"""
redis_semantic_cache.py
A semantic cache for LLM responses backed by Redis.

WHY this file:
    Exact-match caches are useless for LLM prompts because users paraphrase
    endlessly ("reset my password" vs "I forgot my password"). A *semantic*
    cache keys on MEANING: embed the query, find the nearest previously-cached
    query, and reuse its answer only if similarity clears a threshold. That
    turns a multi-second, paid model call into a ~ms lookup.

Design decisions demonstrated:
    - Two-tier: an exact-hash tier (free, instant) in front of the semantic tier.
    - Similarity THRESHOLD as the core correctness knob (too loose = wrong
      answers served; too tight = low hit rate).
    - Per-tenant/context scoping so "what's my balance?" is never shared.
    - TTL for freshness. A vector match is only a CANDIDATE until the threshold
      approves reuse -- and we only count a "hit" (avoided model call) then.

Prereqs:
    - A running Redis 7+ (this demo uses plain string keys + a small scan, which
      is fine to illustrate the logic; at scale use Redis Query Engine / a vector
      index so nearest-neighbor search is O(log n), not O(n)).
    - pip install redis numpy
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass

import numpy as np
import redis

EMBED_DIM = 256
SIMILARITY_THRESHOLD = 0.92   # tune on real traffic; higher = safer, fewer hits
TTL_SECONDS = 3600            # freshness bound; also event-invalidate on updates


def embed(text: str) -> np.ndarray:
    """Deterministic placeholder embedding (see pgvector_rag.py for the why)."""
    seed = int.from_bytes(hashlib.sha256(text.lower().encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(EMBED_DIM).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-12)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    # Both vectors are unit-length, so the dot product IS the cosine similarity.
    return float(np.dot(a, b))


@dataclass
class CacheResult:
    answer: str
    kind: str        # "exact", "semantic", or "miss"
    similarity: float


class SemanticCache:
    def __init__(self, client: redis.Redis, tenant: str):
        self.r = client
        # WHY scope by tenant: prevents leaking one user's answer to another and
        # keeps the per-tenant candidate set small.
        self.ns = f"semcache:{tenant}"

    # --- exact tier -------------------------------------------------------
    def _exact_key(self, query: str) -> str:
        h = hashlib.sha256(query.strip().lower().encode()).hexdigest()
        return f"{self.ns}:exact:{h}"

    # --- semantic tier ----------------------------------------------------
    def _entry_key(self, h: str) -> str:
        return f"{self.ns}:entry:{h}"

    def get(self, query: str) -> CacheResult:
        # Tier 1: exact hash. Free and instant -- handles repeated identical prompts.
        exact = self.r.get(self._exact_key(query))
        if exact is not None:
            return CacheResult(exact.decode(), "exact", 1.0)

        # Tier 2: semantic. Embed and compare against stored entries.
        q = embed(query)
        best_sim, best_answer = -1.0, None
        # NOTE: linear scan for clarity. Replace with a Redis vector index
        # (FT.SEARCH KNN) in production for sub-linear search.
        for key in self.r.scan_iter(match=f"{self.ns}:entry:*"):
            raw = self.r.get(key)
            if not raw:
                continue
            entry = json.loads(raw)
            sim = cosine(q, np.array(entry["embedding"], dtype=np.float32))
            if sim > best_sim:
                best_sim, best_answer = sim, entry["answer"]

        # The threshold decides: a nearby vector is only a candidate until now.
        if best_answer is not None and best_sim >= SIMILARITY_THRESHOLD:
            return CacheResult(best_answer, "semantic", best_sim)
        return CacheResult("", "miss", best_sim)

    def put(self, query: str, answer: str) -> None:
        """Store after the LLM has generated (and ideally you've guardrailed) it.

        WHY store both tiers: the exact key makes identical repeats free; the
        semantic entry makes paraphrases cheap. Both carry a TTL for freshness.
        """
        q = embed(query)
        h = hashlib.sha256(query.strip().lower().encode()).hexdigest()
        self.r.set(self._exact_key(query), answer, ex=TTL_SECONDS)
        self.r.set(
            self._entry_key(h),
            json.dumps({"query": query, "answer": answer, "embedding": q.tolist()}),
            ex=TTL_SECONDS,
        )


def answer_query(cache: SemanticCache, query: str) -> str:
    """Cache-aside flow around a (simulated) expensive LLM call."""
    hit = cache.get(query)
    if hit.kind != "miss":
        print(f"  cache {hit.kind} (sim={hit.similarity:.3f}) -> no model call")
        return hit.answer

    # --- cache miss: this is where the real, paid LLM call would happen ---
    print(f"  cache miss (best sim={hit.similarity:.3f}) -> calling model...")
    time.sleep(0.2)  # stand-in for model latency
    generated = "You can reset your password from Settings > Security."
    cache.put(query, generated)  # only cache validated answers
    return generated


if __name__ == "__main__":
    client = redis.Redis()  # localhost:6379 by default
    cache = SemanticCache(client, tenant="acme")

    print("Q1:", answer_query(cache, "How do I reset my password?"))
    # Paraphrase -> should hit the semantic tier, skipping the model.
    print("Q2:", answer_query(cache, "I forgot my password, how can I change it?"))
    # Identical -> exact tier.
    print("Q3:", answer_query(cache, "How do I reset my password?"))
