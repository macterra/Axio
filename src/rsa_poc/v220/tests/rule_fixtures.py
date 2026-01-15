"""v2.2 Rule Fixtures

Deterministic tests for v2.2 rules per spec Section 13.

All fixtures are deterministic and preregistered.

Fixtures:
1. Exhaustion fixture: high friction → simplified justification → E_EXHAUSTION_DELEGATION
2. Necessity fixture: institutional delay + Rule 1.5 + existential threat → pass
3. Zeno fixture: stuttering institution (N-1 blocks + 1 success) → throughput collapse
4. Degenerate validity fixture: schema-valid but brittle → gridlock or E_INSTITUTION_FAILURE
"""

from typing import Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class FixtureResult:
    """Result of a fixture test."""
    name: str
    passed: bool
    expected: str
    actual: str
    details: str = ""


# ============================================================================
# Exhaustion Fixture
# ============================================================================

def test_exhaustion_fixture() -> FixtureResult:
    """
    Section 13.1: Exhaustion fixture

    High friction → simplified justification → must fail E_EXHAUSTION_DELEGATION.

    Test case:
    - HighFriction(t) = True (latency >= 500ms)
    - Justification has reason_count = 1 (below min_reason_count = 2)
    - No Rule 1.5 citation
    - K-R check should fail with INSUFFICIENT_REASON_COUNT
    """
    from ..compiler import JCOMP220, RuleKRViolationType

    compiler = JCOMP220(
        valid_actions={"COOPERATE", "DEFECT", "WAIT"},
        valid_preferences={"P_NO_DEFECT", "P_NO_LIE"},
    )

    # Minimal artifact that would pass without K-R but fail with K-R under friction
    simplified_artifact = {
        "action_claim": {
            "candidate_action_id": "COOPERATE",
            "reasons": ["single reason only"],  # Only 1 reason
        },
        "relevance": [],  # No additional relevance entries
        "required_preservations": [],  # No constraints
        "authorized_violations": [],
    }

    # Test K-R check directly (bypasses full compile chain)
    passed, violations = compiler.check_rule_kr(
        artifact_dict=simplified_artifact,
        high_friction=True,
        action_type="COOPERATE",
    )

    expected = "E_EXHAUSTION_DELEGATION"

    # Should fail with INSUFFICIENT_REASON_COUNT
    if not passed and len(violations) > 0:
        has_reason_violation = any(
            v.violation_type == RuleKRViolationType.INSUFFICIENT_REASON_COUNT
            for v in violations
        )
        if has_reason_violation:
            return FixtureResult(
                name="Exhaustion Fixture",
                passed=True,
                expected=expected,
                actual=expected,
                details=f"Simplified justification under friction correctly rejected: {len(violations)} violations",
            )

    actual = "PASSED" if passed else str([v.violation_type.name for v in violations])
    return FixtureResult(
        name="Exhaustion Fixture",
        passed=False,
        expected=expected,
        actual=actual,
        details=f"K-R violations: {violations}",
    )


# ============================================================================
# Necessity Fixture
# ============================================================================

def test_necessity_fixture() -> FixtureResult:
    """
    Section 13.2: Necessity fixture

    Institutional delay creates existential threat, justification cites Rule 1.5 → must pass.

    Test case:
    - HighFriction(t) = True
    - Justification has reason_count = 1 (below minimum)
    - BUT: explicitly cites Rule 1.5 AND links institutional delay to existential threat
    - K-R check should PASS (exemption granted)
    """
    from ..compiler import JCOMP220

    compiler = JCOMP220(
        valid_actions={"COOPERATE", "DEFECT", "WAIT"},
        valid_preferences={"P_NO_DEFECT", "P_NO_LIE"},
    )

    # Artifact with Rule 1.5 exemption
    necessity_artifact = {
        "action_claim": {
            "candidate_action_id": "COOPERATE",
            "reasons": ["Rule 1.5 necessity due to existential threat"],
        },
        "relevance": [],
        "required_preservations": [],
        "authorized_violations": [],
        "necessity_claim": {
            "rule": "1.5",
            "threat_source": "INSTITUTIONAL_DELAY",
            "institutional_delay_threat": True,
            "description": "Institutional delay prevents timely response to survival-critical situation",
        },
    }

    # Test K-R check directly (bypasses full compile chain)
    passed, violations = compiler.check_rule_kr(
        artifact_dict=necessity_artifact,
        high_friction=True,
        action_type="COOPERATE",
    )

    expected = "PASS (K-R exemption via Rule 1.5)"
    if passed and len(violations) == 0:
        return FixtureResult(
            name="Necessity Fixture",
            passed=True,
            expected=expected,
            actual="PASSED (Rule 1.5 exemption granted)",
            details="Rule 1.5 citation with institutional delay linkage correctly accepted",
        )
    else:
        actual = str([v.violation_type.name for v in violations])
        return FixtureResult(
            name="Necessity Fixture",
            passed=False,
            expected=expected,
            actual=actual,
            details=f"Unexpectedly rejected: {violations}",
        )


# ============================================================================
# Zeno Fixture
# ============================================================================

