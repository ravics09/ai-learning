"""
drift_detection.py
==================
Detect data drift with PSI (Population Stability Index) and the KS test.

WHY THIS MATTERS
----------------
Models decay because the world changes while the weights stay frozen. You often
can't measure accuracy live (labels arrive late or never), so you watch the
INPUTS instead: if production data drifts far from the training distribution,
that's an early warning to investigate or retrain.

Two complementary tests:
  - PSI: an interpretable MAGNITUDE of shift with actionable thresholds.
  - KS : a statistical test for "are these two samples from the same dist?"

KEY GOTCHA (anti-noise):
  KS is oversensitive on large samples - it flags tiny, meaningless shifts and
  causes alert fatigue. So we ALERT only when KS is significant AND PSI shows a
  meaningful magnitude. This mirrors how mature teams cut false pages.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import ks_2samp

# PSI rules of thumb (industry standard):
PSI_STABLE = 0.10      # < 0.10  -> stable
PSI_ACTION = 0.20      # > 0.20  -> significant shift, act
KS_ALPHA = 0.05        # significance level for the KS test


def psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index between a reference and current sample.

    WHY quantile bins on the reference: equal-population buckets make PSI robust
    to skewed distributions (vs fixed-width bins that can be nearly empty).
    """
    # Build bin edges from the reference distribution's quantiles.
    cuts = np.percentile(reference, np.linspace(0, 100, bins + 1))
    cuts[0], cuts[-1] = -np.inf, np.inf  # WHY: capture out-of-range live values

    # +1e-6 avoids log(0)/divide-by-zero when a bin is empty.
    ref_pct = np.histogram(reference, cuts)[0] / len(reference) + 1e-6
    cur_pct = np.histogram(current, cuts)[0] / len(current) + 1e-6

    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


@dataclass
class DriftResult:
    feature: str
    psi: float
    ks_pvalue: float
    drifted: bool
    severity: str
    should_alert: bool


def check_feature(name: str, reference: np.ndarray, current: np.ndarray) -> DriftResult:
    p = psi(reference, current)
    ks_stat, ks_p = ks_2samp(reference, current)

    if p < PSI_STABLE:
        severity = "stable"
    elif p < PSI_ACTION:
        severity = "moderate"
    else:
        severity = "significant"

    ks_significant = ks_p < KS_ALPHA
    drifted = p >= PSI_ACTION or ks_significant

    # ANTI-NOISE: require BOTH a significant KS p-value AND a meaningful PSI
    # magnitude before paging a human. Either one alone is too trigger-happy.
    should_alert = ks_significant and p >= PSI_ACTION

    return DriftResult(name, round(p, 4), round(float(ks_p), 4),
                       drifted, severity, should_alert)


def main() -> None:
    rng = np.random.default_rng(0)

    # Reference = training-time distribution.
    reference = rng.normal(loc=0.0, scale=1.0, size=10_000)

    # Case 1: no real drift (same distribution, new sample).
    stable = rng.normal(loc=0.0, scale=1.0, size=5_000)
    # Case 2: real drift (mean shifted -> covariate shift).
    shifted = rng.normal(loc=0.8, scale=1.2, size=5_000)

    for label, sample in [("age_stable", stable), ("age_shifted", shifted)]:
        r = check_feature(label, reference, sample)
        print(f"{r.feature:12s} PSI={r.psi:<7} KS_p={r.ks_pvalue:<8} "
              f"severity={r.severity:<11} alert={r.should_alert}")

    print("\nInterpretation: feature drift -> open a ticket and investigate.")
    print("If model QUALITY also drops (once labels arrive) -> page + retrain.")


if __name__ == "__main__":
    main()
