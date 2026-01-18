"""
RSA-PoC v4.0 — Calibration Gate
Implements §6 of v40_design_freeze.md

Verifies environment discriminativeness:
- Oracle (scripted optimal) ≥ 95% success
- ASB Null (uniform random) ≤ 10% success
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from .core.harness import ASBNullAgent, RunMetrics
from .core.oracle import OracleRunner


# ============================================================================
# §6.1 — Calibration Thresholds
# ============================================================================

TAU = 0.95  # Oracle success rate threshold
EPSILON = 0.10  # ASB Null success rate threshold
CALIBRATION_EPISODES = 100  # Per §6.2


# ============================================================================
# §6.2 — Calibration Protocol
# ============================================================================


@dataclass
class CalibrationResult:
    """Result of calibration gate check."""
    oracle_success_rate: float
    asb_null_success_rate: float
    oracle_passed: bool
    asb_null_passed: bool
    overall_passed: bool
    error_message: str = ""


def run_calibration(seeds: List[int] = None) -> CalibrationResult:
    """
    Run calibration protocol per §6.2.

    1. Run Human Oracle for 100 episodes across all seeds
    2. Verify success rate ≥ τ = 0.95
    3. Run ASB Null for 100 episodes across all seeds
    4. Verify success rate ≤ ε = 0.10

    Args:
        seeds: Seeds to use (default: preregistered seeds)

    Returns:
        CalibrationResult with pass/fail status
    """
    if seeds is None:
        seeds = [42, 123, 456, 789, 1024]

    # Run Oracle across seeds
    oracle_successes = 0
    oracle_total = 0

    for seed in seeds:
        runner = OracleRunner(seed=seed, max_episodes=CALIBRATION_EPISODES)
        result = runner.run()
        oracle_successes += result["successes"]
        oracle_total += result["episodes"]

    oracle_success_rate = oracle_successes / oracle_total if oracle_total > 0 else 0.0

    # Run ASB Null across seeds
    asb_successes = 0
    asb_total = 0

    for seed in seeds:
        agent = ASBNullAgent(seed=seed, max_episodes=CALIBRATION_EPISODES)
        metrics = agent.run()
        asb_successes += int(metrics.success_rate * metrics.episodes)
        asb_total += metrics.episodes

    asb_null_success_rate = asb_successes / asb_total if asb_total > 0 else 0.0

    # Check thresholds
    oracle_passed = oracle_success_rate >= TAU
    asb_null_passed = asb_null_success_rate <= EPSILON
    overall_passed = oracle_passed and asb_null_passed

    error_message = ""
    if not oracle_passed:
        error_message += f"Oracle failed: {oracle_success_rate:.2%} < {TAU:.0%}. "
    if not asb_null_passed:
        error_message += f"ASB Null failed: {asb_null_success_rate:.2%} > {EPSILON:.0%}. "

    return CalibrationResult(
        oracle_success_rate=oracle_success_rate,
        asb_null_success_rate=asb_null_success_rate,
        oracle_passed=oracle_passed,
        asb_null_passed=asb_null_passed,
        overall_passed=overall_passed,
        error_message=error_message.strip()
    )


def calibration_report(result: CalibrationResult) -> str:
    """Generate human-readable calibration report."""
    lines = [
        "=" * 60,
        "RSA-PoC v4.0 — Calibration Gate Report",
        f"Timestamp: {datetime.now().isoformat()}",
        "=" * 60,
        "",
        "§6.1 Thresholds:",
        f"  τ (Oracle min):     {TAU:.0%}",
        f"  ε (ASB Null max):   {EPSILON:.0%}",
        "",
        "§6.2 Results:",
        f"  Oracle success rate:    {result.oracle_success_rate:.2%} {'✓' if result.oracle_passed else '✗'}",
        f"  ASB Null success rate:  {result.asb_null_success_rate:.2%} {'✓' if result.asb_null_passed else '✗'}",
        "",
        "Gate Status:",
    ]

    if result.overall_passed:
        lines.append("  ✓ PASSED — Environment is discriminative")
    else:
        lines.append("  ✗ FAILED — INVALID_RUN / ENV_NOT_DISCRIMINATIVE")
        lines.append(f"  Error: {result.error_message}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


# ============================================================================
# CLI Entry Point
# ============================================================================


def main():
    """Run calibration and print report."""
    print("Running v4.0 Calibration Gate...")
    print("This may take a few minutes...")
    print()

    result = run_calibration()
    print(calibration_report(result))

    return 0 if result.overall_passed else 1


if __name__ == "__main__":
    exit(main())
