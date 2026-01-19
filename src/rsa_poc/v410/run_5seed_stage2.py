#!/usr/bin/env python3
"""
RSA-PoC v4.1 — 5-Seed Replication Runner

Staged execution per frozen protocol:
  Stage 1: Baseline replication (LLM) for remaining seeds
  Stage 2: Fast checks (Task Oracle, ASB Null, Ablation D)
  Stage 3: Expensive ablations (A, B, C)

Preregistered seeds: [42, 123, 456, 789, 1024]
Seed 42 already complete.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v410.calibration import (
    TaskOracleCalibration,
    TaskOracleCalibrationConfig,
    ASBNullCalibration,
    ASBNullCalibrationConfig,
)
from src.rsa_poc.v410.ablations import (
    AblationType,
    AblationHarness,
)
from src.rsa_poc.v410.harness import HarnessConfig
from src.rsa_poc.v410.deliberator import DeterministicDeliberator
from src.rsa_poc.v410.env import TriDemandV410

# Frozen protocol parameters
FROZEN_H = 40
FROZEN_E = 20
FROZEN_SEEDS = [42, 123, 456, 789, 1024]
REMAINING_SEEDS = [123, 456, 789, 1024]

# Calibration parameters
CALIBRATION_E = 100

# Guardrail thresholds
C_MIN = 0.70
H_MAX = 0.20
A_MAX = 0.10

# Calibration thresholds
TASK_ORACLE_MIN = 0.95
ASB_NULL_MAX = 0.10


def save_result(result: Dict[str, Any], prefix: str, seed: int) -> Path:
    """Save result to JSON file."""
    results_dir = Path(__file__).parent.parent.parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_seed{seed}_{timestamp}.json"
    filepath = results_dir / filename

    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    return filepath


def run_stage2_fast_checks(seed: int) -> Dict[str, Any]:
    """
    Stage 2: Fast checks for a single seed.

    - Task Oracle calibration (should be ≥95% success)
    - ASB Null calibration (should be ≤10% success)
    - Ablation D (should be 100% halt)

    Returns dict with pass/fail status for each check.
    """
    print(f"\n{'='*60}")
    print(f"STAGE 2: Fast Checks (seed={seed})")
    print(f"{'='*60}")

    results = {
        "seed": seed,
        "stage": "2_FAST_CHECKS",
        "checks": {}
    }
    all_passed = True

    # Task Oracle
    print(f"\n[1/3] Task Oracle (E={CALIBRATION_E}, H={FROZEN_H})...")
    task_config = TaskOracleCalibrationConfig(
        max_steps_per_episode=FROZEN_H,
        max_episodes=CALIBRATION_E,
        seed=seed
    )
    task_cal = TaskOracleCalibration(task_config)
    task_result = task_cal.run()

    task_passed = task_result['summary']['success_rate'] >= TASK_ORACLE_MIN
    results['checks']['task_oracle'] = {
        'success_rate': task_result['summary']['success_rate'],
        'threshold': TASK_ORACLE_MIN,
        'passed': task_passed
    }

    status = "✅ PASS" if task_passed else "❌ FAIL"
    print(f"       Success rate: {task_result['summary']['success_rate']:.2%} {status}")

    if not task_passed:
        all_passed = False
        print(f"       STOP: Task Oracle failed for seed {seed}")
        results['all_passed'] = False
        return results

    # ASB Null
    print(f"\n[2/3] ASB Null (E={CALIBRATION_E}, H={FROZEN_H})...")
    asb_config = ASBNullCalibrationConfig(
        max_steps_per_episode=FROZEN_H,
        max_episodes=CALIBRATION_E,
        seed=seed
    )
    asb_cal = ASBNullCalibration(asb_config)
    asb_result = asb_cal.run()

    # ASB Null success rate is computed from episodes
    asb_successes = sum(1 for ep in asb_result['episodes']
                        if ep.get('success', False))
    asb_success_rate = asb_successes / CALIBRATION_E

    asb_passed = asb_success_rate <= ASB_NULL_MAX
    results['checks']['asb_null'] = {
        'success_rate': asb_success_rate,
        'threshold': ASB_NULL_MAX,
        'halt_rate': asb_result['summary']['halt_rate'],
        'passed': asb_passed
    }

    status = "✅ PASS" if asb_passed else "❌ FAIL"
    print(f"       Success rate: {asb_success_rate:.2%} (≤{ASB_NULL_MAX:.0%} required) {status}")
    print(f"       Halt rate: {asb_result['summary']['halt_rate']:.2%} (should be 0%)")

    if not asb_passed:
        all_passed = False
        print(f"       STOP: ASB Null failed for seed {seed}")
        results['all_passed'] = False
        return results

    # Ablation D
    print(f"\n[3/3] Ablation D: Trace Excision (E={FROZEN_E}, H={FROZEN_H})...")

    # Run Ablation D directly
    env = TriDemandV410(seed=seed)
    config = HarnessConfig(
        max_steps_per_episode=FROZEN_H,
        max_episodes=FROZEN_E,
        seed=seed
    )
    deliberator = DeterministicDeliberator()
    harness = AblationHarness(
        env=env,
        ablation_type=AblationType.TRACE_EXCISION,
        config=config,
        deliberator=deliberator,
        seed=seed
    )
    ablation_d_result = harness.run()

    expected_halts = FROZEN_H * FROZEN_E
    actual_halts = ablation_d_result['summary']['total_halts']
    total_steps = ablation_d_result['summary']['total_steps']

    # Trace excision causes HALT at step 0 of every episode
    # So total_steps may be 0 (no steps executed, all HALTs)
    # We count attempts = E * H (how many step attempts were made)
    attempts = FROZEN_H * FROZEN_E
    halt_rate = actual_halts / attempts if attempts > 0 else 0

    d_passed = actual_halts == expected_halts

    results['checks']['ablation_d'] = {
        'expected_halts': expected_halts,
        'actual_halts': actual_halts,
        'halt_rate': halt_rate,
        'passed': d_passed
    }

    status = "✅ PASS" if d_passed else "❌ FAIL"
    print(f"       Halts: {actual_halts}/{expected_halts} ({halt_rate:.0%}) {status}")

    if not d_passed:
        all_passed = False
        print(f"       STOP: Ablation D failed for seed {seed}")

    results['all_passed'] = all_passed

    # Save results
    filepath = save_result(results, "v410_stage2_fast", seed)
    print(f"\nResults saved to: {filepath}")

    return results


def print_stage2_summary(all_results: List[Dict[str, Any]]):
    """Print summary table for Stage 2 results."""
    print(f"\n{'='*60}")
    print("STAGE 2 SUMMARY")
    print(f"{'='*60}")
    print()
    print(f"| Seed | Task Oracle | ASB Null | Ablation D | Status |")
    print(f"|------|-------------|----------|------------|--------|")

    for r in all_results:
        seed = r['seed']
        task = r['checks'].get('task_oracle', {})
        asb = r['checks'].get('asb_null', {})
        abl_d = r['checks'].get('ablation_d', {})

        task_str = f"{task.get('success_rate', 0):.0%}" if task else "—"
        asb_str = f"{asb.get('success_rate', 0):.0%}" if asb else "—"
        d_str = f"{abl_d.get('halt_rate', 0):.0%}" if abl_d else "—"

        status = "✅ PASS" if r.get('all_passed', False) else "❌ FAIL"

        print(f"| {seed:4d} | {task_str:>11} | {asb_str:>8} | {d_str:>10} | {status} |")

    print()
    passed = sum(1 for r in all_results if r.get('all_passed', False))
    print(f"Passed: {passed}/{len(all_results)}")


def main():
    print("=" * 60)
    print("RSA-PoC v4.1 — 5-Seed Replication")
    print("=" * 60)
    print()
    print("Frozen Protocol:")
    print(f"  H = {FROZEN_H}")
    print(f"  E = {FROZEN_E}")
    print(f"  Seeds = {FROZEN_SEEDS}")
    print()
    print("Seed 42 already complete (1_SEED_COMPLETE).")
    print(f"Running remaining seeds: {REMAINING_SEEDS}")
    print()
    print("This script runs Stage 2 (fast checks) only.")
    print("Stage 1 (LLM baseline) and Stage 3 (LLM ablations) require")
    print("separate execution due to cost/time (~45 min per seed).")
    print()

    # Run Stage 2 for all remaining seeds
    all_results = []

    for i, seed in enumerate(REMAINING_SEEDS):
        print(f"\n[Seed {i+1}/{len(REMAINING_SEEDS)}] Running fast checks for seed={seed}...")
        result = run_stage2_fast_checks(seed)
        all_results.append(result)

    # Summary
    print_stage2_summary(all_results)

    # Determine next step
    all_passed = all(r.get('all_passed', False) for r in all_results)

    if all_passed:
        print("\n✅ All Stage 2 checks passed.")
        print("\nNext: Run Stage 1 (LLM baseline) for each seed.")
        print("Command: python run_5seed_baseline.py --seed <SEED>")
        return 0
    else:
        failed_seeds = [r['seed'] for r in all_results if not r.get('all_passed', False)]
        print(f"\n❌ Stage 2 failed for seeds: {failed_seeds}")
        print("Investigate before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
