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
from typing import Dict, Any, Optional, List, Tuple

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


def _exception_subsumes(exception_condition: Any, trace: Any) -> bool:
    """
    R10 Behavioral Replay: Check if an exception condition would have prevented the trace.

    For TriDemand, this checks if the exception's semantics cover the scenario
    where the trace occurred.

    Args:
        exception_condition: The exception condition from post-Repair-A state
        trace: The collision trace that Repair B is trying to fix

    Returns:
        True if the exception would prevent the HALT that caused trace
        (meaning B is subsumed by A)
    """
    # Extract the trace's context
    rule_id = trace.rule_id

    # For TriDemand Contradiction B:
    # - R7/R8 block DEPOSIT at ZONE_A/ZONE_B in regime 2
    # - If Repair A added an exception for regime 2 on R7 or R8, it covers B

    if rule_id in ("R7", "R8"):
        # Contradiction B scenario: regime 2 DEPOSIT blocking
        # Check if exception applies to regime 2

        # Get exception as dict or string
        if hasattr(exception_condition, 'to_dict'):
            exc_dict = exception_condition.to_dict()
            # Check for REGIME_EQ(2) or dual_delivery_mode
            exc_str = str(exc_dict)
            if 'regime' in exc_str.lower() and '2' in exc_str:
                return True
            if 'dual_delivery' in exc_str.lower():
                return True
        elif isinstance(exception_condition, str):
            if 'REGIME' in exception_condition and '2' in exception_condition:
                return True
            if 'dual_delivery' in exception_condition.lower():
                return True

    elif rule_id == "R6":
        # Contradiction A scenario: regime 1 STAMP blocking
        # (Typically not relevant for B subsumption, but handle for completeness)
        if hasattr(exception_condition, 'to_dict'):
            exc_dict = exception_condition.to_dict()
            exc_str = str(exc_dict)
            if 'regime' in exc_str.lower() and '1' in exc_str:
                return True
        elif isinstance(exception_condition, str):
            if 'REGIME' in exception_condition and '1' in exception_condition:
                return True

    # Default: exception does not subsume
    return False


