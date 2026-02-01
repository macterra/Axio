#!/usr/bin/env python3
"""
AKR-0 Main Runner

Executes all 15 runs (3 conditions x 5 seeds) and verifies replay.
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from aie import Condition
from harness import ExecutionHarness, HarnessConfig
from logger import verify_run


# Preregistered configuration
SEEDS = [11, 22, 33, 44, 55]
CONDITIONS = [Condition.A, Condition.B, Condition.C]


def run_experiment(output_dir: str = "results") -> dict:
    """
    Run the full AKR-0 experiment.

    Returns:
        Summary dict with all results
    """
    os.makedirs(output_dir, exist_ok=True)
    logs_dir = os.path.join(output_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    experiment_start = datetime.now().isoformat()

    results = {
        "experiment": "AKR-0 v0.1",
        "start_time": experiment_start,
        "conditions": {},
        "runs": [],
        "replay_verification": [],
        "summary": {
            "total_runs": 0,
            "passed_runs": 0,
            "failed_runs": 0,
            "replay_verified": 0,
            "replay_failed": 0,
        },
    }

    # Run all conditions
    for condition in CONDITIONS:
        condition_results = {
            "condition": condition.value,
            "seeds": [],
            "total_actions_executed": 0,
            "total_actions_refused": 0,
            "total_conflicts": 0,
            "total_transformations": 0,
            "deadlocks": [],
            "failures": [],
        }

        for seed in SEEDS:
            print(f"\n{'='*60}")
            print(f"Running Condition {condition.value}, Seed {seed}")
            print(f"{'='*60}")

            run_start = time.time()

            config = HarnessConfig(
                condition=condition,
                seed=seed,
                output_dir=logs_dir,
            )

            harness = ExecutionHarness(config)
            run_result = harness.run()

            run_elapsed = time.time() - run_start
            run_result["elapsed_seconds"] = run_elapsed

            print(f"\nRun completed in {run_elapsed:.2f}s")
            print(f"  Epochs: {run_result['epochs']}")
            print(f"  Events: {run_result['total_events']}")
            print(f"  Actions executed: {run_result['actions_executed']}")
            print(f"  Actions refused: {run_result['actions_refused']}")
            print(f"  Conflicts: {run_result['conflicts_registered']}")
            print(f"  Transformations: {run_result['transformations']}")

            if run_result.get("deadlock"):
                print(f"  DEADLOCK: {run_result['deadlock']}")
                condition_results["deadlocks"].append({
                    "seed": seed,
                    "type": run_result["deadlock"],
                })

            if run_result.get("failure"):
                print(f"  FAILURE: {run_result['failure']}")
                condition_results["failures"].append({
                    "seed": seed,
                    "type": run_result["failure"],
                })
                results["summary"]["failed_runs"] += 1
            else:
                results["summary"]["passed_runs"] += 1

            print(f"  Final state hash: {run_result['final_state_hash'][:16]}...")

            condition_results["seeds"].append(seed)
            condition_results["total_actions_executed"] += run_result["actions_executed"]
            condition_results["total_actions_refused"] += run_result["actions_refused"]
            condition_results["total_conflicts"] += run_result["conflicts_registered"]
            condition_results["total_transformations"] += run_result["transformations"]

            results["runs"].append(run_result)
            results["summary"]["total_runs"] += 1

        results["conditions"][condition.value] = condition_results

    # Verify replay for all runs
    print(f"\n{'='*60}")
    print("Verifying Replay Determinism")
    print(f"{'='*60}")

    for condition in CONDITIONS:
        for seed in SEEDS:
            run_id = f"{condition.value}_{seed}"
            print(f"\nVerifying {run_id}...")

            try:
                success, divergence = verify_run(run_id, logs_dir)

                if success:
                    print(f"  ✓ Replay verified")
                    results["summary"]["replay_verified"] += 1
                    results["replay_verification"].append({
                        "run_id": run_id,
                        "success": True,
                    })
                else:
                    print(f"  ✗ Replay FAILED at event {divergence.divergence_event_index}")
                    print(f"    Expected state: {divergence.expected_state_hash[:16]}...")
                    print(f"    Observed state: {divergence.observed_state_hash[:16]}...")
                    results["summary"]["replay_failed"] += 1
                    results["replay_verification"].append({
                        "run_id": run_id,
                        "success": False,
                        "divergence": {
                            "event_index": divergence.divergence_event_index,
                            "expected_state": divergence.expected_state_hash,
                            "observed_state": divergence.observed_state_hash,
                        },
                    })

            except Exception as e:
                print(f"  ✗ Verification error: {e}")
                results["summary"]["replay_failed"] += 1
                results["replay_verification"].append({
                    "run_id": run_id,
                    "success": False,
                    "error": str(e),
                })

    # Finalize
    experiment_end = datetime.now().isoformat()
    results["end_time"] = experiment_end

    # Determine overall result
    if (results["summary"]["failed_runs"] == 0 and
        results["summary"]["replay_failed"] == 0):
        results["classification"] = "AKR0_PASS / AUTHORITY_EXECUTION_ESTABLISHED"
    else:
        results["classification"] = "AKR_FAIL / SEE_DETAILS"

    # Write results
    results_path = os.path.join(output_dir, "akr0_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print("EXPERIMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Classification: {results['classification']}")
    print(f"Total runs: {results['summary']['total_runs']}")
    print(f"Passed: {results['summary']['passed_runs']}")
    print(f"Failed: {results['summary']['failed_runs']}")
    print(f"Replay verified: {results['summary']['replay_verified']}")
    print(f"Replay failed: {results['summary']['replay_failed']}")
    print(f"\nResults written to: {results_path}")

    return results


def run_single(condition: str, seed: int, output_dir: str = "results") -> dict:
    """Run a single condition/seed combination."""
    os.makedirs(output_dir, exist_ok=True)
    logs_dir = os.path.join(output_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    cond = Condition[condition.upper()]

    config = HarnessConfig(
        condition=cond,
        seed=seed,
        output_dir=logs_dir,
    )

    harness = ExecutionHarness(config)
    return harness.run()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AKR-0 Experiment Runner")
    parser.add_argument("--single", action="store_true",
                       help="Run a single condition/seed")
    parser.add_argument("--condition", type=str, choices=["A", "B", "C"],
                       help="Condition to run (for --single)")
    parser.add_argument("--seed", type=int, choices=SEEDS,
                       help="Seed to use (for --single)")
    parser.add_argument("--output", type=str, default="results",
                       help="Output directory")

    args = parser.parse_args()

    if args.single:
        if not args.condition or not args.seed:
            parser.error("--single requires --condition and --seed")
        result = run_single(args.condition, args.seed, args.output)
        print(json.dumps(result, indent=2))
    else:
        run_experiment(args.output)
