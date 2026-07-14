"""
instructor_structured_output.py
--------------------------------
Goal: get GUARANTEED typed output from an LLM using Instructor + Pydantic, with
automatic retries and validation — then show why "valid shape" != "correct content".

WHY INSTRUCTOR?
  Instructor "patches" a normal provider client so every call returns a validated
  Pydantic object instead of a raw string. If the model's output doesn't satisfy the
  schema, Instructor feeds the validation error back and RETRIES. This kills the
  brittle "parse JSON out of free text and hope" pattern. It's vendor-agnostic and
  adds no agent loop — perfect when you just need typed extraction.

Run:
  export OPENAI_API_KEY=sk-...
  python instructor_structured_output.py
"""

from typing import List

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator


# 1) Define the schema you want back. Pydantic constraints become guarantees the
#    LLM output must satisfy (WHY: shape + basic validity enforced automatically).
class LineItem(BaseModel):
    name: str
    quantity: int = Field(ge=1, description="must be at least 1")
    unit_price: float = Field(ge=0)


class Invoice(BaseModel):
    customer: str
    items: List[LineItem]
    total: float = Field(ge=0)

    # 2) Cross-field validation. WHY: a schema guarantees SHAPE, not CORRECTNESS.
    #    {"total": 3} can be well-formed and still wrong. Here we verify the total
    #    actually equals the sum of line items — catching a whole class of silent bugs.
    @field_validator("total")
    @classmethod
    def total_matches_items(cls, v, info):
        items = info.data.get("items") or []
        computed = round(sum(i.quantity * i.unit_price for i in items), 2)
        if items and abs(computed - v) > 0.01:
            raise ValueError(f"total {v} != sum of items {computed}")
        return v


# 3) Patch the client. Every call can now take a `response_model`.
client = instructor.from_openai(OpenAI())


def extract_invoice(text: str) -> Invoice:
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=Invoice,     # <-- guaranteed Invoice or Instructor retries
        max_retries=3,              # WHY: transient schema misses self-heal
        messages=[
            {"role": "system", "content": "Extract a structured invoice from the text."},
            {"role": "user", "content": text},
        ],
    )


if __name__ == "__main__":
    text = (
        "Invoice for Acme Corp: 2 keyboards at $25 each, and 1 monitor at $150. "
        "Total due: $200."
    )
    invoice = extract_invoice(text)
    print("Typed object:", type(invoice).__name__)
    print(invoice.model_dump_json(indent=2))
    # Takeaway to say in an interview: I still add content-level evals (grounding,
    # cross-field checks) on top of schema validation — correctness is separate.
