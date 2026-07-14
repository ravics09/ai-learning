"""
langchain_lcel_chain.py
-----------------------
Goal: show LangChain Expression Language (LCEL) — composing a prompt, a model, and
an output parser into a single Runnable using the pipe operator.

WHY LCEL?
  Every LangChain building block implements the `Runnable` interface (invoke / batch /
  stream + async variants). Because they share that interface, `prompt | model | parser`
  gives you streaming, batching, async, and retries for FREE — without writing glue.
  That's the real payoff over hand-rolled string formatting + requests calls.

Run:
  export OPENAI_API_KEY=sk-...
  python langchain_lcel_chain.py
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field


# 1) Prompt template: parameterized + versionable (WHY: not scattered f-strings that
#    are impossible to trace, test, or reuse).
prompt = ChatPromptTemplate.from_template(
    "Explain {topic} to a {level} in exactly 3 short bullet points."
)

# 2) Model: temperature=0 for deterministic, testable output (WHY: reproducibility).
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 3) Output parser: turn the chat message into a plain string.
parser = StrOutputParser()

# 4) Compose. The pipe wires each Runnable's output into the next.
chain = prompt | model | parser


def demo_invoke() -> None:
    """Single call — the simplest use."""
    result = chain.invoke({"topic": "vector databases", "level": "beginner"})
    print("=== invoke ===")
    print(result)


def demo_batch() -> None:
    """Batch — parallelism for free because `chain` is a Runnable.
    WHY: process many inputs concurrently instead of a Python for-loop."""
    inputs = [
        {"topic": "embeddings", "level": "beginner"},
        {"topic": "LoRA fine-tuning", "level": "engineer"},
    ]
    print("\n=== batch ===")
    for out in chain.batch(inputs):
        print("-", out.splitlines()[0], "...")


def demo_stream() -> None:
    """Stream — lower time-to-first-token, better UX.
    WHY: users perceive speed even if total time is unchanged."""
    print("\n=== stream ===")
    for chunk in chain.stream({"topic": "prompt injection", "level": "engineer"}):
        print(chunk, end="", flush=True)
    print()


# --- Bonus: native structured output via `with_structured_output` -----------------
# WHY: instead of a fragile text parser, ask the model to fill a schema directly.
class Explanation(BaseModel):
    topic: str = Field(description="the subject explained")
    bullets: list[str] = Field(description="exactly three concise bullets")


def demo_structured() -> None:
    structured_model = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(
        Explanation
    )
    structured_chain = prompt | structured_model  # no parser needed; typed object out
    obj = structured_chain.invoke({"topic": "RAG", "level": "beginner"})
    print("\n=== structured output ===")
    print(type(obj).__name__, "->", obj)


if __name__ == "__main__":
    # Each demo is independent; comment out any you don't want to run (they cost tokens).
    demo_invoke()
    demo_batch()
    demo_stream()
    demo_structured()
