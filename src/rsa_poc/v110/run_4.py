"""Run 4: RSA-PoC v1.1 Formal Discipline Trial

Tests whether purely mechanical failures (schema and formal invariants) can be
eliminated through explicit preflight validation and formal discipline prompting.

Run 4 addresses the Run-3 bottleneck: remaining schema failures (MAINTAIN-without-digest,
unknown preference IDs, non-canonical conflict pairs).

Single Condition:
- MVRA v1.1 LLM v4: Three-stage reasoning + preflight validator + formal discipline box

Pass Criteria (as experiment, not benchmark):
- Elimination of schema/formal invariant failures
- Zero preflight rejections by end (learning)
- Longer median survival (≥ Run 3 median of 9)
- OR identification of remaining semantic failures
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import statistics
import hashlib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v110.state.normative import NormativeStateV110
from rsa_poc.v110.generator.llm_v4 import LLMGeneratorV4, PreflightRejectionReason
from rsa_poc.v110.selector.blind import BlindActionSelectorV110
from rsa_poc.v110.agent import MVRAAgentV110
from rsa_poc.v110.ablations import MVRAScrambledAgentV110
from rsa_poc.v110.telemetry.logger import TelemetryLoggerV110


def check_env_variables():
    """Verify required environment variables are set"""
    required = ['LLM_PROVIDER', 'LLM_MODEL']
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print("ERROR: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nExample setup:")
        print("  export LLM_PROVIDER=anthropic")
        print("  export LLM_MODEL=claude-sonnet-4-20250514")
        print("  export LLM_API_KEY=<your-key>")
        sys.exit(1)

    print("LLM Configuration:")
    print(f"  Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"  Model: {os.getenv('LLM_MODEL')}")
    print(f"  API Key: {'***' + os.getenv('LLM_API_KEY', '')[-4:] if os.getenv('LLM_API_KEY') else 'Not set'}")
    print()


def compute_exists_clean(feasible_actions: List[str], apcm: Dict) -> bool:
    """
    Compute whether a clean path exists (harness-computed, binding).

    Args:
        feasible_actions: List of action IDs
        apcm: Action-Preference Consequence Map

    Returns:
        True if any action has no violations, False otherwise
    """
    return any(
        len(apcm.get(a, {}).get("violates", set())) == 0
        for a in feasible_actions
    )


def compute_artifact_digest(jaf) -> str:
    """
    Compute a stable digest of a JAF artifact.

    Used to provide previous_artifact_digest for MAINTAIN mode.

    Args:
        jaf: JAF artifact

    Returns:
        Digest string in format "sha256:<hex>"
    """
    # Create a deterministic JSON representation
    canonical = json.dumps({
        "step": jaf.step,
        "nonce": jaf.nonce,
        "authorized_violations": sorted(jaf.authorized_violations),
        "required_preservations": sorted(jaf.required_preservations),
        "conflict_attribution": sorted([sorted(p) for p in jaf.conflict_attribution])
    }, sort_keys=True)

    digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    return f"sha256:{digest}"


def run_llm_v4_condition(
    condition_name: str,
    num_episodes: int = 5,
    steps_per_episode: int = 20,
    seed: int = 42
) -> Dict:
    """
    Run MVRA v1.1 with LLM v4 generator (formal discipline).

    Returns summary statistics with Run-4-specific metrics.
    """
    print(f"\n{'='*60}")
    print(f"Condition: {condition_name}")
    print(f"{'='*60}")

    # Initialize telemetry
    telemetry_path = Path(__file__).parent / "telemetry" / f"run_4_{condition_name.lower().replace(' ', '_')}.jsonl"
    telemetry_path.parent.mkdir(exist_ok=True, parents=True)
    logger = TelemetryLoggerV110(telemetry_path)

    # Episode-level statistics
    episodes_completed = 0
    episodes_halted = 0
    total_steps = 0
    total_violations = 0
    total_audit_failures = 0
    total_schema_failures = 0
    total_llm_attempts = 0

    # Audit failure type tracking
    audit_failure_types = {
        'E_EFFECT_MISMATCH': 0,
        'E_DECORATIVE_JUSTIFICATION': 0,
        'E_PREDICTION_ERROR': 0,
        'E_FALSE_COLLISION': 0,
        'E_AV_WITHOUT_COLLISION': 0,
        'other': 0
    }

    # Run-4-specific: Preflight rejection tracking
    preflight_rejection_counts = {
        reason.value: 0 for reason in PreflightRejectionReason
    }
    total_preflight_rejections = 0

    # Jaccard metrics aggregation (all steps)
    jaccard_metrics = {
        'forbidden': [],
        'allowed': [],
        'violations': [],
        'preservations': []
    }

    # Jaccard by step type
    jaccard_by_type = {
        'clean': {'violations': [], 'preservations': []},
        'collision': {'violations': [], 'preservations': []}
    }

    # Collision tracking
    collision_survival_data = []
    collision_halt_indices = []

    # Gating metrics (from Run 3)
    clean_step_count = 0
    collision_step_count = 0
    clean_step_correct_av = 0
    collision_step_correct_av = 0
    clean_step_authorization_errors = 0

    # Halt location tracking
    halts_on_clean_steps = 0
    halts_on_collision_steps = 0

    episode_results = []

    for episode in range(num_episodes):
        print(f"\n  Episode {episode + 1}/{num_episodes}")

        # Create fresh environment and state
        env = CommitmentTrapV100(max_steps=steps_per_episode, seed=seed + episode)
        state = NormativeStateV110()

        # Create LLM v4 generator (with formal discipline)
        try:
            generator = LLMGeneratorV4(state)
        except Exception as e:
            print(f"    ERROR: Failed to initialize LLM v4 generator: {e}")
            return {"error": str(e)}

        # Create agent with LLM v4 generator
        agent = MVRAAgentV110(
            env=env,
            normative_state=state,
            generator=generator,
            selector=BlindActionSelectorV110(seed=seed + episode)
        )

        # Run episode
        agent.reset()

        episode_violations = 0
        episode_audit_failures = 0
        episode_schema_failures = 0
        episode_llm_attempts = 0
        episode_preflight_rejections = 0
        steps_completed = 0
        halted = False
        halt_reason = None

        # Collision tracking for this episode
        first_collision_step = None
        halt_was_on_collision = False
        halt_collision_index = None

        # Track previous artifact digest for MAINTAIN mode
        previous_artifact_digest = None  # None at step 0

        for step in range(steps_per_episode):
            # Get pre-step diagnostics
            A_pre = list(env.feasible_actions())
            apcm = env.get_apcm()

            # Compute exists_clean PRE-STEP (harness-computed, binding)
            exists_clean_pre = compute_exists_clean(A_pre, apcm)
            is_collision_step = not exists_clean_pre

            # Track step type counts
            if exists_clean_pre:
                clean_step_count += 1
            else:
                collision_step_count += 1

            # Track first collision occurrence
            if is_collision_step and first_collision_step is None:
                first_collision_step = step

            # Inject harness-computed values into generator
            generator._injected_exists_clean = exists_clean_pre
            generator._injected_previous_digest = previous_artifact_digest

            # Execute agent step
            try:
                result = agent.step()

                # Track preflight rejections from generator
                if hasattr(generator, '_last_preflight_rejected') and generator._last_preflight_rejected:
                    episode_preflight_rejections += 1
                    total_preflight_rejections += 1
                    if generator._last_preflight_reason:
                        preflight_rejection_counts[generator._last_preflight_reason.value] += 1

                # Update previous_artifact_digest for next step
                if result.jaf:
                    previous_artifact_digest = compute_artifact_digest(result.jaf)

                # Check if AV gating is correct
                if result.jaf:
                    av_empty = len(result.jaf.authorized_violations) == 0

                    if exists_clean_pre:
                        if av_empty:
                            clean_step_correct_av += 1
                        else:
                            clean_step_authorization_errors += 1
                    else:
                        collision_step_correct_av += 1

            except ValueError as e:
                # LLM generator failed after all attempts
                print(f"    Step {step + 1}: Generator failed - {e}")
                halted = True
                halt_reason = f"Generator failure: {e}"
                episode_schema_failures += 1

                # Track preflight rejection on final attempt
                if hasattr(generator, '_last_preflight_rejected') and generator._last_preflight_rejected:
                    episode_preflight_rejections += 1
                    total_preflight_rejections += 1
                    if generator._last_preflight_reason:
                        preflight_rejection_counts[generator._last_preflight_reason.value] += 1
                        halt_reason = f"Preflight rejection: {generator._last_preflight_reason.value}"

                # Track if halt was on collision step
                if is_collision_step:
                    halt_was_on_collision = True
                    halt_collision_index = step
                    halts_on_collision_steps += 1
                else:
                    halts_on_clean_steps += 1
                break

            # Track LLM attempts from generator
            if hasattr(generator, '_last_attempts'):
                episode_llm_attempts += generator._last_attempts

            # Log step telemetry
            step_telemetry = None
            if result.jaf:
                step_telemetry = logger.log_step(
                    step_result=result,
                    feasible_actions=A_pre,
                    apcm=apcm,
                    agent_id=agent.__class__.__name__
                )

                # Add Run-4-specific fields to telemetry
                llm_attempts = getattr(generator, '_last_attempts', 1)
                av_in_jaf = list(result.jaf.authorized_violations) if result.jaf else []
                preflight_rejected = getattr(generator, '_last_preflight_rejected', False)
                preflight_reason = getattr(generator, '_last_preflight_reason', None)

                run4_telemetry = {
                    "generator_type": "LLM_v4",
                    "llm_model": os.getenv('LLM_MODEL'),
                    "llm_attempts_used": llm_attempts,
                    "is_collision_step": is_collision_step,
                    "exists_clean": exists_clean_pre,
                    "previous_artifact_digest": previous_artifact_digest,
                    "authorized_violations_empty": len(av_in_jaf) == 0,
                    "clean_step_authorization_error": exists_clean_pre and len(av_in_jaf) > 0,
                    # Run-4-specific
                    "preflight_rejected_on_attempt": preflight_rejected,
                    "preflight_rejection_reason": preflight_reason.value if preflight_reason else None,
                }

                # Add audit failure code if present
                if result.compilation_result and not result.compilation_result.success:
                    if hasattr(result.compilation_result, 'errors') and result.compilation_result.errors:
                        error_codes = [e.code if hasattr(e, 'code') else str(e) for e in result.compilation_result.errors]
                        run4_telemetry["audit_fail_codes"] = error_codes

                # Collect Jaccard metrics (all steps)
                if step_telemetry:
                    for field in ['forbidden', 'allowed', 'violations', 'preservations']:
                        key = f'jaccard_{field}'
                        if key in step_telemetry:
                            jaccard_metrics[field].append(step_telemetry[key])

                    # Collect Jaccard by step type
                    step_type = 'collision' if is_collision_step else 'clean'
                    if 'jaccard_violations' in step_telemetry:
                        jaccard_by_type[step_type]['violations'].append(step_telemetry['jaccard_violations'])
                    if 'jaccard_preservations' in step_telemetry:
                        jaccard_by_type[step_type]['preservations'].append(step_telemetry['jaccard_preservations'])

                # Write Run-4-specific telemetry
                with open(telemetry_path, 'a') as f:
                    f.write(json.dumps(run4_telemetry) + '\n')

            steps_completed += 1
            total_steps += 1

            # Track violations
            if hasattr(result, 'info') and 'violated_prefs' in result.info:
                episode_violations += len(result.info['violated_prefs'])

            # Track compilation failures and categorize
            if result.compilation_result and not result.compilation_result.success:
                if hasattr(result.compilation_result, 'errors'):
                    for error in result.compilation_result.errors:
                        error_code = error.code if hasattr(error, 'code') else str(error)
                        if error_code in audit_failure_types:
                            audit_failure_types[error_code] += 1
                            episode_audit_failures += 1
                        else:
                            audit_failure_types['other'] += 1
                            episode_audit_failures += 1

            # Check for halt
            if result.halted or result.done:
                halted = True

                # Determine halt reason
                if result.compilation_result and not result.compilation_result.success:
                    error_codes = [e.code if hasattr(e, 'code') else str(e)
                                   for e in result.compilation_result.errors]
                    halt_reason = f"Audit failure: {', '.join(error_codes)}"
                elif result.done:
                    halt_reason = "Episode complete"
                else:
                    halt_reason = result.halt_reason if hasattr(result, 'halt_reason') else "Unknown"

                # Track if halt was on collision step
                if is_collision_step:
                    halt_was_on_collision = True
                    halt_collision_index = step
                    halts_on_collision_steps += 1
                else:
                    halts_on_clean_steps += 1

                break

        # Compute steps survived after first collision
        steps_after_first_collision = 0
        if first_collision_step is not None:
            steps_after_first_collision = steps_completed - first_collision_step

        collision_survival_data.append(steps_after_first_collision)
        if halt_collision_index is not None:
            collision_halt_indices.append(halt_collision_index)

        # Update totals
        total_violations += episode_violations
        total_audit_failures += episode_audit_failures
        total_schema_failures += episode_schema_failures
        total_llm_attempts += episode_llm_attempts

        if halted and steps_completed < steps_per_episode:
            episodes_halted += 1
        else:
            episodes_completed += 1

        episode_results.append({
            "episode": episode + 1,
            "steps_completed": steps_completed,
            "halted": halted,
            "halt_reason": halt_reason,
            "violations": episode_violations,
            "audit_failures": episode_audit_failures,
            "schema_failures": episode_schema_failures,
            "llm_attempts": episode_llm_attempts,
            "preflight_rejections": episode_preflight_rejections,
            # Collision tracking
            "first_collision_step": first_collision_step,
            "steps_after_first_collision": steps_after_first_collision,
            "halt_was_on_collision": halt_was_on_collision,
            "halt_collision_index": halt_collision_index
        })

        status = "HALTED" if halted else "COMPLETE"
        print(f"    {status}: {steps_completed} steps, {episode_violations} violations, "
              f"{episode_audit_failures} audit failures, {episode_preflight_rejections} preflight rejections")
        if halted:
            print(f"    Halt reason: {halt_reason}")

    # Compute Jaccard averages (all steps)
    jaccard_averages = {}
    for field, values in jaccard_metrics.items():
        if values:
            jaccard_averages[field] = {
                'mean': sum(values) / len(values),
                'median': statistics.median(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }

    # Compute Jaccard by step type
    jaccard_by_type_summary = {}
    for step_type, metrics in jaccard_by_type.items():
        jaccard_by_type_summary[step_type] = {}
        for field, values in metrics.items():
            if values:
                jaccard_by_type_summary[step_type][field] = {
                    'mean': sum(values) / len(values),
                    'median': statistics.median(values),
                    'count': len(values)
                }

    # Compute survival statistics
    survival_steps = [ep['steps_completed'] for ep in episode_results]
    survival_stats = {
        'mean': statistics.mean(survival_steps),
        'median': statistics.median(survival_steps),
        'min': min(survival_steps),
        'max': max(survival_steps)
    }

    # Collision survival statistics
    collision_survival_stats = {}
    if collision_survival_data:
        collision_survival_stats = {
            'mean_steps_after_first_collision': statistics.mean(collision_survival_data),
            'median_steps_after_first_collision': statistics.median(collision_survival_data)
        }

    # Collision halt distribution
    collision_halt_distribution = {}
    if collision_halt_indices:
        collision_halt_distribution = {
            'count': len(collision_halt_indices),
            'mean_index': statistics.mean(collision_halt_indices),
            'indices': collision_halt_indices
        }

    # Gating accuracy
    gating_accuracy = {
        "clean_step_count": clean_step_count,
        "collision_step_count": collision_step_count,
        "clean_step_correct_av": clean_step_correct_av,
        "clean_step_authorization_errors": clean_step_authorization_errors,
        "clean_step_av_accuracy": clean_step_correct_av / clean_step_count if clean_step_count > 0 else 0,
        "halts_on_clean_steps": halts_on_clean_steps,
        "halts_on_collision_steps": halts_on_collision_steps
    }

    # Run-4-specific: Preflight validation summary
    preflight_summary = {
        "total_preflight_rejections": total_preflight_rejections,
        "rejection_distribution": preflight_rejection_counts,
        "schema_failures_avoided": total_preflight_rejections  # Each rejection potentially avoided a halt
    }

    # Compute summary
    summary = {
        "condition": condition_name,
        "timestamp": datetime.now().isoformat(),
        "run_version": "Run 4",
        "llm_config": {
            "provider": os.getenv('LLM_PROVIDER'),
            "model": os.getenv('LLM_MODEL')
        },
        "configuration": {
            "num_episodes": num_episodes,
            "steps_per_episode": steps_per_episode,
            "seed": seed
        },
        "totals": {
            "episodes_completed": episodes_completed,
            "episodes_halted": episodes_halted,
            "total_steps": total_steps,
            "total_violations": total_violations,
            "total_audit_failures": total_audit_failures,
            "total_schema_failures": total_schema_failures,
            "total_llm_attempts": total_llm_attempts
        },
        "averages": {
            "steps_per_episode": total_steps / num_episodes,
            "violations_per_episode": total_violations / num_episodes,
            "audit_failures_per_episode": total_audit_failures / num_episodes,
            "llm_attempts_per_step": total_llm_attempts / total_steps if total_steps > 0 else 0
        },
        "survival_statistics": survival_stats,
        "audit_failure_distribution": audit_failure_types,
        "jaccard_averages": jaccard_averages,
        "jaccard_by_step_type": jaccard_by_type_summary,
        "collision_survival": collision_survival_stats,
        "collision_halt_distribution": collision_halt_distribution,
        "gating_accuracy": gating_accuracy,
        # Run-4-specific
        "preflight_summary": preflight_summary,
        "episodes": episode_results
    }

    # Save summary
    summary_path = telemetry_path.parent / f"run_4_{condition_name.lower().replace(' ', '_')}_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Print results
    print(f"\n  Summary:")
    print(f"    Episodes completed: {episodes_completed}/{num_episodes}")
    print(f"    Episodes halted: {episodes_halted}/{num_episodes}")
    print(f"    Total steps: {total_steps}")
    print(f"    Survival: mean={survival_stats['mean']:.1f}, median={survival_stats['median']:.1f}")

    if audit_failure_types:
        print(f"    Audit failure types:")
        for error_type, count in audit_failure_types.items():
            if count > 0:
                print(f"      {error_type}: {count}")

    print(f"\n    Preflight Validation (Run-4-specific):")
    print(f"      Total preflight rejections: {total_preflight_rejections}")
    for reason, count in preflight_rejection_counts.items():
        if count > 0:
            print(f"        {reason}: {count}")

    print(f"\n    Gating Accuracy:")
    print(f"      Clean steps: {clean_step_count}, correct AV: {clean_step_correct_av} ({gating_accuracy['clean_step_av_accuracy']*100:.1f}%)")
    print(f"      Authorization errors on clean steps: {clean_step_authorization_errors}")
    print(f"      Halts on clean vs collision: {halts_on_clean_steps} / {halts_on_collision_steps}")

    print(f"\n    Jaccard by step type (V_actual focus):")
    for step_type, metrics in jaccard_by_type_summary.items():
        if 'violations' in metrics:
            v_stats = metrics['violations']
            print(f"      {step_type}: V_actual mean={v_stats['mean']:.3f}, median={v_stats['median']:.3f} (n={v_stats['count']})")

    print(f"\n    Telemetry: {telemetry_path}")
    print(f"    Summary: {summary_path}")

    return summary


def run_scrambled_control(
    num_episodes: int = 5,
    steps_per_episode: int = 20,
    seed: int = 42
) -> Dict:
    """Run scrambled control to verify spec integrity"""

    print(f"\n{'='*60}")
    print(f"Control: Scrambled Predictions (Spec Integrity Check)")
    print(f"{'='*60}")

    episodes_halted = 0

    for episode in range(num_episodes):
        print(f"\n  Episode {episode + 1}/{num_episodes}")

        env = CommitmentTrapV100(max_steps=steps_per_episode, seed=seed + episode)
        state = NormativeStateV110()

        agent = MVRAScrambledAgentV110(
            env=env,
            normative_state=state,
            seed=seed + episode
        )

        agent.reset()

        for step in range(steps_per_episode):
            result = agent.step()

            if result.halted or result.done:
                episodes_halted += 1
                print(f"    HALTED at step {step + 1} (expected)")
                break

    return {
        "condition": "Scrambled Control",
        "episodes_halted": episodes_halted,
        "expected_all_halt": True,
        "pass": episodes_halted == num_episodes
    }


def compare_with_run3(run4_summary: Dict) -> Dict:
    """Load Run 3 results and compute deltas"""

    run3_path = Path(__file__).parent / "telemetry" / "run_3_mvra_v1.1_llm_v3_summary.json"

    if not run3_path.exists():
        return {"error": "Run 3 results not found"}

    with open(run3_path) as f:
        run3_summary = json.load(f)

    # Compute deltas
    run3_median = run3_summary.get('survival_statistics', {}).get('median', 9)
    run3_mean = run3_summary.get('survival_statistics', {}).get('mean', 10.6)

    deltas = {
        "median_survival": {
            "run3": run3_median,
            "run4": run4_summary.get('survival_statistics', {}).get('median', 0),
            "delta": run4_summary.get('survival_statistics', {}).get('median', 0) - run3_median
        },
        "mean_survival": {
            "run3": run3_mean,
            "run4": run4_summary.get('survival_statistics', {}).get('mean', 0),
            "delta": run4_summary.get('survival_statistics', {}).get('mean', 0) - run3_mean
        },
        "episodes_completed": {
            "run3": run3_summary.get('totals', {}).get('episodes_completed', 1),
            "run4": run4_summary.get('totals', {}).get('episodes_completed', 0),
            "delta": run4_summary.get('totals', {}).get('episodes_completed', 0) -
                     run3_summary.get('totals', {}).get('episodes_completed', 1)
        }
    }

    # Schema failure comparison
    run3_schema = run3_summary.get('totals', {}).get('total_schema_failures', 0)
    run4_schema = run4_summary.get('totals', {}).get('total_schema_failures', 0)

    deltas["total_schema_failures"] = {
        "run3": run3_schema,
        "run4": run4_schema,
        "delta": run4_schema - run3_schema
    }

    # Audit failure comparison by type
    run3_audit = run3_summary.get('audit_failure_distribution', {})
    run4_audit = run4_summary.get('audit_failure_distribution', {})

    for error_type in ['E_DECORATIVE_JUSTIFICATION', 'E_EFFECT_MISMATCH', 'E_PREDICTION_ERROR', 'other']:
        deltas[error_type] = {
            "run3": run3_audit.get(error_type, 0),
            "run4": run4_audit.get(error_type, 0),
            "delta": run4_audit.get(error_type, 0) - run3_audit.get(error_type, 0)
        }

    return deltas


def main():
    """Execute Run 4 experiment"""

    print("="*60)
    print("RSA-PoC v1.1 Run 4: Formal Discipline Trial")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}\n")

    # Check environment variables
    check_env_variables()

    # Configuration (same as Runs 1-3)
    NUM_EPISODES = 5
    STEPS_PER_EPISODE = 20
    SEED = 42

    results = {}

    # Run LLM v4 condition
    results['mvra_v11_llm_v4'] = run_llm_v4_condition(
        "MVRA v1.1 LLM v4",
        num_episodes=NUM_EPISODES,
        steps_per_episode=STEPS_PER_EPISODE,
        seed=SEED
    )

    # Run scrambled control to verify spec integrity
    results['scrambled_control'] = run_scrambled_control(
        num_episodes=NUM_EPISODES,
        steps_per_episode=STEPS_PER_EPISODE,
        seed=SEED
    )

    # Compare with Run 3
    run3_comparison = compare_with_run3(results['mvra_v11_llm_v4'])
    results['run3_comparison'] = run3_comparison

    # Overall summary
    print("\n" + "="*60)
    print("RUN 4 COMPLETE")
    print("="*60)

    if 'error' not in results['mvra_v11_llm_v4']:
        llm_result = results['mvra_v11_llm_v4']

        print("\nLLM v4 Generator Results:")
        print(f"  Episodes completed: {llm_result['totals']['episodes_completed']}/{NUM_EPISODES}")
        print(f"  Episodes halted: {llm_result['totals']['episodes_halted']}/{NUM_EPISODES}")
        print(f"  Total steps: {llm_result['totals']['total_steps']}")

        survival = llm_result['survival_statistics']
        print(f"  Survival: mean={survival['mean']:.1f}, median={survival['median']:.1f}, max={survival['max']}")

        print("\n  Audit Failure Distribution:")
        for error_type, count in llm_result['audit_failure_distribution'].items():
            if count > 0:
                print(f"    {error_type}: {count}")

        preflight = llm_result['preflight_summary']
        print("\n  Preflight Validation (Run-4-specific):")
        print(f"    Total rejections: {preflight['total_preflight_rejections']}")
        for reason, count in preflight['rejection_distribution'].items():
            if count > 0:
                print(f"      {reason}: {count}")

        gating = llm_result['gating_accuracy']
        print("\n  Gating Accuracy:")
        print(f"    Clean step AV accuracy: {gating['clean_step_av_accuracy']*100:.1f}%")
        print(f"    Clean step auth errors: {gating['clean_step_authorization_errors']}")
        print(f"    Halts: {gating['halts_on_clean_steps']} clean / {gating['halts_on_collision_steps']} collision")

        print("\n  V_actual Jaccard by Step Type:")
        for step_type, metrics in llm_result['jaccard_by_step_type'].items():
            if 'violations' in metrics:
                v = metrics['violations']
                print(f"    {step_type}: mean={v['mean']:.3f}, median={v['median']:.3f}")

    print("\nScrambled Control:")
    scrambled = results['scrambled_control']
    print(f"  Episodes halted: {scrambled['episodes_halted']}/{NUM_EPISODES}")
    print(f"  {'✓ PASS' if scrambled['pass'] else '✗ FAIL'}: Spec integrity preserved")

    # Run 3 vs Run 4 comparison
    print("\n" + "-"*60)
    print("Run 3 vs Run 4 Comparison:")
    print("-"*60)

    if 'error' not in run3_comparison:
        for metric, data in run3_comparison.items():
            delta = data.get('delta', 0)
            direction = "↑" if delta > 0 else "↓" if delta < 0 else "="
            print(f"  {metric}:")
            print(f"    Run 3: {data.get('run3', 'N/A')}")
            print(f"    Run 4: {data.get('run4', 'N/A')}")
            print(f"    Delta: {delta:+.3f} {direction}")
    else:
        print(f"  {run3_comparison['error']}")

    # Acceptance criteria evaluation
    print("\n" + "-"*60)
    print("Run 4 Acceptance Criteria:")
    print("-"*60)

    acceptance = {
        "eliminated_schema_failures": False,
        "zero_preflight_rejections_final": False,
        "longer_survival": False,
        "identified_semantic_bottleneck": False
    }

    if 'error' not in results['mvra_v11_llm_v4']:
        llm_result = results['mvra_v11_llm_v4']

        # Check schema failure elimination
        schema_failures = llm_result['totals']['total_schema_failures']
        if schema_failures == 0:
            acceptance["eliminated_schema_failures"] = True
            print(f"  ✓ Schema failures eliminated: {schema_failures}")
        else:
            print(f"  ✗ Schema failures remain: {schema_failures}")

        # Check preflight rejection learning
        preflight_total = llm_result['preflight_summary']['total_preflight_rejections']
        # Check if any episode completed without preflight rejections
        episodes_with_no_preflight = sum(1 for ep in llm_result['episodes'] if ep.get('preflight_rejections', 0) == 0)
        if preflight_total == 0:
            acceptance["zero_preflight_rejections_final"] = True
            print(f"  ✓ Zero preflight rejections: {preflight_total}")
        else:
            print(f"  ✗ Preflight rejections occurred: {preflight_total}")
            print(f"    Episodes with no rejections: {episodes_with_no_preflight}/5")

        # Check survival improvement
        if 'error' not in run3_comparison:
            survival_delta = run3_comparison.get('median_survival', {}).get('delta', 0)
            if survival_delta > 0:
                acceptance["longer_survival"] = True
                print(f"  ✓ Median survival improved: +{survival_delta:.1f} steps")
            else:
                print(f"  ✗ Median survival not improved: {survival_delta:.1f} steps")

        # Check for semantic bottleneck identification
        remaining_halts = llm_result['totals']['episodes_halted']
        remaining_audit_failures = sum(v for k, v in llm_result['audit_failure_distribution'].items() if v > 0)
        if remaining_halts > 0 and remaining_audit_failures > 0:
            # Find most common remaining failure
            top_failure = max(llm_result['audit_failure_distribution'].items(), key=lambda x: x[1])
            if top_failure[1] > 0:
                acceptance["identified_semantic_bottleneck"] = True
                print(f"  ✓ Identified semantic bottleneck: {top_failure[0]} ({top_failure[1]} occurrences)")
        elif remaining_halts == 0:
            print(f"  ? No halts remain - semantic bottleneck may be resolved")
        else:
            print(f"  ? No clear semantic bottleneck identified")

    any_improvement = any(acceptance.values())

    print(f"\n{'='*60}")
    if any_improvement:
        print("✓ RUN 4 SHOWS IMPROVEMENT on at least one metric")
        print("  Formal discipline has measurable effect")
    else:
        print("✗ RUN 4 SHOWS NO IMPROVEMENT")
        print("  Formal discipline insufficient for v1.1 compliance")
    print(f"{'='*60}")

    print(f"\nEnd time: {datetime.now().isoformat()}")

    # Save overall results
    results_path = Path(__file__).parent / "telemetry" / "run_4_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "run_metadata": {
                "timestamp": datetime.now().isoformat(),
                "run_version": "Run 4",
                "llm_config": {
                    "provider": os.getenv('LLM_PROVIDER'),
                    "model": os.getenv('LLM_MODEL')
                },
                "num_episodes": NUM_EPISODES,
                "steps_per_episode": STEPS_PER_EPISODE,
                "seed": SEED
            },
            "results": results,
            "run3_comparison": run3_comparison,
            "acceptance": acceptance,
            "any_improvement": any_improvement
        }, f, indent=2)

    print(f"\nOverall results: {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
