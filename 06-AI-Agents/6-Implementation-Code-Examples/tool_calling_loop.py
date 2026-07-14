"""
tool_calling_loop.py
====================
The REAL tool-calling loop against an LLM provider (OpenAI-style function calling).

This is what production agents actually do: give the model JSON tool schemas, let it
emit structured tool calls, execute them, feed results back, repeat until it answers.

WHY this matters vs. the from-scratch version:
    Modern models are fine-tuned for "tool calling" — they return machine-parseable
    {name, arguments} objects instead of free text you have to regex. This is more
    reliable and is the substrate every framework builds on.

Safety features shown:
    - Pydantic validation of tool arguments BEFORE execution (never trust raw args).
    - A step budget so the loop can't run forever.
    - Graceful fallback to a MOCK client if OPENAI_API_KEY is not set, so the file is
      runnable offline for study.

Run:  python tool_calling_loop.py      (uses mock unless OPENAI_API_KEY is set)
"""

from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, ValidationError, field_validator


# ---------------------------------------------------------------------------
# 1. TOOL ARGUMENT SCHEMAS (Pydantic)
# WHY: the model's arguments are untrusted text. Validating against a schema catches
# hallucinated / malformed / malicious inputs before they hit a real system.
# ---------------------------------------------------------------------------
class WeatherArgs(BaseModel):
    city: str

    @field_validator("city")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("city must not be empty")
        return v


class ConvertArgs(BaseModel):
    celsius: float


def get_weather(city: str) -> dict[str, Any]:
    """Pretend weather API. Returns a compact result (WHY: big blobs bloat context)."""
    fake = {"London": 12, "Tokyo": 18, "Cairo": 30}
    return {"city": city, "celsius": fake.get(city, 20)}


def c_to_f(celsius: float) -> dict[str, Any]:
    """Convert Celsius to Fahrenheit."""
    return {"fahrenheit": round(celsius * 9 / 5 + 32, 1)}


# Registry maps tool name -> (schema, function). One place to enforce validation + authz.
REGISTRY = {
    "get_weather": (WeatherArgs, get_weather),
    "c_to_f": (ConvertArgs, c_to_f),
}

# The JSON schemas we advertise to the model. Descriptions double as prompts:
# they tell the model WHEN to use each tool.
TOOLS_SPEC = [
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "Get the current temperature (Celsius) for a city.",
        "parameters": {"type": "object",
                       "properties": {"city": {"type": "string"}},
                       "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "c_to_f",
        "description": "Convert a Celsius temperature to Fahrenheit.",
        "parameters": {"type": "object",
                       "properties": {"celsius": {"type": "number"}},
                       "required": ["celsius"]}}},
]


def dispatch(name: str, raw_args: dict) -> dict:
    """Validate args against the schema, then execute. Central safety chokepoint."""
    if name not in REGISTRY:
        return {"error": f"unknown tool '{name}'"}
    schema, fn = REGISTRY[name]
    try:
        args = schema.model_validate(raw_args)         # VALIDATE before executing
    except ValidationError as e:
        return {"error": f"invalid arguments: {e.errors()}"}
    return fn(**args.model_dump())


# ---------------------------------------------------------------------------
# 2. THE LOOP
# ---------------------------------------------------------------------------
def run(goal: str, max_steps: int = 6) -> str:
    client, model = _make_client()
    messages = [
        {"role": "system", "content": "You are a helpful agent. Use tools when needed."},
        {"role": "user", "content": goal},
    ]

    for step in range(max_steps):                        # STEP BUDGET
        resp = client.chat(model=model, messages=messages, tools=TOOLS_SPEC)
        msg = resp["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:                               # no tool => final answer
            return msg.get("content", "")

        # Execute every tool call the model requested this turn (can be parallel).
        for call in tool_calls:
            name = call["function"]["name"]
            raw_args = json.loads(call["function"]["arguments"])
            result = dispatch(name, raw_args)            # validated + executed
            print(f"[step {step}] {name}({raw_args}) -> {result}")
            # Feed the observation back keyed to the tool_call_id.
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(result)})

    return "Stopped: step budget exhausted."


# ---------------------------------------------------------------------------
# 3. CLIENT: real OpenAI if a key exists, else a deterministic mock for offline study.
# ---------------------------------------------------------------------------
def _make_client():
    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI
        sdk = OpenAI()

        class RealClient:
            def chat(self, model, messages, tools):
                r = sdk.chat.completions.create(model=model, messages=messages,
                                                tools=tools)
                m = r.choices[0].message
                return {"message": {
                    "role": "assistant",
                    "content": m.content,
                    "tool_calls": [
                        {"id": tc.id, "type": "function",
                         "function": {"name": tc.function.name,
                                      "arguments": tc.function.arguments}}
                        for tc in (m.tool_calls or [])
                    ] or None,
                }}

        return RealClient(), "gpt-4o-mini"

    # ---- Mock client: scripts a weather -> convert -> answer trajectory. ----
    class MockClient:
        def __init__(self):
            self.turn = 0

        def chat(self, model, messages, tools):
            self.turn += 1
            if self.turn == 1:
                return _tool_call("get_weather", {"city": "Tokyo"})
            if self.turn == 2:
                # Read the previous tool observation to chain the next call.
                last = json.loads(messages[-1]["content"])
                return _tool_call("c_to_f", {"celsius": last["celsius"]})
            last = json.loads(messages[-1]["content"])
            return {"message": {"role": "assistant",
                                "content": f"Tokyo is about {last['fahrenheit']}F.",
                                "tool_calls": None}}

    return MockClient(), "mock-model"


def _tool_call(name: str, args: dict) -> dict:
    return {"message": {"role": "assistant", "content": None,
                        "tool_calls": [{"id": f"call_{name}", "type": "function",
                                        "function": {"name": name,
                                                     "arguments": json.dumps(args)}}]}}


if __name__ == "__main__":
    goal = "What's the weather in Tokyo, in Fahrenheit?"
    print("GOAL:", goal)
    print("RESULT:", run(goal))
