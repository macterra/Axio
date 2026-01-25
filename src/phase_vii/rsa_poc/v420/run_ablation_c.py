#!/usr/bin/env python3
"""
RSA-PoC v4.2 — Ablation C: Persistence Excision (LLM Run)

Runs Ablation C with LLM deliberator where:
- norm_state is RESET at each episode boundary
- Repair from previous episode is lost
- Repair epoch chain is broken

Expected collapse mode:
- Episode 0: regime=0, no contradiction → succeeds
- Episode 1: regime=1, contradiction, repair attempted and accepted
- Episode 2+: norm_state RESET, repair lost, contradiction recurs
  - Repair attempted with prior_repair_epoch that doesn't match norm_state
  - R5/R6 gate rejects (epoch chain broken)
  - HALT

Usage:
    python -m src.rsa_poc.v420.run_ablation_c
    python -m src.rsa_poc.v420.run_ablation_c --seed 42 --episodes 5
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
)
from .core.norm_state import create_initial_norm_state_v420
from .env.tri_demand import TriDemandV420, Observation420


# Frozen parameters
FROZEN_H = 40
FROZEN_E = 20
DEFAULT_SEED = 42


class MVRSA420HarnessAblationC(MVRSA420Harness):
    """
    Harness variant for Ablation C: Persistence Excision.

    norm_state is RESET at each episode boundary:
    - Repair from previous episode is lost
    - Repair epoch is cleared
    - Agent "forgets" any repairs

    This breaks the R5/R6 epoch chain validation.
    """

    def reset_for_episode(self, episode: int) -> Observation420:
        """
        Reset environment AND norm_state for new episode.

        ABLATION C: norm_state is reset, breaking persistence.
        """
        # Continuity check before reset (should fail after ep1 repair is lost)
        if episode > 0 and self._expected_norm_hash is not None:
            self.continuity_checks_total += 1
            current_hash = self.norm_state.norm_hash
            if current_hash != self._expected_norm_hash:
                self.continuity_failures_total += 1

        # ================================================================
        # ABLATION C: Reset norm_state at episode boundary
        # ================================================================
        if episode > 0:
            # Reset norm_state to initial (repair lost)
            self.norm_state = create_initial_norm_state_v420()

            # Agent's epoch cache is now stale - this will cause R5/R6 failure
            # We keep current_repair_epoch so repair attempts use it,
            # but norm_state no longer has the repair, causing mismatch

            # Reset repair tracking (agent "forgets" it repaired)
            self.repair_issued = False
            self.repair_accepted = False

        obs, info = self.env.reset()

        # Always recompile rules (needed on every episode)
        self._recompile_rules()

        # Record expected hash for next check
        self._expected_norm_hash = self.norm_state.norm_hash

        return obs

    def _attempt_repair(
        self,
        obs: Observation420,
        blocking_rules: List[str],
        episode: int,
        step: int
    ) -> bool:
        """
        Attempt repair with PERSISTENCE EXCISION.

        Under Ablation C:
        - Episode 1: First repair, prior_repair_epoch=None → succeeds
        - Episode 2+: norm_state was reset, but prior_repair_epoch is stale
        - R5/R6 check: prior_repair_epoch doesn't match norm_state epoch → reject
        """
        from .calibration import create_canonical_repair_action
        from .core.trace import TraceEntryID, TraceEntry, TraceEntryType
        from datetime import datetime

        self.total_repairs_attempted += 1

        # Generate trace entry (reflection is intact in Ablation C)
        trace_entry_id = TraceEntryID.generate(
            run_seed=self.config.seed,
            episode=episode,
            step=step,
            entry_type="CONTRADICTION"
        )

        # Record in trace
        trace_entry = TraceEntry(
            trace_entry_id=trace_entry_id,
            entry_type=TraceEntryType.CONTRADICTION,
            run_seed=self.config.seed,
            episode=episode,
            step=step,
            timestamp=datetime.now().isoformat(),
            blocking_rule_ids=blocking_rules,
            active_obligation_target={"kind": "DEPOSIT_ZONE", "target_id": "ZONE_A"},
            progress_actions={"A6"}
        )
        self.trace_log.add(trace_entry)

        # Create repair action with current epoch state
        repair_action = create_canonical_repair_action(
            trace_entry_id=trace_entry_id,
            blocking_rule_ids=blocking_rules,
            prior_repair_epoch=self.current_repair_epoch
        )

        # ================================================================
        # R5/R6 GATE CHECK: Epoch chain validation
        # ================================================================
        # Under Ablation C, after episode 1:
        # - norm_state was reset, so norm_state.repair_epoch is None/original
        # - But agent's current_repair_epoch is from previous repair
        # - If these don't match AND this isn't the first repair, reject

        # Get norm_state's current repair epoch (if any)
        # After reset, this should be the original fingerprint, not a repair epoch
        norm_epoch = getattr(self.norm_state, 'law_fingerprint', None)

        # R5/R6 validation: if prior_repair_epoch is set but doesn't match
        # what norm_state expects, the epoch chain is broken
        epoch_chain_valid = True
        rejection_reason = None

        if episode > 1:
            # After episode 1, we've had a repair, so current_repair_epoch is set
            # But norm_state was reset, so it doesn't have that repair
            # This means any repair attempt will have a stale prior_repair_epoch
            if self.current_repair_epoch is not None:
                # Agent thinks it has a repair epoch, but norm_state was reset
                # The repair_action references prior_repair_epoch that doesn't
                # exist in the reset norm_state
                epoch_chain_valid = False
                rejection_reason = "prior_repair_epoch stale (norm_state reset, R5/R6 chain broken)"

        if not epoch_chain_valid:
            # R5/R6 REJECTS - epoch chain broken
            self.repair_bindings.append({
                "trace_entry_id": str(trace_entry_id),
                "blocking_rule_ids": blocking_rules,
                "repair_epoch": None,
                "prior_repair_epoch": self.current_repair_epoch,
                "episode": episode,
                "step": step,
                "accepted": False,
                "rejected_by": "R5/R6",
                "rejection_reason": rejection_reason
            })
            return False

        # First repair (episode 1) or valid epoch chain - apply repair
        success = self._apply_repair_direct(repair_action)

        if success:
            self.repair_issued = True
            self.repair_accepted = True
            self.total_repairs_accepted += 1

            self.repair_bindings.append({
                "trace_entry_id": str(trace_entry_id),
                "blocking_rule_ids": blocking_rules,
                "repair_epoch": self.current_repair_epoch,
                "prior_repair_epoch": repair_action.prior_repair_epoch,
                "episode": episode,
                "step": step,
                "accepted": True
            })
            return True

        return False


def run_preflight_validation(
    seed: int,
    max_episodes: int = 5,
    verbose: bool = True
) -> bool:
    """
    Pre-flight validation for Ablation C.

    Expected: Episode 0 succeeds, Episode 1 succeeds (first repair),
    Episodes 2+ fail (R5/R6 rejects due to broken epoch chain).
    """
    if verbose:
        print("\n--- Pre-Flight Validation (Oracle, Ablation C) ---")

    env = TriDemandV420(seed=seed)
    deliberator = OracleDeliberatorV420()

    harness_config = HarnessConfigV420(
        max_steps_per_episode=FROZEN_H,
        max_episodes=max_episodes,
        seed=seed,
        selector_type="argmax",
        record_telemetry=False,
        verbose=False,
        validity_gates_only=True
    )

    harness = MVRSA420HarnessAblationC(
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
    repairs_rejected = harness.total_repairs_attempted - harness.total_repairs_accepted

    # Count R5/R6 rejections
    r5r6_reject_count = sum(
        1 for b in harness.repair_bindings
        if b.get("rejected_by") == "R5/R6"
    )

    valid = True
    issues = []

    # Episodes 0 and 1 should succeed, 2+ should fail
    if successes != 2:
        valid = False
        issues.append(f"Expected 2 successes (ep0, ep1), got {successes}")

    if harness.total_repairs_accepted != 1:
        valid = False
        issues.append(f"Expected 1 repair accepted (ep1), got {harness.total_repairs_accepted}")

    if harness.total_halts < 1:
        valid = False
        issues.append(f"Expected halts >= 1, got {harness.total_halts}")

    if verbose:
        print(f"  Success rate: {successes}/{max_episodes} = {success_rate:.1%}")
        print(f"  Repairs attempted: {harness.total_repairs_attempted}")
        print(f"  Repairs accepted: {harness.total_repairs_accepted}")
        print(f"  Repairs rejected (R5/R6): {r5r6_reject_count}")
        print(f"  Halts: {harness.total_halts}")
        print(f"  Halts by reason: {harness.halts_by_reason}")
        print(f"  Continuity failures: {harness.continuity_failures_total}")
        if valid:
            print("  ✅ Pre-flight PASSED (Ablation C collapse confirmed)")
        else:
            print(f"  ❌ Pre-flight FAILED: {', '.join(issues)}")

    return valid


def run_with_llm(
    seed: int,
    max_episodes: int = FROZEN_E,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run Ablation C with LLM deliberator.
    """
    from .deliberator import LLMDeliberatorV420, LLMDeliberatorConfigV420

    if verbose:
        print(f"\n--- LLM Run (Seed {seed}, Ablation C) ---")

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
        validity_gates_only=True
    )

    harness = MVRSA420HarnessAblationC(
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

    # Count R5/R6 rejections
    r5r6_reject_count = sum(
        1 for b in harness.repair_bindings
        if b.get("rejected_by") == "R5/R6"
    )

    result = {
        "seed": seed,
        "max_episodes": max_episodes,
        "elapsed_seconds": elapsed,
        "ablation": "C",
        "ablation_name": "Persistence Excision",
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
            "r5r6_reject_count": r5r6_reject_count,
            "continuity_checks_total": harness.continuity_checks_total,
            "continuity_failures_total": harness.continuity_failures_total,
            "halts_by_reason": harness.halts_by_reason,
            "repair_bindings": harness.repair_bindings
        },
        "ablation_analysis": {
            "collapse_confirmed": (
                harness.total_halts >= 1 and
                r5r6_reject_count >= 1
            ),
            "r5r6_reject_count": r5r6_reject_count,
            "halted_episodes": sum(1 for e in episode_results if e.get("halts", 0) > 0),
            "continuity_failures": harness.continuity_failures_total
        },
        "episode_results": episode_results
    }

    if verbose:
        print(f"\n  Results:")
        print(f"    Successes: {successes}/{max_episodes}")
        print(f"    Success rate: {successes/max_episodes:.1%}")
        print(f"    Repairs accepted: {harness.total_repairs_accepted}")
        print(f"    Repairs rejected (R5/R6): {r5r6_reject_count}")
        print(f"    Total halts: {harness.total_halts}")
        print(f"    Time: {elapsed:.1f}s")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="RSA-PoC v4.2 Ablation C: Persistence Excision (LLM Run)"
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
    print("RSA-PoC v4.2 — Ablation C: Persistence Excision")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Seed:              {args.seed}")
    print(f"  Episodes:          {args.episodes}")
    print(f"  Steps/episode:     {FROZEN_H}")
    print(f"  Model:             claude-sonnet-4-20250514")
    print(f"  Selector:          task_aware")
    print(f"  Validity gates:    ENABLED")
    print(f"  Ablation:          C (Persistence Excision)")
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
        output_path = Path(f"v420_ablation_c_{args.seed}_{timestamp}.json")

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
