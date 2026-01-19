#!/usr/bin/env python3
"""
RSA-PoC v4.2 — Calibration Runner

Runs calibration baselines:
1. Task Oracle v4.2 - Must succeed ≥95% AND issue valid repairs
2. ASB Null v4.2 - Expected to HALT at contradictions

This validates:
- Environment is solvable with LAW_REPAIR
- Repair is necessary (ASB Null fails without it)
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v420.calibration import (
    TaskOracleCalibrationV420,
    TaskOracleCalibrationConfigV420,
    ASBNullBaselineV420,
    ASBNullConfigV420,
)


def run_task_oracle_calibration():
    """Run Task Oracle v4.2 calibration."""
    print("=" * 60)
    print("RSA-PoC v4.2 — Task Oracle Calibration")
    print("=" * 60)
    print()
    print("Purpose: Validate environment solvability with LAW_REPAIR")
    print("Requirements:")
    print("  - Task Oracle success ≥ τ (0.95)")
    print("  - At least one valid LAW_REPAIR issued")
    print()

    config = TaskOracleCalibrationConfigV420(
        max_steps_per_episode=40,
        max_episodes=100,
        seed=42
    )

    print(f"Parameters:")
    print(f"  H (steps/episode): {config.max_steps_per_episode}")
    print(f"  E (episodes):      {config.max_episodes}")
    print(f"  Seed:              {config.seed}")
    print()

    print("Running Task Oracle v4.2 calibration...")
    cal = TaskOracleCalibrationV420(config)
    result = cal.run()

    # Display results
    summary = result['summary']
    print()
    print("-" * 60)
    print("Task Oracle v4.2 Results:")
    print("-" * 60)
    print(f"  Total steps:          {summary['total_steps']}")
    print(f"  Total successes:      {summary['total_successes']}")
    print(f"  Success rate:         {summary['success_rate']:.2%}")
    print(f"  Repairs issued:       {summary['total_repairs_issued']}")
    print(f"  Repairs accepted:     {summary['total_repairs_accepted']}")
    print(f"  Repair accept rate:   {summary['repair_acceptance_rate']:.2%}")
    print(f"  Elapsed:              {summary['elapsed_ms']:.1f}ms")
    print()

    passed = summary['calibration_passed']
    if passed:
        print("✅ TASK ORACLE CALIBRATION PASSED")
        print(f"   Success rate ({summary['success_rate']:.2%}) ≥ τ (95%)")
        print(f"   Repairs issued and accepted ({summary['total_repairs_accepted']})")
    else:
        print("❌ TASK ORACLE CALIBRATION FAILED")
        if summary['success_rate'] < 0.95:
            print(f"   Success rate ({summary['success_rate']:.2%}) < τ (95%)")
        if summary['total_repairs_accepted'] == 0:
            print(f"   No repairs issued/accepted")
    print()

    return result


def run_asb_null_baseline():
    """Run ASB Null v4.2 baseline."""
    print("=" * 60)
    print("RSA-PoC v4.2 — ASB Null Baseline")
    print("=" * 60)
    print()
    print("Purpose: Demonstrate repair is necessary")
    print("Expected: HALT at contradictions (no repair capability)")
    print()

    config = ASBNullConfigV420(
        max_steps_per_episode=40,
        max_episodes=100,
        seed=42
    )

    print(f"Parameters:")
    print(f"  H (steps/episode): {config.max_steps_per_episode}")
    print(f"  E (episodes):      {config.max_episodes}")
    print(f"  Seed:              {config.seed}")
    print()

    print("Running ASB Null v4.2 baseline...")
    baseline = ASBNullBaselineV420(config)
    result = baseline.run()

    # Display results
    summary = result['summary']
    print()
    print("-" * 60)
    print("ASB Null v4.2 Results:")
    print("-" * 60)
    print(f"  Total steps:          {summary['total_steps']}")
    print(f"  Total successes:      {summary['total_successes']}")
    print(f"  Success rate:         {summary['success_rate']:.2%}")
    print(f"  Total halts:          {summary['total_halts']}")
    print(f"  Halt rate:            {summary['halt_rate']:.2%}")
    print(f"  Elapsed:              {summary['elapsed_ms']:.1f}ms")
    print()

    # ASB Null demonstrates repair necessity via halts or low success
    demonstrates_necessity = summary['demonstrates_repair_necessity']
    if demonstrates_necessity:
        print("✅ ASB NULL DEMONSTRATES REPAIR NECESSITY")
        print(f"   Halts: {summary['total_halts']}, Success rate: {summary['success_rate']:.2%}")
        print("   Contradiction detection works; repair needed for progress")
    else:
        print("⚠️  ASB NULL UNEXPECTED BEHAVIOR")
        print("   May indicate environment issue")
    print()

    return result


def main():
    print()
    print("=" * 70)
    print("RSA-PoC v4.2 — CALIBRATION SUITE")
    print("=" * 70)
    print()

    # Run both calibrations
    task_oracle_result = run_task_oracle_calibration()
    asb_null_result = run_asb_null_baseline()

    # Combined summary
    print("=" * 60)
    print("CALIBRATION SUMMARY")
    print("=" * 60)
    print()

    to_passed = task_oracle_result['summary']['calibration_passed']
    asb_demonstrates = asb_null_result['summary']['demonstrates_repair_necessity']

    if to_passed and asb_demonstrates:
        print("✅ CALIBRATION SUITE PASSED")
        print("   - Task Oracle demonstrates solvability with repair")
        print("   - ASB Null demonstrates repair necessity")
        calibration_passed = True
    else:
        print("❌ CALIBRATION SUITE INCOMPLETE")
        if not to_passed:
            print("   - Task Oracle failed calibration gate")
        if not asb_demonstrates:
            print("   - ASB Null did not demonstrate repair necessity")
        calibration_passed = False
    print()

    # Save results
    results_dir = Path(__file__).parent.parent.parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v420_calibration_{timestamp}.json"
    filepath = results_dir / filename

    combined_result = {
        "version": "v4.2.0",
        "timestamp": timestamp,
        "calibration_passed": calibration_passed,
        "task_oracle": task_oracle_result,
        "asb_null": asb_null_result
    }

    with open(filepath, 'w') as f:
        json.dump(combined_result, f, indent=2)

    print(f"Results saved to: {filepath}")
    print()

    return 0 if calibration_passed else 1


if __name__ == "__main__":
    sys.exit(main())
