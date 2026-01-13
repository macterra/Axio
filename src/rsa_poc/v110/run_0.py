"""Run 0: RSA-PoC v1.1 Baseline Experiment

4-Condition Comparison:
1. MVRA v1.1: Full audit pipeline with deterministic predictions
2. ASB: v1.0 baseline (no audits, no predictions)
3. Scrambled: Corrupted predictions to test audit sensitivity
4. Bypass: Audit-free v1.1 (predictions present but not enforced)

Pass Criteria:
- MVRA v1.1: Completes run without audit failures
- ASB: Matches v1.0 baseline behavior
- Scrambled: Halts on audit failures (proves audits are load-bearing)
- Bypass: Similar to ASB but with predictions present
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v110.state.normative import NormativeStateV110
from rsa_poc.v110.generator.deterministic import DeterministicGeneratorV110
from rsa_poc.v110.selector.blind import BlindActionSelectorV110
from rsa_poc.v110.agent import MVRAAgentV110
from rsa_poc.v110.ablations import (
    ASBAgentV110,
    MVRAScrambledAgentV110,
    MVRABypassAgentV110
)
from rsa_poc.v110.telemetry.logger import TelemetryLoggerV110


def run_condition(
    condition_name: str,
    agent_class,
    num_episodes: int = 3,
    steps_per_episode: int = 10,
    seed: int = 42
) -> Dict:
    """
    Run a single experimental condition.

    Returns summary statistics.
    """
    print(f"\n{'='*60}")
    print(f"Condition: {condition_name}")
    print(f"{'='*60}")

    # Initialize telemetry
    telemetry_path = Path(__file__).parent / "telemetry" / f"run_0_{condition_name.lower().replace(' ', '_')}.jsonl"
    telemetry_path.parent.mkdir(exist_ok=True, parents=True)
    logger = TelemetryLoggerV110(telemetry_path)

    # Episode-level statistics
    episodes_completed = 0
    episodes_halted = 0
    total_steps = 0
    total_violations = 0
    total_audit_failures = 0
    total_v100_compilation_failures = 0

    episode_results = []

    for episode in range(num_episodes):
        print(f"\n  Episode {episode + 1}/{num_episodes}")

        # Create fresh environment and state
        env = CommitmentTrapV100(max_steps=steps_per_episode, seed=seed + episode)
        state = NormativeStateV110()

        # Create agent
        if agent_class == ASBAgentV110:
            agent = agent_class(
                env=env
            )
        elif agent_class == MVRAAgentV110:
            agent = agent_class(
                env=env,
                normative_state=state,
                generator=DeterministicGeneratorV110(state),
                selector=BlindActionSelectorV110(seed=seed + episode)
            )
        elif agent_class == MVRAScrambledAgentV110:
            agent = agent_class(
                env=env,
                normative_state=state,
                seed=seed + episode
            )
        elif agent_class == MVRABypassAgentV110:
            agent = agent_class(
                env=env,
                normative_state=state
            )
        else:
            raise ValueError(f"Unknown agent class: {agent_class}")

        # Run episode
        agent.reset()

        episode_violations = 0
        episode_audit_failures = 0
        episode_v100_failures = 0
        steps_completed = 0
        halted = False
        halt_reason = None

        for step in range(steps_per_episode):
            # === v1.1 FIX 2: FORCED DIAGNOSTIC INSTRUMENTATION ===
            # Hard assertion block to validate collision semantics

            # 1. Get pre-mask feasible actions
            A_pre = set(env.feasible_actions())

            # 2. Get APCM for all feasible actions
            apcm = env.get_apcm()

            # 3. Compute: exists_clean = any action with empty violates set
            exists_clean = any(
                len(apcm.get(a, {}).get("violates", set())) == 0
                for a in A_pre
            )

            # 4. Determine collision using v1.0 definition
            # Collision = no action violates nothing (i.e., every action violates something)
            collision = not exists_clean

            # 5. Assert collision matches environment claim (if env provides this flag)
            if hasattr(env, 'is_collision_step'):
                env_collision = env.is_collision_step()
                assert collision == env_collision, \
                    f"Step {step}: Collision mismatch: computed={collision}, env={env_collision}"

            # Execute agent step
            result = agent.step()

            # 6. After action is chosen, validate collision semantics
            if result.selected_action and collision:
                selected_violates = apcm.get(result.selected_action, {}).get("violates", set())
                assert len(selected_violates) >= 1, \
                    f"Step {step}: Collision step but selected action '{result.selected_action}' has no violations. APCM: {apcm.get(result.selected_action)}"

                # Log diagnostic info
                if step == 0:  # Log first step details
                    print(f"    [DIAG] Step {step}: collision={collision}, selected={result.selected_action}, violates={selected_violates}")

            # Log step telemetry
            if result.jaf:
                logger.log_step(
                    step_result=result,
                    feasible_actions=env.feasible_actions(),
                    apcm=env.get_apcm(),
                    agent_id=agent.__class__.__name__
                )

            steps_completed += 1
            total_steps += 1

            # Track violations (from environment feedback)
            # Environment reports as 'violated_prefs', not 'violations'
            if hasattr(result, 'info') and 'violated_prefs' in result.info:
                episode_violations += len(result.info['violated_prefs'])

            # Track compilation failures
            if result.compilation_result and not result.compilation_result.success:
                if hasattr(result.compilation_result, 'errors'):
                    for error in result.compilation_result.errors:
                        error_code = error.code if hasattr(error, 'code') else error
                        if error_code in ['E_PREDICTION_ERROR', 'E_AUDIT_VIOLATION']:
                            episode_audit_failures += 1
                        else:
                            episode_v100_failures += 1

            # Check for halt
            if result.halted or result.done:
                halted = True
                halt_reason = result.halt_reason if hasattr(result, 'halt_reason') else "Episode complete"
                break

        # Update totals
        total_violations += episode_violations
        total_audit_failures += episode_audit_failures
        total_v100_compilation_failures += episode_v100_failures

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
            "v100_failures": episode_v100_failures
        })

        status = "HALTED" if halted else "COMPLETE"
        print(f"    {status}: {steps_completed} steps, {episode_violations} violations, "
              f"{episode_audit_failures} audit failures")

    # Compute summary
    summary = {
        "condition": condition_name,
        "timestamp": datetime.now().isoformat(),
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
            "total_v100_failures": total_v100_compilation_failures
        },
        "averages": {
            "steps_per_episode": total_steps / num_episodes,
            "violations_per_episode": total_violations / num_episodes,
            "audit_failures_per_episode": total_audit_failures / num_episodes
        },
        "episodes": episode_results
    }

    # Save summary
    summary_path = telemetry_path.parent / f"run_0_{condition_name.lower().replace(' ', '_')}_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Summary:")
    print(f"    Episodes completed: {episodes_completed}/{num_episodes}")
    print(f"    Episodes halted: {episodes_halted}/{num_episodes}")
    print(f"    Total steps: {total_steps}")
    print(f"    Total violations: {total_violations}")
    print(f"    Total audit failures: {total_audit_failures}")
    print(f"    Avg steps/episode: {total_steps / num_episodes:.1f}")
    print(f"    Telemetry: {telemetry_path}")
    print(f"    Summary: {summary_path}")

    return summary


def main():
    """Execute Run 0 experiment"""

    print("="*60)
    print("RSA-PoC v1.1 Run 0: Justification Audit Tightening")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}")

    # Configuration
    NUM_EPISODES = 5
    STEPS_PER_EPISODE = 20
    SEED = 42

    results = {}

    # Condition 1: MVRA v1.1 (Full audit pipeline)
    results['mvra_v11'] = run_condition(
        "MVRA v1.1",
        MVRAAgentV110,
        num_episodes=NUM_EPISODES,
        steps_per_episode=STEPS_PER_EPISODE,
        seed=SEED
    )

    # Condition 2: ASB (v1.0 baseline)
    results['asb'] = run_condition(
        "ASB Baseline",
        ASBAgentV110,
        num_episodes=NUM_EPISODES,
        steps_per_episode=STEPS_PER_EPISODE,
        seed=SEED
    )

    # Condition 3: Scrambled Predictions
    results['scrambled'] = run_condition(
        "Scrambled Predictions",
        MVRAScrambledAgentV110,
        num_episodes=NUM_EPISODES,
        steps_per_episode=STEPS_PER_EPISODE,
        seed=SEED
    )

    # Condition 4: Bypass Audit
    results['bypass'] = run_condition(
        "Bypass Audit",
        MVRABypassAgentV110,
        num_episodes=NUM_EPISODES,
        steps_per_episode=STEPS_PER_EPISODE,
        seed=SEED
    )

    # Overall summary
    print("\n" + "="*60)
    print("RUN 0 COMPLETE")
    print("="*60)

    print("\nComparative Summary:")
    print(f"{'Condition':<25} {'Completed':<12} {'Halted':<10} {'Steps':<8} {'Violations':<12} {'Audit Fails'}")
    print("-" * 80)

    for key, result in results.items():
        totals = result['totals']
        print(f"{result['condition']:<25} "
              f"{totals['episodes_completed']}/{NUM_EPISODES:<11} "
              f"{totals['episodes_halted']:<10} "
              f"{totals['total_steps']:<8} "
              f"{totals['total_violations']:<12} "
              f"{totals['total_audit_failures']}")

    print("\nPass Criteria Validation:")

    # MVRA v1.1: Should complete without audit failures
    mvra_pass = (results['mvra_v11']['totals']['total_audit_failures'] == 0 and
                 results['mvra_v11']['totals']['episodes_halted'] == 0)
    print(f"  ✓ MVRA v1.1: No audit failures" if mvra_pass else "  ✗ MVRA v1.1: Had audit failures")

    # ASB: Should match v1.0 behavior (no audits)
    asb_pass = results['asb']['totals']['total_audit_failures'] == 0
    print(f"  ✓ ASB: No audit failures (v1.0 compatible)" if asb_pass else "  ✗ ASB: Unexpected behavior")

    # Scrambled: Should halt on audit failures
    scrambled_pass = results['scrambled']['totals']['episodes_halted'] > 0
    print(f"  ✓ Scrambled: Halted {results['scrambled']['totals']['episodes_halted']} episodes (audits working)"
          if scrambled_pass else "  ✗ Scrambled: Did not halt (audits not enforced)")

    # Bypass: Should complete without audit failures
    bypass_pass = (results['bypass']['totals']['total_audit_failures'] == 0 and
                   results['bypass']['totals']['episodes_halted'] == 0)
    print(f"  ✓ Bypass: No audit failures (bypass working)" if bypass_pass else "  ✗ Bypass: Had failures")

    # Overall pass
    overall_pass = mvra_pass and asb_pass and scrambled_pass and bypass_pass

    print(f"\n{'='*60}")
    if overall_pass:
        print("✓ RUN 0 PASSED: All conditions met criteria")
    else:
        print("✗ RUN 0 FAILED: Some conditions did not meet criteria")
    print(f"{'='*60}")

    print(f"\nEnd time: {datetime.now().isoformat()}")

    # Save overall results
    results_path = Path(__file__).parent / "telemetry" / "run_0_results.json"
    with open(results_path, 'w') as f:
        json.dump({
            "run_metadata": {
                "timestamp": datetime.now().isoformat(),
                "num_episodes": NUM_EPISODES,
                "steps_per_episode": STEPS_PER_EPISODE,
                "seed": SEED
            },
            "conditions": results,
            "pass_criteria": {
                "mvra_v11": mvra_pass,
                "asb": asb_pass,
                "scrambled": scrambled_pass,
                "bypass": bypass_pass,
                "overall": overall_pass
            }
        }, f, indent=2)

    print(f"\nOverall results: {results_path}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
