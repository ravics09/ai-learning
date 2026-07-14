# Databases — Rapid Fire (50 Q&A)

> One-line answers for fast recall. Grouped by theme. Cover the answer, quiz yourself.

## Relational & Modeling
1. **What is normalization?** Store each fact once to avoid redundancy/anomalies.
2. **Denormalization?** Duplicate data to speed reads at write-complexity cost.
3. **Primary key?** Unique, not-null row identifier.
4. **Foreign key?** Reference to another table's PK; enforces referential integrity.
5. **1NF?** Atomic columns, no repeating groups.
6. **3NF?** Non-key columns depend on nothing but the key.
7. **Surrogate vs natural key?** Generated id vs meaningful business value.
8. **When denormalize?** Read-heavy hot path, after profiling proves join cost.
9. **Materialized view?** Precomputed, stored query result you refresh.
10. **CHECK constraint?** Enforces a per-row boolean rule at the DB.

## Indexing
11. **What is an index?** Sorted secondary structure for fast lookups.
12. **Default index type?** B-tree.
13. **B-tree complexity?** O(log n) lookups + range scans.
14. **Composite index rule?** Leftmost-prefix.
15. **Partial index?** Indexes only rows matching a `WHERE`.
16. **Covering index?** Includes extra cols → index-only scan.
17. **GIN index for?** JSONB, arrays, full-text.
18. **BRIN index for?** Huge naturally-ordered tables (time-series).
19. **Downside of indexes?** Slower writes + disk/RAM cost.
20. **Why won't `LIKE '%x'` use an index?** Leading wildcard breaks sort order.

## Transactions & Concurrency
21. **ACID?** Atomicity, Consistency, Isolation, Durability.
22. **What ensures durability?** WAL + fsync.
23. **MVCC?** New row versions; readers don't block writers.
24. **Read Committed allows?** Non-repeatable + phantom reads.
25. **PG Repeatable Read is really?** Snapshot Isolation.
26. **Write skew?** Two txns read then write, breaking a cross-row invariant.
27. **Serializable in PG uses?** SSI (aborts conflicts → retry on 40001).
28. **Dirty read?** Reading uncommitted data.
29. **Pessimistic lock?** `SELECT ... FOR UPDATE`.
30. **Optimistic lock?** Version-check on write, retry on mismatch.

## SQL / NoSQL
31. **Four NoSQL types?** Document, key-value, wide-column, graph.
32. **Redis type?** In-memory key-value.
33. **Cassandra sweet spot?** Write-heavy, time-series, multi-DC.
34. **Neo4j for?** Relationship traversal / GraphRAG.
35. **WHERE vs HAVING?** Pre-group filter vs post-aggregate filter.
36. **INNER vs LEFT JOIN?** Matches-only vs all-left-with-nulls.
37. **When SQL over NoSQL?** Relationships + strong consistency.
38. **BASE?** Basically Available, Soft state, Eventual consistency.

## CAP & Distributed
39. **CAP theorem?** On partition, pick Consistency or Availability.
40. **CP example?** Strongly-consistent RDBMS, etcd.
41. **AP example?** Cassandra, DynamoDB eventual.
42. **PACELC adds?** Latency-vs-consistency when no partition.
43. **Linearizable?** Every read sees the latest committed write.
44. **Eventual consistency?** Replicas converge over time.

## Caching
45. **Default cache pattern?** Cache-aside.
46. **Cache stampede fix?** Lock/single-flight or early recompute.
47. **Avalanche fix?** Jitter TTLs.
48. **Semantic cache key?** Query embedding + similarity threshold.

## Scaling & AI
49. **Scale reads?** Cache + read replicas.
50. **Scale writes?** Short txns → partition → shard on a good key.

### Bonus AI patterns
51. **pgvector distance op `<=>`?** Cosine distance.
52. **pgvector default index (2025-26)?** HNSW.
53. **`hnsw.ef_search` higher =?** Better recall, more latency.
54. **pgvector comfort ceiling?** ~10M vectors, then partition/migrate.
55. **Training/serving skew fix?** One feature transform → offline + online stores, point-in-time joins.
56. **Chat history index?** `(conversation_id, created_at)`.
57. **Prevent SQLi?** Parameterized queries.
58. **Fix connection exhaustion?** PgBouncer (connection pooling).

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
