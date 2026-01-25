"""v2.3 Test Suite"""

from .rule_fixtures import (
    TestFixture,
    FixtureCategory,
    ALL_FIXTURES,
    BEHAVIORAL_CAPTURE_FIXTURES,
    DEFENSIVE_GRIDLOCK_FIXTURES,
    MANIPULATED_GRIDLOCK_FIXTURES,
    SCOPE_BREACH_FIXTURES,
    SILENT_FAILURE_FIXTURES,
    get_fixtures_by_category,
    get_fixture_by_id,
)

from .determinism_gate import (
    SAMDeterminismGate,
    DeterminismCheckResult,
    generate_test_signals,
    run_determinism_gate_all_profiles,
)

__all__ = [
    # Fixtures
    "TestFixture",
    "FixtureCategory",
    "ALL_FIXTURES",
    "BEHAVIORAL_CAPTURE_FIXTURES",
    "DEFENSIVE_GRIDLOCK_FIXTURES",
    "MANIPULATED_GRIDLOCK_FIXTURES",
    "SCOPE_BREACH_FIXTURES",
    "SILENT_FAILURE_FIXTURES",
    "get_fixtures_by_category",
    "get_fixture_by_id",
    # Determinism gate
    "SAMDeterminismGate",
    "DeterminismCheckResult",
    "generate_test_signals",
    "run_determinism_gate_all_profiles",
]
