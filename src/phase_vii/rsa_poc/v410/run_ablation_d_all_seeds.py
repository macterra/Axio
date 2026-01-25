#!/usr/bin/env python3
"""
RSA-PoC v4.1 — Run Ablation D for all seeds

Ablation D (Trace Excision) is deterministic and fast (~65ms per seed).
This script runs it for all 5 preregistered seeds to confirm seed-invariance.

Usage:
    python run_ablation_d_all_seeds.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v410.ablations import (
    AblationType,
    AblationHarness,
)
from src.rsa_poc.v410.harness import HarnessConfig
from src.rsa_poc.v410.deliberator import DeterministicDeliberator
from src.rsa_poc.v410.env import TriDemandV410
from src.rsa_poc.v410.experiment import FROZEN_H, FROZEN_E

FROZEN_SEEDS = [42, 123, 456, 789, 1024]


def run_ablation_d_all_seeds():
    """Run Ablation D for all preregistered seeds."""
    results_dir = Path(__file__).parent.parent.parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("Ablation D: Trace Excision — All Seeds")
    print("=" * 60)
    print(f"Protocol: H={FROZEN_H}, E={FROZEN_E}")
    print(f"Seeds: {FROZEN_SEEDS}")
    print()

    all_results = {}

    for seed in FROZEN_SEEDS:
        print(f"\n--- Seed {seed} ---")
        start_time = datetime.now()

        # Create environment
        env = TriDemandV410(seed=seed)

        # Use DeterministicDeliberator (trace excision bypasses it anyway)
        deliberator = DeterministicDeliberator()

        # Create harness config
        harness_config = HarnessConfig(
            max_steps_per_episode=FROZEN_H,
            max_episodes=FROZEN_E,
            seed=seed,
        )

        # Create and run ablation harness
        harness = AblationHarness(
            ablation_type=AblationType.TRACE_EXCISION,
            config=harness_config,
            deliberator=deliberator,
            env=env,
        )

        result = harness.run()
        elapsed = (datetime.now() - start_time).total_seconds()

        # Extract metrics from summary
        summary = result.get('summary', {})
        total_steps = summary.get('total_steps', 0)
        total_halts = summary.get('total_halts', 0)
        halt_rate = total_halts / (total_steps + total_halts) if (total_steps + total_halts) > 0 else 0

        print(f"  Steps: {total_steps}")
        print(f"  Halts: {total_halts}")
        print(f"  Halt Rate: {halt_rate:.1%}")
        print(f"  Runtime: {elapsed:.1f}ms")

        all_results[seed] = {
            'seed': seed,
            'total_steps': total_steps,
            'total_halts': total_halts,
            'halt_rate': halt_rate,
            'runtime_seconds': elapsed,
            'expected_100_percent_halt': halt_rate == 1.0,
        }

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n| Seed | Steps | Halts | Halt Rate | Status |")
    print(f"|------|-------|-------|-----------|--------|")

    all_pass = True
    for seed in FROZEN_SEEDS:
        r = all_results[seed]
        status = "✅ 100% HALT" if r['halt_rate'] == 1.0 else "❌ UNEXPECTED"
        if r['halt_rate'] != 1.0:
            all_pass = False
        print(f"| {seed:4d} | {r['total_steps']:5d} | {r['total_halts']:5d} | {r['halt_rate']:8.1%} | {status} |")

    print()
    if all_pass:
        print("✅ SEED-INVARIANCE CONFIRMED: All 5 seeds show 100% halt rate")
    else:
        print("❌ UNEXPECTED: Some seeds did not show 100% halt rate")

    # Save consolidated result
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v410_ablationD_all_seeds_{timestamp}.json"
    filepath = results_dir / filename

    consolidated = {
        'ablation': 'D',
        'ablation_type': 'TRACE_EXCISION',
        'protocol': {'H': FROZEN_H, 'E': FROZEN_E},
        'seeds': FROZEN_SEEDS,
        'per_seed_results': all_results,
        'seed_invariance_confirmed': all_pass,
        'timestamp': timestamp,
    }

    with open(filepath, 'w') as f:
        json.dump(consolidated, f, indent=2)

    print(f"\nResults saved to: {filepath}")

    return all_pass, all_results


if __name__ == "__main__":
    run_ablation_d_all_seeds()
