#!/usr/bin/env python3
"""
RSA-PoC v4.2 — LLM Baseline Run (Single Seed, Validity Gates Only)

Runs the LLM deliberator (Claude Sonnet 4) with:
- Pre-flight validation using oracle deliberator (NO API COST)
- Task-aware selector for LLM runs
- Validity gates only (simplified repair, no full R1-R8)
- Single seed (default: 42)
- H=40 steps per episode
- E=20 episodes

ALWAYS RUNS PRE-FLIGHT VALIDATION FIRST!

Usage:
    python -m src.rsa_poc.v420.run_llm_baseline
    python -m src.rsa_poc.v420.run_llm_baseline --seed 123 --episodes 10
    python -m src.rsa_poc.v420.run_llm_baseline --preflight-only  # Validate only, no LLM
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .deliberator_oracle import OracleDeliberatorV420, DeliberationOutputV420
from .harness import MVRSA420Harness, HarnessConfigV420
from .env.tri_demand import TriDemandV420


# Frozen parameters
FROZEN_H = 40  # Steps per episode
FROZEN_E = 20  # Episodes
DEFAULT_SEED = 42


def run_preflight_validation(
    seed: int,
    max_episodes: int = 5,  # Short run for validation
    verbose: bool = True
) -> bool:
    """
    Run pre-flight validation with oracle deliberator.

    This validates:
    1. Harness works correctly
    2. Environment behaves as expected
    3. Repair and persistence work

    NO API COSTS - uses deterministic oracle.
    """
    if verbose:
        print("\n--- Pre-Flight Validation (Oracle) ---")

    env = TriDemandV420(seed=seed)
    deliberator = OracleDeliberatorV420()

    harness_config = HarnessConfigV420(
        max_steps_per_episode=FROZEN_H,
        max_episodes=max_episodes,
        seed=seed,
        selector_type="argmax",  # Oracle only justifies optimal, argmax works
        record_telemetry=False,
        verbose=False,
        validity_gates_only=True
    )

    harness = MVRSA420Harness(
        env=env,
        deliberator=deliberator,
        config=harness_config
    )

    # Run episodes
    successes = 0
    for ep in range(max_episodes):
        result = harness.run_episode(ep)
        if result["success"]:
            successes += 1

    success_rate = successes / max_episodes

    # Validate invariants
    valid = True
    issues = []

    if success_rate < 1.0:
        valid = False
        issues.append(f"Success rate {success_rate:.1%} < 100%")

    if harness.total_repairs_accepted != 1:
        valid = False
        issues.append(f"Repairs {harness.total_repairs_accepted} != 1 (persistence violation)")

    if verbose:
        print(f"  Success rate: {successes}/{max_episodes} = {success_rate:.1%}")
        print(f"  Repairs: {harness.total_repairs_accepted}")
        print(f"  Halts: {harness.total_halts}")
        if valid:
            print("  ✅ Pre-flight PASSED")
        else:
            print(f"  ❌ Pre-flight FAILED: {', '.join(issues)}")

    return valid


def run_with_llm(
    seed: int,
    max_episodes: int = FROZEN_E,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run LLM baseline for a single seed with task-aware selector.

    IMPORTANT: Uses task_aware selector because LLM justifies multiple actions.
    """
    # Import LLM deliberator only when needed
    from .deliberator import LLMDeliberatorV420, LLMDeliberatorConfigV420

    if verbose:
        print(f"\n--- LLM Run (Seed {seed}) ---")

    env = TriDemandV420(seed=seed)
    config = LLMDeliberatorConfigV420()
    deliberator = LLMDeliberatorV420(config)

    # Use task_aware selector for LLM (justifies multiple actions)
    harness_config = HarnessConfigV420(
        max_steps_per_episode=FROZEN_H,
        max_episodes=max_episodes,
        seed=seed,
        selector_type="task_aware",  # CRITICAL: LLM needs task-aware selector
        record_telemetry=True,
        verbose=verbose,
        validity_gates_only=True
    )

    harness = MVRSA420Harness(
        env=env,
        deliberator=deliberator,
        config=harness_config
    )

    # Run all episodes
    start = time.perf_counter()

    successes = 0
    episode_results = []

    for ep in range(max_episodes):
        ep_result = harness.run_episode(ep)
        episode_results.append(ep_result)
        if ep_result["success"]:
            successes += 1
        if verbose:
            print(f"  Ep{ep}: steps={ep_result['steps']}, success={ep_result['success']}")

    elapsed = time.perf_counter() - start

    result = {
        "seed": seed,
        "max_episodes": max_episodes,
        "elapsed_seconds": elapsed,
        "deliberator": "LLMDeliberatorV420",
        "model": config.model,
        "selector": "task_aware",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_steps": harness.total_steps,
            "total_halts": harness.total_halts,
            "total_contradictions": harness.total_contradictions,
            "total_repairs_accepted": harness.total_repairs_accepted,
            "total_successes": successes,
            "episodes_completed": max_episodes,
            "success_rate": successes / max_episodes
        },
        "gate_telemetry": {
            "repairs_submitted_total": harness.total_repairs_attempted,
            "repairs_accepted_total": harness.total_repairs_accepted,
            "repairs_rejected_total": harness.total_repairs_attempted - harness.total_repairs_accepted,
            "continuity_checks_total": harness.continuity_checks_total,
            "continuity_failures_total": harness.continuity_failures_total,
            "halts_by_reason": harness.halts_by_reason,
            "repair_bindings": harness.repair_bindings
        },
        "episode_results": episode_results
    }

    if verbose:
        print(f"\n  Results:")
        print(f"    Successes: {successes}/{max_episodes}")
        print(f"    Success rate: {successes/max_episodes:.1%}")
        print(f"    Repairs accepted: {harness.total_repairs_accepted}")
        print(f"    Time: {elapsed:.1f}s")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="RSA-PoC v4.2 LLM Baseline Run"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed (default: {DEFAULT_SEED})"
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=FROZEN_E,
        help=f"Number of episodes (default: {FROZEN_E})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: v420_llm_baseline_<seed>_<timestamp>.json)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run only pre-flight validation (no LLM, no cost)"
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip pre-flight validation (DANGEROUS: may waste money)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("RSA-PoC v4.2 — LLM Baseline Run")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Seed:              {args.seed}")
    print(f"  Episodes:          {args.episodes}")
    print(f"  Steps/episode:     {FROZEN_H}")
    print(f"  Model:             claude-sonnet-4-20250514")
    print(f"  Selector:          task_aware")
    print(f"  Validity gates:    ENABLED (simplified repair)")
    print()

    # Pre-flight validation (FREE, no API cost)
    if not args.skip_preflight:
        preflight_passed = run_preflight_validation(
            seed=args.seed,
            max_episodes=5,
            verbose=not args.quiet
        )

        if not preflight_passed:
            print("\n❌ Pre-flight validation FAILED - aborting to save costs")
            return 1

        if args.preflight_only:
            print("\n✅ Pre-flight validation passed (no LLM run requested)")
            return 0
    else:
        print("⚠️  Skipping pre-flight validation (--skip-preflight)")

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nERROR: ANTHROPIC_API_KEY not set in environment")
        print("       Set with: export ANTHROPIC_API_KEY=<your-key>")
        return 1

    # Run with LLM
    result = run_with_llm(
        seed=args.seed,
        max_episodes=args.episodes,
        verbose=not args.quiet
    )

    # Save result
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"v420_llm_baseline_{args.seed}_{timestamp}.json")

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print()
    print("=" * 70)
    print(f"Results saved to: {output_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
