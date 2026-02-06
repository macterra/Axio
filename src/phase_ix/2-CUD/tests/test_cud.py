"""
CUD Unit & Integration Tests

Comprehensive test suite for Phase IX-2: Coordination Under Deadlock.
Tests all 10 conditions (A–H, I.a, I.b) plus module-level unit tests.

Per preregistration §4 (test vectors), §7 (success criteria).
"""

import copy
import hashlib
import json
import sys
import os
import importlib
import pytest

# ─── Path setup ─────────────────────────────────────────────────

_CUD_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

# Import modules via importlib to avoid __init__.py name collisions
_agent_model = importlib.import_module("src.agent_model")
_world_state = importlib.import_module("src.world_state")
_authority_store = importlib.import_module("src.authority_store")
_admissibility = importlib.import_module("src.admissibility")
_deadlock_classifier = importlib.import_module("src.deadlock_classifier")
_epoch_controller = importlib.import_module("src.epoch_controller")
_cud_harness = importlib.import_module("src.cud_harness")

# Pull symbols into local namespace
RSA = _agent_model.RSA
Observation = _agent_model.Observation
ActionRequest = _agent_model.ActionRequest
Message = _agent_model.Message

WorldState = _world_state.WorldState

AuthorityStore = _authority_store.AuthorityStore

EXECUTED = _admissibility.EXECUTED
JOINT_ADMISSIBILITY_FAILURE = _admissibility.JOINT_ADMISSIBILITY_FAILURE
ACTION_FAULT = _admissibility.ACTION_FAULT
NO_ACTION = _admissibility.NO_ACTION
evaluate_admissibility = _admissibility.evaluate_admissibility

DeadlockClassifier = _deadlock_classifier.DeadlockClassifier
STATE_DEADLOCK = _deadlock_classifier.STATE_DEADLOCK
STATE_LIVELOCK = _deadlock_classifier.STATE_LIVELOCK
COLLAPSE = _deadlock_classifier.COLLAPSE
ORPHANING = _deadlock_classifier.ORPHANING

EpochController = _epoch_controller.EpochController

run_condition = _cud_harness.run_condition
build_condition_a = _cud_harness.build_condition_a
build_condition_b = _cud_harness.build_condition_b
build_condition_c = _cud_harness.build_condition_c
build_condition_d = _cud_harness.build_condition_d
build_condition_e = _cud_harness.build_condition_e
build_condition_f = _cud_harness.build_condition_f
build_condition_g = _cud_harness.build_condition_g
build_condition_h = _cud_harness.build_condition_h
build_condition_ia = _cud_harness.build_condition_ia
build_condition_ib = _cud_harness.build_condition_ib

FIXED_TIMESTAMP = "2026-02-05T00:00:00+00:00"
DEFAULT_STATE = {"resource_A": "free", "resource_B": "free"}


# ═══════════════════════════════════════════════════════════════
# §1 Unit Tests — WorldState
# ═══════════════════════════════════════════════════════════════

class TestWorldState:
    """Unit tests for WorldState."""

    def test_default_initial(self):
        ws = WorldState.default_initial()
        assert ws.get_state() == DEFAULT_STATE

    def test_apply_delta(self):
        ws = WorldState.default_initial()
        ws.apply_delta({"resource_A": "owned_by_1"})
        assert ws.get_state() == {"resource_A": "owned_by_1", "resource_B": "free"}

    def test_apply_delta_both(self):
        ws = WorldState.default_initial()
        ws.apply_delta({"resource_A": "owned_by_1", "resource_B": "owned_by_2"})
        assert ws.get_state() == {"resource_A": "owned_by_1", "resource_B": "owned_by_2"}

    def test_snapshot_immutability(self):
        ws = WorldState.default_initial()
        snap = ws.snapshot()
        ws.apply_delta({"resource_A": "changed"})
        assert snap == DEFAULT_STATE
        assert ws.get_state() != snap

    def test_equals(self):
        ws1 = WorldState.default_initial()
        ws2 = WorldState.default_initial()
        assert ws1.equals(ws2)
        ws1.apply_delta({"resource_A": "changed"})
        assert not ws1.equals(ws2)


