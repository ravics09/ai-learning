# LLMs — Use Case Diagrams

> Visual architectures for how LLMs are used and served in production. Mermaid renders automatically on GitHub. Each diagram includes the problem and the design notes interviewers probe.

---

## 1. LLM Inference Loop (what happens per request)

```mermaid
flowchart LR
    P[Prompt tokens] --> PRE[Prefill: parallel, compute-bound -> TTFT]
    PRE --> KV[(KV cache)]
    KV --> DEC[Decode: one token at a time, memory-bound -> TPOT]
    DEC --> SAMP[Sample: temp / top-p]
    SAMP --> DEC
    DEC --> OUT[Streamed output]
```

**Notes:** prefill vs decode have different bottlenecks; stream tokens for low perceived latency; KV cache reuse makes decode fast.

---

## 2. Attention Variants (KV-cache trade-off)

```mermaid
flowchart TB
    MHA[MHA: each head own K/V - largest cache, best quality] --> MQA
    MQA[MQA: all heads share 1 K/V - tiny cache, quality drop] --> GQA
    GQA[GQA: grouped K/V - balanced, open-model default] --> MLA
    MLA[MLA: low-rank latent K/V - very small cache, DeepSeek]
```

**Notes:** the industry moved MHA → GQA → MLA to shrink the KV cache because decode is memory-bandwidth-bound.

---

## 3. Training / Post-training Pipeline

```mermaid
flowchart LR
    DATA[Trillions of tokens] --> PT[Pretraining: next-token]
    PT --> BASE[Base model]
    BASE --> SFT[SFT: instruction/chat pairs]
    SFT --> DPO[Preference alignment: DPO/RLHF]
    DPO --> RLVR[RLVR + GRPO: verifiable rewards]
    RLVR --> CHAT[Aligned reasoning model]
```

**Notes:** each stage adds capability; DPO simplified preference alignment; RLVR/GRPO produce reasoning.

---

## 4. Production LLM Serving Stack

```mermaid
flowchart TB
    U[Clients] --> GW[Gateway: auth, rate limit]
    GW --> CACHE{Prompt/semantic cache}
    CACHE -->|hit| U
    CACHE -->|miss| LB[Load balancer]
    LB --> R1[vLLM replica 1]
    LB --> R2[vLLM replica 2]
    R1 --> PA[(PagedAttention KV cache)]
    R1 --> CB[Continuous batching]
    R1 --> SD[Speculative decoding]
    R1 --> OBS[Observability: tokens, latency, cost]
    OBS --> U
```

**Notes:** continuous batching + PagedAttention for throughput; caching + speculative decoding for latency/cost; full observability.

---

## 5. Multi-LoRA Serving (many tenants, one base model)

```mermaid
flowchart TB
    REQ[Request + tenant_id] --> ROUTER[Adapter router]
    ROUTER --> BASE[Shared base model on GPU]
    A1[(Tenant A LoRA)] -.-> BASE
    A2[(Tenant B LoRA)] -.-> BASE
    A3[(Tenant C LoRA)] -.-> BASE
    BASE --> OUT[Tenant-specific output]
```

**Notes:** one resident base + thousands of few-MB adapters swapped per request → cheap customization at scale.

---

## 6. LLM Gateway (routing, fallback, cost control)

```mermaid
flowchart TB
    APP[App] --> GATE[LLM Gateway - LiteLLM style]
    GATE --> CLASS{Query complexity / policy}
    CLASS -->|simple| CHEAP[Small/cheap model]
    CLASS -->|hard| FRONTIER[Frontier API]
    CLASS -->|sensitive| SELF[Self-hosted open model]
    CHEAP --> FB[Fallback on error/timeout]
    FRONTIER --> FB
    SELF --> FB
    FB --> LOG[Cost + usage logging]
    LOG --> APP
```

**Notes:** model routing cuts cost; fallback handles provider outages; sensitive data routed to self-hosted for compliance.

---

## 7. Tool-Calling / Agent Loop

```mermaid
flowchart TB
    Q[User request] --> LLM[LLM decides]
    LLM --> D{Tool needed?}
    D -->|yes| TOOL[Call tool: search / code / DB]
    TOOL --> SB[Sandbox + validate output]
    SB --> LLM
    D -->|no| ANS[Final answer]
    LLM --> BUDGET{Step/cost budget left?}
    BUDGET -->|no| STOP[Stop / escalate]
```

**Notes:** least-privilege tools, sandbox execution, step/cost budgets to prevent loops and runaway spend (excessive agency risk).

---

## 8. Structured Output Extraction

```mermaid
flowchart LR
    TXT[Unstructured text] --> LLM[LLM + JSON schema]
    LLM --> VAL{Valid schema?}
    VAL -->|no| RETRY[Repair / retry]
    RETRY --> LLM
    VAL -->|yes| JSON[Validated JSON]
    JSON --> DB[(Downstream system)]
```

**Notes:** enforce schema via structured outputs / function calling / constrained decoding; validate + auto-retry (Instructor/Pydantic).

---

## 9. Deployment Decision: API vs Self-Hosted

```mermaid
flowchart TD
    S[Start] --> Q1{Strict data residency / compliance?}
    Q1 -->|yes| SELF[Self-host open model]
    Q1 -->|no| Q2{High steady volume?}
    Q2 -->|yes| Q3{Have MLOps/GPU capacity?}
    Q3 -->|yes| SELF
    Q3 -->|no| API[Hosted API]
    Q2 -->|no| API
    SELF --> HYBRID[Or hybrid via gateway]
    API --> HYBRID
```

**Notes:** compliance and steady high volume favor self-hosting; small teams / top quality favor API; mature systems often do both.

*Diagrams synthesized from general domain knowledge and current best practices; rephrased for compliance with licensing restrictions.*
