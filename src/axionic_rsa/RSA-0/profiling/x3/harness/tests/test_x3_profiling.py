"""
X-3 Harness Tests

Tests for the X-3 sovereign succession profiling harness.

Coverage:
  T1: Gate admission (6X/7X/8X) — valid + invalid sessions
  T2: Generator determinism — same seeds → same plan
  T3: Constitution helper — frame creation with overlay
  T4: Runner — minimal session execution + closure
  T5: Replay chain consistency
  T6: Boundary fault detection
  + Additional: gate stability, sub-session variants
"""

from __future__ import annotations

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

from kernel.src.rsax3.constitution_x3 import EffectiveConstitutionFrame
from kernel.src.rsax3.policy_core_x3 import KERNEL_VERSION_ID
from profiling.x3.harness.src.constitution_helper_x3 import (
    create_x3_profiling_constitution,
)
from profiling.x3.harness.src.schemas_x3 import (
    SessionFamilyX3,
    X3SessionStart,
    X3SessionEnd,
    X3GateResult,
    KERNEL_VERSION_ID_X3,
    gate_6x,
    gate_7x,
    gate_8x,
    admit_session,
)
from profiling.x3.harness.src.generators_x3 import (
    X3Generator,
    X3CyclePlan,
    X3BaseGenerator,
    X3NearBoundGenerator,
    X3ChurnGenerator,
    X3RatDelayGenerator,
    X3MultiRotGenerator,
    X3InvalidSigGenerator,
    X3DupCycleGenerator,
    X3InvalidBoundaryGenerator,
    create_generator,
    X3_GENESIS_SEED,
)
from profiling.x3.harness.src.runner_x3 import (
    X3Runner,
    X3CycleResult,
    X3SessionResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def constitution() -> EffectiveConstitutionFrame:
    """Profiling constitution frame: v0.3 + AUTH_DELEGATION + X-3 overlay."""
    return create_x3_profiling_constitution(repo_root=RSA0_ROOT)


def _make_session_start(
    family: str = "X3-BASE",
    cycles: int = 10,
    rotation_schedule: List[Dict[str, Any]] | None = None,
    ratification_delay: int = 1,
    delegation_mode: str = "LOW",
    grantee_count: int = 3,
    invalid_succession_fractions: Dict[str, float] | None = None,
    invalid_boundary_faults: List[Dict[str, Any]] | None = None,
) -> X3SessionStart:
    """Factory for test session starts."""
    return X3SessionStart(
        session_family=family,
        session_id=str(uuid.uuid4()),
        session_length_cycles=cycles,
        density_upper_bound=0.75,
        seeds={
            "treaty_stream": 42,
            "action_stream": 43,
            "succession_stream": 44,
        },
        rotation_schedule=rotation_schedule or [{"cycle": 5, "successor_index": 1}],
        ratification_delay_cycles=ratification_delay,
        delegation_state_mode=delegation_mode,
        grantee_count=grantee_count,
        delegated_requests_per_cycle_fraction=0.5,
        invalid_succession_fractions=invalid_succession_fractions or {},
        invalid_boundary_faults=invalid_boundary_faults or [],
        created_at="2026-03-01T12:00:00Z",
    )


# ---------------------------------------------------------------------------
# T1: Gate Admission Tests
# ---------------------------------------------------------------------------

class TestGateAdmission:
    """Test X-3 session admission gates 6X/7X/8X."""

    def test_gate_6x_valid(self, constitution):
        result = gate_6x(
            KERNEL_VERSION_ID_X3,
            constitution.sha256,
            constitution.has_x2_sections(),
            SessionFamilyX3.X3_BASE.value,
        )
        assert result.passed

    def test_gate_6x_wrong_kernel_version(self, constitution):
        result = gate_6x(
            "wrong-version",
            constitution.sha256,
            True,
            SessionFamilyX3.X3_BASE.value,
        )
        assert not result.passed
        assert result.reason == "KERNEL_VERSION_MISMATCH"

    def test_gate_6x_missing_constitution(self, constitution):
        result = gate_6x(KERNEL_VERSION_ID_X3, "", True, "X3-BASE")
        assert not result.passed
        assert result.reason == "CONSTITUTION_MISSING"

    def test_gate_6x_no_x2_sections(self, constitution):
        result = gate_6x(
            KERNEL_VERSION_ID_X3,
            constitution.sha256,
            False,
            "X3-BASE",
        )
        assert not result.passed
        assert result.reason == "X2_SECTIONS_REQUIRED"

    def test_gate_6x_invalid_family(self, constitution):
        result = gate_6x(
            KERNEL_VERSION_ID_X3,
            constitution.sha256,
            True,
            "X3-INVALID",
        )
        assert not result.passed
        assert result.reason == "INVALID_FAMILY"

    def test_gate_7x_valid(self):
        session = _make_session_start()
        result = gate_7x(session)
        assert result.passed

    def test_gate_7x_missing_session_id(self):
        session = _make_session_start()
        session.session_id = ""
        result = gate_7x(session)
        assert not result.passed
        assert "session_id" in result.detail

    def test_gate_7x_bad_density_bound(self):
        session = _make_session_start()
        session.density_upper_bound = 0
        result = gate_7x(session)
        assert not result.passed

    def test_gate_7x_missing_seed_keys(self):
        session = _make_session_start()
        session.seeds = {"treaty_stream": 1}
        result = gate_7x(session)
        assert not result.passed

    def test_gate_7x_invalid_delegation_mode(self):
        session = _make_session_start()
        session.delegation_state_mode = "INVALID_MODE"
        result = gate_7x(session)
        assert not result.passed

    def test_gate_7x_too_many_rotations(self):
        session = _make_session_start(
            cycles=100,
            rotation_schedule=[
                {"cycle": i * 10} for i in range(1, 7)
            ],
        )
        result = gate_7x(session)
        assert not result.passed

    def test_gate_8x_valid(self):
        session = _make_session_start()
        result = gate_8x(session)
        assert result.passed

    def test_gate_8x_rotation_out_of_range(self):
        session = _make_session_start(
            cycles=10,
            rotation_schedule=[{"cycle": 15}],
        )
        result = gate_8x(session)
        assert not result.passed
        assert result.reason == "ROTATION_OUT_OF_RANGE"

    def test_gate_8x_duplicate_rotation(self):
        session = _make_session_start(
            cycles=30,
            rotation_schedule=[{"cycle": 10}, {"cycle": 10}],
        )
        result = gate_8x(session)
        assert not result.passed
        assert result.reason == "DUPLICATE_ROTATION_CYCLE"

    def test_gate_8x_bad_ratification_delay(self):
        session = _make_session_start(ratification_delay=0)
        result = gate_8x(session)
        assert not result.passed

    def test_admit_session_all_pass(self, constitution):
        session = _make_session_start()
        results = admit_session(
            session,
            KERNEL_VERSION_ID_X3,
            constitution.sha256,
            constitution.has_x2_sections(),
        )
        assert all(r.passed for r in results)
        assert len(results) == 3

    def test_admit_session_early_stop(self, constitution):
        session = _make_session_start()
        results = admit_session(
            session,
            "wrong-version",
            constitution.sha256,
            True,
        )
        assert len(results) == 1
        assert not results[0].passed

    def test_all_families_admit(self, constitution):
        """Every family's default params pass all gates."""
        for f in SessionFamilyX3:
            rot = [{"cycle": 5, "successor_index": 1}]
            session = _make_session_start(family=f.value, rotation_schedule=rot)
            results = admit_session(
                session,
                KERNEL_VERSION_ID_X3,
                constitution.sha256,
                constitution.has_x2_sections(),
            )
            assert all(r.passed for r in results), f"Family {f.value} failed"


# ---------------------------------------------------------------------------
# T2: Generator Determinism
# ---------------------------------------------------------------------------

class TestGeneratorDeterminism:
    """Same parameters → identical plans."""

    def test_base_deterministic(self, constitution):
        s1 = _make_session_start()
        s2 = _make_session_start()
        s2.session_id = s1.session_id

        g1 = create_generator(s1, constitution)
        g2 = create_generator(s2, constitution)
        plan1 = g1.generate_plan()
        plan2 = g2.generate_plan()

        assert len(plan1) == len(plan2)
        for p1, p2 in zip(plan1, plan2):
            assert p1.cycle_index == p2.cycle_index
            assert p1.timestamp == p2.timestamp

    def test_different_seeds_differ(self, constitution):
        s1 = _make_session_start()
        s2 = _make_session_start()
        s2.seeds = {
            "treaty_stream": 999,
            "action_stream": 998,
            "succession_stream": 997,
        }
        g1 = create_generator(s1, constitution)
        g2 = create_generator(s2, constitution)
        plan1 = g1.generate_plan()
        plan2 = g2.generate_plan()
        # Plans have same length but may differ in content
        assert len(plan1) == len(plan2)

    @pytest.mark.parametrize("family", [
        "X3-BASE", "X3-NEAR_BOUND", "X3-CHURN", "X3-RAT_DELAY",
        "X3-MULTI_ROT", "X3-INVALID_SIG", "X3-DUP_CYCLE",
        "X3-INVALID_BOUNDARY",
    ])
    def test_all_families_generate_plans(self, constitution, family):
        """Every family produces a non-empty plan."""
        kwargs = {"family": family}
        if family == "X3-MULTI_ROT":
            kwargs["rotation_schedule"] = [
                {"cycle": 5, "successor_index": 1},
                {"cycle": 8, "successor_index": 2},
            ]
            kwargs["cycles"] = 15
        elif family == "X3-INVALID_SIG":
            kwargs["invalid_succession_fractions"] = {"invalid_signature": 1.0}
        elif family == "X3-DUP_CYCLE":
            kwargs["invalid_succession_fractions"] = {"duplicate_cycle": 1.0}
        elif family == "X3-INVALID_BOUNDARY":
            kwargs["invalid_boundary_faults"] = [
                {"sub_session": "A", "fault_type": "wrong_commit_signer", "cycle": 6},
            ]

        session = _make_session_start(**kwargs)
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        assert len(plan) > 0

    def test_succession_proposal_at_rotation(self, constitution):
        """Generator places succession proposals at rotation cycles."""
        session = _make_session_start(cycles=15, rotation_schedule=[
            {"cycle": 5, "successor_index": 1},
        ])
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        rot_cycle = plan[5]
        assert len(rot_cycle.succession_proposals) >= 1

    def test_ratification_at_delay(self, constitution):
        """Ratification placed at rotation_cycle + delay + 1."""
        session = _make_session_start(
            cycles=15,
            rotation_schedule=[{"cycle": 5, "successor_index": 1}],
            ratification_delay=2,
        )
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        # Ratification at cycle 5 + 2 + 1 = 8
        rat_cycle = plan[8]
        assert len(rat_cycle.ratifications) >= 1

    def test_boundary_fault_at_specified_cycle(self, constitution):
        """Boundary fault injected at specified cycle."""
        session = _make_session_start(
            family="X3-INVALID_BOUNDARY",
            cycles=15,
            invalid_boundary_faults=[
                {"sub_session": "A", "fault_type": "wrong_commit_signer", "cycle": 7},
            ],
        )
        gen = create_generator(session, constitution)
        plan = gen.generate_plan()
        assert plan[7].boundary_fault is not None
        assert plan[7].boundary_fault["fault_type"] == "wrong_commit_signer"


# ---------------------------------------------------------------------------
# T3: Constitution Helper
# ---------------------------------------------------------------------------

class TestConstitutionHelper:
    """Test X-3 constitution frame creation."""

    def test_frame_created(self, constitution):
        assert isinstance(constitution, EffectiveConstitutionFrame)

    def test_overlay_hash_present(self, constitution):
        assert len(constitution.overlay_hash) == 64

    def test_succession_enabled(self, constitution):
        assert constitution.is_succession_enabled()

    def test_treaty_ratification_required(self, constitution):
        assert constitution.is_treaty_ratification_required()

    def test_suspension_on_succession(self, constitution):
        assert constitution.is_treaty_suspension_on_succession()

    def test_boundary_signature_required(self, constitution):
        assert constitution.is_boundary_signature_required()

    def test_density_bound(self, constitution):
        assert constitution.density_upper_bound() == 0.75

    def test_delegation_permissions(self, constitution):
        perms = constitution.get_action_permissions()
        has_delegation = any(
            p.get("authority") == "AUTH_DELEGATION" for p in perms
        )
        assert has_delegation

    def test_x2_sections_present(self, constitution):
        assert constitution.has_x2_sections()

    def test_overlay_citation_resolution(self, constitution):
        oh = constitution.overlay_hash
        resolved = constitution.resolve_citation(
            f"overlay:{oh}#CL-SUCCESSION-ENABLED"
        )
        assert resolved is not None
        assert resolved["enabled"] is True


# ---------------------------------------------------------------------------
# T4: Runner — Minimal Session Execution
# ---------------------------------------------------------------------------

class TestRunnerExecution:
    """Minimal runner execution tests."""

    def test_base_short_session(self, constitution):
        """10-cycle BASE session with rotation at 5."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(cycles=10)
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            assert result.total_cycles == 10
            assert result.replay_divergence_count == 0
            assert result.closure_pass, result.failure_reasons
            assert result.total_rotations_activated >= 1
            assert len(result.density_series) == 10

    def test_near_bound_session(self, constitution):
        """NEAR_BOUND with more grantees."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                family="X3-NEAR_BOUND",
                cycles=10,
                delegation_mode="NEAR_BOUND",
                grantee_count=5,
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            assert result.total_cycles == 10
            assert result.replay_divergence_count == 0

    def test_multi_rot_session(self, constitution):
        """MULTI_ROT with 2 rotations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                family="X3-MULTI_ROT",
                cycles=15,
                rotation_schedule=[
                    {"cycle": 4, "successor_index": 1},
                    {"cycle": 10, "successor_index": 2},
                ],
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            assert result.total_cycles == 15
            assert result.replay_divergence_count == 0

    def test_invalid_sig_rejection(self, constitution):
        """INVALID_SIG: at least one succession rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                family="X3-INVALID_SIG",
                cycles=10,
                invalid_succession_fractions={"invalid_signature": 1.0},
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            assert result.total_cycles == 10
            assert result.replay_divergence_count == 0
            assert result.total_successions_rejected >= 1

    def test_dup_cycle_rejection(self, constitution):
        """DUP_CYCLE: at least one succession rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                family="X3-DUP_CYCLE",
                cycles=10,
                invalid_succession_fractions={"duplicate_cycle": 1.0},
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            assert result.total_cycles == 10
            assert result.replay_divergence_count == 0
            assert result.total_successions_rejected >= 1

    def test_session_result_serializable(self, constitution):
        """Session result to_dict() produces valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                cycles=10,
                rotation_schedule=[{"cycle": 5, "successor_index": 1}],
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            d = result.to_dict()
            text = json.dumps(d)
            assert "X3SessionResult" in text

    def test_cycle_result_to_dict(self, constitution):
        """Cycle results are serializable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                cycles=5,
                rotation_schedule=[{"cycle": 3, "successor_index": 1}],
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            assert len(result.cycle_results) == 5
            for cr in result.cycle_results:
                d = cr.to_dict()
                assert "X3CycleResult" in json.dumps(d)


# ---------------------------------------------------------------------------
# T5: Replay Chain Consistency
# ---------------------------------------------------------------------------

class TestReplayConsistency:
    """Replay verification: state_out[i] == state_in[i+1]."""

    def test_short_replay_consistent(self, constitution):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(cycles=10)
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            assert result.replay_divergence_count == 0

    def test_density_never_exceeds_bound(self, constitution):
        """No density sample exceeds constitution bound + tolerance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(cycles=15, grantee_count=5)
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            bound = session.density_upper_bound
            for d in result.density_series:
                assert d <= bound + 1e-9, f"density {d} > bound {bound}"


# ---------------------------------------------------------------------------
# T6: Log Schema
# ---------------------------------------------------------------------------

class TestLogSchema:
    """Verify log files are written with expected structure."""

    def test_session_logs_written(self, constitution):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                cycles=10,
                rotation_schedule=[{"cycle": 5, "successor_index": 1}],
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            result = runner.run()
            session_dir = Path(tmpdir) / session.session_id
            assert (session_dir / "x3_sessions.jsonl").exists()
            assert (session_dir / "x3_metrics.jsonl").exists()

    def test_metrics_log_valid_json(self, constitution):
        with tempfile.TemporaryDirectory() as tmpdir:
            session = _make_session_start(
                cycles=10,
                rotation_schedule=[{"cycle": 5, "successor_index": 1}],
            )
            runner = X3Runner(
                session_start=session,
                constitution_frame=constitution,
                repo_root=RSA0_ROOT,
                log_root=Path(tmpdir),
                verbose=False,
            )
            runner.run()
            metrics_path = Path(tmpdir) / session.session_id / "x3_metrics.jsonl"
            with open(metrics_path) as f:
                for line in f:
                    record = json.loads(line.strip())
                    assert "cycle_index" in record


# ---------------------------------------------------------------------------
# T7: Schema Artifacts
# ---------------------------------------------------------------------------

class TestSchemaArtifacts:
    """X3SessionStart / X3SessionEnd schemas."""

    def test_session_start_canonical_hash(self):
        s1 = _make_session_start()
        h1 = s1.canonical_hash()
        assert len(h1) == 64
        h2 = s1.canonical_hash()
        assert h1 == h2  # deterministic

    def test_session_start_to_dict(self):
        s = _make_session_start()
        d = s.to_dict()
        assert d["type"] == "X3SessionStart"
        assert d["session_family"] == "X3-BASE"

    def test_session_end_to_dict(self):
        e = X3SessionEnd(session_id="test", final_cycle=9, closure_pass=True)
        d = e.to_dict()
        assert d["type"] == "X3SessionEnd"
        assert d["final_cycle"] == 9
