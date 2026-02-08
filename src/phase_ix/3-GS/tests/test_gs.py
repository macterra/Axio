"""
GS Test Suite — Per preregistration §6, §8.

Tests all 10 conditions (A–J), failure detectors, governance classification,
replay determinism, and aggregate results.
"""

import copy
import json
import os
import sys
import types
import importlib
import pytest

# ─── Path setup ─────────────────────────────────────────────────

_GS_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
_CUD_ROOT = os.path.normpath(os.path.join(_GS_ROOT, '..', '2-CUD'))

# Phase 1: Import CUD's src package and all needed modules.
# This establishes sys.modules["src"] = 2-CUD/src/ and caches all
# CUD sub-modules (agent_model, world_state, etc.) in sys.modules.
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

_cud_agent_model = importlib.import_module("src.agent_model")
_cud_world_state = importlib.import_module("src.world_state")
_cud_authority_store = importlib.import_module("src.authority_store")
_cud_admissibility = importlib.import_module("src.admissibility")
importlib.import_module("src.deadlock_classifier")
importlib.import_module("src.epoch_controller")

# Phase 2: Replace sys.modules["src"] with a synthetic package whose
# __path__ points to 3-GS/src/.  The CUD sub-modules remain cached
# in sys.modules under their dotted names (src.agent_model, etc.),
# so _kernel.py's importlib.import_module("src.agent_model") calls
# return the cached CUD modules.  New imports (failure_detectors,
# gs_harness, strategies) resolve via the GS __path__.
_gs_src_dir = os.path.join(_GS_ROOT, 'src')
_gs_src = types.ModuleType("src")
_gs_src.__path__ = [_gs_src_dir]
_gs_src.__file__ = os.path.join(_gs_src_dir, '__init__.py')
_gs_src.__package__ = "src"
sys.modules["src"] = _gs_src

# Phase 3: Import GS modules (relative imports resolve to 3-GS/src/).
_failure_detectors = importlib.import_module("src.failure_detectors")
_governance_classifier = importlib.import_module("src.governance_classifier")
_gs_harness = importlib.import_module("src.gs_harness")

# ─── Unpack CUD symbols ────────────────────────────────────────

RSA = _cud_agent_model.RSA
Observation = _cud_agent_model.Observation
ActionRequest = _cud_agent_model.ActionRequest
Message = _cud_agent_model.Message
WorldState = _cud_world_state.WorldState
AuthorityStore = _cud_authority_store.AuthorityStore
evaluate_admissibility = _cud_admissibility.evaluate_admissibility
EXECUTED = _cud_admissibility.EXECUTED
JOINT_ADMISSIBILITY_FAILURE = _cud_admissibility.JOINT_ADMISSIBILITY_FAILURE
ACTION_FAULT = _cud_admissibility.ACTION_FAULT
NO_ACTION = _cud_admissibility.NO_ACTION

# Unpack failure_detectors symbols
K_INST = _failure_detectors.K_INST
K_OPS = _failure_detectors.K_OPS
ALL_KEYS = _failure_detectors.ALL_KEYS
STATE_DEADLOCK = _failure_detectors.STATE_DEADLOCK
STATE_LIVELOCK = _failure_detectors.STATE_LIVELOCK
COLLAPSE = _failure_detectors.COLLAPSE
ORPHANING = _failure_detectors.ORPHANING
FAILURE_FREE_GOVERNANCE = _failure_detectors.FAILURE_FREE_GOVERNANCE
TOOLING_SOVEREIGNTY = _failure_detectors.TOOLING_SOVEREIGNTY
check_failure_free_governance = _failure_detectors.check_failure_free_governance
detect_tooling_sovereignty = _failure_detectors.detect_tooling_sovereignty
InstitutionalDeadlockDetector = _failure_detectors.InstitutionalDeadlockDetector
InstitutionalLivelockDetector = _failure_detectors.InstitutionalLivelockDetector
OrphaningDetector = _failure_detectors.OrphaningDetector
CollapseDetector = _failure_detectors.CollapseDetector

