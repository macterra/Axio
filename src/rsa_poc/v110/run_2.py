"""Run 2: RSA-PoC v1.1 Explicit Consequence Reasoning Trial

Tests whether an LLM can satisfy v1.1 audits when forced to explicitly
reason through consequences (V_actual/P_actual) prior to emitting JAF.

Run 2 addresses the primary bottleneck from Run 1: failure to compute
V_actual (inevitable violations) on collision steps.

Single Condition:
- MVRA v1.1 LLM v2: Two-phase output with mandatory consequence reasoning

Pass Criteria (as experiment, not benchmark):
- Improved V_actual Jaccard on collision steps vs Run 1
- OR longer median survival
- OR failure mode shift (fewer E_EFFECT_MISMATCH, later failures)
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import statistics

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v110.state.normative import NormativeStateV110
from rsa_poc.v110.generator.llm_v2 import LLMGeneratorV2
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


def run_llm_v2_condition(
    condition_name: str,
    num_episodes: int = 5,
    steps_per_episode: int = 20,
    seed: int = 42
) -> Dict:
    """
    Run MVRA v1.1 with LLM v2 generator (explicit consequence reasoning).

    Returns summary statistics with Run-2-specific metrics.
    """
    print(f"\n{'='*60}")
    print(f"Condition: {condition_name}")
    print(f"{'='*60}")

    # Initialize telemetry
    telemetry_path = Path(__file__).parent / "telemetry" / f"run_2_{condition_name.lower().replace(' ', '_')}.jsonl"
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
        'other': 0
    }

    # Jaccard metrics aggregation (all steps)
    jaccard_metrics = {
        'forbidden': [],
        'allowed': [],
        'violations': [],
        'preservations': []
    }

    # Run-2-specific: Jaccard by step type
    jaccard_by_type = {
        'clean': {'violations': [], 'preservations': []},
        'collision': {'violations': [], 'preservations': []}
    }

    # Run-2-specific: Collision tracking
    collision_survival_data = []  # Steps survived after first collision per episode
    collision_halt_indices = []   # Step index where halt occurred on collision step

    episode_results = []

    for episode in range(num_episodes):
        print(f"\n  Episode {episode + 1}/{num_episodes}")

        # Create fresh environment and state
        env = CommitmentTrapV100(max_steps=steps_per_episode, seed=seed + episode)
        state = NormativeStateV110()

        # Create LLM v2 generator (with explicit consequence reasoning)
        try:
            generator = LLMGeneratorV2(state)
        except Exception as e:
            print(f"    ERROR: Failed to initialize LLM v2 generator: {e}")
            return {"error": str(e)}

        # Create agent with LLM v2 generator
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
        steps_completed = 0
        halted = False
        halt_reason = None

        # Collision tracking for this episode
        first_collision_step = None
        halt_was_on_collision = False
        halt_collision_index = None

        for step in range(steps_per_episode):
            # Get pre-step diagnostics
            A_pre = list(env.feasible_actions())
            apcm = env.get_apcm()

            # Detect collision (Run-2-specific tracking)
            exists_clean = any(
                len(apcm.get(a, {}).get("violates", set())) == 0
                for a in A_pre
            )
            is_collision_step = not exists_clean

            # Track first collision occurrence
            if is_collision_step and first_collision_step is None:
                first_collision_step = step

            # Execute agent step
            try:
                result = agent.step()
            except ValueError as e:
                # LLM generator failed after all attempts
                print(f"    Step {step + 1}: Generator failed - {e}")
                halted = True
                halt_reason = f"Generator failure: {e}"
                episode_schema_failures += 1

                # Track if halt was on collision step
                if is_collision_step:
                    halt_was_on_collision = True
                    halt_collision_index = step
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

                # Add Run-2-specific fields to telemetry
                llm_attempts = getattr(generator, '_last_attempts', 1)
                run2_telemetry = {
                    "generator_type": "LLM_v2",
                    "llm_model": os.getenv('LLM_MODEL'),
                    "llm_attempts_used": llm_attempts,
                    "is_collision_step": is_collision_step,
                    "collision_step_index": step if is_collision_step else None,
                    "first_collision_step": first_collision_step
                }

                # Add audit failure code if present
                if result.compilation_result and not result.compilation_result.success:
                    if hasattr(result.compilation_result, 'errors') and result.compilation_result.errors:
                        error_codes = [e.code if hasattr(e, 'code') else str(e) for e in result.compilation_result.errors]
                        run2_telemetry["audit_fail_codes"] = error_codes
                        run2_telemetry["audit_failure_on_collision_step"] = is_collision_step

                # Collect Jaccard metrics (all steps)
                if step_telemetry:
                    for field in ['forbidden', 'allowed', 'violations', 'preservations']:
                        key = f'jaccard_{field}'
                        if key in step_telemetry:
                            jaccard_metrics[field].append(step_telemetry[key])

                    # Collect Jaccard by step type (Run-2-specific)
                    step_type = 'collision' if is_collision_step else 'clean'
                    if 'jaccard_violations' in step_telemetry:
                        jaccard_by_type[step_type]['violations'].append(step_telemetry['jaccard_violations'])
                    if 'jaccard_preservations' in step_telemetry:
                        jaccard_by_type[step_type]['preservations'].append(step_telemetry['jaccard_preservations'])

                    # Add V_actual Jaccard for collision step tracking
                    if is_collision_step:
                        run2_telemetry["V_actual_jaccard_on_collision"] = step_telemetry.get('jaccard_violations', 0)

                # Write Run-2-specific telemetry
                with open(telemetry_path, 'a') as f:
                    f.write(json.dumps(run2_telemetry) + '\n')

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
            # Run-2-specific
            "first_collision_step": first_collision_step,
            "steps_after_first_collision": steps_after_first_collision,
            "halt_was_on_collision": halt_was_on_collision,
            "halt_collision_index": halt_collision_index
        })

        status = "HALTED" if halted else "COMPLETE"
        print(f"    {status}: {steps_completed} steps, {episode_violations} violations, "
              f"{episode_audit_failures} audit failures, {episode_llm_attempts} LLM attempts")
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

    # Compute Jaccard by step type (Run-2-specific)
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

    # Compute summary
    summary = {
        "condition": condition_name,
        "timestamp": datetime.now().isoformat(),
        "run_version": "Run 2",
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
        # Run-2-specific metrics
        "jaccard_by_step_type": jaccard_by_type_summary,
        "collision_survival": collision_survival_stats,
        "collision_halt_distribution": collision_halt_distribution,
        "episodes": episode_results
    }

    # Save summary
    summary_path = telemetry_path.parent / f"run_2_{condition_name.lower().replace(' ', '_')}_summary.json"
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


def compare_with_run1(run2_summary: Dict) -> Dict:
    """Load Run 1 results and compute deltas"""

    run1_path = Path(__file__).parent / "telemetry" / "run_1_mvra_v1.1_llm_summary.json"

    if not run1_path.exists():
        return {"error": "Run 1 results not found"}

    with open(run1_path) as f:
        run1_summary = json.load(f)

    # Compute deltas
    deltas = {
        "median_survival": {
            "run1": 4.0,  # From Run 1 report
            "run2": run2_summary.get('survival_statistics', {}).get('median', 0),
            "delta": run2_summary.get('survival_statistics', {}).get('median', 0) - 4.0
        },
        "mean_survival": {
            "run1": 5.0,  # From Run 1 report
            "run2": run2_summary.get('survival_statistics', {}).get('mean', 0),
            "delta": run2_summary.get('survival_statistics', {}).get('mean', 0) - 5.0
        }
    }

    # V_actual Jaccard comparison (collision steps)
    run1_v_jaccard_collision = 0.000  # From Run 1 report
    run2_v_jaccard_collision = run2_summary.get('jaccard_by_step_type', {}).get('collision', {}).get('violations', {}).get('mean', 0)

    deltas["V_actual_jaccard_collision"] = {
        "run1": run1_v_jaccard_collision,
        "run2": run2_v_jaccard_collision,
        "delta": run2_v_jaccard_collision - run1_v_jaccard_collision
    }

    # Audit failure comparison
    run1_effect_mismatch = 3  # From Run 1 report
    run2_effect_mismatch = run2_summary.get('audit_failure_distribution', {}).get('E_EFFECT_MISMATCH', 0)

    deltas["E_EFFECT_MISMATCH"] = {
        "run1": run1_effect_mismatch,
        "run2": run2_effect_mismatch,
        "delta": run2_effect_mismatch - run1_effect_mismatch
    }

    return deltas


def main():
    """Execute Run 2 experiment"""

    print("="*60)
    print("RSA-PoC v1.1 Run 2: Explicit Consequence Reasoning Trial")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}\n")

    # Check environment variables
    check_env_variables()

    # Configuration (same as Run 1)
    NUM_EPISODES = 5
    STEPS_PER_EPISODE = 20
    SEED = 42

    results = {}

    # Run LLM v2 condition
    results['mvra_v11_llm_v2'] = run_llm_v2_condition(
        "MVRA v1.1 LLM v2",
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

    # Compare with Run 1
    run1_comparison = compare_with_run1(results['mvra_v11_llm_v2'])
    results['run1_comparison'] = run1_comparison

    # Overall summary
    print("\n" + "="*60)
    print("RUN 2 COMPLETE")
    print("="*60)

    if 'error' not in results['mvra_v11_llm_v2']:
        llm_result = results['mvra_v11_llm_v2']

        print("\nLLM v2 Generator Results:")
        print(f"  Episodes completed: {llm_result['totals']['episodes_completed']}/{NUM_EPISODES}")
        print(f"  Episodes halted: {llm_result['totals']['episodes_halted']}/{NUM_EPISODES}")
        print(f"  Total steps: {llm_result['totals']['total_steps']}")

        survival = llm_result['survival_statistics']
        print(f"  Survival: mean={survival['mean']:.1f}, median={survival['median']:.1f}, max={survival['max']}")

        print("\n  Audit Failure Distribution:")
        for error_type, count in llm_result['audit_failure_distribution'].items():
            if count > 0:
                print(f"    {error_type}: {count}")

        print("\n  V_actual Jaccard by Step Type:")
        for step_type, metrics in llm_result['jaccard_by_step_type'].items():
            if 'violations' in metrics:
                v = metrics['violations']
                print(f"    {step_type}: mean={v['mean']:.3f}, median={v['median']:.3f}")

    print("\nScrambled Control:")
    scrambled = results['scrambled_control']
    print(f"  Episodes halted: {scrambled['episodes_halted']}/{NUM_EPISODES}")
    print(f"  {'✓ PASS' if scrambled['pass'] else '✗ FAIL'}: Spec integrity preserved")

    # Run 1 vs Run 2 comparison
    print("\n" + "-"*60)
    print("Run 1 vs Run 2 Comparison:")
    print("-"*60)

    if 'error' not in run1_comparison:
        for metric, data in run1_comparison.items():
            delta = data.get('delta', 0)
            direction = "↑" if delta > 0 else "↓" if delta < 0 else "="
            print(f"  {metric}:")
            print(f"    Run 1: {data.get('run1', 'N/A')}")
            print(f"    Run 2: {data.get('run2', 'N/A')}")
            print(f"    Delta: {delta:+.3f} {direction}")
    else:
        print(f"  {run1_comparison['error']}")

    # Acceptance criteria evaluation
    print("\n" + "-"*60)
    print("Run 2 Acceptance Criteria:")
    print("-"*60)

    acceptance = {
        "improved_v_actual": False,
        "longer_survival": False,
        "failure_mode_shift": False
    }

    if 'error' not in run1_comparison:
        # Check V_actual improvement
        v_delta = run1_comparison.get('V_actual_jaccard_collision', {}).get('delta', 0)
        if v_delta > 0:
            acceptance["improved_v_actual"] = True
            print(f"  ✓ V_actual Jaccard improved: +{v_delta:.3f}")
        else:
            print(f"  ✗ V_actual Jaccard not improved: {v_delta:.3f}")

        # Check survival improvement
        survival_delta = run1_comparison.get('median_survival', {}).get('delta', 0)
        if survival_delta > 0:
            acceptance["longer_survival"] = True
            print(f"  ✓ Median survival improved: +{survival_delta:.1f} steps")
        else:
            print(f"  ✗ Median survival not improved: {survival_delta:.1f} steps")

        # Check failure mode shift
        effect_delta = run1_comparison.get('E_EFFECT_MISMATCH', {}).get('delta', 0)
        if effect_delta < 0:
            acceptance["failure_mode_shift"] = True
            print(f"  ✓ Fewer E_EFFECT_MISMATCH: {effect_delta}")
        else:
            print(f"  ✗ E_EFFECT_MISMATCH not reduced: {effect_delta}")

    any_improvement = any(acceptance.values())

    print(f"\n{'='*60}")
    if any_improvement:
        print("✓ RUN 2 SHOWS IMPROVEMENT on at least one metric")
        print("  Explicit consequence reasoning has measurable effect")
    else:
        print("✗ RUN 2 SHOWS NO IMPROVEMENT")
        print("  Explicit reasoning insufficient for V_actual computation")
    print(f"{'='*60}")

    print(f"\nEnd time: {datetime.now().isoformat()}")

    # Save overall results
    results_path = Path(__file__).parent / "telemetry" / "run_2_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "run_metadata": {
                "timestamp": datetime.now().isoformat(),
                "run_version": "Run 2",
                "llm_config": {
                    "provider": os.getenv('LLM_PROVIDER'),
                    "model": os.getenv('LLM_MODEL')
                },
                "num_episodes": NUM_EPISODES,
                "steps_per_episode": STEPS_PER_EPISODE,
                "seed": SEED
            },
            "results": results,
            "run1_comparison": run1_comparison,
            "acceptance": acceptance,
            "any_improvement": any_improvement
        }, f, indent=2)

    print(f"\nOverall results: {results_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
