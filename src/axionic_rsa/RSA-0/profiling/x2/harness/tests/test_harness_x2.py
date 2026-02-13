"""
X-2 Harness Tests

Tests the end-to-end X-2 profiling harness:
  - Scenario construction (lawful + adversarial)
  - Cycle execution (normal, delegated, treaty rejection)
  - Full session run
  - Report generation
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

# Ensure RSA-0 root is on path
# tests → harness → x2 → profiling → RSA-0
RSA0_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(RSA0_ROOT) not in sys.path:
    sys.path.insert(0, str(RSA0_ROOT))

from kernel.src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyGrant,
    TreatyRejectionCode,
    TreatyRevocation,
)
from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax2.policy_core_x2 import DelegatedActionRequest

from profiling.x2.harness.src.scenarios import (
    TreatyScenario,
    build_all_adversarial_delegation,
    build_all_adversarial_grants,
    build_all_lawful,
    build_all_scenarios,
    build_lawful_read_delegation,
    build_lawful_notify_delegation,
    build_lawful_revocation,
    build_adv_fake_grantor,
    build_adv_no_treaty_permission,
    build_adv_bad_grantee_format,
    build_adv_scope_not_map,
    build_adv_invalid_scope_type,
    build_adv_wildcard_action,
    build_adv_unknown_action,
    build_adv_grantor_lacks_action,
    build_adv_scope_zone_invalid,
    build_adv_duration_exceeded,
    build_adv_nonrevocable_revocation,
    build_adv_unsigned_dar,
    build_adv_wrong_key_dar,
    build_adv_no_treaty_citation,
    build_adv_scope_zone_outside_grant,
)
from profiling.x2.harness.src.cycle_x2 import (
    X2CycleResult,
    build_notify_candidate,
    run_x2_cycle,
)
from profiling.x2.harness.src.runner_x2 import (
    X2Runner,
    X2SessionConfig,
    X2SessionResult,
)
from profiling.x2.harness.src.report_x2 import generate_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONSTITUTION_PATH = (
    RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.3.yaml"
)
SCHEMA_PATH = (
    RSA0_ROOT / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.3.schema.json"
)


@pytest.fixture
def constitution() -> ConstitutionX2:
    return ConstitutionX2(yaml_path=str(CONSTITUTION_PATH))


@pytest.fixture
def schema() -> Dict[str, Any]:
    if SCHEMA_PATH.exists():
        return json.loads(SCHEMA_PATH.read_text())
    return {}


@pytest.fixture
def state(constitution: ConstitutionX2) -> InternalStateX2:
    return InternalStateX2(active_constitution_hash=constitution.sha256)


# ---------------------------------------------------------------------------
# Scenario tests
# ---------------------------------------------------------------------------

class TestScenarios:
    """Test that scenario builders produce valid artifacts."""

    # --- Lawful ---

    def test_lawful_read_delegation(self, constitution):
        s = build_lawful_read_delegation(constitution)
        assert s.scenario_id == "L-1-READ-DELEGATION"
        assert s.expected_delegation_outcome == "WARRANT"
        assert len(s.pre_populated_grants) == 1
        assert len(s.delegated_actions) == 1
        assert s.delegated_actions[0].signature  # must be signed

    def test_lawful_notify_delegation(self, constitution):
        s = build_lawful_notify_delegation(constitution)
        assert s.scenario_id == "L-2-NOTIFY-DELEGATION"
        assert s.expected_delegation_outcome == "WARRANT"
        assert len(s.pre_populated_grants) == 1
        assert len(s.delegated_actions) == 1

    def test_lawful_revocation(self, constitution):
        s = build_lawful_revocation(constitution)
        assert s.scenario_id == "L-3-REVOCATION"
        assert s.expected_revocation_outcome == "ADMIT"
        assert len(s.pre_populated_grants) == 1
        assert len(s.revocations) == 1

    def test_all_lawful_count(self, constitution):
        scenarios = build_all_lawful(constitution)
        assert len(scenarios) == 3

    # --- Adversarial grants ---

    def test_adv_fake_grantor(self, constitution):
        s = build_adv_fake_grantor(constitution)
        assert s.expected_grant_outcome == "REJECT"
        assert s.expected_grant_rejection_code == TreatyRejectionCode.GRANTOR_NOT_CONSTITUTIONAL

    def test_adv_no_treaty_permission(self, constitution):
        s = build_adv_no_treaty_permission(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.TREATY_PERMISSION_MISSING

    def test_adv_bad_grantee_format(self, constitution):
        s = build_adv_bad_grantee_format(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.INVALID_FIELD

    def test_adv_scope_not_map(self, constitution):
        s = build_adv_scope_not_map(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.INVALID_FIELD

    def test_adv_invalid_scope_type(self, constitution):
        s = build_adv_invalid_scope_type(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.INVALID_FIELD

    def test_adv_wildcard_action(self, constitution):
        s = build_adv_wildcard_action(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.INVALID_FIELD

    def test_adv_unknown_action(self, constitution):
        s = build_adv_unknown_action(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.INVALID_FIELD

    def test_adv_grantor_lacks_action(self, constitution):
        s = build_adv_grantor_lacks_action(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.GRANTOR_LACKS_PERMISSION

    def test_adv_scope_zone_invalid(self, constitution):
        s = build_adv_scope_zone_invalid(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.GRANTOR_LACKS_PERMISSION

    def test_adv_duration_exceeded(self, constitution):
        s = build_adv_duration_exceeded(constitution)
        assert s.expected_grant_rejection_code == TreatyRejectionCode.GRANTOR_LACKS_PERMISSION

    def test_adv_nonrevocable_revocation(self, constitution):
        s = build_adv_nonrevocable_revocation(constitution)
        assert s.expected_revocation_outcome == "REJECT"
        assert s.expected_revocation_rejection_code == TreatyRejectionCode.NONREVOCABLE_GRANT

    def test_all_adversarial_grants_count(self, constitution):
        scenarios = build_all_adversarial_grants(constitution)
        assert len(scenarios) == 11

    # --- Adversarial delegation ---

    def test_adv_unsigned_dar(self, constitution):
        s = build_adv_unsigned_dar(constitution)
        assert s.expected_delegation_rejection_code == TreatyRejectionCode.SIGNATURE_MISSING

    def test_adv_wrong_key_dar(self, constitution):
        s = build_adv_wrong_key_dar(constitution)
        assert s.expected_delegation_rejection_code == TreatyRejectionCode.SIGNATURE_INVALID

    def test_adv_no_treaty_citation(self, constitution):
        s = build_adv_no_treaty_citation(constitution)
        assert s.expected_delegation_rejection_code == TreatyRejectionCode.AUTHORITY_CITATION_INVALID

    def test_adv_scope_zone_outside_grant(self, constitution):
        s = build_adv_scope_zone_outside_grant(constitution)
        assert s.expected_delegation_rejection_code == TreatyRejectionCode.AUTHORITY_CITATION_INVALID

    def test_all_adversarial_delegation_count(self, constitution):
        scenarios = build_all_adversarial_delegation(constitution)
        assert len(scenarios) == 4

    # --- Total count ---

    def test_all_scenarios_count(self, constitution):
        scenarios = build_all_scenarios(constitution)
        assert len(scenarios) == 18  # 3 lawful + 11 adv grant + 4 adv deleg


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
        result, next_state, output = run_x2_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Test cycle",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        assert result.decision_type == DecisionTypeX2.ACTION
        assert next_state.cycle_index == 1
        assert result.grants_admitted == 0
        assert result.grants_rejected == 0

    def test_delegated_action_produces_warrant(self, constitution, state):
        """Pre-populated grant + signed DAR → delegated warrant."""
        scenario = build_lawful_read_delegation(constitution)

        # Pre-populate grant
        for grant in scenario.pre_populated_grants:
            state.active_treaty_set.add_grant(grant)

        candidates = [
            build_notify_candidate("delegation test", [], constitution),
        ]
        result, next_state, output = run_x2_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Delegation test",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=scenario.delegated_actions,
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        assert result.decision_type == DecisionTypeX2.ACTION
        assert result.delegated_warrants_issued >= 1
        assert len(result.warrant_ids) >= 2  # RSA warrant + delegated warrant

    def test_adversarial_grant_rejected(self, constitution, state):
        """Fake grantor grant is rejected at 6T."""
        scenario = build_adv_fake_grantor(constitution)

        candidates = [
            build_notify_candidate("adv grant test", [], constitution),
        ]
        result, next_state, output = run_x2_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Adversarial grant",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=scenario.grants,
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        assert result.grants_rejected >= 1
        assert TreatyRejectionCode.GRANTOR_NOT_CONSTITUTIONAL in result.grant_rejection_codes

    def test_adversarial_delegation_rejected(self, constitution, state):
        """Unsigned DAR is rejected with SIGNATURE_MISSING."""
        scenario = build_adv_unsigned_dar(constitution)

        for grant in scenario.pre_populated_grants:
            state.active_treaty_set.add_grant(grant)

        candidates = [
            build_notify_candidate("adv deleg test", [], constitution),
        ]
        result, next_state, output = run_x2_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Adversarial delegation",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=scenario.delegated_actions,
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        assert result.delegated_rejections >= 1
        assert TreatyRejectionCode.SIGNATURE_MISSING in result.delegation_rejection_codes

    def test_revocation_cycle(self, constitution, state):
        """Lawful revocation admitted."""
        scenario = build_lawful_revocation(constitution)
        for grant in scenario.pre_populated_grants:
            state.active_treaty_set.add_grant(grant)

        candidates = [
            build_notify_candidate("revocation test", [], constitution),
        ]
        result, next_state, output = run_x2_cycle(
            cycle_index=0,
            phase="test",
            timestamp="2026-02-12T12:00:00Z",
            user_message="Revocation",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=scenario.revocations,
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        assert result.revocations_admitted >= 1

    def test_cycle_state_hash_determinism(self, constitution, state):
        """Same inputs produce same state hashes."""
        candidates = [
            build_notify_candidate("determinism test", [], constitution),
        ]
        r1, _, _ = run_x2_cycle(
            cycle_index=0, phase="test",
            timestamp="2026-02-12T12:00:00Z", user_message="Test",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        r2, _, _ = run_x2_cycle(
            cycle_index=0, phase="test",
            timestamp="2026-02-12T12:00:00Z", user_message="Test",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        assert r1.state_in_hash == r2.state_in_hash
        assert r1.state_out_hash == r2.state_out_hash

    def test_cycle_result_to_dict(self, constitution, state):
        """Cycle result serializes to dict."""
        candidates = [
            build_notify_candidate("to_dict test", [], constitution),
        ]
        result, _, _ = run_x2_cycle(
            cycle_index=0, phase="test",
            timestamp="2026-02-12T12:00:00Z", user_message="Test",
            action_candidates=candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[],
            constitution=constitution,
            internal_state=state,
            repo_root=RSA0_ROOT,
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["cycle_index"] == 0
        assert d["decision_type"] == DecisionTypeX2.ACTION


# ---------------------------------------------------------------------------
# Full session test
# ---------------------------------------------------------------------------

class TestFullSession:
    """Test full X-2 profiling session."""

    def test_full_session_runs_to_completion(self):
        """Full session with all phases completes without error."""
        config = X2SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            schema_path=str(SCHEMA_PATH) if SCHEMA_PATH.exists() else None,
            base_timestamp="2026-02-12T12:00:00Z",
            normal_cycles_pre=2,
            normal_cycles_post=1,
            adversarial_grants=True,
            adversarial_delegation=True,
            expiry_test=True,
            verbose=False,
        )
        runner = X2Runner(config)
        result = runner.run()

        assert not result.aborted, f"Session aborted: {result.abort_reason}"
        assert result.total_cycles > 0
        assert result.total_delegated_warrants >= 1, "At least one delegated warrant required"
        assert result.replay_verified, f"Replay failed: {result.replay_divergences}"

    def test_session_has_all_decision_types(self):
        """Session contains ACTION decisions."""
        config = X2SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            normal_cycles_pre=1,
            adversarial_grants=False,
            adversarial_delegation=False,
            expiry_test=False,
            verbose=False,
        )
        runner = X2Runner(config)
        result = runner.run()

        assert DecisionTypeX2.ACTION in result.decision_type_counts

    def test_adversarial_grants_all_rejected(self):
        """All adversarial grant scenarios produce correct rejection codes."""
        config = X2SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            schema_path=str(SCHEMA_PATH) if SCHEMA_PATH.exists() else None,
            normal_cycles_pre=1,
            adversarial_grants=True,
            adversarial_delegation=False,
            expiry_test=False,
            verbose=False,
        )
        runner = X2Runner(config)
        result = runner.run()

        assert len(result.grant_rejection_results) == 11
        for r in result.grant_rejection_results:
            assert r.get("correct"), (
                f"Grant rejection mismatch for {r.get('scenario_id')}: "
                f"expected={r.get('expected_code')}, actual={r.get('actual_code')}"
            )

    def test_adversarial_delegation_all_rejected(self):
        """All adversarial delegation scenarios produce correct rejection codes."""
        config = X2SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            normal_cycles_pre=1,
            adversarial_grants=False,
            adversarial_delegation=True,
            expiry_test=False,
            verbose=False,
        )
        runner = X2Runner(config)
        result = runner.run()

        assert len(result.delegation_rejection_results) == 4
        for r in result.delegation_rejection_results:
            assert r.get("correct"), (
                f"Delegation rejection mismatch for {r.get('scenario_id')}: "
                f"expected={r.get('expected_code')}, actual={r.get('actual_code')}"
            )

    def test_expiry_lifecycle(self):
        """Grant expiry lifecycle is verified."""
        config = X2SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            normal_cycles_pre=1,
            adversarial_grants=False,
            adversarial_delegation=False,
            expiry_test=True,
            verbose=False,
        )
        runner = X2Runner(config)
        result = runner.run()

        assert result.expiry_confirmed, "Expiry lifecycle not confirmed"


# ---------------------------------------------------------------------------
# Report test
# ---------------------------------------------------------------------------

class TestReport:
    """Test report generation."""

    def test_report_generation(self):
        """Report generates valid markdown."""
        config = X2SessionConfig(
            repo_root=RSA0_ROOT,
            constitution_path=str(CONSTITUTION_PATH),
            normal_cycles_pre=1,
            adversarial_grants=False,
            adversarial_delegation=False,
            expiry_test=False,
            verbose=False,
        )
        runner = X2Runner(config)
        result = runner.run()
        report = generate_report(result)

        assert "# RSA X-2" in report
        assert "Closure Criteria" in report
        assert "Treaty Event Summary" in report
        assert "PASS" in report or "FAIL" in report
