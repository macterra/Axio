"""
RSA-PoC v4.1 — Experiment Runner
Implements §10.1-10.4 of v41_design_freeze.md

Main entry point for running v4.1 experiments with:
- Configurable seeds [42, 123, 456, 789, 1024]
- Full RSA pipeline, ablations, and calibrations
- Results output to JSON
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ablations import (
    AblationType,
    AblationHarness,
    AblationSuiteConfig,
    run_ablation_suite,
)
from .calibration import run_calibrations
from .core import create_initial_norm_state
from .deliberator import (
    DeterministicDeliberator,
    LLMDeliberator,
    LLMDeliberatorConfig,
)
from .env.tri_demand import TriDemandV410
from .harness import (
    HarnessConfig,
    MVRSA410Harness,
    check_guardrails,
)


# ============================================================================
# §10.1 — Experiment Configuration
# ============================================================================

# Frozen seeds per §10.1
FROZEN_SEEDS = [42, 123, 456, 789, 1024]

# Frozen parameters per §4.6
FROZEN_H = 40  # Max steps per episode
FROZEN_E = 20  # Max episodes
FROZEN_F = 10  # Max conflicts

# Guardrail thresholds per §4.7
FROZEN_C_MIN = 0.70  # Minimum compliance rate
FROZEN_H_MAX = 0.20  # Maximum halt rate
FROZEN_A_MAX = 0.10  # Maximum anomaly rate


@dataclass
class ExperimentConfig:
    """Configuration for a v4.1 experiment run."""
    name: str = "v410_experiment"
    seeds: List[int] = None
    max_steps_per_episode: int = FROZEN_H
    max_episodes: int = FROZEN_E
    max_conflicts: int = FROZEN_F
    use_llm: bool = False
    llm_model: str = "claude-sonnet-4-20250514"
    run_ablations: bool = True
    run_calibrations: bool = True
    output_dir: str = "."
    selector_type: str = "random"

    def __post_init__(self):
        if self.seeds is None:
            self.seeds = FROZEN_SEEDS.copy()


# ============================================================================
# §10.2 — Single Run Executor
# ============================================================================


def run_single_experiment(
    config: ExperimentConfig,
    seed: int,
    deliberator_type: str = "deterministic",
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Run a single experiment with one seed.

    Args:
        config: Experiment configuration
        seed: Random seed
        deliberator_type: "deterministic" or "llm"
        verbose: Print progress updates

    Returns:
        Experiment results dictionary
    """
    # Create environment
    env = TriDemandV410(seed=seed)

    # Create deliberator
    if deliberator_type == "llm" and config.use_llm:
        llm_config = LLMDeliberatorConfig(model=config.llm_model)
        deliberator = LLMDeliberator(llm_config)
    else:
        deliberator = DeterministicDeliberator()

    # Create harness config
    harness_config = HarnessConfig(
        max_steps_per_episode=config.max_steps_per_episode,
        max_episodes=config.max_episodes,
        max_conflicts=config.max_conflicts,
        seed=seed,
        selector_type=config.selector_type,
        record_telemetry=True,
        verbose=verbose
    )

    # Create and run harness
    harness = MVRSA410Harness(
        env=env,
        deliberator=deliberator,
        config=harness_config
    )

    results = harness.run()

    # Add metadata
    results["seed"] = seed
    results["deliberator_type"] = deliberator_type
    results["timestamp"] = datetime.now().isoformat()

    # Check guardrails
    guardrail_check = check_guardrails(
        results,
        c_min=FROZEN_C_MIN,
        h_max=FROZEN_H_MAX,
        a_max=FROZEN_A_MAX
    )
    results["guardrails"] = guardrail_check

    return results


# ============================================================================
# §10.3 — Full Experiment Suite
# ============================================================================


