#!/usr/bin/env python3
"""
RSA-PoC v4.4 — LLM Baseline and Run D′

Runs the LLM deliberator (Claude Sonnet 4) with v4.4 dual-channel observations.

Baseline-44: Dual-channel format, normative opacity DISABLED
Run D′:      Dual-channel format, normative opacity ENABLED (Golden Test)

Usage:
    python -m src.rsa_poc.v440.run_llm_baseline                     # Baseline-44
    python -m src.rsa_poc.v440.run_llm_baseline --run-d-prime       # Run D′
    python -m src.rsa_poc.v440.run_llm_baseline --seed 123
    python -m src.rsa_poc.v440.run_llm_baseline --preflight-only
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from .env.tri_demand import TriDemandV440, ACTION_NAMES
from .deliberator import (
    LLMDeliberatorV440,
    LLMDeliberatorConfigV440,
    format_dual_channel_observation,
)
from .core import (
    create_initial_norm_state_v430,
    NormStateV430,
    JCOMP430,
    compute_feasible_430,
)


# Frozen parameters
FROZEN_H = 40  # Steps per episode
FROZEN_E = 20  # Episodes
DEFAULT_SEED = 42

# Preregistered seeds
PREREGISTERED_SEEDS = [42, 123, 456, 789, 1000]


def task_aware_select(justified_action_ids: List[str], obs: Any, regime: int) -> str:
    """
    Select the best action from justified actions using task-aware heuristics.

    This mirrors v4.3 TaskAwareSelector but works on LLM-justified action set.
    Priority: DEPOSIT (at zone) > STAMP (regime 1, at stamp loc) > COLLECT (at source) > MOVE toward goal
    """
    from .env.tri_demand import POSITIONS

    if not justified_action_ids:
        return "A0"  # Default fallback

    pos = tuple(obs.agent_pos)
    inv = obs.inventory
    stamped = obs.stamped
    zones = [obs.zone_a_satisfied, obs.zone_b_satisfied, obs.zone_c_satisfied]
    zone_positions = [tuple(POSITIONS["ZONE_A"]), tuple(POSITIONS["ZONE_B"]), tuple(POSITIONS["ZONE_C"])]

    # DEPOSIT only valid at a zone with inventory
    if "A5" in justified_action_ids and inv > 0 and pos in zone_positions:
        return "A5"

    # STAMP only valid at STAMP_LOCATION in regime 1+ with unstamped inventory
    if "A6" in justified_action_ids and regime >= 1 and inv > 0 and not stamped and pos == tuple(POSITIONS["STAMP_LOCATION"]):
        return "A6"

    # COLLECT only valid at SOURCE with no inventory
    if "A4" in justified_action_ids and inv == 0 and pos == tuple(POSITIONS["SOURCE"]):
        return "A4"

    # Otherwise, prefer movement toward goals
    if inv == 0:
        # Move toward SOURCE
        target = POSITIONS["SOURCE"]
    elif regime >= 1 and not stamped:
        # Move toward STAMP_LOCATION
        target = POSITIONS["STAMP_LOCATION"]
    else:
        # Move toward first unsatisfied zone
        zone_names = ["ZONE_A", "ZONE_B", "ZONE_C"]
        target = None
        for i, zone_name in enumerate(zone_names):
            if not zones[i]:
                target = POSITIONS[zone_name]
                break
        if target is None:
            target = POSITIONS["ZONE_A"]

    # Determine best movement action toward target
    dr = target[0] - pos[0]
    dc = target[1] - pos[1]

    move_priority = []
    if dr < 0 and "A0" in justified_action_ids:  # MOVE_N
        move_priority.append("A0")
    if dr > 0 and "A1" in justified_action_ids:  # MOVE_S
        move_priority.append("A1")
    if dc > 0 and "A2" in justified_action_ids:  # MOVE_E
        move_priority.append("A2")
    if dc < 0 and "A3" in justified_action_ids:  # MOVE_W
        move_priority.append("A3")

    if move_priority:
        return move_priority[0]

    # Fallback: any justified action that's valid
    # Exclude object actions if not at right location
    safe_fallbacks = [a for a in justified_action_ids if a in ["A0", "A1", "A2", "A3"]]
    if safe_fallbacks:
        return safe_fallbacks[0]

    return justified_action_ids[0]


def _apply_repair_simple(norm_state: NormStateV430, repair_action: Any) -> NormStateV430:
    """
    Simplified repair application for v4.4.

    Directly applies patch operations without full gate validation.
    v4.4 focuses on opacity testing, not repair gate semantics.
    """
    from copy import deepcopy
    from .core.dsl import PatchOp

    new_rules = list(norm_state.rules)

    for patch in repair_action.patch_ops:
        if patch.op == PatchOp.ADD_EXCEPTION:
            # Find the rule and add exception
            for i, rule in enumerate(new_rules):
                if rule.id == patch.rule_id:
                    new_rule = deepcopy(rule)
                    object.__setattr__(new_rule, 'exception_condition', patch.new_value)
                    new_rules[i] = new_rule
                    break

    # Create new norm state with updated rules
    return NormStateV430(
        rules=tuple(new_rules),
        law_fingerprint=norm_state.law_fingerprint,
        norm_hash=norm_state.norm_hash,
        current_epoch=norm_state.current_epoch,
        repair_count=norm_state.repair_count + 1,
    )


def run_preflight_validation(
    seed: int,
    normative_opacity: bool = False,
    max_episodes: int = 5,
    verbose: bool = True
) -> bool:
    """
    Run pre-flight validation with deterministic oracle.

    Validates execution-competence gate and basic environment behavior.
    NO API COSTS.
    """
    if verbose:
        print("\n--- Pre-Flight Validation ---")
        print(f"    Normative opacity: {normative_opacity}")

    env = TriDemandV440(seed=seed, normative_opacity=normative_opacity)

    # Simple oracle that always moves toward objectives
    successes = 0
    exec_gate_failures = 0

    for ep in range(max_episodes):
        obs, info = env.reset(episode=ep)
        done = False
        steps = 0

        while not done and steps < FROZEN_H:
            # Simple greedy policy
            action = _oracle_policy(obs, env.regime)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            steps += 1

        if info.get("success"):
            successes += 1

        # Check exec gate at regime 2 boundary
        if env.regime == 2 and env._exec_gate_evaluated and not env._exec_gate_passed:
            exec_gate_failures += 1

    success_rate = successes / max_episodes
    valid = success_rate >= 0.6 and exec_gate_failures == 0

    if verbose:
        print(f"  Success rate: {successes}/{max_episodes} = {success_rate:.1%}")
        print(f"  Exec gate failures: {exec_gate_failures}")
        if valid:
            print("  ✅ Pre-flight PASSED")
        else:
            print("  ❌ Pre-flight FAILED")

    return valid


def _oracle_policy(obs, regime: int) -> str:
    """Simple greedy oracle policy for pre-flight validation."""
    from .env.tri_demand import POSITIONS, Action

    pos = obs.agent_pos
    inv = obs.inventory
    stamped = obs.stamped

    # Track zone satisfaction from observation
    zones_satisfied = [obs.zone_a_satisfied, obs.zone_b_satisfied, obs.zone_c_satisfied]
    zone_names = ["ZONE_A", "ZONE_B", "ZONE_C"]

    # Priority: collect → stamp (if regime 1) → deposit at unsatisfied zone
    if inv == 0:
        # Need to collect - move toward SOURCE or collect if there
        if pos == POSITIONS["SOURCE"]:
            return "A4"  # COLLECT
        return _move_toward(pos, POSITIONS["SOURCE"])

    # Have item - stamp if needed in regime 1+
    if regime >= 1 and not stamped:
        if pos == POSITIONS["STAMP_LOCATION"]:
            return "A6"  # STAMP
        return _move_toward(pos, POSITIONS["STAMP_LOCATION"])

    # Have item - deposit at first unsatisfied zone
    for i, zone_name in enumerate(zone_names):
        if not zones_satisfied[i]:
            zone_pos = POSITIONS[zone_name]
            if pos == zone_pos:
                return "A5"  # DEPOSIT
            return _move_toward(pos, zone_pos)

    # All zones satisfied - just wait (shouldn't happen)
    return "A0"


def _move_toward(from_pos, to_pos) -> str:
    """Return action to move from from_pos toward to_pos."""
    dr = to_pos[0] - from_pos[0]
    dc = to_pos[1] - from_pos[1]

    if dr < 0:
        return "A0"  # MOVE_N
    elif dr > 0:
        return "A1"  # MOVE_S
    elif dc < 0:
        return "A3"  # MOVE_W
    elif dc > 0:
        return "A2"  # MOVE_E

    return "A0"  # Default


def run_single_episode_llm(
    env: TriDemandV440,
    deliberator: LLMDeliberatorV440,
    norm_state: NormStateV430,
    episode: int,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Run a single episode with LLM deliberator."""
    obs, info = env.reset(episode=episode)

    # Get bijection for this episode
    bijection = env.bijection

    # Pass collision traces to deliberator
    deliberator.set_collision_traces(env.get_collision_traces())

    done = False
    step = 0
    total_reward = 0.0
    contradiction_detected = False
    repair_accepted = False
    exec_gate_checked = False

    step_log = []

    while not done and step < FROZEN_H:
        regime = env.regime

        # Check execution-competence gate at regime 1→2 transition
        if regime == 2 and not exec_gate_checked:
            exec_gate_checked = True
            if not env._exec_gate_passed:
                # Gate failed - invalid run
                return {
                    "episode": episode,
                    "steps": step,
                    "success": False,
                    "halt_reason": "EXECUTION_COLLAPSE_UNDER_OPACITY",
                    "exec_gate_passed": False,
                    "total_reward": total_reward,
                    "step_log": step_log,
                }

        # Deliberate
        output = deliberator.deliberate(
            observation=obs,
            norm_state=norm_state,
            episode=episode,
            step=step,
            regime=regime,
            bijection=bijection,
        )

        if output.error:
            if verbose:
                print(f"    Deliberation error: {output.error}")
            break

        # Handle contradiction / repair
        if output.conflict_detected:
            contradiction_detected = True
            if output.repair_action:
                # Simplified repair application (v4.4 focuses on opacity, not full gate validation)
                # Accept repair if it's the right type and we haven't already done that repair
                if output.conflict_type == 'A' and not deliberator.repair_a_issued:
                    norm_state = _apply_repair_simple(norm_state, output.repair_action)
                    repair_accepted = True
                    deliberator.record_repair_accepted('A')
                    env.record_repair_a_accepted(episode)
                elif output.conflict_type == 'B' and not deliberator.repair_b_issued:
                    norm_state = _apply_repair_simple(norm_state, output.repair_action)
                    repair_accepted = True
                    deliberator.record_repair_accepted('B')

        # Select action using task-aware heuristics
        if output.justifications:
            justified_actions = [j.action_id for j in output.justifications]
            action_id = task_aware_select(justified_actions, obs, regime)
        else:
            action_id = "A0"  # Default

        # Execute
        obs, reward, terminated, truncated, exec_info = env.step(action_id)
        total_reward += reward
        done = terminated or truncated

        step_log.append({
            "step": step,
            "action": action_id,
            "reward": reward,
            "regime": regime,
            "conflict": output.conflict_detected,
            "collision_grounded": output.collision_grounded,
        })

        step += 1

        # Update collision traces for next deliberation
        deliberator.set_collision_traces(env.get_collision_traces())

    success = exec_info.get("success", False) if done else False

    return {
        "episode": episode,
        "steps": step,
        "success": success,
        "contradiction_detected": contradiction_detected,
        "repair_accepted": repair_accepted,
        "exec_gate_passed": env._exec_gate_passed if env._exec_gate_evaluated else None,
        "regime_at_end": env.regime,
        "total_reward": total_reward,
        "step_log": step_log,
    }