# Unpack governance_classifier symbols
classify_governance_style = _governance_classifier.classify_governance_style
REFUSAL_CENTRIC = _governance_classifier.REFUSAL_CENTRIC
EXECUTION_BIASED = _governance_classifier.EXECUTION_BIASED
EXIT_NORMALIZED = _governance_classifier.EXIT_NORMALIZED
COLLAPSE_ACCEPTING = _governance_classifier.COLLAPSE_ACCEPTING
LIVELOCK_ENDURING = _governance_classifier.LIVELOCK_ENDURING
UNCLASSIFIED = _governance_classifier.UNCLASSIFIED

# Unpack gs_harness symbols
GS_INITIAL_STATE = _gs_harness.GS_INITIAL_STATE
GSEpochController = _gs_harness.GSEpochController
GSConditionLog = _gs_harness.GSConditionLog
GSExecutionLog = _gs_harness.GSExecutionLog
build_condition_a = _gs_harness.build_condition_a
build_condition_b = _gs_harness.build_condition_b
build_condition_c = _gs_harness.build_condition_c
build_condition_d = _gs_harness.build_condition_d
build_condition_e = _gs_harness.build_condition_e
build_condition_f = _gs_harness.build_condition_f
build_condition_g = _gs_harness.build_condition_g
build_condition_h = _gs_harness.build_condition_h
build_condition_i = _gs_harness.build_condition_i
build_condition_j = _gs_harness.build_condition_j
run_condition = _gs_harness.run_condition
evaluate_condition = _gs_harness.evaluate_condition
check_ffg = _gs_harness.check_ffg
run_all_conditions = _gs_harness.run_all_conditions
FIXED_CLOCK = _gs_harness.FIXED_CLOCK


# ═══════════════════════════════════════════════════════════════
# §1 — Unit Tests: Failure Detectors
# ═══════════════════════════════════════════════════════════════

class TestInstitutionalDeadlockDetector:
    """Test institutional deadlock detection per §2.7."""

    def test_immediate_deadlock(self):
        """M=1: deadlock detected on first epoch with no admissible K_INST actions."""
        d = InstitutionalDeadlockDetector()
        result = d.record_epoch(
            inst_state_changed=False,
            any_inst_pass1_admissible=False,
            any_inst_action_submitted=True,
        )
        assert result is True
        assert d.deadlock_epochs == 1

    def test_no_deadlock_on_progress(self):
        d = InstitutionalDeadlockDetector()
        result = d.record_epoch(
            inst_state_changed=True,
            any_inst_pass1_admissible=True,
            any_inst_action_submitted=True,
        )
        assert result is False
        assert d.deadlock_epochs == 0

    def test_no_deadlock_when_no_attempts(self):
        """No deadlock if no agent even tried K_INST."""
        d = InstitutionalDeadlockDetector()
        result = d.record_epoch(
            inst_state_changed=False,
            any_inst_pass1_admissible=False,
            any_inst_action_submitted=False,
        )
        assert result is False

    def test_deadlock_resets_on_progress(self):
        d = InstitutionalDeadlockDetector()
        d.record_epoch(False, False, True)  # Deadlock epoch
        d.record_epoch(True, True, True)    # Progress resets
        assert d.deadlock_epochs == 0


class TestInstitutionalLivelockDetector:
    """Test institutional livelock detection per §2.7."""

    def test_livelock_at_threshold(self):
        """Livelock latches after N=5 consecutive interference epochs."""
        ll = InstitutionalLivelockDetector(threshold=5)
        for i in range(4):
            result = ll.record_epoch(i, False, True, True)
            assert result is False
        result = ll.record_epoch(4, False, True, True)
        assert result is True
        assert ll.is_latched is True
        assert ll.latch_epoch == 4

    def test_livelock_never_clears(self):
        """Once latched, livelock is permanent."""
        ll = InstitutionalLivelockDetector(threshold=2)
        ll.record_epoch(0, False, True, True)
        ll.record_epoch(1, False, True, True)
        assert ll.is_latched is True
        # Even with progress, stays latched
        ll.record_epoch(2, True, True, False)
        assert ll.is_latched is True

    def test_livelock_resets_before_latch(self):
        ll = InstitutionalLivelockDetector(threshold=5)
        for i in range(3):
            ll.record_epoch(i, False, True, True)
        ll.record_epoch(3, True, True, False)  # Progress resets
        assert ll.is_latched is False
        # Need 5 more consecutive
        for i in range(5):
            ll.record_epoch(4 + i, False, True, True)
        assert ll.is_latched is True