def run_full_experiment(config: ExperimentConfig) -> Dict[str, Any]:
    """
    Run the full experiment suite with all seeds, ablations, and calibrations.

    Returns:
        Complete experiment results
    """
    start_time = time.perf_counter()

    results = {
        "experiment_name": config.name,
        "version": "4.1.0",
        "config": asdict(config),
        "timestamp_start": datetime.now().isoformat(),
        "runs": {
            "baseline": [],
            "ablations": {},
            "calibrations": {}
        }
    }

    # Run baseline (full RSA) for each seed
    print(f"\n{'='*60}")
    print(f"Running baseline experiments across {len(config.seeds)} seeds...")
    print(f"Deliberator: {'LLM (Claude)' if config.use_llm else 'Deterministic'}")
    print(f"Protocol: H={config.max_steps_per_episode}, E={config.max_episodes}")
    print(f"{'='*60}")

    for i, seed in enumerate(config.seeds):
        print(f"\n[{i+1}/{len(config.seeds)}] Seed {seed}...", flush=True)
        deliberator_type = "llm" if config.use_llm else "deterministic"
        run_result = run_single_experiment(config, seed, deliberator_type, verbose=True)
        results["runs"]["baseline"].append(run_result)

        # Print seed summary
        summary = run_result["summary"]
        print(f"  ✓ Seed {seed} complete: {summary['total_steps']} steps, "
              f"{summary['total_halts']} halts ({summary['total_halts']/max(1,summary['total_steps'])*100:.1f}%), "
              f"{summary['elapsed_ms']/1000:.1f}s", flush=True)

    # Run ablations if enabled
    if config.run_ablations:
        print(f"\n{'='*60}")
        print("Running ablation experiments...")
        print(f"{'='*60}")

        for ablation_type in AblationType:
            print(f"\n[Ablation {ablation_type.value}]", flush=True)
            ablation_results = []

            for i, seed in enumerate(config.seeds):
                print(f"  [{i+1}/{len(config.seeds)}] Seed {seed}...", end="", flush=True)
                env = TriDemandV410(seed=seed)
                harness_config = HarnessConfig(
                    max_steps_per_episode=config.max_steps_per_episode,
                    max_episodes=config.max_episodes,
                    max_conflicts=config.max_conflicts,
                    seed=seed,
                    selector_type=config.selector_type,
                    record_telemetry=True,
                    verbose=config.use_llm  # Verbose for LLM runs
                )

                # Create deliberator for ablation - use LLM if configured
                if config.use_llm:
                    llm_config = LLMDeliberatorConfig(model=config.llm_model)
                    ablation_deliberator = LLMDeliberator(llm_config)
                else:
                    ablation_deliberator = DeterministicDeliberator()

                ablation_harness = AblationHarness(
                    env=env,
                    ablation_type=ablation_type,
                    config=harness_config,
                    deliberator=ablation_deliberator
                )

                ablation_result = ablation_harness.run()
                ablation_result["seed"] = seed
                ablation_results.append(ablation_result)

                summary = ablation_result["summary"]
                print(f" {summary['total_steps']} steps, {summary['total_halts']} halts, "
                      f"{summary['elapsed_ms']/1000:.1f}s", flush=True)

            results["runs"]["ablations"][ablation_type.value] = ablation_results

    # Run calibrations if enabled
    if config.run_calibrations:
        print("Running calibration experiments...")
        calibration_results = run_calibrations(
            seeds=config.seeds,
            max_steps=config.max_steps_per_episode,
            max_episodes=config.max_episodes
        )
        results["runs"]["calibrations"] = calibration_results

    # Calculate summary statistics
    elapsed = (time.perf_counter() - start_time) * 1000
    results["timestamp_end"] = datetime.now().isoformat()
    results["elapsed_ms"] = elapsed

    # Compute aggregate metrics
    results["summary"] = compute_summary_statistics(results)

    return results


