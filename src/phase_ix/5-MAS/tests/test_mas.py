"""
IX-5 MAS — Comprehensive Unit Tests.

Covers strategies, detectors, classifiers, harness, and end-to-end conditions.
"""

import copy
import importlib
import os
import sys
import types
import unittest

# ─── 3-phase import setup (per IX-4 pattern) ───────────────────
# Phase 1: Import CUD's src package first, caching IX-2 modules.

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_MAS_ROOT = os.path.normpath(os.path.join(_TEST_DIR, ".."))
_CUD_ROOT = os.path.normpath(os.path.join(_MAS_ROOT, "..", "2-CUD"))

if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

_cud_agent_model = importlib.import_module("src.agent_model")
_cud_world_state = importlib.import_module("src.world_state")
_cud_authority_store = importlib.import_module("src.authority_store")
_cud_admissibility = importlib.import_module("src.admissibility")

# Phase 2: Replace sys.modules["src"] with synthetic package
# pointing to 5-MAS/src/. CUD sub-modules stay cached.
_mas_src_dir = os.path.join(_MAS_ROOT, "src")
_mas_src = types.ModuleType("src")
_mas_src.__path__ = [_mas_src_dir]
_mas_src.__file__ = os.path.join(_mas_src_dir, "__init__.py")
_mas_src.__package__ = "src"
sys.modules["src"] = _mas_src

# Phase 3: Import IX-5 modules (resolve via 5-MAS/src/).
from src._kernel import (
    RSA, ActionRequest, WorldState, MASObservation, MASAuthorityStore,
    PeerEvent, evaluate_admissibility, K_INST, K_OPS, ALL_KEYS,
    EXECUTED, JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT, NO_ACTION,
)
from src.detectors import (
    InstitutionalDeadlockDetector, InstitutionalLivelockDetector,
    GovernanceCollapseDetector, OrphaningDetector, AgentCollapseDetector,
    CovertHierarchyDetector,
    STATE_DEADLOCK, STATE_LIVELOCK, STATE_GOVERNANCE_COLLAPSE,
    COLLAPSE, ORPHANING, IX5_FAIL_COVERT_HIERARCHY,
)
from src.classifiers import DominationClassifier, RegimeClassifier, ZombieClassifier
from src.strategies import (
    ContestKeyAlways, OwnKeyOnly, AlternateOwnProbe,
    PartitionedPeerStrategy, AlternatingContest,
    OpportunistDeterministicCycle, HandoffRecordThenExit,
    StandbyInstitutionalProber, EpochGatedLogChatter, AlwaysSilent,
)
from src.mas_harness import (
    MASEpochController, MAS_INITIAL_STATE, AGENTS,
    run_condition, compute_condition_digest, compute_experiment_digest,
    build_condition_a, build_condition_b, build_condition_c,
    build_condition_d, build_condition_e, build_condition_f,
    _reset_auth_counter, _allow, _get_auth_ids,
)


# ────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────

def _obs(epoch: int, outcome=None, peer_events=None) -> MASObservation:
    """Create a minimal observation."""
    return MASObservation(
        epoch=epoch,
        own_last_outcome=outcome,
        peer_events=peer_events,
    )


def _make_auth_store(spec: dict[str, list[str]]) -> tuple[MASAuthorityStore, list[dict]]:
    """Create authority store from {agent_id: [keys]} spec.

    Returns (store, authorities_list).
    """
    _reset_auth_counter()
    authorities = []
    for agent_id, keys in sorted(spec.items()):
        for key in keys:
            authorities.append(_allow(key, agent_id))
    store = MASAuthorityStore()
    store.inject(authorities)
    return store, authorities


# ════════════════════════════════════════════════════════════════
#  1. Kernel Extension Tests
# ════════════════════════════════════════════════════════════════

class TestMASAuthorityStore(unittest.TestCase):
    """Tests for MASAuthorityStore (ALLOW-only, source-blind)."""

    def test_inject_and_has_allow(self):
        store, _ = _make_auth_store({"A0": ["K_POLICY", "K_LOG"]})
        self.assertTrue(store.has_allow("A0", "K_POLICY"))
        self.assertTrue(store.has_allow("A0", "K_LOG"))
        self.assertFalse(store.has_allow("A0", "K_TREASURY"))
        self.assertFalse(store.has_allow("A1", "K_POLICY"))

    def test_has_deny_always_false(self):
        store, _ = _make_auth_store({"A0": ["K_POLICY"]})
        self.assertFalse(store.has_deny_for_scope("K_POLICY", "WRITE"))

    def test_get_allow_holders(self):
        store, _ = _make_auth_store({"A0": ["K_POLICY"], "A1": ["K_POLICY"]})
        holders = store.get_allow_holders_for_scope("K_POLICY", "WRITE")
        self.assertEqual(holders, {"A0", "A1"})

    def test_get_allow_ids_for_agent(self):
        store, auths = _make_auth_store({"A0": ["K_POLICY", "K_LOG"]})
        ids = store.get_allow_ids_for_agent("A0")
        self.assertEqual(len(ids), 2)
        self.assertEqual(ids, sorted(ids))  # sorted


