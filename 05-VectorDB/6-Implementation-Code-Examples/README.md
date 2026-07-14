# Vector Databases — Implementation Code Examples

Runnable, heavily-commented examples. Each file demonstrates ONE core idea, with comments
explaining the **why** — the same reasoning you'd give in an interview. Every example is
designed to run with minimal setup: heavy dependencies degrade gracefully to a numpy
fallback so nothing hard-fails.

## Setup
```bash
pip install -r requirements.txt
```
Run one at a time:
```bash
python embeddings_similarity.py
```

## Index
| File | What it shows | Key "why" |
|---|---|---|
| [`embeddings_similarity.py`](./embeddings_similarity.py) | Text → vectors; cosine vs dot vs L2; the normalization gotcha | Similarity is geometry; wrong metric/normalization silently kills recall |
| [`hnsw_index_faiss.py`](./hnsw_index_faiss.py) | Build HNSW, measure recall@k vs a Flat baseline while sweeping `ef_search` | Never tune blind — recall is measured against exact search |
| [`hybrid_search_rrf.py`](./hybrid_search_rrf.py) | Dense + BM25 retrieval fused with Reciprocal Rank Fusion | RRF fuses by rank, dodging incompatible score scales |
| [`metadata_filtering.py`](./metadata_filtering.py) | Pre-filter vs post-filter; post-filter starvation + over-fetch fix | Selective filters break naive post-filtering |
| [`qdrant_or_chroma_crud.py`](./qdrant_or_chroma_crud.py) | Full CRUD + filtered search against an embedded vector DB | Real database ergonomics: payloads, upsert-by-id, deletes |

## Suggested reading order
1. `embeddings_similarity.py` — the geometric foundation.
2. `hnsw_index_faiss.py` — the recall/latency tuning loop.
3. `metadata_filtering.py` — the pre/post-filter trade-off.
4. `hybrid_search_rrf.py` — combining dense + sparse retrieval.
5. `qdrant_or_chroma_crud.py` — the production CRUD lifecycle.

## Notes
- Model names and dims are illustrative — swap for whatever you have access to.
- These are teaching scaffolds. Before production, add: recall canaries, p95/p99 latency
  monitoring, quantization + re-rank for scale, per-tenant auth, and compaction/rebuild
  schedules (see `../3-Cheatsheet/VectorDB-Cheatsheet.md`).
- FAISS (`faiss-cpu`), `rank-bm25`, `qdrant-client`, and `chromadb` are optional; each file
  falls back to a numpy stand-in so it still runs and teaches the same idea.

> Content synthesized from general domain knowledge and current (2025-2026) documentation and interview trends; rephrased for compliance with licensing restrictions.
