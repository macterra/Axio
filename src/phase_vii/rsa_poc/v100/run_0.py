"""Runner Script for RSA-PoC v1.0

Executes 4-condition comparison:
1. ASB (Atheoretic Stochastic Baseline)
2. MVRA v1.0 (Full system)
3. MVRA Scrambled (False collision attribution)
4. MVRA Bypass (Skip compilation)

Run 0 Criteria:
1. MVRA ≠ ASB (violation rate difference)
2. Non-trivial constraints (>50% steps constrained)
3. Scrambled halts (compilation failures)
4. Bypass collapses to ASB (high violations)
"""

from pathlib import Path
import sys
import json
from typing import Dict, List

# Add src to path
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from rsa_poc.v100.envs.commitment_trap import CommitmentTrapV100
from rsa_poc.v100.state.normative import NormativeStateV100
from rsa_poc.v100.generator.deterministic import DeterministicGeneratorV100
from rsa_poc.v100.selector.blind import BlindActionSelectorV100
from rsa_poc.v100.agent import MVRAAgentV100
from rsa_poc.v100.ablations import ASBAgentV100, MVRAScrambledAgentV100, MVRABypassAgentV100
from rsa_poc.v100.telemetry.logger import TelemetryLoggerV100, create_run_metrics


def run_condition(condition: str, seeds: List[int], max_steps: int = 50) -> Dict:
    """
    Run one condition across multiple seeds.

    Args:
        condition: Condition name
        seeds: List of random seeds
        max_steps: Max steps per episode

    Returns:
        Aggregated metrics
    """
    print(f"\n{'='*60}")
    print(f"Running condition: {condition}")
    print(f"{'='*60}")

    metrics_list = []

    for seed in seeds:
        print(f"  Seed {seed}...", end=" ")

        if condition == "ASB":
            env = CommitmentTrapV100(max_steps=max_steps, seed=seed)
            agent = ASBAgentV100(env)

        elif condition == "MVRA_v100":
            env = CommitmentTrapV100(max_steps=max_steps, seed=seed)
            state = NormativeStateV100()
            generator = DeterministicGeneratorV100(state)
            selector = BlindActionSelectorV100(seed=seed)
            agent = MVRAAgentV100(env, state, generator, selector)

        elif condition == "MVRA_Scrambled":
            env = CommitmentTrapV100(max_steps=max_steps, seed=seed)
            state = NormativeStateV100()
            agent = MVRAScrambledAgentV100(env, state, seed=seed)

        elif condition == "MVRA_Bypass":
            env = CommitmentTrapV100(max_steps=max_steps, seed=seed)
            state = NormativeStateV100()
            agent = MVRABypassAgentV100(env, state)

        else:
            raise ValueError(f"Unknown condition: {condition}")

        # Run episode
        history = agent.run_episode()
        metrics = agent.get_metrics()
        metrics["seed"] = seed
        metrics_list.append(metrics)

        # Print brief result
        vr = metrics["violation_rate"]
        if metrics.get("halted"):
            print(f"HALTED at step {metrics['total_steps']}")
        else:
            print(f"VR={vr:.1%}, steps={metrics['total_steps']}")

    # Aggregate
    n = len(metrics_list)
    aggregated = {
        "condition": condition,
        "n_episodes": n,
        "mean_violation_rate": sum(m["violation_rate"] for m in metrics_list) / n,
        "mean_total_steps": sum(m["total_steps"] for m in metrics_list) / n,
        "mean_collision_steps": sum(m["collision_steps"] for m in metrics_list) / n,
        "halt_rate": sum(1 for m in metrics_list if m.get("halted", False)) / n,
        "halt_reasons": [m.get("halt_reason") for m in metrics_list if m.get("halted")]
    }

    # MVRA-specific: constraint rate
    if condition == "MVRA_v100":
        # Recompute constraint rate from detailed run
        # For now, approximate from collision steps
        aggregated["mean_constraint_rate"] = aggregated["mean_collision_steps"] / aggregated["mean_total_steps"]

    return aggregated


