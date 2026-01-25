"""Run 1: RSA-PoC v1.1 LLM Generator Experiment

Tests whether an LLM-based generator can satisfy v1.1 audit constraints.

Single Condition:
- MVRA v1.1 LLM: Full audit pipeline with LLM-generated predictions

Pass Criteria:
- Audit failures are deterministic and attributable
- Telemetry distinguishes near-miss vs hallucination
- Scrambled control still halts (spec integrity preserved)

This is a falsification experiment, not a benchmark. Failure is expected and informative.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v110.state.normative import NormativeStateV110
from rsa_poc.v110.generator.llm import LLMGeneratorV110
from rsa_poc.v110.generator.deterministic import DeterministicGeneratorV110
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
        print("  export LLM_MODEL=claude-3-5-sonnet-20241022")
        print("  export LLM_API_KEY=<your-key>")
        print("\nOr for OpenAI:")
        print("  export LLM_PROVIDER=openai")
        print("  export LLM_MODEL=gpt-4")
        print("  export LLM_API_KEY=<your-key>")
        sys.exit(1)

    print("LLM Configuration:")
    print(f"  Provider: {os.getenv('LLM_PROVIDER')}")
    print(f"  Model: {os.getenv('LLM_MODEL')}")
    print(f"  API Key: {'***' + os.getenv('LLM_API_KEY', '')[-4:] if os.getenv('LLM_API_KEY') else 'Not set'}")
    if os.getenv('LLM_BASE_URL'):
        print(f"  Base URL: {os.getenv('LLM_BASE_URL')}")
    print()


def run_llm_condition(
    condition_name: str,
    num_episodes: int = 3,
    steps_per_episode: int = 10,
    seed: int = 42
) -> Dict:
    """
    Run MVRA v1.1 with LLM generator.

    Returns summary statistics including LLM-specific metrics.
    """
    print(f"\n{'='*60}")
    print(f"Condition: {condition_name}")
    print(f"{'='*60}")

    # Initialize telemetry
    telemetry_path = Path(__file__).parent / "telemetry" / f"run_1_{condition_name.lower().replace(' ', '_')}.jsonl"
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
        'other': 0
    }

    # Jaccard metrics aggregation
    jaccard_metrics = {
        'forbidden': [],
        'allowed': [],
        'violations': [],
        'preservations': []
    }

    episode_results = []

    for episode in range(num_episodes):
        print(f"\n  Episode {episode + 1}/{num_episodes}")

        # Create fresh environment and state
        env = CommitmentTrapV100(max_steps=steps_per_episode, seed=seed + episode)
        state = NormativeStateV110()

        # Create LLM generator
        try:
            generator = LLMGeneratorV110(state)
        except Exception as e:
            print(f"    ERROR: Failed to initialize LLM generator: {e}")
            return {"error": str(e)}

        # Create agent with LLM generator
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

        for step in range(steps_per_episode):
            # Get pre-step diagnostics
            A_pre = set(env.feasible_actions())
            apcm = env.get_apcm()

            # Detect collision
            exists_clean = any(
                len(apcm.get(a, {}).get("violates", set())) == 0
                for a in A_pre
            )
            collision = not exists_clean

            # Execute agent step
            try:
                result = agent.step()
            except ValueError as e:
                # LLM generator failed after all attempts
                print(f"    Step {step}: Generator failed - {e}")
                halted = True
                halt_reason = f"Generator failure: {e}"
                episode_schema_failures += 1
                break

            # Track LLM attempts from generator
            if hasattr(agent, 'generator') and hasattr(agent.generator, '_last_attempts'):
                episode_llm_attempts += agent.generator._last_attempts

            # Log step telemetry with LLM-specific fields
            if result.jaf:
                step_telemetry = logger.log_step(
                    step_result=result,
                    feasible_actions=env.feasible_actions(),
                    apcm=env.get_apcm(),
                    agent_id=agent.__class__.__name__
                )

                # Add LLM-specific metrics to telemetry
                llm_attempts = getattr(agent.generator, '_last_attempts', 1) if hasattr(agent, 'generator') else 1
                llm_telemetry = {
                    "generator_type": "LLM",
                    "llm_model": os.getenv('LLM_MODEL'),
                    "llm_attempts_used": llm_attempts,
                    "collision_detected": collision
                }

                # Add audit failure code if present
                if result.compilation_result and not result.compilation_result.success:
                    if hasattr(result.compilation_result, 'errors') and result.compilation_result.errors:
                        error_codes = [e.code if hasattr(e, 'code') else str(e) for e in result.compilation_result.errors]
                        llm_telemetry["audit_fail_codes"] = error_codes

                # Collect Jaccard metrics for analysis
                if step_telemetry:
                    if 'jaccard_forbidden' in step_telemetry:
                        jaccard_metrics['forbidden'].append(step_telemetry['jaccard_forbidden'])
                    if 'jaccard_allowed' in step_telemetry:
                        jaccard_metrics['allowed'].append(step_telemetry['jaccard_allowed'])
                    if 'jaccard_violations' in step_telemetry:
                        jaccard_metrics['violations'].append(step_telemetry['jaccard_violations'])
                    if 'jaccard_preservations' in step_telemetry:
                        jaccard_metrics['preservations'].append(step_telemetry['jaccard_preservations'])

                # Write LLM-specific telemetry
                with open(telemetry_path, 'a') as f:
                    f.write(json.dumps(llm_telemetry) + '\n')

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
                        elif error_code in ['E_PREDICTION_ERROR', 'E_AUDIT_VIOLATION']:
                            audit_failure_types['other'] += 1
                            episode_audit_failures += 1

            # Check for halt
            if result.halted or result.done:
                halted = True

                # Determine halt reason
                if hasattr(result, 'generation_result') and result.generation_result.error_type:
                    halt_reason = f"Generator {result.generation_result.error_type} failure"
                elif result.compilation_result and not result.compilation_result.success:
                    error_codes = [e.code if hasattr(e, 'code') else str(e)
                                   for e in result.compilation_result.errors]
                    halt_reason = f"Audit failure: {', '.join(error_codes)}"
                elif result.done:
                    halt_reason = "Episode complete"
                else:
                    halt_reason = result.halt_reason if hasattr(result, 'halt_reason') else "Unknown"

                break

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
            "llm_attempts": episode_llm_attempts
        })

        status = "HALTED" if halted else "COMPLETE"
        print(f"    {status}: {steps_completed} steps, {episode_violations} violations, "
              f"{episode_audit_failures} audit failures, {episode_llm_attempts} LLM attempts")
        if halted:
            print(f"    Halt reason: {halt_reason}")

    # Compute Jaccard averages
    jaccard_averages = {}
    for field, values in jaccard_metrics.items():
        if values:
            jaccard_averages[field] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }

    # Compute summary
    summary = {
        "condition": condition_name,
        "timestamp": datetime.now().isoformat(),
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
        "audit_failure_distribution": audit_failure_types,
        "jaccard_averages": jaccard_averages,
        "episodes": episode_results
    }

    # Save summary
    summary_path = telemetry_path.parent / f"run_1_{condition_name.lower().replace(' ', '_')}_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Summary:")
    print(f"    Episodes completed: {episodes_completed}/{num_episodes}")
    print(f"    Episodes halted: {episodes_halted}/{num_episodes}")
    print(f"    Total steps: {total_steps}")
    print(f"    Total violations: {total_violations}")
    print(f"    Total audit failures: {total_audit_failures}")
    print(f"    Total schema failures: {total_schema_failures}")
    print(f"    Total LLM attempts: {total_llm_attempts}")
    print(f"    Avg LLM attempts/step: {total_llm_attempts / total_steps if total_steps > 0 else 0:.2f}")

    if audit_failure_types:
        print(f"    Audit failure types:")
        for error_type, count in audit_failure_types.items():
            if count > 0:
                print(f"      {error_type}: {count}")

    if jaccard_averages:
        print(f"    Jaccard averages:")
        for field, stats in jaccard_averages.items():
            print(f"      {field}: mean={stats['mean']:.3f}, range=[{stats['min']:.3f}, {stats['max']:.3f}]")

    print(f"    Telemetry: {telemetry_path}")
    print(f"    Summary: {summary_path}")

    return summary


def run_scrambled_control(
    num_episodes: int = 3,
    steps_per_episode: int = 10,
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


def main():
    """Execute Run 1 experiment"""

    print("="*60)
    print("RSA-PoC v1.1 Run 1: LLM Generator Experiment")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}\n")

    # Check environment variables
    check_env_variables()

    # Configuration
    NUM_EPISODES = 5
    STEPS_PER_EPISODE = 20
    SEED = 42

    results = {}

    # Run LLM condition
    results['mvra_v11_llm'] = run_llm_condition(
        "MVRA v1.1 LLM",
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

    # Overall summary
    print("\n" + "="*60)
    print("RUN 1 COMPLETE")
    print("="*60)

    if 'error' not in results['mvra_v11_llm']:
        llm_result = results['mvra_v11_llm']

        print("\nLLM Generator Results:")
        print(f"  Episodes completed: {llm_result['totals']['episodes_completed']}/{NUM_EPISODES}")
        print(f"  Episodes halted: {llm_result['totals']['episodes_halted']}/{NUM_EPISODES}")
        print(f"  Total steps before halt: {llm_result['totals']['total_steps']}")
        print(f"  Audit failures: {llm_result['totals']['total_audit_failures']}")
        print(f"  Schema failures: {llm_result['totals']['total_schema_failures']}")

        print("\n  Audit Failure Distribution:")
        for error_type, count in llm_result['audit_failure_distribution'].items():
            if count > 0:
                print(f"    {error_type}: {count}")

        print("\n  Prediction Accuracy (Jaccard):")
        for field, stats in llm_result['jaccard_averages'].items():
            print(f"    {field}: {stats['mean']:.3f} (range: [{stats['min']:.3f}, {stats['max']:.3f}])")

        # Survival analysis
        survival_steps = [ep['steps_completed'] for ep in llm_result['episodes']]
        print(f"\n  Survival curve: {survival_steps}")
        print(f"  Median survival: {sorted(survival_steps)[NUM_EPISODES // 2]} steps")

    print("\nScrambled Control:")
    scrambled = results['scrambled_control']
    print(f"  Episodes halted: {scrambled['episodes_halted']}/{NUM_EPISODES}")
    print(f"  {'✓ PASS' if scrambled['pass'] else '✗ FAIL'}: Spec integrity preserved")

    print("\nAcceptance Criteria:")
    print("  1. Audit failures are deterministic and attributable")
    print("  2. Scrambled control still halts (spec integrity)")
    print("  3. Telemetry distinguishes near-miss vs hallucination")

    criteria_met = (
        'error' not in results['mvra_v11_llm'] and
        scrambled['pass'] and
        len(llm_result['jaccard_averages']) > 0
    )

    print(f"\n{'='*60}")
    if criteria_met:
        print("✓ RUN 1 ACCEPTANCE: Experiment executed successfully")
        print("  (Note: High failure rates are expected and informative)")
    else:
        print("✗ RUN 1 INCOMPLETE: Check errors above")
    print(f"{'='*60}")

    print(f"\nEnd time: {datetime.now().isoformat()}")

    # Save overall results
    results_path = Path(__file__).parent / "telemetry" / "run_1_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "run_metadata": {
                "timestamp": datetime.now().isoformat(),
                "llm_config": {
                    "provider": os.getenv('LLM_PROVIDER'),
                    "model": os.getenv('LLM_MODEL')
                },
                "num_episodes": NUM_EPISODES,
                "steps_per_episode": STEPS_PER_EPISODE,
                "seed": SEED
            },
            "results": results,
            "acceptance_criteria_met": criteria_met
        }, f, indent=2)

    print(f"\nOverall results: {results_path}")

    return 0 if criteria_met else 1


if __name__ == "__main__":
    sys.exit(main())
