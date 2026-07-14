# AI Agents — Rapid Fire (50 Q&A)

One‑line answers for last‑minute review and quick recall drills. Grouped by theme.

## Fundamentals
1. **What is an agent?** An LLM in a loop with tools, memory, and a stopping condition.
2. **Chain vs agent?** Chain = fixed path; agent = model decides the path at runtime.
3. **When use an agent?** Only when the next step depends on runtime discovery.
4. **Four agent components?** Reasoning engine, tools, control loop, memory.
5. **Core agent cycle?** Reason → Act → Observe → repeat.
6. **Least‑agentic rule?** Prefer prompt → workflow → agent, in that order.
7. **Why are agents unpredictable?** The model chooses actions dynamically.
8. **What makes an LLM "an agent"?** Adding tools, memory, and planning.

## Reasoning loops
9. **ReAct means?** Reason + Act: interleave Thought, Action, Observation.
10. **Why Thought before Action?** Reduces wrong/failed tool calls.
11. **What grounds the next step?** The Observation (real tool result).
12. **Plan‑and‑Execute?** Plan all steps first, then run, replan when needed.
13. **Reflexion?** Retry using self‑critique stored as a lesson in memory.
14. **Tree‑of‑Thought?** Explore + score multiple reasoning branches.
15. **ReAct failure mode?** Looping on a failing action.
16. **Plan‑and‑Execute failure mode?** Plan goes stale when the world changes.
17. **Do you combine patterns?** Yes — e.g. ReAct + Reflexion in production.

## Planning
18. **Decomposition?** Break a goal into smaller sub‑tasks.
19. **Why decompose?** Focused calls, smaller context, fewer errors.
20. **ToT cost concern?** It multiplies LLM calls — gate behind difficulty.
21. **Who replans?** The planner, when the executor detects it's off track.

## Tools
22. **Function calling?** Model returns structured `{name, args}` from a JSON schema.
23. **First rule of tool args?** Validate them before executing.
24. **Tool descriptions are…?** Prompts — say when to use and not use.
25. **Few vs many tools?** Few sharp tools; overlap causes wrong selection.
26. **Big tool output problem?** Fills context, triggers loops — summarize.
27. **On tool error?** Feed it back so the model can recover; cap retries.

## Memory
28. **Working memory?** Current‑run scratchpad in the prompt.
29. **Long‑term memory store?** Vector DB (embeddings) for semantic recall.
30. **Episodic memory?** Record of past interactions/sessions.
31. **Memory pipeline?** Embed → retrieve top‑k → filter → inject → write back.
32. **Hardest memory problem?** The write policy (what to keep), not storage.
33. **Why cap memory tokens?** So retrieved text doesn't crowd out the task.

## Reflection
34. **Reflection?** Agent critiques and revises its own output.
35. **When skip reflection?** Simple lookups — it just burns tokens.
36. **Always do what with reflection?** Cap the iterations.

## Multi‑agent
37. **Supervisor pattern?** Router delegates to specialized workers.
38. **Supervisor risk?** Router is a bottleneck/single point of failure.
39. **Network topology risk?** Hard to debug; agents can loop.
40. **When add an agent?** Only for a distinct responsibility/tool set.
41. **Chatty‑loop fix?** Turn budgets + termination checks.

## Frameworks & standards
42. **LangGraph model?** Stateful graph with cycles + checkpointing.
43. **CrewAI model?** Role/crew‑based agents.
44. **AutoGen status?** Maintenance mode (→ Microsoft Agent Framework).
45. **MCP is?** Open standard connecting agents to tools/data ("USB‑C for AI").
46. **MCP six features?** Tools, Resources, Prompts, Sampling, Roots, Elicitation.
47. **A2A vs MCP?** A2A = agent↔agent; MCP = agent↔tools/data.

## Reliability, security, eval
48. **Stop runaway agents?** Budgets: steps, cost, time + loop detection + HITL.
49. **Top agent security risks?** Prompt injection, excessive agency, tool misuse.
50. **How to evaluate agents?** Judge the trajectory (tools/order/steps), not just the answer; gate on a regression suite.

---

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
