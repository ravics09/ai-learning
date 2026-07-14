# Databases — Cheatsheet (Dense Reference)

> One-page memory jog for interviews and production. Skim before a call.

---

## SQL vs NoSQL
| | SQL (Relational) | NoSQL |
|---|---|---|
| Schema | fixed, enforced | flexible / schema-on-read |
| Joins | native | limited / app-side |
| Transactions | ACID, multi-row | often single-key |
| Scale | scale up; shard w/ effort | scale out natively |
| Consistency | strong | tunable / eventual |
| Use when | relationships, correctness | scale/flexibility/specialized access |
| Examples | PostgreSQL, MySQL | MongoDB, Redis, Cassandra, Neo4j |

## Four NoSQL families
| Type | Example | Use for |
|---|---|---|
| Document | MongoDB | evolving schema, per-object reads |
| Key-Value | Redis, DynamoDB | cache, sessions, hot single-key |
| Wide-column | Cassandra | write-heavy, time-series, multi-DC |
| Graph | Neo4j | traversal, recommendations, GraphRAG |

---

## ACID
- **A**tomicity — all-or-nothing
- **C**onsistency — constraints/invariants hold
- **I**solation — concurrent txns don't corrupt
- **D**urability — survives crash (WAL/fsync)

## Isolation levels & anomalies
| Level | Dirty | Non-repeat | Phantom | Write skew |
|---|:--:|:--:|:--:|:--:|
| Read Uncommitted | maybe | Y | Y | Y |
| Read Committed (PG default) | N | Y | Y | Y |
| Repeatable Read (PG = Snapshot) | N | N | N* | Y |
| Serializable (PG = SSI) | N | N | N | N |

\* PG blocks phantoms at RR. Serializable may abort → **retry on SQLSTATE 40001**.
**MVCC:** writers make new versions; readers don't block writers. `VACUUM` reclaims dead tuples.

---

## Index types (PostgreSQL)
| Type | Best for |
|---|---|
| B-tree | equality, range, sort (default) |
| Hash | equality only |
| GIN | JSONB, arrays, full-text |
| GiST/SP-GiST | geometric, ranges, KNN |
| BRIN | huge, ordered tables (time-series) |
| HNSW / IVFFlat | vector ANN (pgvector) |

**Index tips:** leftmost-prefix for composites; partial (`WHERE`) for subsets; covering (`INCLUDE`) → index-only scan; index FKs + query predicates; writes pay the cost.

```sql
CREATE INDEX idx ON t (a, b) INCLUDE (c) WHERE active;  -- composite+covering+partial
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;  -- Seq Scan on big+selective = missing index
```

---

## CAP / consistency
- **CAP:** on partition, choose **Consistency** or **Availability**.
- **CP:** correct, may reject (money, uniqueness). **AP:** always answers, may be stale (counters, feeds).
- **PACELC:** else (no partition) trade **Latency vs Consistency**.
- Spectrum: strong/linearizable → sequential → causal → eventual.

---

## Redis / caching patterns
| Pattern | Write | Risk |
|---|---|---|
| Cache-aside (default) | write DB, delete key | first read after write misses |
| Write-through | write DB+cache | 2 writes/update |
| Write-behind | write cache, async DB | data loss if cache dies |
| Read-through | cache owns DB fetch | cache = critical path |

**Invalidation:** TTL, delete-on-write, versioned keys, event/CDC.
**Hazards:** stampede (lock/single-flight), penetration (cache negatives), avalanche (jitter TTLs).
**Semantic cache (LLM):** embed query → ANN search → return if `sim >= threshold` + policy ok; scope per user/context; TTL/event invalidate; count only *approved* reuse.

---

## Scaling levers
| Lever | Scales | Notes |
|---|---|---|
| Caching (Redis) | reads | biggest, cheapest win |
| Read replicas | reads + HA | async lag → stale reads |
| Partitioning | one table | range/hash; pruning + archival |
| Sharding | writes | shard key is everything; cross-shard = pain |
| Connection pooling (PgBouncer) | connections | fixes "slow under load" |
| CQRS/event sourcing | write throughput | derive read models async |

**Shard key:** even spread + co-locate related + high cardinality; consistent hashing for rebalancing.

---

## AI-specific
```sql
CREATE EXTENSION vector;
CREATE TABLE docs (id BIGSERIAL, tenant_id BIGINT, content TEXT, embedding VECTOR(1536));
CREATE INDEX ON docs USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
SET hnsw.ef_search = 100;                       -- higher = recall↑ latency↑
SELECT id FROM docs WHERE tenant_id=7 ORDER BY embedding <=> $1 LIMIT 5;  -- hybrid
```
- HNSW default; iterative scans (0.8+) for filtered recall; quantization + partition for RAM; replicas+PgBouncer for read scale; ~10M vector comfort ceiling; budget HNSW reindex on model change.
- **Feature store:** one transform → offline (train) + online (serve); point-in-time correctness kills training/serving skew.
- **Chat history:** conversations + messages (indexed by `conversation_id, created_at`); hot turns in Redis; summarize/trim old.

---

## Security
- **SQLi:** always parameterize (`%s` / prepared stmts); never concat input.
- **Least privilege:** app role ≠ superuser; read-only role for analytics; RLS for multi-tenant.
- **Encryption:** TLS in transit + at rest; keys in KMS.
- **PII:** don't leak into shared caches/embeddings; retention/deletion policies.

---

## Quick heuristics
- Default DB = **PostgreSQL** (add JSONB/full-text/pgvector before adding a new system).
- Read Committed by default; Serializable for cross-row invariants.
- Add a pooler before blaming the DB.
- Reads → cache+replicas; writes → short txns → partition → shard.
- CAP = pick stale-answer vs error, at partition time.

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
