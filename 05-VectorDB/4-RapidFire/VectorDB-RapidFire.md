# Vector Databases — Rapid Fire (50 Q&A)

One-line answers for fast recall and warm-up. Grouped by theme.

## Embeddings & Metrics
1. **What is an embedding?** A vector that places similar content close in geometric space.
2. **Same model for docs and queries?** Yes — mixing models breaks the shared space.
3. **Cosine measures what?** The angle between vectors, ignoring magnitude.
4. **Dot product sensitive to magnitude?** Yes.
5. **When cosine == dot?** When vectors are L2-normalized.
6. **L2 used for?** Image embeddings, clustering, absolute-position tasks.
7. **Why normalize?** Enables the fast dot kernel and avoids the "hub" problem.
8. **Typical text dims?** 384–3072 depending on model.
9. **Matryoshka embeddings?** First-K dims are a valid smaller embedding you can truncate to.
10. **Curse of dimensionality?** High dims make distances uniform, weakening "nearest".

## ANN & Indexes
11. **Why approximate?** Exact O(N) search is too slow at scale.
12. **The core trade-off?** Recall vs latency vs memory.
13. **recall@k?** Fraction of true top-k the ANN actually returns.
14. **Flat index?** Exact brute-force; perfect recall, slow at scale.
15. **HNSW is?** A layered proximity graph traversed greedily.
16. **HNSW `M`?** Neighbors per node — higher recall, more memory.
17. **HNSW `ef_search`?** Query-time candidate list — the recall/latency dial.
18. **HNSW `ef_construction`?** Build-time candidate list — graph quality.
19. **HNSW weakness?** High memory and poor deletion handling.
20. **IVF idea?** k-means clusters; search only nearest clusters.
21. **IVF `nlist`?** Number of clusters (~sqrt(N)+).
22. **IVF `nprobe`?** Clusters scanned per query — recall/latency dial.
23. **IVF-PQ adds?** Product Quantization compression on top of IVF.
24. **Why re-rank after PQ?** PQ is lossy; re-score candidates with full precision.
25. **DiskANN?** Graph index with data on SSD — billion-scale, low RAM.
26. **LSH?** Hashing-based ANN; good for streaming, weaker recall.

## Quantization
27. **Scalar quant?** float32 → int8, ~4×, tiny recall loss.
28. **Product quant?** Sub-vector codebooks; 20–100× smaller, lossy.
29. **Binary quant?** 1 bit/dim, ~32×, Hamming distance, coarse filter.
30. **OPQ?** PQ with a learned rotation to reduce error.
31. **Best quantization pattern?** Compress candidate stage, re-rank top-N in full precision.
32. **Matryoshka + quant?** Stack truncation with quantization for compounding savings.

## Filtering & Hybrid
33. **Pre-filter?** Filter first, then ANN over the subset.
34. **Post-filter?** ANN first, then drop non-matches.
35. **Post-filter risk?** Selective filters return fewer than k — over-fetch to fix.
36. **Filtered-search hard case?** Medium-selectivity (~1%) filters.
37. **Hybrid search?** Combine dense (vector) + sparse (BM25).
38. **RRF formula?** score = Σ 1/(k + rank), k≈60.
39. **Why rank-based fusion?** BM25 and cosine scores aren't on the same scale.
40. **Cross-encoder reranker?** Jointly scores query+doc; accurate but run on top-N only.

## Scaling & Ops
41. **Sharding scales?** Data size and write throughput.
42. **Replication scales?** Read QPS and availability.
43. **Scatter-gather latency bound by?** The slowest shard (tail amplification).
44. **Fix tail latency?** Hedged requests, warm caches, fewer shards.
45. **Visibility lag?** Delay between write and searchability.
46. **Deletes handled by?** Tombstones + background compaction.
47. **Compute/storage separation benefit?** Elastic cost; scale query nodes independently.
48. **Multi-tenancy options?** Filter, namespace, collection-per-tenant, cluster-per-tenant.
49. **Enforce tenant_id where?** Server-side middleware — never trust the client.
50. **2025-2026 default DB?** pgvector to start; graduate when scale/filtering/cost demand.

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
