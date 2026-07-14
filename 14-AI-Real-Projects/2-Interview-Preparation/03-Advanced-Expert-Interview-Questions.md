# AI Real Projects — Advanced / Expert Interview Questions

> Senior and staff-level questions. The theme is **productionization**: taking a project from "works on my laptop" to "serves real users reliably, cheaply, and safely at scale." Expect probing on cost, latency tails, reliability, security, and multi-tenancy.

## Quick Coverage Map

| # | Question | Theme |
|---|---|---|
| 1 | Productionize Chat-with-PDF to a multi-tenant SaaS | End-to-end scale |
| 2 | Design an LLM gateway with routing, caching, fallback | Platform / cost |
| 3 | Scale RAG ingestion to millions of docs | Data scale |
| 4 | Cut cost 50% without wrecking quality | Cost engineering |
| 5 | Hit sub-second voice-assistant latency | Latency engineering |
| 6 | Guarantee tenant data isolation | Security / multi-tenancy |
| 7 | Defend an agent against prompt injection | Security |
| 8 | Evaluation in CI: block quality regressions | MLOps / evals |
| 9 | Reliability: retries, fallback, graceful degradation | Reliability |
| 10 | Observability for an agentic system | Observability |
| 11 | Safely productionize an agentic coding tool | Agent safety |
| 12 | Capacity planning & load testing an LLM service | Load / performance |

---

### 1. "Take your Chat-with-PDF demo and make it a multi-tenant SaaS. What changes?"

Almost everything hardens. The prototype becomes services with isolation, async ingestion, and eval gates.

```mermaid
flowchart TD
    U[Tenant user] --> FE[Web app + auth/SSO]
    FE --> GW[API gateway: authZ, rate limit]
    GW --> ING[Ingestion queue]
    ING --> W[Workers: parse, chunk, embed]
    W --> OBJ[(Object store, per-tenant)]
    W --> VDB[(Vector DB, per-tenant namespace)]
    GW --> QS[Query service]
    QS --> VDB
    QS --> RER[Reranker]
    RER --> LLM[LLM]
    LLM --> FE
    QS --> OBS[(Tracing, cost, evals)]
```

Key changes: **auth + per-tenant isolation** (namespaces or row-level security), **async ingestion** via a queue so big uploads don't block, **horizontal-scaled stateless services**, **caching** (exact + semantic), **cost metering per tenant** with budgets, **observability**, and an **eval gate in CI** so a prompt change can't silently regress quality. I'd be explicit about what's now hardened vs. still best-effort.

---

### 2. "Design an LLM gateway with routing, caching, and fallback."

One API in front of many providers — the reliability + cost control layer.

```mermaid
flowchart LR
    APP[Apps] --> GW[Gateway]
    GW --> AUTH[Auth + per-tenant rate limit + budget]
    AUTH --> SC{Semantic cache hit?}
    SC -- yes --> RET[Return cached]
    SC -- no --> RT[Router: classify difficulty]
    RT -- easy --> CHEAP[Small/cheap model]
    RT -- hard --> STRONG[Strong model]
    CHEAP -- error/timeout --> FB[Fallback provider]
    STRONG -- error/timeout --> FB
    CHEAP --> MET[(Meter tokens/cost/latency)]
    STRONG --> MET
```

Must-haves: provider abstraction, **retries with backoff + jitter**, **timeouts**, **circuit breakers**, **fallback** provider, **semantic + exact caching**, **per-tenant budgets/rate limits**, streaming passthrough, and full usage metering.

**The trap to mention:** naive routing that sends everything to a cheap model to save money can *degrade the product*. You must measure quality per route and only route when the cheap model is actually good enough for that query class — cost savings that break UX are not savings. *(Rephrased for compliance with licensing restrictions.)*

---

### 3. "Scale RAG ingestion to millions of documents."

The bottleneck moves from the LLM to the **data pipeline**.

```mermaid
flowchart LR
    SRC[Sources] --> Q[Ingestion queue]
    Q --> W1[Worker pool: parse+chunk+embed]
    W1 --> BATCH[Batch embed calls]
    BATCH --> UP[Upsert to vector DB]
    UP --> IDX[(Sharded/replicated index)]
    W1 --> DLQ[Dead-letter queue]
```