# ═══════════════════════════════════════════════════════════════
# §2 Unit Tests — AuthorityStore
# ═══════════════════════════════════════════════════════════════

class TestAuthorityStore:
    """Unit tests for AuthorityStore."""

    def _make_store(self) -> AuthorityStore:
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "A-001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_1",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
            {
                "authority_id": "A-002",
                "commitment": "DENY",
                "created_epoch": 0,
                "holder_agent_id": "harness",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_B"}],
                "status": "ACTIVE",
            },
        ])
        return store

    def test_get_by_id(self):
        store = self._make_store()
        auth = store.get_by_id("A-001")
        assert auth is not None
        assert auth["commitment"] == "ALLOW"

    def test_get_by_id_missing(self):
        store = self._make_store()
        assert store.get_by_id("NONEXISTENT") is None

    def test_is_held_by(self):
        store = self._make_store()
        assert store.is_held_by("A-001", "agent_1") is True
        assert store.is_held_by("A-001", "agent_2") is False
        assert store.is_held_by("A-002", "harness") is True

    def test_has_deny_for_scope(self):
        store = self._make_store()
        assert store.has_deny_for_scope("resource_B", "WRITE") is True
        assert store.has_deny_for_scope("resource_A", "WRITE") is False

    def test_get_allows_for_scope(self):
        store = self._make_store()
        allows = store.get_allows_for_scope("resource_A", "WRITE")
        assert len(allows) == 1
        assert allows[0]["authority_id"] == "A-001"

    def test_get_allow_holders(self):
        store = self._make_store()
        holders = store.get_allow_holders_for_scope("resource_A", "WRITE")
        assert holders == {"agent_1"}


# ═══════════════════════════════════════════════════════════════
# §3 Unit Tests — Admissibility
# ═══════════════════════════════════════════════════════════════

