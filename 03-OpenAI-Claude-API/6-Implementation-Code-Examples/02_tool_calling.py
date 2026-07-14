"""
02_tool_calling.py
==================
The full tool- (function-) calling loop for OpenAI and Anthropic.

MENTAL MODEL
------------
The model NEVER runs code. It only *asks* your program to run a function by
emitting a structured call (name + JSON args). Your code executes the function
and feeds the result back. You then call the model again; it either requests
more tools or produces the final answer.

    send tools -> model requests call(s) -> YOU execute -> append results
      -> call model again -> ... -> final answer

WHY A LOOP (AND WHY CAP IT)?
----------------------------
A task may need several tool calls (look up A, then use A to look up B). The
model drives this over multiple turns. We cap the iterations because a buggy or
adversarial prompt could otherwise loop forever, burning tokens and money.

PARALLEL TOOL CALLS
-------------------
When the requested calls are independent (weather for 3 cities), the model can
emit them together so you run them concurrently and cut round-trips.
"""
import json
import os

MAX_STEPS = 6  # hard cap so the agent can never loop forever


# --- The "real" tool your app exposes. Keep tools narrow + validated. --------
def get_weather(city: str) -> dict:
    """Pretend to call a weather API. Returns deterministic fake data."""
    fake = {"Paris": 12, "New York": 3, "Tokyo": 18}
    return {"city": city, "temp_c": fake.get(city, 20)}


TOOL_IMPLS = {"get_weather": get_weather}


# ---------------------------------------------------------------------------
# OpenAI implementation
# ---------------------------------------------------------------------------
def openai_tool_loop(user_msg: str) -> str:
    from openai import OpenAI

    client = OpenAI()

    # Tools are described with JSON Schema. `additionalProperties: False` and
    # listing every field in `required` are what let strict schema enforcement
    # work and stop the model from inventing extra keys.
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current temperature (Celsius) for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    }]

    messages = [{"role": "user", "content": user_msg}]

    for _ in range(MAX_STEPS):
        resp = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools,
        )
        msg = resp.choices[0].message

        # No tool calls => the model produced the final answer.
        if not msg.tool_calls:
            return msg.content

        # Append the assistant's tool-call turn verbatim; the follow-up tool
        # results must reference these tool_call_ids.
        messages.append(msg)

        # Execute each requested call (could be parallelized with a thread pool).
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)   # args are JSON strings
            result = TOOL_IMPLS[call.function.name](**args)
            messages.append({
                "role": "tool",                          # OpenAI tool-result role
                "tool_call_id": call.id,                 # link back to the call
                "content": json.dumps(result),
            })
    return "Stopped: hit the tool-call iteration cap."


# ---------------------------------------------------------------------------
# Anthropic implementation (same loop, different envelope)
# ---------------------------------------------------------------------------
def anthropic_tool_loop(user_msg: str) -> str:
    import anthropic

    client = anthropic.Anthropic()

    # Claude tool schema: `input_schema` instead of `parameters`.
    tools = [{
        "name": "get_weather",
        "description": "Get the current temperature (Celsius) for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    }]

    messages = [{"role": "user", "content": user_msg}]

    for _ in range(MAX_STEPS):
        resp = client.messages.create(
            model="claude-sonnet-4-5", max_tokens=512,
            messages=messages, tools=tools,
        )

        # stop_reason tells us whether Claude wants a tool or is done.
        if resp.stop_reason != "tool_use":
            # Final answer: concatenate any text blocks.
            return "".join(b.text for b in resp.content if b.type == "text")

        # Echo the assistant turn (which contains the tool_use blocks) back.
        messages.append({"role": "assistant", "content": resp.content})

        # Build a single user message carrying tool_result block(s).
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                result = TOOL_IMPLS[block.name](**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,             # link back to the call
                    "content": json.dumps(result),
                })
        messages.append({"role": "user", "content": tool_results})
    return "Stopped: hit the tool-call iteration cap."


if __name__ == "__main__":
    q = "What's the weather in Paris and New York right now?"
    if os.getenv("OPENAI_API_KEY"):
        print("OpenAI :", openai_tool_loop(q))
    if os.getenv("ANTHROPIC_API_KEY"):
        print("Claude :", anthropic_tool_loop(q))
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY to run this example.")
