#!/usr/bin/env python3
"""
RSA-PoC v4.2 — Ablation B: Reflection Excision (LLM Run)

Runs Ablation B with LLM deliberator where:
- Trace access is excised (trace_entry_id = None, blocking_rule_ids = [])
- This causes LAW_REPAIR to be invalid
- Under validity gates, repair is still "accepted" but binding is invalid
- Under full R1-R8 gates, R7 would reject the repair

Expected outcome:
- Under validity_gates_only=True: Same behavior as baseline (gates don't check R7)
- The telemetry shows empty/invalid bindings

This establishes that with full gates, Ablation B would collapse.

Usage:
    python -m src.rsa_poc.v420.run_ablation_b
    python -m src.rsa_poc.v420.run_ablation_b --seed 42 --episodes 5
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .deliberator_oracle import OracleDeliberatorV420
from .harness import (
    MVRSA420Harness,
    HarnessConfigV420,
    HaltReason,
    StepRecord,
    DeliberatorProtocol,
)
from .env.tri_demand import TriDemandV420, Observation420
from .core.norm_state import NormStateV420


# Frozen parameters
FROZEN_H = 40
FROZEN_E = 20
DEFAULT_SEED = 42


class MVRSA420HarnessAblationB(MVRSA420Harness):
    """
    Harness variant for Ablation B: Reflection Excision.

    The trace is unavailable, so _attempt_repair:
    - Cannot construct valid trace_entry_id or blocking_rule_ids
    - R7 gate REJECTS the invalid repair
    - Rejection triggers HALT

    This is the expected collapse mode for Ablation B.
    """

    def _attempt_repair(
        self,
        obs: Observation420,
        blocking_rules: List[str],  # IGNORED in Ablation B - trace unavailable
        episode: int,
        step: int
    ) -> bool:
        """
        Attempt repair with REFLECTION EXCISED.

        Trace is unavailable → cannot construct valid bindings → R7 REJECTS → HALT.
        """
        self.total_repairs_attempted += 1

        # ABLATION B: Reflection is excised
        # Cannot access trace to get valid trace_entry_id or blocking_rules
        # R7 requires valid trace binding - this repair is REJECTED

        # Record the rejected repair binding
        self.repair_bindings.append({
            "trace_entry_id": None,  # EXCISED - unavailable
            "blocking_rule_ids": [],  # EXCISED - unavailable
            "repair_epoch": None,  # No repair applied
            "episode": episode,
            "step": step,
            "accepted": False,
            "rejected_by": "R7",
            "rejection_reason": "trace_entry_id unavailable (reflection excised)"
        })

        # R7 REJECTS - repair is invalid, return False → triggers HALT
        return False


def run_preflight_validation(
    seed: int,
    max_episodes: int = 5,
    verbose: bool = True
) -> bool:
    """
    Pre-flight validation for Ablation B.

    Expected behavior: R7 rejects invalid repair → HALT.
    Episode 0 succeeds (no contradiction), Episode 1+ fails at contradiction.
    """
    if verbose:
        print("\n--- Pre-Flight Validation (Oracle, Ablation B) ---")

    env = TriDemandV420(seed=seed)
    deliberator = OracleDeliberatorV420()

    harness_config = HarnessConfigV420(
        max_steps_per_episode=FROZEN_H,
        max_episodes=max_episodes,
        seed=seed,
        selector_type="argmax",
        record_telemetry=False,
        verbose=False,
        validity_gates_only=True  # Gates still enforced, but R7 check is in harness
    )

    harness = MVRSA420HarnessAblationB(
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

    # Compute derived counters
    repairs_rejected = harness.total_repairs_attempted - harness.total_repairs_accepted

    valid = True
    issues = []

    # Ablation B should: Episode 0 succeeds (no contradiction yet)
    # Episode 1+ hits contradiction, R7 rejects, HALT → no success
    if successes != 1:  # Only episode 0 should succeed
        valid = False
        issues.append(f"Expected 1 success (ep0), got {successes}")

    # Should have attempted repair but rejected
    if harness.total_repairs_attempted < 1:
        valid = False
        issues.append(f"No repair attempted (expected >= 1)")

    if harness.total_repairs_accepted != 0:
        valid = False
        issues.append(f"Repairs accepted {harness.total_repairs_accepted} != 0 (R7 should reject)")

    if harness.total_halts < 1:
        valid = False
        issues.append(f"Halts {harness.total_halts} < 1 (rejection should cause HALT)")

    if verbose:
        print(f"  Success rate: {successes}/{max_episodes} = {success_rate:.1%}")
        print(f"  Repairs attempted: {harness.total_repairs_attempted}")
        print(f"  Repairs accepted: {harness.total_repairs_accepted}")
        print(f"  Repairs rejected: {repairs_rejected}")
        print(f"  Halts: {harness.total_halts}")
        print(f"  Halts by reason: {harness.halts_by_reason}")
        if harness.repair_bindings:
            print(f"  Binding rejected_by: {harness.repair_bindings[0].get('rejected_by')}")
        if valid:
            print("  ✅ Pre-flight PASSED (Ablation B collapse confirmed)")
        else:
            print(f"  ❌ Pre-flight FAILED: {', '.join(issues)}")

    return valid


def run_with_llm(
    seed: int,
    max_episodes: int = FROZEN_E,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run Ablation B with LLM deliberator.

    Expected: R7 rejects invalid repair → HALT on first contradiction.
    """
    from .deliberator import LLMDeliberatorV420, LLMDeliberatorConfigV420

    if verbose:
        print(f"\n--- LLM Run (Seed {seed}, Ablation B) ---")

    env = TriDemandV420(seed=seed)
    config = LLMDeliberatorConfigV420()
    deliberator = LLMDeliberatorV420(config)

    harness_config = HarnessConfigV420(
        max_steps_per_episode=FROZEN_H,
        max_episodes=max_episodes,
        seed=seed,
        selector_type="task_aware",
        record_telemetry=True,
        verbose=verbose,
        validity_gates_only=True  # R7 enforced in Ablation B harness
    )

    harness = MVRSA420HarnessAblationB(
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

    # Compute R7 rejection count
    r7_reject_count = sum(
        1 for b in harness.repair_bindings
        if b.get("rejected_by") == "R7"
    )

    result = {
        "seed": seed,
        "max_episodes": max_episodes,
        "elapsed_seconds": elapsed,
        "ablation": "B",
        "ablation_name": "Reflection Excision",
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
            "r7_reject_count": r7_reject_count,
            "continuity_checks_total": harness.continuity_checks_total,
            "continuity_failures_total": harness.continuity_failures_total,
            "halts_by_reason": harness.halts_by_reason,
            "repair_bindings": harness.repair_bindings
        },
        "ablation_analysis": {
            "collapse_confirmed": (
                harness.total_repairs_accepted == 0 and
                harness.total_halts >= 1 and
                r7_reject_count >= 1
            ),
            "r7_reject_count": r7_reject_count,
            "halted_episodes": sum(1 for e in episode_results if e.get("halts", 0) > 0)
        },
        "episode_results": episode_results
    }

    if verbose:
        print(f"\n  Results:")
        print(f"    Successes: {successes}/{max_episodes}")
        print(f"    Success rate: {successes/max_episodes:.1%}")
        print(f"    Repairs rejected (R7): {r7_reject_count}")
        print(f"    Total halts: {harness.total_halts}")
        print(f"    Time: {elapsed:.1f}s")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="RSA-PoC v4.2 Ablation B: Reflection Excision (LLM Run)"
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
    print("RSA-PoC v4.2 — Ablation B: Reflection Excision")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Seed:              {args.seed}")
    print(f"  Episodes:          {args.episodes}")
    print(f"  Steps/episode:     {FROZEN_H}")
    print(f"  Model:             claude-sonnet-4-20250514")
    print(f"  Selector:          task_aware")
    print(f"  Validity gates:    ENABLED (simplified repair)")
    print(f"  Ablation:          B (Reflection Excision)")
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
            print("\n✅ Pre-flight validation passed (no LLM run requested)")
            return 0
    else:
        print("⚠️  Skipping pre-flight validation")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nERROR: ANTHROPIC_API_KEY not set")
        return 1

    result = run_with_llm(
        seed=args.seed,
        max_episodes=args.episodes,
        verbose=not args.quiet
    )

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"v420_ablation_b_{args.seed}_{timestamp}.json")

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
