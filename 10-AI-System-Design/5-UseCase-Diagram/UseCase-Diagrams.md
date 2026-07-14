# AI System Design — Use-Case & Architecture Diagrams

> Mermaid architecture diagrams for the worked designs plus a generic reference architecture. Use these to practice sketching fast on a whiteboard.

---

## 0. Generic Reference Architecture (memorize this shape)
```mermaid
flowchart LR
    U[Client] --> GW[API Gateway<br/>auth, rate limit, routing]
    GW --> ORCH[Orchestrator<br/>stateless]
    ORCH --> CACHE[(Cache:<br/>exact + semantic)]
    ORCH --> RET[Retrieval]
    RET --> VDB[(Vector DB)]
    RET --> RR[Reranker]
    ORCH --> GRD[Guardrails]
    GRD --> LLM[Inference layer<br/>managed API / vLLM + fallback]
    ORCH --> Q[Queue<br/>async jobs]
    ORCH --> OBS[Observability<br/>traces, tokens, cost, evals]
    subgraph Offline
      ING[Ingestion] --> CH[Chunk] --> EMB[Embed] --> VDB
    end
```

---

## 1. Support Chatbot over Docs (RAG)
```mermaid
flowchart LR
    U[Web widget] --> GW[Gateway<br/>auth + rate limit]
    GW --> ORCH[Chat orchestrator]
    ORCH --> SC[(Semantic cache)]
    ORCH --> RET[Hybrid retrieve]
    RET --> VDB[(Vector DB<br/>tenant-filtered)]
    RET --> RR[Reranker]
    ORCH --> GRD[Guardrails]
    GRD --> LLM[LLM API + fallback]
    ORCH --> ESC{Low confidence?}
    ESC -- yes --> HUM[Human handoff]
    subgraph Ingestion
      DOC[Docs / KB] --> CHK[Chunk + overlap] --> EMB[Embed] --> VDB
    end
    ORCH --> OBS[Traces + cost + evals]
```

---

## 2. Code Assistant (Copilot-like)
```mermaid
flowchart LR
    IDE[IDE plugin] --> GW[Gateway]
    GW --> COMP[Completion service]
    COMP --> KV[(Prefix / KV cache)]
    COMP --> FIM[Small fast model<br/>fill-in-the-middle]
    IDE --> CHAT[Chat service]
    CHAT --> RET[Repo retrieval]
    RET --> CVDB[(Code vector index)]
    CHAT --> BIG[Large model]
    COMP --> OBS[Accept rate + latency]
    CHAT --> OBS
```

---

## 3. Semantic Search at Scale (500M docs)
```mermaid
flowchart LR
    Q[Query] --> GW[Gateway]
    GW --> QE[Embed + analyze query]
    QE --> HS[Hybrid search]
    HS --> BM[BM25 / keyword]
    HS --> ANN[(ANN vector shards<br/>HNSW / IVF-PQ)]
    BM --> FUSE[Fusion RRF]
    ANN --> FUSE
    FUSE --> RR[Rerank top-100<br/>cross-encoder]
    RR --> RES[Results]
    subgraph Indexing
      SRC[Docs] --> EMB[Batch embed] --> IDX[Build + replicate]
      IDX --> ANN
    end
```

---

## 4. Multi-Tenant RAG SaaS
```mermaid
flowchart TD
    subgraph Request Path
      U[Tenant user] --> GW[Gateway<br/>authz + tenant_id + quota]
      GW --> ORCH[Orchestrator]
      ORCH --> RET[Retrieve<br/>filter by tenant_id]
      RET --> VDB[(Vector DB<br/>per-tenant namespace)]
      ORCH --> LLMGW[LLM gateway<br/>routing + fallback]
      ORCH --> METER[Token metering<br/>per tenant]
    end
    subgraph Ingestion
      UP[Upload] --> Q[Queue] --> W[Worker: parse+chunk+embed] --> VDB
    end
    METER --> BILL[Billing]
    ORCH --> OBS[Per-tenant traces/cost/evals]
```

---

## 5. LLM Gateway
```mermaid
flowchart TD
    APP[Internal apps / agents] --> GW[LLM Gateway]
    GW --> AUTH[Auth + per-team quota/budget]
    GW --> CACHE[(Exact + semantic cache)]
    GW --> ROUTE{Router}
    ROUTE -->|cheap/easy| M1[Small model]
    ROUTE -->|hard/quality| M2[Large model]
    ROUTE -->|provider down| M3[Fallback provider]
    GW --> GRD[Guardrails: moderation, PII, injection]
    GW --> OBS[Central logs, traces, token+cost metering]
```

---

## 6. Agent Platform with Tools
```mermaid
flowchart TD
    U[User / app] --> AG[Agent loop]
    AG --> PLAN[Plan / reason]
    PLAN --> TOOL[Tool call<br/>sandboxed, allow-listed]
    TOOL --> OBSV[Observe result]
    OBSV --> AG
    AG --> MEM[(Memory / state)]
    AG --> LLMGW[LLM gateway]
    AG --> GUARD{Risky action?}
    GUARD -- yes --> HIL[Human approval]
    AG --> TRACE[Full step trace<br/>tokens + budget caps]
```

---

## 7. Self-Hosted Inference Service
```mermaid
flowchart LR
    REQ[Requests] --> LB[Load balancer]
    LB --> SRV[Serving engine<br/>vLLM / TGI]
    SRV --> CB[Continuous batching]
    CB --> KV[(Paged KV cache)]
    SRV --> SPEC[Speculative decoding<br/>draft + verify]
    SRV --> GPU[(GPU fleet<br/>autoscaled)]
    SRV --> M[Metrics: tokens/s, queue time, util]
```

---

## 8. Real-Time Voice Assistant
```mermaid
flowchart LR
    MIC[Mic] --> STT[Streaming STT]
    STT --> LLM[LLM streaming<br/>+ optional RAG]
    LLM --> TTS[Streaming TTS]
    TTS --> SPK[Speaker]
    BARGE{User interrupts?} -.cancel.-> LLM
    SPK --> BARGE
```

---

## 9. Guardrails / Moderation Pipeline
```mermaid
flowchart LR
    IN[User input] --> IMOD[Input moderation]
    IMOD --> PII[PII redaction]
    PII --> INJ[Injection detection]
    INJ --> LLM[Model]
    LLM --> OMOD[Output moderation]
    OMOD --> VAL[Schema + groundedness validation]
    VAL --> OUT[Safe response]
    IMOD -. block .-> REJ[Reject / safe fallback]
    OMOD -. block .-> REJ
```

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
