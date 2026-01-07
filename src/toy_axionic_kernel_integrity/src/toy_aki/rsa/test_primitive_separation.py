"""
RSA v2.0 Test #7: Primitive Separation Check

Verifies that v2.0 action primitives produce behavioral differences
from pure v1.0 generators when used in adaptive context.

Test procedure:
1. Run Model F (OUTCOME_TOGGLE) with v2.0 primitives (5 seeds)
2. Run v1.0 baseline with equivalent fixed schedule (5 seeds)
3. Compare key metrics (constitutional integrity, eligibility, CTA passage)
4. Pass if ANY metric differs by ≥0.05 across aggregated runs

Acceptance criteria:
- Must detect ≥0.05 difference on at least one metric
- Demonstrates primitives enable behavioral variation beyond v1.0
- Must run before adversarial runs (preregistered separation check)
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np


@dataclass
class SeparationTestResult:
    """Results from primitive separation test."""
    v2_metrics: Dict[str, float]
    v1_metrics: Dict[str, float]
    differences: Dict[str, float]
    max_difference: float
    max_difference_metric: str
    passes: bool  # True if max_difference >= 0.05


def compute_metric_aggregates(run_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute aggregate metrics across multiple runs.

    Args:
        run_results: List of run result dicts

    Returns:
        Dict of metric name -> mean value
    """
    metrics = {
        "constitutional_integrity": [],
        "eligibility_maintenance": [],
        "cta_passage": [],
        "authority_age_mean": [],
        "succession_count": [],
    }

    for result in run_results:
        summary = result.get("summary", {})
        metrics["constitutional_integrity"].append(summary.get("constitutional_integrity", 1.0))
        metrics["eligibility_maintenance"].append(summary.get("eligibility_maintenance", 0.0))
        metrics["cta_passage"].append(summary.get("cta_passage", 0.0))
        metrics["authority_age_mean"].append(summary.get("authority_age_mean", 0.0))
        metrics["succession_count"].append(summary.get("succession_count", 0))

    return {
        metric: float(np.mean(values)) for metric, values in metrics.items()
    }


def compute_metric_differences(v2_metrics: Dict[str, float], v1_metrics: Dict[str, float]) -> Dict[str, float]:
    """
    Compute absolute differences between v2.0 and v1.0 metrics.

    Args:
        v2_metrics: Aggregated v2.0 metrics
        v1_metrics: Aggregated v1.0 metrics

    Returns:
        Dict of metric name -> absolute difference
    """
    differences = {}
    for metric in v2_metrics:
        if metric in v1_metrics:
            differences[metric] = abs(v2_metrics[metric] - v1_metrics[metric])
    return differences


def run_separation_test(
    v2_run_results: List[Dict[str, Any]],
    v1_run_results: List[Dict[str, Any]],
    threshold: float = 0.05
) -> SeparationTestResult:
    """
    Execute primitive separation test.

    Args:
        v2_run_results: List of v2.0 run results (Model F)
        v1_run_results: List of v1.0 run results (equivalent baseline)
        threshold: Minimum difference threshold (default 0.05)

    Returns:
        SeparationTestResult with comparison details
    """
    # Aggregate metrics
    v2_metrics = compute_metric_aggregates(v2_run_results)
    v1_metrics = compute_metric_aggregates(v1_run_results)

    # Compute differences
    differences = compute_metric_differences(v2_metrics, v1_metrics)

    # Find maximum difference
    if differences:
        max_diff_metric = max(differences, key=differences.get)
        max_diff = differences[max_diff_metric]
    else:
        max_diff_metric = "none"
        max_diff = 0.0

    # Check threshold
    passes = max_diff >= threshold

    return SeparationTestResult(
        v2_metrics=v2_metrics,
        v1_metrics=v1_metrics,
        differences=differences,
        max_difference=max_diff,
        max_difference_metric=max_diff_metric,
        passes=passes
    )


def format_separation_report(result: SeparationTestResult) -> str:
    """
    Format separation test result as readable report.

    Args:
        result: Test result

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append("RSA v2.0 Test #7: Primitive Separation Check")
    lines.append("=" * 80)
    lines.append("")

    lines.append("v2.0 Metrics (Model F with primitives):")
    for metric, value in result.v2_metrics.items():
        lines.append(f"  {metric}: {value:.4f}")
    lines.append("")

    lines.append("v1.0 Metrics (Equivalent baseline):")
    for metric, value in result.v1_metrics.items():
        lines.append(f"  {metric}: {value:.4f}")
    lines.append("")

    lines.append("Absolute Differences:")
    for metric, diff in result.differences.items():
        marker = " ***" if diff >= 0.05 else ""
        lines.append(f"  {metric}: {diff:.4f}{marker}")
    lines.append("")

    lines.append(f"Maximum Difference: {result.max_difference:.4f} ({result.max_difference_metric})")
    lines.append(f"Threshold: 0.05")
    lines.append("")

    if result.passes:
        lines.append("✓ TEST PASSED: Primitives produce measurable behavioral separation")
    else:
        lines.append("✗ TEST FAILED: Primitives do not produce sufficient separation")
        lines.append(f"  Required: ≥0.05 difference on any metric")
        lines.append(f"  Observed: {result.max_difference:.4f} maximum difference")

    lines.append("=" * 80)

    return "\n".join(lines)


if __name__ == "__main__":
    print("RSA v2.0 Test #7: Primitive Separation Check")
    print("This test must be run via harness with actual run results.")
    print("Use rsa_v200_test7_separation.py to execute.")
