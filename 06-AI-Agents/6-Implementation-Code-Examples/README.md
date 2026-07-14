# AI Agents — Implementation Code Examples

Runnable, heavily‑commented examples. Each file demonstrates ONE core agent idea, with
comments explaining **why** — the same reasoning you'd give in an interview.

## Setup
```bash
pip install -r requirements.txt
# Optional — only tool_calling_loop.py can use it; it falls back to a mock without one:
export OPENAI_API_KEY=sk-...
```

Two of the files run **completely offline** (stdlib + a mock LLM) so you can study the
mechanics with no API key and no network.

## Index
| File | Concept | Runs offline? | Key "why" |
|---|---|---|---|
| [`react_agent_from_scratch.py`](./react_agent_from_scratch.py) | The ReAct loop, no frameworks | ✅ yes (mock LLM) | See the Thought→Action→Observation loop + budgets/loop‑detection that frameworks hide |
| [`tool_calling_loop.py`](./tool_calling_loop.py) | Real function‑calling loop | ✅ yes (mock fallback) | Models emit structured `{name,args}`; validate args before executing |
| [`agent_memory.py`](./agent_memory.py) | Short‑term + long‑term memory | ✅ yes (stdlib) | Memory = context management: write policy + retrieval budget matter most |
| [`langgraph_multi_agent.py`](./langgraph_multi_agent.py) | Supervisor multi‑agent on LangGraph | ⚠️ needs `langgraph` | Stateful graph + cycles + checkpointing = traceable, durable coordination |
| [`mcp_tool_server.py`](./mcp_tool_server.py) | Expose tools via MCP | ⚠️ needs `mcp` + a host | One protocol replaces N×M integrations; tools vs resources vs security |

## Suggested reading order
1. `react_agent_from_scratch.py` — the mental model: an LLM in a loop with a budget.
2. `tool_calling_loop.py` — how real models call tools (structured, validated).
3. `agent_memory.py` — give the agent state across steps/sessions.
4. `langgraph_multi_agent.py` — coordinate specialized agents durably.
5. `mcp_tool_server.py` — publish tools the standard, reusable way.

## What these examples deliberately show
- **Reliability first:** step budgets, time budgets, loop detection, error‑feedback, and a
  checkpointer for durable resume.
- **Security first:** argument validation (Pydantic / regex allowlists), locked‑down `eval`,
  input size limits, and the tools‑vs‑resources distinction from MCP.
- **Cost/context awareness:** compact tool observations and memory compaction.

## Notes
- Model names (`gpt-4o-mini`) are illustrative — swap for whatever you have access to.
- These are teaching scaffolds. Before production add: tracing/observability, retries with
  backoff, timeouts, HITL approval for risky tools, sandboxing for code execution, and a
  trajectory‑based eval suite (see `../3-Cheatsheet/AI-Agents-Cheatsheet.md`).
- Real vector memory → use FAISS / pgvector / a managed store instead of the toy embedding
  in `agent_memory.py`.

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
