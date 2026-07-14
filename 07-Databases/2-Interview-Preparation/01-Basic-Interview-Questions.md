# Databases — Basic Interview Questions

> Foundational questions you should be able to answer smoothly and confidently. Natural tone, real examples, and the *why* behind each answer.

## Quick Coverage Map
| # | Question | Theme |
|---|----------|-------|
| 1 | What is a database index? | Indexing |
| 2 | SQL vs NoSQL | Data models |
| 3 | What is ACID? | Transactions |
| 4 | Primary key vs foreign key | Modeling |
| 5 | What is normalization? | Modeling |
| 6 | INNER vs LEFT JOIN | SQL |
| 7 | What is a transaction? | Transactions |
| 8 | What is caching / Redis? | Caching |
| 9 | WHERE vs HAVING | SQL |
| 10 | What is CAP theorem (intro)? | Distributed |
| 11 | What is pgvector? | AI patterns |
| 12 | DELETE vs TRUNCATE vs DROP | SQL |

---

### 1. What is a database index and why does it matter?
An index is a sorted secondary structure (usually a B-tree) that lets the database jump straight to matching rows instead of scanning the whole table — exactly like the index at the back of a book. Without one, a `WHERE email = ?` on a million-row table reads all million rows (a "sequential scan"); with one, it's an `O(log n)` lookup.

```sql
CREATE INDEX idx_users_email ON users (email);
```
**Trade-off:** indexes speed up reads but slow down writes (each insert/update maintains them) and use disk. Index the columns you filter, join, or sort on — not everything.

---

### 2. What's the difference between SQL and NoSQL databases?
- **SQL (relational):** fixed schema, tables with rows/columns, joins, strong consistency, ACID transactions. Great when data is relational and correctness matters (PostgreSQL, MySQL).
- **NoSQL:** flexible or specialized models — document (MongoDB), key-value (Redis), wide-column (Cassandra), graph (Neo4j). Often trades joins and multi-key transactions for horizontal scale or schema flexibility.

**Why/when:** default to SQL; pick NoSQL when a specific access pattern (huge write volume, single-key hot reads, graph traversal, evolving schemas) demands it.

---

### 3. What does ACID stand for?
- **Atomicity** — all statements in a transaction succeed or none do.
- **Consistency** — the DB moves between valid states; constraints hold.
- **Isolation** — concurrent transactions don't corrupt each other.
- **Durability** — once committed, data survives crashes.

It's the promise that lets you move money between accounts without ever losing or duplicating it.

---

### 4. Primary key vs foreign key?
- **Primary key:** uniquely identifies each row in a table (unique + not null). One per table.
- **Foreign key:** a column that references a primary key in another table, enforcing referential integrity (you can't reference a user that doesn't exist).

```sql
CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT REFERENCES users(id)   -- foreign key
);
```

---

### 5. What is normalization?
Organizing tables so each fact is stored once, eliminating redundancy and update anomalies. You split data into related tables (users, orders, products) linked by keys. **Denormalization** is the opposite — deliberately duplicating data to speed up reads at the cost of write complexity. Normalize by default; denormalize when profiling proves a read path needs it.

---

### 6. INNER JOIN vs LEFT JOIN?
- **INNER JOIN** returns only rows with a match in both tables.
- **LEFT JOIN** returns all rows from the left table, with NULLs where the right has no match.

```sql
-- Users and their orders; users with no orders still appear (order columns NULL)
SELECT u.id, o.id
FROM users u
LEFT JOIN orders o ON o.user_id = u.id;
```

---

### 7. What is a transaction?
A unit of work that groups multiple statements so they commit or roll back together. `BEGIN ... COMMIT` (or `ROLLBACK` on error). It's how you keep multi-step operations correct under failures and concurrency.

---

### 8. What is caching, and where does Redis fit?
Caching stores expensive-to-compute or frequently-read data in a fast layer so future requests skip the slow source. **Redis** is an in-memory key-value store with microsecond latency, used for caching, sessions, rate limiting, and (in AI apps) semantic caching of LLM responses. The most common pattern is **cache-aside**: check cache → on miss, read DB and fill cache; on write, invalidate the key. Always set a TTL to bound staleness.

---

### 9. WHERE vs HAVING?
- **WHERE** filters rows *before* grouping/aggregation.
- **HAVING** filters *after* `GROUP BY`, on aggregate results.

```sql
SELECT user_id, COUNT(*) AS n
FROM orders
WHERE total > 0          -- per-row filter
GROUP BY user_id
HAVING COUNT(*) > 5;     -- filter groups
```

---

### 10. What is the CAP theorem (in simple terms)?
In a distributed database, when a network partition happens, you can guarantee **Consistency** (everyone sees the latest data) or **Availability** (every request gets a response) — but not both. So you design for CP (correctness, may reject requests) or AP (always answers, may be stale) depending on the workload. A bank balance wants CP; a "likes" counter is fine with AP.

---

### 11. What is pgvector?
A PostgreSQL extension that adds a `vector` data type and similarity-search indexes (HNSW, IVFFlat), letting you store embeddings and run nearest-neighbor search **inside** your relational database. That means RAG retrieval can join embeddings with normal columns and run in a real transaction — no separate vector service needed.

```sql
CREATE EXTENSION vector;
SELECT id FROM documents ORDER BY embedding <=> $1 LIMIT 5;  -- <=> = cosine distance
```

---

### 12. DELETE vs TRUNCATE vs DROP?
- **DELETE** removes rows (optionally with `WHERE`); logged per row, can be rolled back, keeps the table.
- **TRUNCATE** empties the whole table fast (minimal logging), keeps structure.
- **DROP** removes the table entirely (structure + data).

---

## Further Reading
- PostgreSQL tutorial: https://www.postgresql.org/docs/current/tutorial.html
- Use The Index, Luke: https://use-the-index-luke.com/
- Redis docs: https://redis.io/docs/latest/

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