class TestMASObservation(unittest.TestCase):
    """Tests for MASObservation dataclass."""

    def test_obs_min_peer_events_none(self):
        obs = MASObservation(epoch=0, own_last_outcome=None)
        self.assertIsNone(obs.peer_events)

    def test_obs_full_peer_events(self):
        pe = PeerEvent(epoch=0, agent_id="A1", event_type="SILENCE")
        obs = MASObservation(epoch=1, own_last_outcome=EXECUTED, peer_events=[pe])
        self.assertEqual(len(obs.peer_events), 1)
        self.assertEqual(obs.peer_events[0].agent_id, "A1")


class TestPeerEvent(unittest.TestCase):
    """Tests for PeerEvent dataclass."""

    def test_frozen(self):
        pe = PeerEvent(epoch=0, agent_id="A0", event_type="EXIT")
        with self.assertRaises(AttributeError):
            pe.epoch = 1

    def test_action_event_fields(self):
        pe = PeerEvent(
            epoch=3, agent_id="A0", event_type="ACTION_EXECUTED",
            target_key="K_POLICY", outcome_code=EXECUTED,
        )
        self.assertEqual(pe.target_key, "K_POLICY")
        self.assertEqual(pe.outcome_code, EXECUTED)


# ════════════════════════════════════════════════════════════════
#  2. Strategy Tests
# ════════════════════════════════════════════════════════════════

class TestContestKeyAlways(unittest.TestCase):
    def test_targets_correct_key(self):
        s = ContestKeyAlways("A0", "K_POLICY", ["MAS-0001"])
        s.observe(_obs(5))
        action = s.propose_action()
        self.assertEqual(action.declared_scope, ["K_POLICY"])
        self.assertEqual(action.authorities_cited, ["MAS-0001"])
        self.assertIn("CONTEST:A0:5", action.proposed_delta["K_POLICY"])

    def test_never_exits(self):
        s = ContestKeyAlways("A0", "K_POLICY", ["MAS-0001"])
        s.observe(_obs(100))
        self.assertFalse(s.wants_to_exit())

    def test_epoch_varying_payload(self):
        s = ContestKeyAlways("A0", "K_POLICY", ["MAS-0001"])
        s.observe(_obs(0))
        a0 = s.propose_action()
        s.observe(_obs(1))
        a1 = s.propose_action()
        self.assertNotEqual(a0.proposed_delta, a1.proposed_delta)


class TestOwnKeyOnly(unittest.TestCase):
    def test_always_writes_own(self):
        s = OwnKeyOnly("A1", "K_TREASURY", ["MAS-0002"])
        for e in range(5):
            s.observe(_obs(e))
            action = s.propose_action()
            self.assertEqual(action.declared_scope, ["K_TREASURY"])
            self.assertIn(f"OWN:A1:{e}", action.proposed_delta["K_TREASURY"])


class TestPartitionedPeerStrategy(unittest.TestCase):
    def test_phase1_own_only(self):
        s = PartitionedPeerStrategy("A0", "K_POLICY", "K_TREASURY", 10,
                                    ["MAS-0001"], ["MAS-0002"])
        for e in range(10):
            s.observe(_obs(e))
            action = s.propose_action()
            self.assertEqual(action.declared_scope, ["K_POLICY"])

    def test_phase2_alternates(self):
        s = PartitionedPeerStrategy("A0", "K_POLICY", "K_TREASURY", 10,
                                    ["MAS-0001"], ["MAS-0002"])
        s.observe(_obs(10))  # even, phase 2
        a = s.propose_action()
        self.assertEqual(a.declared_scope, ["K_POLICY"])

        s.observe(_obs(11))  # odd, phase 2
        a = s.propose_action()
        self.assertEqual(a.declared_scope, ["K_TREASURY"])


class TestAlternatingContest(unittest.TestCase):
    def test_alternates_keys(self):
        s = AlternatingContest("A0", "K_POLICY", "K_LOG",
                               ["MAS-0001"], ["MAS-0002"])
        s.observe(_obs(0))
        self.assertEqual(s.propose_action().declared_scope, ["K_POLICY"])
        s.observe(_obs(1))
        self.assertEqual(s.propose_action().declared_scope, ["K_LOG"])
        s.observe(_obs(2))
        self.assertEqual(s.propose_action().declared_scope, ["K_POLICY"])


