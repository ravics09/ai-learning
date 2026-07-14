# AI Real Projects — Use-Case & Architecture Diagrams

> Flagship project architectures as Mermaid diagrams you can reproduce on a whiteboard. Each has a short "what to say" note so you can narrate it in an interview. Draw the diagram, then talk through the data flow, the key decision, and the failure mode.

---

## 1. Chat-with-your-PDF (RAG)

```mermaid
flowchart TD
    subgraph Ingestion (offline)
      P[PDF upload] --> LD[Load + extract text]
      LD --> CH[Chunk with overlap]
      CH --> EM[Embed chunks]
      EM --> VDB[(Vector store)]
    end
    subgraph Query (online)
      U[User question] --> QE[Embed query]
      QE --> SR[Top-k similarity search]
      VDB --> SR
      SR --> RR[Rerank (optional)]
      RR --> CB[Build context + citations]
      CB --> LLM[LLM: answer only from context]
      LLM --> ANS[Answer + page citations]
      LLM -.no good context.-> IDK[I don't know / closest section]
    end
```
**What to say:** "Two phases. Ingestion is offline; query is online. The key decision was grounding strictly and citing pages, plus an 'I don't know' path so retrieval misses don't become hallucinations. Adding the reranker moved faithfulness from 0.82 to 0.91."

---

## 2. Customer Support Bot (RAG + actions + handoff)

```mermaid
flowchart TD
    U[Customer message] --> G[Guardrails: PII + injection]
    G --> SC{In scope?}
    SC -- no --> H[Human handoff]
    SC -- yes --> INT{Intent}
    INT -- FAQ --> R[RAG over knowledge base]
    INT -- action --> T[Tool: create ticket / order status]
    R --> CF{Confident?}
    T --> LLM[LLM composes reply]
    CF -- no --> H
    CF -- yes --> LLM
    LLM --> REPLY[Reply + citation]
    LLM --> OBS[(Trace: tool calls, cost, deflection)]
```
**What to say:** "The bot blends retrieval with actions. The safety net is a confidence gate plus a scope check that routes to a human. I measure deflection rate alongside a quality check, so it can't 'win' by answering everything badly."

---

## 3. Multi-Agent Research Assistant

```mermaid
flowchart TD
    Q[Research question] --> O[Orchestrator / Planner]
    O --> SA[Search agent]
    O --> AA[Analysis agent]
    SA --> SRC[(Web / docs / vector store)]
    AA --> SRC
    SA --> W[Writer agent]
    AA --> W
    W --> CR[Critic / verifier agent]
    CR -- claims unsupported --> W
    CR -- verified --> REP[Report + citations]
    O --> BUD[[Shared token/cost budget]]
    O --> MEM[(Shared memory/state)]
```
**What to say:** "A planner decomposes the task and delegates to specialized agents. The critic verifies claims against sources to cut hallucination. A shared cost budget stops the agents from talking in circles and blowing the bill — the main risk with multi-agent."

---

## 4. LLM Gateway / Router (platform)

```mermaid
flowchart LR
    APP[Client apps] --> GW[Gateway API]
    GW --> AUTH[Auth + per-tenant rate limit + budget]
    AUTH --> CACHE{Semantic / exact cache hit?}
    CACHE -- hit --> RET[Return cached]
    CACHE -- miss --> RT[Router: classify difficulty]
    RT -- easy --> M1[Cheap model]
    RT -- hard --> M2[Strong model]
    M1 -- error/timeout --> FB[Fallback provider]
    M2 -- error/timeout --> FB
    M1 --> MET[(Meter tokens/cost/latency)]
    M2 --> MET
    FB --> MET
    MET --> RESP[Response + usage headers]
```
**What to say:** "One API in front of many providers: caching, routing by difficulty, retries, circuit breakers, fallback, and per-tenant budgets. The trap I call out is that naive routing to cheap models can degrade the product — so I measure quality per route, not just cost."

---

## 5. SQL Analytics Agent (text-to-SQL)

