#!/usr/bin/env python3
"""
RSA-PoC v4.1 — Stage 3: LLM Ablations Runner

Runs ablations A, B, C at frozen protocol (H=40, E=20) for a single seed.
Only run after Stage 1 baseline passes for that seed.

Usage:
    python run_5seed_ablations.py --seed 123
    python run_5seed_ablations.py --seed 456 --ablation A
    python run_5seed_ablations.py --seed 789 --ablation B C
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v410.ablations import (
    AblationType,
    AblationHarness,
)
from src.rsa_poc.v410.harness import HarnessConfig
from src.rsa_poc.v410.deliberator import LLMDeliberator, LLMDeliberatorConfig
from src.rsa_poc.v410.env import TriDemandV410
from src.rsa_poc.v410.experiment import FROZEN_H, FROZEN_E

FROZEN_SEEDS = [42, 123, 456, 789, 1024]

ABLATION_TYPES = {
    'A': (AblationType.SEMANTIC_EXCISION, 'Semantic Excision'),
    'B': (AblationType.REFLECTION_EXCISION, 'Reflection Excision'),
    'C': (AblationType.PERSISTENCE_EXCISION, 'Persistence Excision'),
}


def save_result(result: Dict[str, Any], ablation: str, seed: int) -> Path:
    """Save result to JSON file."""
    results_dir = Path(__file__).parent.parent.parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"v410_ablation{ablation}_seed{seed}_{timestamp}.json"
    filepath = results_dir / filename

    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    return filepath


def run_ablation(
    ablation: str,
    seed: int,
    dry_run: bool = False
) -> Optional[Dict[str, Any]]:
    """Run a single ablation for a seed."""
    if ablation not in ABLATION_TYPES:
        print(f"❌ Unknown ablation: {ablation}")
        return None

    ablation_type, name = ABLATION_TYPES[ablation]

    print(f"\n{'='*60}")
    print(f"Ablation {ablation}: {name} (seed={seed})")
    print(f"{'='*60}")
    print(f"Protocol: H={FROZEN_H}, E={FROZEN_E}")
    print()

    if dry_run:
        print("[DRY RUN] Would execute:")
        print(f"  - {name}: {FROZEN_E} episodes × {FROZEN_H} steps")
        print(f"  - Expected runtime: ~45 minutes")
        return None

    start_time = datetime.now()

    try:
        # Create environment
        env = TriDemandV410(seed=seed)

        # Create LLM deliberator
        llm_config = LLMDeliberatorConfig(model="claude-sonnet-4-20250514")
        deliberator = LLMDeliberator(llm_config)

        # Create harness config
        config = HarnessConfig(
            max_steps_per_episode=FROZEN_H,
            max_episodes=FROZEN_E,
            seed=seed
        )

        # Run ablation
        harness = AblationHarness(
            env=env,
            ablation_type=ablation_type,
            config=config,
            deliberator=deliberator,
            seed=seed
        )
        result = harness.run()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'ablation': ablation, 'seed': seed}

    elapsed = (datetime.now() - start_time).total_seconds()

    # Add metadata
    result['metadata'] = {
        'seed': seed,
        'ablation': ablation,
        'ablation_name': name,
        'stage': '3_ABLATIONS',
        'protocol': {
            'H': FROZEN_H,
            'E': FROZEN_E
        },
        'elapsed_seconds': elapsed,
        'timestamp': datetime.now().isoformat()
    }

    # Save
    filepath = save_result(result, ablation, seed)
    print(f"Results saved to: {filepath}")

    # Print summary
    summary = result.get('summary', {})
    halts = summary.get('total_halts', 0)
    steps = summary.get('total_steps', 0)
    halt_rate = halts / steps if steps > 0 else 0
    print()
    print(f"Steps: {steps}")
    print(f"Halts: {halts} ({halt_rate:.1%})")
    print(f"Runtime: {elapsed:.1f}s ({elapsed/60:.1f} min)")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run LLM ablations for a single seed"
    )
    parser.add_argument(
        '--seed',
        type=int,
        required=True,
        choices=FROZEN_SEEDS,
        help=f"Seed to run (one of {FROZEN_SEEDS})"
    )
    parser.add_argument(
        '--ablation',
        type=str,
        nargs='+',
        default=['A', 'B', 'C'],
        choices=['A', 'B', 'C'],
        help="Ablation(s) to run (default: A B C)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be run without executing"
    )

    args = parser.parse_args()
    seed = args.seed
    ablations = args.ablation

    print("=" * 60)
    print(f"RSA-PoC v4.1 — Stage 3: LLM Ablations (seed={seed})")
    print("=" * 60)
    print()
    print(f"Protocol: H={FROZEN_H}, E={FROZEN_E}")
    print(f"Ablations to run: {', '.join(ablations)}")
    print()

    if args.dry_run:
        total_time = len(ablations) * 45
        print(f"[DRY RUN] Total expected runtime: ~{total_time} minutes")
        for abl in ablations:
            run_ablation(abl, seed, dry_run=True)
        return 0

    # Check if baseline exists for this seed
    results_dir = Path(__file__).parent.parent.parent.parent / "results"
    baseline_files = list(results_dir.glob(f"v410_baseline_seed{seed}_*.json"))
    pilot_files = list(results_dir.glob(f"v410_pilot_*.json")) if seed == 42 else []

    if not baseline_files and not pilot_files:
        print(f"⚠️  Warning: No baseline result found for seed {seed}")
        print(f"   Run Stage 1 first: python run_5seed_baseline.py --seed {seed}")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            return 1

    # Run ablations
    results = {}
    for abl in ablations:
        result = run_ablation(abl, seed, dry_run=False)
        if result:
            results[abl] = result

    # Summary
    print()
    print("=" * 60)
    print("ABLATION SUMMARY")
    print("=" * 60)
    print()
    print(f"| Ablation | Halts | Halt Rate | Avg Reward | Status |")
    print(f"|----------|-------|-----------|------------|--------|")

    for abl in ablations:
        if abl in results:
            r = results[abl]
            if 'error' in r:
                print(f"| {abl:8} | ERROR | —         | —          | ❌ FAIL |")
            else:
                summary = r.get('summary', {})
                halts = summary.get('total_halts', 0)
                halt_rate = summary.get('halt_rate', 0)
                avg_reward = summary.get('avg_reward', 0)
                print(f"| {abl:8} | {halts:5} | {halt_rate:9.1%} | {avg_reward:10.2f} | ✅ Done |")

    print()
    print(f"Results saved to: {results_dir}/v410_ablation*_seed{seed}_*.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