class TestOpportunistDeterministicCycle(unittest.TestCase):
    def test_cycles_through_keys(self):
        keys = ["K_LOG", "K_POLICY", "K_REGISTRY", "K_TREASURY"]
        auth = {k: [f"MAS-{i:04d}"] for i, k in enumerate(keys, 1)}
        s = OpportunistDeterministicCycle("A0", keys, auth)
        for e in range(8):
            s.observe(_obs(e))
            action = s.propose_action()
            expected_key = keys[e % 4]
            self.assertEqual(action.declared_scope, [expected_key])


class TestHandoffRecordThenExit(unittest.TestCase):
    def test_own_before_exit_epoch(self):
        s = HandoffRecordThenExit("A2", "K_REGISTRY", 12, ["MAS-0001"])
        for e in range(12):
            s.observe(_obs(e))
            self.assertFalse(s.wants_to_exit())
            action = s.propose_action()
            self.assertIn("OWN:", action.proposed_delta["K_REGISTRY"])

    def test_handoff_at_exit_epoch(self):
        s = HandoffRecordThenExit("A2", "K_REGISTRY", 12, ["MAS-0001"])
        s.observe(_obs(12))
        self.assertFalse(s.wants_to_exit())  # Not yet
        action = s.propose_action()
        self.assertIn("HANDOFF:", action.proposed_delta["K_REGISTRY"])

    def test_exits_after_handoff(self):
        s = HandoffRecordThenExit("A2", "K_REGISTRY", 12, ["MAS-0001"])
        s.observe(_obs(12))
        s.propose_action()  # Sets _exited
        s.observe(_obs(13))
        self.assertTrue(s.wants_to_exit())


class TestStandbyInstitutionalProber(unittest.TestCase):
    def test_phase1_own_key(self):
        s = StandbyInstitutionalProber("A0", "K_POLICY", ["MAS-0001"])
        for e in range(12):
            s.observe(_obs(e))
            action = s.propose_action()
            self.assertEqual(action.declared_scope, ["K_POLICY"])

    def test_phase2_probe_registry(self):
        s = StandbyInstitutionalProber("A0", "K_POLICY", ["MAS-0001"])
        s.observe(_obs(13))  # odd, 12 <= 13 < 18
        action = s.propose_action()
        self.assertEqual(action.declared_scope, ["K_REGISTRY"])

    def test_phase3_probe_alternation(self):
        s = StandbyInstitutionalProber("A0", "K_POLICY", ["MAS-0001"])
        # epoch 21: odd, epoch % 4 == 1 → K_REGISTRY
        s.observe(_obs(21))
        action = s.propose_action()
        self.assertEqual(action.declared_scope, ["K_REGISTRY"])
        # epoch 23: odd, epoch % 4 == 3 → K_LOG
        s.observe(_obs(23))
        action = s.propose_action()
        self.assertEqual(action.declared_scope, ["K_LOG"])


class TestEpochGatedLogChatter(unittest.TestCase):
    def test_silent_before_start(self):
        s = EpochGatedLogChatter("A2", "K_LOG", 15, ["MAS-0001"])
        for e in range(15):
            s.observe(_obs(e))
            self.assertIsNone(s.propose_action())

    def test_writes_from_start(self):
        s = EpochGatedLogChatter("A2", "K_LOG", 15, ["MAS-0001"])
        for e in range(15, 20):
            s.observe(_obs(e))
            action = s.propose_action()
            self.assertIsNotNone(action)
            self.assertEqual(action.declared_scope, ["K_LOG"])
            self.assertIn(f"ZOMBIE:A2:{e}", action.proposed_delta["K_LOG"])


class TestAlwaysSilent(unittest.TestCase):
    def test_always_none(self):
        s = AlwaysSilent("A3")
        s.observe(_obs(0))
        self.assertIsNone(s.propose_action())
        self.assertFalse(s.wants_to_exit())
        self.assertIsNone(s.compose_message())


# ════════════════════════════════════════════════════════════════
#  3. Detector Tests
# ════════════════════════════════════════════════════════════════