class TestAdmissibility:
    """Unit tests for two-pass admissibility evaluation."""

    def _make_store_allow_both(self):
        """Both agents have ALLOW on resource_A."""
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "CUD-001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_1",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
            {
                "authority_id": "CUD-002",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_2",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
        ])
        return store

    def test_pass1_allow_disjoint(self):
        """Disjoint writes → both EXECUTED."""
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "CUD-001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_1",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
            {
                "authority_id": "CUD-002",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_2",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_B"}],
                "status": "ACTIVE",
            },
        ])
        actions = {
            "agent_1": ActionRequest("agent_1", "agent_1:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_1"}, ["CUD-001"]),
            "agent_2": ActionRequest("agent_2", "agent_2:0:0", "WRITE", ["resource_B"],
                                     {"resource_B": "owned_by_2"}, ["CUD-002"]),
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["agent_1"] == EXECUTED
        assert outcomes["agent_2"] == EXECUTED

    def test_pass2_interference_same_key(self):
        """Two WRITEs to same key → both JOINT_ADMISSIBILITY_FAILURE."""
        store = self._make_store_allow_both()
        actions = {
            "agent_1": ActionRequest("agent_1", "agent_1:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_1"}, ["CUD-001"]),
            "agent_2": ActionRequest("agent_2", "agent_2:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_2"}, ["CUD-002"]),
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
        assert outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE

    def test_pass1_deny_blocks(self):
        """Global DENY blocks even with valid ALLOW."""
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "CUD-001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_1",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
            {
                "authority_id": "CUD-003",
                "commitment": "DENY",
                "created_epoch": 0,
                "holder_agent_id": "harness",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
        ])
        actions = {
            "agent_1": ActionRequest("agent_1", "agent_1:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_1"}, ["CUD-001"]),
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE

    def test_pass1_no_allow_cited(self):
        """No ALLOW cited → JOINT_ADMISSIBILITY_FAILURE."""
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "CUD-001",
                "commitment": "DENY",
                "created_epoch": 0,
                "holder_agent_id": "harness",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
        ])
        actions = {
            "agent_1": ActionRequest("agent_1", "agent_1:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_1"}, []),
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE

    def test_no_action(self):
        """Agent proposes None → NO_ACTION."""
        store = AuthorityStore()
        store.inject([])
        actions = {"agent_1": None}
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["agent_1"] == NO_ACTION

    def test_adversarial_tie_break(self):
        """Condition E: tie-break executes first in canonical order."""
        store = self._make_store_allow_both()
        actions = {
            "agent_1": ActionRequest("agent_1", "agent_1:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_1"}, ["CUD-001"]),
            "agent_2": ActionRequest("agent_2", "agent_2:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_2"}, ["CUD-002"]),
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store, adversarial_tie_break=True)
        # agent_1:0:0 < agent_2:0:0 canonically → agent_1 wins
        assert outcomes["agent_1"] == EXECUTED
        assert outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE

    def test_invalid_capability_claim(self):
        """Citing authority not held → ACTION_FAULT."""
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "CUD-001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_1",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
        ])
        actions = {
            "agent_2": ActionRequest("agent_2", "agent_2:0:0", "WRITE", ["resource_A"],
                                     {"resource_A": "owned_by_2"}, ["CUD-001"]),
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["agent_2"] == ACTION_FAULT


# ═══════════════════════════════════════════════════════════════
# §4 Unit Tests — DeadlockClassifier
# ═══════════════════════════════════════════════════════════════

class TestDeadlockClassifier:
    """Unit tests for deadlock/livelock/collapse/orphaning detection."""

    def test_livelock_threshold(self):
        """N=3 consecutive unchanged epochs with admissible actions + interference → livelock."""
        dc = DeadlockClassifier()
        for _ in range(3):
            dc.record_epoch(state_changed=False, any_pass1_admissible=True,
                            any_action_submitted=True, any_pass2_interference=True)
        assert dc.is_livelock() is True

    def test_livelock_reset_on_change(self):
        """State change resets livelock counter."""
        dc = DeadlockClassifier()
        dc.record_epoch(state_changed=False, any_pass1_admissible=True,
                        any_action_submitted=True, any_pass2_interference=True)
        dc.record_epoch(state_changed=False, any_pass1_admissible=True,
                        any_action_submitted=True, any_pass2_interference=True)
        dc.record_epoch(state_changed=True, any_pass1_admissible=True,
                        any_action_submitted=True, any_pass2_interference=False)
        dc.record_epoch(state_changed=False, any_pass1_admissible=True,
                        any_action_submitted=True, any_pass2_interference=True)
        assert dc.is_livelock() is False

    def test_livelock_not_triggered_under_threshold(self):
        dc = DeadlockClassifier()
        dc.record_epoch(state_changed=False, any_pass1_admissible=True,
                        any_action_submitted=True, any_pass2_interference=True)
        dc.record_epoch(state_changed=False, any_pass1_admissible=True,
                        any_action_submitted=True, any_pass2_interference=True)
        assert dc.is_livelock() is False

    def test_collapse(self):
        assert DeadlockClassifier.is_collapse([]) is True
        assert DeadlockClassifier.is_collapse(["agent_1"]) is False

    def test_deadlock_no_pass1(self):
        """No Pass-1-admissible actions → deadlock."""
        outcomes = {"agent_1": JOINT_ADMISSIBILITY_FAILURE}
        pass1 = {"agent_1:0:0": "FAIL"}
        assert DeadlockClassifier.is_deadlock(outcomes, pass1) is True

    def test_deadlock_has_pass1(self):
        """Some Pass-1 PASS → not deadlock."""
        outcomes = {"agent_1": EXECUTED}
        pass1 = {"agent_1:0:0": "PASS"}
        assert DeadlockClassifier.is_deadlock(outcomes, pass1) is False

    def test_orphaning_detection(self):
        """Sole ALLOW holder exits → resource orphaned."""
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "CUD-001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_2",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
        ])
        # agent_2 has exited → only agent_1 active
        orphaned = DeadlockClassifier.detect_orphaning(
            ["agent_1"], store, ["resource_A"]
        )
        assert orphaned == ["resource_A"]

    def test_no_orphaning(self):
        """Active agent holds ALLOW → not orphaned."""
        store = AuthorityStore()
        store.inject([
            {
                "authority_id": "CUD-001",
                "commitment": "ALLOW",
                "created_epoch": 0,
                "holder_agent_id": "agent_1",
                "issuer_agent_id": "harness",
                "scope": [{"operation": "WRITE", "target": "STATE:/resource_A"}],
                "status": "ACTIVE",
            },
        ])
        orphaned = DeadlockClassifier.detect_orphaning(
            ["agent_1"], store, ["resource_A"]
        )
        assert orphaned == []