```mermaid
flowchart TD
    Q[NL question] --> SCH[Fetch schema + few-shot examples]
    SCH --> GEN[LLM generates SQL]
    GEN --> V1[Parse: SELECT-only]
    V1 --> V2[Allowlist tables/columns]
    V2 --> V3[Force LIMIT + timeout]
    V3 -- unsafe --> REJ[Reject / repair]
    V3 -- safe --> RUN[Run on read-only replica]
    RUN --> ERR{DB error?}
    ERR -- yes --> FIX[Feed error back → regenerate]
    FIX --> GEN
    ERR -- no --> NL[LLM explains result]
    NL --> OUT[Answer + the SQL used]
```
**What to say:** "Schema-aware generation, then layered safety: SELECT-only parsing, table allowlist, forced LIMIT, and a read-only replica. The self-correction loop stays inside those guardrails. I also surface the SQL so users can trust the answer."

---

## 6. Production RAG SaaS (multi-tenant, end-to-end)

```mermaid
flowchart TD
    U[Tenant user] --> FE[Web app + auth/SSO]
    FE --> GW[API gateway: authZ, rate limit]
    GW --> INGQ[Ingestion queue]
    INGQ --> WK[Workers: parse, chunk, embed]
    WK --> OBJ[(Object store, per-tenant)]
    WK --> VDB[(Vector DB, per-tenant namespace)]
    GW --> QS[Query service]
    QS --> VDB
    QS --> RER[Reranker]
    RER --> LLM[LLM]
    LLM --> FE
    QS --> OBS[(Tracing / cost / evals)]
    CI[CI pipeline] --> EVG[Eval gate blocks regressions]
    EVG --> QS
```
**What to say:** "The demo hardens into services: async ingestion so uploads don't block, per-tenant isolation via namespaces, an eval gate in CI so prompt changes can't silently regress quality, and cost metering per tenant. Tenant isolation is derived from the auth token, never from request params."

---

## 7. Voice Assistant (real-time, streaming)

```mermaid
flowchart LR
    MIC[Mic audio] --> VAD[VAD: detect end of speech]
    VAD --> STT[Streaming speech-to-text]
    STT --> LLM[LLM + tools/RAG, streams tokens]
    LLM --> TTS[Streaming TTS on first sentence]
    TTS --> SPK[Speaker]
    U[User interrupts] --> BARGE[Barge-in handler]
    BARGE --> LLM
    LLM --> LAT[(Per-stage latency budget)]
```
**What to say:** "Latency is a budget split across stages. Everything streams — STT, LLM tokens, and TTS starts on the first sentence — so the turn feels sub-second even if the full answer takes longer. Barge-in lets the user interrupt, which is essential for natural voice UX."

---

## 8. Agentic Coding Tool (sandboxed self-correction)

```mermaid
flowchart TD
    TASK[Task / issue] --> IDX[Index repo]
    IDX --> PLAN[Planner]
    PLAN --> EDIT[Edit files in sandbox]
    EDIT --> TEST[Run tests in sandbox]
    TEST --> GREEN{Tests pass?}
    GREEN -- no --> READ[Read failures]
    READ --> EDIT
    GREEN -- yes --> PR[Open PR for human review]
    EDIT --> LIM[[Iteration + cost caps]]
    TEST --> SBX[[Sandbox: no secrets/network]]
```
**What to say:** "Tests are the ground truth for the self-correction loop. Everything runs in a locked-down sandbox — no network, no secrets, resource caps — and it never auto-merges; a human approves the PR. The biggest risk to guard is unsandboxed code execution."

---

## 9. Semantic Search Engine (hybrid + rerank)

```mermaid
flowchart LR
    C[Corpus] --> IDX1[BM25 keyword index]
    C --> IDX2[Embed → vector index]
    Q[Query] --> K[Keyword search]
    Q --> V[Vector search]
    IDX1 --> K
    IDX2 --> V
    K --> FUSE[Fuse scores (RRF)]
    V --> FUSE
    FUSE --> RER[Cross-encoder rerank]
    RER --> RES[Ranked results + filters]
```
**What to say:** "Hybrid retrieval fuses keyword and vector results (reciprocal rank fusion), then a cross-encoder reranks the top candidates. I report Recall@k and MRR versus pure keyword search to prove the hybrid approach actually helps."

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