class TestInstitutionalDeadlockDetector(unittest.TestCase):
    def test_threshold_m2(self):
        d = InstitutionalDeadlockDetector(threshold=2)
        # Epoch 0: actions submitted, 0 executed
        self.assertFalse(d.record_epoch(3, 0))
        self.assertEqual(d.counter, 1)
        # Epoch 1: still deadlocked
        self.assertTrue(d.record_epoch(2, 0))
        self.assertEqual(d.counter, 2)
        self.assertTrue(d.is_active)

    def test_resets_on_execution(self):
        d = InstitutionalDeadlockDetector(threshold=2)
        d.record_epoch(3, 0)
        d.record_epoch(3, 1)  # one executed → reset
        self.assertEqual(d.counter, 0)
        self.assertFalse(d.is_active)

    def test_quiescence_not_deadlock(self):
        d = InstitutionalDeadlockDetector(threshold=2)
        # No actions submitted → not deadlock
        d.record_epoch(0, 0)
        self.assertEqual(d.counter, 0)


class TestInstitutionalLivelockDetector(unittest.TestCase):
    def test_threshold_l5_and_latch(self):
        d = InstitutionalLivelockDetector(threshold=5)
        for e in range(4):
            self.assertFalse(d.record_epoch(e, False, 2))
        # 5th epoch triggers
        self.assertTrue(d.record_epoch(4, False, 2))
        self.assertTrue(d.is_latched)
        self.assertEqual(d.latch_epoch, 4)

    def test_latch_is_permanent(self):
        d = InstitutionalLivelockDetector(threshold=5)
        for e in range(5):
            d.record_epoch(e, False, 2)
        self.assertTrue(d.is_latched)
        # After latching, record_epoch returns False (already latched)
        self.assertFalse(d.record_epoch(5, True, 2))
        self.assertTrue(d.is_latched)

    def test_resets_on_state_change(self):
        d = InstitutionalLivelockDetector(threshold=5)
        d.record_epoch(0, False, 2)
        d.record_epoch(1, False, 2)
        d.record_epoch(2, True, 2)  # state changed → reset
        self.assertEqual(d.counter, 0)


class TestGovernanceCollapseDetector(unittest.TestCase):
    def test_livelock_triggers_collapse(self):
        d = GovernanceCollapseDetector(threshold=5)
        # Livelock already latched → immediate collapse trigger
        self.assertTrue(d.record_epoch(0, False, True, 4))
        self.assertTrue(d.is_latched)

    def test_persistent_deadlock_d5(self):
        d = GovernanceCollapseDetector(threshold=5)
        for e in range(4):
            self.assertFalse(d.record_epoch(e, True, False, 4))
        self.assertTrue(d.record_epoch(4, True, False, 4))

    def test_latch_permanent(self):
        d = GovernanceCollapseDetector(threshold=5)
        d.record_epoch(0, False, True, 4)
        self.assertTrue(d.is_latched)
        # Further calls return False (already latched)
        self.assertFalse(d.record_epoch(1, False, False, 4))
        self.assertTrue(d.is_latched)

    def test_requires_active_agents(self):
        d = GovernanceCollapseDetector(threshold=5)
        # 0 active agents → no collapse
        self.assertFalse(d.record_epoch(0, False, True, 0))


class TestOrphaningDetector(unittest.TestCase):
    def test_detects_orphan(self):
        # A0 holds K_POLICY, A1 holds K_TREASURY/K_REGISTRY/K_LOG
        store, _ = _make_auth_store({
            "A0": ["K_POLICY"],
            "A1": ["K_TREASURY", "K_REGISTRY", "K_LOG"],
        })
        d = OrphaningDetector()
        # All agents active: no orphan
        newly = d.check_orphaning(0, ["A0", "A1"], store)
        self.assertEqual(newly, [])
        # A0 exits → K_POLICY orphaned (A0 was sole holder)
        newly = d.check_orphaning(1, ["A1"], store)
        self.assertIn("K_POLICY", newly)
        self.assertTrue(d.orphaning_present)

    def test_orphan_permanent(self):
        store, _ = _make_auth_store({
            "A0": ["K_POLICY"],
            "A1": ["K_TREASURY", "K_REGISTRY", "K_LOG"],
        })
        d = OrphaningDetector()
        d.check_orphaning(0, ["A1"], store)  # K_POLICY orphaned
        # Check again: K_POLICY already orphaned, not re-reported
        newly = d.check_orphaning(1, ["A1"], store)
        self.assertEqual(newly, [])
        self.assertIn("K_POLICY", d.orphaned_keys)


class TestAgentCollapseDetector(unittest.TestCase):
    def test_collapse_when_empty(self):
        self.assertTrue(AgentCollapseDetector.is_collapse([]))

    def test_no_collapse_with_agents(self):
        self.assertFalse(AgentCollapseDetector.is_collapse(["A0"]))


