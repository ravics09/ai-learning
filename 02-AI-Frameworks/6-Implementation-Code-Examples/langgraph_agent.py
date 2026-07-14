"""
langgraph_agent.py
------------------
Goal: build a minimal stateful, cyclic agent with LangGraph — the "think -> act ->
observe -> repeat" loop with a tool, plus checkpointing so the run is durable.

WHY LANGGRAPH?
  A plain chain (DAG) can't loop. Agents need to call a tool, read the result, and
  decide what to do next — that's a CYCLE. LangGraph gives you:
    - typed shared STATE with reducers (how updates merge)
    - conditional EDGES (route based on state)
    - CHECKPOINTING (persist state each step -> resume after a crash/timeout)
    - a natural place to add human-in-the-loop approval gates
  Philosophy: little abstraction, maximum control + durability.

Run:
  export OPENAI_API_KEY=sk-...
  python langgraph_agent.py
"""

from typing import Annotated, TypedDict

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


# 1) A tool the agent can choose to call. WHY: agents act on the world via tools;
#    keep tool args schema'd and side effects controlled.
@tool
def word_count(text: str) -> int:
    """Return the number of words in the given text."""
    return len(text.split())


tools = [word_count]

# 2) Model bound to the tools. WHY: binding tells the model what it may call and how.
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools)


# 3) Typed shared state. `add_messages` is a REDUCER: new messages are APPENDED,
#    not overwritten. WHY: the whole conversation/tool history must accumulate.
class State(TypedDict):
    messages: Annotated[list, add_messages]


# 4) The agent node: call the model with the running message history.
def agent(state: State) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}


# 5) Wire the graph.
builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))  # executes any tool calls the model made

builder.add_edge(START, "agent")
# Conditional edge: if the model asked for a tool -> go to "tools"; else -> END.
# WHY: this is what creates the loop (tools routes back to agent below).
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")  # <-- the CYCLE: observe tool result, think again
builder.add_edge("agent", END)

# 6) Compile WITH a checkpointer -> durability + the ability to resume a thread.
#    WHY: long agent runs fail (bad output, timeouts, crashes). Checkpointing turns a
#    catastrophe into a resume. MemorySaver is in-memory for the demo; use a DB in prod.
graph = builder.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    # `thread_id` identifies a conversation; state is checkpointed under it so you could
    # resume or continue later.
    config = {"configurable": {"thread_id": "demo-1"}}
    result = graph.invoke(
        {"messages": [("user", "How many words are in: 'the quick brown fox jumps'?")]},
        config,
    )
    # Print the final assistant message.
    print(result["messages"][-1].content)
