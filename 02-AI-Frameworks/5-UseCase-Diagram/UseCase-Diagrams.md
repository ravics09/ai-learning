# AI Frameworks — Use-Case Diagrams

> Mermaid diagrams for the patterns you'll be asked to whiteboard. Each has a one-line "when to use."

---

## 1. LCEL chain (stateless composition)
**When:** fixed, predictable pipeline with no branching/loops.

```mermaid
flowchart LR
    IN[Input dict] --> P[PromptTemplate]
    P --> M[ChatModel]
    M --> OP[OutputParser / structured output]
    OP --> OUT[Typed result]
    M -. tokens .-> CB[Callbacks / stream / trace]
```

---

## 2. LangGraph agent loop (stateful + cyclic)
**When:** open-ended tasks needing dynamic tool use and a think-act-observe loop.

```mermaid
stateDiagram-v2
    [*] --> Agent
    Agent --> Tools: tool call requested
    Tools --> Agent: observation
    Agent --> Human: high-stakes action
    Human --> Agent: approve / edit
    Agent --> [*]: final answer
```

---

## 3. LlamaIndex RAG pipeline
**When:** answering questions over your documents / enterprise search.

```mermaid
flowchart LR
    subgraph Ingest [Offline]
      SRC[Connectors] --> DOC[Documents] --> N[Nodes + metadata] --> EMB[Embed] --> IDX[(Vector index)]
    end
    subgraph Query [Online]
      Q[Query] --> R[Retriever]
      IDX --> R
      R --> RR[Rerank]
      RR --> SYN[Response synthesizer]
      SYN --> A[Answer + sources]
    end
```

---

## 4. DSPy compile pipeline
**When:** you have a metric + trainset and want optimized, model-portable prompts.

```mermaid
flowchart LR
    SIG[Signature: inputs -> outputs] --> MOD[Module: CoT / ReAct]
    MOD --> PROG[Program]
    TRAIN[Trainset] --> OPT[Optimizer: MIPROv2 / BootstrapFewShot]
    METRIC[Metric] --> OPT
    PROG --> OPT
    OPT --> CP[Compiled prompts + demos]
    CP --> RUN[Runtime program]
```

---

## 5. Structured-output flow (Instructor / Pydantic)
**When:** you need validated, typed data out of an LLM.

```mermaid
flowchart TD
    REQ[Prompt + response_model schema] --> LLM[LLM call]
    LLM --> RAW[Raw output]
    RAW --> VAL{Validates against schema?}
    VAL -- No --> RETRY[Feed error back + retry]
    RETRY --> LLM
    VAL -- Yes --> OBJ[Typed Pydantic object]
    OBJ --> CHK{Content correct? cross-field / grounding}
    CHK -- No --> FLAG[Flag / human review]
    CHK -- Yes --> USE[Use downstream]
```

---

## 6. Framework-selection flowchart
**When:** starting a new LLM feature and choosing tooling.

```mermaid
flowchart TD
    S[New LLM feature] --> A{More than a single call?}
    A -- No --> RAW[Raw provider SDK]
    A -- Yes --> B{Document-heavy retrieval?}
    B -- Yes --> LI[LlamaIndex]
    B -- No --> C{Multi-step / stateful / tools?}
    C -- Yes --> LG[LangGraph]
    C -- No --> D{Typed output only?}
    D -- Yes --> INS[Instructor / Pydantic AI]
    D -- No --> E{Optimize prompts to a metric?}
    E -- Yes --> DS[DSPy]
    E -- No --> LC[LangChain LCEL]
```

---

## 7. Production agent runtime at scale
**When:** high-traffic agents that must stay reliable and resumable.

```mermaid
flowchart LR
    U[Clients] --> GW[API gateway: auth + rate limit]
    GW --> Q[(Queue: Redis/NATS)]
    Q --> W[Stateless agent workers]
    W --> CK[(Checkpoint store)]
    W --> VDB[(Vector store)]
    W --> LLM[(LLM providers + fallback)]
    W --> OBS[Tracing / cost / metrics]
    W --> GW
```

---

## 8. Combined stack (real-world composition)
**When:** production RAG + agent — mix focused tools.

```mermaid
flowchart LR
    Q[User query] --> LG[LangGraph orchestrator]
    LG --> RET[LlamaIndex retriever]
    RET --> VDB[(Vector store)]
    LG --> TOOLS[Tools APIs]
    LG --> OUT[Instructor: typed final answer]
    LG -. traces .-> OBS[Observability + evals]
```

---

## 9. Fine-tuning with PEFT/LoRA
**When:** adapting a base model cheaply for a specific task.

```mermaid
flowchart LR
    DATA[Task dataset] --> TOK[Tokenizer]
    TOK --> BASE[Frozen base model]
    BASE --> LORA[Trainable LoRA adapters]
    LORA --> TRAIN[Trainer + metric]
    TRAIN --> ADPT[Saved adapter]
    ADPT --> SERVE[Base + adapter at inference]
```

> Content synthesized from general domain knowledge and current (2025-2026) documentation and interview trends; rephrased for compliance with licensing restrictions.