class TestCovertHierarchyDetector(unittest.TestCase):
    def test_no_violation_with_allow(self):
        store, _ = _make_auth_store({"A0": ["K_POLICY"]})
        d = CovertHierarchyDetector()
        action = ActionRequest(
            agent_id="A0", action_id="A0:0:0", action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": "test"},
            authorities_cited=["MAS-0001"],
        )
        found = d.check_epoch(0, {"A0": action}, {"A0": EXECUTED}, store)
        self.assertFalse(found)

    def test_violation_without_allow(self):
        store, _ = _make_auth_store({"A1": ["K_POLICY"]})  # A0 has no authority
        d = CovertHierarchyDetector()
        action = ActionRequest(
            agent_id="A0", action_id="A0:0:0", action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": "test"},
            authorities_cited=[],
        )
        found = d.check_epoch(0, {"A0": action}, {"A0": EXECUTED}, store)
        self.assertTrue(found)
        self.assertTrue(d.fired)


# ════════════════════════════════════════════════════════════════
#  4. Classifier Tests
# ════════════════════════════════════════════════════════════════

class TestDominationClassifier(unittest.TestCase):
    def test_no_domination_equal(self):
        dc = DominationClassifier(["A0", "A1", "A2", "A3"])
        logs = []
        for e in range(10):
            agent_id = f"A{e % 4}"
            action = ActionRequest(
                agent_id=agent_id, action_id=f"{agent_id}:{e}:0",
                action_type="WRITE", declared_scope=["K_POLICY"],
                proposed_delta={"K_POLICY": "x"}, authorities_cited=[],
            )
            logs.append({
                "actions": {agent_id: action},
                "outcomes": {agent_id: EXECUTED},
            })
        result = dc.compute(logs)
        self.assertFalse(result["domination_detected"])

    def test_domination_detected(self):
        dc = DominationClassifier(["A0", "A1"])
        action = ActionRequest(
            agent_id="A0", action_id="A0:0:0", action_type="WRITE",
            declared_scope=["K_POLICY"], proposed_delta={"K_POLICY": "x"},
            authorities_cited=[],
        )
        logs = [{"actions": {"A0": action}, "outcomes": {"A0": EXECUTED}}] * 10
        result = dc.compute(logs)
        self.assertTrue(result["domination_detected"])
        self.assertGreaterEqual(result["domination_index"]["A0"], 0.75)
        self.assertLessEqual(result["domination_index"]["A1"], 0.05)


class TestRegimeClassifier(unittest.TestCase):
    def test_all_conditions_classified(self):
        for cond_id in "ABCDEF":
            c = RegimeClassifier.classify(cond_id)
            self.assertIn("authority_overlap", c)
            self.assertIn("persistence_asymmetry", c)
            self.assertIn("exit_topology", c)
            self.assertIn("observation_surface", c)

    def test_condition_a_symmetric(self):
        c = RegimeClassifier.classify("A")
        self.assertEqual(c["authority_overlap"], "SYMMETRIC")
        self.assertEqual(c["observation_surface"], "OBS_MIN")

    def test_condition_e_cascade(self):
        c = RegimeClassifier.classify("E")
        self.assertEqual(c["exit_topology"], "CASCADE")
        self.assertEqual(c["persistence_asymmetry"], "SCHEDULED_EXIT")


class TestZombieClassifier(unittest.TestCase):
    def test_no_zombies(self):
        zc = ZombieClassifier()
        result = zc.compute([], {"K_POLICY": "P0"}, {"K_POLICY": "P0"})
        self.assertEqual(result["zombie_write_count"], 0)
        self.assertEqual(result["zombie_write_rate"], 0.0)

    def test_zombie_writes(self):
        zc = ZombieClassifier()
        action = ActionRequest(
            agent_id="A0", action_id="A0:10:0", action_type="WRITE",
            declared_scope=["K_POLICY"], proposed_delta={"K_POLICY": "zombie"},
            authorities_cited=["MAS-0001"],
        )
        logs = [{"actions": {"A0": action}, "outcomes": {"A0": EXECUTED}}] * 5
        result = zc.compute(
            logs,
            {"K_POLICY": "P0", "K_TREASURY": "T0", "K_REGISTRY": "R0", "K_LOG": ""},
            {"K_POLICY": "zombie", "K_TREASURY": "T0", "K_REGISTRY": "R0", "K_LOG": ""},
        )
        self.assertEqual(result["zombie_write_count"], 5)
        self.assertEqual(result["zombie_write_rate"], 1.0)
        self.assertEqual(result["zombie_progress_delta"], 1)


# ════════════════════════════════════════════════════════════════
#  5. Authority Factory Tests
# ════════════════════════════════════════════════════════════════

