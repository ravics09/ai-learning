# Databases — Implementation Code Examples

Runnable, heavily-commented examples for the patterns in the Detailed Learning guide. Every file explains **why**, not just how.

## Files
| File | What it shows | Why it matters |
|------|---------------|----------------|
| [`pgvector_setup.sql`](./pgvector_setup.sql) | RAG schema, HNSW index, hybrid query, row-level security | The data layer for RAG done in plain PostgreSQL — embeddings next to relational data |
| [`pgvector_rag.py`](./pgvector_rag.py) | Parameterized inserts + hybrid similarity search with `hnsw.ef_search` | The retrieval half of RAG, with the recall/latency knob exposed |
| [`redis_semantic_cache.py`](./redis_semantic_cache.py) | Two-tier (exact + semantic) LLM response cache with a similarity threshold | Turns paid, multi-second model calls into ~ms lookups; shows the correctness knobs |
| [`transactions_isolation.py`](./transactions_isolation.py) | Atomic transfers, `SERIALIZABLE` + retry on `40001`, `SELECT … FOR UPDATE` | Using isolation correctly, not just defining it |
| [`chat_history_schema.sql`](./chat_history_schema.sql) | Conversations/messages/checkpoints schema + the hot-path index | Durable LLM memory and resumable agent state |

## Prerequisites
- **PostgreSQL 16+** with the `vector` extension available (`CREATE EXTENSION vector;`).
- **Redis 7+** for the semantic cache demo.
- **Python 3.10+** and the packages in [`requirements.txt`](./requirements.txt):
  ```bash
  pip install -r requirements.txt
  ```
- Set your connection string:
  ```bash
  export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
  ```

## Suggested order
1. Apply the SQL schemas:
   ```bash
   psql "$DATABASE_URL" -f pgvector_setup.sql
   psql "$DATABASE_URL" -f chat_history_schema.sql
   ```
2. Run the RAG retrieval demo:
   ```bash
   python pgvector_rag.py
   ```
3. Run the transaction/isolation demo:
   ```bash
   python transactions_isolation.py
   ```
4. Start Redis, then run the semantic cache demo:
   ```bash
   python redis_semantic_cache.py
   ```

## Notes
- The embedding functions are **deterministic placeholders** so the demos run offline and reproducibly. Swap in a real embedding model (OpenAI or `sentence-transformers`) for production — see the comment block at the bottom of `pgvector_rag.py`. Keep the model's output dimension in lockstep with the `VECTOR(n)` column.
- The semantic cache uses a linear scan for clarity; at scale, replace it with the Redis vector index (`FT.SEARCH` KNN) for sub-linear nearest-neighbor search.
- All Python DB access uses **parameterized queries** (`%s`) — never string concatenation — to prevent SQL injection.

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
