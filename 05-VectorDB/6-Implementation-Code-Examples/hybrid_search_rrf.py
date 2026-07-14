"""
hybrid_search_rrf.py
====================
Hybrid search = dense (vector) retrieval + sparse (BM25 keyword) retrieval, fused with
Reciprocal Rank Fusion (RRF). This combination beats either method alone because they
have complementary blind spots:
  - Dense search understands MEANING but misses exact tokens (IDs, rare acronyms).
  - BM25 nails exact TOKENS but misses paraphrases and synonyms.

WHY RRF (and not weighted score averaging):
  BM25 scores (~0..30) and cosine scores (~-1..1) live on totally different scales, so
  naively adding them is brittle. RRF fuses by RANK only, sidestepping that problem.

Run:
    python hybrid_search_rrf.py

Uses numpy for the dense side (cosine over toy embeddings) and rank-bm25 for the sparse
side. Falls back to a tiny built-in BM25 if rank-bm25 isn't installed.
"""

from __future__ import annotations
import numpy as np


DOCS = [
    "The HNSW graph index gives fast approximate nearest neighbor search.",
    "Product quantization compresses vectors so billions fit in memory.",
    "BM25 is a classic keyword ranking function used in search engines.",
    "Reciprocal rank fusion merges result lists by rank, not by score.",
    "Cosine similarity measures the angle between two embedding vectors.",
    "pgvector adds vector search to PostgreSQL via an extension.",
    "DiskANN keeps most of the graph on SSD to save RAM at billion scale.",
    "Metadata filtering restricts search to rows matching tenant or language.",
]


# --------------------------------------------------------------------------
# Dense side: toy "embeddings" via hashed bag-of-words. Real systems use a
# neural embedding model; the FUSION logic is identical regardless.
# --------------------------------------------------------------------------
def toy_embed(text: str, dim: int = 256) -> np.ndarray:
    v = np.zeros(dim, dtype="float32")
    for tok in text.lower().split():
        v[hash(tok) % dim] += 1.0
    n = np.linalg.norm(v)
    return v / n if n else v  # normalize => dot == cosine


def dense_search(query: str, k: int):
    q = toy_embed(query)
    mat = np.vstack([toy_embed(d) for d in DOCS])
    scores = mat @ q                          # cosine on normalized vectors
    order = np.argsort(-scores)[:k]           # descending
    return order.tolist()


# --------------------------------------------------------------------------
# Sparse side: BM25 keyword ranking.
# --------------------------------------------------------------------------
def bm25_search(query: str, k: int):
    tokenized = [d.lower().split() for d in DOCS]
    try:
        from rank_bm25 import BM25Okapi

        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())
    except Exception:
        # Minimal TF overlap fallback so the demo runs without rank-bm25.
        q = set(query.lower().split())
        scores = np.array([len(q & set(toks)) for toks in tokenized], dtype="float32")
    return np.argsort(-np.asarray(scores))[:k].tolist()


# --------------------------------------------------------------------------
# The fusion step — the heart of hybrid search.
# --------------------------------------------------------------------------
def reciprocal_rank_fusion(result_lists, k_const: int = 60, top_n: int = 5):
    """Combine multiple ranked lists of doc ids by rank.

    score(d) = sum over lists of 1 / (k_const + rank_in_that_list)
    Rank is 1-based; rank 1 (best) contributes the most. k_const (≈60) dampens the
    influence of very high ranks so a single list can't fully dominate.
    """
    scores: dict[int, float] = {}
    for results in result_lists:
        for rank, doc_id in enumerate(results, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k_const + rank)
    return sorted(scores, key=scores.get, reverse=True)[:top_n]


def main() -> None:
    # This query mixes an exact term ("BM25") with a conceptual phrase ("merge lists").
    # Dense should like the concept docs; BM25 should like the exact "BM25" doc.
    query = "how does BM25 merge ranked lists"
    k = 5

    dense = dense_search(query, k)
    sparse = bm25_search(query, k)
    fused = reciprocal_rank_fusion([dense, sparse], k_const=60, top_n=5)

    def show(title, ids):
        print(f"\n{title}:")
        for rank, i in enumerate(ids, 1):
            print(f"  {rank}. [{i}] {DOCS[i]}")

    print(f"Query: {query!r}")
    show("Dense (vector) results", dense)
    show("Sparse (BM25) results", sparse)
    show("Hybrid via RRF (final)", fused)

    print("\nTakeaway: RRF promotes docs that BOTH retrievers rank highly, and rescues "
          "good docs that only one retriever found. In production, add a cross-encoder "
          "reranker on top of these fused candidates for the final ordering.")


if __name__ == "__main__":
    main()