class TestAuthorityFactory(unittest.TestCase):
    def test_authority_id_format(self):
        _reset_auth_counter()
        a = _allow("K_POLICY", "A0")
        self.assertEqual(a["authority_id"], "MAS-0001")
        self.assertEqual(a["commitment"], "ALLOW")
        self.assertEqual(a["created_epoch"], 0)
        self.assertEqual(a["holder_agent_id"], "A0")
        self.assertEqual(a["issuer_agent_id"], "harness")
        self.assertEqual(a["status"], "ACTIVE")
        self.assertEqual(a["scope"][0]["target"], "STATE:/K_POLICY")
        self.assertEqual(a["scope"][0]["operation"], "WRITE")

    def test_sequential_ids(self):
        _reset_auth_counter()
        a1 = _allow("K_POLICY", "A0")
        a2 = _allow("K_LOG", "A1")
        self.assertEqual(a1["authority_id"], "MAS-0001")
        self.assertEqual(a2["authority_id"], "MAS-0002")

    def test_get_auth_ids(self):
        _reset_auth_counter()
        auths = [
            _allow("K_POLICY", "A0"),
            _allow("K_LOG", "A0"),
            _allow("K_POLICY", "A1"),
        ]
        ids = _get_auth_ids(auths, "A0", "K_POLICY")
        self.assertEqual(ids, ["MAS-0001"])
        ids = _get_auth_ids(auths, "A0", "K_LOG")
        self.assertEqual(ids, ["MAS-0002"])


# ════════════════════════════════════════════════════════════════
#  6. Admissibility Integration Tests
# ════════════════════════════════════════════════════════════════

class TestAdmissibilityWithMASStore(unittest.TestCase):
    """Test that IX-2 evaluate_admissibility works with MASAuthorityStore."""

    def test_single_allowed_action(self):
        store, auths = _make_auth_store({"A0": ["K_POLICY"]})
        action = ActionRequest(
            agent_id="A0", action_id="A0:0:0", action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": "new"},
            authorities_cited=[auths[0]["authority_id"]],
        )
        outcomes, p1, p2 = evaluate_admissibility({"A0": action}, store)
        self.assertEqual(outcomes["A0"], EXECUTED)

    def test_two_writes_same_key_refuse_both(self):
        store, auths = _make_auth_store({
            "A0": ["K_POLICY"], "A1": ["K_POLICY"],
        })
        a0_auth = _get_auth_ids(auths, "A0", "K_POLICY")
        a1_auth = _get_auth_ids(auths, "A1", "K_POLICY")
        actions = {
            "A0": ActionRequest(
                agent_id="A0", action_id="A0:0:0", action_type="WRITE",
                declared_scope=["K_POLICY"],
                proposed_delta={"K_POLICY": "a0"},
                authorities_cited=a0_auth,
            ),
            "A1": ActionRequest(
                agent_id="A1", action_id="A1:0:0", action_type="WRITE",
                declared_scope=["K_POLICY"],
                proposed_delta={"K_POLICY": "a1"},
                authorities_cited=a1_auth,
            ),
        }
        outcomes, _, _ = evaluate_admissibility(actions, store)
        self.assertEqual(outcomes["A0"], JOINT_ADMISSIBILITY_FAILURE)
        self.assertEqual(outcomes["A1"], JOINT_ADMISSIBILITY_FAILURE)

    def test_no_authority_action_fault(self):
        store, _ = _make_auth_store({"A0": ["K_POLICY"]})
        action = ActionRequest(
            agent_id="A1", action_id="A1:0:0", action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": "hack"},
            authorities_cited=[],
        )
        outcomes, _, _ = evaluate_admissibility({"A1": action}, store)
        self.assertIn(outcomes["A1"], (JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT))

    def test_none_action_is_no_action(self):
        store, _ = _make_auth_store({"A0": ["K_POLICY"]})
        outcomes, _, _ = evaluate_admissibility({"A0": None}, store)
        self.assertEqual(outcomes["A0"], NO_ACTION)


# ════════════════════════════════════════════════════════════════
#  7. Condition Builder Tests
# ════════════════════════════════════════════════════════════════

