# 05 — Vector Databases

Vector databases store and search high-dimensional embeddings for semantic similarity — the backbone of RAG and semantic search.

## Learning Objectives
- Understand embeddings, similarity metrics, and ANN indexes.
- Compare vector DB options and pick the right one.
- Tune for recall, latency, and cost.

## Core Concepts
### Embeddings
- Dense vector representations of text/images/audio.
- Embedding models: OpenAI `text-embedding-3`, Cohere, `bge`, `e5`, sentence-transformers.
- Dimensionality, normalization, and Matryoshka embeddings.

### Similarity Metrics
- Cosine similarity, dot product, Euclidean (L2).
- When to use each (normalized vs unnormalized vectors).

### Indexing Algorithms (ANN)
- **HNSW** (graph-based) — great recall/latency, memory heavy.
- **IVF / IVF-PQ** — clustering + quantization for scale.
- **Flat** — exact but slow; good for small datasets.
- Trade-offs: recall vs latency vs memory.

### Metadata & Filtering
- Pre-filter vs post-filter.
- Hybrid search (dense + sparse).
- Namespaces / multi-tenancy.

## Popular Vector DBs
- **Pinecone** — managed, serverless.
- **Weaviate** — open source, hybrid search, modules.
- **Qdrant** — Rust, fast, great filtering.
- **Milvus** — scalable, GPU support.
- **Chroma** — lightweight, great for prototyping.
- **pgvector** — Postgres extension (reuse your DB).

## Interview Questions
1. What is an embedding and how is similarity computed?
2. Explain HNSW vs IVF-PQ trade-offs.
3. Cosine vs dot product vs Euclidean — when to use each?
4. How does metadata filtering interact with ANN search?
5. How do you decide vector dimensions and index parameters?
6. When would you use pgvector over a dedicated vector DB?

## Hands-On
- [ ] Index 10k documents in two different vector DBs; compare recall/latency.
- [ ] Tune HNSW `ef`/`M` parameters and measure impact.
- [ ] Implement hybrid search with metadata filters.

## Resources
- Pinecone learn: https://www.pinecone.io/learn/
- Qdrant docs: https://qdrant.tech/documentation/
