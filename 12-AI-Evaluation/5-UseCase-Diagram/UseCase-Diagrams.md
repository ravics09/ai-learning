# AI Evaluation — Use-Case Diagrams

Mermaid diagrams for the core evaluation workflows. Each includes a short "why it matters" note.

---

## 1. Offline eval pipeline in CI (deploy gate)

Runs the golden set on every PR and blocks merges that regress quality.

```mermaid
flowchart TD
    PR[PR: prompt/model/retriever change] --> LOAD[Load versioned golden set]
    LOAD --> RUN[Run system on each row]
    RUN --> DET[Deterministic checks<br/>schema, PII, exact-match]
    RUN --> JUDGE[Semantic + LLM-judge metrics]
    DET --> AGG[Aggregate + per-slice scores]
    JUDGE --> AGG
    AGG --> CMP{Below abs threshold<br/>OR slice regressed vs main?}
    CMP -->|yes| FAIL[Fail check + post diff comment]
    CMP -->|no| PASS[Green check -> allow merge]
```
*Why:* turns "feels better" into a hard, reviewable gate; catches regressions before users.

---

## 2. LLM-as-judge flow (with bias controls)

```mermaid
flowchart TD
    OUT[Candidate output] --> J[Judge LLM]
    RUBRIC[Rubric + criteria<br/>ignore length/format] --> J
    REF[Optional reference / context] --> J
    J --> SWAP[Run both orders A/B and B/A]
    SWAP --> CONS{Verdicts consistent?}
    CONS -->|yes| V[Trust verdict + rationale]
    CONS -->|no| TIE[Mark tie / low confidence]
    V --> CAL[Calibrate vs human anchor<br/>Cohen's kappa]
    TIE --> CAL
```
*Why:* order swapping neutralizes position bias; calibration proves the judge agrees with humans.

---

## 3. RAG evaluation split (retriever vs generator)

```mermaid
flowchart LR
    Q[Question] --> R[Retriever]
    R --> CTX[Context chunks]
    CTX --> G[Generator LLM]
    G --> A[Answer]

    subgraph Retriever metrics
        M1[Context precision]
        M2[Context recall]
        M3[Context relevance]
    end
    subgraph Generator metrics
        M4[Faithfulness]
        M5[Answer relevance]
    end
    CTX -.-> M1 & M2 & M3
    A -.-> M4 & M5
    Q -.-> M5
```
*Why:* isolating the halves tells you whether to fix retrieval or the prompt/generator.

---

## 4. A/B test & canary rollout

```mermaid
flowchart TD
    NEW[New version] --> SHADOW[Shadow: real inputs, hidden output]
    SHADOW --> CAN[Canary 1-5% traffic]
    CAN --> GUARD{Guardrails OK?<br/>latency, error, cost, safety}
    GUARD -->|no| RB[Auto-rollback]
    GUARD -->|yes| AB[A/B split 50/50]
    AB --> SIG{Stat-sig win on primary KPI?}
    SIG -->|yes| FULL[Full rollout]
    SIG -->|no| KEEP[Keep control]
```
*Why:* progressive exposure limits blast radius and proves real-world wins, not just offline.

---

## 5. Online feedback loop

```mermaid
flowchart LR
    APP[Production app] --> TR[(Traces)]
    TR --> IMP[Implicit signals<br/>edits, retries, abandon]
    TR --> EXP[Explicit signals<br/>thumbs, ratings]
    TR --> SAMP[Sampled rows]
    SAMP --> OJ[Async LLM-judge / heuristics]
    IMP --> DASH[Dashboards + drift alerts]
    EXP --> DASH
    OJ --> DASH
    DASH --> CUR[Curate failures]
    CUR --> GS[(Golden set)]
    GS --> APP
```
*Why:* closes the loop — real failures become new eval cases (the flywheel).

---

## 6. Golden dataset lifecycle

```mermaid
flowchart LR
    LOGS[Real prod logs] --> CUR[Curate + label]
    CUR --> EDGE[Add edge + adversarial cases]
    EDGE --> STRAT[Stratify by intent/difficulty/lang]
    STRAT --> VER[Version + freeze in Git]
    VER --> RUN[Run evals]
    RUN --> FAIL[New production failures]
    FAIL --> CUR
```
*Why:* a living, versioned, stratified set is the highest-leverage eval artifact.

---

## 7. Eval platform architecture at scale

```mermaid
flowchart TB
    DS[(Golden datasets<br/>versioned)] --> ORCH[Eval orchestrator]
    TRACES[(Prod traces)] --> SAMP[Stratified + risk-weighted sampler]
    SAMP --> ORCH
    ORCH --> WORK[Autoscaled workers]
    WORK --> CACHE[(Verdict cache by input hash)]
    WORK --> JP[Judge pool<br/>cascade cheap->strong, rate-limited]
    WORK --> RES[(Results store)]
    RES --> RPT[CI gate / dashboards / alerts]
    RES --> BACK[Curate failures -> DS]
```
*Why:* deterministic on 100%, sample + cascade + cache for judges, async so user latency is untouched.

---

## 8. Agent trajectory evaluation

```mermaid
flowchart LR
    G[User goal] --> PLAN[Plan]
    PLAN --> T1[Tool call 1]
    T1 --> T2[Tool call 2]
    T2 --> TN[Tool call n]
    TN --> OUT[Outcome]

    PLAN -. planning quality .- G
    T1 -. tool + arg correctness .- T2
    T2 -. trajectory efficiency .- TN
    OUT -. task completion .- G
    OUT -. cost/latency/safety .- TN
```
*Why:* evaluate outcome AND path — a right answer via an unsafe/costly route is still a failure.

---

## 9. Metric selection decision tree

```mermaid
flowchart TD
    S{What kind of system?} --> LLM[Plain LLM]
    S --> RAG[RAG]
    S --> AGENT[Agent]
    LLM --> LM[correctness, relevance, safety, format]
    RAG --> RM[faithfulness, answer-rel, context precision/recall]
    AGENT --> AM[task completion, tool use, trajectory, cost]
    LM --> GT{Ground truth?}
    RM --> GT
    AM --> GT
    GT -->|yes| REFM[exact-match / F1 / execution acc]
    GT -->|no| JUDGE[LLM-judge + reference-free metrics + pairwise-vs-prod]
```
*Why:* the right metric depends on system type and whether ground truth exists.

---

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