def run_with_llm(
    seed: int,
    normative_opacity: bool = False,
    max_episodes: int = FROZEN_E,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Run LLM deliberator for a single seed.

    Args:
        seed: Random seed
        normative_opacity: If True, enable normative opacity (Run D′)
        max_episodes: Number of episodes
        verbose: Print progress
    """
    run_name = "Run D′ (Normative Opacity)" if normative_opacity else "Baseline-44"

    if verbose:
        print(f"\n--- {run_name} (Seed {seed}) ---")

    env = TriDemandV440(seed=seed, normative_opacity=normative_opacity)

    config = LLMDeliberatorConfigV440(normative_opacity=normative_opacity)
    deliberator = LLMDeliberatorV440(config)

    # Initialize norm state
    norm_state = create_initial_norm_state_v430()

    start = time.perf_counter()

    successes = 0
    exec_gate_failures = 0
    contradictions_detected = 0
    repairs_accepted = 0
    episode_results = []

    for ep in range(max_episodes):
        ep_result = run_single_episode_llm(
            env=env,
            deliberator=deliberator,
            norm_state=norm_state,
            episode=ep,
            verbose=verbose,
        )
        episode_results.append(ep_result)

        if ep_result["success"]:
            successes += 1
        if ep_result.get("halt_reason") == "EXECUTION_COLLAPSE_UNDER_OPACITY":
            exec_gate_failures += 1
        if ep_result.get("contradiction_detected"):
            contradictions_detected += 1
        if ep_result.get("repair_accepted"):
            repairs_accepted += 1

        if verbose:
            status = "✓" if ep_result["success"] else "✗"
            print(f"  Ep{ep}: steps={ep_result['steps']}, {status}, regime={ep_result.get('regime_at_end', '?')}")

    elapsed = time.perf_counter() - start
    success_rate = successes / max_episodes

    result = {
        "version": "4.4.0",
        "run_type": "run_d_prime" if normative_opacity else "baseline_44",
        "seed": seed,
        "max_episodes": max_episodes,
        "normative_opacity": normative_opacity,
        "elapsed_seconds": elapsed,
        "model": config.model,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_successes": successes,
            "success_rate": success_rate,
            "exec_gate_failures": exec_gate_failures,
            "contradictions_detected": contradictions_detected,
            "repairs_accepted": repairs_accepted,
        },
        "episode_results": episode_results,
    }

    if verbose:
        print(f"\n  Results:")
        print(f"    Successes: {successes}/{max_episodes} = {success_rate:.1%}")
        print(f"    Exec gate failures: {exec_gate_failures}")
        print(f"    Contradictions: {contradictions_detected}")
        print(f"    Repairs: {repairs_accepted}")
        print(f"    Time: {elapsed:.1f}s")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="RSA-PoC v4.4 LLM Baseline / Run D′"
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
        "--run-d-prime",
        action="store_true",
        help="Enable normative opacity (Run D′ / Golden Test)"
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
        help="Run only pre-flight validation (no LLM, no cost)"
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip pre-flight validation"
    )

    args = parser.parse_args()

    run_type = "Run D′ (Normative Opacity)" if args.run_d_prime else "Baseline-44"

    print("=" * 70)
    print(f"RSA-PoC v4.4 — {run_type}")
    print("=" * 70)
    print()
    print("Configuration:")
    print(f"  Seed:              {args.seed}")
    print(f"  Episodes:          {args.episodes}")
    print(f"  Steps/episode:     {FROZEN_H}")
    print(f"  Normative opacity: {args.run_d_prime}")
    print(f"  Model:             claude-sonnet-4-20250514")
    print()

    # Pre-flight validation
    if not args.skip_preflight:
        preflight_passed = run_preflight_validation(
            seed=args.seed,
            normative_opacity=args.run_d_prime,
            max_episodes=5,
            verbose=not args.quiet
        )

        if not preflight_passed:
            print("\n❌ Pre-flight validation FAILED")
            return 1

        if args.preflight_only:
            print("\n✅ Pre-flight validation passed (no LLM run requested)")
            return 0

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\nERROR: ANTHROPIC_API_KEY not set")
        return 1

    # Run with LLM
    result = run_with_llm(
        seed=args.seed,
        normative_opacity=args.run_d_prime,
        max_episodes=args.episodes,
        verbose=not args.quiet,
    )

    # Save result
    script_dir = Path(__file__).parent
    results_dir = script_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_suffix = "run_d_prime" if args.run_d_prime else "baseline_44"
        output_path = results_dir / f"v440_{run_suffix}_{args.seed}_{timestamp}.json"

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2, default=str)

    print()
    print("=" * 70)
    print(f"Results saved to: {output_path}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
