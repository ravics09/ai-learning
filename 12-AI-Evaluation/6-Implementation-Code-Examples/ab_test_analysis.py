"""
ab_test_analysis.py
===================
Offline-green does not guarantee an online win. When you A/B test a new prompt/model, a
higher thumbs-up rate is NOT a win until it's STATISTICALLY SIGNIFICANT -- otherwise you
might be shipping noise.

This computes a two-proportion z-test comparing the success rate of Control (A) vs
Treatment (B), plus a Wald confidence interval on the difference. Pure stats -- no API key,
no network.

Run:
    python ab_test_analysis.py
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Arm:
    name: str
    successes: int   # e.g., thumbs-up / task completions
    total: int       # e.g., total requests served to this arm

    @property
    def rate(self) -> float:
        return self.successes / self.total


def two_proportion_z_test(control: Arm, treatment: Arm) -> dict:
    """
    H0: treatment rate == control rate.  We use the POOLED proportion for the standard error
    because under H0 both arms share the same true rate. WHY pooled: it's the standard,
    less-biased SE when testing equality of proportions.
    """
    p_pool = (control.successes + treatment.successes) / (control.total + treatment.total)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / control.total + 1 / treatment.total))
    if se == 0:
        raise ValueError("Zero standard error -- check inputs.")

    diff = treatment.rate - control.rate
    z = diff / se

    # Two-sided p-value from the normal CDF (via erf) -- avoids a scipy dependency here.
    p_value = 2 * (1 - _normal_cdf(abs(z)))

    # 95% CI on the difference uses the UNPOOLED SE (estimating the actual gap, not testing H0).
    se_unpooled = math.sqrt(
        control.rate * (1 - control.rate) / control.total
        + treatment.rate * (1 - treatment.rate) / treatment.total
    )
    margin = 1.96 * se_unpooled
    return {"diff": diff, "z": z, "p_value": p_value,
            "ci95": (diff - margin, diff + margin)}


def _normal_cdf(x: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def main() -> None:
    # Example: control converts 500/5000 (10.0%); treatment 560/5000 (11.2%).
    control = Arm("A_control", successes=500, total=5000)
    treatment = Arm("B_treatment", successes=560, total=5000)

    print(f"{control.name}:   {control.rate:.3%}")
    print(f"{treatment.name}: {treatment.rate:.3%}")

    res = two_proportion_z_test(control, treatment)
    lo, hi = res["ci95"]
    print(f"\nabsolute lift : {res['diff']:+.3%}")
    print(f"z-score       : {res['z']:.2f}")
    print(f"p-value       : {res['p_value']:.4f}")
    print(f"95% CI on lift: [{lo:+.3%}, {hi:+.3%}]")

    # WHY 0.05: conventional significance level. If the CI excludes 0 and p < 0.05, the win
    # is unlikely to be noise. ALSO check guardrails (latency/cost/safety) before rollout.
    if res["p_value"] < 0.05 and lo > 0:
        print("\nSHIP: treatment is a statistically significant win (guardrails permitting).")
    else:
        print("\nHOLD: not significant -- keep collecting data or keep control.")


if __name__ == "__main__":
    main()