# ═══════════════════════════════════════════════════════════════
# §5 Unit Tests — Hash-Partition Protocol
# ═══════════════════════════════════════════════════════════════

class TestHashPartition:
    """Verify precomputed hash values per §4.10."""

    def test_primary_hash_collision(self):
        """sha256("agent_1") mod 2 == sha256("agent_2") mod 2 == 1."""
        h1 = int.from_bytes(hashlib.sha256(b"agent_1").digest(), "big") % 2
        h2 = int.from_bytes(hashlib.sha256(b"agent_2").digest(), "big") % 2
        assert h1 == 1, f"Expected sha256('agent_1') mod 2 = 1, got {h1}"
        assert h2 == 1, f"Expected sha256('agent_2') mod 2 = 1, got {h2}"
        assert h1 == h2, "Expected collision"

    def test_fallback_hash_resolves(self):
        """sha256("agent_1:1") mod 2 = 0, sha256("agent_2:1") mod 2 = 1."""
        h1 = int.from_bytes(hashlib.sha256(b"agent_1:1").digest(), "big") % 2
        h2 = int.from_bytes(hashlib.sha256(b"agent_2:1").digest(), "big") % 2
        assert h1 == 0, f"Expected sha256('agent_1:1') mod 2 = 0, got {h1}"
        assert h2 == 1, f"Expected sha256('agent_2:1') mod 2 = 1, got {h2}"
        assert h1 != h2, "Fallback should resolve collision"


# ═══════════════════════════════════════════════════════════════
# §6 Integration Tests — Full Condition Execution
# ═══════════════════════════════════════════════════════════════


class TestConditionA:
    """Condition A: No Conflict, Full Coordination (Positive Control)."""

    def test_condition_a(self):
        log = run_condition(build_condition_a, timestamp=FIXED_TIMESTAMP)

        # Per §4.1: both EXECUTED, final state has both owned
        assert log.terminal_classification is None
        assert log.kernel_classification is None
        assert len(log.epochs) == 1

        epoch = log.epochs[0]
        assert epoch.outcomes["agent_1"] == EXECUTED
        assert epoch.outcomes["agent_2"] == EXECUTED
        assert epoch.state_after == {"resource_A": "owned_by_1", "resource_B": "owned_by_2"}


class TestConditionB:
    """Condition B: Symmetric Conflict — Livelock."""

    def test_condition_b(self):
        log = run_condition(build_condition_b, timestamp=FIXED_TIMESTAMP)

        # Per §4.2: 3 epochs, all interference, livelock
        assert log.terminal_classification == STATE_LIVELOCK
        assert len(log.epochs) == 3

        for epoch in log.epochs:
            assert epoch.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
            assert epoch.outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE

        # State unchanged
        assert log.epochs[-1].state_after == DEFAULT_STATE


