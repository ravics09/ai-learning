"""
hnsw_index_faiss.py
===================
Build an HNSW index with FAISS, then MEASURE recall against an exact (Flat) baseline while
sweeping ef_search. This is the single most important habit in vector search:
never tune blind — always compare approximate results to ground truth.

WHY this file exists:
- Interviewers love "how do you tune recall vs latency?". The answer is this loop.
- It shows ef_search as the runtime recall/latency dial and how latency rises with recall.

Run:
    python hnsw_index_faiss.py

Requires faiss-cpu. If FAISS is missing it prints install instructions and exits.
"""

from __future__ import annotations
import time
import numpy as np

try:
    import faiss
except ImportError:
    raise SystemExit("This example needs FAISS. Install with:  pip install faiss-cpu")


def make_data(n=50_000, d=128, seed=42):
    # Synthetic normalized vectors. Real workloads use embeddings, but random data is
    # enough to demonstrate the recall/latency mechanics.
    rng = np.random.default_rng(seed)
    x = rng.standard_normal((n, d)).astype("float32")
    faiss.normalize_L2(x)  # unit vectors => inner product behaves like cosine
    return x, d


def recall_at_k(approx_ids: np.ndarray, exact_ids: np.ndarray) -> float:
    # recall@k = average fraction of the true neighbors we recovered, per query.
    hits = 0
    for a_row, e_row in zip(approx_ids, exact_ids):
        hits += len(set(a_row.tolist()) & set(e_row.tolist()))
    return hits / (approx_ids.shape[0] * approx_ids.shape[1])


def main() -> None:
    data, d = make_data()
    queries = data[:200]  # reuse some points as queries for a quick demo
    k = 10

    # -----------------------------------------------------------------
    # 1. EXACT baseline (Flat). This is our ground truth for recall.
    #    IndexFlatIP = inner product; on normalized vectors that's cosine.
    # -----------------------------------------------------------------
    flat = faiss.IndexFlatIP(d)
    flat.add(data)
    t0 = time.perf_counter()
    _, exact_ids = flat.search(queries, k)
    flat_ms = (time.perf_counter() - t0) / len(queries) * 1000
    print(f"Flat (exact) baseline: {flat_ms:.3f} ms/query over {data.shape[0]} vectors\n")

    # -----------------------------------------------------------------
    # 2. Build HNSW. M and efConstruction are BUILD-TIME quality knobs.
    # -----------------------------------------------------------------
    M = 32                       # graph degree: higher recall, more memory
    hnsw = faiss.IndexHNSWFlat(d, M, faiss.METRIC_INNER_PRODUCT)
    hnsw.hnsw.efConstruction = 200  # bigger candidate pool at build => better graph
    t0 = time.perf_counter()
    hnsw.add(data)
    print(f"Built HNSW (M={M}, efConstruction=200) in {time.perf_counter()-t0:.2f}s\n")

    # -----------------------------------------------------------------
    # 3. Sweep ef_search: the RUNTIME recall/latency dial.
    #    Watch recall climb toward 1.0 while latency grows. Pick the
    #    smallest ef that meets your recall SLO.
    # -----------------------------------------------------------------
    print(f"{'ef_search':>10}{'recall@10':>12}{'ms/query':>12}")
    for ef in (16, 32, 64, 128, 256):
        hnsw.hnsw.efSearch = ef
        t0 = time.perf_counter()
        _, approx_ids = hnsw.search(queries, k)
        ms = (time.perf_counter() - t0) / len(queries) * 1000
        r = recall_at_k(approx_ids, exact_ids)
        print(f"{ef:>10}{r:>12.3f}{ms:>12.3f}")

    print("\nTakeaway: raise ef_search until recall@k hits your target, then STOP — "
          "extra ef just costs latency for recall you don't need.")


if __name__ == "__main__":
    main()
