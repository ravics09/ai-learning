# AI Agents — Cheatsheet

Dense, scannable reference. For depth see `../1-Detailed-Learning/Detailed-Learning.md`.

---

## Agent in one line
> **An LLM in a loop with tools, memory, and a stopping condition.** Reason → Act → Observe → repeat.

Four parts: **reasoning engine** (LLM) · **tools** (act/observe) · **control loop** (govern/stop) · **memory** (state).

## Chain vs Agent
| | Workflow/Chain | Agent |
|---|---|---|
| Path | fixed, author‑defined | dynamic, model‑decided |
| Predictable | yes | no (needs guardrails) |
| Use when | flowchart known upfront | next step depends on runtime |

**Rule:** use the least‑agentic thing that works: prompt → workflow → agent.

---

## The agent loop (ReAct)
```
Thought  -> reason about next move
Action   -> {tool, args}
Observation -> tool result
(loop)   -> until Final Answer OR budget hit
```
Why: explicit *Thought* before *Action* cuts wrong tool calls; *Observation* grounds next step.

## Reasoning loops
| Pattern | Idea | Best for | Fails by |
|---|---|---|---|
| ReAct | think/act/observe each step | tool‑heavy tasks | looping on failure |
| Plan‑and‑Execute | plan first, then run (+replan) | long‑horizon | stale plan |
| Reflexion | retry w/ self‑critique | ambiguous | over‑confident critique |
| Tree‑of‑Thought | branch + score + search | hard search problems | cost explosion |
| Autonomous loop | open‑ended | research (risky) | drift / runaway cost |

## Planning
- **Decomposition** → split goal into sub‑tasks (cheap, do first).
- **Plan‑and‑Execute** → planner (strong) + executor (cheap) + replan.
- **ToT** → multiple branches, scored (BFS/DFS); gate behind difficulty.

---

## Tools / function calling
- Model returns `{name, arguments}` from a **JSON schema** you provide.
- **Validate args** (Pydantic) *before* executing.
- **Descriptions are prompts** — say when to use / not use.
- **Few sharp tools > many overlapping.** Accuracy drops as tool count grows.
- **Compact observations** — big blobs fill context → loops.
- Feed errors back so the model can recover; retries + cap.

## Memory
| Type | Lifetime | Store |
|---|---|---|
| Working/short‑term | this run | prompt/scratchpad |
| Semantic long‑term | forever | vector DB |
| Episodic | forever | log/DB (+embeddings) |
| Procedural | forever | prompt/skills/config |

Pipeline: embed → retrieve top‑k → filter (relevance/recency) → inject → write back (summarized).
Cap memory tokens; TTL/decay + dedupe. Hard part = **write policy**, not storage.

## Reflection
draft → critique → revise (cap iterations). Reflexion = write lesson to memory + retry.
Use for ambiguous/high‑stakes; skip for simple lookups (costs tokens).

---

## Multi‑agent patterns
| Pattern | Pros | Cons |
|---|---|---|
| Supervisor (orchestrator‑worker) | clear, traceable | router SPOF |
| Hierarchical | scales | cost/latency compound |
| Network (P2P) | flexible | hard to debug, loops |
| Sequential pipeline | simple | no adaptivity |

**Start single.** Add an agent only for a distinct responsibility/tool set. Watch: error
propagation, context loss, chatty loops, cost multiplication.

## Frameworks (2025→2026)
| Framework | Model | Pick when |
|---|---|---|
| **LangGraph** | stateful graph + checkpoints | production, control, durability, HITL |
| **CrewAI** | roles/crews | role‑based, fast prototyping |
| **OpenAI Agents SDK** | agents+handoffs+guardrails | lightweight, provider‑native |
| **AutoGen** (maint.) | conversation | existing deployments (→ MS Agent Framework) |
| **Temporal** | durable workflow | mission‑critical orchestration |

*Swarm archived (→ Agents SDK); AutoGen → maintenance (→ MAF). Choose by mental model.*

## Standards
- **MCP** = agent↔**tools/data**. Host→client→server, JSON‑RPC over stdio / **Streamable HTTP**.
  Features: **Tools, Resources, Prompts, Sampling, Roots, Elicitation**. Kills N×M integrations.
- **A2A** = agent↔**agent** (capability discovery via agent cards).

---

## Reliability checklist
- [ ] **Step budget** (`max_steps`)
- [ ] **Cost/token budget** (abort past $)
- [ ] **Timeouts** (per tool + per run)
- [ ] **Loop detection** (same action/args → break)
- [ ] **Retries** with backoff + cap (transient only)
- [ ] **Replan** when approach is wrong (not for flakiness)
- [ ] **HITL** for risky/irreversible actions
- [ ] **Idempotent** side‑effecting tools (idempotency keys)
- [ ] **Durable state** (checkpoint → resume, not restart)
- [ ] **Fallbacks** on repeated failure

## Security (OWASP LLM 2025 / Agentic 2026)
| Threat | Defense |
|---|---|
| Prompt injection (LLM01) | untrusted‑by‑default; separate data/instructions; input guardrails |
| Excessive agency (LLM06) | least privilege; minimal tools; approvals |
| Tool misuse (ASI02) | allowlist; validate args; rate limit; audit |
| Data leak | redaction/PII filters; scoped memory |
| Insecure output | sandbox; validate; parameterized queries |

Stack: input guardrails → least‑privilege authz → **sandbox/microVM** → output guardrails → HITL → audit.
**Mindset:** anything the agent reads can try to reprogram it.

## Observability
Log per step: run_id, step, thought, tool+args (redacted), obs size, tokens, latency, cost, error.
Dashboards: success rate, avg steps, p95 latency, $/run, tool error rate, loop incidents. (LangSmith/Langfuse/Phoenix.)

## Evaluation
Evaluate **trajectory**, not just answer. Metrics: success, tool select/arg/order accuracy,
steps/tokens/$, side effects, loop rate. Methods: reference paths · LLM/Agent‑as‑judge (calibrate) ·
benchmarks (TRAJECT‑Bench, AgentRewardBench, MCPEval). **Gate releases on a regression suite.**

## Scale levers
Durable execution · stateless workers + queue · **model routing** · caching (tools/embeddings/prefixes) ·
parallel async tools · context compaction · per‑tenant budgets/quotas · streaming.
*Most latency = round trips, not compute.*

---

## Minimal loop (memorize)
```python
scratch = []
for step in range(MAX_STEPS):        # step budget
    out = llm(prompt(goal, tools, scratch))
    if out.final: return out.final
    try: obs = tools[out.action](**out.args)   # validate args first!
    except Exception as e: obs = f"ERROR: {e}"  # recover
    scratch.append((out.thought, out.action, out.args, obs))
return "budget exhausted"            # never loop forever
```

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
