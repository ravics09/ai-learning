# OpenAI / Claude API — Use-Case Diagrams

> Mermaid diagrams for the patterns interviewers love to whiteboard. Each includes the *why* and key trade-offs.

---

## 1. Tool / function calling loop
The model plans, your code acts, repeat until done.

```mermaid
sequenceDiagram
    participant U as User
    participant M as Model
    participant App as Your code
    participant Ext as External APIs/DB
    U->>M: question
    loop until no tool calls (capped)
        M-->>App: tool_calls / tool_use
        App->>Ext: execute tool(s) (parallel if independent)
        Ext-->>App: results
        App-->>M: append tool results
    end
    M-->>U: final grounded answer
```
**Why:** connect the model to live data/actions. **Trade-off:** each round is a full model call — cap iterations and cache the prefix.

---

## 2. Streaming response (SSE)
Tokens flow to the client as they're produced.

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant API as Provider
    Client->>Gateway: request (stream=true)
    Gateway->>API: forward (buffering OFF)
    API-->>Gateway: delta: "Hel"
    Gateway-->>Client: delta: "Hel"
    API-->>Gateway: delta: "lo"
    Gateway-->>Client: delta: "lo"
    API-->>Gateway: [DONE] + usage
    Gateway-->>Client: close
```
**Why:** low time-to-first-token, better UX. **Trade-off:** must accumulate tool-arg fragments; handle mid-stream disconnects; disable proxy buffering.

---

## 3. Retry with backoff + failover
Absorb transient errors, then fall back across providers.

```mermaid
flowchart TB
    REQ[Request] --> A[Provider A]
    A -->|2xx| OK[Return]
    A -->|429/5xx/timeout| RA{Retries left?}
    RA -->|yes| WAIT[backoff * 2^n + jitter, honor Retry-After]
    WAIT --> A
    RA -->|no| B[Provider B - normalized request]
    B -->|2xx| OK
    B -->|fail| DEG[Degrade: smaller model / cache / safe message]
    A -->|4xx non-429| ERR[Fail fast - do not retry]
```
**Why:** resilience to throttling and outages. **Trade-off:** idempotency keys required so retries/failover don't double-charge.

---

## 4. Prompt caching
Reuse computed KV state for a stable prefix.

```mermaid
flowchart LR
    subgraph Prompt
      SYS[System prompt] --> TOOLS[Tool defs] --> DOC[Reference doc] --> DYN[User turn - dynamic]
    end
    SYS -.stable prefix.-> CACHE[(Cached KV)]
    TOOLS -.stable prefix.-> CACHE
    DOC -.stable prefix.-> CACHE
    CACHE -->|cheap read ~0.1x / faster TTFT| MODEL[Model]
    DYN -->|always recomputed| MODEL
```
**Why:** up to ~90% cheaper reads, big TTFT wins on repeated context. **Trade-off:** one changed byte early busts everything after it — keep prefix byte-stable, dynamic content last.

---

## 5. Multi-provider LLM gateway
One interface; providers become swappable config.

```mermaid
flowchart TB
    APP[App services] --> GW[LLM Gateway]
    GW --> AUTH[AuthN/Z + per-tenant quota]
    AUTH --> CACHE{Response / semantic cache}
    CACHE -->|hit| APP
    CACHE -->|miss| RL[Rate limiter RPM/TPM]
    RL --> RT[Router + normalizer]
    RT --> CB1[Breaker] --> OAI[OpenAI]
    RT --> CB2[Breaker] --> ANT[Anthropic]
    OAI --> OBS[(Metrics/traces/cost per tenant)]
    ANT --> OBS
```
**Why:** centralize auth, quotas, caching, routing, failover, telemetry. **Trade-off:** must normalize provider envelope differences (system prompt, tool results, structured output).

---

## 6. Cost-aware model routing
Cheap model for easy work; escalate only when needed.

```mermaid
flowchart TB
    Q[Incoming request] --> CL{Classifier / heuristics}
    CL -->|simple, short| SMALL[Haiku / mini - cheap]
    CL -->|complex / long / high-stakes| BIG[Frontier model]
    SMALL --> CHK{Confidence / quality OK?}
    CHK -->|no| BIG
    CHK -->|yes| OUT[Response]
    BIG --> OUT
```
**Why:** often 2–4× cost reduction with minimal quality loss. **Trade-off:** classifier adds latency/complexity; needs eval to tune the routing threshold.

---

## 7. Secure tool execution pipeline
Guard the highest-risk surface (tools + untrusted content).

```mermaid
flowchart TB
    M[Model tool call] --> V[Strict schema + business-rule validation]
    V -->|invalid| REJ[Reject]
    V -->|sensitive| HITL[Human / policy approval]
    V -->|safe| AUTHZ[Server-side authz check]
    AUTHZ --> SB[Sandboxed execution: egress + timeout limits]
    SB --> OUTF[Output filter: PII / secret redaction]
    OUTF --> LOG[(Audit log)]
```
**Why:** defend against indirect prompt injection and data exfiltration. **Trade-off:** approval/validation add latency for high-stakes actions — apply selectively.

---

## 8. Batch / async processing
High-throughput, latency-tolerant workloads at ~50% cost.

```mermaid
flowchart LR
    JOBS[Bulk inputs] --> Q[Queue]
    Q --> W[Workers: bounded concurrency + token-bucket]
    W --> BATCH[Batch API ~50% off]
    BATCH --> STORE[(Results store)]
    STORE --> DOWN[Downstream: index / report / notify]
```
**Why:** cheaper and rate-limit-friendly for embeddings, evals, bulk extraction. **Trade-off:** not for interactive use — results are async.

---

## 9. Sliding-window chat memory + summarization
Keep long chats affordable and within context limits.

```mermaid
flowchart TB
    NEW[New user turn] --> WIN[Recent N turns kept verbatim]
    OLD[Older turns] --> SUM[LLM summary - running context]
    SUM --> PROMPT[Prompt = system + summary + recent turns + new]
    WIN --> PROMPT
    PROMPT --> MODEL[Model]
```
**Why:** bounds token growth as conversations get long. **Trade-off:** summaries lose detail — keep IDs/facts that matter verbatim.

*Content synthesized from general domain knowledge and current (2025-2026) provider docs; rephrased for compliance with licensing restrictions.*
