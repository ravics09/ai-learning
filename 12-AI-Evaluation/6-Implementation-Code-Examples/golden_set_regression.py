"""
golden_set_regression.py
========================
Evals are the unit tests of an AI system. This script is a CI GATE: it runs a versioned
golden set through your system, scores each row, computes PER-SLICE aggregates, compares
against a saved baseline, and EXITS NON-ZERO if quality regressed -> which fails the CI
check and blocks the merge.

Two gates (you want both):
  1) absolute threshold : score >= --fail-under
  2) baseline diff       : no slice dropped more than --max-slice-drop vs baseline

WHY per-slice: a model change can raise the AVERAGE while tanking a low-volume, high-value
slice (e.g., "legal" queries). Averages hide that; slices catch it.

Run:
    python golden_set_regression.py --fail-under 0.9 --max-slice-drop 0.03
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict


# --- The golden set (normally golden.jsonl in Git; inlined here to be self-contained) ----
GOLDEN = [
    {"id": "billing-1", "slice": "billing", "input": "How do I update my card?",
     "expected_keywords": ["payment", "card"]},
    {"id": "refund-1", "slice": "refunds", "input": "What is the refund window?",
     "expected_keywords": ["30", "days"]},
    {"id": "refund-2", "slice": "refunds", "input": "Can I get a refund after 60 days?",
     "expected_keywords": ["no", "30"]},
    {"id": "tech-1", "slice": "technical", "input": "The app crashes on login.",
     "expected_keywords": ["restart", "update"]},
]


def run_system(user_input: str) -> str:
    """
    STUB for your real LLM/RAG/agent call. Replace with a real invocation.
    We fake deterministic outputs so the example runs offline and reproducibly.
    """
    canned = {
        "How do I update my card?": "Go to payment settings and update your card.",
        "What is the refund window?": "Refunds are available within 30 days.",
        "Can I get a refund after 60 days?": "No, refunds are only within 30 days.",
        "The app crashes on login.": "Please update the app, then restart your device.",
    }
    return canned.get(user_input, "I'm not sure.")


def score_row(output: str, expected_keywords: list[str]) -> float:
    """
    A cheap DETERMINISTIC scorer (keyword coverage). WHY deterministic first: it's ~free and
    runs on 100% of rows. In practice you'd ALSO run LLM-judge metrics on PRs/nightly. Score
    = fraction of expected keywords present.
    """
    out = output.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in out)
    return hits / len(expected_keywords)


def evaluate() -> dict[str, float]:
    """Run the golden set; return per-slice mean scores plus an overall mean."""
    per_slice = defaultdict(list)
    for row in GOLDEN:
        out = run_system(row["input"])
        per_slice[row["slice"]].append(score_row(out, row["expected_keywords"]))

    scores = {s: sum(v) / len(v) for s, v in per_slice.items()}
    all_vals = [x for v in per_slice.values() for x in v]
    scores["__overall__"] = sum(all_vals) / len(all_vals)
    return scores


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail-under", type=float, default=0.9,
                    help="Absolute minimum acceptable overall score.")
    ap.add_argument("--max-slice-drop", type=float, default=0.03,
                    help="Max allowed drop for any slice vs baseline.")
    ap.add_argument("--baseline", default="baseline_scores.json",
                    help="Path to saved baseline scores (from main branch).")
    ap.add_argument("--update-baseline", action="store_true",
                    help="Write current scores as the new baseline and exit 0.")
    args = ap.parse_args()

    scores = evaluate()
    print("Per-slice scores:")
    for k, v in sorted(scores.items()):
        print(f"  {k:<14} {v:.3f}")

    if args.update_baseline:
        with open(args.baseline, "w") as f:
            json.dump(scores, f, indent=2)
        print(f"Baseline written to {args.baseline}")
        return 0

    failures: list[str] = []

    # Gate 1: absolute threshold on the overall score.
    if scores["__overall__"] < args.fail_under:
        failures.append(f"overall {scores['__overall__']:.3f} < fail-under {args.fail_under}")

    # Gate 2: per-slice regression vs baseline (if a baseline exists).
    try:
        with open(args.baseline) as f:
            baseline = json.load(f)
        for slice_name, cur in scores.items():
            base = baseline.get(slice_name)
            if base is not None and (base - cur) > args.max_slice_drop:
                failures.append(
                    f"slice '{slice_name}' dropped {base - cur:.3f} "
                    f"(> {args.max_slice_drop}) : {base:.3f} -> {cur:.3f}")
    except FileNotFoundError:
        print(f"(no baseline at {args.baseline}; run with --update-baseline on main)")

    if failures:
        print("\nEVAL GATE FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1  # non-zero -> CI check fails -> merge blocked

    print("\nEVAL GATE PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
