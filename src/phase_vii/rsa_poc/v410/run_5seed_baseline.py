#!/usr/bin/env python3
"""
RSA-PoC v4.1 — Stage 1: LLM Baseline Runner

Runs LLM baseline at frozen protocol (H=40, E=20) for a single seed.
Stop condition: If guardrails fail or qualitative divergence, do not proceed.

Usage:
    python run_5seed_baseline.py --seed 123
    python run_5seed_baseline.py --seed 456
    python run_5seed_baseline.py --seed 789
    python run_5seed_baseline.py --seed 1024
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v410.experiment import (
    run_single_experiment,
    ExperimentConfig,
    FROZEN_H,
    FROZEN_E,
    FROZEN_C_MIN,
    FROZEN_H_MAX,
    FROZEN_A_MAX,
)

FROZEN_SEEDS = [42, 123, 456, 789, 1024]


def save_result(result: Dict[str, Any], seed: int) -> Path:
    """Save result to JSON file."""
    results_dir = Path(__file__).parent.parent.parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v410_baseline_seed{seed}_{timestamp}.json"
    filepath = results_dir / filename

    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    return filepath


def check_guardrails(result: Dict[str, Any]) -> Dict[str, Any]:
    """Check if baseline passes guardrails."""
    summary = result.get('summary', {})

    compliance_rate = summary.get('compliance_rate', 0)
    halt_rate = summary.get('halt_rate', 1)
    anomaly_rate = summary.get('anomaly_rate', 0)

    c_pass = compliance_rate >= FROZEN_C_MIN
    h_pass = halt_rate <= FROZEN_H_MAX
    a_pass = anomaly_rate <= FROZEN_A_MAX

    return {
        'compliance_rate': compliance_rate,
        'halt_rate': halt_rate,
        'anomaly_rate': anomaly_rate,
        'c_min_pass': c_pass,
        'h_max_pass': h_pass,
        'a_max_pass': a_pass,
        'all_passed': c_pass and h_pass and a_pass,
        'thresholds': {
            'c_min': FROZEN_C_MIN,
            'h_max': FROZEN_H_MAX,
            'a_max': FROZEN_A_MAX
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM baseline for a single seed"
    )
    parser.add_argument(
        '--seed',
        type=int,
        required=True,
        choices=FROZEN_SEEDS,
        help=f"Seed to run (one of {FROZEN_SEEDS})"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be run without executing"
    )

    args = parser.parse_args()
    seed = args.seed

    print("=" * 60)
    print(f"RSA-PoC v4.1 — Stage 1: LLM Baseline (seed={seed})")
    print("=" * 60)
    print()
    print(f"Protocol: H={FROZEN_H}, E={FROZEN_E}")
    print(f"Deliberator: LLM (Claude Sonnet 4)")
    print(f"Guardrails: C_min={FROZEN_C_MIN}, H_max={FROZEN_H_MAX}, A_max={FROZEN_A_MAX}")
    print()

    if seed == 42:
        print("⚠️  Seed 42 already complete (1_SEED_COMPLETE).")
        print("    Results in: v410_pilot_20260118_144227.json")
        return 0

    if args.dry_run:
        print("[DRY RUN] Would execute:")
        print(f"  - LLM baseline: {FROZEN_E} episodes × {FROZEN_H} steps")
        print(f"  - Expected runtime: ~45 minutes")
        print(f"  - Output: results/v410_baseline_seed{seed}_*.json")
        return 0

    print(f"Starting LLM baseline run...")
    print(f"Expected runtime: ~45 minutes")
    print()

    start_time = datetime.now()

    try:
        config = ExperimentConfig(
            name=f"v410_baseline_seed{seed}",
            max_steps_per_episode=FROZEN_H,
            max_episodes=FROZEN_E,
            use_llm=True
        )
        result = run_single_experiment(
            config=config,
            seed=seed,
            deliberator_type="llm",
            verbose=True
        )
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    elapsed = (datetime.now() - start_time).total_seconds()

    # Add metadata
    result['metadata'] = {
        'seed': seed,
        'stage': '1_BASELINE',
        'protocol': {
            'H': FROZEN_H,
            'E': FROZEN_E
        },
        'elapsed_seconds': elapsed,
        'timestamp': datetime.now().isoformat()
    }

    # Check guardrails
    guardrails = check_guardrails(result)
    result['guardrails'] = guardrails

    # Save
    filepath = save_result(result, seed)
    print(f"\nResults saved to: {filepath}")

    # Print summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    summary = result.get('summary', {})
    print(f"Steps: {summary.get('total_steps', 0)}")
    print(f"Halts: {summary.get('total_halts', 0)} ({guardrails['halt_rate']:.1%})")
    print(f"Compliance: {guardrails['compliance_rate']:.1%}")
    print(f"Anomaly: {guardrails['anomaly_rate']:.1%}")
    print(f"Runtime: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print()

    # Guardrail status
    print("Guardrails:")
    c_status = "✅" if guardrails['c_min_pass'] else "❌"
    h_status = "✅" if guardrails['h_max_pass'] else "❌"
    a_status = "✅" if guardrails['a_max_pass'] else "❌"

    print(f"  {c_status} C_min (≥{FROZEN_C_MIN}): {guardrails['compliance_rate']:.2f}")
    print(f"  {h_status} H_max (≤{FROZEN_H_MAX}): {guardrails['halt_rate']:.2f}")
    print(f"  {a_status} A_max (≤{FROZEN_A_MAX}): {guardrails['anomaly_rate']:.2f}")
    print()

    if guardrails['all_passed']:
        print(f"✅ Baseline PASSED for seed {seed}")
        print()
        print("Next steps:")
        print(f"  1. Run Stage 3 ablations: python run_5seed_ablations.py --seed {seed}")
        return 0
    else:
        print(f"❌ Baseline FAILED for seed {seed}")
        print()
        print("STOP: Do not proceed to ablations for this seed.")
        print("Investigate the failure before continuing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
