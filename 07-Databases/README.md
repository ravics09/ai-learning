# 07 — Databases

AI applications still need solid data foundations: relational, NoSQL, caching, and vector-capable stores.

## Learning Objectives
- Model data correctly and query efficiently.
- Choose the right database for each workload.
- Understand transactions, indexing, and scaling.

## Core Topics
### Relational (SQL)
- Schema design, normalization, and denormalization.
- Joins, indexes (B-tree), query planning (`EXPLAIN`).
- Transactions and ACID; isolation levels.
- PostgreSQL as the default choice (+ `pgvector` for embeddings).

### NoSQL
- **Document** (MongoDB) — flexible schema.
- **Key-Value** (Redis, DynamoDB) — speed, caching.
- **Wide-column** (Cassandra) — write-heavy scale.
- **Graph** (Neo4j) — relationships, GraphRAG.

### Caching
- Redis for sessions, rate limiting, semantic caching of LLM responses.
- Cache invalidation strategies.

### Scaling
- Replication, sharding, partitioning.
- Read replicas and connection pooling.
- CAP theorem trade-offs.

## AI-Specific Data Patterns
- Storing embeddings + metadata (pgvector).
- Semantic caching to cut LLM cost.
- Feature stores for ML features.
- Storing chat history and conversation state.

## Interview Questions
1. SQL vs NoSQL — how do you choose?
2. Explain ACID and isolation levels.
3. What is an index and how does it speed up queries?
4. Explain the CAP theorem.
5. How would you implement semantic caching for an LLM app?
6. Normalization vs denormalization — trade-offs?
7. How do you scale reads vs writes?

## Hands-On
- [ ] Design a schema for a chat app (users, conversations, messages).
- [ ] Add `pgvector` and run similarity queries.
- [ ] Implement Redis-based semantic caching for LLM responses.

## Resources
- PostgreSQL docs: https://www.postgresql.org/docs/
- Use The Index, Luke: https://use-the-index-luke.com/
