"""
metadata_filtering.py
=====================
Demonstrates the pre-filter vs post-filter trade-off — one of the most practical (and
most misunderstood) parts of vector search.

  - PRE-FILTER: restrict to rows matching the metadata predicate, THEN do similarity.
      Correct results; efficient when the filter is selective.
  - POST-FILTER: do similarity to get top-k, THEN drop rows failing the predicate.
      Fast, but if the filter is selective you can return FEWER than k (even zero),
      because the true matches were never in the unfiltered top-k neighborhood.

WHY this file exists:
- It makes the "post-filter starvation" failure mode concrete and shows the standard
  fix: OVER-FETCH (retrieve k * factor, then filter down).

Run:
    python metadata_filtering.py

Pure numpy — no external services needed.
"""

from __future__ import annotations
import numpy as np

rng = np.random.default_rng(7)
N, D = 5_000, 64

# Corpus of normalized vectors, each tagged with metadata (tenant + language).
data = rng.standard_normal((N, D)).astype("float32")
data /= np.linalg.norm(data, axis=1, keepdims=True) + 1e-12
tenants = rng.choice(["acme", "globex", "initech"], size=N)
langs = rng.choice(["en", "fr", "de"], size=N, p=[0.8, 0.1, 0.1])

# Make "acme + fr" deliberately RARE (~2% of rows) to trigger post-filter starvation.
selective_mask = (tenants == "acme") & (langs == "fr")
print(f"Rows matching selective filter (tenant=acme, lang=fr): "
      f"{selective_mask.sum()} / {N} ({selective_mask.mean()*100:.1f}%)\n")


def cosine_scores(query: np.ndarray) -> np.ndarray:
    return data @ query  # normalized vectors => dot == cosine


def pre_filter_search(query, mask, k=10):
    # Compute similarity ONLY over rows passing the filter. Always returns up to k real
    # matches. In a real engine this is done inside the index (payload index / filtered
    # HNSW) rather than a full scan, but the semantics are the same.
    idx = np.where(mask)[0]
    scores = data[idx] @ query
    top = idx[np.argsort(-scores)[:k]]
    return top.tolist()


def post_filter_search(query, mask, k=10, overfetch=1):
    # Retrieve top (k * overfetch) ignoring the filter, THEN drop non-matches.
    fetch = k * overfetch
    scores = cosine_scores(query)
    cand = np.argsort(-scores)[:fetch]
    kept = [i for i in cand if mask[i]][:k]
    return kept


def main() -> None:
    query = data[0]  # arbitrary query vector
    k = 10

    pre = pre_filter_search(query, selective_mask, k)
    post_naive = post_filter_search(query, selective_mask, k, overfetch=1)
    post_overfetch = post_filter_search(query, selective_mask, k, overfetch=50)

    print(f"Pre-filter returned:              {len(pre):>3} results (correct: up to k)")
    print(f"Post-filter (overfetch x1):       {len(post_naive):>3} results  "
          f"<-- STARVED: selective filter left almost nothing")
    print(f"Post-filter (overfetch x50):      {len(post_overfetch):>3} results  "
          f"<-- fixed by fetching a bigger candidate pool")

    print("\nTakeaways:")
    print("  * Selective filter + naive post-filter => too few / zero results.")
    print("  * Fixes: pre-filter (best for selective predicates) OR post-filter with")
    print("    over-fetch. Either way, INDEX the metadata fields you filter on.")
    print("  * Loose filters (match most rows) are fine with cheap post-filtering.")


if __name__ == "__main__":
    main()