class TestOrphaningDetector:
    """Test orphaning detection per §2.7."""

    def test_orphaning_on_exit(self):
        store = AuthorityStore()
        store.inject([{
            "authority_id": "GS-0001",
            "commitment": "ALLOW",
            "created_epoch": 0,
            "holder_agent_id": "A3",
            "issuer_agent_id": "harness",
            "scope": [{"operation": "WRITE", "target": "STATE:/K_OPS_A"}],
            "status": "ACTIVE",
        }])
        od = OrphaningDetector()
        # A3 has exited; only A0, A1, A2 remain active
        newly = od.check_orphaning(10, ["A0", "A1", "A2"], store, ALL_KEYS)
        assert "K_OPS_A" in newly
        assert od.orphaning_present is True

    def test_no_orphaning_with_standby(self):
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "GS-0001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "A3",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/K_REGISTRY"}],
                "status": "ACTIVE",
            },
            {
                "authority_id": "GS-0002",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "A1",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/K_REGISTRY"}],
                "status": "ACTIVE",
            },
        ])
        od = OrphaningDetector()
        # A3 exits but A1 still has ALLOW
        newly = od.check_orphaning(10, ["A0", "A1", "A2"], store, ALL_KEYS)
        assert "K_REGISTRY" not in newly
        assert od.orphaning_present is False


class TestCollapseDetector:
    def test_collapse_no_agents(self):
        assert CollapseDetector.is_collapse([]) is True

    def test_no_collapse_with_agents(self):
        assert CollapseDetector.is_collapse(["A0"]) is False


class TestFailureFreeGovernance:
    """Test FAILURE_FREE_GOVERNANCE detection per §2.12."""

    def test_failure_free_detected(self):
        m = {
            "exit_count": 0,
            "orphan_events": 0,
            "collapse_flag": False,
            "institutional_deadlock_epochs": 0,
            "institutional_livelock_occurred": False,
            "institutional_write_overlap_epochs": 0,
            "ix3_fail_tokens": [],
        }
        assert check_failure_free_governance(m) is True

    def test_not_failure_free_with_exits(self):
        m = {
            "exit_count": 1,
            "orphan_events": 0,
            "collapse_flag": False,
            "institutional_deadlock_epochs": 0,
            "institutional_livelock_occurred": False,
            "institutional_write_overlap_epochs": 0,
            "ix3_fail_tokens": [],
        }
        assert check_failure_free_governance(m) is False

    def test_not_failure_free_with_overlap(self):
        m = {
            "exit_count": 0,
            "orphan_events": 0,
            "collapse_flag": False,
            "institutional_deadlock_epochs": 0,
            "institutional_livelock_occurred": False,
            "institutional_write_overlap_epochs": 3,
            "ix3_fail_tokens": [],
        }
        assert check_failure_free_governance(m) is False


class TestToolingSovereignty:
    def test_detected_when_agent_returns_none_but_action_present(self):
        action = ActionRequest("A2", "A2:2:0", "WRITE", ["K_TREASURY"],
                               {"K_TREASURY": 98}, ["GS-0001"])
        result = detect_tooling_sovereignty(
            epoch=2,
            agent_actions={"A2": action},
            agent_proposals={"A2": None},
        )
        assert result == TOOLING_SOVEREIGNTY

    def test_not_detected_when_consistent(self):
        action = ActionRequest("A2", "A2:2:0", "WRITE", ["K_TREASURY"],
                               {"K_TREASURY": 98}, ["GS-0001"])
        result = detect_tooling_sovereignty(
            epoch=2,
            agent_actions={"A2": action},
            agent_proposals={"A2": action},
        )
        assert result is None


# ═══════════════════════════════════════════════════════════════
# §2 — Unit Tests: Governance Classifier
# ═══════════════════════════════════════════════════════════════

