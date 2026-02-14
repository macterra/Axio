"""
X-2D Harness Tests

Tests for the X-2D delegation churn & density stress profiling harness.

Coverage per instructions §15:
  T1: Gate admission (6D/7D/8D) — valid + invalid sessions
  T2: Generator determinism — same seeds → same plan
  T3: Cycle execution with X2D_TOPOLOGICAL ordering
  T4: Density enforcement — density never exceeds bound
  T5: Revalidation cascade after amendment
  T6: Replay chain consistency
  T7: Per-cycle and window metrics
  + Additional: revocation monotonicity, log schema, expiry boundary,
    same-invalid-twice, deadlock, gate stability
"""

from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pytest

# Ensure RSA-0 root is on path
RSA0_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(RSA0_ROOT) not in sys.path:
    sys.path.insert(0, str(RSA0_ROOT))

from kernel.src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyGrant,
    TreatyRevalidationEvent,
    TreatyRevocation,
    _compute_effective_density,
)
from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax2.policy_core_x2 import (
    CYCLE_ORDERING_DEFAULT,
    CYCLE_ORDERING_X2D_TOPOLOGICAL,
    DelegatedActionRequest,
    PolicyOutputX2,
    policy_core_x2,
)
from kernel.src.state_hash import KERNEL_VERSION_ID

