"""
02 — Tool / function calling loop.

The model doesn't run tools itself. The loop is:
  1. Send messages + tool schemas.
  2. Model replies with a tool call (name + JSON args).
  3. YOU execute the tool and append the result.
  4. Send back so the model can produce the final answer.

Run:   python 02_tool_calling.py
Needs: OPENAI_API_KEY
"""
from __future__ import annotations

import json

from openai import OpenAI

client = OpenAI()
MODEL = "gpt-4o-mini"


# ---- the actual local functions the model may "call" ----
def get_weather(city: str) -> str:
    fake_db = {"paris": "18C, cloudy", "delhi": "34C, sunny"}
    return fake_db.get(city.lower(), "unknown")


def calculate(expression: str) -> str:
    # NOTE: eval is unsafe on untrusted input; use a real parser in production.
    return str(eval(expression, {"__builtins__": {}}))


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a math expression",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
]

DISPATCH = {"get_weather": get_weather, "calculate": calculate}


def run(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]

    # Loop until the model stops asking for tools (with a safety cap).
    for _ in range(5):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS
        )
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content  # final answer

        # Execute each requested tool and feed results back.
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = DISPATCH[call.function.name](**args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })
    return "Stopped: too many tool iterations."


if __name__ == "__main__":
    print(run("What's the weather in Paris, and what is 23*19?"))
