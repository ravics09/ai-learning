# Databases — Use-Case Diagrams

> Mermaid diagrams for the database patterns that come up most in AI/backend system design. Each has a one-line "why" and "when."

---

## 1. Read replicas (scale reads + HA)
**Why:** most workloads are read-heavy; replicas absorb reads and provide failover.
**When:** read/write ratio is high and some replica lag (stale reads) is acceptable.

```mermaid
flowchart LR
    App --> Pool[PgBouncer]
    Pool -->|writes + read-your-writes| P[(Primary)]
    Pool -->|reads| R1[(Replica 1)]
    Pool -->|reads| R2[(Replica 2)]
    P -. WAL stream .-> R1
    P -. WAL stream .-> R2
```

---

## 2. Sharding (scale writes)
**Why:** one primary can't hold the write volume/data set.
**When:** writes exceed a single node; you can pick a shard key that spreads load and co-locates related rows.

```mermaid
flowchart TD
    App --> Router{Shard router\nhash(tenant_id)}
    Router -->|shard 0| S0[(DB 0 primary+replica)]
    Router -->|shard 1| S1[(DB 1 primary+replica)]
    Router -->|shard 2| S2[(DB 2 primary+replica)]
    S0 & S1 & S2 --> Agg[Scatter-gather only when unavoidable]
```

---

## 3. Caching layer (cache-aside)
**Why:** cut latency and DB load for repeated reads.
**When:** hot, read-heavy keys where bounded staleness is fine.

```mermaid
sequenceDiagram
    participant App
    participant Redis
    participant DB
    App->>Redis: GET key
    alt hit
        Redis-->>App: value (fast)
    else miss
        App->>DB: query
        DB-->>App: rows
        App->>Redis: SET key value EX ttl
    end
    Note over App,DB: On write: UPDATE DB then DEL key (invalidate)
```

---

## 4. Semantic cache for an LLM
**Why:** paraphrased prompts never match a byte-exact cache; match on *meaning* to skip model calls.
**When:** high volume of similar questions; correctness policy + threshold in place.

```mermaid
flowchart LR
    Q[User query] --> E[Embed]
    E --> V{ANN search top-1\nsim >= threshold?}
    V -->|hit + policy ok| C[Return cached answer\n~tens of ms, no model call]
    V -->|miss| L[Call LLM]
    L --> G[Guardrail/validate]
    G --> St[(Store embedding + answer\nscoped by tenant/context, TTL)]
    St --> Ret[Return answer]
```

---

## 5. pgvector RAG store
**Why:** keep embeddings next to relational data — real joins, real transactions, one backup story.
**When:** under ~10M vectors; want hybrid (filter + similarity) queries without a separate service.

```mermaid
flowchart LR
    Doc[Documents] --> Chunk[Chunk] --> Emb[Embed]
    Emb --> PG[(PostgreSQL + pgvector\nHNSW index)]
    Query[User question] --> QE[Embed query]
    QE --> PG
    PG -->|WHERE tenant=? ORDER BY embedding <=> q LIMIT k| Ctx[Top-k chunks]
    Ctx --> Prompt[Build prompt] --> LLM[LLM] --> Ans[Answer]
```

---

## 6. Chat-history schema (conversation state)
**Why:** LLM apps need durable, session-scoped memory.
**When:** any assistant/agent that must recall prior turns across requests.

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : has
    CONVERSATIONS ||--o{ MESSAGES : contains
    USERS {
        bigint id PK
        citext email
    }
    CONVERSATIONS {
        uuid id PK
        bigint user_id FK
        timestamptz created_at
    }
    MESSAGES {
        bigserial id PK
        uuid conversation_id FK
        text role
        text content
        timestamptz created_at
    }
```

---

## 7. SQL-vs-NoSQL selection
**Why:** pick the store by access pattern and guarantees, not hype.
**When:** every new service — start here.

```mermaid
flowchart TD
    Q{Complex relationships +\nstrong consistency?} -->|yes| SQL[(Relational / PostgreSQL)]
    Q -->|no| A{Access pattern?}
    A -->|single-key hot reads| KV[(Key-Value / Redis)]
    A -->|flexible documents| DOC[(Document / MongoDB)]
    A -->|write-heavy, huge scale| WC[(Wide-column / Cassandra)]
    A -->|graph traversal| G[(Graph / Neo4j)]
    A -->|similarity search| VEC[(Vector / pgvector)]
```

---

## 8. Feature store (offline + online)
**Why:** serve identical features to training and inference to kill training/serving skew.
**When:** production ML with both batch training and low-latency inference.

```mermaid
flowchart LR
    Raw[Raw events] --> T[Single feature transform]
    T --> Off[(Offline store\nwarehouse - training)]
    T --> On[(Online store\nRedis/DynamoDB - serving)]
    Off -->|point-in-time joins| Train[Model training]
    On -->|ms reads| Infer[Real-time inference]
```

---

## 9. Multi-region failover (CP-leaning)
**Why:** survive a regional outage without data loss.
**When:** availability-critical services that can tolerate a promotion + short redirect.

```mermaid
flowchart TD
    subgraph Region A
    PA[(Primary)]
    end
    subgraph Region B
    RB[(Sync/Async Replica)]
    end
    PA -. replicate .-> RB
    Mon[Consensus/Patroni] -->|primary down| Promote[Promote Region B]
    Promote --> RB
    App --> Proxy[Write endpoint proxy] --> PA
    Proxy -. after failover .-> RB
```

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
