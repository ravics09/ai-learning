# RAG — Implementation Code Examples

Runnable, progressively advanced RAG examples. Each file is heavily commented so you can read it like a tutorial and explain every line in an interview.

## Files
| File | What it shows |
|---|---|
| `requirements.txt` | Dependencies |
| `01_basic_rag.py` | Minimal end-to-end RAG: chunk → embed → store → retrieve → generate |
| `02_hybrid_search_rerank.py` | Hybrid (dense + BM25) + Reciprocal Rank Fusion + cross-encoder rerank |
| `03_contextual_chunking.py` | Anthropic-style contextual retrieval (context-prefixed chunks) |
| `04_evaluation_ragas.py` | Evaluate retrieval + generation with RAGAS on a golden set |
| `05_production_rag_service.py` | FastAPI service with semantic cache, ACL pre-filter, streaming, citations |

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...        # or configure your provider
```

## How to read these
Start with `01_basic_rag.py` to see the skeleton, then `02` to see why naive RAG isn't enough, then `03`–`05` for the production concerns (accuracy, evaluation, security, scale). The comments explain *why*, not just *what*.

> These are teaching examples. In production, add retries, timeouts, structured logging, and error handling.