class TestGovernanceClassifier:

    def test_refusal_centric(self):
        m = {
            "refusal_rate": 0.90,
            "epoch_progress_rate_K_INST": 0.0,
            "collapse_flag": False,
            "ix3_fail_tokens": [],
        }
        assert classify_governance_style(m) == REFUSAL_CENTRIC

    def test_execution_biased(self):
        m = {
            "refusal_rate": 0.10,
            "epoch_progress_rate_K_INST": 0.60,
            "write_overlap_rate_K_INST": 0.10,
            "exit_rate": 0.0,
            "collapse_flag": False,
            "ix3_fail_tokens": [],
        }
        assert classify_governance_style(m) == EXECUTION_BIASED

    def test_collapse_accepting(self):
        m = {
            "collapse_flag": True,
            "ix3_fail_tokens": [],
        }
        assert classify_governance_style(m) == COLLAPSE_ACCEPTING

    def test_livelock_enduring(self):
        m = {
            "livelock_latched": True,
            "livelock_epoch": 5,
            "total_epochs": 30,
            "llock_ack_in_log": True,
            "collapse_flag": False,
            "ix3_fail_tokens": [],
        }
        assert classify_governance_style(m) == LIVELOCK_ENDURING

    def test_exit_normalized(self):
        m = {
            "exit_rate": 0.10,
            "handoff_in_log": True,
            "refusal_rate": 0.20,
            "epoch_progress_rate_K_INST": 0.30,
            "collapse_flag": False,
            "ix3_fail_tokens": [],
        }
        assert classify_governance_style(m) == EXIT_NORMALIZED

    def test_unclassified(self):
        m = {
            "refusal_rate": 0.50,
            "epoch_progress_rate_K_INST": 0.30,
            "exit_rate": 0.0,
            "collapse_flag": False,
            "ix3_fail_tokens": [],
        }
        assert classify_governance_style(m) == UNCLASSIFIED


# ═══════════════════════════════════════════════════════════════
# §3 — Integration Tests: Individual Conditions
# ═══════════════════════════════════════════════════════════════

