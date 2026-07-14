"""
profiling_optimization.py
=========================

The #1 performance rule: MEASURE before you optimize. The bottleneck is rarely
where you guess. This file shows how to time and profile code, then demonstrates
the single biggest win in numeric Python: replacing pure-Python loops with
vectorized NumPy (the loop then runs in optimized C, not the interpreter).

Run:  python profiling_optimization.py
"""
from __future__ import annotations

import cProfile
import io
import math
import pstats
import time
from contextlib import contextmanager

import numpy as np


# ---------------------------------------------------------------------------
# A tiny timing context manager. `time.perf_counter()` is the right clock for
# measuring elapsed wall time (monotonic, high resolution). `with timer(...)`
# guarantees we print the timing even if the block raises.
# ---------------------------------------------------------------------------
@contextmanager
def timer(label: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{label:<28}: {time.perf_counter() - start:.4f}s")


# ---------------------------------------------------------------------------
# The task: compute cosine similarity between one query vector and many document
# vectors. We implement it two ways to show the vectorization win.
# ---------------------------------------------------------------------------
def cosine_similarities_pyloop(query: list[float], docs: list[list[float]]) -> list[float]:
    """Pure-Python version. Correct, but every operation runs in the interpreter.

    This is the kind of loop that shows up in a naive embedding-search prototype and
    becomes the bottleneck at scale. Great for correctness tests; bad for hot paths.
    """
    q_norm = math.sqrt(sum(x * x for x in query))
    out: list[float] = []
    for doc in docs:
        dot = sum(a * b for a, b in zip(query, doc))
        d_norm = math.sqrt(sum(x * x for x in doc))
        out.append(dot / (q_norm * d_norm) if d_norm and q_norm else 0.0)
    return out


def cosine_similarities_numpy(query: np.ndarray, docs: np.ndarray) -> np.ndarray:
    """Vectorized version. The loops happen inside NumPy's compiled C code.

    - `docs @ query` does all dot products at once (matrix-vector multiply).
    - `np.linalg.norm(docs, axis=1)` computes every row norm at once (broadcasting).
    Typically 10-100x faster and far less interpreter overhead.
    """
    q_norm = np.linalg.norm(query)
    d_norms = np.linalg.norm(docs, axis=1)
    denom = d_norms * q_norm
    # Avoid divide-by-zero: where denom==0, output 0.
    return np.divide(docs @ query, denom, out=np.zeros_like(denom), where=denom != 0)


def demo_speed() -> None:
    rng = np.random.default_rng(42)
    n_docs, dim = 5000, 256
    docs_np = rng.random((n_docs, dim))
    query_np = rng.random(dim)
    # Python-native copies for the loop version.
    docs_py = docs_np.tolist()
    query_py = query_np.tolist()

    with timer("pure-python loop"):
        py_result = cosine_similarities_pyloop(query_py, docs_py)

    with timer("numpy vectorized"):
        np_result = cosine_similarities_numpy(query_np, docs_np)

    # Sanity check: both approaches must agree (correctness before speed).
    max_diff = float(np.max(np.abs(np.array(py_result) - np_result)))
    print(f"max difference between methods: {max_diff:.2e}  (should be ~0)")


def demo_cprofile() -> None:
    """Show cProfile output: which functions dominate cumulative time.

    In practice you'd also use py-spy (live, no code change) for production processes
    and line_profiler to drill into a single hot function.
    """
    profiler = cProfile.Profile()
    rng = np.random.default_rng(0)
    docs = rng.random((2000, 128)).tolist()
    query = rng.random(128).tolist()

    profiler.enable()
    cosine_similarities_pyloop(query, docs)
    profiler.disable()

    buf = io.StringIO()
    stats = pstats.Stats(profiler, stream=buf).sort_stats("cumulative")
    stats.print_stats(5)                # top 5 by cumulative time
    print("\ncProfile (top functions by cumulative time):")
    print(buf.getvalue())


if __name__ == "__main__":
    # 1) See the vectorization speedup and confirm correctness.
    demo_speed()
    print()
    # 2) See how to find hotspots with a profiler.
    demo_cprofile()
