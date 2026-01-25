#!/usr/bin/env python3
"""
Quick validation of Bug #3 and Bug #4 fixes.

Ablation D: E=1, H=3, seed=42 → expect HALT at step 0 (empty rule_evals)
ASB Null:   E=5, H=40, seed=42 → expect ~0% halt rate
"""

import sys
sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v410.env.tri_demand import TriDemandV410
from src.rsa_poc.v410.ablations import AblationType, AblationHarness, TraceExcisionCompiler
from src.rsa_poc.v410.calibration import ASBNullCalibration
from src.rsa_poc.v410.harness import HarnessConfig
from src.rsa_poc.v410.deliberator import DeterministicDeliberator
from src.rsa_poc.v410.calibration import ASBNullCalibration, ASBNullCalibrationConfig


def test_ablation_d():
    """Ablation D micro-run: E=1, H=3, seed=42."""
    print("=" * 60)
    print("ABLATION D MICRO-RUN: E=1, H=3, seed=42")
    print("=" * 60)
    print()

    env = TriDemandV410(seed=42)
    config = HarnessConfig(max_episodes=1, max_steps_per_episode=3, seed=42)

    harness = AblationHarness(
        env=env,
        ablation_type=AblationType.TRACE_EXCISION,
        config=config,
        deliberator=DeterministicDeliberator(),
        seed=42
    )

    # Verify TraceExcisionCompiler is in place
    print(f"Compiler type: {type(harness._harness.compiler).__name__}")
    is_trace_compiler = isinstance(harness._harness.compiler, TraceExcisionCompiler)
    print(f"Is TraceExcisionCompiler: {is_trace_compiler}")
    print()

    # Test compilation directly
    print("--- Direct Compiler Test ---")
    test_justification = '{"action_id": "A0", "rule_refs": ["R4"], "claims": []}'
    result = harness._harness.compiler.compile(test_justification)
    print(f"  Compilation status: {result.status}")
    print(f"  rule_evals count: {len(result.rule_evals)}")
    print(f"  rule_evals: {result.rule_evals}")

    rule_evals_empty = len(result.rule_evals) == 0
    print(f"  rule_evals == []: {rule_evals_empty}")
    print()

    # Run the harness
    print("--- Running Harness ---")
    run_result = harness.run()

    summary = run_result.get('summary', {})
    total_halts = summary.get('total_halts', 0)
    total_steps = summary.get('total_steps', 0)
    # Note: When HALT occurs, no step is executed, so total_steps = 0 is expected!
    # For Ablation D, we expect ALL attempts to HALT
    max_attempts = 1 * 3  # E=1, H=3

    print(f"Total steps executed: {total_steps}")
    print(f"Total halts: {total_halts}")
    print(f"Max attempts: {max_attempts}")
    print()

    # Check pass criterion: All 3 attempts should HALT
    all_halted = total_halts == max_attempts and total_steps == 0
    passed = rule_evals_empty and all_halted
    print(f"PASS CRITERIA:")
    print(f"  rule_evals == []: {'✅' if rule_evals_empty else '❌'}")
    print(f"  All {max_attempts} attempts HALT (steps=0, halts={max_attempts}): {'✅' if all_halted else '❌'}")
    print(f"RESULT: {'✅ PASS' if passed else '❌ FAIL'}")
    print()

    return passed


def test_asb_null():
    """ASB Null micro-run: E=5, H=40, seed=42."""
    print("=" * 60)
    print("ASB NULL MICRO-RUN: E=5, H=40, seed=42")
    print("=" * 60)
    print()

    config = ASBNullCalibrationConfig(
        max_episodes=5,
        max_steps_per_episode=40,
        seed=42
    )
    calibration = ASBNullCalibration(config=config)

    result = calibration.run()

    summary = result['summary']
    total_steps = summary['total_steps']
    total_halts = summary['total_halts']
    halt_rate = summary['halt_rate']
    total_reward = summary['total_reward']

    print(f"Total steps: {total_steps}")
    print(f"Total halts: {total_halts}")
    print(f"Halt rate: {halt_rate:.2%}")
    print(f"Total reward: {total_reward}")
    print()

    # Calculate success rate (reward per episode)
    avg_reward_per_episode = total_reward / 5
    # In TriDemand, max reward per episode is 3.0 (all zones satisfied)
    # Random walk success rate should be very low
    success_rate = avg_reward_per_episode / 3.0 if total_reward > 0 else 0.0

    print(f"Avg reward/episode: {avg_reward_per_episode:.2f}")
    print(f"Estimated success rate: {success_rate:.2%}")
    print()

    # Check pass criteria
    halt_pass = halt_rate < 0.01  # ~0% halt rate
    success_pass = success_rate <= 0.10  # Low success for random walk
    passed = halt_pass and success_pass

    print(f"PASS CRITERIA:")
    print(f"  halt_rate ≈ 0%: {'✅' if halt_pass else '❌'} ({halt_rate:.2%})")
    print(f"  success_rate ≤ 10%: {'✅' if success_pass else '❌'} ({success_rate:.2%})")
    print(f"RESULT: {'✅ PASS' if passed else '❌ FAIL'}")
    print()

    return passed


def main():
    print()
    print("v4.1.1 BUG FIX VALIDATION")
    print("=" * 60)
    print()

    ablation_d_pass = test_ablation_d()
    asb_null_pass = test_asb_null()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Ablation D (Bug #3 fix): {'✅ PASS' if ablation_d_pass else '❌ FAIL'}")
    print(f"ASB Null (Bug #4 fix):   {'✅ PASS' if asb_null_pass else '❌ FAIL'}")
    print()

    if ablation_d_pass and asb_null_pass:
        print("🎉 Both fixes validated! Ready for full-protocol reruns.")
        return 0
    else:
        print("⚠️  Fix validation failed. Review required.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
