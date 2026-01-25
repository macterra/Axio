"""v2.2 Tests Module

Contains rule fixtures, determinism tests, and unit tests for v2.2 components.

Section 3.1: Determinism Gate
- StubPlan S0: Canned JAF sequence for replay validation
- Determinism gate test: Run harness twice, assert identical results

Rule fixtures (from spec Section 13):
- Exhaustion fixture: high friction → simplified justification → E_EXHAUSTION_DELEGATION
- Necessity fixture: institutional delay + Rule 1.5 + existential threat → must pass
- Zeno fixture: N-1 blocks + 1 success stuttering → throughput collapse termination
- Degenerate validity fixture: schema-valid but brittle → gridlock or E_INSTITUTION_FAILURE
"""

from .rule_fixtures import (
    test_exhaustion_fixture,
    test_necessity_fixture,
    test_zeno_fixture,
    test_degenerate_validity_fixture,
    run_all_fixtures,
    print_fixture_results,
)

from .determinism_stub import (
    StubGenerator,
    STUB_PLAN_S0,
    get_stub_jaf_for_step,
    CannedJAF,
    StepSnapshot,
    RunSnapshot,
    compare_snapshots,
)

from .determinism_gate import (
    run_determinism_gate,
)

__all__ = [
    # Rule fixtures
    "test_exhaustion_fixture",
    "test_necessity_fixture",
    "test_zeno_fixture",
    "test_degenerate_validity_fixture",
    "run_all_fixtures",
    "print_fixture_results",
    # Determinism gate
    "StubGenerator",
    "STUB_PLAN_S0",
    "get_stub_jaf_for_step",
    "CannedJAF",
    "StepSnapshot",
    "RunSnapshot",
    "compare_snapshots",
    "run_determinism_gate",
]
