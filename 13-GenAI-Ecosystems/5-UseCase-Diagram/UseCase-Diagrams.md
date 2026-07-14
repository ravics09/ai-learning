# GenAI Ecosystems — Use-Case Diagrams

> Visual mental models. Each diagram is rendered with Mermaid and paired with a short "how to
> read it" note.

---

## 1. Modality map — inputs, model types, outputs

How different data types flow through specialized models.

```mermaid
graph TD
    subgraph Inputs
        T[Text]
        I[Image]
        A[Audio]
        V[Video]
    end
    T --> LLM[LLM / reasoning]
    I --> VLM[Vision-Language Model]
    A --> STT[Speech-to-Text]
    V --> VU[Video understanding]
    T --> EMB[Embedding model]

    LLM --> OT[Text out]
    LLM --> DIFF[Diffusion -> Image]
    LLM --> TTS[TTS -> Audio]
    LLM --> VGEN[Video gen]
    EMB --> VEC[(Vectors -> search/RAG)]
```

**Read it:** pick the model type by modality; embeddings feed retrieval, not generation.

---

## 2. Model-selection flowchart

The decision tree a senior engineer walks when choosing a model.

```mermaid
flowchart TD
    A[New workload] --> B{Data must stay on-prem?}
    B -- Yes --> C[Open-weight self-host]
    B -- No --> D{Need frontier reasoning/coding?}
    D -- Yes --> E[Closed frontier / reasoning API]
    D -- No --> F{High volume / cost-critical?}
    F -- Yes --> G[SLM or discount open + routing]
    F -- No --> H{Image / audio / video?}
    H -- Yes --> I[Native multimodal or specialist]
    H -- No --> J[General mid-tier default]
    C --> K{Need behavior change?}
    K -- Yes --> L[LoRA / QLoRA]
    K -- No --> M[Serve base via vLLM]
```

**Read it:** constraints first (data, hardness, volume, modality), leaderboard last.

---

## 3. GenAI tooling stack

The layers of a production application.

```mermaid
graph TD
    UI[App / UX] --> ORCH[Orchestration<br/>LangChain, LlamaIndex, DSPy]
    ORCH --> GW[LLM Gateway<br/>LiteLLM / Portkey]
    GW --> GUARD[Guardrails<br/>PII, injection, moderation, schema]
    GUARD --> M{Models}
    M --> API[Closed APIs]
    M --> SELF[Self-host: vLLM / TGI / Ollama]
    ORCH --> RET[Retrieval]
    RET --> VDB[(Vector DB)]
    ORCH --> OBS[Observability & Evals<br/>Langfuse / Phoenix / OTel]
```

**Read it:** the gateway + guardrails layer is where routing, cost, and security concentrate.

---

## 4. Open vs closed decision

```mermaid
flowchart TD
    S[Choosing a model] --> Q1{Privacy / data residency critical?}
    Q1 -- Yes --> OPEN[Open-weight]
    Q1 -- No --> Q2{Volume high & stable?}
    Q2 -- Yes --> Q3{Can keep GPUs busy?}
    Q3 -- Yes --> OPEN
    Q3 -- No --> CLOSED[Closed API]
    Q2 -- No --> Q4{Need frontier quality now?}
    Q4 -- Yes --> CLOSED
    Q4 -- No --> CLOSED
    OPEN --> NOTE1[Control, cost-at-scale, customization]
    CLOSED --> NOTE2[Best quality, low ops, per-token cost]
```

**Read it:** open wins on privacy/control/cost-at-scale *if* you can keep GPUs utilized; closed
wins on speed-to-frontier and low ops.

---

## 5. Multimodal pipeline (support ticket example)

```mermaid
sequenceDiagram
    participant U as User
    participant O as Orchestrator
    participant S as Whisper STT
    participant V as VLM
    participant R as Retriever
    participant L as LLM
    participant G as Guardrails
    U->>O: Text + screenshot + voice note
    O->>S: transcribe audio
    O->>V: describe/OCR image
    S-->>O: transcript
    V-->>O: image text + description
    O->>R: retrieve KB articles
    R-->>O: top chunks
    O->>L: fused context -> draft resolution
    L-->>G: draft
    G-->>U: safe, PII-masked response
```

**Read it:** route each modality to a specialist, fuse into one context, ground with retrieval,
then guardrail the output.

---

## 6. Inference-serving options

```mermaid
flowchart LR
    NEED[Serving need] --> C1{Concurrency?}
    C1 -- Single user / dev --> OLL[Ollama]
    C1 -- Many concurrent --> C2{Ecosystem?}
    C2 -- HF-native --> TGI[TGI]
    C2 -- Max throughput --> VLLM[vLLM]
    C2 -- Shared prefixes --> SG[SGLang]
    C1 -- CPU-only / edge --> LCPP[llama.cpp]
```

**Read it:** match the engine to the load pattern, not the headline benchmark.

---

## 7. Training-to-deployment lifecycle

```mermaid
flowchart LR
    P[Pretraining] --> BASE[Base model]
    BASE --> SFT[SFT]
    SFT --> ALIGN[RLHF / DPO / RLVR]
    ALIGN --> CHAT[Aligned model]
    CHAT --> PEFT[LoRA/QLoRA for your task]
    PEFT --> QUANT[Quantize AWQ/GGUF]
    QUANT --> SERVE[Serve via vLLM/Ollama]
    SERVE --> EVAL[Evals + observability]
    EVAL -->|drift/regression| PEFT
```

**Read it:** the loop never ends — evals feed back into re-tuning and re-tiering.

---

## 8. Cost-optimizing router / cascade

```mermaid
flowchart TD
    REQ[Request] --> CACHE{Semantic cache hit?}
    CACHE -- Yes --> RET[Return cached]
    CACHE -- No --> CHEAP[Cheap SLM + self-check]
    CHEAP --> CONF{Confident?}
    CONF -- Yes --> OUT[Return + cache]
    CONF -- No --> FRON[Frontier/reasoning model]
    FRON --> OUT
```

**Read it:** cache -> cheap-by-default -> escalate. Monitor the escalation rate as a live cost
metric.

---

## 9. RAG data flow (grounding a model)

```mermaid
flowchart LR
    DOCS[Documents] --> CHUNK[Chunk]
    CHUNK --> EMB[Embed]
    EMB --> VDB[(Vector DB)]
    Q[User query] --> QEMB[Embed query]
    QEMB --> SRCH[Similarity search]
    VDB --> SRCH
    SRCH --> CTX[Top-k chunks]
    CTX --> PROMPT[Prompt + context]
    PROMPT --> LLM[LLM]
    LLM --> ANS[Grounded answer + citations]
```

**Read it:** same embedding model for indexing and querying; keep prompts tight and put the best
chunks near the edges.

---

*Content synthesized from general domain knowledge and current (2025-2026) trends; rephrased for
compliance with licensing restrictions.*
