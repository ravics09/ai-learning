# 06 — AI Agents

Agents are LLM systems that reason, plan, use tools, and act autonomously toward goals.

## Learning Objectives
- Understand agent architectures and control loops.
- Build reliable tool-using, multi-step agents.
- Handle memory, planning, and multi-agent coordination.

## Core Concepts
### Agent Loop
- Perceive → Reason → Act → Observe → Repeat.
- **ReAct** (Reason + Act) pattern.
- Planning vs reactive execution.

### Building Blocks
- **Tools/Functions**: APIs, code execution, search, databases.
- **Memory**: short-term (context), long-term (vector store), episodic.
- **Planning**: task decomposition, plan-and-execute, tree-of-thought.
- **Reflection**: self-critique and retry.

### Multi-Agent Systems
- Orchestrator/worker, supervisor patterns.
- Agent communication and hand-offs.
- Frameworks: LangGraph, CrewAI, AutoGen, OpenAI Swarm/Agents SDK.

### Emerging Standards
- **MCP (Model Context Protocol)** — standard for tools/context.
- **A2A** — agent-to-agent communication.

## Reliability Concerns
- Infinite loops and runaway costs — add step/budget limits.
- Tool errors and recovery.
- Guardrails, human-in-the-loop approvals.
- Observability and tracing (every step logged).

## Interview Questions
1. Explain the ReAct pattern.
2. Chain vs agent — what's the difference?
3. How do you prevent an agent from looping forever or overspending?
4. How do you design agent memory?
5. When do you use multi-agent vs a single agent?
6. What is MCP and what problem does it solve?
7. How do you make tool calls robust to failures?

## Hands-On
- [ ] Build a ReAct agent with 3+ tools and a step budget.
- [ ] Add long-term memory backed by a vector DB.
- [ ] Build a supervisor + workers multi-agent system in LangGraph.
- [ ] Expose a tool via an MCP server.

## Resources
- MCP: https://modelcontextprotocol.io/
- LangGraph: https://langchain-ai.github.io/langgraph/
