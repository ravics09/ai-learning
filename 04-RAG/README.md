# 04 — Retrieval-Augmented Generation (RAG)

RAG grounds LLM responses in external knowledge to reduce hallucination and add up-to-date/private data.

## Learning Objectives
- Build a complete RAG pipeline end to end.
- Optimize chunking, retrieval, and ranking.
- Evaluate and improve RAG quality.

## RAG Pipeline
1. **Ingestion**: load, clean, and parse documents (PDF, HTML, code).
2. **Chunking**: split text (fixed, recursive, semantic, or structure-aware).
3. **Embedding**: convert chunks to vectors.
4. **Indexing**: store vectors in a vector DB with metadata.
5. **Retrieval**: query, similarity search, filtering.
6. **Reranking**: cross-encoder / LLM reranking of candidates.
7. **Generation**: stuff context into the prompt and answer.
8. **Citation**: return sources.

## Advanced Techniques
- **Hybrid search**: dense (vectors) + sparse (BM25/keyword).
- **Query transformation**: rewriting, HyDE, multi-query.
- **Chunk strategies**: parent-document, sentence-window, contextual retrieval.
- **Reranking**: Cohere Rerank, cross-encoders.
- **Agentic RAG**: the model decides when/what to retrieve.
- **GraphRAG**: knowledge-graph-based retrieval.

## Common Failure Modes
- Poor chunking → lost context.
- Retrieval misses → wrong or empty context.
- Context overflow → "lost in the middle".
- No citations → untrustworthy answers.

## Evaluation
- Retrieval metrics: precision@k, recall@k, MRR, nDCG.
- Generation metrics: faithfulness, answer relevance, context precision/recall.
- Tools: RAGAS, TruLens, LangSmith, DeepEval.

## Interview Questions
1. Walk through a RAG pipeline end to end.
2. How do you choose chunk size and overlap?
3. What is hybrid search and why does it help?
4. What is reranking and when do you need it?
5. How do you evaluate a RAG system?
6. How do you handle the "lost in the middle" problem?
7. When is fine-tuning better than RAG (and vice versa)?

## Hands-On
- [ ] Build a RAG system over your own PDFs with citations.
- [ ] Add hybrid search and a reranker; measure improvement.
- [ ] Set up a RAGAS evaluation harness.

## Resources
- Anthropic contextual retrieval: https://www.anthropic.com/news/contextual-retrieval
- RAGAS: https://docs.ragas.io/