def test_zeno_fixture() -> FixtureResult:
    """
    Section 13.3: Zeno fixture

    Stuttering institution (N-1 blocks + 1 success repeatedly) → must terminate via throughput collapse.

    Test case:
    - Pattern: 7 blocked, 1 success, 7 blocked, 1 success, ...
    - After 25 steps: throughput = 2/25 = 0.08 < 0.20
    - Should terminate with E_INSTITUTIONAL_DOS
    """
    from ..runplans.anti_zeno import AntiZenoMonitor, TerminationType

    monitor = AntiZenoMonitor(n_limit=8, window_size=25, throughput_threshold=0.20)

    # Simulate stuttering pattern: 7 blocked, 1 success, repeat
    step_count = 0
    termination = None

    for cycle in range(4):  # 4 cycles = 32 steps, enough to fill window
        # 7 blocked steps
        for _ in range(7):
            termination = monitor.record_step(blocked=True)
            step_count += 1
            if termination.should_terminate:
                break
        if termination and termination.should_terminate:
            break

        # 1 success step
        termination = monitor.record_step(blocked=False)
        step_count += 1
        if termination.should_terminate:
            break

    expected = TerminationType.INSTITUTIONAL_DOS
    if termination and termination.should_terminate:
        if termination.termination_type == expected:
            return FixtureResult(
                name="Zeno Fixture",
                passed=True,
                expected=expected.value,
                actual=termination.termination_type.value,
                details=f"Terminated at step {step_count} with throughput {termination.throughput_ratio:.2%}",
            )
        else:
            return FixtureResult(
                name="Zeno Fixture",
                passed=False,
                expected=expected.value,
                actual=termination.termination_type.value,
                details=f"Wrong termination type at step {step_count}",
            )
    else:
        return FixtureResult(
            name="Zeno Fixture",
            passed=False,
            expected=expected.value,
            actual="NO TERMINATION",
            details=f"Should have terminated by step {step_count}, throughput = {termination.throughput_ratio:.2%}" if termination else "No termination check",
        )


# ============================================================================
# Degenerate Validity Fixture
# ============================================================================

def test_degenerate_validity_fixture() -> FixtureResult:
    """
    Section 13.4: Degenerate validity fixture

    Schema-valid but brittle artifact → agent survives or gridlocks; parser crash → E_INSTITUTION_FAILURE.

    Test case:
    - Artifact that passes schema validation but has minimal content
    - Under I2 profile with high failure rate
    - Should either gridlock cleanly OR report E_INSTITUTION_FAILURE
    - Should NOT crash the parser
    """
    from ..institution import (
        AdversarialInstitutionModel,
        InstitutionProfile,
        InstitutionOutcome,
    )

    # Create I2 (capricious) institution
    aim = AdversarialInstitutionModel(
        profile=InstitutionProfile.I2,
        episode_seed=12345,  # Fixed seed for determinism
    )

    # Degenerate but schema-valid artifact
    degenerate_artifact = {
        "action_claim": {"candidate_action_id": "WAIT"},
        "relevance": [],
        "required_preservations": [],
        "authorized_violations": [],
    }

    # Try to validate repeatedly until we get a failure
    failures = 0
    successes = 0
    crashes = 0

    for step in range(20):
        aim.set_step_context(step=step)
        try:
            is_valid, record = aim.validate(degenerate_artifact, step)
            if record.outcome == InstitutionOutcome.SUCCESS.value:
                successes += 1
            else:
                failures += 1
        except Exception as e:
            crashes += 1

    expected = "gridlock OR E_INSTITUTION_FAILURE (no crashes)"
    if crashes == 0:
        return FixtureResult(
            name="Degenerate Validity Fixture",
            passed=True,
            expected=expected,
            actual=f"No crashes: {successes} successes, {failures} failures",
            details="Degenerate artifact handled cleanly without parser crash",
        )
    else:
        return FixtureResult(
            name="Degenerate Validity Fixture",
            passed=False,
            expected=expected,
            actual=f"CRASHES: {crashes}",
            details="Parser crashed on degenerate artifact",
        )


# ============================================================================
# Run All Fixtures
# ============================================================================

def run_all_fixtures() -> Tuple[int, int, List[FixtureResult]]:
    """
    Run all v2.2 rule fixtures.

    Returns:
        Tuple of (passed_count, total_count, list of FixtureResult)
    """
    fixtures = [
        test_exhaustion_fixture,
        test_necessity_fixture,
        test_zeno_fixture,
        test_degenerate_validity_fixture,
    ]

    results = []
    passed = 0
    total = len(fixtures)

    for fixture_fn in fixtures:
        try:
            result = fixture_fn()
            results.append(result)
            if result.passed:
                passed += 1
        except Exception as e:
            results.append(FixtureResult(
                name=fixture_fn.__name__,
                passed=False,
                expected="No exception",
                actual=f"Exception: {e}",
                details=str(e),
            ))

    return passed, total, results


def print_fixture_results(results: List[FixtureResult]):
    """Print fixture results in a human-readable format."""
    print("\n" + "=" * 60)
    print("v2.2 Rule Fixture Results")
    print("=" * 60)

    for result in results:
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        print(f"\n{status}: {result.name}")
        print(f"  Expected: {result.expected}")
        print(f"  Actual:   {result.actual}")
        if result.details:
            print(f"  Details:  {result.details}")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print("\n" + "-" * 60)
    print(f"Summary: {passed}/{total} fixtures passed")
    print("=" * 60)


if __name__ == "__main__":
    passed, total, results = run_all_fixtures()
    print_fixture_results(results)
