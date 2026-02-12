"""
X-1 Harness Tests

Tests the end-to-end X-1 profiling harness:
  - Scenario construction
  - Cycle execution
  - Full session run
  - Report generation
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

# Ensure RSA-0 root is on path
# tests → harness → x1 → profiling → RSA-0
RSA0_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
import sys
if str(RSA0_ROOT) not in sys.path:
    sys.path.insert(0, str(RSA0_ROOT))

from kernel.src.rsax1.artifacts_x1 import (
    AmendmentProposal,
    DecisionTypeX1,
    InternalStateX1,
)
from kernel.src.rsax1.constitution_x1 import ConstitutionX1

from profiling.x1.harness.src.scenarios import (
    build_adversarial_cooling_reduction,
    build_adversarial_eck_removal,
    build_adversarial_physics_claim,
    build_adversarial_scope_collapse,
    build_adversarial_threshold_reduction,
    build_adversarial_universal_auth,
    build_adversarial_wildcard,
    build_all_adversarial,
    build_lawful_tighten_ratchet,
    build_lawful_trivial,
)
from profiling.x1.harness.src.cycle_x1 import (
    X1CycleResult,
    build_notify_candidate,
    run_x1_cycle,
)
from profiling.x1.harness.src.runner_x1 import (
    X1Runner,
    X1SessionConfig,
    X1SessionResult,
)
from profiling.x1.harness.src.report_x1 import generate_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONSTITUTION_PATH = (
    RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.2.yaml"
)
SCHEMA_PATH = (
    RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.2.schema.json"
)


@pytest.fixture
def constitution() -> ConstitutionX1:
    return ConstitutionX1(yaml_path=str(CONSTITUTION_PATH))


@pytest.fixture
def schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def state(constitution: ConstitutionX1) -> InternalStateX1:
    return InternalStateX1(active_constitution_hash=constitution.sha256)


# ---------------------------------------------------------------------------
# Scenario tests
# ---------------------------------------------------------------------------

class TestScenarios:
    """Test that scenario builders produce valid proposals."""

    def test_lawful_trivial_produces_valid_proposal(self, constitution):
        s = build_lawful_trivial(constitution)
        assert s.expected_outcome == "ADOPT"
        assert s.proposal.prior_constitution_hash == constitution.sha256
        assert s.proposal.proposed_constitution_yaml
        assert s.proposal.proposed_constitution_hash
        assert len(s.proposal.authority_citations) >= 2

    def test_lawful_tighten_ratchet(self, constitution):
        s = build_lawful_tighten_ratchet(constitution)
        assert s.expected_outcome == "ADOPT"
        assert "RATCHET" in s.scenario_id

    def test_adversarial_universal_auth(self, constitution):
        s = build_adversarial_universal_auth(constitution)
        assert s.expected_outcome == "REJECT"
        assert s.expected_rejection_code == "UNIVERSAL_AUTHORIZATION"

    def test_adversarial_scope_collapse(self, constitution):
        s = build_adversarial_scope_collapse(constitution)
        assert s.expected_outcome == "REJECT"
        assert s.expected_rejection_code == "SCOPE_COLLAPSE"

    def test_adversarial_cooling_reduction(self, constitution):
        s = build_adversarial_cooling_reduction(constitution)
        assert s.expected_outcome == "REJECT"
        assert s.expected_rejection_code == "ENVELOPE_DEGRADED"

    def test_adversarial_threshold_reduction(self, constitution):
        s = build_adversarial_threshold_reduction(constitution)
        assert s.expected_outcome == "REJECT"

    def test_adversarial_wildcard(self, constitution):
        s = build_adversarial_wildcard(constitution)
        assert s.expected_outcome == "REJECT"
        assert s.expected_rejection_code == "WILDCARD_MAPPING"

    def test_adversarial_physics_claim(self, constitution):
        s = build_adversarial_physics_claim(constitution)
        assert s.expected_outcome == "REJECT"
        assert s.expected_rejection_code == "PHYSICS_CLAIM_DETECTED"

    def test_adversarial_eck_removal(self, constitution):
        s = build_adversarial_eck_removal(constitution)
        assert s.expected_outcome == "REJECT"
        assert s.expected_rejection_code == "ECK_MISSING"

    def test_all_adversarial_count(self, constitution):
        scenarios = build_all_adversarial(constitution)
        assert len(scenarios) == 7


# ---------------------------------------------------------------------------
# Cycle tests
# ---------------------------------------------------------------------------

class TestCycleExecution:
    """Test single cycle execution."""

    def test_normal_action_cycle(self, constitution, state):
        """Normal notify cycle produces ACTION decision."""
        candidates = [
            build_notify_candidate("test message", [], constitution),
        ]
        result, next_state, output = run_x1_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Test cycle",
            action_candidates=candidates,
            amendment_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        assert result.decision_type == DecisionTypeX1.ACTION
        assert next_state.cycle_index == 1

    def test_amendment_queued_cycle(self, constitution, state, schema):
        """Lawful amendment proposal produces QUEUE_AMENDMENT."""
        scenario = build_lawful_trivial(constitution)
        result, next_state, output = run_x1_cycle(
            cycle_index=0,
            phase="propose",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Propose amendment",
            action_candidates=[],
            amendment_candidates=[scenario.proposal],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
            schema=schema,
        )
        assert result.decision_type == DecisionTypeX1.QUEUE_AMENDMENT
        assert result.amendment_proposed
        assert result.proposal_id
        assert len(next_state.pending_amendments) == 1

    def test_adversarial_rejected(self, constitution, state, schema):
        """Adversarial amendment produces rejection (falls through to action or refuse)."""
        scenario = build_adversarial_universal_auth(constitution)
        result, next_state, output = run_x1_cycle(
            cycle_index=0,
            phase="adversarial",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Adversarial",
            action_candidates=[],
            amendment_candidates=[scenario.proposal],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
            schema=schema,
        )
        # Amendment rejected (may be caught by schema gate or semantic gate)
        assert result.amendment_rejection_code is not None, (
            f"Expected amendment rejection, got decision_type={result.decision_type}"
        )

    def test_cycle_state_hash_determinism(self, constitution, state, schema):
        """Same inputs produce same state hashes."""
        scenario = build_lawful_trivial(constitution)
        r1, s1, _ = run_x1_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Test",
            action_candidates=[],
            amendment_candidates=[scenario.proposal],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
            schema=schema,
        )
        r2, s2, _ = run_x1_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Test",
            action_candidates=[],
            amendment_candidates=[scenario.proposal],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
            schema=schema,
        )
        assert r1.state_in_hash == r2.state_in_hash
        assert r1.state_out_hash == r2.state_out_hash

    def test_adoption_after_cooling(self, constitution, state, schema):
        """Amendment queued, cooling satisfied at cycle >= proposal + cooling_period."""
        # Queue at cycle 0
        scenario = build_lawful_trivial(constitution)
        _, state_1, _ = run_x1_cycle(
            cycle_index=0, phase="propose",
            timestamp="2026-02-12T12:00:00Z", user_message="propose",
            action_candidates=[], amendment_candidates=[scenario.proposal],
            constitution=constitution, internal_state=state,
            repo_root=RSA0_ROOT, schema=schema,
        )
        assert len(state_1.pending_amendments) == 1

        # Cooling cycle 1 (cycle_index=1): 1 >= 0+2 = 2 → FALSE, too early
        _, state_2, out_2 = run_x1_cycle(
            cycle_index=1, phase="cooling",
            timestamp="2026-02-12T12:00:01Z", user_message="cooling 1",
            action_candidates=[build_notify_candidate("c1", [], constitution)],
            amendment_candidates=[], constitution=constitution,
            internal_state=state_1, repo_root=RSA0_ROOT,
        )
        assert out_2.decision_type != DecisionTypeX1.ADOPT, "Too early for adoption"
        assert len(state_2.pending_amendments) == 1

        # Cooling cycle 2 (cycle_index=2): 2 >= 0+2 = 2 → TRUE, adoption triggers
        result_adopt, state_3, out_3 = run_x1_cycle(
            cycle_index=2, phase="cooling",
            timestamp="2026-02-12T12:00:02Z", user_message="cooling 2",
            action_candidates=[build_notify_candidate("c2", [], constitution)],
            amendment_candidates=[], constitution=constitution,
            internal_state=state_2, repo_root=RSA0_ROOT,
        )
        assert result_adopt.decision_type == DecisionTypeX1.ADOPT
        assert result_adopt.amendment_adopted


# ---------------------------------------------------------------------------
# Full session test
# ---------------------------------------------------------------------------

class TestFullSession:
    """Test full X-1 profiling session."""

    def test_full_session_runs_to_completion(self):
        """Full session with all phases completes without error."""
        config = X1SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            schema_path=str(SCHEMA_PATH),
            base_timestamp="2026-02-12T12:00:00Z",
            normal_cycles_pre_amendment=2,
            cooling_cycles=2,
            normal_cycles_post_fork=2,
            adversarial_scenarios=True,
            chained_amendments=2,
            verbose=False,
        )
        runner = X1Runner(config)
        result = runner.run()

        assert not result.aborted, f"Session aborted: {result.abort_reason}"
        assert result.total_cycles > 0
        assert len(result.adoptions) >= 1, "At least one adoption required"
        assert result.replay_verified, f"Replay failed: {result.replay_divergences}"
        assert len(result.constitution_transitions) >= 1

    def test_session_decision_types(self):
        """Session contains expected decision types."""
        config = X1SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            schema_path=str(SCHEMA_PATH),
            normal_cycles_pre_amendment=1,
            cooling_cycles=2,
            normal_cycles_post_fork=1,
            adversarial_scenarios=False,
            chained_amendments=0,
            verbose=False,
        )
        runner = X1Runner(config)
        result = runner.run()

        assert DecisionTypeX1.ACTION in result.decision_type_counts
        assert DecisionTypeX1.QUEUE_AMENDMENT in result.decision_type_counts
        assert DecisionTypeX1.ADOPT in result.decision_type_counts

    def test_adversarial_all_rejected(self):
        """All adversarial scenarios produce correct rejections."""
        config = X1SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            schema_path=str(SCHEMA_PATH),
            normal_cycles_pre_amendment=1,
            cooling_cycles=2,
            normal_cycles_post_fork=1,
            adversarial_scenarios=True,
            chained_amendments=0,
            verbose=False,
        )
        runner = X1Runner(config)
        result = runner.run()

        assert len(result.rejections) == 7
        for r in result.rejections:
            assert r.get("actual_code"), f"Missing rejection code for {r.get('scenario_id')}"


# ---------------------------------------------------------------------------
# Report test
# ---------------------------------------------------------------------------

class TestReport:
    """Test report generation."""

    def test_report_generation(self):
        """Report generates valid markdown."""
        config = X1SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            normal_cycles_pre_amendment=1,
            cooling_cycles=2,
            normal_cycles_post_fork=1,
            adversarial_scenarios=False,
            chained_amendments=0,
            verbose=False,
        )
        runner = X1Runner(config)
        result = runner.run()
        report = generate_report(result)

        assert "# RSA X-1" in report
        assert "Closure Criteria" in report
        assert "PASS" in report or "FAIL" in report
