# AI Security — Use Case Diagrams

> Mermaid diagrams for the core AI security patterns. Use them to explain designs on a whiteboard.

---

## 1. Defense-in-depth pipeline
Every request passes through independent layers; no single layer is trusted alone.

```mermaid
flowchart TB
    U[User request] --> L1[Network: WAF, TLS, authn, rate limit]
    L1 --> L2[Input guardrails: PII detect + injection classifier]
    L2 -->|block| R1[Refuse / sanitize]
    L2 --> L3[Prompt hardening: spotlight untrusted text]
    L3 --> L4[Model: safety-tuned + minimal scoped tools]
    L4 --> L5[Output guardrails: schema + PII/secret scan + groundedness]
    L5 -->|block| R2[Redact / refuse]
    L5 --> L6[Action layer: least priv + HITL + egress allow-list]
    L6 --> L7[(Audit log + anomaly detection)]
    L7 --> RESP[Response]
```

---

## 2. Prompt injection flow (direct & indirect)
Two paths to the same failure: attacker text treated as a command.

```mermaid
flowchart LR
    subgraph Direct
        A1[Attacker = user] -->|malicious prompt| M1[LLM]
    end
    subgraph Indirect
        A2[Attacker] -->|plants payload| SRC[Web / email / PDF / repo]
        SRC --> ING[App retrieves content]
        ING --> M2[LLM]
    end
    M1 --> ACT{Has authority to act?}
    M2 --> ACT
    ACT -->|yes = danger| BAD[Exfiltrate / destructive action]
    ACT -->|no = bounded| SAFE[Harmless: least priv + HITL + egress limit]
    style BAD fill:#f88
    style SAFE fill:#8f8
```

---

## 3. Secure agent tool execution
Policy check → sandbox → HITL for risky actions → audit.

```mermaid
flowchart TB
    AG[Agent proposes action] --> POL[Policy engine / tool allow-list]
    POL -->|denied| BLK[Reject + log]
    POL -->|allowed, low-risk| SBX[Ephemeral sandbox: no net, RO FS, quotas]
    POL -->|allowed, high-risk| HITL[Human approval]
    HITL -->|approved| SBX
    HITL -->|rejected| BLK
    SBX --> EGR{Egress allow-list check}
    EGR -->|blocked| BLK
    EGR -->|permitted| RES[Result]
    RES --> AUD[(Immutable audit log)]
```

---

## 4. Multi-tenant isolation
Tenant context from the verified token drives every data access.

```mermaid
flowchart TB
    REQ[Request] --> AUTH[Verify token -> tenant_id]
    AUTH --> GW[Gateway injects tenant context]
    GW --> RL[Per-tenant rate/budget]
    GW --> VDB[(Vector store: filter WHERE tenant_id)]
    GW --> KMS[Per-tenant encryption keys]
    GW --> CACHE[(Cache keyed by tenant)]
    VDB --> LLM[Stateless inference]
    RL --> LLM
    LLM --> RESP[Response scoped to tenant]
    RESP --> LOG[(Per-tenant audit log)]
```

---

## 5. Guardrail layers (input & output)
Cheap deterministic checks first, model checks in parallel, schema last.

```mermaid
flowchart LR
    IN[Input] --> D1[Regex: PII/secrets/length]
    D1 --> C1[Injection classifier]
    D1 --> C2[Topic/policy classifier]
    C1 --> J{Pass all?}
    C2 --> J
    J -->|no| B1[Block]
    J -->|yes| LLM[LLM]
    LLM --> O1[PII/secret scan]
    LLM --> O2[Toxicity]
    O1 --> O3[Schema validate]
    O2 --> O3
    O3 -->|fail| B2[Redact/refuse]
    O3 -->|pass| OUT[Response]
```

---

## 6. PII redaction flow
Detect → tokenize → process → re-insert only for the authorized user; logs stay tokenized.

```mermaid
flowchart LR
    IN[User input] --> DET[Detect PII: Presidio + regex]
    DET --> MAP[Map to placeholders <PERSON_1>]
    MAP --> LLM[LLM sees redacted text]
    LLM --> REH[Re-insert real values for authorized user]
    REH --> OUT[Response]
    MAP --> LOG[(Logs: tokenized only)]
    style LOG fill:#eef
```

---

## 7. Secure RAG retrieval
Authorize before retrieval; treat retrieved text as untrusted.

```mermaid
flowchart LR
    Q[Query + identity] --> AZ[Authz: what can this user see?]
    AZ --> EMB[Embed query]
    EMB --> VDB[(Vector DB: tenant/ACL filter)]
    VDB --> K[Top-k chunks]
    K --> SPOT[Spotlight as untrusted data]
    SPOT --> LLM[LLM]
    LLM --> CITE[Output + citations + groundedness check]
    CITE --> ANS[Answer]
```

---

## 8. Unbounded consumption / rate & budget control
Reject over-limit, cap resources, meter spend, circuit-break on anomalies.

```mermaid
flowchart TB
    REQ[Request] --> RL{Token-bucket rate check}
    RL -->|over| REJ[429 + backoff]
    RL -->|ok| BUD{Budget remaining?}
    BUD -->|exceeded| REJ
    BUD -->|ok| CAP[Cap max_tokens, input len, agent steps]
    CAP --> LLM[LLM]
    LLM --> METER[Meter tokens & cost per tenant]
    METER --> AL{Anomaly?}
    AL -->|yes| CB[Throttle / circuit-break / alert]
    AL -->|no| RESP[Response]
```

---

## 9. Threat model (STRIDE data-flow)
Trust boundaries around each component.

```mermaid
flowchart TB
    subgraph Boundary_User
        USR[User input - untrusted]
    end
    subgraph Boundary_App
        GRD[Guardrails]
        MODEL[LLM]
        TOOLS[Tools - least privilege]
    end
    subgraph Boundary_Data
        RAG[(RAG store - tenant filtered)]
        DB[(App DB - scoped)]
    end
    USR --> GRD --> MODEL
    MODEL --> TOOLS
    TOOLS --> DB
    MODEL --> RAG
    RAG -.spoof/tamper.-> MODEL
    TOOLS -.elevation.-> DB
    MODEL -.info disclosure.-> USR
    USR -.DoS.-> GRD
```

---

*Content synthesized from general domain knowledge and current (2025-2026) trends; rephrased for compliance with licensing restrictions.*
