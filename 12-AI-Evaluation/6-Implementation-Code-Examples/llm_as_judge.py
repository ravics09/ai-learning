"""
llm_as_judge.py
===============
LLM-as-a-judge is the most common eval method in 2025-2026 for open-ended quality that
BLEU/ROUGE can't capture. But a raw judge is biased and uncalibrated. This file shows the
two things that make a judge trustworthy in an interview answer:

  1) PAIRWISE with POSITION-SWAP  -> neutralizes position bias
  2) CALIBRATION vs human labels via Cohen's kappa -> proves the judge agrees with people

Run:
    export OPENAI_API_KEY=sk-...
    python llm_as_judge.py
"""
from __future__ import annotations

import json
from dataclasses import dataclass


# --- The judge prompt --------------------------------------------------------------------
# WHY we spell out "ignore length and formatting": verbosity/formatting bias make judges
# prefer longer, prettier answers regardless of correctness. Instructing against it is the
# cheapest mitigation. We also force JSON so the verdict is machine-parseable.
JUDGE_PROMPT = """You are a strict, impartial evaluator.
Compare two answers (A and B) to the user's question.
Judge ONLY factual correctness and helpfulness. IGNORE length, verbosity, and formatting.
Respond ONLY as JSON: {{"winner": "A" | "B" | "tie", "reason": "<one sentence>"}}.

Question: {q}
Answer A: {a}
Answer B: {b}"""


def _raw_judge(client, model: str, q: str, a: str, b: str) -> str:
    """Single directional judgement. Returns 'A' | 'B' | 'tie'."""
    resp = client.chat.completions.create(
        model=model,
        temperature=0,  # WHY: determinism -> reproducible eval scores in CI
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(q=q, a=a, b=b)}],
    )
    return json.loads(resp.choices[0].message.content)["winner"]


def judge_pairwise(client, q: str, ans1: str, ans2: str, model: str = "gpt-4o") -> str:
    """
    Compare ans1 vs ans2 while controlling for POSITION BIAS.

    We run the comparison twice with the answers in opposite slots. If the verdict flips
    when we swap positions, the judge is being swayed by ORDER, not content -> we return
    'tie' (low confidence) instead of a bogus winner.
    """
    fwd = _raw_judge(client, model, q, ans1, ans2)          # ans1 = A
    rev = _raw_judge(client, model, q, ans2, ans1)          # ans1 = B now
    # Translate the reverse verdict back into ans1/ans2 terms.
    rev_mapped = {"A": "B", "B": "A", "tie": "tie"}[rev]
    if fwd == rev_mapped:
        return {"A": "ans1", "B": "ans2", "tie": "tie"}[fwd]  # consistent -> trustworthy
    return "tie"                                              # inconsistent -> biased/unsure


# --- Calibration: is the judge even any good? --------------------------------------------
def cohens_kappa(judge_labels: list[str], human_labels: list[str]) -> float:
    """
    Cohen's kappa = chance-corrected agreement. WHY not plain accuracy? If 90% of items are
    'A', a judge that always says 'A' looks 90% accurate but has learned nothing. Kappa
    subtracts the agreement you'd expect by chance. Rule of thumb: kappa >= ~0.6 to trust.
    """
    assert len(judge_labels) == len(human_labels)
    n = len(judge_labels)
    categories = set(judge_labels) | set(human_labels)

    observed = sum(j == h for j, h in zip(judge_labels, human_labels)) / n  # p_o

    expected = 0.0  # p_e: probability of chance agreement
    for c in categories:
        p_judge = judge_labels.count(c) / n
        p_human = human_labels.count(c) / n
        expected += p_judge * p_human

    if expected == 1.0:            # avoid divide-by-zero when everything is one class
        return 1.0
    return (observed - expected) / (1 - expected)


@dataclass
class Example:
    question: str
    answer_a: str
    answer_b: str
    human_winner: str  # 'ans1' | 'ans2' | 'tie'  -> the calibration ground truth


def main() -> None:
    from openai import OpenAI  # imported lazily so the file imports without a key set
    client = OpenAI()

    # A tiny calibration anchor set. In practice you'd have ~100 human-labeled rows.
    dataset = [
        Example(
            question="What is the capital of France?",
            answer_a="The capital of France is Paris.",
            answer_b="France's capital is Lyon.",
            human_winner="ans1",
        ),
        Example(
            question="Is water wet at room temperature?",
            answer_a="No, water is always dry.",
            answer_b="Yes, liquid water at room temperature is wet.",
            human_winner="ans2",
        ),
    ]

    judge_labels, human_labels = [], []
    for ex in dataset:
        verdict = judge_pairwise(client, ex.question, ex.answer_a, ex.answer_b)
        judge_labels.append(verdict)
        human_labels.append(ex.human_winner)
        print(f"Q: {ex.question}\n  judge={verdict}  human={ex.human_winner}\n")

    k = cohens_kappa(judge_labels, human_labels)
    print(f"Judge<->human Cohen's kappa = {k:.2f}")
    print("Trustworthy for CI gating." if k >= 0.6 else "Recalibrate: fix rubric / judge model.")


if __name__ == "__main__":
    main()
