#!/usr/bin/env python3
"""
RSA-PoC v4.2 — Ablation D: Trace Excision / Golden Test (LLM Run)

Runs Ablation D with LLM deliberator where:
- Justification trace is completely excised
- Deliberator output is ignored/cleared
- No actions can be justified
- Every step results in HALT

This is the "Golden Test" - the most extreme ablation that must cause
complete collapse. If the system can still act without justifications,
it is not an RSA.

Expected outcome:
- All episodes: HALT on first step
- success_rate = 0%
- total_halts = number of episodes
- No actions executed

Usage:
    python -m src.rsa_poc.v420.run_ablation_d
    python -m src.rsa_poc.v420.run_ablation_d --seed 42 --episodes 5
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .deliberator_oracle import OracleDeliberatorV420, DeliberationOutputV420
from .harness import (
    MVRSA420Harness,
    HarnessConfigV420,
    HaltReason,
    DeliberatorProtocol,
)
from .core.norm_state import NormStateV420
from .env.tri_demand import TriDemandV420, Observation420


# Frozen parameters
FROZEN_H = 40
FROZEN_E = 20
DEFAULT_SEED = 42


class TraceExcisedDeliberatorV420(DeliberatorProtocol):
    """
    Deliberator with trace excision (Ablation D).

    Returns empty justifications for all inputs.
    This causes the harness to HALT because no actions can be justified.
    """

    def deliberate(
        self,
        obs: Observation420,
        norm_state: NormStateV420,
        episode: int,
        step: int
    ) -> DeliberationOutputV420:
        """
        Return empty deliberation output.

        ABLATION D: Trace is excised - no justifications produced.
        """
        # Return with empty justifications
        # success property will return False since len(justifications) == 0
        return DeliberationOutputV420(
            justifications=[],  # EXCISED - no justifications
            deliberation_time_ms=0.0,
            error=None  # No error - deliberator ran, just produced nothing
        )


class MVRSA420HarnessAblationD(MVRSA420Harness):
    """
    Harness variant for Ablation D: Trace Excision.

    Uses TraceExcisedDeliberatorV420 which returns empty justifications.
    Every step should HALT due to no feasible justified actions.
    """
    pass  # No changes needed - the deliberator returns empty, harness HALTs


def run_preflight_validation(
    seed: int,
    max_episodes: int = 5,
    verbose: bool = True
) -> bool:
    """
    Pre-flight validation for Ablation D.

    Expected: Every episode HALTs on first step.
    """
    if verbose:
        print("\n--- Pre-Flight Validation (Ablation D: Trace Excision) ---")

    env = TriDemandV420(seed=seed)
    deliberator = TraceExcisedDeliberatorV420()  # Empty deliberator

    harness_config = HarnessConfigV420(
        max_steps_per_episode=FROZEN_H,
        max_episodes=max_episodes,
        seed=seed,
        selector_type="argmax",
        record_telemetry=False,
        verbose=False,
        validity_gates_only=True
    )

    harness = MVRSA420HarnessAblationD(
        env=env,
        deliberator=deliberator,
        config=harness_config
    )

    successes = 0
    for ep in range(max_episodes):
        result = harness.run_episode(ep)
        if result["success"]:
            successes += 1

    success_rate = successes / max_episodes

    valid = True
    issues = []

    # Every episode should fail (HALT on first step)
    if successes != 0:
        valid = False
        issues.append(f"Expected 0 successes, got {successes}")

    # Should have halts equal to episodes
    if harness.total_halts != max_episodes:
        valid = False
        issues.append(f"Expected {max_episodes} halts, got {harness.total_halts}")

    # Should have 0 or minimal steps (just the HALTs)
    if harness.total_steps > max_episodes:
        valid = False
        issues.append(f"Expected <= {max_episodes} steps, got {harness.total_steps}")

    if verbose:
        print(f"  Success rate: {successes}/{max_episodes} = {success_rate:.1%}")
        print(f"  Total steps: {harness.total_steps}")
        print(f"  Total halts: {harness.total_halts}")
        print(f"  Halts by reason: {harness.halts_by_reason}")
        if valid:
            print("  ✅ Pre-flight PASSED (Ablation D collapse confirmed)")
        else:
            print(f"  ❌ Pre-flight FAILED: {', '.join(issues)}")

    return valid


def run_with_llm(
    seed: int,
    max_episodes: int = FROZEN_E,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run Ablation D with trace-excised deliberator.

    Note: Uses TraceExcisedDeliberatorV420, not LLM.
    The "LLM" is effectively replaced with a null output.
    """
    if verbose:
        print(f"\n--- Ablation D Run (Seed {seed}, Trace Excision) ---")

    env = TriDemandV420(seed=seed)
    deliberator = TraceExcisedDeliberatorV420()

    harness_config = HarnessConfigV420(
        max_steps_per_episode=FROZEN_H,
        max_episodes=max_episodes,
        seed=seed,
        selector_type="task_aware",
        record_telemetry=True,
        verbose=verbose,
        validity_gates_only=True
    )

    harness = MVRSA420HarnessAblationD(
        env=env,
        deliberator=deliberator,
        config=harness_config
    )

    start = time.perf_counter()

    successes = 0
    episode_results = []

    for ep in range(max_episodes):
        ep_result = harness.run_episode(ep)
        episode_results.append(ep_result)
        if ep_result["success"]:
            successes += 1
        if verbose:
            halted = ep_result.get("halts", 0) > 0
            print(f"  Ep{ep}: steps={ep_result['steps']}, success={ep_result['success']}, halted={halted}")

    elapsed = time.perf_counter() - start

    # Count NO_FEASIBLE_ACTIONS halts
    no_feasible_halts = harness.halts_by_reason.get("NO_FEASIBLE_ACTIONS", 0)

    result = {
        "seed": seed,
        "max_episodes": max_episodes,
        "elapsed_seconds": elapsed,
        "ablation": "D",
        "ablation_name": "Trace Excision (Golden Test)",
        "deliberator": "TraceExcisedDeliberatorV420",
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
        "ablation_analysis": {
            "collapse_confirmed": (
                successes == 0 and
                harness.total_halts == max_episodes
            ),
            "no_feasible_halts": no_feasible_halts,
            "halted_episodes": sum(1 for e in episode_results if e.get("halts", 0) > 0),
            "actions_executed": harness.total_steps - harness.total_halts  # Should be 0
        },
        "episode_results": episode_results
    }

    if verbose:
        print(f"\n  Results:")
        print(f"    Successes: {successes}/{max_episodes}")
        print(f"    Success rate: {successes/max_episodes:.1%}")
        print(f"    Total halts: {harness.total_halts}")
        print(f"    Halts (NO_FEASIBLE_ACTIONS): {no_feasible_halts}")
        print(f"    Time: {elapsed:.1f}s")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="RSA-PoC v4.2 Ablation D: Trace Excision / Golden Test"
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
        help="Output file path"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run only pre-flight validation"
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip pre-flight validation"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("RSA-PoC v4.2 — Ablation D: Trace Excision (Golden Test)")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Seed:              {args.seed}")
    print(f"  Episodes:          {args.episodes}")
    print(f"  Steps/episode:     {FROZEN_H}")
    print(f"  Deliberator:       TraceExcisedDeliberatorV420 (empty)")
    print(f"  Selector:          task_aware")
    print(f"  Validity gates:    ENABLED")
    print(f"  Ablation:          D (Trace Excision)")
    print()

    if not args.skip_preflight:
        preflight_passed = run_preflight_validation(
            seed=args.seed,
            max_episodes=5,
            verbose=not args.quiet
        )

        if not preflight_passed:
            print("\n❌ Pre-flight validation FAILED - aborting")
            return 1

        if args.preflight_only:
            print("\n✅ Pre-flight validation passed (no full run requested)")
            return 0
    else:
        print("⚠️  Skipping pre-flight validation")

    # No API key needed - uses local trace-excised deliberator
    result = run_with_llm(
        seed=args.seed,
        max_episodes=args.episodes,
        verbose=not args.quiet
    )

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"v420_ablation_d_{args.seed}_{timestamp}.json")

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print()
    print("=" * 70)
    print(f"Results saved to: {output_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