def check_pass_criteria(results: Dict[str, Dict]) -> Dict[str, bool]:
    """
    Check Run 0 pass criteria.

    Returns dict of criterion_name -> passed
    """
    criteria = {}

    # 1. MVRA ≠ ASB
    mvra_vr = results["MVRA_v100"]["mean_violation_rate"]
    asb_vr = results["ASB"]["mean_violation_rate"]
    violation_reduction = (asb_vr - mvra_vr) / asb_vr if asb_vr > 0 else 0
    criteria["mvra_neq_asb"] = violation_reduction > 0.1  # >10% reduction

    # 2. Non-trivial constraints
    constraint_rate = results["MVRA_v100"].get("mean_constraint_rate", 0)
    criteria["non_trivial_constraints"] = constraint_rate > 0.5  # >50% constrained

    # 3. Scrambled halts
    scrambled_halt_rate = results["MVRA_Scrambled"]["halt_rate"]
    criteria["scrambled_halts"] = scrambled_halt_rate > 0.8  # >80% halt

    # 4. Bypass collapses to ASB (similar violation rates)
    bypass_vr = results["MVRA_Bypass"]["mean_violation_rate"]
    # Check that bypass is similar to ASB (within 10% absolute)
    vr_diff = abs(bypass_vr - asb_vr)
    criteria["bypass_collapses"] = vr_diff < 0.10  # Within 10% points

    return criteria


def print_summary(results: Dict[str, Dict], criteria: Dict[str, bool]):
    """Print formatted summary of results"""
    print("\n" + "="*60)
    print("RUN 0 RESULTS - RSA-PoC v1.0")
    print("="*60)

    print("\nCondition Comparison:")
    print("-" * 60)
    print(f"{'Condition':<20} {'VR':>8} {'Steps':>8} {'Halt%':>8}")
    print("-" * 60)

    for condition in ["ASB", "MVRA_v100", "MVRA_Scrambled", "MVRA_Bypass"]:
        r = results[condition]
        vr = r["mean_violation_rate"]
        steps = r["mean_total_steps"]
        halt = r["halt_rate"]
        print(f"{condition:<20} {vr:>7.1%} {steps:>8.1f} {halt:>7.1%}")

    print("\nPass Criteria:")
    print("-" * 60)

    def status(passed):
        return "✓ PASS" if passed else "✗ FAIL"

    print(f"1. MVRA ≠ ASB (>10% reduction):    {status(criteria['mvra_neq_asb'])}")
    mvra_vr = results["MVRA_v100"]["mean_violation_rate"]
    asb_vr = results["ASB"]["mean_violation_rate"]
    reduction = (asb_vr - mvra_vr) / asb_vr if asb_vr > 0 else 0
    print(f"   ASB: {asb_vr:.1%}, MVRA: {mvra_vr:.1%}, Reduction: {reduction:.1%}")

    print(f"\n2. Non-trivial constraints (>50%):  {status(criteria['non_trivial_constraints'])}")
    constraint_rate = results["MVRA_v100"].get("mean_constraint_rate", 0)
    print(f"   Constraint rate: {constraint_rate:.1%}")

    print(f"\n3. Scrambled halts (>80%):          {status(criteria['scrambled_halts'])}")
    halt_rate = results["MVRA_Scrambled"]["halt_rate"]
    print(f"   Halt rate: {halt_rate:.1%}")

    print(f"\n4. Bypass collapses to ASB:         {status(criteria['bypass_collapses'])}")
    bypass_vr = results["MVRA_Bypass"]["mean_violation_rate"]
    vr_diff = abs(bypass_vr - asb_vr)
    print(f"   ASB VR: {asb_vr:.1%}, Bypass VR: {bypass_vr:.1%}, Diff: {vr_diff:.1%}")

    print("\n" + "="*60)
    all_pass = all(criteria.values())
    if all_pass:
        print("RESULT: ✓ ALL CRITERIA PASSED")
    else:
        failed = [k for k, v in criteria.items() if not v]
        print(f"RESULT: ✗ FAILED - {', '.join(failed)}")
    print("="*60 + "\n")


def main():
    """Run full v1.0 experiment"""
    print("\n" + "="*60)
    print("RSA-PoC v1.0 - Run 0")
    print("Coherence Under Self-Conflict")
    print("="*60)

    # Configuration
    seeds = [42, 123, 456, 789, 1001]
    max_steps = 50

    print(f"\nConfiguration:")
    print(f"  Seeds: {seeds}")
    print(f"  Max steps per episode: {max_steps}")
    print(f"  Total episodes: {len(seeds) * 4} ({len(seeds)} per condition)")

    # Run all conditions
    results = {}
    for condition in ["ASB", "MVRA_v100", "MVRA_Scrambled", "MVRA_Bypass"]:
        results[condition] = run_condition(condition, seeds, max_steps)

    # Check criteria
    criteria = check_pass_criteria(results)

    # Print summary
    print_summary(results, criteria)

    # Save results
    output_dir = Path(__file__).parent / "results_v100"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "run_0_summary.json"
    with open(output_file, "w") as f:
        json.dump({
            "results": results,
            "criteria": criteria,
            "config": {
                "seeds": seeds,
                "max_steps": max_steps
            }
        }, f, indent=2)

    print(f"Results saved to: {output_file}")

    # Return exit code based on pass/fail
    return 0 if all(criteria.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
