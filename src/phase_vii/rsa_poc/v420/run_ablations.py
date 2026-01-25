#!/usr/bin/env python3
"""
RSA-PoC v4.2 — Ablation Runner (B only)

Runs Ablation B (Reflection Excision) calibration for v4.2.

NOTE: Ablation C (Persistence Excision) uses the standard run harness
with TaskOraclePersistenceExcisedV420. There is no separate calibration
fork for Ablation C. When the LLM/baseline run harness is implemented,
it will call oracle.on_episode_start(episode) at each episode boundary.

Usage:
    python run_ablations.py --ablation B
    python run_ablations.py --ablation B --seed 42 --episodes 100
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def run_ablation_b(seed: int, episodes: int) -> dict:
    """Run Ablation B (Reflection Excision)."""
    from ablations import run_ablation_b as _run_b
    return _run_b(seed=seed, episodes=episodes)


def print_ablation_b_report(result: dict) -> None:
    """Print Ablation B report."""
    print("=" * 70)
    print("RSA-PoC v4.2 — Ablation B: Reflection Excision")
    print("=" * 70)
    print()
    print(f"Description: {result['description']}")
    print(f"Flag: {result['ablation_flag']}")
    print()
    print("Parameters:")
    print(f"  H (steps/episode): {result['config']['max_steps']}")
    print(f"  E (episodes):      {result['config']['max_episodes']}")
    print(f"  Seed:              {result['config']['seed']}")
    print()
    print("Results:")
    s = result['summary']
    print(f"  Total steps:       {s['total_steps']}")
    print(f"  Total successes:   {s['total_successes']}")
    print(f"  Success rate:      {s['success_rate']:.2%}")
    print(f"  Total halts:       {s['total_halts']}")
    print(f"  Halt rate:         {s['halt_rate']:.2%}")
    print(f"  Elapsed:           {s['elapsed_ms']:.1f}ms")
    print()
    print("R7 Enforcement:")
    r7 = result['r7_enforcement']
    print(f"  Contradictions detected:  {r7['contradictions_detected']}")
    print(f"  Repairs attempted:        {r7['repairs_attempted']}")
    print(f"  Repairs rejected (R7):    {r7['repairs_rejected_r7']}")
    print(f"  Total R7 failures:        {r7['total_r7_failures']}")
    print()

    if s['ablation_effective']:
        print("✅ ABLATION B EFFECTIVE")
        print("   Reflection excision prevents valid LAW_REPAIR construction")
        print("   R7 correctly rejects repairs with invalid trace_entry_id")
    else:
        print("⚠️  ABLATION B NOT EFFECTIVE")
        print("   Unexpected: agent may have bypassed trace requirement")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Run RSA-PoC v4.2 Ablation B calibration"
    )
    parser.add_argument(
        "--ablation",
        choices=["B"],
        required=True,
        help="Ablation to run (B only; C uses standard harness)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=100,
        help="Number of episodes (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file (optional)"
    )

    args = parser.parse_args()

    results = {}

    if args.ablation == "B":
        print("\n" + "=" * 70)
        print("Running Ablation B: Reflection Excision...")
        print("=" * 70 + "\n")

        result_b = run_ablation_b(seed=args.seed, episodes=args.episodes)
        results["ablation_b"] = result_b
        print_ablation_b_report(result_b)

    # Save results if output specified
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {output_path}")

    # Also save to timestamped file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_output = Path(__file__).parent / f"v420_ablation_b_{timestamp}.json"
    with open(default_output, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {default_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
