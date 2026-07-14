"""
ragas_eval.py
=============
RAG has two halves -- RETRIEVER and GENERATOR -- and you must measure them separately or
you'll "fix" the wrong one. RAGAS gives the standard metrics out of the box:

  Retriever : context_precision, context_recall
  Generator : faithfulness (groundedness), answer_relevancy

WHY these four: they let you localize failures.
  - low context_recall  -> retrieval missed needed chunks
  - low faithfulness     -> generator hallucinated despite good context
  - low answer_relevancy -> grounded but off-topic

Run:
    export OPENAI_API_KEY=sk-...
    python ragas_eval.py
"""
from __future__ import annotations


def build_eval_dataset():
    """
    A tiny RAG eval set. Each row needs:
      - question       : the user query
      - answer          : what your RAG system produced (the thing under test)
      - contexts        : the chunks your retriever returned (list[str])
      - ground_truth    : reference answer (needed for context_recall / correctness)

    In real life you generate `answer` + `contexts` by RUNNING your pipeline over the
    questions; here we hardcode them so the example is self-contained.
    """
    from datasets import Dataset  # HF Dataset is what ragas.evaluate() consumes

    rows = {
        "question": [
            "What is the refund window?",
            "Which regions support same-day delivery?",
        ],
        "answer": [
            "You can request a refund within 30 days of purchase.",
            "Same-day delivery is available in New York and Chicago.",
        ],
        # WHY separate contexts per row: faithfulness checks the answer against THESE chunks.
        "contexts": [
            ["Refunds are accepted within 30 days of the original purchase date."],
            ["Same-day delivery is offered in New York, Chicago, and Los Angeles."],
        ],
        "ground_truth": [
            "Refunds are available within 30 days.",
            "New York, Chicago, and Los Angeles.",
        ],
    }
    return Dataset.from_dict(rows)


def main() -> None:
    # Imported lazily so the module imports cleanly even without ragas installed.
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,          # generator: claims supported by contexts?
        answer_relevancy,      # generator: answer addresses the question?
        context_precision,     # retriever: relevant chunks ranked high?
        context_recall,        # retriever: all needed chunks retrieved? (uses ground_truth)
    )

    dataset = build_eval_dataset()

    # ragas uses an LLM + embeddings under the hood (LLM-as-judge style). Defaults to OpenAI.
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )

    print("Per-metric scores (0..1, higher is better):")
    print(result)

    # WHY convert to a DataFrame: inspect PER-ROW so you can see which question failed and
    # on which half. Averages hide a single broken row.
    df = result.to_pandas()
    print("\nPer-row breakdown:")
    print(df[["question", "faithfulness", "answer_relevancy",
              "context_precision", "context_recall"]].to_string(index=False))

    # Example of a hard gate you'd enforce in CI:
    if df["faithfulness"].min() < 0.9:
        print("\nFAIL: at least one answer is not fully grounded (possible hallucination).")


if __name__ == "__main__":
    main()