class TestConditionBuilders(unittest.TestCase):
    def test_condition_a_structure(self):
        c = build_condition_a()
        self.assertEqual(c["condition"], "A")
        self.assertEqual(c["max_epochs"], 30)
        self.assertEqual(c["obs_mode"], "OBS_MIN")
        self.assertEqual(len(c["agents"]), 4)
        self.assertEqual(len(c["authorities"]), 16)  # 4 agents × 4 keys

    def test_condition_b_partitioned(self):
        c = build_condition_b()
        self.assertEqual(len(c["authorities"]), 4)  # 1 key per agent

    def test_condition_c_partial_overlap(self):
        c = build_condition_c()
        self.assertEqual(len(c["authorities"]), 6)  # A0:2 + A1:2 + A2:1 + A3:1

    def test_condition_d_asymmetric(self):
        c = build_condition_d()
        self.assertEqual(len(c["authorities"]), 7)  # A0:4 + A1:1 + A2:1 + A3:1

    def test_condition_e_max_epochs(self):
        c = build_condition_e()
        self.assertEqual(c["max_epochs"], 40)
        self.assertEqual(c["obs_mode"], "OBS_FULL")

    def test_condition_f_max_epochs(self):
        c = build_condition_f()
        self.assertEqual(c["max_epochs"], 60)
        self.assertEqual(len(c["authorities"]), 16)


# ════════════════════════════════════════════════════════════════
#  8. End-to-End Condition Tests
# ════════════════════════════════════════════════════════════════

class TestConditionA(unittest.TestCase):
    """Condition A: Symmetric Sovereign Peers → Livelock + Collapse."""

    @classmethod
    def setUpClass(cls):
        cls.result = run_condition("A")

    def test_passes(self):
        self.assertEqual(self.result["condition_result"], "PASS")

    def test_governance_collapse(self):
        self.assertIn(
            self.result["terminal_classification"],
            (STATE_GOVERNANCE_COLLAPSE, STATE_LIVELOCK),
        )

    def test_livelock_latched(self):
        final_det = self.result["epochs"][-1]["detectors"]
        self.assertTrue(final_det["livelock_latched"])

    def test_no_fail_tokens(self):
        self.assertEqual(self.result["ix5_fail_tokens"], [])

    def test_no_progress(self):
        # All K_POLICY writes collide → no institutional progress
        am = self.result["aggregate_metrics"]
        self.assertEqual(am["epoch_progress_rate_K_INST"], 0.0)

    def test_high_refusal(self):
        am = self.result["aggregate_metrics"]
        self.assertGreater(am["refusal_rate"], 0.9)


class TestConditionB(unittest.TestCase):
    """Condition B: Partitioned Peers → Max epochs, no livelock."""

    @classmethod
    def setUpClass(cls):
        cls.result = run_condition("B")

    def test_passes(self):
        self.assertEqual(self.result["condition_result"], "PASS")

    def test_max_epochs(self):
        self.assertEqual(len(self.result["epochs"]), 30)

    def test_no_collapse(self):
        final_det = self.result["epochs"][-1]["detectors"]
        self.assertFalse(final_det["governance_collapse_latched"])

    def test_phase1_progress(self):
        # First 10 epochs: each agent writes own key undisputed → progress
        am = self.result["aggregate_metrics"]
        self.assertGreater(am["epoch_progress_rate_K_INST"], 0.0)


class TestConditionC(unittest.TestCase):
    """Condition C: Boundary Conflict.

    A0/A1 collide on K_POLICY (even) and K_LOG (odd) every epoch.
    A2/A3 write uncontested K_REGISTRY/K_TREASURY → K_INST state changes
    every epoch, so livelock never triggers. Terminal = max epochs.
    """

    @classmethod
    def setUpClass(cls):
        cls.result = run_condition("C")

    def test_passes(self):
        self.assertEqual(self.result["condition_result"], "PASS")

    def test_obs_full(self):
        self.assertEqual(self.result["observation_mode"], "OBS_FULL")

    def test_max_epochs(self):
        self.assertEqual(len(self.result["epochs"]), 35)

    def test_interference_present(self):
        # A0/A1 collide every epoch → interference rate > 0
        am = self.result["aggregate_metrics"]
        self.assertGreater(am["write_overlap_rate_K_INST"], 0.0)

    def test_no_livelock(self):
        # A2/A3 progress prevents livelock
        final_det = self.result["epochs"][-1]["detectors"]
        self.assertFalse(final_det["livelock_latched"])


class TestConditionD(unittest.TestCase):
    """Condition D: Persistent Asymmetry → Max epochs, no domination."""

    @classmethod
    def setUpClass(cls):
        cls.result = run_condition("D")

    def test_passes(self):
        self.assertEqual(self.result["condition_result"], "PASS")

    def test_max_epochs(self):
        self.assertEqual(len(self.result["epochs"]), 35)

    def test_no_domination(self):
        am = self.result["aggregate_metrics"]
        self.assertFalse(am["domination_detected"])