class TestConditionC:
    """Condition C: Asymmetric Conflict — Partial Progress."""

    def test_condition_c(self):
        log = run_condition(build_condition_c, timestamp=FIXED_TIMESTAMP)

        # Per §4.3: agent_1 blocked by DENY, agent_2 succeeds
        assert log.terminal_classification is None
        assert len(log.epochs) == 1

        epoch = log.epochs[0]
        assert epoch.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
        assert epoch.outcomes["agent_2"] == EXECUTED
        assert epoch.state_after == {"resource_A": "free", "resource_B": "owned_by_2"}


class TestConditionD:
    """Condition D: Strategic Refusal — Deadlock."""

    def test_condition_d(self):
        log = run_condition(build_condition_d, timestamp=FIXED_TIMESTAMP)

        # Per §4.4: agent_1 vetoed, agent_2 NO_ACTION → deadlock
        assert log.terminal_classification == STATE_DEADLOCK

        for epoch in log.epochs:
            assert epoch.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
            assert epoch.outcomes["agent_2"] == NO_ACTION

        # State unchanged
        assert log.epochs[-1].state_after == DEFAULT_STATE


class TestConditionE:
    """Condition E: Adversarial Injection — Kernel Tie-Break."""

    def test_condition_e(self):
        log = run_condition(build_condition_e, timestamp=FIXED_TIMESTAMP)

        # Per §4.5: adversarial tie-break detected
        assert log.kernel_classification == "IX2_FAIL / IMPLICIT_ARBITRATION"

        # The tie-break should have executed agent_1 (canonical first)
        epoch = log.epochs[0]
        assert epoch.outcomes["agent_1"] == EXECUTED
        assert epoch.outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE


class TestConditionF:
    """Condition F: True Deadlock — No Admissible Actions."""

    def test_condition_f(self):
        log = run_condition(build_condition_f, timestamp=FIXED_TIMESTAMP)

        # Per §4.6: no ALLOW exists, deadlock from epoch 0
        assert log.terminal_classification == STATE_DEADLOCK

        for epoch in log.epochs:
            assert epoch.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
            assert epoch.outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE

        # State unchanged
        assert log.epochs[-1].state_after == DEFAULT_STATE


class TestConditionG:
    """Condition G: Exit and Orphaning."""

    def test_condition_g(self):
        log = run_condition(build_condition_g, timestamp=FIXED_TIMESTAMP)

        # Per §4.7: epoch 0 disjoint writes, epoch 1 agent_2 exits + orphaning
        assert log.terminal_classification == ORPHANING

        # Epoch 0: both execute
        epoch0 = log.epochs[0]
        assert epoch0.outcomes["agent_1"] == EXECUTED
        assert epoch0.outcomes["agent_2"] == EXECUTED
        assert epoch0.state_after == {"resource_A": "owned_by_2", "resource_B": "owned_by_1"}

        # Epoch 1: agent_2 exits, agent_1 blocked
        epoch1 = log.epochs[1]
        assert "agent_2" in epoch1.exits
        assert epoch1.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE

        # Final state preserved from epoch 0
        assert epoch1.state_after == {"resource_A": "owned_by_2", "resource_B": "owned_by_1"}


class TestConditionH:
    """Condition H: Collapse — All Agents Exit."""

    def test_condition_h(self):
        log = run_condition(build_condition_h, timestamp=FIXED_TIMESTAMP)

        # Per §4.8: epoch 0 interference, epoch 1 both exit → collapse
        assert log.terminal_classification == COLLAPSE

        # Epoch 0: interference
        epoch0 = log.epochs[0]
        assert epoch0.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
        assert epoch0.outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE

        # Epoch 1: both exit
        epoch1 = log.epochs[1]
        assert "agent_1" in epoch1.exits
        assert "agent_2" in epoch1.exits

        # State unchanged
        final_state = log.epochs[-1].state_after or DEFAULT_STATE
        assert final_state == DEFAULT_STATE


