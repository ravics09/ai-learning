# MLOps & LLMOps — Use Case Diagrams

> Visual architectures for the MLOps/LLMOps patterns interviewers probe. GitHub renders Mermaid automatically, so these display as diagrams. Each includes the problem, the flow, and the design notes to mention out loud.

---

## 1. Training Pipeline (reproducible, tracked)

**Problem:** Turn "run notebook cells and pray" into a reproducible, cached, tracked pipeline.

```mermaid
flowchart TB
    RAW[(Raw data / DVC-versioned)] --> VAL[Data validation: schema, nulls, ranges]
    VAL --> FE[Feature engineering / feature store]
    FE --> SPLIT[Train / val / test split]
    SPLIT --> TRAIN[Train + log to tracker]
    TRAIN --> EVAL[Evaluate on held-out + slices]
    EVAL --> GATE{Beats baseline + thresholds?}
    GATE -->|no| TRAIN
    GATE -->|yes| REG[(Model registry: Staging)]
    TRAIN --> TRK[Experiment tracker: params/metrics/SHA/data-version]
```

**Design notes:** validate data *before* training (bad data in → bad model out); track git SHA + data version for reproducibility; cache stages so only changed steps re-run; gate registration on beating the current baseline, not an absolute score.

---

## 2. CI/CD for ML (with eval gate + Continuous Training)

**Problem:** Automatically build, test, evaluate, and deploy models without shipping regressions.

```mermaid
flowchart TB
    A[PR / new data] --> B[CI: lint + unit tests]
    B --> C[Data validation + drift vs baseline]
    C --> D[Train / fine-tune]
    D --> E[Evaluate on golden set]
    E --> F{Pass gate?}
    F -->|no| X[Fail build, block deploy]
    F -->|yes| G[(Register: Staging)]
    G --> H[CD: deploy canary]
    H --> I[Monitor SLOs + evals]
    I -->|healthy| J[Promote to Production]
    I -->|bad| K[Auto-rollback]
    DRIFT[Drift / schedule trigger] -.CT.-> D
```

**Design notes:** the **eval gate** is the ML-specific addition; deterministic checks hard-fail, subjective scores use margins; Continuous Training closes the loop from monitoring back to training.

---

## 3. Model Serving with Autoscaling (online inference)

**Problem:** Serve low-latency predictions that scale with bursty traffic and survive pod failures.

```mermaid
flowchart TB
    U[Clients] --> GW[API gateway: authn/z, rate limit]
    GW --> LB[Load balancer]
    LB --> P1[Model pod 1]
    LB --> P2[Model pod 2]
    LB --> P3[Model pod N]
    HPA[HPA/KEDA: scale on queue depth] -.scales.-> P3
    P1 --> FS[(Feature store: online)]
    P1 --> REG[(Registry: current Production model)]
    P1 --> MET[Metrics: latency p99, QPS, errors]
    MET --> HPA
```

**Design notes:** stateless replicas + shared feature/registry stores; scale on **queue depth / GPU util**, not CPU; readiness probes gate traffic until the model loads; keep a warm floor to dodge cold starts.

---

## 4. Canary Deployment (safe rollout)

**Problem:** Ship a new model version while limiting the blast radius of a bad release.

```mermaid
flowchart TB
    T[Traffic] --> R[Router / service mesh]
    R -->|95%| V7[Model v7 - stable]
    R -->|5%| V8[Model v8 - canary]
    V7 --> M[Metrics + online evals]
    V8 --> M
    M --> D{Canary healthy?}
    D -->|yes| RAMP[Ramp 5% -> 25% -> 100%]
    D -->|no| RB[Auto-rollback to v7]
    RAMP --> DONE[v8 is new stable]
```

**Design notes:** define automatic rollback triggers (error rate, latency p99, eval score, cost spike); ramp gradually; keep v7 pinned by image digest for instant revert.

---

## 5. Drift Monitoring Loop (production feedback)

**Problem:** Detect when the model's world changes and act before quality silently collapses.

```mermaid
flowchart LR
    SVC[Model service] -->|async log| LOG[(Prediction + feature log)]
    REF[(Reference: training stats)] --> CMP{Windowed compare: PSI/KS/Chi-sq}
    LOG --> CMP
    CMP -->|drift > threshold| ALERT[Alert / open ticket]
    LABELS[(Delayed ground truth)] --> ACC[Compute live accuracy]
    ACC -->|quality drop| PAGE[Page + trigger retrain]
    ALERT --> DEC{Root cause}
    DEC -->|data bug| FIX[Fix pipeline]
    DEC -->|real shift| CT[Continuous Training]
```