class TestConditionA:
    """Condition A: Refusal-Dominant Institution (Livelock)."""

    def test_condition_a_pass(self):
        log = run_condition(build_condition_a, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"A failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_a_livelock_detected(self):
        log = run_condition(build_condition_a, timestamp=FIXED_CLOCK)
        assert log.terminal_classification == STATE_LIVELOCK

    def test_condition_a_no_institutional_progress(self):
        log = run_condition(build_condition_a, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["epoch_progress_rate_K_INST"] <= 0.10

    def test_condition_a_high_refusal(self):
        log = run_condition(build_condition_a, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["refusal_rate"] >= 0.70


class TestConditionB:
    """Condition B: Execution-Dominant Institution (Minimal Overlap)."""

    def test_condition_b_pass(self):
        log = run_condition(build_condition_b, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"B failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_b_no_deadlock_livelock(self):
        log = run_condition(build_condition_b, timestamp=FIXED_CLOCK)
        assert log.terminal_classification not in (STATE_DEADLOCK, STATE_LIVELOCK)

    def test_condition_b_institutional_progress(self):
        log = run_condition(build_condition_b, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["epoch_progress_rate_K_INST"] >= 0.40

    def test_condition_b_overlap_present(self):
        log = run_condition(build_condition_b, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["write_overlap_rate_K_INST"] >= 0.05


class TestConditionC:
    """Condition C: Exit-Normalized Institution (Authorized State Handoff)."""

    def test_condition_c_pass(self):
        log = run_condition(build_condition_c, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"C failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_c_exit_with_handoff(self):
        log = run_condition(build_condition_c, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["exit_count"] >= 1
        assert log.aggregate_metrics["orphan_events"] == 0

    def test_condition_c_handoff_in_log(self):
        log = run_condition(build_condition_c, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics.get("handoff_in_log", False) is True


class TestConditionD:
    """Condition D: Exit-Unprepared Institution (Orphaning)."""

    def test_condition_d_pass(self):
        log = run_condition(build_condition_d, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"D failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_d_orphaning(self):
        log = run_condition(build_condition_d, timestamp=FIXED_CLOCK)
        assert log.terminal_classification == ORPHANING
        assert log.aggregate_metrics["orphan_events"] >= 1


class TestConditionE:
    """Condition E: Livelock Endurance."""

    def test_condition_e_pass(self):
        log = run_condition(build_condition_e, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"E failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_e_livelock_latched(self):
        log = run_condition(build_condition_e, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["livelock_latched"] is True

    def test_condition_e_runs_to_30(self):
        log = run_condition(build_condition_e, timestamp=FIXED_CLOCK)
        assert len(log.epochs) == 30

    def test_condition_e_llock_ack_present(self):
        log = run_condition(build_condition_e, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics.get("llock_ack_in_log", False) is True


class TestConditionF:
    """Condition F: Collapse Acceptance."""

    def test_condition_f_pass(self):
        log = run_condition(build_condition_f, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"F failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_f_collapse(self):
        log = run_condition(build_condition_f, timestamp=FIXED_CLOCK)
        assert log.terminal_classification == COLLAPSE


class TestConditionG:
    """Condition G: Coordinator Loss Under Delegated Coordination."""

    def test_condition_g_pass(self):
        log = run_condition(build_condition_g, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"G failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_g_orphaning_after_coordinator_exit(self):
        log = run_condition(build_condition_g, timestamp=FIXED_CLOCK)
        assert log.terminal_classification == ORPHANING
        assert log.aggregate_metrics["orphan_events"] >= 1


class TestConditionH:
    """Condition H: Ambiguity Without Timeouts (Partition Simulation)."""

    def test_condition_h_pass(self):
        log = run_condition(build_condition_h, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"H failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_h_overlap(self):
        log = run_condition(build_condition_h, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["institutional_write_overlap_epochs"] >= 1


class TestConditionI:
    """Condition I: Tooling Default Opt-In (Adversarial)."""

    def test_condition_i_pass(self):
        log = run_condition(build_condition_i, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"I failed: fails={log.ix3_fail_tokens}"
        )

    def test_condition_i_tooling_sovereignty_detected(self):
        log = run_condition(build_condition_i, timestamp=FIXED_CLOCK)
        assert TOOLING_SOVEREIGNTY in log.ix3_fail_tokens


class TestConditionJ:
    """Condition J: Unauthorized Reclamation Attempt (Adversarial)."""

    def test_condition_j_pass(self):
        log = run_condition(build_condition_j, timestamp=FIXED_CLOCK)
        ffg = check_ffg(log)
        if ffg:
            log.ix3_fail_tokens.append(ffg)
        log.condition_result = evaluate_condition(log)
        assert log.condition_result == "PASS", (
            f"J failed: terminal={log.terminal_classification}, "
            f"metrics={log.aggregate_metrics}, fails={log.ix3_fail_tokens}"
        )

    def test_condition_j_reclamation_refused(self):
        log = run_condition(build_condition_j, timestamp=FIXED_CLOCK)
        final = log.epochs[-1].state_after
        assert final["K_OPS_A"] == GS_INITIAL_STATE["K_OPS_A"]

    def test_condition_j_orphaning(self):
        log = run_condition(build_condition_j, timestamp=FIXED_CLOCK)
        assert log.aggregate_metrics["orphan_events"] >= 1


# ═══════════════════════════════════════════════════════════════
# §4 — Replay Determinism
# ═══════════════════════════════════════════════════════════════

class TestReplayDeterminism:
    """Verify bit-perfect replay for all conditions."""

    @pytest.mark.parametrize("builder", [
        build_condition_a,
        build_condition_b,
        build_condition_c,
        build_condition_d,
        build_condition_e,
        build_condition_f,
        build_condition_g,
        build_condition_h,
        build_condition_i,
        build_condition_j,
    ], ids=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
    def test_replay_determinism(self, builder):
        """Two runs of same condition must produce identical epoch data."""
        log1 = run_condition(builder, timestamp=FIXED_CLOCK)
        log2 = run_condition(builder, timestamp=FIXED_CLOCK)

        # Compare epoch-by-epoch
        assert len(log1.epochs) == len(log2.epochs), (
            f"Epoch count mismatch: {len(log1.epochs)} vs {len(log2.epochs)}"
        )
        for i, (e1, e2) in enumerate(zip(log1.epochs, log2.epochs)):
            d1 = e1.to_dict()
            d2 = e2.to_dict()
            assert d1 == d2, f"Epoch {i} diverged: {d1} != {d2}"

        # Compare terminal classifications
        assert log1.terminal_classification == log2.terminal_classification
        assert log1.aggregate_metrics == log2.aggregate_metrics


# ═══════════════════════════════════════════════════════════════
# §5 — Aggregate Experiment
# ═══════════════════════════════════════════════════════════════

class TestAggregateExperiment:
    """Test full experiment run."""

    def test_all_conditions_pass(self):
        """All 10 conditions should PASS → IX3_PASS."""
        result = run_all_conditions(timestamp=FIXED_CLOCK)
        for clog in result.conditions:
            assert clog.condition_result == "PASS", (
                f"Condition {clog.condition} FAILED: "
                f"terminal={clog.terminal_classification}, "
                f"metrics={clog.aggregate_metrics}, "
                f"fails={clog.ix3_fail_tokens}"
            )
        assert result.aggregate_result == "IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED"

    def test_all_10_conditions_executed(self):
        result = run_all_conditions(timestamp=FIXED_CLOCK)
        conditions = [c.condition for c in result.conditions]
        assert sorted(conditions) == ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]

    def test_no_failure_free_governance(self):
        """No condition should exhibit FAILURE_FREE_GOVERNANCE."""
        result = run_all_conditions(timestamp=FIXED_CLOCK)
        for clog in result.conditions:
            assert FAILURE_FREE_GOVERNANCE not in clog.ix3_fail_tokens, (
                f"Condition {clog.condition} has FAILURE_FREE_GOVERNANCE"
            )


# ═══════════════════════════════════════════════════════════════
# §6 — JSON Serialization
# ═══════════════════════════════════════════════════════════════

class TestSerialization:
    """Test log serialization round-trip."""

    def test_condition_log_json_roundtrip(self):
        log = run_condition(build_condition_a, timestamp=FIXED_CLOCK)
        json_str = log.to_json()
        parsed = json.loads(json_str)
        assert parsed["condition"] == "A"
        assert "epochs" in parsed
        assert "aggregate_metrics" in parsed

    def test_execution_log_json_roundtrip(self):
        result = run_all_conditions(timestamp=FIXED_CLOCK)
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["phase"] == "IX-3"
        assert parsed["subphase"] == "GS"
        assert len(parsed["conditions"]) == 10


# ═══════════════════════════════════════════════════════════════
# §7 — Strategy Smoke Tests
# ═══════════════════════════════════════════════════════════════

class TestStrategies:
    """Smoke tests for individual strategy classes."""

    def test_contest_policy_always(self):
        ContestPolicyAlways = importlib.import_module("src.strategies.contest_policy").ContestPolicyAlways
        agent = ContestPolicyAlways("A0", "GS-0001")
        obs = Observation(0, {"K_POLICY": "P0"}, None, None, None, [])
        agent.observe(obs)
        assert agent.wants_to_exit() is False
        action = agent.propose_action()
        assert action is not None
        assert action.declared_scope == ["K_POLICY"]
        assert action.action_type == "WRITE"

    def test_ops_partition_writer_a(self):
        OpsPartitionWriter_A = importlib.import_module("src.strategies.ops_partition").OpsPartitionWriter_A
        agent = OpsPartitionWriter_A("A0", "GS-0001")
        obs = Observation(0, {"K_OPS_A": "free"}, None, None, None, [])
        agent.observe(obs)
        action = agent.propose_action()
        assert action.declared_scope == ["K_OPS_A"]

    def test_dissolution_exits_at_scheduled_epoch(self):
        DissolutionSequence = importlib.import_module("src.strategies.dissolution").DissolutionSequence
        agent = DissolutionSequence("A0", "GS-0001", exit_epoch=5)
        obs = Observation(5, {}, None, None, None, [])
        agent.observe(obs)
        assert agent.wants_to_exit() is True

    def test_dissolution_doesnt_exit_early(self):
        DissolutionSequence = importlib.import_module("src.strategies.dissolution").DissolutionSequence
        agent = DissolutionSequence("A0", "GS-0001", exit_epoch=5)
        obs = Observation(4, {}, None, None, None, [])
        agent.observe(obs)
        assert agent.wants_to_exit() is False

    def test_silent_window_observer(self):
        SilentWindowObserver_6_11 = importlib.import_module("src.strategies.silent_window").SilentWindowObserver_6_11
        agent = SilentWindowObserver_6_11("A2", "GS-0001")
        # During window
        obs = Observation(7, {"K_POLICY": "P0"}, None, None, None, [])
        agent.observe(obs)
        assert agent.propose_action() is None
        assert agent.compose_message() is None
        # Outside window
        obs = Observation(12, {"K_POLICY": "P0"}, None, None, None, [])
        agent.observe(obs)
        assert agent.propose_action() is not None

    def test_exit_abrupt_no_handoff(self):
        ExitAbruptNoHandoff = importlib.import_module("src.strategies.reclaim_attempt").ExitAbruptNoHandoff
        agent = ExitAbruptNoHandoff("A3", exit_epoch=10)
        obs = Observation(10, {}, None, None, None, [])
        agent.observe(obs)
        assert agent.wants_to_exit() is True
        assert agent.propose_action() is None

    def test_livelock_acknowledger(self):
        LivelockAcknowledger_AfterLatch = importlib.import_module("src.strategies.livelock_ack").LivelockAcknowledger_AfterLatch
        agent = LivelockAcknowledger_AfterLatch("A2", "GS-0001", livelock_n=3)
        fixed_state = {"K_POLICY": "P0"}
        # Epoch 0: first observation, no stagnation comparison yet
        obs = Observation(0, fixed_state, None, None, None, [])
        agent.observe(obs)
        assert agent.propose_action() is None
        # Epoch 1-2: same state → stagnant_epochs = 1, 2
        for e in (1, 2):
            obs = Observation(e, dict(fixed_state), "NO_ACTION", None, None, [])
            agent.observe(obs)
            assert agent.propose_action() is None
        # Epoch 3: same state → stagnant_epochs = 3 → latched
        obs = Observation(3, dict(fixed_state), "NO_ACTION", None, None, [])
        agent.observe(obs)
        action = agent.propose_action()
        assert action is not None
        assert "LLOCK_ACK" in action.proposed_delta.get("K_LOG", "")
        # Next epoch: observe EXECUTED → confirmed
        obs = Observation(4, dict(fixed_state), "EXECUTED", None, None, [])
        agent.observe(obs)
        assert agent.propose_action() is None


# ═══════════════════════════════════════════════════════════════
# §8 — World State
# ═══════════════════════════════════════════════════════════════

class TestWorldState:
    """Test GS initial state and key structure."""

    def test_initial_state_has_6_keys(self):
        ws = WorldState(copy.deepcopy(GS_INITIAL_STATE))
        state = ws.get_state()
        assert set(state.keys()) == {"K_POLICY", "K_TREASURY", "K_OPS_A",
                                      "K_OPS_B", "K_REGISTRY", "K_LOG"}

    def test_initial_state_values(self):
        ws = WorldState(copy.deepcopy(GS_INITIAL_STATE))
        state = ws.get_state()
        assert state["K_POLICY"] == "P0"
        assert state["K_TREASURY"] == 100
        assert state["K_OPS_A"] == "free"
        assert state["K_OPS_B"] == "free"
        assert "A0,A1,A2,A3" in state["K_REGISTRY"]
        assert state["K_LOG"] == ""

    def test_key_sets(self):
        assert K_INST == frozenset({"K_POLICY", "K_TREASURY", "K_REGISTRY", "K_LOG"})
        assert K_OPS == frozenset({"K_OPS_A", "K_OPS_B"})
        assert ALL_KEYS == K_INST | K_OPS
