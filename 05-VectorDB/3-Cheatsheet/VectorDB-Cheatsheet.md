# Vector Databases — Cheatsheet

Dense, scannable reference. Metrics, indexes, tuning knobs, quantization, and DB choices.

---

## 1. Similarity Metrics

| Metric | Higher = closer? | Magnitude-sensitive | Use for |
|---|---|---|---|
| Cosine | yes (→1) | no | text semantic search (default) |
| Dot product | yes | yes | normalized vectors, magnitude-as-importance |
| Euclidean L2 | no (lower=closer) | yes | images, clustering, absolute position |

- Normalize vectors → dot == cosine, and use the fast dot kernel.
- Always match the metric the embedding model was trained on.

---

## 2. Index Comparison

| Index | Type | Recall | Latency | Memory | Build | Incremental? | Best for |
|---|---|---|---|---|---|---|---|
| Flat | exact | 100% | O(N) high | high (raw) | none | yes | <100k, ground truth, re-rank |
| HNSW | graph | very high | very low | **high** | medium | yes (deletes weak) | in-memory real-time, <~100M |
| IVF-Flat | cluster | tunable | low–med | medium | fast (train) | needs train | mid scale, GPU |
| IVF-PQ | cluster+compress | med (↑ rerank) | low | **very low** | medium | needs train | billion-scale, cost-bound |
| HNSW-PQ | graph+compress | high | low | low–med | medium | yes | memory-limited graph |
| DiskANN | graph on SSD | high | med (SSD) | low RAM | heavy | partial | billion-scale on one box |
| LSH | hashing | low–med | low | low | fast | yes | streaming, theoretical bounds |

---

## 3. Tuning Knobs

**HNSW**
| Knob | Effect of ↑ | Typical |
|---|---|---|
| `M` | recall ↑, memory ↑, build slower | 16–48 |
| `ef_construction` | graph quality ↑, build slower | 100–400 |
| `ef_search` | recall ↑, latency ↑ | 64–512 (tune to SLO) |

**IVF / IVF-PQ**
| Knob | Effect of ↑ | Typical |
|---|---|---|
| `nlist` | finer partitions; needs more training data | `sqrt(N)`–`4*sqrt(N)` |
| `nprobe` | recall ↑, latency ↑ | 8–128 |
| `m` (PQ subquantizers) | recall ↑, memory ↑ | 16–64 (divides d) |
| `nbits` | codebook size (2^nbits) | 8 |

Rule: raise the runtime dial (`ef_search`/`nprobe`) until recall@k hits target, no higher.

---

## 4. Quantization

| Method | Compression | Recall impact | Distance | Notes |
|---|---|---|---|---|
| Scalar (int8) | ~4× | tiny | approx L2/IP | free default |
| float16 | 2× | ~none | native | easy win |
| Product Quant (PQ) | 20–100× | moderate–high | lookup tables | pair with re-rank; OPQ = +rotation |
| Binary | ~32× | high alone | Hamming (XOR+popcount) | coarse pre-filter → re-rank |
| Matryoshka (MRL) | dim ÷ (e.g. 4×) | low if trained | native | truncate dims; stack with quant |

Golden rule: **quantize the candidate stage, re-rank top-N with full precision.**

---

## 5. Filtering & Hybrid

- **Pre-filter**: filter → ANN. Correct; efficient for *selective* filters; index the field.
- **Post-filter**: ANN → filter. Fast; over-fetch (`k*factor`) or you starve top-k.
- **Hybrid** = dense + sparse (BM25), fused by **RRF**: `score = Σ 1/(k+rank)`, `k≈60`.
  - Rank-based fusion avoids incompatible score scales.
  - Add cross-encoder reranker on top ~50–100 for final ordering.

---

## 6. Scaling

- **Shard** for data size + write throughput (scatter → local top-k → merge global top-k).
- **Replicate** for read QPS + HA.
- Tail latency = slowest shard; mitigate with hedged requests, warm caches, fewer shards.
- **Compute/storage separation** (Milvus, Pinecone serverless, Turbopuffer) = elastic cost.
- RAM estimate (HNSW): `N * (d*4 + M*8)` bytes for float32.

---

## 7. Consistency

- Eventually consistent; LSM-style segments; write→searchable visibility lag.
- Deletes tombstoned, purged at compaction; churn bloats index → schedule rebuilds.
- Some engines offer per-query strong vs eventual consistency.

---

## 8. Vector DB Comparison

| DB | Model | Strengths | Watch-outs | Sweet spot |
|---|---|---|---|---|
| pgvector | Postgres ext | reuse DB, SQL joins, ACID meta | RAM-bound, 2000-dim cap | existing PG, <few M |
| Pinecone | managed/serverless | zero ops, elastic | cost at scale, lock-in | fully managed teams |
| Qdrant | Rust OSS+cloud | fast, great filtering, quant | self-host HA effort | metadata-heavy RAG |
| Weaviate | OSS+cloud | built-in hybrid, modules, multi-tenant | resource use | hybrid out of box |
| Milvus | OSS+Zilliz | huge scale, GPU, many indexes | operationally complex | billion-scale |
| Chroma | embedded/OSS | dead simple, local | not large-scale prod | prototypes/notebooks |
| Vespa/ES | search engines | rich ranking + filters at scale | heavier ops | search teams |

Decision drivers: N, QPS+latency SLO, recall target, filter complexity, hybrid needs,
ops budget, cost model, existing stack, compliance.

---

## 9. Quick Decision Rules

- Small (<100k) or need exact → **Flat**.
- In-memory, real-time, top recall, <~100M → **HNSW**.
- Billion-scale, memory/cost bound → **IVF-PQ** (+ re-rank) or **DiskANN**.
- Already on Postgres, modest scale → **pgvector**.
- Want managed + elastic → **Pinecone / serverless**.
- Heavy filters → **Qdrant**; built-in hybrid → **Weaviate**.

---

## 10. Common Pitfalls

- Different embedding models for docs vs queries → broken recall.
- Wrong metric / unnormalized vectors → silent recall loss.
- Post-filter with selective predicate → too few results.
- Tuning without measuring recall vs a Flat baseline.
- HNSW at billion scale without quantization → OOM / cost blowup.
- Ignoring tombstone bloat / never compacting.
- Trusting client-supplied `tenant_id` → cross-tenant leak.

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
