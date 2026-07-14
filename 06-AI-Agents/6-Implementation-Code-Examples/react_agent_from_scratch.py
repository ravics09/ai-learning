"""
react_agent_from_scratch.py
===========================
A ReAct agent built with ZERO frameworks so you can see the actual mechanics that
LangGraph / CrewAI / OpenAI Agents SDK hide behind abstractions.

WHY build it from scratch?
    In an interview, "explain how an agent works" is really "show me the loop." Frameworks
    are convenience wrappers around exactly this: Thought -> Action -> Observation, repeated
    under a budget until a Final Answer.

This file runs OFFLINE with a tiny rule-based "mock LLM" so you can study the control flow
without an API key or network. Swap `mock_llm` for a real model call to make it live.

Run:  python react_agent_from_scratch.py
"""

from __future__ import annotations

import json
import re
import time
from typing import Callable


# ---------------------------------------------------------------------------
# 1. TOOLS
# A tool is just a Python function. The agent can only do what its tools allow —
# this is your primary security boundary (least privilege). Keep the set SMALL and
# each description SHARP, because the model selects tools from these descriptions.
# ---------------------------------------------------------------------------
def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression like '12 * (3 + 4)'."""
    # WHY the allowlist regex: never feed raw model output to eval(). We restrict to
    # digits and math operators so a malicious/hallucinated expression can't run code.
    if not re.fullmatch(r"[0-9+\-*/(). ]+", expression):
        return "ERROR: expression contains disallowed characters"
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))  # locked-down eval
    except Exception as e:  # feed errors back so the model can recover
        return f"ERROR: {e}"


def word_count(text: str) -> str:
    """Count the words in a piece of text."""
    return str(len(text.split()))


TOOLS: dict[str, Callable[..., str]] = {
    "calculator": calculator,
    "word_count": word_count,
}

TOOL_DOCS = "\n".join(f"- {name}: {fn.__doc__}" for name, fn in TOOLS.items())


# ---------------------------------------------------------------------------
# 2. THE "LLM"
# A real agent calls an LLM here. We use a deterministic mock so the example is
# runnable and reproducible. The mock returns the SAME structured JSON shape a real
# model would when prompted to emit ReAct steps: {thought, action, action_input} or
# {thought, final_answer}.
# ---------------------------------------------------------------------------
def mock_llm(goal: str, scratchpad: list[dict]) -> dict:
    """Pretend to be an LLM doing ReAct reasoning for a math word problem."""
    # If we already have a tool observation, we're ready to answer.
    if scratchpad and scratchpad[-1].get("observation") is not None:
        result = scratchpad[-1]["observation"]
        return {"thought": "I have the computed value; I can answer now.",
                "final_answer": f"The answer is {result}."}
    # Otherwise, decide to use the calculator (first step).
    return {"thought": "This needs arithmetic, so I'll call the calculator.",
            "action": "calculator",
            "action_input": {"expression": "12 * (3 + 4)"}}


def build_prompt(goal: str, scratchpad: list[dict]) -> str:
    """Render the ReAct prompt. Shown for realism; the mock LLM ignores it."""
    transcript = "\n".join(
        f"Thought: {s['thought']}\nAction: {s['action']}({s['args']})\nObservation: {s['observation']}"
        for s in scratchpad
    )
    return (
        "You are a ReAct agent. Use tools to reach the goal.\n"
        f"Tools:\n{TOOL_DOCS}\n\n"
        f"Goal: {goal}\n\n"
        f"{transcript}\n"
        "Respond as JSON: {thought, action, action_input} or {thought, final_answer}."
    )


# ---------------------------------------------------------------------------
# 3. THE AGENT LOOP
# This is the heart of every agent. Note the guardrails baked in:
#   - max_steps  -> can't loop forever
#   - time budget -> can't hang
#   - loop detection -> break if it repeats the same action
#   - errors fed back as observations -> the model can self-correct
# ---------------------------------------------------------------------------
def react_agent(goal: str, max_steps: int = 6, max_seconds: float = 10.0) -> str:
    scratchpad: list[dict] = []
    start = time.time()
    seen_actions: set[str] = set()

    for step in range(max_steps):                 # STEP BUDGET
        if time.time() - start > max_seconds:      # TIME BUDGET
            return "Stopped: time budget exhausted."

        _ = build_prompt(goal, scratchpad)         # a real agent sends this to the LLM
        out = mock_llm(goal, scratchpad)
        print(f"[step {step}] thought: {out['thought']}")

        # Termination: the model decided it's done.
        if "final_answer" in out:
            return out["final_answer"]

        name, args = out["action"], out.get("action_input", {})

        # LOOP DETECTION: if we've already run this exact action+args, bail out.
        signature = f"{name}:{json.dumps(args, sort_keys=True)}"
        if signature in seen_actions:
            return "Stopped: detected a repeated action (possible loop)."
        seen_actions.add(signature)

        # ACT: validate the tool exists, then execute. Never call an unknown tool.
        if name not in TOOLS:
            observation = f"ERROR: unknown tool '{name}'"
        else:
            observation = TOOLS[name](**args)
        print(f"[step {step}] action: {name}({args}) -> {observation}")

        # OBSERVE: record the result so the next reasoning step is grounded in reality.
        scratchpad.append({"thought": out["thought"], "action": name,
                           "args": args, "observation": observation})

    return "Stopped: step budget exhausted."       # NEVER loop forever


if __name__ == "__main__":
    goal = "What is 12 * (3 + 4)?"
    print("GOAL:", goal)
    print("RESULT:", react_agent(goal))
