#!/usr/bin/env python3
"""v2.0 Experiment Runner

Runs the v2.0 Incentive Interference experiments:
1. v1.2 Baseline (no IIC)
2. R0 Noise Control (sovereign under noise)
3. Control Agent under R1/R2 (should show drift)
4. Sovereign Agent under R1/R2 (should NOT drift)

Usage:
    export LLM_PROVIDER=anthropic
    export LLM_MODEL=claude-sonnet-4-20250514
    export LLM_API_KEY=<your-key>
    python run_v200_experiments.py
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from rsa_poc.v200.runplans import (
    V200ExperimentHarness,
    V200RunConfig,
    run_v12_baseline,
    run_control_experiment,
    run_sovereign_experiment,
)
from rsa_poc.v200.runplans.harness_v200 import AgentType
from rsa_poc.v200.runplans.runplan_control import validate_control_drift
from rsa_poc.v200.runplans.runplan_sovereign import (
    analyze_sovereignty,
    compare_sovereign_to_control,
)


def main():
    """Run all v2.0 experiments."""
    print("=" * 70)
    print("RSA-PoC v2.0 Incentive Interference Experiments")
    print("=" * 70)
    print()

    # Check LLM configuration
    provider = os.getenv("LLM_PROVIDER")
    model = os.getenv("LLM_MODEL")
    api_key = os.getenv("LLM_API_KEY")

    if not all([provider, model, api_key]):
        print("ERROR: LLM environment variables not set.")
        print("Required: LLM_PROVIDER, LLM_MODEL, LLM_API_KEY")
        sys.exit(1)

    print(f"LLM Provider: {provider}")
    print(f"LLM Model: {model}")
    print()

    # Experiment parameters (reduced for initial run)
    NUM_EPISODES = 3
    STEPS_PER_EPISODE = 10
    RANDOM_SEED = 42

    print(f"Parameters: {NUM_EPISODES} episodes × {STEPS_PER_EPISODE} steps")
    print()

    results = {}

    # 1. v1.2 Baseline
    print("-" * 70)
    print("1. Running v1.2 Baseline (no IIC)...")
    print("-" * 70)
    try:
        baseline_result = run_v12_baseline(
            num_episodes=NUM_EPISODES,
            steps_per_episode=STEPS_PER_EPISODE,
            random_seed=RANDOM_SEED,
        )
        results["baseline"] = baseline_result.summary
        print(f"   Completed: {baseline_result.summary}")
    except Exception as e:
        print(f"   FAILED: {e}")
        results["baseline"] = {"error": str(e)}
    print()

    # 2. R0 Noise Control
    print("-" * 70)
    print("2. Running Sovereign under R0 (noise control)...")
    print("-" * 70)
    try:
        r0_result = run_sovereign_experiment(
            regime="R0",
            num_episodes=NUM_EPISODES,
            steps_per_episode=STEPS_PER_EPISODE,
            random_seed=RANDOM_SEED,
        )
        results["r0_noise"] = r0_result.summary
        print(f"   Completed: {r0_result.summary}")
    except Exception as e:
        print(f"   FAILED: {e}")
        results["r0_noise"] = {"error": str(e)}
    print()

    # 3. Control Agent under R1
    print("-" * 70)
    print("3. Running Control Agent under R1 (boundary pressure)...")
    print("-" * 70)
    try:
        control_r1_result = run_control_experiment(
            regime="R1",
            num_episodes=NUM_EPISODES,
            steps_per_episode=STEPS_PER_EPISODE,
            random_seed=RANDOM_SEED,
        )
        control_r1_validation = validate_control_drift(control_r1_result)
        results["control_r1"] = {
            "summary": control_r1_result.summary,
            "validation": control_r1_validation,
        }
        print(f"   Summary: {control_r1_result.summary}")
        print(f"   Drift validation: {control_r1_validation['message']}")
    except Exception as e:
        print(f"   FAILED: {e}")
        results["control_r1"] = {"error": str(e)}
    print()

    # 4. Control Agent under R2
    print("-" * 70)
    print("4. Running Control Agent under R2 (perverse friction)...")
    print("-" * 70)
    try:
        control_r2_result = run_control_experiment(
            regime="R2",
            num_episodes=NUM_EPISODES,
            steps_per_episode=STEPS_PER_EPISODE,
            random_seed=RANDOM_SEED + 1000,
        )
        control_r2_validation = validate_control_drift(control_r2_result)
        results["control_r2"] = {
            "summary": control_r2_result.summary,
            "validation": control_r2_validation,
        }
        print(f"   Summary: {control_r2_result.summary}")
        print(f"   Drift validation: {control_r2_validation['message']}")
    except Exception as e:
        print(f"   FAILED: {e}")
        results["control_r2"] = {"error": str(e)}
    print()

    # 5. Sovereign Agent under R1
    print("-" * 70)
    print("5. Running Sovereign Agent under R1 (boundary pressure)...")
    print("-" * 70)
    try:
        sovereign_r1_result = run_sovereign_experiment(
            regime="R1",
            num_episodes=NUM_EPISODES,
            steps_per_episode=STEPS_PER_EPISODE,
            random_seed=RANDOM_SEED,
        )
        sovereign_r1_analysis = analyze_sovereignty(sovereign_r1_result)
        results["sovereign_r1"] = {
            "summary": sovereign_r1_result.summary,
            "analysis": sovereign_r1_analysis,
        }
        print(f"   Summary: {sovereign_r1_result.summary}")
        print(f"   Sovereignty analysis: {sovereign_r1_analysis}")
    except Exception as e:
        print(f"   FAILED: {e}")
        results["sovereign_r1"] = {"error": str(e)}
    print()

    # 6. Sovereign Agent under R2
    print("-" * 70)
    print("6. Running Sovereign Agent under R2 (perverse friction)...")
    print("-" * 70)
    try:
        sovereign_r2_result = run_sovereign_experiment(
            regime="R2",
            num_episodes=NUM_EPISODES,
            steps_per_episode=STEPS_PER_EPISODE,
            random_seed=RANDOM_SEED + 1000,
        )
        sovereign_r2_analysis = analyze_sovereignty(sovereign_r2_result)
        results["sovereign_r2"] = {
            "summary": sovereign_r2_result.summary,
            "analysis": sovereign_r2_analysis,
        }
        print(f"   Summary: {sovereign_r2_result.summary}")
        print(f"   Sovereignty analysis: {sovereign_r2_analysis}")
    except Exception as e:
        print(f"   FAILED: {e}")
        results["sovereign_r2"] = {"error": str(e)}
    print()

    # Compare sovereign vs control
    print("=" * 70)
    print("COMPARISON: Sovereign vs Control")
    print("=" * 70)

    if "control_r1" in results and "sovereign_r1" in results:
        if "error" not in results["control_r1"] and "error" not in results["sovereign_r1"]:
            comparison = compare_sovereign_to_control(
                sovereign_r1_result,
                control_r1_result,
            )
            results["comparison_r1"] = comparison
            print(f"R1 Comparison:")
            print(f"   Experiment valid: {comparison['experiment_valid']}")
            print(f"   Sovereign stable: {comparison['sovereign_stable']}")
            print(f"   Control drifted: {comparison['control_drifted']}")
            print(f"   Interpretation: {comparison['interpretation']}")
    print()

    # Save results
    output_file = f"v200_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {output_file}")

    print()
    print("=" * 70)
    print("v2.0 Experiments Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
