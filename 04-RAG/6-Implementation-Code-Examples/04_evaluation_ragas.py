"""
04 — Evaluating RAG with RAGAS.

You cannot ship what you cannot measure. Evaluate RETRIEVAL and GENERATION
separately:
  - faithfulness      -> is the answer supported by the context? (hallucination)
  - answer_relevancy  -> does it address the question?
  - context_precision -> was the retrieved context on-target?
  - context_recall    -> did we retrieve everything needed?

Diagnosis rule:
  low faithfulness + high recall  -> prompt/generation problem
  low context recall              -> retrieval problem

Run this in CI against a GOLDEN SET and gate deploys on no regression.

Run:   python 04_evaluation_ragas.py
Needs: OPENAI_API_KEY (RAGAS uses an LLM judge) + ragas, datasets
"""
from __future__ import annotations

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

# A tiny golden set. In practice, curate 100-500 real questions with
# known-correct answers and the source chunks that should be retrieved.
golden = {
    "question": [
        "What is the refund window?",
        "How much is the Enterprise plan?",
    ],
    "answer": [  # your RAG system's generated answers
        "You can return items within 30 days with a receipt.",
        "The Enterprise plan is $99 per user per month.",
    ],
    "contexts": [  # chunks your retriever returned for each question
        ["Refund policy allows returns within 30 days of purchase with a receipt."],
        ["The Enterprise plan costs $99/user/month and includes SSO and audit logs."],
    ],
    "ground_truth": [  # reference answers
        "Returns are allowed within 30 days with a receipt.",
        "It costs $99 per user per month.",
    ],
}


def main():
    dataset = Dataset.from_dict(golden)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    print(result)
    # In CI: assert result["faithfulness"] >= threshold, else fail the build.


if __name__ == "__main__":
    main()