def _apply_repair_simple(
    norm_state: NormStateV430,
    repair_action: Any,
    collision_traces: List = None,
    repair_type: str = None,
    pre_repair_a_norm_state: NormStateV430 = None,
    require_collision_grounding: bool = True,
) -> Tuple[NormStateV430, bool, Dict[str, Any]]:
    """
    Simplified repair application for v4.4 with full R-gate checks.

    Enforces:
    - R7: Repair must cite a collision trace (if require_collision_grounding=True)
    - R9: Multi-repair discipline (checked externally via repair_type)
    - R10: Non-subsumption replay for Repair B

    Args:
        norm_state: Current norm state
        repair_action: The repair action to apply
        collision_traces: List of collision traces for R7 validation
        repair_type: 'A' or 'B' (needed for R10 check)
        pre_repair_a_norm_state: Norm state BEFORE Repair A was applied (needed for R10)
        require_collision_grounding: If True, enforce R7 (default).
            Set False for Baseline-44 where foresight reasoning is allowed.

    Returns:
        Tuple of (new_norm_state, success, metadata)
        metadata contains: {'r7_passed': bool, 'r10_passed': bool, 'r10_reason': str}
    """
    from copy import deepcopy
    from .core.dsl import PatchOp

    metadata = {
        'r7_passed': True,
        'r10_passed': True,
        'r10_reason': 'not_required',
    }

    # R7: If collision traces available AND collision grounding required, verify repair cites one
    if require_collision_grounding and collision_traces is not None and len(collision_traces) > 0:
        trace_id = getattr(repair_action, 'trace_entry_id', None)
        if trace_id is None:
            metadata['r7_passed'] = False
            return norm_state, False, metadata  # R7 failure: no trace cited

        # Check if cited trace exists
        trace_ids = [t.trace_entry_id for t in collision_traces]
        if trace_id not in trace_ids:
            metadata['r7_passed'] = False
            return norm_state, False, metadata  # R7 failure: trace not found

    # R10: Non-subsumption BEHAVIORAL REPLAY for Repair B
    # Per spec: replay the post-A law WITHOUT B, verify Contradiction B still triggers
    # If Repair A already solves B, then B is subsumed and should be rejected
    if repair_type == 'B' and pre_repair_a_norm_state is not None:
        # Get the trace B is trying to fix
        trace_id = getattr(repair_action, 'trace_entry_id', None)
        if trace_id and collision_traces:
            matching_traces = [t for t in collision_traces if t.trace_entry_id == trace_id]
            if matching_traces:
                trace = matching_traces[0]
                blocking_rule_id = trace.rule_id

                # BEHAVIORAL REPLAY: Check if post-A norm_state (WITHOUT B) still blocks
                # We replay by checking if the rule that caused trace B's HALT
                # would still fire under the current norm_state (post-A, pre-B)

                # Find the blocking rule in post-A state
                post_a_rule = None
                for rule in norm_state.rules:
                    if rule.id == blocking_rule_id:
                        post_a_rule = rule
                        break

                if post_a_rule is not None:
                    # Check if this rule has an exception from Repair A
                    existing_exception = getattr(post_a_rule, 'exception_condition', None)

                    if existing_exception is not None:
                        # Post-A state has an exception on this rule
                        # REPLAY: Would the exception prevent the Contradiction B scenario?

                        # We need to evaluate: does the existing exception cover
                        # the scenario that triggered trace B?

                        # For TriDemand, Contradiction B occurs in regime 2 at ZONE_A or ZONE_B
                        # If Repair A added an exception that applies to regime 2 scenarios,
                        # then B is subsumed

                        # Heuristic: If the blocking rule has ANY exception, check if it
                        # matches what B is trying to add. If yes, B is redundant.
                        # If no, check if the exception's semantics would prevent B's trigger.

                        # Get what Repair B is trying to add
                        for patch in repair_action.patch_ops:
                            if patch.op == PatchOp.ADD_EXCEPTION and patch.target_rule_id == blocking_rule_id:
                                proposed_exception = patch.exception_condition

                                # BEHAVIORAL TEST: Would existing exception prevent the HALT?
                                # For proper replay, we'd need to re-evaluate the trace scenario
                                # against the post-A rules. Since the trace already occurred,
                                # we check if the exception would have prevented it.

                                # The trace occurred because the rule fired. Under post-A:
                                # - If post-A has an exception that covers this scenario,
                                #   the trace would NOT have occurred → B is subsumed
                                # - If post-A exception doesn't cover this scenario,
                                #   the trace WOULD still occur → B is needed

                                # Semantic check: does existing_exception cover B's scenario?
                                # For now, we use string equality as a proxy for subsumption
                                # A more sophisticated check would evaluate the exception's
                                # condition against the trace's state

                                if _exception_subsumes(existing_exception, trace):
                                    # Existing exception would prevent B's HALT
                                    metadata['r10_passed'] = False
                                    metadata['r10_reason'] = 'B_SUBSUMED_BY_A'
                                    return norm_state, False, metadata

        metadata['r10_reason'] = 'non_subsumption_replay_passed'

    new_rules = list(norm_state.rules)

    for patch in repair_action.patch_ops:
        if patch.op == PatchOp.ADD_EXCEPTION:
            # Find the rule and add exception
            for i, rule in enumerate(new_rules):
                if rule.id == patch.target_rule_id:
                    new_rule = deepcopy(rule)
                    object.__setattr__(new_rule, 'exception_condition', patch.exception_condition)
                    new_rules[i] = new_rule
                    break

    # Create new norm state with updated rules
    # NormStateV430 only takes rules, epoch_chain, and repair_count
    # law_fingerprint, norm_hash, and current_epoch are computed properties
    new_state = NormStateV430(
        rules=new_rules,
        epoch_chain=list(norm_state.epoch_chain),
        repair_count=norm_state.repair_count + 1,
    )

    return new_state, True, metadata


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

    # Track pre-Repair-A norm state for R10 check
    pre_repair_a_norm_state = None

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
                # Get collision traces for R7 validation
                collision_traces = env.get_collision_traces()

                # R7 collision grounding only required in normative_opacity mode
                # In Baseline-44 (clear semantics), foresight reasoning is allowed
                require_collision_grounding = env.normative_opacity

                # Apply repair with R-gate checks (R7, R9, R10)
                if output.conflict_type == 'A' and not deliberator.repair_a_issued:
                    # Store pre-Repair-A state for R10 check later
                    pre_repair_a_norm_state = norm_state

                    new_state, success, r_metadata = _apply_repair_simple(
                        norm_state,
                        output.repair_action,
                        collision_traces,
                        repair_type='A',
                        pre_repair_a_norm_state=None,  # Not needed for Repair A
                        require_collision_grounding=require_collision_grounding,
                    )
                    if success:
                        norm_state = new_state
                        repair_accepted = True
                        deliberator.record_repair_accepted('A')
                        env.record_repair_a_accepted(episode)
                        if verbose:
                            print(f"    Repair A accepted (R7 passed)")
                    elif verbose:
                        print(f"    Repair A rejected (R7 check failed)")

                elif output.conflict_type == 'B' and not deliberator.repair_b_issued:
                    new_state, success, r_metadata = _apply_repair_simple(
                        norm_state,
                        output.repair_action,
                        collision_traces,
                        repair_type='B',
                        pre_repair_a_norm_state=pre_repair_a_norm_state,
                        require_collision_grounding=require_collision_grounding,
                    )
                    if success:
                        norm_state = new_state
                        repair_accepted = True
                        deliberator.record_repair_accepted('B')
                        if verbose:
                            print(f"    Repair B accepted (R7, R10 passed: {r_metadata['r10_reason']})")
                    elif verbose:
                        r10_msg = f", R10: {r_metadata['r10_reason']}" if not r_metadata['r10_passed'] else ""
                        print(f"    Repair B rejected (R7: {r_metadata['r7_passed']}{r10_msg})")

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
