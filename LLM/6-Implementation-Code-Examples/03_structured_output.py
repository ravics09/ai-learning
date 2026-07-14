"""
03 — Structured output with schema enforcement.

Downstream systems need valid, predictable JSON. Don't "ask nicely" and hope;
enforce a schema so output is always parseable.

Run:   python 03_structured_output.py
Needs: OPENAI_API_KEY + pydantic
"""
from __future__ import annotations

from enum import Enum

from openai import OpenAI
from pydantic import BaseModel, Field

client = OpenAI()
MODEL = "gpt-4o-mini"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SupportTicket(BaseModel):
    """The schema the model MUST return."""
    category: str = Field(description="e.g. billing, bug, feature_request")
    priority: Priority
    summary: str
    requires_human: bool


def classify(text: str) -> SupportTicket:
    # .parse() constrains the model to the Pydantic schema and validates it.
    resp = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Extract a structured support ticket."},
            {"role": "user", "content": text},
        ],
        response_format=SupportTicket,
    )
    return resp.choices[0].message.parsed


if __name__ == "__main__":
    ticket = classify("The app crashes every time I open the billing page! Urgent!")
    print(ticket.model_dump_json(indent=2))
    # -> guaranteed valid: category, priority (enum), summary, requires_human
