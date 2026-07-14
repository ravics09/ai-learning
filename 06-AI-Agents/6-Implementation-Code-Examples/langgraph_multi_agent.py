"""
langgraph_multi_agent.py
=======================
A SUPERVISOR multi-agent system on LangGraph: a router delegates to specialized workers
(a researcher and a math worker), collects their results, and produces a final answer.

WHY LangGraph for multi-agent:
    - It models the system as a STATE GRAPH with cycles — exactly what "supervisor loops
      until done" needs.
    - Typed shared state acts as the single source of truth (better than passing giant
      messages between agents).
    - A checkpointer gives DURABLE execution: a long run can resume after a crash instead
      of restarting (and re-paying for) every step.

WHY a supervisor topology:
    It's the easiest multi-agent shape to trace and debug — one place decides who works
    next. Add hierarchy/network only when a single supervisor becomes the bottleneck.

Requires: langgraph, langchain-core (see requirements.txt). This example uses stub "worker"
functions instead of live LLM calls so the graph wiring is the star and it runs offline.

Run:  python langgraph_multi_agent.py
"""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver


# ---------------------------------------------------------------------------
# 1. SHARED STATE
# WHY a typed shared state: all agents read/write ONE object (a "blackboard"). This avoids
# context loss from copying big messages around, and makes the run inspectable/resumable.
# `add` reducer lets multiple nodes append to the log without clobbering each other.
# ---------------------------------------------------------------------------
def add(left: list, right: list) -> list:
    return left + right


class TeamState(TypedDict):
    task: str
    log: Annotated[list[str], add]     # append-only trail of what each agent did
    findings: dict                     # results workers contribute
    next: str                          # supervisor's routing decision
    steps: int                         # budget counter (reliability guardrail)


MAX_STEPS = 6   # STEP BUDGET so the supervisor loop can't spin forever.


# ---------------------------------------------------------------------------
# 2. WORKERS (each owns a distinct responsibility + tool set)
# ---------------------------------------------------------------------------
def researcher(state: TeamState) -> TeamState:
    """Pretend to look up a fact. Real version = LLM + search/RAG tools."""
    findings = dict(state["findings"])
    findings["population_millions"] = 37   # stubbed "research result"
    return {"findings": findings, "log": ["researcher: found population = 37M"]}


def math_worker(state: TeamState) -> TeamState:
    """Do a calculation on the research output. Real version = LLM + calculator tool."""
    findings = dict(state["findings"])
    pop = findings.get("population_millions", 0)
    findings["double"] = pop * 2
    return {"findings": findings, "log": [f"math_worker: doubled to {pop * 2}M"]}


# ---------------------------------------------------------------------------
# 3. SUPERVISOR (the router)
# Decides who works next based on what's already in state. In production this is an LLM
# choosing among workers; here it's explicit rules so the control flow is obvious.
# ---------------------------------------------------------------------------
def supervisor(state: TeamState) -> TeamState:
    step = state.get("steps", 0) + 1
    if step > MAX_STEPS:                                  # budget guardrail
        return {"next": "done", "steps": step,
                "log": ["supervisor: budget hit, finishing"]}
    if "population_millions" not in state["findings"]:
        decision = "researcher"
    elif "double" not in state["findings"]:
        decision = "math_worker"
    else:
        decision = "done"
    return {"next": decision, "steps": step,
            "log": [f"supervisor: route -> {decision}"]}


def route(state: TeamState) -> Literal["researcher", "math_worker", "done"]:
    """Conditional edge reads the supervisor's decision from state."""
    return state["next"]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# 4. BUILD THE GRAPH
# Workers always report BACK to the supervisor (the cycle), which re-routes until done.
# ---------------------------------------------------------------------------
def build_app():
    g = StateGraph(TeamState)
    g.add_node("supervisor", supervisor)
    g.add_node("researcher", researcher)
    g.add_node("math_worker", math_worker)

    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", route,
                            {"researcher": "researcher",
                             "math_worker": "math_worker",
                             "done": END})
    g.add_edge("researcher", "supervisor")   # report back -> re-route
    g.add_edge("math_worker", "supervisor")

    # Checkpointer = durability. With a real DB-backed saver you can resume by thread_id.
    return g.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    app = build_app()
    config = {"configurable": {"thread_id": "demo-1"}}  # identifies this run for resume
    initial: TeamState = {"task": "Find a city's population and double it.",
                          "log": [], "findings": {}, "next": "", "steps": 0}

    final = app.invoke(initial, config=config)

    print("TASK:", final["task"])
    print("\nTRAJECTORY:")
    for line in final["log"]:
        print("  -", line)
    print("\nFINDINGS:", final["findings"])
