# RAG — Use Case Diagrams

> Visual architectures for common RAG use cases. GitHub renders Mermaid automatically, so these display as diagrams. Each includes the problem, the flow, and the key design notes an interviewer will probe.

---

## 1. Customer Support Assistant (classic RAG)

**Problem:** Customers ask repetitive questions; a plain LLM doesn't know company policies.

```mermaid
flowchart TB
    C[Customer] --> UI[Chat widget]
    UI --> COND[Condense to standalone query]
    COND --> HS[Hybrid retrieve: help articles]
    HS --> RR[Rerank]
    RR --> LLM[LLM answer with citations]
    LLM --> ESC{Confident?}
    ESC -->|yes| C
    ESC -->|no| AGENT[Escalate to human agent]
    subgraph KB [Knowledge base - synced nightly]
        DOCS[Help center + policies] --> IDX[(Vector + BM25 index)]
    end
    IDX -.-> HS
```

**Design notes:** conversation condensation for follow-ups; escalation path on low confidence; nightly re-index; citations link to help articles.

---

## 2. Enterprise Knowledge Assistant (multi-tenant, secured)

**Problem:** Employees want to search across wikis, Slack, Drive — but only what they're allowed to see.

```mermaid
flowchart TB
    E[Employee] --> AUTH[SSO / auth]
    AUTH --> Q[Query + user ACL]
    Q --> FILT[Pre-filter: tenant_id + access_level]
    FILT --> RET[Retrieve authorized chunks only]
    RET --> RR[Rerank]
    RR --> LLM[LLM answer + citations]
    LLM --> AUD[(Audit log)]
    LLM --> E
    subgraph Sources
        W[Wiki] --> ING[Ingestion + ACL metadata]
        SL[Slack] --> ING
        DR[Drive] --> ING
        ING --> DB[(Vector index w/ ACL metadata)]
    end
    DB -.-> RET
```

**Design notes:** ACL pre-filtering inside the query (never post-filter); per-source connectors capture permissions; full audit trail for compliance.

---

## 3. Contextual RAG with Reranking (high-accuracy pipeline)

**Problem:** Naive top-5 vector search misses or misranks the right chunk.

```mermaid
flowchart LR
    subgraph Index
        D[Doc] --> CH[Chunk]
        CH --> CTX[LLM adds chunk context]
        CTX --> EMB[Embed]
        EMB --> V[(Vector)]
        CH --> KW[(BM25)]
    end
    Q[Query] --> DE[Dense top-50]
    Q --> SP[BM25 top-50]
    DE --> RRF[RRF fusion]
    SP --> RRF
    RRF --> CE[Cross-encoder rerank]
    CE --> TOP[Top 3-5]
    TOP --> GEN[Generate + cite]
    V -.-> DE
    KW -.-> SP
```

**Design notes:** contextual chunks + hybrid + RRF + cross-encoder reranking is the current high-accuracy default (largest measured accuracy lifts).

---

## 4. Agentic RAG (multi-source, self-correcting)

**Problem:** Complex questions need multiple sources and iterative retrieval.

```mermaid
flowchart TB
    Q[Complex query] --> PLAN[Agent: plan sub-questions]
    PLAN --> ROUTE{Pick tool}
    ROUTE --> VDB[Vector DB]
    ROUTE --> SQL[SQL analytics]
    ROUTE --> WEB[Web search]
    ROUTE --> API[Internal API]
    VDB --> GRADE[Grade relevance]
    SQL --> GRADE
    WEB --> GRADE
    API --> GRADE
    GRADE -->|insufficient| PLAN
    GRADE -->|sufficient| SYN[Synthesize + cite]
    SYN --> ANS[Answer]
```

**Design notes:** add step budget, timeout, and tracing to prevent loops and runaway cost; grading step = Corrective/Self-RAG idea.

---

## 5. GraphRAG (relational / multi-hop questions)

**Problem:** "How are our vendors connected to last year's outages?" — needs relationships, not isolated chunks.

```mermaid
flowchart TB
    subgraph Build
        DOCS[Documents] --> EXT[LLM extracts entities + relations]
        EXT --> KG[(Knowledge graph)]
        KG --> COMM[Community detection + summaries]
    end
    Q[Global/multi-hop query] --> TRAV[Traverse subgraph]
    TRAV --> SUM[Gather community summaries]
    SUM --> GEN[LLM synthesizes]
    GEN --> A[Comprehensive answer]
    KG -.-> TRAV
    COMM -.-> SUM
```

**Design notes:** best comprehensiveness for entity-rich/global queries; ~2.3–2.4× latency and heavy build cost — reserve for questions vector RAG can't answer.

---

## 6. Production RAG SaaS (full system, at scale)

**Problem:** Serve many tenants, high QPS, with cost/latency control and observability.

```mermaid
flowchart TB
    U[Clients] --> GW[API Gateway: auth, rate limit, quota]
    GW --> CACHE{Semantic cache}
    CACHE -->|hit| U
    CACHE -->|miss| RS[Retrieval service - autoscaled]
    RS --> ROUTER{Query complexity}
    ROUTER -->|simple| SMALL[Small/cheap LLM]
    ROUTER -->|hard| BIG[Frontier LLM + fallback]
    RS --> VDB[(Sharded + replicated vector DB)]
    RS --> BM[(BM25)]
    VDB --> RR[Reranker GPU pool]
    BM --> RR
    RR --> ROUTER
    SMALL --> OBS[Observability: traces, cost, evals]
    BIG --> OBS
    OBS --> U
    subgraph Ingest [Async ingestion]
        SRC[Sources] --> Kq[Queue] --> EW[Embed workers] --> VDB
    end
```

**Design notes:** semantic cache first; model routing for cost; sharded/replicated index; async ingestion; end-to-end observability + online evals; provider fallback for reliability.

---

## 7. Multimodal RAG (docs with images/tables)

**Problem:** Answers live in diagrams, scanned invoices, or tables — not plain text.

```mermaid
flowchart LR
    subgraph Ingest
        PDF[PDF/scan] --> SPLIT[Split text / images / tables]
        SPLIT --> TE[Text embed]
        SPLIT --> IE[Image embed / VLM summary]
        SPLIT --> TAB[Table -> markdown]
        TE --> V[(Multimodal index)]
        IE --> V
        TAB --> V
    end
    Q[Query] --> RET[Retrieve text+image chunks]
    RET --> VLM[Vision-language model]
    VLM --> A[Answer referencing figures]
    V -.-> RET
```

**Design notes:** use multimodal embeddings or summarize images/tables into text; answer with a VLM; cite the specific figure/page.

---

## Choosing a pattern (quick guide)

```mermaid
flowchart TD
    S[Start] --> Q1{Relational / multi-hop?}
    Q1 -->|yes| G[GraphRAG]
    Q1 -->|no| Q2{Multiple sources / iterative?}
    Q2 -->|yes| AG[Agentic RAG]
    Q2 -->|no| Q3{Accuracy critical?}
    Q3 -->|yes| CR[Contextual + hybrid + rerank]
    Q3 -->|no| B[Basic RAG]
```

*Diagrams synthesized from general domain knowledge and current best practices; rephrased for compliance with licensing restrictions.*