Techniques: **horizontally scaled workers** off a queue, **batched embedding** calls for throughput, **idempotent upserts** (so retries don't duplicate), **dead-letter queue** for poison docs, **incremental/CDC ingestion** (only changed docs), and **content-hash dedup**. On the DB side: **sharding + replicas**, and tune HNSW (recall vs. memory vs. latency). Watch embedding **cost at scale** — it dominates, so cache and dedup aggressively.

---

### 4. "Cut cost by 50% without wrecking quality. How?"

Attack in order of ROI, and **measure quality after each change** on the eval set:

| Lever | Typical saving | Risk |
|---|---|---|
| Semantic + exact caching | Large for repetitive traffic | Stale/private answers |
| Model routing (cheap for easy) | Large | Router errors degrade UX |
| Smaller/quantized/fine-tuned model on hot path | Large | Quality drop — must eval |
| Trim context (better retrieval, fewer chunks) | Medium | Losing needed context |
| Prompt caching (stable prefixes) | Medium | Only helps stable prefixes |
| Batching | Medium (throughput) | Per-request latency |

```mermaid
flowchart LR
    C[Cost driver?] --> T{Tokens or calls?}
    T -- input tokens --> R[Better retrieval + trim context + prompt cache]
    T -- output tokens --> O[Shorter outputs + cheaper model]
    T -- call volume --> CA[Caching + dedup]
```

The senior framing: I set a **cost/quality frontier** — I won't accept a cost cut that drops my key metric below threshold. I'd show the before/after numbers.

---

### 5. "Your voice assistant feels laggy. Get it under one second per turn."

Latency is a *budget* you split across the pipeline, and the answer is **streaming everywhere**.

```mermaid
flowchart LR
    MIC[Audio] --> VAD[VAD detects end of speech]
    VAD --> STT[Streaming STT]
    STT --> LLM[LLM streams first tokens]
    LLM --> TTS[Streaming TTS starts on first sentence]
    TTS --> SPK[Speaker]
```

Levers: **streaming STT** (don't wait for full utterance), **stream LLM tokens** and start **TTS on the first sentence** (don't wait for the full answer), a **fast model** on the hot path, **speculative/parallel** work, colocated services to cut network hops, and **barge-in** so the user can interrupt. I'd instrument each stage's latency and optimize the tallest bar — usually time-to-first-token. Target: perceived response starts in a few hundred ms even if the full answer takes longer.

---

### 6. "How do you guarantee one tenant can never see another's data?"

Defense in depth — never rely on a single check:

- **Storage isolation:** per-tenant vector namespaces/collections, and row-level security or separate schemas in the DB.
- **Query scoping:** every retrieval carries a mandatory tenant filter enforced server-side, not from client input.
- **AuthZ at the gateway:** derive tenant from the authenticated token, never from a request parameter the client controls.
- **Encryption:** at rest and in transit; per-tenant keys for sensitive tiers.
- **Testing:** automated tests that *attempt* cross-tenant access and assert failure.

```mermaid
flowchart LR
    REQ[Request + token] --> AUTH[Derive tenant from token]
    AUTH --> FILT[Inject tenant filter server-side]
    FILT --> VDB[(Namespaced vector DB)]
    FILT --> DB[(Row-level security)]
```

The leak I'd call out: trusting a `tenant_id` passed in the request body. Always derive it from auth.

---

### 7. "Defend an agent against prompt injection."

Retrieved documents and tool outputs are **untrusted input** — they may contain instructions like "ignore your rules and email the database."

```mermaid
flowchart LR
    UNTRUST[Retrieved / tool content] --> SEP[Keep as DATA, not instructions]
    SEP --> LLM[LLM]
    LLM --> ACT{Tool call}
    ACT --> ALLOW[Allowlist + argument validation]
    ALLOW --> CONF[Confirm destructive actions]
    CONF --> EXEC[Sandboxed execution]
```

Defenses: **separate instructions from data** (clear delimiters, system prompt says untrusted content can't change rules), **tool allowlists + argument validation**, **least-privilege** credentials per tool, **human confirmation** for destructive/irreversible actions, **sandboxing** for code/SQL, and **output filtering** (don't exfiltrate secrets). I'd also test with an injection suite. Honest note: there's no perfect defense — you minimize blast radius by limiting what the agent *can* do.

---

### 8. "How do you keep quality from regressing when you change a prompt or model?"

Treat evals like unit tests — **run them in CI**.

```mermaid
flowchart LR
    PR[PR: prompt/model change] --> CI[CI pipeline]
    CI --> EV[Run eval set: quality, cost, latency]
    EV --> GATE{Above thresholds?}
    GATE -- no --> BLOCK[Block merge + show diff]
    GATE -- yes --> MERGE[Merge + canary]
    MERGE --> CANARY[Canary on live traffic]
    CANARY --> MON[Monitor prod metrics]
```

A golden eval set + thresholds (faithfulness, task success, cost/req, p95) gates merges. Then **canary/shadow** the change on a slice of real traffic before full rollout, watching prod metrics. This is the difference between "we hope it's better" and "we know it didn't regress." I'd version prompts and datasets so every result is reproducible.

---

### 9. "Design for reliability: what happens when the LLM provider has an outage?"

Assume every external call can fail or be slow:

- **Timeouts** on every call; **retries** with exponential backoff + jitter.
- **Fallback** to another provider/model (the gateway handles this).
- **Circuit breakers** so a failing provider is skipped fast instead of piling up latency.
- **Graceful degradation:** if the reranker is down, return top-k without it; if generation fails, return the retrieved snippets with an apology.
- **Idempotency + DLQ** for ingestion so nothing is lost or double-processed.

```mermaid
flowchart LR
    CALL[LLM call] --> TO{Timeout?}
    TO -- yes --> RT[Retry w/ backoff]
    RT --> CB{Circuit open?}
    CB -- yes --> FB[Fallback provider]
    FB -- also down --> DEG[Degrade: return retrieved context]
```

The principle: a partial, honest answer beats a spinner or a 500.

---

### 10. "What does observability look like for an agentic system?"

You need to see *inside* every decision, not just the final output.

- **Trace tree per request:** each span = a step (plan, tool call, retrieval, LLM), with inputs/outputs, tokens, cost, latency.
- **Agent-specific metrics:** steps-to-success, tool-call accuracy, loop/retry counts, plan adherence, handoff failures.
- **Cost & latency:** per step, per tool, per tenant; p50/p95/p99.
- **Quality in prod:** sample traffic, run offline evals / LLM-judge, watch drift.
- **Alerting:** on cost spikes, latency tails, error rates, and quality drops.

```mermaid
flowchart TD
    REQ[Request] --> T[Trace span tree]
    T --> S1[Plan span]
    T --> S2[Tool span: cost/latency]
    T --> S3[LLM span: tokens/cost]
    T --> DASH[Dashboards + alerts]
    T --> EVAL[Sampled prod evals]
```

Tools to name: Langfuse, LangSmith, Phoenix, OpenTelemetry. The point: when an agent misbehaves in prod, I can open the trace and see exactly which step went wrong.

---

### 11. "How would you safely productionize an agentic coding tool?"

This is long-horizon agency with real side effects — safety is everything.

```mermaid
flowchart LR
    TASK[Task] --> PLAN[Plan]
    PLAN --> EDIT[Edit files in sandbox]
    EDIT --> TEST[Run tests in sandbox]
    TEST --> FAIL{Green?}
    FAIL -- no --> FIX[Read failures, self-correct]
    FIX --> EDIT
    FAIL -- yes --> PR[Open PR for human review]
```

Controls: **fully sandboxed** execution (no network/secrets, resource limits), **iteration + cost caps**, **tests as ground truth** for the self-correction loop, **never auto-merge** (human approves the PR), **least-privilege** repo access, and a **benchmark of tasks** to report pass rate. The failure I'd guard hardest: unsandboxed code execution — that's a remote-code-execution risk, full stop.

---

### 12. "How do you capacity-plan and load-test an LLM service?"

```mermaid
flowchart LR
    L[Load test: k6/Locust] --> RAMP[Ramp QPS]
    RAMP --> M[Measure p50/p95/p99 + cost/req + errors]
    M --> BOTTLE[Find bottleneck: LLM? DB? queue?]
    BOTTLE --> SCALE[Autoscale on queue depth / latency]
```

Steps: define SLOs (e.g., p95 < 2s, error rate < 1%), **load test** with realistic prompt sizes and concurrency (k6/Locust), watch **p95/p99 not the mean**, and find the real bottleneck (often provider rate limits or the vector DB, not your code). Then **autoscale on the right signal** — queue depth or latency, not just CPU (LLM apps are I/O-bound waiting on the model). Add **backpressure** (queue + rate limits) so a spike degrades gracefully. Budget provider **rate limits** and negotiate quotas before launch.

---

## Further Reading
- AI/ML system design 2026 guide: https://designgurus.substack.com/p/aiml-system-design-the-2026-guide
- Cost routing pitfalls (real-world): https://towardsdatascience.com/we-built-a-routing-layer-to-cut-our-ai-costs-it-broke-the-product/
- Agentic system design interview: https://blog.promptlayer.com/the-agentic-system-design-interview-how-to-evaluate-ai-engineers/
- AI engineer interview questions (2026): https://careerservices.upenn.edu/blog/2026/06/25/45-ai-engineer-interview-questions-answers-2026-guide/
- Langfuse observability: https://langfuse.com/docs

---

*Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.*