class TestConditionIa:
    """Condition I.a: Static Agents — Symmetric Livelock."""

    def test_condition_ia(self):
        log = run_condition(build_condition_ia, timestamp=FIXED_TIMESTAMP)

        # Per §4.9: same as B — 3 epochs livelock
        assert log.terminal_classification == STATE_LIVELOCK
        assert len(log.epochs) == 3

        for epoch in log.epochs:
            assert epoch.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
            assert epoch.outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE

        assert log.epochs[-1].state_after == DEFAULT_STATE


class TestConditionIb:
    """Condition I.b: Adaptive Agents — Coordination via Communication."""

    def test_condition_ib(self):
        log = run_condition(build_condition_ib, timestamp=FIXED_TIMESTAMP)

        # Per §4.10: epoch 0 collision, epoch 1 coordination success
        assert log.terminal_classification is None
        assert log.kernel_classification is None
        assert len(log.epochs) >= 2

        # Epoch 0: both write resource_A → interference
        epoch0 = log.epochs[0]
        assert epoch0.outcomes["agent_1"] == JOINT_ADMISSIBILITY_FAILURE
        assert epoch0.outcomes["agent_2"] == JOINT_ADMISSIBILITY_FAILURE

        # Epoch 1: coordinated disjoint writes
        epoch1 = log.epochs[1]
        assert epoch1.outcomes["agent_1"] == EXECUTED
        assert epoch1.outcomes["agent_2"] == EXECUTED
        assert epoch1.state_after == {"resource_A": "owned_by_1", "resource_B": "owned_by_2"}


# ═══════════════════════════════════════════════════════════════
# §7 Determinism Tests
# ═══════════════════════════════════════════════════════════════

class TestDeterminism:
    """Verify all conditions produce identical results across runs."""

    @pytest.mark.parametrize("builder", [
        build_condition_a,
        build_condition_b,
        build_condition_c,
        build_condition_d,
        build_condition_e,
        build_condition_f,
        build_condition_g,
        build_condition_h,
        build_condition_ia,
        build_condition_ib,
    ])
    def test_deterministic_replay(self, builder):
        log1 = run_condition(builder, timestamp=FIXED_TIMESTAMP)
        log2 = run_condition(builder, timestamp=FIXED_TIMESTAMP)

        d1 = log1.to_dict()
        d2 = log2.to_dict()

        assert d1 == d2, (
            f"Non-determinism in condition {log1.condition}: "
            f"logs differ across runs"
        )


# ═══════════════════════════════════════════════════════════════
# §8 Serialization Tests
# ═══════════════════════════════════════════════════════════════

class TestSerialization:
    """Verify all condition logs serialize to valid JSON."""

    @pytest.mark.parametrize("builder", [
        build_condition_a,
        build_condition_b,
        build_condition_c,
        build_condition_d,
        build_condition_e,
        build_condition_f,
        build_condition_g,
        build_condition_h,
        build_condition_ia,
        build_condition_ib,
    ])
    def test_json_round_trip(self, builder):
        log = run_condition(builder, timestamp=FIXED_TIMESTAMP)
        j = log.to_json()
        parsed = json.loads(j)
        assert parsed["condition"] == log.condition
        assert isinstance(parsed["epochs"], list)


# ═══════════════════════════════════════════════════════════════
# §9 ActionRequest / Agent Model Tests
# ═══════════════════════════════════════════════════════════════

class TestActionRequest:
    """Unit tests for ActionRequest dataclass."""

    def test_to_dict_field_order(self):
        ar = ActionRequest(
            agent_id="agent_1",
            action_id="agent_1:0:0",
            action_type="WRITE",
            declared_scope=["resource_A"],
            proposed_delta={"resource_A": "owned_by_1"},
            authorities_cited=["CUD-001"],
        )
        d = ar.to_dict()
        keys = list(d.keys())
        assert keys == ["action_id", "action_type", "agent_id",
                        "authorities_cited", "declared_scope", "proposed_delta"]

    def test_frozen(self):
        ar = ActionRequest("a", "a:0:0", "WRITE", ["k"], {"k": "v"}, [])
        with pytest.raises(Exception):
            ar.agent_id = "b"
