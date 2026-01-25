#!/usr/bin/env python3
"""
RSA-PoC v4.1 — Task Oracle Calibration Runner

Runs Task Oracle calibration to satisfy the calibration gate:
- Task Oracle success ≥ τ (0.95)

This is a solvability witness, not an RSA component.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v410.calibration import (
    TaskOracleCalibration,
    TaskOracleCalibrationConfig,
)


def main():
    print("=" * 60)
    print("RSA-PoC v4.1 — Task Oracle Calibration")
    print("=" * 60)
    print()
    print("Purpose: Validate environment solvability (calibration gate)")
    print("Requirement: Task Oracle success ≥ τ (0.95)")
    print()

    # Configuration per design freeze
    config = TaskOracleCalibrationConfig(
        max_steps_per_episode=40,  # H=40
        max_episodes=100,          # E=100 for calibration
        seed=42
    )

    print(f"Parameters:")
    print(f"  H (steps/episode): {config.max_steps_per_episode}")
    print(f"  E (episodes):      {config.max_episodes}")
    print(f"  Seed:              {config.seed}")
    print()

    # Run calibration
    print("Running Task Oracle calibration...")
    cal = TaskOracleCalibration(config)
    result = cal.run()

    # Display results
    summary = result['summary']
    print()
    print("-" * 60)
    print("Results:")
    print("-" * 60)
    print(f"  Total steps:     {summary['total_steps']}")
    print(f"  Total successes: {summary['total_successes']}")
    print(f"  Success rate:    {summary['success_rate']:.2%}")
    print(f"  Total halts:     {summary['total_halts']}")
    print(f"  Halt rate:       {summary['halt_rate']:.2%}")
    print(f"  Elapsed:         {summary['elapsed_ms']:.1f}ms")
    print()

    # Calibration gate check
    passed = summary['calibration_passed']
    if passed:
        print("✅ CALIBRATION GATE PASSED")
        print(f"   Task Oracle success ({summary['success_rate']:.2%}) ≥ τ (95%)")
    else:
        print("❌ CALIBRATION GATE FAILED")
        print(f"   Task Oracle success ({summary['success_rate']:.2%}) < τ (95%)")
    print()

    # Save results
    results_dir = Path(__file__).parent.parent.parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v410_task_oracle_calibration_{timestamp}.json"
    filepath = results_dir / filename

    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Results saved to: {filepath}")
    print()

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
