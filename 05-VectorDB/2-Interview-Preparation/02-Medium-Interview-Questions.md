# Vector Databases — Medium Interview Questions

Mid-level questions that probe whether you can *tune* and *reason about* vector search, not
just define it. Expect follow-ups; the answers below include the reasoning you'd say aloud.

## Quick Coverage Map
| # | Question | Theme |
|---|---|---|
| 1 | Explain HNSW and its tuning knobs | Index tuning |
| 2 | How does IVF work; nlist/nprobe? | Index tuning |
| 3 | Pre-filter vs post-filter trade-offs | Filtering |
| 4 | What is IVF-PQ and why re-rank? | Quantization |
| 5 | How does hybrid search + RRF work? | Hybrid |
| 6 | How do you measure/tune recall vs latency? | Evaluation |
| 7 | Deletes and updates in ANN indexes | Consistency |
| 8 | Sharding vs replication | Scaling |
| 9 | Multi-tenancy approaches | Architecture |
| 10 | Curse of dimensionality effects | Foundations |
| 11 | When is a reranker worth it? | Retrieval quality |
| 12 | Estimating memory for an index | Capacity |

---

### 1. Explain HNSW and its main tuning knobs.

HNSW builds a multi-layer graph. Upper layers are sparse with long-range links (express
lanes); the bottom layer contains every node with dense short-range links. Search enters
at the top, greedily walks toward the query, and descends layer by layer.

Knobs:
- **`M`** — neighbors per node. Higher = better recall, more memory, slower build.
- **`ef_construction`** — candidate pool during build. Higher = better graph, slower build.
- **`ef_search`** — candidate pool at query time. Higher = better recall, higher latency.

**Reasoning to say aloud:** "`M` and `ef_construction` are build-time quality; `ef_search`
is the runtime recall/latency dial. I fix `M` around 16–48, set `ef_construction` ~200,
then raise `ef_search` at query time until recall@10 hits target."

---

### 2. How does IVF work, and what are nlist / nprobe?

IVF runs k-means to partition vectors into `nlist` clusters, each with a centroid. At query
time it finds the `nprobe` nearest centroids and only scans vectors in those clusters.

- **`nlist`**: number of clusters (start around `sqrt(N)` to `4*sqrt(N)`).
- **`nprobe`**: clusters scanned per query — the recall/latency dial.

**Trade-off:** low `nprobe` = fast but risks missing neighbors near cluster boundaries;
high `nprobe` approaches brute force. IVF needs a training step, so it's less "just insert"
than HNSW, but uses far less memory.

---

### 3. Pre-filter vs post-filter — trade-offs?

- **Pre-filter:** apply the metadata filter first, then ANN only over matching vectors.
  Correct and efficient *when the filter is selective*, but naive implementations disrupt
  the graph/cluster structure and can slow the search.
- **Post-filter:** run ANN for top-k, then drop non-matching results. Fast, but if the
  filter is selective you may return far fewer than k (even zero) — you searched the wrong
  neighborhood.

**Best practice:** index the fields you filter on; pre-filter selective predicates,
post-filter loose ones with **over-fetch** (`k * factor`). Engines like Qdrant push filters
into the traversal to make pre-filtering efficient.

---

### 4. What is IVF-PQ and why do you re-rank?

IVF-PQ = IVF partitioning + **Product Quantization** compression. PQ splits each vector into
sub-vectors and stores each as a 1-byte codebook id, shrinking a 4 KB vector to ~32–64
bytes (20–100× less memory). That makes billion-scale search affordable — but PQ is
**lossy**, so raw recall drops.

**Why re-rank:** you use IVF-PQ to cheaply get a candidate set (say top-200), then fetch the
full-precision vectors for those candidates and re-score them exactly, returning the true
top-k. You recover most of the lost recall while paying the memory cost only during the
tiny re-rank step.

---

### 5. How does hybrid search + RRF work?

Dense (vector) search captures meaning; sparse (BM25) search captures exact terms like
product codes. Hybrid runs both and fuses them. **Reciprocal Rank Fusion** combines by
*rank*, not score:

```
RRF(d) = Σ 1 / (k + rank_of_d_in_each_list)   # k ≈ 60
```