**Design notes:** log asynchronously so monitoring adds no inference latency; precompute reference stats; feature drift → ticket, model-quality drop → page; join delayed labels to confirm concept drift.

---

## 6. LLM Observability & Tracing

**Problem:** Debug a non-deterministic multi-step LLM chain and track cost/quality per request.

```mermaid
flowchart TB
    Q[User request] --> TR[Trace root span]
    TR --> RET[Span: retrieve context]
    RET --> PR[Span: build prompt - versioned]
    PR --> LLM[Span: LLM call - tokens, latency, cost]
    LLM --> TOOL[Span: tool call]
    TOOL --> ANS[Response]
    ANS --> SCORE[Online eval + user feedback]
    SCORE --> STORE[(Observability store: Langfuse/LangSmith)]
    STORE --> DASH[Dashboards: cost/tenant, quality, latency]
    STORE --> GOLD[Feed failures into golden set]
```

**Design notes:** capture the full span tree with tokens/latency/cost per step; reference prompts by version; sample prod traffic for online evals; loop real failures back into the eval set.

---

## 7. LLM Serving Stack with Routing, Cache & Guardrails

**Problem:** Serve LLMs to many users with cost control, safety, and reliability.

```mermaid
flowchart TB
    U[Clients] --> GW[Gateway: authn, rate limit, quota]
    GW --> IN[Input guardrails: injection/PII/jailbreak]
    IN --> CACHE{Semantic cache}
    CACHE -->|hit| U
    CACHE -->|miss| ROUTE{Query complexity}
    ROUTE -->|easy| SMALL[Small/cheap model]
    ROUTE -->|hard| BIG[Frontier model + fallback provider]
    SMALL --> OUT[Output guardrails: toxicity/secrets/schema]
    BIG --> OUT
    OUT --> OBS[Observability: traces, tokens, cost]
    OBS --> U
    subgraph GPU[Self-hosted pool]
        VLLM[vLLM / TGI / Triton: continuous batching]
    end
    BIG --- VLLM
```

**Design notes:** semantic cache first (biggest cost win); model routing for cost; provider fallback for reliability; guardrails on both input and output; self-hosted models on a batching server for throughput.

---

## 8. Feature Store & Model Registry Flow

**Problem:** Prevent training/serving skew and make deploy/rollback a controlled contract.

```mermaid
flowchart LR
    subgraph Features
        STREAM[Streaming events] --> ONLINE[(Online store: fresh)]
        BATCH[Batch jobs] --> OFFLINE[(Offline store: point-in-time)]
    end
    OFFLINE -->|no leakage| TRAIN[Training]
    TRAIN --> REG[(Model registry)]
    REG -->|Staging -> gate -> Production| SERVE[Serving]
    ONLINE -->|same feature defs| SERVE
    REG -.rollback pointer.-> SERVE
```

**Design notes:** one feature definition serves both training (offline, point-in-time) and inference (online, fresh) — killing skew and leakage; registry pointer is the deploy/rollback contract.

---

## 9. Champion / Challenger with Shadow Testing

**Problem:** Validate a retrained model on real traffic before promoting it — with zero user risk.

```mermaid
flowchart TB
    T[Live traffic] --> CH[Champion v7 - serves users]
    T -.mirror.-> CL[Challenger v8 - scores silently]
    CH --> RESP[User responses]
    CL --> LOG[(Challenger predictions)]
    RESP --> CMP[Compare on delayed labels]
    LOG --> CMP
    CMP --> D{Challenger better?}
    D -->|yes| PROMOTE[Promote v8 to champion via canary]
    D -->|no| KEEP[Keep v7, archive v8]
```

**Design notes:** shadow gives real-traffic signal without user impact (but no click/label feedback); confirm on delayed labels; still roll out the winner via canary, not a hard switch.

---

## Choosing a Deployment Strategy (quick guide)

```mermaid
flowchart TD
    S[Start] --> Q1{Zero user risk needed first?}
    Q1 -->|yes| SH[Shadow / champion-challenger]
    Q1 -->|no| Q2{Instant rollback + can afford 2x infra?}
    Q2 -->|yes| BG[Blue-green]
    Q2 -->|no| Q3{Want gradual metric-driven rollout?}
    Q3 -->|yes| CN[Canary]
    Q3 -->|no| RO[Rolling update]
```

*Diagrams synthesized from general domain knowledge and current best practices; rephrased for compliance with licensing restrictions.*
