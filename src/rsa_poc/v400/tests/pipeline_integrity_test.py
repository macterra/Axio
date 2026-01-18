"""
RSA-PoC v4.0.1 — Pipeline Integrity Test
Per v4.0.1 binding action item D.

This test verifies that the pipeline correctly HALTs when JCOMP fails.

Test procedure:
1. Run baseline for 1 episode
2. At one step, force JCOMP to return SCHEMA_ERROR for all justifications
3. Verify that step results in HALT
4. Verify compilation failure counter is incremented
5. Verify no action executes on that step

If this test fails, the pipeline is bypassing normative control.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Optional

# Add parent to path for imports
sys.path.insert(0, "/home/david/Axio/src/rsa_poc")

from v400.core.compiler import (
    JCOMP400,
    CompilationBatch,
    CompilationResult,
    CompilationStatus,
    compute_feasible,
)
from v400.core.deliberator import FormalDeliberator
from v400.core.harness import (
    Deliberator,
    DeliberationOutput,
    MaskedActions,
    MVRSA400,
    SelectionSource,
    Selector,
    StepMetrics,
)
from v400.core.norm_state import create_initial_norm_state, expire_rules
from v400.env.tri_demand import ACTION_ID_MAP, Observation, TriDemandV400


@dataclass
class IntegrityTestResult:
    """Result of pipeline integrity test."""
    passed: bool
    halt_on_schema_error: bool
    compilation_failure_counted: bool
    no_action_executed: bool
    details: str


class FailingJCOMP(JCOMP400):
    """JCOMP that fails on a specific step."""

    def __init__(self, norm_state, fail_on_step: int):
        super().__init__(norm_state)
        self.fail_on_step = fail_on_step
        self.current_step = 0

    def compile_justifications(self, justifications):
        """Override to fail on specific step."""
        if self.current_step == self.fail_on_step:
            # Force SCHEMA_ERROR for all justifications
            results = [
                CompilationResult(
                    action_id=j.action_id,
                    status=CompilationStatus.SCHEMA_ERROR,
                    error_message="FORCED_FAILURE: Pipeline integrity test"
                )
                for j in justifications
            ]
            return CompilationBatch(results=results)
        return super().compile_justifications(justifications)


def run_pipeline_integrity_test(seed: int = 42, fail_on_step: int = 5) -> IntegrityTestResult:
    """
    Run pipeline integrity test.

    Forces JCOMP to fail on step `fail_on_step` and verifies:
    1. HALT occurs on that step
    2. Compilation failure is counted
    3. No action executes on that step
    """
    # Setup
    env = TriDemandV400(seed=seed)
    norm_state = create_initial_norm_state()
    deliberator = FormalDeliberator()
    selector = Selector(seed=seed)

    # Run one episode
    obs = env.reset(episode=0)
    norm_state = expire_rules(norm_state, 0)

    halt_on_error_step = False
    compilation_failure_counted = False
    no_action_on_error_step = True

    step_metrics: List[StepMetrics] = []

    for step in range(40):  # H=40 per spec
        # DELIBERATE
        delib_output = deliberator.deliberate(obs, norm_state)

        # COMPILE (with possible forced failure)
        compiler = FailingJCOMP(norm_state, fail_on_step=fail_on_step)
        compiler.current_step = step
        batch = compiler.compile_justifications(delib_output.justifications)

        # Check compilation failure
        if step == fail_on_step:
            if batch.failed_count == len(batch.results):
                compilation_failure_counted = True

        # Get compiled predicates
        compiled_predicates = [
            r.predicate for r in batch.results
            if r.status == CompilationStatus.COMPILED and r.predicate is not None
        ]

        # MASK
        mask_result = compute_feasible(
            compiled_predicates,
            norm_state,
            obs,
            0  # episode 0
        )

        masked_actions = MaskedActions(
            feasible=mask_result.feasible,
            feasible_count=mask_result.feasible_count
        )

        # SELECT
        selection = selector.select(masked_actions)

        # Track metrics for error step
        if step == fail_on_step:
            halt_on_error_step = (selection.source == SelectionSource.HALT)
            if selection.source != SelectionSource.HALT:
                no_action_on_error_step = False

        # Record
        metrics = StepMetrics(
            compilation_success=batch.compiled_count > 0,
            compilation_count=batch.compiled_count,
            halt=selection.source == SelectionSource.HALT,
            action_taken=selection.action_id if selection.source != SelectionSource.HALT else None,
            reward=0.0,
            binding_obligation=mask_result.binding_obligation,
        )
        step_metrics.append(metrics)

        if selection.source == SelectionSource.HALT:
            # Skip execution on HALT
            continue

        # EXECUTE
        action_int = ACTION_ID_MAP.get(selection.action_id, 0)
        obs, reward, done, info = env.step(action_int)

        if done:
            break

    # Analyze results
    passed = (
        halt_on_error_step and
        compilation_failure_counted and
        no_action_on_error_step
    )

    details = []
    if not halt_on_error_step:
        details.append(f"FAIL: Step {fail_on_step} did not HALT despite SCHEMA_ERROR")
    if not compilation_failure_counted:
        details.append(f"FAIL: Compilation failure not counted on step {fail_on_step}")
    if not no_action_on_error_step:
        details.append(f"FAIL: Action executed on step {fail_on_step} despite SCHEMA_ERROR")

    if passed:
        details.append("PASS: Pipeline correctly HALTs on SCHEMA_ERROR")

    return IntegrityTestResult(
        passed=passed,
        halt_on_schema_error=halt_on_error_step,
        compilation_failure_counted=compilation_failure_counted,
        no_action_executed=no_action_on_error_step,
        details="; ".join(details)
    )


def main():
    """Run pipeline integrity test."""
    print("=" * 60)
    print("RSA-PoC v4.0.1 — Pipeline Integrity Test")
    print("=" * 60)
    print()

    # Test on multiple steps
    test_steps = [0, 5, 10, 20]
    all_passed = True

    for step in test_steps:
        result = run_pipeline_integrity_test(seed=42, fail_on_step=step)
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"Step {step:2d}: {status}")
        print(f"         Halt on error: {result.halt_on_schema_error}")
        print(f"         Failure counted: {result.compilation_failure_counted}")
        print(f"         No action: {result.no_action_executed}")
        print(f"         {result.details}")
        print()
        all_passed = all_passed and result.passed

    print("=" * 60)
    if all_passed:
        print("PIPELINE INTEGRITY: ✓ VERIFIED")
        print("The pipeline correctly HALTs when JCOMP fails.")
    else:
        print("PIPELINE INTEGRITY: ✗ COMPROMISED")
        print("The pipeline is bypassing normative control!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