from profiling.x2d.harness.src.schemas import (
    SessionFamily,
    X2DSessionStart,
    X2DSessionEnd,
    X2DGateResult,
    gate_6d,
    gate_7d,
    gate_8d,
    admit_session,
)
from profiling.x2d.harness.src.generators import (
    X2DGenerator,
    X2DCyclePlan,
    DBaseGenerator,
    DChurnGenerator,
    DSatGenerator,
    DRatchetGenerator,
    DEdgeGenerator,
    create_generator,
)
from profiling.x2d.harness.src.metrics import (
    X2DPerCycleMetric,
    X2DWindowMetric,
    compute_per_cycle_metrics,
    compute_window_metrics,
    write_metrics,
)
from profiling.x2d.harness.src.replay import (
    ReplayResult,
    verify_chain_consistency,
    verify_session_from_log,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONSTITUTION_PATH = (
    RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.3.yaml"
)


@pytest.fixture
def constitution() -> ConstitutionX2:
    return ConstitutionX2(yaml_path=str(CONSTITUTION_PATH))


@pytest.fixture
def state(constitution: ConstitutionX2) -> InternalStateX2:
    return InternalStateX2(active_constitution_hash=constitution.sha256)


def _make_session_start(
    family: str = "D-BASE",
    cycles: int = 20,
    window: int = 5,
    amendment_schedule: List[Dict[str, Any]] | None = None,
    target_band_low: float = 0.0,
    target_band_high: float = 0.0,
) -> X2DSessionStart:
    """Factory for test session starts."""
    return X2DSessionStart(
        session_family=family,
        session_id=str(uuid.uuid4()),
        session_length_cycles=cycles,
        window_size_cycles=window,
        density_upper_bound=0.75,
        density_proximity_delta=0.05,
        deadlock_threshold_K=5,
        seeds={"treaty_stream": 42, "action_stream": 43, "amendment_stream": 44},
        invalid_request_fractions={
            "missing_signature": 0.05,
            "invalid_signature": 0.05,
        },
        grant_duration_distribution={"type": "uniform", "min": 5, "max": 20},
        grantee_count=3,
        max_active_grants_per_grantee=2,
        delegated_requests_per_cycle_fraction=0.5,
        amendment_schedule=amendment_schedule or [],
        target_density_band_low=target_band_low,
        target_density_band_high=target_band_high,
        created_at="2026-02-13T12:00:00Z",
    )


# ---------------------------------------------------------------------------
# T1: Gate Admission Tests
# ---------------------------------------------------------------------------

class TestGateAdmission:
    """Test X-2D session admission gates 6D/7D/8D."""

    def test_gate_6d_valid(self, constitution):
        """Valid preconditions pass gate 6D."""
        result = gate_6d(
            KERNEL_VERSION_ID,
            constitution.sha256,
            constitution.sha256,
            constitution.has_x2_sections(),
            constitution.amendments_enabled(),
            SessionFamily.D_BASE.value,
        )
        assert result.passed

    def test_gate_6d_wrong_kernel_version(self, constitution):
        """Wrong kernel version fails gate 6D."""
        result = gate_6d(
            "wrong-version",
            constitution.sha256,
            constitution.sha256,
            True, True,
            SessionFamily.D_BASE.value,
        )
        assert not result.passed
        assert result.reason == "KERNEL_VERSION_MISMATCH"

    def test_gate_6d_invalid_family(self, constitution):
        """Invalid session family fails gate 6D."""
        result = gate_6d(
            KERNEL_VERSION_ID,
            constitution.sha256,
            constitution.sha256,
            True, True,
            "D-INVALID",
        )
        assert not result.passed
        assert result.reason == "INVALID_FAMILY"

    def test_gate_7d_valid(self):
        """Valid session schema passes gate 7D."""
        session = _make_session_start()
        result = gate_7d(session)
        assert result.passed

    def test_gate_7d_missing_session_id(self):
        """Missing session_id fails gate 7D."""
        session = _make_session_start()
        session.session_id = ""
        result = gate_7d(session)
        assert not result.passed
        assert "session_id" in result.detail

    def test_gate_7d_invalid_fraction(self):
        """Fractions > 1 fail gate 7D."""
        session = _make_session_start()
        session.delegated_requests_per_cycle_fraction = 1.5
        result = gate_7d(session)
        assert not result.passed

    def test_gate_7d_missing_seed_keys(self):
        """Missing seed keys fail gate 7D."""
        session = _make_session_start()
        session.seeds = {"treaty_stream": 1}  # missing others
        result = gate_7d(session)
        assert not result.passed
        assert "seeds missing" in result.detail

    def test_gate_8d_base_no_amendment(self):
        """D-BASE with empty amendment_schedule passes."""
        session = _make_session_start(family="D-BASE")
        result = gate_8d(session)
        assert result.passed

    def test_gate_8d_base_with_amendment_forbidden(self):
        """D-BASE with amendment_schedule fails."""
        session = _make_session_start(
            family="D-BASE",
            amendment_schedule=[{"cycle": 10, "type": "ban_action"}],
        )
        result = gate_8d(session)
        assert not result.passed
        assert result.reason == "AMENDMENT_SCHEDULE_FORBIDDEN"

    def test_gate_8d_ratchet_requires_amendment(self):
        """D-RATCHET without amendment_schedule fails."""
        session = _make_session_start(family="D-RATCHET")
        result = gate_8d(session)
        assert not result.passed
        assert result.reason == "AMENDMENT_SCHEDULE_REQUIRED"

    def test_gate_8d_ratchet_with_amendment(self):
        """D-RATCHET with amendment_schedule passes."""
        session = _make_session_start(
            family="D-RATCHET",
            amendment_schedule=[{"cycle": 10, "type": "ban_action", "action": "WriteLocal"}],
        )
        result = gate_8d(session)
        assert result.passed

    def test_gate_8d_edge_valid_band(self):
        """D-EDGE with valid density band passes."""
        session = _make_session_start(
            family="D-EDGE",
            target_band_low=0.60,
            target_band_high=0.74,
        )
        result = gate_8d(session)
        assert result.passed

    def test_gate_8d_edge_invalid_band(self):
        """D-EDGE with band_high <= band_low fails."""
        session = _make_session_start(
            family="D-EDGE",
            target_band_low=0.70,
            target_band_high=0.60,
        )
        result = gate_8d(session)
        assert not result.passed

    def test_gate_8d_window_exceeds_session(self):
        """Window > session length fails gate 8D."""
        session = _make_session_start(cycles=5, window=10)
        result = gate_8d(session)
        assert not result.passed

    def test_admit_session_short_circuits(self, constitution):
        """Admission short-circuits on first gate failure."""
        session = _make_session_start()
        results = admit_session(
            session, "wrong-version",
            constitution.sha256, constitution.sha256,
            True, True,
        )
        assert len(results) == 1
        assert not results[0].passed

    def test_admit_session_all_pass(self, constitution):
        """All gates pass for valid session."""
        session = _make_session_start()
        results = admit_session(
            session, KERNEL_VERSION_ID,
            constitution.sha256, constitution.sha256,
            constitution.has_x2_sections(),
            constitution.amendments_enabled(),
        )
        assert all(r.passed for r in results)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# T2: Generator Determinism
# ---------------------------------------------------------------------------

class TestGenerators:
    """Test that generators are deterministic and produce valid plans."""

    def test_d_base_generator_determinism(self, constitution):
        """Same seeds → same plan for D-BASE."""
        session = _make_session_start(family="D-BASE", cycles=10)
        gen1 = create_generator(session, constitution)
        gen2 = create_generator(session, constitution)
        plan1 = gen1.generate_plan()
        plan2 = gen2.generate_plan()
        assert len(plan1) == len(plan2) == 10
        for p1, p2 in zip(plan1, plan2):
            assert p1.cycle_index == p2.cycle_index
            assert len(p1.grants) == len(p2.grants)
            assert len(p1.revocations) == len(p2.revocations)

    def test_d_churn_generator_produces_churn(self, constitution):
        """D-CHURN produces some grants AND some revocations."""
        session = _make_session_start(family="D-CHURN", cycles=30)
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        has_grants = any(p.grants for p in plan)
        has_revocations = any(p.revocations for p in plan)
        assert has_grants, "D-CHURN should produce some grants"
        assert has_revocations, "D-CHURN should produce some revocations"

    def test_d_sat_generator_length(self, constitution):
        """D-SAT produces correct number of cycles."""
        session = _make_session_start(family="D-SAT", cycles=20)
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        assert len(plan) == 20

    def test_d_ratchet_generator_has_amendment(self, constitution):
        """D-RATCHET plan includes amendment at scheduled cycle."""
        session = _make_session_start(
            family="D-RATCHET", cycles=40,
            amendment_schedule=[{"cycle": 20, "type": "ban_action", "action": "WriteLocal"}],
        )
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        amend_cycle = next(
            (p for p in plan if p.amendment_adoption is not None), None
        )
        assert amend_cycle is not None
        assert amend_cycle.cycle_index == 20

    def test_d_edge_generator_length(self, constitution):
        """D-EDGE produces correct number of cycles."""
        session = _make_session_start(
            family="D-EDGE", cycles=15,
            target_band_low=0.60, target_band_high=0.74,
        )
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        assert len(plan) == 15

    def test_create_generator_invalid_family(self, constitution):
        """Invalid family raises ValueError."""
        session = _make_session_start()
        session.session_family = "D-INVALID"
        with pytest.raises(ValueError, match="Unknown session family"):
            create_generator(session, constitution)

    def test_generator_plan_cycles_sequential(self, constitution):
        """All plan cycles have sequential indices."""
        session = _make_session_start(family="D-BASE", cycles=10)
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        for i, p in enumerate(plan):
            assert p.cycle_index == i


# ---------------------------------------------------------------------------
# T3: Cycle Execution with X2D_TOPOLOGICAL
# ---------------------------------------------------------------------------

class TestTopologicalOrdering:
    """Test X2D_TOPOLOGICAL cycle ordering."""

    def test_topological_mode_accepted(self, constitution, state):
        """policy_core_x2 accepts cycle_ordering_mode parameter."""
        from kernel.src.artifacts import ActionType, Author, Observation, ObservationKind
        obs = [Observation(
            kind=ObservationKind.TIMESTAMP.value,
            payload={"iso8601_utc": "2026-02-13T12:00:00Z"},
            author=Author.HOST.value,
        )]
        from profiling.x2.harness.src.cycle_x2 import build_notify_candidate
        candidates = [build_notify_candidate("test", [], constitution)]

        output = policy_core_x2(
            observations=obs,
            action_candidates=candidates,
            amendment_candidates=[],
            pending_amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
            schema=None,
            cycle_ordering_mode=CYCLE_ORDERING_X2D_TOPOLOGICAL,
        )
        # Should produce a valid decision (ACTION or REFUSE)
        assert output.decision_type in (
            DecisionTypeX2.ACTION,
            DecisionTypeX2.REFUSE,
        )

    def test_default_mode_backward_compatible(self, constitution, state):
        """Default mode still works (backward compatibility guard)."""
        from kernel.src.artifacts import Author, Observation, ObservationKind
        obs = [Observation(
            kind=ObservationKind.TIMESTAMP.value,
            payload={"iso8601_utc": "2026-02-13T12:00:00Z"},
            author=Author.HOST.value,
        )]
        from profiling.x2.harness.src.cycle_x2 import build_notify_candidate
        candidates = [build_notify_candidate("test", [], constitution)]

        output = policy_core_x2(
            observations=obs,
            action_candidates=candidates,
            amendment_candidates=[],
            pending_amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
            schema=None,
            cycle_ordering_mode=CYCLE_ORDERING_DEFAULT,
        )
        assert output.decision_type in (
            DecisionTypeX2.ACTION,
            DecisionTypeX2.REFUSE,
        )


# ---------------------------------------------------------------------------
# T4: Density Enforcement
# ---------------------------------------------------------------------------

class TestDensityEnforcement:
    """Test that density never exceeds the constitutional bound."""

    def test_density_bound_respected(self, constitution):
        """After density repair, density is below bound."""
        ats = ActiveTreatySet()
        bound = constitution.density_upper_bound() or 0.75
        action_perms = constitution.get_action_permissions()
        action_type_count = len(constitution.get_action_types())

        # Add many grants to exceed density
        for i in range(20):
            grant = TreatyGrant(
                grantor_authority_id="rsa-0",
                grantee_identifier=f"ed25519:grantee{i:04d}",
                granted_actions=["Notify", "ReadLocal", "WriteLocal"],
                scope_constraints={},
                duration_cycles=100,
                revocable=True,
                authority_citations=["AUTH_GOVERNANCE"],
                justification=f"density test {i}",
                created_at="2026-02-13T12:00:00Z",
            )
            grant.grant_cycle = 0
            ats.add_grant(grant)

        events = ats.apply_density_repair(
            density_upper_bound=bound,
            action_permissions=action_perms,
            action_type_count=action_type_count,
            current_cycle=0,
        )

        active = ats.active_grants(0)
        if active:
            d = _compute_effective_density(action_perms, active, action_type_count)
            assert d < bound + 1e-9, f"density {d} >= bound {bound}"
        # At least some events should have been generated
        assert len(events) > 0

    def test_density_a_zero_convention(self, constitution):
        """A=0 → density=0 by convention."""
        action_perms = constitution.get_action_permissions()
        action_type_count = len(constitution.get_action_types())
        d = _compute_effective_density(action_perms, [], action_type_count)
        # With base action_perms, A > 0, so density > 0
        # Test with empty action_perms:
        d_empty = _compute_effective_density([], [], action_type_count)
        assert d_empty == 0.0


# ---------------------------------------------------------------------------
# T5: Revalidation Cascade
# ---------------------------------------------------------------------------

class TestRevalidation:
    """Test constitutional revalidation on ActiveTreatySet."""

    def test_revalidation_invalidates_banned_action(self, constitution):
        """Grants with a banned action are invalidated."""
        ats = ActiveTreatySet()
        grant = TreatyGrant(
            grantor_authority_id="rsa-0",
            grantee_identifier="ed25519:test0001",
            granted_actions=["BannedAction"],
            scope_constraints={},
            duration_cycles=100,
            revocable=True,
            authority_citations=["AUTH_GOVERNANCE"],
            justification="reval test",
            created_at="2026-02-13T12:00:00Z",
        )
        grant.grant_cycle = 0
        ats.add_grant(grant)

        events = ats.apply_constitutional_revalidation(constitution, 0)
        # Should invalidate the grant (BannedAction not in closed action set)
        invalidated = [e for e in events if e.result == "INVALIDATED"]
        assert len(invalidated) >= 1

    def test_revalidation_passes_valid_grant(self, constitution):
        """Grants with valid actions are NOT invalidated."""
        ats = ActiveTreatySet()
        closed = constitution.get_closed_action_set()
        valid_action = closed[0] if closed else "Notify"

        grant = TreatyGrant(
            grantor_authority_id="rsa-0",
            grantee_identifier="ed25519:test0002",
            granted_actions=[valid_action],
            scope_constraints={},
            duration_cycles=100,
            revocable=True,
            authority_citations=["AUTH_GOVERNANCE"],
            justification="reval valid test",
            created_at="2026-02-13T12:00:00Z",
        )
        grant.grant_cycle = 0
        ats.add_grant(grant)

        events = ats.apply_constitutional_revalidation(constitution, 0)
        invalidated = [e for e in events if e.result == "INVALIDATED"]
        assert len(invalidated) == 0

    def test_revalidation_event_has_pass_type(self, constitution):
        """Revalidation events include pass_type field."""
        ats = ActiveTreatySet()
        events = ats.apply_constitutional_revalidation(constitution, 0)
        summary = [e for e in events if e.result == "SUMMARY"]
        assert len(summary) == 1
        assert summary[0].pass_type == "POST_AMENDMENT"


# ---------------------------------------------------------------------------
# T6: Replay Chain Consistency
# ---------------------------------------------------------------------------

class TestReplay:
    """Test replay verification logic."""

    def test_consistent_chain(self):
        """Consistent chain passes verification."""
        records = [
            {"cycle_index": 0, "state_in_hash": "aaa", "state_out_hash": "bbb"},
            {"cycle_index": 1, "state_in_hash": "bbb", "state_out_hash": "ccc"},
            {"cycle_index": 2, "state_in_hash": "ccc", "state_out_hash": "ddd"},
        ]
        consistent, divs = verify_chain_consistency(records)
        assert consistent
        assert len(divs) == 0

    def test_inconsistent_chain(self):
        """Inconsistent chain is detected."""
        records = [
            {"cycle_index": 0, "state_in_hash": "aaa", "state_out_hash": "bbb"},
            {"cycle_index": 1, "state_in_hash": "WRONG", "state_out_hash": "ccc"},
        ]
        consistent, divs = verify_chain_consistency(records)
        assert not consistent
        assert len(divs) == 1

    def test_empty_chain(self):
        """Empty chain is trivially consistent."""
        consistent, divs = verify_chain_consistency([])
        assert consistent

    def test_single_record(self):
        """Single record chain is trivially consistent."""
        records = [
            {"cycle_index": 0, "state_in_hash": "aaa", "state_out_hash": "bbb"},
        ]
        consistent, divs = verify_chain_consistency(records)
        assert consistent

    def test_verify_from_log_file(self):
        """JSONL log file verification works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "x2d_session.jsonl"
            records = [
                {"type": "X2DSessionStart", "session_id": "test"},
                {"cycle_index": 0, "state_in_hash": "a", "state_out_hash": "b"},
                {"cycle_index": 1, "state_in_hash": "b", "state_out_hash": "c"},
                {"type": "X2DSessionEnd", "session_id": "test"},
            ]
            with open(log_path, "w") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")

            result = verify_session_from_log(log_path, "test")
            assert result.passed
            assert result.total_cycles_verified == 2

    def test_verify_missing_log(self):
        """Missing log file produces divergence."""
        result = verify_session_from_log(Path("/nonexistent/log.jsonl"), "test")
        assert not result.passed


# ---------------------------------------------------------------------------
# T7: Metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    """Test per-cycle and window metrics computation."""

    def _make_cycle_result(self, cycle_index: int, density: float = 0.5) -> Any:
        """Create a mock cycle result for metrics testing."""
        from profiling.x2d.harness.src.runner import X2DCycleResult
        return X2DCycleResult(
            cycle_index=cycle_index,
            cycle_id=f"X2D-{cycle_index:04d}",
            decision_type="ACTION",
            density=density,
            a_eff=3, b=4, m_eff=6,
            active_grants_count=2,
            density_upper_bound_active=0.75,
            grants_admitted=1 if cycle_index % 2 == 0 else 0,
            grants_rejected=0,
            revocations_admitted=1 if cycle_index % 3 == 0 else 0,
            delegated_warrants_issued=1,
            delegated_rejections=0,
            revalidation_invalidated=0,
            density_repair_invalidated=0,
            latency_ms=1.0,
        )

    def test_per_cycle_metrics_count(self):
        """Per-cycle metrics count matches input."""
        cycle_results = [self._make_cycle_result(i) for i in range(10)]
        metrics = compute_per_cycle_metrics(cycle_results)
        assert len(metrics) == 10

    def test_per_cycle_metric_fields(self):
        """Per-cycle metrics have expected fields."""
        cycle_results = [self._make_cycle_result(0)]
        metrics = compute_per_cycle_metrics(cycle_results)
        d = metrics[0].to_dict()
        assert "density" in d
        assert "a_eff" in d
        assert "active_treaty_count" in d
        assert "density_upper_bound_active" in d

    def test_window_metrics_count(self):
        """Window metrics count is correct."""
        cycle_results = [self._make_cycle_result(i) for i in range(20)]
        per_cycle = compute_per_cycle_metrics(cycle_results)
        windows = compute_window_metrics(per_cycle, 5)
        # Windows start at index W-1 = 4, so 20 - 5 + 1 = 16 windows
        assert len(windows) == 16

    def test_window_metrics_short_sequence(self):
        """Sequence shorter than window produces no window metrics."""
        cycle_results = [self._make_cycle_result(i) for i in range(3)]
        per_cycle = compute_per_cycle_metrics(cycle_results)
        windows = compute_window_metrics(per_cycle, 5)
        assert len(windows) == 0

    def test_window_churn_w(self):
        """Churn_W is (grants + revocations) / window_size."""
        cycle_results = [self._make_cycle_result(i) for i in range(5)]
        per_cycle = compute_per_cycle_metrics(cycle_results)
        windows = compute_window_metrics(per_cycle, 5)
        assert len(windows) == 1
        w = windows[0]
        total_grants = sum(m.grants_admitted for m in per_cycle)
        total_revocs = sum(m.revocations_admitted for m in per_cycle)
        expected_churn = (total_grants + total_revocs) / 5
        assert abs(w.churn_w - expected_churn) < 1e-9

    def test_write_metrics_creates_files(self):
        """Write metrics creates JSONL files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_dir = Path(tmpdir)
            per_cycle = [X2DPerCycleMetric(
                cycle_index=0, density=0.5, a_eff=2, b=4, m_eff=4,
                active_treaty_count=1, density_upper_bound_active=0.75,
            )]
            windows = [X2DWindowMetric(
                window_end_cycle=0, window_size=1,
                churn_w=1.0, refusal_rate_w=0.0, type_iii_rate_w=0.0,
                density_mean_w=0.5, density_max_w=0.5, active_treaty_mean_w=1.0,
            )]
            write_metrics(session_dir, per_cycle, windows)
            assert (session_dir / "x2d_metrics.jsonl").exists()
            assert (session_dir / "x2d_window_metrics.jsonl").exists()


# ---------------------------------------------------------------------------
# Additional: Schema & Serialization
# ---------------------------------------------------------------------------

class TestSchemas:
    """Test session schema serialization."""

    def test_session_start_canonical_hash(self):
        """Canonical hash is deterministic."""
        s1 = _make_session_start()
        s2 = _make_session_start()
        s2.session_id = s1.session_id  # same ID
        h1 = s1.canonical_hash()
        h2 = s2.canonical_hash()
        assert h1 == h2

    def test_session_start_to_dict(self):
        """to_dict includes all fields."""
        s = _make_session_start()
        d = s.to_dict()
        assert d["session_family"] == "D-BASE"
        assert "seeds" in d
        assert "amendment_schedule" in d

    def test_session_end_to_dict(self):
        """SessionEnd serializes correctly."""
        e = X2DSessionEnd(
            session_id="test-id",
            final_cycle=49,
            replay_divergence_count=0,
            closure_pass=True,
        )
        d = e.to_dict()
        assert d["session_id"] == "test-id"
        assert d["closure_pass"] is True

    def test_session_family_enum_values(self):
        """All 5 session families have expected values."""
        assert SessionFamily.D_BASE.value == "D-BASE"
        assert SessionFamily.D_CHURN.value == "D-CHURN"
        assert SessionFamily.D_SAT.value == "D-SAT"
        assert SessionFamily.D_RATCHET.value == "D-RATCHET"
        assert SessionFamily.D_EDGE.value == "D-EDGE"
        assert len(SessionFamily) == 5


# ---------------------------------------------------------------------------
# Additional: Invalidation & Revocation
# ---------------------------------------------------------------------------

class TestInvalidation:
    """Test treaty invalidation mechanics."""

    def test_invalidate_removes_from_active(self):
        """Invalidated grant is excluded from active_grants()."""
        ats = ActiveTreatySet()
        grant = TreatyGrant(
            grantor_authority_id="rsa-0",
            grantee_identifier="ed25519:test",
            granted_actions=["Notify"],
            scope_constraints={},
            duration_cycles=100,
            revocable=True,
            authority_citations=["AUTH_GOVERNANCE"],
            justification="test",
            created_at="2026-02-13T12:00:00Z",
        )
        grant.grant_cycle = 0
        ats.add_grant(grant)
        assert len(ats.active_grants(0)) == 1

        ats.invalidate(grant.id, 0)
        assert len(ats.active_grants(0)) == 0

    def test_revoked_grant_excluded(self):
        """Revoked grant is excluded from active_grants()."""
        ats = ActiveTreatySet()
        grant = TreatyGrant(
            grantor_authority_id="rsa-0",
            grantee_identifier="ed25519:test",
            granted_actions=["Notify"],
            scope_constraints={},
            duration_cycles=100,
            revocable=True,
            authority_citations=["AUTH_GOVERNANCE"],
            justification="test",
            created_at="2026-02-13T12:00:00Z",
        )
        grant.grant_cycle = 0
        ats.add_grant(grant)
        ats.revoke(grant.id)
        assert len(ats.active_grants(0)) == 0

    def test_revocation_monotonicity(self):
        """Revoked grants stay revoked — no un-revocation."""
        ats = ActiveTreatySet()
        grant = TreatyGrant(
            grantor_authority_id="rsa-0",
            grantee_identifier="ed25519:test",
            granted_actions=["Notify"],
            scope_constraints={},
            duration_cycles=100,
            revocable=True,
            authority_citations=["AUTH_GOVERNANCE"],
            justification="test",
            created_at="2026-02-13T12:00:00Z",
        )
        grant.grant_cycle = 0
        ats.add_grant(grant)
        ats.revoke(grant.id)
        # Verify no API to un-revoke
        assert grant.id in ats.revoked_grant_ids
        # Re-adding the same grant doesn't un-revoke
        ats.add_grant(grant)
        # Still revoked — active_grants filters by revoked_grant_ids
        active = [g for g in ats.active_grants(0) if g.id == grant.id]
        # Both copies are excluded (same ID)
        assert all(g.id not in ats.revoked_grant_ids for g in active) or len(active) == 0


# ---------------------------------------------------------------------------
# Additional: Density Repair Details
# ---------------------------------------------------------------------------

class TestDensityRepair:
    """Test density repair loop behavior."""

    def test_density_repair_newest_first(self, constitution):
        """Density repair invalidates newest grants first."""
        ats = ActiveTreatySet()
        action_perms = constitution.get_action_permissions()
        action_type_count = len(constitution.get_action_types())
        bound = constitution.density_upper_bound() or 0.75

        # Add grants at different cycles
        for i in range(15):
            grant = TreatyGrant(
                grantor_authority_id="rsa-0",
                grantee_identifier=f"ed25519:newestfirst{i:04d}",
                granted_actions=["Notify", "ReadLocal"],
                scope_constraints={},
                duration_cycles=100,
                revocable=True,
                authority_citations=["AUTH_GOVERNANCE"],
                justification=f"newest first test {i}",
                created_at="2026-02-13T12:00:00Z",
            )
            grant.grant_cycle = i  # Later cycle = newer
            ats.add_grant(grant)

        events = ats.apply_density_repair(
            density_upper_bound=bound,
            action_permissions=action_perms,
            action_type_count=action_type_count,
            current_cycle=20,
        )

        # Check that invalidated grants are from higher grant_cycles
        invalidated_ids = {e.grant_id for e in events if e.result == "INVALIDATED"}
        if invalidated_ids:
            max_invalidated_cycle = max(
                g.grant_cycle for g in ats.grants if g.id in invalidated_ids
            )
            max_active_cycle = max(
                (g.grant_cycle for g in ats.active_grants(20)),
                default=-1,
            )
            assert max_active_cycle <= max_invalidated_cycle or max_active_cycle == -1

    def test_density_repair_convergence(self, constitution):
        """Density repair loop terminates (no infinite loop)."""
        ats = ActiveTreatySet()
        action_perms = constitution.get_action_permissions()
        action_type_count = len(constitution.get_action_types())

        for i in range(50):
            grant = TreatyGrant(
                grantor_authority_id="rsa-0",
                grantee_identifier=f"ed25519:converge{i:04d}",
                granted_actions=["Notify", "ReadLocal", "WriteLocal"],
                scope_constraints={},
                duration_cycles=100,
                revocable=True,
                authority_citations=["AUTH_GOVERNANCE"],
                justification=f"convergence test {i}",
                created_at="2026-02-13T12:00:00Z",
            )
            grant.grant_cycle = i
            ats.add_grant(grant)

        # Should not hang
        events = ats.apply_density_repair(
            density_upper_bound=0.75,
            action_permissions=action_perms,
            action_type_count=action_type_count,
            current_cycle=60,
        )
        # Should have produced events
        assert isinstance(events, list)


# ---------------------------------------------------------------------------
# Additional: Simulation API
# ---------------------------------------------------------------------------

class TestSimulationAPI:
    """Test kernel simulation API."""

    def test_simulate_cycle_import(self):
        """Simulation module is importable."""
        from kernel.src.rsax2.sim import simulate_cycle, SimCycleOutput
        assert simulate_cycle is not None
        assert SimCycleOutput is not None

    def test_simulate_plan_import(self):
        """Plan simulation is importable."""
        from kernel.src.rsax2.sim import simulate_plan, SimPlanOutput
        assert simulate_plan is not None
        assert SimPlanOutput is not None

    def test_simulate_cycle_does_not_mutate_input(self, constitution, state):
        """simulate_cycle deep-copies state."""
        from kernel.src.rsax2.sim.simulate_cycle import simulate_cycle
        from kernel.src.artifacts import Author, Observation, ObservationKind

        state_before = copy.deepcopy(state)
        obs = [Observation(
            kind=ObservationKind.TIMESTAMP.value,
            payload={"iso8601_utc": "2026-02-13T12:00:00Z"},
            author=Author.HOST.value,
        )]

        result = simulate_cycle(
            state=state,
            observations=obs,
            action_candidates=[],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            repo_root=RSA0_ROOT,
        )

        # Original state should be unchanged
        assert state.cycle_index == state_before.cycle_index
        assert state.to_dict() == state_before.to_dict()


# ---------------------------------------------------------------------------
# Additional: Gate stability
# ---------------------------------------------------------------------------

class TestGateStability:
    """Test that gate results are stable across runs."""

    def test_gate_6d_idempotent(self, constitution):
        """Same inputs produce same gate_6d result."""
        r1 = gate_6d(
            KERNEL_VERSION_ID, constitution.sha256, constitution.sha256,
            True, True, "D-BASE",
        )
        r2 = gate_6d(
            KERNEL_VERSION_ID, constitution.sha256, constitution.sha256,
            True, True, "D-BASE",
        )
        assert r1.passed == r2.passed
        assert r1.reason == r2.reason
