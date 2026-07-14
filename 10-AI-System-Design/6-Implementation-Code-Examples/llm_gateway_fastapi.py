"""
llm_gateway_fastapi.py
=======================
A *minimal, illustrative* LLM gateway showing the four things every real gateway
does, and the four things interviewers want to hear about:

    1. ROUTING      - send easy requests to a cheap/small model, hard ones to a
                      large model (a "cascade"). This is the biggest cost lever.
    2. CACHING      - exact-match cache (identical prompt) + semantic cache
                      (embedding-similar prompt). Repetitive traffic is free.
    3. FALLBACK     - if the primary model errors/times out, try a fallback so a
                      single provider outage doesn't take you down.
    4. GOVERNANCE   - per-tenant rate limiting + token budgets so one caller
                      can't starve others or run up a huge bill.

The model + embedding calls are MOCKED so this file is self-contained (no API
keys). Swap `mock_model_call` / `mock_embed` for a real SDK to go live.

Run:  uvicorn llm_gateway_fastapi:app --reload
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Illustrative LLM Gateway")


# ---------------------------------------------------------------------------
# 1. MODEL REGISTRY
# ---------------------------------------------------------------------------
# WHY: We describe each model by *price* and *capability tier* so the router can
# make a cost/quality decision. Prices are per 1M tokens (illustrative numbers).
@dataclass(frozen=True)
class Model:
    name: str
    price_in: float   # $ / 1M input tokens
    price_out: float  # $ / 1M output tokens
    tier: str         # "small" or "large"


SMALL = Model("small-fast", price_in=0.15, price_out=0.60, tier="small")
LARGE = Model("large-quality", price_in=2.50, price_out=10.00, tier="large")
FALLBACK = Model("fallback-provider", price_in=3.00, price_out=12.00, tier="large")


# ---------------------------------------------------------------------------
# 2. MOCKED PROVIDER CALLS
# ---------------------------------------------------------------------------
# WHY mocked: keeps the teaching example runnable offline. The *shape* (it can
# raise, it returns text + token counts) is what matters for the gateway logic.
_FAIL_ONCE = {"tripped": False}


def mock_model_call(model: Model, prompt: str, force_fail: bool = False) -> dict:
    if force_fail:
        # Simulate a provider outage / timeout to demonstrate fallback.
        raise RuntimeError(f"{model.name} unavailable")
    # Fake token accounting: ~1 token per 4 chars is a common rule of thumb.
    in_tokens = max(1, len(prompt) // 4)
    out_text = f"[{model.name}] answer to: {prompt[:60]}"
    out_tokens = max(1, len(out_text) // 4)
    return {"text": out_text, "in_tokens": in_tokens, "out_tokens": out_tokens}


def mock_embed(text: str, dim: int = 64) -> list[float]:
    # Deterministic pseudo-embedding from a hash so "similar" strings that share
    # a prefix land near each other. Real systems use an embedding model.
    h = hashlib.sha256(text.lower().strip().encode()).digest()
    vec = [(b / 255.0) for b in h[:dim]]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# 3. CACHING (exact + semantic)
# ---------------------------------------------------------------------------
# WHY two layers: exact cache is O(1) and free; semantic cache catches
# paraphrases ("reset password" vs "how do I change my password"). Both cut
# cost AND latency on repetitive traffic where 30-50% hit rates are common.
#
# IMPORTANT (security): caches are keyed *per tenant* so one tenant can never
# read another tenant's cached answer. This is a real interview gotcha.
@dataclass
class CacheEntry:
    prompt: str
    embedding: list[float]
    response: dict


class TenantCache:
    def __init__(self, semantic_threshold: float = 0.97):
        self._exact: dict[str, dict] = {}
        self._semantic: list[CacheEntry] = []
        self.threshold = semantic_threshold

    def get(self, prompt: str, embedding: list[float]) -> Optional[dict]:
        key = hashlib.sha256(prompt.encode()).hexdigest()
        if key in self._exact:
            return {"source": "exact-cache", **self._exact[key]}
        # Semantic lookup: return the closest entry above the threshold.
        best, best_sim = None, 0.0
        for entry in self._semantic:
            sim = cosine(embedding, entry.embedding)
            if sim > best_sim:
                best, best_sim = entry, sim
        if best and best_sim >= self.threshold:
            return {"source": f"semantic-cache(sim={best_sim:.3f})", **best.response}
        return None

    def put(self, prompt: str, embedding: list[float], response: dict) -> None:
        key = hashlib.sha256(prompt.encode()).hexdigest()
        self._exact[key] = response
        self._semantic.append(CacheEntry(prompt, embedding, response))


# ---------------------------------------------------------------------------
# 4. PER-TENANT GOVERNANCE (rate limit + token budget)
# ---------------------------------------------------------------------------
# WHY: prevents noisy neighbors and cost blowups. A compromised key hitting a
# hard budget cap is a *security* control, not just a billing one.
@dataclass
class TenantState:
    cache: TenantCache = field(default_factory=TenantCache)
    tokens_used: int = 0
    token_budget: int = 100_000          # hard monthly cap (illustrative)
    request_times: list[float] = field(default_factory=list)
    rate_limit_per_min: int = 60

    def check_rate(self) -> None:
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60]
        if len(self.request_times) >= self.rate_limit_per_min:
            raise HTTPException(429, "Rate limit exceeded for tenant")
        self.request_times.append(now)

    def check_budget(self, projected: int) -> None:
        if self.tokens_used + projected > self.token_budget:
            raise HTTPException(402, "Token budget exhausted for tenant")


TENANTS: dict[str, TenantState] = {}


def tenant(tenant_id: str) -> TenantState:
    return TENANTS.setdefault(tenant_id, TenantState())


# ---------------------------------------------------------------------------
# 5. ROUTER (cheap -> expensive cascade)
# ---------------------------------------------------------------------------
# WHY: most traffic is easy. A cheap model handles it; we escalate only when the
# request looks hard. This routinely cuts cost 50-80% on easy traffic.
# Real routers use a difficulty classifier or a verifier check; here we use a
# simple, explainable heuristic (length + keywords) to keep the idea clear.
HARD_HINTS = ("analyze", "prove", "design", "debug", "step by step", "explain why")


def route(prompt: str) -> Model:
    long_prompt = len(prompt) > 800
    looks_hard = any(h in prompt.lower() for h in HARD_HINTS)
    return LARGE if (long_prompt or looks_hard) else SMALL


def cost_of(model: Model, in_tok: int, out_tok: int) -> float:
    return in_tok / 1e6 * model.price_in + out_tok / 1e6 * model.price_out


# ---------------------------------------------------------------------------
# 6. THE ENDPOINT — ties it all together
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    tenant_id: str
    prompt: str
    simulate_primary_failure: bool = False  # to demo fallback


@app.post("/v1/chat")
def chat(req: ChatRequest):
    ts = tenant(req.tenant_id)

    # Governance first: cheap checks before spending money.
    ts.check_rate()

    embedding = mock_embed(req.prompt)

    # Cache lookup (per tenant) — the cheapest possible path.
    cached = ts.cache.get(req.prompt, embedding)
    if cached:
        return {"cached": True, **cached, "cost_usd": 0.0}

    # Route to the appropriate model.
    model = route(req.prompt)

    # Rough budget pre-check using an estimate (assume ~300 output tokens).
    est_in = max(1, len(req.prompt) // 4)
    ts.check_budget(est_in + 300)

    # Call the model with FALLBACK on failure.
    try:
        result = mock_model_call(model, req.prompt,
                                 force_fail=req.simulate_primary_failure)
        used_model = model
    except RuntimeError:
        # Primary failed -> fall back to a secondary provider. In production this
        # sits behind a circuit breaker + retries with exponential backoff.
        result = mock_model_call(FALLBACK, req.prompt)
        used_model = FALLBACK

    # Account for real tokens used and update the budget.
    spend = cost_of(used_model, result["in_tokens"], result["out_tokens"])
    ts.tokens_used += result["in_tokens"] + result["out_tokens"]

    response = {
        "text": result["text"],
        "model": used_model.name,
        "tier": used_model.tier,
    }
    # Store in cache for next time.
    ts.cache.put(req.prompt, embedding, response)

    return {
        "cached": False,
        "source": "model",
        **response,
        "cost_usd": round(spend, 6),
        "tenant_tokens_used": ts.tokens_used,
    }


@app.get("/v1/usage/{tenant_id}")
def usage(tenant_id: str):
    ts = tenant(tenant_id)
    return {
        "tenant_id": tenant_id,
        "tokens_used": ts.tokens_used,
        "token_budget": ts.token_budget,
        "remaining": ts.token_budget - ts.tokens_used,
    }


# WHY a health endpoint: load balancers use it to route around unhealthy nodes.
@app.get("/health")
def health():
    return {"status": "ok"}
