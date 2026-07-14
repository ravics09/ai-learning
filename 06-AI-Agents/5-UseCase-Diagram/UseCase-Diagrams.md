# AI Agents — Use‑Case Diagrams

Mermaid diagrams for the patterns you'll draw on a whiteboard. Each has a one‑line "why."

---

## 1. ReAct loop
*Why: the fundamental think→act→observe cycle with a hard stop.*

```mermaid
flowchart TD
    Q[User goal] --> T[Thought: what next?]
    T --> D{Need a tool?}
    D -- yes --> A[Action: tool + args]
    A --> V{Args valid & budget OK?}
    V -- no --> Stop[Abort / best-effort]
    V -- yes --> Ex[Execute tool]
    Ex --> O[Observation]
    O --> T
    D -- no --> F[Final Answer]
```

---

## 2. Tool / function calling sequence
*Why: shows validation + authz between the model and the real API.*

```mermaid
sequenceDiagram
    participant U as User
    participant M as Model
    participant R as Runtime
    participant T as Tool/API
    U->>M: goal
    M->>R: tool_call {name, args}
    R->>R: validate args + check authz + budget
    alt allowed
        R->>T: execute
        T-->>R: result
        R-->>M: compact observation
        M-->>U: final answer
    else blocked
        R-->>M: error / needs approval
    end
```

---

## 3. Supervisor multi‑agent
*Why: clearest multi‑agent topology — router delegates, workers report back.*

```mermaid
flowchart TD
    U[User goal] --> S[Supervisor / Router]
    S -->|research| R[Researcher + web/search tools]
    S -->|code| C[Coder + code exec]
    S -->|write| W[Writer]
    R --> S
    C --> S
    W --> S
    S --> Done{Goal met?}
    Done -- no --> S
    Done -- yes --> Ans[Final deliverable]
```

---

## 4. Memory architecture
*Why: how working, semantic, episodic, and procedural memory feed one agent.*

```mermaid
flowchart TB
    subgraph Working["Working memory (this run)"]
        SP[Scratchpad + recent turns]
    end
    subgraph Persistent
        VEC[(Vector store: semantic)]
        EP[(Episodic log)]
        PROC[[Procedural / skills]]
    end
    A((Agent)) <--> SP
    A -->|retrieve top-k| VEC
    A -->|write salient facts| VEC
    A <--> EP
    A <--> PROC
    VEC --> Filter[Relevance + recency filter] --> A
```

---

## 5. MCP integration
*Why: host runs a client per server; one protocol replaces N×M integrations.*

```mermaid
flowchart LR
    subgraph Host["Host app (agent)"]
        LLM[LLM]
        C1[MCP client A]
        C2[MCP client B]
    end
    LLM --> C1
    LLM --> C2
    C1 <-->|JSON-RPC / Streamable HTTP| S1[MCP server: GitHub]
    C2 <-->|JSON-RPC / stdio| S2[MCP server: Postgres]
    S1 --> GH[(GitHub API)]
    S2 --> DB[(Database)]
    S1 -. exposes .-> Cap1[Tools + Resources + Prompts]
```

---

## 6. Agent platform at scale
*Why: agent runs are distributed durable workflows, not single calls.*

```mermaid
flowchart TB
    U[Clients] --> GW[Gateway: authn/z + rate limit + tenant routing]
    GW --> Q[(Durable task queue)]
    Q --> Wk[Stateless agent workers]
    Wk <--> St[(Checkpoint / state store)]
    Wk --> RT{Model router}
    RT --> Small[Small model]
    RT --> Large[Large model]
    Wk --> MCP[MCP tool gateway + allowlist]
    MCP --> Tools[(APIs / DBs / sandboxes)]
    Wk --> Cache[(Result + embedding cache)]
    Wk --> Obs[(Traces + metrics + eval)]
    Wk --> Guard[Guardrail service]
```

---

## 7. Human‑in‑the‑loop (HITL) approval
*Why: pause on risky/irreversible actions; requires durable suspend/resume.*

```mermaid
flowchart TD
    Step[Agent proposes action] --> Risk{Risky / irreversible?}
    Risk -- no --> Do[Execute]
    Risk -- yes --> Pause[Suspend run + checkpoint state]
    Pause --> Notify[Surface action + reasoning to human]
    Notify --> Dec{Approve / edit / reject}
    Dec -- approve --> Do
    Dec -- edit --> Do
    Dec -- reject --> Cancel[Cancel + log]
    Do --> Audit[(Immutable audit log)]
```

---

## 8. Reliability control flow
*Why: budgets + loop detection + escalation wrap every step.*

```mermaid
flowchart TD
    S[Agent step] --> B{Budgets OK? steps/cost/time}
    B -- no --> Stop[Abort + return best-effort]
    B -- yes --> L{Repeat of prior action?}
    L -- yes --> Esc[Break / escalate]
    L -- no --> Fail{Tool failed?}
    Fail -- transient --> Retry[Backoff + retry]
    Fail -- wrong approach --> Replan[Replan]
    Fail -- no --> Cont[Continue]
    Retry --> S
    Replan --> S
    Cont --> S
```

---

## 9. Trajectory evaluation pipeline
*Why: judge the whole path, then gate releases in CI.*

```mermaid
flowchart LR
    Runs[Agent trajectories] --> Tr[Traces + tool calls]
    Tr --> Ref[Reference-path match]
    Tr --> Judge[LLM / Agent-as-judge + rubric]
    Ref --> Score[Scores: success, steps, side effects]
    Judge --> Score
    Score --> Gate{Meets thresholds?}
    Gate -- yes --> Ship[Release]
    Gate -- no --> Block[Block + investigate]
```

---

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
