"""
03_structured_output.py
======================
Get RELIABLY parseable, schema-conformant JSON out of an LLM.

THE RELIABILITY LADDER
----------------------
1. Prompt "reply as JSON"            -> may include prose / markdown fences
2. JSON mode                         -> valid JSON, but any shape
3. Structured Outputs (strict:true)  -> matches YOUR JSON Schema (constrained decode)
4. Tool schema                       -> args match schema (works on both providers)

WHY STRUCTURED OUTPUTS BEAT "PLEASE OUTPUT JSON"
------------------------------------------------
With strict schema enforcement the decoder is *constrained* to only emit tokens
allowed by your grammar, so it literally cannot produce invalid JSON, extra
keys, or a missing required field. That removes an entire class of production
bugs (parser crashes on malformed output).

BUT: constrained decoding guarantees SHAPE, never SEMANTICS. A schema-valid
object can still contain a wrong value. So we ALWAYS validate afterward.
"""
import json
import os

from pydantic import BaseModel, field_validator


# The target schema. Using an explicit set of allowed priorities means the
# model cannot invent a priority value (if we also enumerate it in the schema).
ALLOWED_PRIORITY = {"P0", "P1", "P2", "P3"}


class BugTicket(BaseModel):
    title: str
    priority: str
    component: str
    tags: list[str]

    @field_validator("priority")
    @classmethod
    def _check_priority(cls, v: str) -> str:
        # Semantic validation the schema alone won't enforce.
        if v not in ALLOWED_PRIORITY:
            raise ValueError(f"priority must be one of {ALLOWED_PRIORITY}")
        return v


PROMPT = "Login is completely broken on Safari for all users. Ship a fix ASAP."


def openai_structured() -> BugTicket:
    """OpenAI Structured Outputs via the SDK's Pydantic helper."""
    from openai import OpenAI

    client = OpenAI()

    # .parse() builds a strict json_schema from the Pydantic model and returns a
    # ready-made instance. The model is guaranteed to fill every required field.
    resp = client.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Extract a bug ticket from the text."},
            {"role": "user", "content": PROMPT},
        ],
        response_format=BugTicket,
    )
    return resp.choices[0].message.parsed  # already a BugTicket


def anthropic_structured() -> BugTicket:
    """Claude idiom: force a TOOL whose input schema is the target object.

    Claude has no `json_schema` response format, so the standard trick is to
    define a single tool that represents your output shape and force the model
    to call it. The tool's `input` block is your structured data.
    """
    import anthropic

    client = anthropic.Anthropic()

    tool = {
        "name": "record_bug_ticket",
        "description": "Record a structured bug ticket.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                # Enumerate categoricals so the model can't invent values.
                "priority": {"type": "string", "enum": sorted(ALLOWED_PRIORITY)},
                "component": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "priority", "component", "tags"],
        },
    }

    resp = client.messages.create(
        model="claude-sonnet-4-5", max_tokens=512,
        system="Extract a bug ticket from the text.",
        messages=[{"role": "user", "content": PROMPT}],
        tools=[tool],
        tool_choice={"type": "tool", "name": "record_bug_ticket"},  # force it
    )
    payload = next(b.input for b in resp.content if b.type == "tool_use")
    return BugTicket(**payload)  # Pydantic validates semantics


if __name__ == "__main__":
    if os.getenv("OPENAI_API_KEY"):
        ticket = openai_structured()
        print("OpenAI :", json.dumps(ticket.model_dump(), indent=2))
    if os.getenv("ANTHROPIC_API_KEY"):
        ticket = anthropic_structured()
        print("Claude :", json.dumps(ticket.model_dump(), indent=2))
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY to run this example.")
