"""
typing_pydantic.py
==================

Two related skills every AI engineer needs:
  1) Type hints for readability + static checking (mypy/pyright catch bugs pre-deploy).
  2) Pydantic for RUNTIME validation at trust boundaries (API input, config, LLM output).

Key mental model:
  - Type hints alone are NOT enforced at runtime — they're metadata for tools/humans.
  - Pydantic DOES validate and coerce at runtime, which is why FastAPI uses it to guard
    every request. Validate untrusted data at the edge so it never reaches your model code.

Run:  python typing_pydantic.py
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator


# ---------------------------------------------------------------------------
# 1. Plain type hints. These document intent and enable static analysis, but Python
#    will NOT stop you from passing the wrong type at runtime — a linter/mypy will.
# ---------------------------------------------------------------------------
def top_k_indices(scores: list[float], k: int = 5) -> list[int]:
    """Return indices of the k highest scores (documented by the signature)."""
    return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]


# ---------------------------------------------------------------------------
# 2. Dataclass: fast, lightweight, for INTERNAL trusted data.
#    - slots=True  -> no per-instance __dict__ => less memory + faster attribute access
#    - frozen=True -> immutable + hashable (safe to share, usable as a cache key)
#    - No runtime validation: if you pass a bad type, it just stores it.
#    Use dataclasses for internal structures where you control the inputs.
# ---------------------------------------------------------------------------
@dataclass(slots=True, frozen=True)
class ModelConfig:
    name: str
    max_tokens: int = 512
    # NEVER use a mutable literal default (e.g. stop: list = []) — it would be shared
    # across all instances. default_factory creates a fresh list each time.
    stop: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# 3. Pydantic model: validates + coerces at the BOUNDARY.
#    This is what protects a service from malformed or malicious input. Constraints
#    live in the schema, so bad requests fail fast with a clear, structured error
#    instead of blowing up deep inside inference.
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)          # cap size => limit abuse/cost
    temperature: float = Field(0.7, ge=0.0, le=2.0)             # must be in [0, 2]
    max_tokens: int = Field(512, gt=0, le=4096)                 # bound output => bound cost
    role: Literal["user", "system"] = "user"                    # only allowed values

    @field_validator("prompt")
    @classmethod
    def reject_null_bytes(cls, v: str) -> str:
        # Custom rule: block control characters that can corrupt logs / downstreams.
        if "\x00" in v:
            raise ValueError("prompt contains a null byte")
        return v


def demo_static_typing() -> None:
    scores = [0.2, 0.9, 0.5, 0.99, 0.1]
    print("top_k_indices:", top_k_indices(scores, k=2))


def demo_dataclass() -> None:
    cfg = ModelConfig(name="demo-llm", stop=(".", "\n"))
    print("dataclass config:", cfg)                # nice auto __repr__
    # cfg.name = "x"  # would raise FrozenInstanceError because frozen=True


def demo_pydantic() -> None:
    # Valid input: types are coerced (e.g., "0.5" -> 0.5) and constraints checked.
    good = ChatRequest.model_validate(
        {"prompt": "Summarize this doc", "temperature": "0.5", "max_tokens": 256}
    )
    print("valid request :", good.model_dump())    # serialize back to a dict/JSON-ready

    # Invalid input: Pydantic raises a structured error we can return as HTTP 422.
    try:
        ChatRequest.model_validate({"prompt": "", "temperature": 5.0})
    except ValidationError as e:
        print("rejected input:", e.error_count(), "error(s):")
        for err in e.errors():
            print(f"   - {err['loc']}: {err['msg']}")


if __name__ == "__main__":
    demo_static_typing()
    demo_dataclass()
    demo_pydantic()
