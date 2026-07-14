"""
capacity_cost_estimator.py
===========================
Back-of-the-envelope estimators for AI system design interviews. Doing this math
*out loud* is one of the strongest signals of seniority, so this file encodes the
formulas you should have at your fingertips.

Everything here is pure functions + a demo in __main__. No external deps.
Run:  python capacity_cost_estimator.py   (or just read it)

The formulas:
    cost/req  = in_tok/1e6 * price_in + out_tok/1e6 * price_out
    month     = cost/req * req_per_day * 30
    latency   ~= fixed_overhead + decode_tokens / decode_tokens_per_sec
    GPUs      ~= peak_output_tokens_per_sec / per_GPU_throughput  (+ headroom)
    vec bytes ~= num_vectors * dim * bytes_per_dim
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# COST
# ---------------------------------------------------------------------------
def cost_per_request(in_tok: int, out_tok: int,
                     price_in_per_m: float, price_out_per_m: float) -> float:
    """$ for a single request. Output tokens are usually priced higher."""
    return in_tok / 1e6 * price_in_per_m + out_tok / 1e6 * price_out_per_m


def monthly_cost(cost_req: float, req_per_day: int, cache_hit_rate: float = 0.0) -> float:
    """WHY cache_hit_rate: cached requests cost ~$0, so effective cost scales
    with the *miss* rate. A 40% hit rate cuts the bill by ~40%."""
    effective = cost_req * (1.0 - cache_hit_rate)
    return effective * req_per_day * 30


# ---------------------------------------------------------------------------
# LATENCY
# ---------------------------------------------------------------------------
def latency_estimate(out_tok: int,
                     decode_tokens_per_sec: float = 50.0,
                     fixed_overhead_ms: float = 220.0) -> dict:
    """fixed_overhead ~ gateway + embed + vector search + rerank + prefill.
    Decode is sequential, so long outputs dominate. Streaming hides most of this
    behind a fast first token."""
    decode_ms = (out_tok / decode_tokens_per_sec) * 1000
    return {
        "fixed_overhead_ms": fixed_overhead_ms,
        "decode_ms": round(decode_ms, 1),
        "total_ms": round(fixed_overhead_ms + decode_ms, 1),
        "note": "first-token ~= fixed_overhead; stream to improve perceived latency",
    }


# ---------------------------------------------------------------------------
# GPU CAPACITY (self-hosting)
# ---------------------------------------------------------------------------
def gpus_needed(peak_concurrent_requests: int,
                avg_output_tokens: int,
                target_seconds_per_request: float,
                per_gpu_tokens_per_sec: float,
                headroom: float = 0.3) -> dict:
    """Size for PEAK concurrency. KV-cache memory (grows with context x
    concurrency) is often the real limit before raw compute — call that out."""
    required_tps = peak_concurrent_requests * avg_output_tokens / target_seconds_per_request
    raw = required_tps / per_gpu_tokens_per_sec
    with_headroom = raw * (1 + headroom)
    return {
        "required_tokens_per_sec": round(required_tps, 1),
        "gpus_raw": round(raw, 2),
        "gpus_with_headroom": max(1, round(with_headroom + 0.5)),
        "caveat": "KV-cache memory may cap concurrency before compute does",
    }


# ---------------------------------------------------------------------------
# VECTOR STORAGE
# ---------------------------------------------------------------------------
def vector_storage_gb(num_vectors: int, dim: int = 768,
                      bytes_per_dim: int = 4, index_overhead: float = 1.6) -> dict:
    """float32 = 4 bytes/dim; int8 quantization = 1 byte (~4x smaller, small
    recall loss). HNSW graph adds ~1.5-2x overhead."""
    raw_bytes = num_vectors * dim * bytes_per_dim
    raw_gb = raw_bytes / 1e9
    return {
        "raw_gb": round(raw_gb, 2),
        "with_index_gb": round(raw_gb * index_overhead, 2),
        "int8_with_index_gb": round(raw_gb / 4 * index_overhead, 2),
    }


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== RAG chatbot cost ===")
    c = cost_per_request(in_tok=3000, out_tok=500,
                         price_in_per_m=2.50, price_out_per_m=10.00)
    print(f"cost/request        : ${c:.4f}")
    print(f"monthly @1M/day     : ${monthly_cost(c, 1_000_000):,.0f}")
    print(f"monthly @1M/day 40% : ${monthly_cost(c, 1_000_000, 0.40):,.0f}  (caching saves ~40%)")

    print("\n=== Latency (500-token answer) ===")
    print(latency_estimate(out_tok=500))

    print("\n=== GPU capacity ===")
    print(gpus_needed(peak_concurrent_requests=200, avg_output_tokens=400,
                      target_seconds_per_request=5.0, per_gpu_tokens_per_sec=2500))

    print("\n=== Vector storage (10M x 768) ===")
    print(vector_storage_gb(num_vectors=10_000_000, dim=768))

    print("\n=== Vector storage (500M x 768) ===")
    print(vector_storage_gb(num_vectors=500_000_000, dim=768))