def compute_summary_statistics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Compute aggregate statistics from experiment results."""
    summary = {
        "baseline": {},
        "ablations": {},
        "calibrations": {}
    }

    # Baseline statistics
    baseline_runs = results["runs"]["baseline"]
    if baseline_runs:
        total_steps = sum(r["summary"]["total_steps"] for r in baseline_runs)
        total_halts = sum(r["summary"]["total_halts"] for r in baseline_runs)
        avg_halt_rate = total_halts / total_steps if total_steps > 0 else 0

        summary["baseline"] = {
            "num_runs": len(baseline_runs),
            "total_steps": total_steps,
            "total_halts": total_halts,
            "avg_halt_rate": avg_halt_rate,
            "guardrails_passed": sum(
                1 for r in baseline_runs
                if r.get("guardrails", {}).get("passed", False)
            )
        }

    # Ablation statistics
    for ablation_type, ablation_runs in results["runs"].get("ablations", {}).items():
        if ablation_runs:
            total_steps = sum(r["summary"]["total_steps"] for r in ablation_runs)
            total_halts = sum(r["summary"]["total_halts"] for r in ablation_runs)
            avg_halt_rate = total_halts / total_steps if total_steps > 0 else 0

            summary["ablations"][ablation_type] = {
                "num_runs": len(ablation_runs),
                "total_steps": total_steps,
                "total_halts": total_halts,
                "avg_halt_rate": avg_halt_rate
            }

    return summary


# ============================================================================
# §10.4 — CLI Entry Point
# ============================================================================


def main():
    """Command-line entry point for v4.1 experiments."""
    parser = argparse.ArgumentParser(
        description="RSA-PoC v4.1 Experiment Runner"
    )

    parser.add_argument(
        "--name",
        type=str,
        default="v410_experiment",
        help="Experiment name"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=FROZEN_SEEDS,
        help="Random seeds to use"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=FROZEN_H,
        help="Max steps per episode"
    )
    parser.add_argument(
        "--max-episodes",
        type=int,
        default=FROZEN_E,
        help="Max episodes"
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM-backed deliberator"
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="LLM model to use"
    )
    parser.add_argument(
        "--no-ablations",
        action="store_true",
        help="Skip ablation experiments"
    )
    parser.add_argument(
        "--no-calibrations",
        action="store_true",
        help="Skip calibration experiments"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Output directory for results"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Output filename (default: auto-generated)"
    )

    args = parser.parse_args()

    # Build config
    config = ExperimentConfig(
        name=args.name,
        seeds=args.seeds,
        max_steps_per_episode=args.max_steps,
        max_episodes=args.max_episodes,
        use_llm=args.use_llm,
        llm_model=args.llm_model,
        run_ablations=not args.no_ablations,
        run_calibrations=not args.no_calibrations,
        output_dir=args.output_dir
    )

    print(f"RSA-PoC v4.1 Experiment Runner")
    print(f"  Name: {config.name}")
    print(f"  Seeds: {config.seeds}")
    print(f"  Max steps: {config.max_steps_per_episode}")
    print(f"  Max episodes: {config.max_episodes}")
    print(f"  Use LLM: {config.use_llm}")
    print(f"  Run ablations: {config.run_ablations}")
    print(f"  Run calibrations: {config.run_calibrations}")
    print()

    # Run experiment
    results = run_full_experiment(config)

    # Generate output filename
    if args.output_file:
        output_file = args.output_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{config.name}_{timestamp}.json"

    output_path = Path(args.output_dir) / output_file

    # Write results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to: {output_path}")

    # Print summary
    print("\n=== Summary ===")
    summary = results.get("summary", {})

    if "baseline" in summary:
        baseline = summary["baseline"]
        print(f"Baseline: {baseline.get('num_runs', 0)} runs, "
              f"halt rate: {baseline.get('avg_halt_rate', 0):.2%}, "
              f"guardrails passed: {baseline.get('guardrails_passed', 0)}/{baseline.get('num_runs', 0)}")

    if "ablations" in summary:
        for ablation_type, stats in summary["ablations"].items():
            print(f"Ablation ({ablation_type}): {stats.get('num_runs', 0)} runs, "
                  f"halt rate: {stats.get('avg_halt_rate', 0):.2%}")

    return 0


# ============================================================================
# Quick Run Functions (for interactive use)
# ============================================================================


def quick_run(seed: int = 42, max_steps: int = 10, max_episodes: int = 2) -> Dict[str, Any]:
    """
    Quick single-seed run for testing.
    """
    config = ExperimentConfig(
        name="quick_test",
        seeds=[seed],
        max_steps_per_episode=max_steps,
        max_episodes=max_episodes,
        run_ablations=False,
        run_calibrations=False
    )
    return run_single_experiment(config, seed)


def quick_ablation_run(
    ablation_type: AblationType,
    seed: int = 42,
    max_steps: int = 10,
    max_episodes: int = 2
) -> Dict[str, Any]:
    """
    Quick ablation run for testing.
    """
    env = TriDemandV410(seed=seed)
    config = HarnessConfig(
        max_steps_per_episode=max_steps,
        max_episodes=max_episodes,
        max_conflicts=10,
        seed=seed
    )

    harness = AblationHarness(
        env=env,
        ablation_type=ablation_type,
        config=config
    )

    return harness.run()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "FROZEN_SEEDS",
    "FROZEN_H",
    "FROZEN_E",
    "FROZEN_F",
    "FROZEN_C_MIN",
    "FROZEN_H_MAX",
    "FROZEN_A_MAX",
    "ExperimentConfig",
    "run_single_experiment",
    "run_full_experiment",
    "compute_summary_statistics",
    "main",
    "quick_run",
    "quick_ablation_run",
]


if __name__ == "__main__":
    sys.exit(main())
