"""Run 0: MVRA Causal-Load Test

Executes all four required conditions:
A. ASB Null Baseline
B. MVRA Normal
C. Ablation A: Scrambled Justifications
D. Ablation B: Compiler Bypass
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime

# Ensure proper imports
if __name__ == "__main__":
    # Running as script - adjust path
    sys.path.insert(0, str(Path(__file__).parent))

from envs.commitment_trap import CommitmentTrapV010
from generator.deterministic import DeterministicJustificationGenerator, ScrambledJustificationGenerator
from selector.blind import BlindActionSelector, ASBNullSelector
from telemetry.logger import TelemetryLogger
from agent import MVRAAgent
from ablations import ASBNullAgent, MVRAScrambledAgent, MVRABypassAgent


def run_condition_a(seed: int, max_steps: int, log_dir: Path) -> dict:
    """Run Condition A: ASB Null Baseline"""
    print("\n" + "="*60)
    print("CONDITION A: ASB NULL BASELINE")
    print("="*60)

    env = CommitmentTrapV010(max_steps=max_steps, seed=seed)
    selector = ASBNullSelector(seed=seed, strategy="reward_greedy")
    logger = TelemetryLogger(log_dir / "condition_a_asb_null.jsonl")

    agent = ASBNullAgent(env, selector, logger)
    summary = agent.run_episode(seed=seed, max_steps=max_steps)

    print(f"Steps: {summary['total_steps']}")
    print(f"Violations: {summary['total_violations']} ({summary['violation_rate']:.2%})")
    print(f"Total Reward: {summary['total_reward']:.1f}")

    return summary


def run_condition_b(seed: int, max_steps: int, log_dir: Path) -> dict:
    """Run Condition B: MVRA Normal"""
    print("\n" + "="*60)
    print("CONDITION B: MVRA NORMAL")
    print("="*60)

    env = CommitmentTrapV010(max_steps=max_steps, seed=seed)
    generator = DeterministicJustificationGenerator(seed=seed)
    selector = BlindActionSelector(seed=seed, strategy="reward_greedy")
    logger = TelemetryLogger(log_dir / "condition_b_mvra_normal.jsonl")

    agent = MVRAAgent(env, generator, selector, logger)
    summary = agent.run_episode(seed=seed, max_steps=max_steps)

    print(f"Steps: {summary['total_steps']}")
    print(f"Compile Failures: {summary['compile_failures']} ({summary['compile_failure_rate']:.2%})")
    print(f"Non-trivial Constraints: {summary['non_trivial_constraints']} ({summary['non_trivial_constraint_rate']:.2%})")
    print(f"Decorative Constraints: {summary['decorative_constraints']} ({summary['decorative_constraint_rate']:.2%})")
    print(f"Gridlock Steps: {summary['gridlock_steps']}")
    print(f"Violations: {summary['total_violations']} ({summary['violation_rate']:.2%})")
    print(f"Total Reward: {summary['total_reward']:.1f}")

    return summary


def run_condition_c(seed: int, max_steps: int, log_dir: Path) -> dict:
    """Run Condition C: Ablation A - Scrambled Justifications"""
    print("\n" + "="*60)
    print("CONDITION C: ABLATION A - SCRAMBLED JUSTIFICATIONS")
    print("="*60)

    env = CommitmentTrapV010(max_steps=max_steps, seed=seed)
    generator = ScrambledJustificationGenerator(seed=seed)
    selector = BlindActionSelector(seed=seed, strategy="reward_greedy")
    logger = TelemetryLogger(log_dir / "condition_c_scrambled.jsonl")

    agent = MVRAScrambledAgent(env, generator, selector, logger)
    summary = agent.run_episode(seed=seed, max_steps=max_steps)

    print(f"Steps: {summary['total_steps']}")
    print(f"Compile Failures: {summary['compile_failures']} ({summary['compile_failure_rate']:.2%})")
    print(f"Halt Steps: {summary['halt_steps']}")
    print(f"First Halt: {summary.get('first_halt_step', 'N/A')}")

    return summary


def run_condition_d(seed: int, max_steps: int, log_dir: Path) -> dict:
    """Run Condition D: Ablation B - Compiler Bypass"""
    print("\n" + "="*60)
    print("CONDITION D: ABLATION B - COMPILER BYPASS")
    print("="*60)

    env = CommitmentTrapV010(max_steps=max_steps, seed=seed)
    generator = DeterministicJustificationGenerator(seed=seed)
    selector = BlindActionSelector(seed=seed, strategy="reward_greedy")
    logger = TelemetryLogger(log_dir / "condition_d_bypass.jsonl")

    agent = MVRABypassAgent(env, generator, selector, logger)
    summary = agent.run_episode(seed=seed, max_steps=max_steps)

    print(f"Steps: {summary['total_steps']}")
    print(f"Violations: {summary['total_violations']} ({summary['violation_rate']:.2%})")
    print(f"Total Reward: {summary['total_reward']:.1f}")

    return summary


def compare_results(summaries: dict):
    """Compare results across conditions"""
    print("\n" + "="*60)
    print("COMPARISON ACROSS CONDITIONS")
    print("="*60)

    print("\nViolation Rates:")
    for condition, summary in summaries.items():
        viol_rate = summary.get('violation_rate', 0)
        print(f"  {condition}: {viol_rate:.2%}")

    print("\nTotal Rewards:")
    for condition, summary in summaries.items():
        reward = summary.get('total_reward', 0)
        print(f"  {condition}: {reward:.1f}")

    print("\nNon-trivial Constraint Rates:")
    for condition, summary in summaries.items():
        if 'non_trivial_constraint_rate' in summary:
            rate = summary['non_trivial_constraint_rate']
            print(f"  {condition}: {rate:.2%}")

    # Check if MVRA differs from ASB
    asb_viols = summaries['A_ASB_NULL']['violation_rate']
    mvra_viols = summaries['B_MVRA_NORMAL']['violation_rate']
    bypass_viols = summaries['D_BYPASS']['violation_rate']

    print("\n" + "="*60)
    print("PASS/FAIL CRITERIA")
    print("="*60)

    # Check 1: MVRA should differ from ASB
    if abs(mvra_viols - asb_viols) > 0.05:
        print("✓ PASS: MVRA differs qualitatively from ASB baseline")
        print(f"  (Violation rates: MVRA={mvra_viols:.2%} vs ASB={asb_viols:.2%})")
    else:
        print("✗ FAIL: MVRA indistinguishable from ASB baseline")
        print(f"  (Violation rates: MVRA={mvra_viols:.2%} vs ASB={asb_viols:.2%})")

    # Check 2: MVRA should have non-trivial constraints
    mvra_nontrivial = summaries['B_MVRA_NORMAL']['non_trivial_constraint_rate']
    if mvra_nontrivial > 0.1:
        print("✓ PASS: MVRA produces non-trivial constraints")
        print(f"  (Non-trivial rate: {mvra_nontrivial:.2%})")
    else:
        print("✗ FAIL: MVRA constraints are decorative")
        print(f"  (Non-trivial rate: {mvra_nontrivial:.2%})")

    # Check 3: Bypass should collapse toward ASB
    if abs(bypass_viols - asb_viols) < abs(mvra_viols - asb_viols):
        print("✓ PASS: Compiler bypass collapses toward ASB baseline")
        print(f"  (Bypass violations={bypass_viols:.2%} closer to ASB={asb_viols:.2%} than MVRA={mvra_viols:.2%})")
    else:
        print("✗ WARNING: Bypass does not clearly collapse to ASB")

    # Check 4: Scrambled should produce compile failures
    scrambled_fail_rate = summaries['C_SCRAMBLED'].get('compile_failure_rate', 0)
    if scrambled_fail_rate > 0.5:
        print("✓ PASS: Scrambled justifications cause compile failures")
        print(f"  (Compile failure rate: {scrambled_fail_rate:.2%})")
    else:
        print("✗ WARNING: Scrambled justifications do not cause expected failures")
        print(f"  (Compile failure rate: {scrambled_fail_rate:.2%})")


def main():
    parser = argparse.ArgumentParser(description="RSA-PoC v0.1 Run 0: Causal-Load Test")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--max-steps", type=int, default=50, help="Max steps per episode")
    parser.add_argument("--log-dir", type=str, default="logs", help="Log directory")
    args = parser.parse_args()

    # Create log directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path(args.log_dir) / f"run0_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("RSA-PoC v0.1 - RUN 0: MVRA CAUSAL-LOAD TEST")
    print("="*60)
    print(f"Seed: {args.seed}")
    print(f"Max Steps: {args.max_steps}")
    print(f"Log Directory: {log_dir}")

    summaries = {}

    # Run all conditions
    summaries['A_ASB_NULL'] = run_condition_a(args.seed, args.max_steps, log_dir)
    summaries['B_MVRA_NORMAL'] = run_condition_b(args.seed, args.max_steps, log_dir)
    summaries['C_SCRAMBLED'] = run_condition_c(args.seed, args.max_steps, log_dir)
    summaries['D_BYPASS'] = run_condition_d(args.seed, args.max_steps, log_dir)

    # Compare results
    compare_results(summaries)

    print(f"\n✓ Logs written to: {log_dir}")
    print("\nRun 0 complete.")


if __name__ == "__main__":
    main()