class TestConditionE(unittest.TestCase):
    """Condition E: Exit Cascades → Orphaning on K_REGISTRY and K_LOG."""

    @classmethod
    def setUpClass(cls):
        cls.result = run_condition("E")

    def test_passes(self):
        self.assertEqual(self.result["condition_result"], "PASS")

    def test_max_epochs(self):
        self.assertEqual(len(self.result["epochs"]), 40)

    def test_orphaning(self):
        final_det = self.result["epochs"][-1]["detectors"]
        self.assertIn("K_REGISTRY", final_det["orphaned_keys"])
        self.assertIn("K_LOG", final_det["orphaned_keys"])

    def test_exits_occurred(self):
        all_exits = []
        for log in self.result["epochs"]:
            all_exits.extend(log["exits"])
        self.assertIn("A2", all_exits)
        self.assertIn("A3", all_exits)


class TestConditionF(unittest.TestCase):
    """Condition F: Zombie Peer Interaction → Collapse + zombie writes."""

    @classmethod
    def setUpClass(cls):
        cls.result = run_condition("F")

    def test_passes(self):
        self.assertEqual(self.result["condition_result"], "PASS")

    def test_max_epochs(self):
        self.assertEqual(len(self.result["epochs"]), 60)

    def test_governance_collapse(self):
        self.assertIn(
            self.result["terminal_classification"],
            (STATE_GOVERNANCE_COLLAPSE, STATE_LIVELOCK),
        )

    def test_zombie_writes(self):
        am = self.result["aggregate_metrics"]
        self.assertGreater(am["zombie_write_count"], 0)


# ════════════════════════════════════════════════════════════════
#  9. Replay Determinism
# ════════════════════════════════════════════════════════════════

class TestReplayDeterminism(unittest.TestCase):
    """Same inputs must produce same outputs."""

    def test_condition_a_deterministic(self):
        r1 = run_condition("A")
        r2 = run_condition("A")
        d1 = compute_condition_digest(r1)
        d2 = compute_condition_digest(r2)
        self.assertEqual(d1, d2)

    def test_condition_b_deterministic(self):
        r1 = run_condition("B")
        r2 = run_condition("B")
        d1 = compute_condition_digest(r1)
        d2 = compute_condition_digest(r2)
        self.assertEqual(d1, d2)


# ════════════════════════════════════════════════════════════════
#  10. Covert Hierarchy Never Fires
# ════════════════════════════════════════════════════════════════

class TestCovertHierarchyNeverFires(unittest.TestCase):
    """Under correct implementation, no condition should trigger
    the covert hierarchy detector."""

    def _check_no_covert(self, cond_id):
        result = run_condition(cond_id)
        self.assertNotIn(
            IX5_FAIL_COVERT_HIERARCHY,
            result["ix5_fail_tokens"],
            f"Covert hierarchy fired in condition {cond_id}",
        )

    def test_a(self):
        self._check_no_covert("A")

    def test_b(self):
        self._check_no_covert("B")

    def test_c(self):
        self._check_no_covert("C")

    def test_d(self):
        self._check_no_covert("D")

    def test_e(self):
        self._check_no_covert("E")

    def test_f(self):
        self._check_no_covert("F")


# ════════════════════════════════════════════════════════════════
#  11. Digest Computation
# ════════════════════════════════════════════════════════════════

class TestDigestComputation(unittest.TestCase):
    def test_digest_excludes_timestamp(self):
        r1 = run_condition("A")
        r2 = copy.deepcopy(r1)
        r2["timestamp"] = "2099-01-01T00:00:00+00:00"
        d1 = compute_condition_digest(r1)
        d2 = compute_condition_digest(r2)
        self.assertEqual(d1, d2)

    def test_experiment_digest_order_matters(self):
        digests = {c: f"hash_{c}" for c in "ABCDEF"}
        d1 = compute_experiment_digest(digests)
        digests_rev = {c: f"hash_{c}" for c in "FEDCBA"}
        d2 = compute_experiment_digest(digests_rev)
        # Same content, concatenation uses fixed A-F order
        self.assertEqual(d1, d2)


# ════════════════════════════════════════════════════════════════
#  12. Regime Classification Tests
# ════════════════════════════════════════════════════════════════

class TestRegimeInResults(unittest.TestCase):
    """Verify regime_classification is present in all condition results."""

    def test_all_conditions_have_regime(self):
        for cond_id in "ABCDEF":
            result = run_condition(cond_id)
            rc = result["regime_classification"]
            self.assertIn("authority_overlap", rc)
            self.assertIn("persistence_asymmetry", rc)
            self.assertIn("exit_topology", rc)
            self.assertIn("observation_surface", rc)


if __name__ == "__main__":
    unittest.main()