**Why RRF and not weighted scores:** BM25 scores (~0–30) and cosine (~-1–1) aren't on the
same scale, so naive weighting is brittle. Rank-based fusion sidesteps that. Hybrid
typically lifts NDCG/recall meaningfully over either method alone; add a cross-encoder
reranker for the final ordering.

---

### 6. How do you measure and tune recall vs latency?

1. Build a **Flat (exact)** index over a sample to get ground-truth top-k.
2. Run the ANN index and compute recall@k against that ground truth.
3. Sweep the runtime dial (`ef_search` for HNSW, `nprobe` for IVF) and plot recall vs
   p95 latency.
4. Pick the smallest setting that meets your recall SLO within your latency budget.

**Reasoning:** "I never tune blind. Recall is measured against exact search; latency is
p95/p99, not average, because tail latency is what users feel."

---

### 7. How are deletes and updates handled in ANN indexes?

Most engines **upsert** (insert-or-replace by id) into a mutable segment that becomes
searchable after a short refresh — so there's a visibility lag. Deletes are usually
**tombstoned** (marked deleted, filtered from results) and physically removed later during
background compaction/merge.

**Consequence:** heavy churn bloats the index with tombstones and degrades recall until
compaction runs; HNSW especially dislikes many deletes, so periodic rebuilds keep it
healthy.

---

### 8. Sharding vs replication — what's the difference?

- **Sharding** splits the data across nodes to scale dataset size and write throughput. A
  query scatters to all shards, each returns local top-k, and a coordinator merges into
  global top-k.
- **Replication** copies each shard to multiple nodes to scale read QPS and provide HA.

**Watch-out:** scatter-gather latency is bounded by the slowest shard (tail amplification),
and each shard must return enough candidates that the true global top-k isn't cut off.

---

### 9. What are the main multi-tenancy approaches?

1. **Shared collection + `tenant_id` filter** — cheapest, but a missing filter leaks data;
   enforce it server-side.
2. **Namespaces/partitions** — logical isolation within one index; good balance.
3. **Collection per tenant** — strong isolation, easy per-tenant delete (GDPR), but many
   tiny indexes are hard to operate.
4. **Cluster per tenant** — max isolation, max cost; for regulated/enterprise.

**Key point:** never trust the client to set `tenant_id`; inject it in a trusted middleware
layer.

---

### 10. What is the curse of dimensionality and how does it affect vector search?

As dimensions grow, distances between points become more uniform — everything looks
roughly equidistant — which makes nearest-neighbor "nearest" less meaningful and indexes
harder to build. It also increases memory and compute per comparison.

**Mitigations:** use well-trained embedding models (they concentrate signal), reduce
dimensions via Matryoshka truncation or PCA, and rely on the fact that real embeddings lie
on a lower-dimensional manifold, which ANN indexes exploit.

---

### 11. When is a cross-encoder reranker worth adding?

When first-stage retrieval returns roughly-right candidates but ordering quality matters
(RAG answer quality, search relevance). A cross-encoder jointly reads query+document and
scores relevance far more accurately than cosine — but it's expensive, so you only run it
on the top ~50–100 candidates.

**Rule:** cheap recall (vector/hybrid) to get candidates, expensive precision (reranker) to
order them. Skip it if latency is critical and first-stage relevance is already good enough.

---

### 12. How do you estimate memory for a vector index?

Rough HNSW estimate:
```
RAM ≈ N * (d * bytes_per_dim + graph_edge_overhead)
```
Example: 10M vectors, 768 dims, float32 → 10M * (768*4 + ~M*8) ≈ ~35–40 GB. If that
exceeds budget, options are: scalar quantization (~4×), PQ (20–100×), Matryoshka truncation,
or DiskANN (keep vectors on SSD).

**Reasoning:** "I estimate RAM before choosing an index. If float32 HNSW blows the budget,
I quantize the candidate stage and re-rank, or move to DiskANN."

---

## Further Reading
- FAISS index guidelines: https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index
- Qdrant filtering & quantization: https://qdrant.tech/documentation/
- Weaviate hybrid search: https://weaviate.io/developers/weaviate/search/hybrid
- HNSW paper: https://arxiv.org/abs/1603.09320

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
