"""
IX-4 Injection Politics — Comprehensive Unit Tests

Per preregistration: tests strategy behavior, injection triggers,
detector thresholds, classifier computations, and full condition runs.
"""

import copy
import importlib
import os
import sys
import json
import types
import pytest
from typing import Any, Optional

# ─── Path setup (3-phase, per IX-3 pattern) ────────────────────

_TEST_DIR = os.path.dirname(os.path.abspath(__file__))
_IP_ROOT = os.path.normpath(os.path.join(_TEST_DIR, '..'))
_CUD_ROOT = os.path.normpath(os.path.join(_IP_ROOT, '..', '2-CUD'))

# Phase 1: Import CUD's src package first, caching all IX-2 modules
# in sys.modules so that _kernel.py's importlib.import_module calls
# return the cached CUD modules.
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

_cud_agent_model = importlib.import_module("src.agent_model")
_cud_world_state = importlib.import_module("src.world_state")
_cud_authority_store = importlib.import_module("src.authority_store")
_cud_admissibility = importlib.import_module("src.admissibility")

# Phase 2: Replace sys.modules["src"] with a synthetic package
# whose __path__ points to 4-IP/src/. CUD sub-modules stay cached.
_ip_src_dir = os.path.join(_IP_ROOT, 'src')
_ip_src = types.ModuleType("src")
_ip_src.__path__ = [_ip_src_dir]
_ip_src.__file__ = os.path.join(_ip_src_dir, '__init__.py')
_ip_src.__package__ = "src"
sys.modules["src"] = _ip_src

# Phase 3: Import IX-4 modules (resolve via 4-IP/src/).
from src._kernel import (
    RSA, ActionRequest, Message, IPObservation,
    WorldState, IPAuthorityStore,
    evaluate_admissibility,
    EXECUTED, JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT, NO_ACTION,
)
from src.strategies import (
    ContestPolicyAlways,
    RefusalHardliner,
    Opportunist,
    CaptureSeeker,
    ComplianceSignaler,
)
from src.strategies._helpers import cite_for_key, canonical_artifact_string
from src.injection_engine import (
    InjectionEngine, InjectionSpec, InjectionEvent,
    STATE_TRIGGERED, FIXED_EPOCH, PREDICATE_CHECK,
)
from src.detectors import (
    K_INST, K_OPS, ALL_KEYS,
    STATE_DEADLOCK, STATE_LIVELOCK, STATE_GOVERNANCE_COLLAPSE,
    COLLAPSE, ORPHANING,
    InstitutionalDeadlockDetector,
    InstitutionalLivelockDetector,
    GovernanceCollapseDetector,
    OrphaningDetector,
    AgentCollapseDetector,
)
from src.classifiers import CaptureClassifier, DependencyClassifier, ZombieClassifier
from src.ip_harness import (
    IP_INITIAL_STATE, AGENTS,
    build_condition_a, build_condition_b, build_condition_c,
    build_condition_d, build_condition_e,
    run_condition, IPEpochController, IPAuthorityStore as HarnessStore,
    _allow, _reset_auth_counter,
)


# ─── Helpers ────────────────────────────────────────────────────

def make_allow(key: str, holder: str, auth_id: str, epoch: int = 0) -> dict:
    """Create a test ALLOW artifact."""
    return {
        "authority_id": auth_id,
        "commitment": "ALLOW",
        "created_epoch": epoch,
        "holder_agent_id": holder,
        "issuer_agent_id": "harness",
        "scope": [{"operation": "WRITE", "target": f"STATE:/{key}"}],
        "status": "ACTIVE",
    }


def make_deny(key: str, holder: str = "harness", auth_id: str = "DENY-001") -> dict:
    """Create a test DENY artifact."""
    return {
        "authority_id": auth_id,
        "commitment": "DENY",
        "created_epoch": 0,
        "holder_agent_id": holder,
        "issuer_agent_id": "harness",
        "scope": [{"operation": "WRITE", "target": f"STATE:/{key}"}],
        "status": "ACTIVE",
    }


def make_observation(
    epoch: int,
    available_authorities: list[str] = None,
    own_last_outcome: str = None,
    world_state: dict = None,
) -> IPObservation:
    """Create a test IPObservation."""
    return IPObservation(
        epoch=epoch,
        world_state=world_state or copy.deepcopy(IP_INITIAL_STATE),
        own_last_outcome=own_last_outcome,
        own_last_action_id=None,
        own_last_declared_scope=None,
        messages=[],
        available_authorities=available_authorities or [],
    )


def build_lookup(*artifacts: dict) -> dict[str, dict[str, Any]]:
    """Build authority lookup from artifacts."""
    return {a["authority_id"]: a for a in artifacts}


# ═══════════════════════════════════════════════════════════════
# §1: IPAuthorityStore Tests
# ═══════════════════════════════════════════════════════════════

class TestIPAuthorityStore:
    """Test source-blind authority store."""

    def test_inject_baseline(self):
        store = IPAuthorityStore()
        auth = make_allow("K_POLICY", "A0", "IP-0001")
        store.inject([auth])
        assert store.get_by_id("IP-0001") is not None

    def test_source_blind_is_held_by(self):
        """is_held_by must NOT check created_epoch."""
        store = IPAuthorityStore()
        baseline = make_allow("K_POLICY", "A0", "IP-0001", epoch=0)
        injected = make_allow("K_POLICY", "A0", "IP-0002", epoch=6)
        store.inject([baseline, injected])

        # Both should be held by A0 regardless of created_epoch
        assert store.is_held_by("IP-0001", "A0") is True
        assert store.is_held_by("IP-0002", "A0") is True
        assert store.is_held_by("IP-0001", "A1") is False

    def test_get_allow_ids_for_agent(self):
        store = IPAuthorityStore()
        a1 = make_allow("K_LOG", "A0", "IP-0001")
        a2 = make_allow("K_POLICY", "A0", "IP-0002", epoch=6)
        a3 = make_allow("K_LOG", "A1", "IP-0003")
        store.inject([a1, a2, a3])

        ids = store.get_allow_ids_for_agent("A0")
        assert "IP-0001" in ids
        assert "IP-0002" in ids
        assert "IP-0003" not in ids

    def test_get_allow_ids_canonical_order(self):
        """Authority IDs should be sorted by canonical artifact serialization."""
        store = IPAuthorityStore()
        # Create two artifacts — canonical order should be deterministic
        a1 = make_allow("K_POLICY", "A0", "IP-0002")
        a2 = make_allow("K_LOG", "A0", "IP-0001")
        store.inject([a1, a2])

        ids = store.get_allow_ids_for_agent("A0")
        assert len(ids) == 2
        # Verify order is by canonical serialization (not by ID)
        c1 = canonical_artifact_string(a1)
        c2 = canonical_artifact_string(a2)
        if c1 < c2:
            assert ids == ["IP-0002", "IP-0001"]
        else:
            assert ids == ["IP-0001", "IP-0002"]

    def test_multi_inject(self):
        """inject() can be called multiple times (for injection)."""
        store = IPAuthorityStore()
        store.inject([make_allow("K_LOG", "A0", "IP-0001")])
        store.inject([make_allow("K_POLICY", "A0", "IP-0002", epoch=6)])
        assert len(store.get_all()) == 2

    def test_has_deny(self):
        store = IPAuthorityStore()
        store.inject([make_deny("K_POLICY")])
        assert store.has_deny_for_scope("K_POLICY", "WRITE") is True
        assert store.has_deny_for_scope("K_LOG", "WRITE") is False


# ═══════════════════════════════════════════════════════════════
# §2: Strategy Tests
# ═══════════════════════════════════════════════════════════════

class TestContestPolicyAlways:
    """Test ContestPolicyAlways strategy."""

    def test_always_targets_k_policy(self):
        agent = ContestPolicyAlways("A0")
        auth = make_allow("K_POLICY", "A0", "IP-0001")
        agent.set_authority_lookup(build_lookup(auth))
        agent.observe(make_observation(0, ["IP-0001"]))
        action = agent.propose_action()
        assert action is not None
        assert action.declared_scope == ["K_POLICY"]
        assert action.proposed_delta == {"K_POLICY": "POLICY_CONTEST"}

    def test_submits_without_authority(self):
        """ContestPolicyAlways still submits even without authority."""
        agent = ContestPolicyAlways("A0")
        agent.set_authority_lookup({})
        agent.observe(make_observation(0, []))
        action = agent.propose_action()
        assert action is not None
        assert action.authorities_cited == []

    def test_cites_injected_authority(self):
        """Should cite injected authority if it covers K_POLICY."""
        agent = ContestPolicyAlways("A0")
        injected = make_allow("K_POLICY", "A0", "IP-0005", epoch=6)
        agent.set_authority_lookup(build_lookup(injected))
        agent.observe(make_observation(7, ["IP-0005"]))
        action = agent.propose_action()
        assert action.authorities_cited == ["IP-0005"]

    def test_never_exits(self):
        agent = ContestPolicyAlways("A0")
        agent.observe(make_observation(0))
        assert agent.wants_to_exit() is False

    def test_action_id_format(self):
        agent = ContestPolicyAlways("A0")
        agent.set_authority_lookup({})
        agent.observe(make_observation(5, []))
        action = agent.propose_action()
        assert action.action_id == "A0:5:0"


class TestRefusalHardliner:
    """Test RefusalHardliner strategy."""

    def test_only_epoch0_authorities(self):
        """Must only cite epoch-0 authorities, even when injected ones appear."""
        agent = RefusalHardliner("A2")
        baseline = make_allow("K_POLICY", "A2", "IP-0001")
        injected = make_allow("K_POLICY", "A2", "IP-0005", epoch=6)
        lookup = build_lookup(baseline, injected)

        # Epoch 0: see baseline
        agent.set_authority_lookup(lookup)
        agent.observe(make_observation(0, ["IP-0001"]))
        action = agent.propose_action()
        assert action.authorities_cited == ["IP-0001"]

        # Epoch 7: see both — should still only cite baseline
        agent.observe(make_observation(7, ["IP-0001", "IP-0005"]))
        action = agent.propose_action()
        assert action.authorities_cited == ["IP-0001"]
        assert "IP-0005" not in action.authorities_cited

    def test_always_targets_k_policy(self):
        agent = RefusalHardliner("A1")
        agent.set_authority_lookup({})
        agent.observe(make_observation(0, []))
        action = agent.propose_action()
        assert action.declared_scope == ["K_POLICY"]
        assert action.proposed_delta == {"K_POLICY": "POLICY_PROPOSAL"}

    def test_no_baseline_authority(self):
        """Submits with empty citations if no baseline covers K_POLICY."""
        agent = RefusalHardliner("A1")
        log_auth = make_allow("K_LOG", "A1", "IP-0001")
        agent.set_authority_lookup(build_lookup(log_auth))
        agent.observe(make_observation(0, ["IP-0001"]))
        action = agent.propose_action()
        assert action.authorities_cited == []


class TestOpportunistStandard:
    """Test Opportunist STANDARD mode."""

    def test_prefers_untried_keys(self):
        agent = Opportunist("A1", mode="STANDARD")
        auth1 = make_allow("K_LOG", "A1", "IP-0001")
        auth2 = make_allow("K_OPS_A", "A1", "IP-0002")
        lookup = build_lookup(auth1, auth2)
        agent.set_authority_lookup(lookup)
        agent.observe(make_observation(0, ["IP-0001", "IP-0002"]))
        action = agent.propose_action()
        # K_OPS_A comes before K_LOG in preferred order
        assert action.declared_scope == ["K_OPS_A"]
        assert action.proposed_delta == {"K_OPS_A": "OPPORTUNIST_ACTION"}

    def test_prefers_successful_keys(self):
        agent = Opportunist("A1", mode="STANDARD")
        auth1 = make_allow("K_LOG", "A1", "IP-0001")
        auth2 = make_allow("K_OPS_A", "A1", "IP-0002")
        lookup = build_lookup(auth1, auth2)
        agent.set_authority_lookup(lookup)

        # Epoch 0: try K_OPS_A
        agent.observe(make_observation(0, ["IP-0001", "IP-0002"]))
        action0 = agent.propose_action()
        assert action0.declared_scope == ["K_OPS_A"]

        # Epoch 1: K_OPS_A was executed, K_LOG untried
        agent.observe(make_observation(1, ["IP-0001", "IP-0002"],
                                        own_last_outcome="EXECUTED"))
        action1 = agent.propose_action()
        # K_LOG is still untried → preferred
        assert action1.declared_scope == ["K_LOG"]

    def test_returns_none_without_authority(self):
        agent = Opportunist("A1", mode="STANDARD")
        agent.set_authority_lookup({})
        agent.observe(make_observation(0, []))
        action = agent.propose_action()
        assert action is None

    def test_governance_keys_preferred(self):
        """K_POLICY > K_TREASURY > K_REGISTRY > K_OPS_A > K_OPS_B > K_LOG."""
        agent = Opportunist("A1", mode="STANDARD")
        auths = [
            make_allow("K_LOG", "A1", "IP-0001"),
            make_allow("K_POLICY", "A1", "IP-0002"),
            make_allow("K_OPS_A", "A1", "IP-0003"),
        ]
        lookup = build_lookup(*auths)
        agent.set_authority_lookup(lookup)
        agent.observe(make_observation(0, ["IP-0001", "IP-0002", "IP-0003"]))
        action = agent.propose_action()
        assert action.declared_scope == ["K_POLICY"]


class TestOpportunistMultiKey:
    """Test Opportunist MULTI_KEY mode."""

    def test_cycles_through_available_keys(self):
        agent = Opportunist("A0", mode="MULTI_KEY")
        auth1 = make_allow("K_LOG", "A0", "IP-0001")
        auth2 = make_allow("K_OPS_A", "A0", "IP-0002")
        lookup = build_lookup(auth1, auth2)
        agent.set_authority_lookup(lookup)

        # Cycle: K_POLICY(skip) → K_TREASURY(skip) → K_REGISTRY(skip) → K_OPS_A → K_OPS_B(skip) → K_LOG
        agent.observe(make_observation(0, ["IP-0001", "IP-0002"]))
        a0 = agent.propose_action()
        # First available in cycle: K_OPS_A (index 3)
        # Wait — cycle starts at index 0 (K_POLICY), skips to K_OPS_A
        assert a0.declared_scope[0] in ("K_OPS_A", "K_LOG")

    def test_resets_cycle_on_expansion(self):
        """Cycle index resets when authority surface expands."""
        agent = Opportunist("A0", mode="MULTI_KEY")
        auth1 = make_allow("K_LOG", "A0", "IP-0001")
        auth2 = make_allow("K_OPS_A", "A0", "IP-0002")
        lookup = build_lookup(auth1, auth2)
        agent.set_authority_lookup(lookup)

        # Epoch 0: 2 authorities
        agent.observe(make_observation(0, ["IP-0001", "IP-0002"]))
        agent.propose_action()

        # Add new authority (expansion)
        auth3 = make_allow("K_POLICY", "A0", "IP-0003", epoch=6)
        lookup_expanded = build_lookup(auth1, auth2, auth3)
        agent.set_authority_lookup(lookup_expanded)

        # Epoch 6: 3 authorities — surface expanded, cycle resets
        agent.observe(make_observation(6, ["IP-0001", "IP-0002", "IP-0003"]))
        action = agent.propose_action()
        # After reset, cycle starts from index 0 → K_POLICY is now available
        assert action.declared_scope == ["K_POLICY"]


class TestCaptureSeeker:
    """Test CaptureSeeker strategy."""

    def test_prioritizes_governance_keys(self):
        agent = CaptureSeeker("A0")
        auths = [
            make_allow("K_LOG", "A0", "IP-0001"),
            make_allow("K_POLICY", "A0", "IP-0002", epoch=6),
            make_allow("K_OPS_A", "A0", "IP-0003"),
        ]
        lookup = build_lookup(*auths)
        agent.set_authority_lookup(lookup)
        agent.observe(make_observation(7, ["IP-0001", "IP-0002", "IP-0003"]))
        action = agent.propose_action()
        assert action.declared_scope == ["K_POLICY"]
        assert action.proposed_delta == {"K_POLICY": "CAPTURE_MARKER"}

    def test_falls_back_to_ops(self):
        agent = CaptureSeeker("A0")
        auth = make_allow("K_OPS_A", "A0", "IP-0001")
        agent.set_authority_lookup(build_lookup(auth))
        agent.observe(make_observation(0, ["IP-0001"]))
        action = agent.propose_action()
        assert action.declared_scope == ["K_OPS_A"]

    def test_returns_none_without_authority(self):
        agent = CaptureSeeker("A0")
        agent.set_authority_lookup({})
        agent.observe(make_observation(0, []))
        action = agent.propose_action()
        assert action is None


class TestComplianceSignaler:
    """Test ComplianceSignaler strategy."""

    def test_default_contests_policy(self):
        agent = ComplianceSignaler("A0")
        auth = make_allow("K_POLICY", "A0", "IP-0001")
        agent.set_authority_lookup(build_lookup(auth))
        agent.observe(make_observation(0, ["IP-0001"]))
        action = agent.propose_action()
        assert action.declared_scope == ["K_POLICY"]
        assert action.proposed_delta == {"K_POLICY": "POLICY_CONTEST"}

    def test_writes_compliance_ack(self):
        """Writes COMPLIANCE_ACK at epoch 5 if deadlock_count >= 2."""
        agent = ComplianceSignaler("A0")
        auth_log = make_allow("K_LOG", "A0", "IP-0001")
        auth_pol = make_allow("K_POLICY", "A0", "IP-0002")
        lookup = build_lookup(auth_log, auth_pol)
        agent.set_authority_lookup(lookup)

        # Epochs 0-2: accumulate deadlock
        for e in range(3):
            outcome = "JOINT_ADMISSIBILITY_FAILURE" if e > 0 else None
            agent.observe(make_observation(e, ["IP-0001", "IP-0002"],
                                            own_last_outcome=outcome))
            agent.propose_action()

        # Epoch 3: another JAF
        agent.observe(make_observation(3, ["IP-0001", "IP-0002"],
                                        own_last_outcome="JOINT_ADMISSIBILITY_FAILURE"))
        agent.propose_action()

        # Epoch 4: another JAF
        agent.observe(make_observation(4, ["IP-0001", "IP-0002"],
                                        own_last_outcome="JOINT_ADMISSIBILITY_FAILURE"))
        agent.propose_action()

        # Epoch 5: should write ack (deadlock_count should be >= 2)
        agent.observe(make_observation(5, ["IP-0001", "IP-0002"],
                                        own_last_outcome="JOINT_ADMISSIBILITY_FAILURE"))
        action = agent.propose_action()
        assert action.declared_scope == ["K_LOG"]
        assert action.proposed_delta == {"K_LOG": "COMPLIANCE_ACK"}

    def test_ack_is_one_shot(self):
        """Ack can only be written once."""
        agent = ComplianceSignaler("A0")
        auth = make_allow("K_LOG", "A0", "IP-0001")
        agent.set_authority_lookup(build_lookup(auth))

        # Force deadlock state and ack
        for e in range(5):
            agent.observe(make_observation(e, ["IP-0001"],
                                            own_last_outcome="JOINT_ADMISSIBILITY_FAILURE" if e > 0 else None))
            agent.propose_action()

        agent.observe(make_observation(5, ["IP-0001"],
                                        own_last_outcome="JOINT_ADMISSIBILITY_FAILURE"))
        action5 = agent.propose_action()
        assert action5.declared_scope == ["K_LOG"]

        # Epoch 6: should go back to contesting K_POLICY
        agent.observe(make_observation(6, ["IP-0001"],
                                        own_last_outcome="EXECUTED"))
        action6 = agent.propose_action()
        assert action6.declared_scope == ["K_POLICY"]


# ═══════════════════════════════════════════════════════════════
# §3: Citation Helper Tests
# ═══════════════════════════════════════════════════════════════

class TestCitationHelper:
    """Test the universal citation rule."""

    def test_cites_lexicographic_first(self):
        """Should cite the authority with smallest canonical serialization."""
        a1 = make_allow("K_POLICY", "A0", "IP-0002")
        a2 = make_allow("K_POLICY", "A0", "IP-0001")
        lookup = build_lookup(a1, a2)
        result = cite_for_key("K_POLICY", ["IP-0001", "IP-0002"], lookup)
        assert len(result) == 1
        # The one with smaller canonical serialization wins
        c1 = canonical_artifact_string(a1)
        c2 = canonical_artifact_string(a2)
        expected = "IP-0002" if c1 < c2 else "IP-0001"
        assert result[0] == expected

    def test_empty_if_no_matching_authority(self):
        a1 = make_allow("K_LOG", "A0", "IP-0001")
        lookup = build_lookup(a1)
        result = cite_for_key("K_POLICY", ["IP-0001"], lookup)
        assert result == []

    def test_empty_if_no_available_authorities(self):
        result = cite_for_key("K_POLICY", [], {})
        assert result == []


# ═══════════════════════════════════════════════════════════════
# §4: Injection Engine Tests
# ═══════════════════════════════════════════════════════════════

class TestInjectionEngine:
    """Test injection trigger evaluation and artifact creation."""

    def test_fixed_epoch_trigger(self):
        """FIXED_EPOCH triggers at exact epoch."""
        spec = InjectionSpec(
            condition_id="B",
            trigger_type=FIXED_EPOCH,
            inject_keys=["K_POLICY"],
            inject_agents=["A0"],
            fixed_epoch=6,
        )
        engine = InjectionEngine(spec, authority_id_counter=4)
        store = IPAuthorityStore()

        # Before trigger epoch
        assert engine.evaluate_step0(5, store) is None
        assert not engine.injected

        # At trigger epoch
        event = engine.evaluate_step0(6, store)
        assert event is not None
        assert event.trigger_value is True
        assert event.artifacts_count == 1
        assert engine.injected

        # After trigger — no more injection
        assert engine.evaluate_step0(7, store) is None

    def test_state_triggered_deadlock(self):
        """STATE_TRIGGERED fires on deadlock persist M=2."""
        spec = InjectionSpec(
            condition_id="A",
            trigger_type=STATE_TRIGGERED,
            inject_keys=["K_POLICY"],
            inject_agents=["A0", "A1", "A2", "A3"],
            state_predicate="STATE_DEADLOCK_INST_PERSIST_M2",
        )
        engine = InjectionEngine(spec, authority_id_counter=4)
        store = IPAuthorityStore()

        # Not enough deadlock persistence
        assert engine.evaluate_step0(2, store, state_deadlock_active=True,
                                      deadlock_persist_count=1) is None

        # Enough persistence
        event = engine.evaluate_step0(3, store, state_deadlock_active=True,
                                       deadlock_persist_count=2)
        assert event is not None
        assert event.trigger_value is True
        assert event.artifacts_count == 4  # 1 key × 4 agents

    def test_predicate_check_success(self):
        """PREDICATE_CHECK at E_check=6 with COMPLIANCE_ACK present."""
        spec = InjectionSpec(
            condition_id="C",
            trigger_type=PREDICATE_CHECK,
            inject_keys=["K_POLICY"],
            inject_agents=["A0", "A1", "A2", "A3"],
            predicate_check_epoch=6,
        )
        engine = InjectionEngine(spec, authority_id_counter=8)
        store = IPAuthorityStore()

        event = engine.evaluate_step0(
            6, store,
            world_state={"K_LOG": "COMPLIANCE_ACK", "K_POLICY": "P0",
                         "K_TREASURY": 100, "K_OPS_A": "free",
                         "K_OPS_B": "free", "K_REGISTRY": "test"},
        )
        assert event is not None
        assert event.trigger_value is True
        assert event.artifacts_count == 4

    def test_predicate_check_failure(self):
        """PREDICATE_CHECK at E_check=6 without COMPLIANCE_ACK."""
        spec = InjectionSpec(
            condition_id="C",
            trigger_type=PREDICATE_CHECK,
            inject_keys=["K_POLICY"],
            inject_agents=["A0", "A1", "A2", "A3"],
            predicate_check_epoch=6,
        )
        engine = InjectionEngine(spec, authority_id_counter=8)
        store = IPAuthorityStore()

        event = engine.evaluate_step0(
            6, store,
            world_state={"K_LOG": "", "K_POLICY": "P0",
                         "K_TREASURY": 100, "K_OPS_A": "free",
                         "K_OPS_B": "free", "K_REGISTRY": "test"},
        )
        assert event is not None
        assert event.trigger_value is False
        assert event.artifacts_count == 0

    def test_flood_injection_d(self):
        """Condition D: inject all 6 keys × 4 agents = 24 artifacts."""
        all_keys = ["K_POLICY", "K_TREASURY", "K_REGISTRY",
                     "K_OPS_A", "K_OPS_B", "K_LOG"]
        spec = InjectionSpec(
            condition_id="D",
            trigger_type=FIXED_EPOCH,
            inject_keys=all_keys,
            inject_agents=["A0", "A1", "A2", "A3"],
            fixed_epoch=6,
        )
        engine = InjectionEngine(spec, authority_id_counter=8)
        store = IPAuthorityStore()

        event = engine.evaluate_step0(6, store)
        assert event.artifacts_count == 24
        assert len(engine.injected_artifact_ids) == 24

    def test_artifact_id_format(self):
        """Injected artifacts use IP-NNNN format."""
        spec = InjectionSpec(
            condition_id="B",
            trigger_type=FIXED_EPOCH,
            inject_keys=["K_POLICY"],
            inject_agents=["A0"],
            fixed_epoch=6,
        )
        engine = InjectionEngine(spec, authority_id_counter=4)
        store = IPAuthorityStore()

        event = engine.evaluate_step0(6, store)
        assert event.artifacts[0]["authority_id"] == "IP-0005"

    def test_injection_event_schema(self):
        """InjectionEvent must match §5.4 schema."""
        spec = InjectionSpec(
            condition_id="B",
            trigger_type=FIXED_EPOCH,
            inject_keys=["K_POLICY"],
            inject_agents=["A0"],
            fixed_epoch=6,
        )
        engine = InjectionEngine(spec, authority_id_counter=4)
        store = IPAuthorityStore()

        event = engine.evaluate_step0(6, store)
        d = event.to_dict()
        assert d["event_type"] == "AUTHORITY_INJECTION"
        assert d["epoch_applied"] == 6
        assert d["condition_id"] == "B"
        assert d["trigger_type"] == "FIXED_EPOCH"
        assert d["trigger_spec_id"] == "FIXED_EPOCH_6"
        assert d["trigger_evidence"]["predicate"] == "FIXED_EPOCH_6"
        assert d["trigger_evidence"]["value"] is True
        assert isinstance(d["artifacts_digest"], str)
        assert len(d["artifacts_digest"]) == 64  # SHA-256 hex


# ═══════════════════════════════════════════════════════════════
# §5: Detector Tests
# ═══════════════════════════════════════════════════════════════

class TestInstitutionalDeadlockDetector:
    """Test deadlock detector with M=2 threshold."""

    def test_deadlock_at_m2(self):
        det = InstitutionalDeadlockDetector(threshold=2)
        # Epoch 0: submitted but none executed
        assert det.record_epoch(2, 0) is False  # counter=1
        # Epoch 1: same
        assert det.record_epoch(2, 0) is True   # counter=2, deadlock!

    def test_resets_on_success(self):
        det = InstitutionalDeadlockDetector(threshold=2)
        det.record_epoch(2, 0)  # counter=1
        det.record_epoch(1, 1)  # counter=0 (one executed)
        det.record_epoch(2, 0)  # counter=1
        assert det.is_active is False

    def test_no_deadlock_without_attempts(self):
        det = InstitutionalDeadlockDetector(threshold=2)
        det.record_epoch(0, 0)  # no attempts = no deadlock
        det.record_epoch(0, 0)
        assert det.is_active is False


class TestInstitutionalLivelockDetector:
    """Test livelock detector with L=5 threshold."""

    def test_livelock_at_l5(self):
        det = InstitutionalLivelockDetector(threshold=5)
        for e in range(4):
            assert det.record_epoch(e, inst_state_changed=False,
                                     inst_actions_submitted=2) is False
        # 5th consecutive epoch
        assert det.record_epoch(4, inst_state_changed=False,
                                 inst_actions_submitted=2) is True
        assert det.is_latched is True

    def test_resets_on_state_change(self):
        det = InstitutionalLivelockDetector(threshold=5)
        for e in range(3):
            det.record_epoch(e, inst_state_changed=False,
                              inst_actions_submitted=2)
        # State changed — resets
        det.record_epoch(3, inst_state_changed=True, inst_actions_submitted=2)
        assert det.counter == 0

    def test_permanent_latch(self):
        """Once latched, never clears."""
        det = InstitutionalLivelockDetector(threshold=5)
        for e in range(5):
            det.record_epoch(e, inst_state_changed=False,
                              inst_actions_submitted=2)
        assert det.is_latched is True
        # Record more epochs with state changes
        det.record_epoch(5, inst_state_changed=True, inst_actions_submitted=1)
        assert det.is_latched is True  # Still latched


class TestGovernanceCollapseDetector:
    """Test governance collapse detector with D=5 threshold."""

    def test_collapse_from_persistent_deadlock(self):
        det = GovernanceCollapseDetector(threshold=5)
        for e in range(4):
            assert det.record_epoch(e, deadlock_active=True,
                                     livelock_latched=False,
                                     active_agent_count=4) is False
        assert det.record_epoch(4, deadlock_active=True,
                                 livelock_latched=False,
                                 active_agent_count=4) is True
        assert det.is_latched is True

    def test_collapse_from_livelock(self):
        det = GovernanceCollapseDetector(threshold=5)
        assert det.record_epoch(0, deadlock_active=False,
                                 livelock_latched=True,
                                 active_agent_count=4) is True
        assert det.is_latched is True

    def test_no_collapse_without_agents(self):
        det = GovernanceCollapseDetector(threshold=5)
        assert det.record_epoch(0, deadlock_active=True,
                                 livelock_latched=True,
                                 active_agent_count=0) is False


class TestOrphaningDetector:
    """Test orphaning detector."""

    def test_detects_orphaned_key(self):
        det = OrphaningDetector()
        store = IPAuthorityStore()
        store.inject([make_allow("K_POLICY", "A0", "IP-0001")])

        # A0 exited, only active agents are A1, A2, A3
        orphaned = det.check_orphaning(5, ["A1", "A2", "A3"], store, K_INST)
        assert "K_POLICY" in orphaned
        assert det.orphaning_present is True

    def test_no_orphaning_with_active_holder(self):
        det = OrphaningDetector()
        store = IPAuthorityStore()
        store.inject([
            make_allow("K_POLICY", "A0", "IP-0001"),
            make_allow("K_POLICY", "A1", "IP-0002"),
        ])

        orphaned = det.check_orphaning(5, ["A1", "A2"], store, K_INST)
        assert "K_POLICY" not in orphaned


class TestAgentCollapseDetector:
    def test_collapse_when_empty(self):
        assert AgentCollapseDetector.is_collapse([]) is True

    def test_no_collapse_with_agents(self):
        assert AgentCollapseDetector.is_collapse(["A0"]) is False


# ═══════════════════════════════════════════════════════════════
# §6: Classifier Tests
# ═══════════════════════════════════════════════════════════════

class TestCaptureClassifier:
    """Test capture classifier."""

    def test_capture_detected(self):
        """Capture: dominance >= 0.70 AND injected_citation >= 0.60."""
        injected_ids = {"IP-0005"}
        classifier = CaptureClassifier(injected_ids)

        # Simulate 10 epochs: A0 executes 8 K_POLICY writes with injected authority
        logs = []
        for e in range(10):
            actions_detail = [
                {"agent_id": "A0", "action_id": f"A0:{e}:0", "action_type": "WRITE",
                 "declared_scope": ["K_POLICY"], "authorities_cited": ["IP-0005"],
                 "outcome": "EXECUTED"},
                {"agent_id": "A1", "action_id": f"A1:{e}:0", "action_type": "WRITE",
                 "declared_scope": ["K_OPS_A"], "authorities_cited": ["IP-0002"],
                 "outcome": "EXECUTED"},
            ]
            if e < 2:
                # A1 also executes K_POLICY in first 2 epochs
                actions_detail.append(
                    {"agent_id": "A1", "action_id": f"A1:{e}:0b", "action_type": "WRITE",
                     "declared_scope": ["K_POLICY"], "authorities_cited": ["IP-0002"],
                     "outcome": "EXECUTED"})
            logs.append({
                "outcomes": {"A0": "EXECUTED", "A1": "EXECUTED"},
                "actions_detail": actions_detail,
            })

        result = classifier.compute(logs)
        assert result["capture_detected"] is True
        assert result["capture_dominance"]["A0"] >= 0.70

    def test_no_capture_without_injection(self):
        """Dominance without injected citation is not capture."""
        injected_ids = {"IP-0099"}  # Not cited
        classifier = CaptureClassifier(injected_ids)
        logs = [{
            "outcomes": {"A0": "EXECUTED"},
            "actions_detail": [
                {"agent_id": "A0", "action_id": "A0:0:0", "action_type": "WRITE",
                 "declared_scope": ["K_POLICY"], "authorities_cited": ["IP-0001"],
                 "outcome": "EXECUTED"},
            ],
        }]
        result = classifier.compute(logs)
        assert result["capture_detected"] is False


class TestDependencyClassifier:
    """Test dependency classifier."""

    def test_computes_dependency_rate(self):
        injected_ids = {"IP-0005", "IP-0006"}
        classifier = DependencyClassifier(injected_ids)
        logs = [{
            "outcomes": {"A0": "EXECUTED", "A1": "EXECUTED"},
            "actions_detail": [
                {"agent_id": "A0", "action_id": "A0:0:0", "action_type": "WRITE",
                 "declared_scope": ["K_POLICY"], "authorities_cited": ["IP-0005"],
                 "outcome": "EXECUTED"},
                {"agent_id": "A1", "action_id": "A1:0:0", "action_type": "WRITE",
                 "declared_scope": ["K_OPS_A"], "authorities_cited": ["IP-0001"],
                 "outcome": "EXECUTED"},
            ],
        }]
        result = classifier.compute(logs)
        assert result["dependency_rate"] == 0.5  # 1 of 2 citing injected
        assert result["dependency_concentration"]["A0"] == 1.0


class TestZombieClassifier:
    """Test zombie classifier."""

    def test_zombie_write_count(self):
        injected_ids = {"IP-0005"}
        classifier = ZombieClassifier(injected_ids)
        post_collapse_logs = [{
            "outcomes": {"A0": "EXECUTED"},
            "actions_detail": [
                {"agent_id": "A0", "action_id": "A0:10:0", "action_type": "WRITE",
                 "declared_scope": ["K_POLICY"], "authorities_cited": ["IP-0005"],
                 "outcome": "EXECUTED"},
            ],
            "pass2_results": {},
        }]
        result = classifier.compute(
            post_collapse_logs,
            {"K_POLICY": "P0", "K_TREASURY": 100, "K_REGISTRY": "test"},
            {"K_POLICY": "POLICY_CONTEST", "K_TREASURY": 100, "K_REGISTRY": "test"},
        )
        assert result["zombie_write_count"] == 1
        assert result["zombie_citing_injected_rate"] == 1.0
        assert result["zombie_progress_delta"] == 1  # K_POLICY changed


# ═══════════════════════════════════════════════════════════════
# §7: Source-Blind Admissibility Integration Tests
# ═══════════════════════════════════════════════════════════════

class TestSourceBlindAdmissibility:
    """Test that IPAuthorityStore + evaluate_admissibility is source-blind."""

    def test_injected_authority_is_admissible(self):
        """Injected authority (created_epoch > 0) must be admissible."""
        store = IPAuthorityStore()
        store.inject([
            make_allow("K_POLICY", "A0", "IP-0001", epoch=0),
            make_allow("K_POLICY", "A1", "IP-0005", epoch=6),
        ])

        actions = {
            "A0": ActionRequest(
                agent_id="A0", action_id="A0:7:0", action_type="WRITE",
                declared_scope=["K_POLICY"],
                proposed_delta={"K_POLICY": "test_A0"},
                authorities_cited=["IP-0001"],
            ),
            "A1": ActionRequest(
                agent_id="A1", action_id="A1:7:0", action_type="WRITE",
                declared_scope=["K_POLICY"],
                proposed_delta={"K_POLICY": "test_A1"},
                authorities_cited=["IP-0005"],
            ),
        }

        outcomes, p1, p2 = evaluate_admissibility(actions, store)

        # Both should pass Pass-1 (source-blind)
        assert p1.get("A0:7:0") == "PASS"
        assert p1.get("A1:7:0") == "PASS"

        # Pass-2: both target K_POLICY → interference → both refused
        assert outcomes["A0"] == JOINT_ADMISSIBILITY_FAILURE
        assert outcomes["A1"] == JOINT_ADMISSIBILITY_FAILURE

    def test_sole_writer_executes(self):
        """Single writer should execute."""
        store = IPAuthorityStore()
        store.inject([make_allow("K_POLICY", "A0", "IP-0001", epoch=6)])

        actions = {
            "A0": ActionRequest(
                agent_id="A0", action_id="A0:7:0", action_type="WRITE",
                declared_scope=["K_POLICY"],
                proposed_delta={"K_POLICY": "captured"},
                authorities_cited=["IP-0001"],
            ),
            "A1": None,
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["A0"] == EXECUTED

    def test_no_authority_refused(self):
        """Action without authority should be refused at Pass-1."""
        store = IPAuthorityStore()

        actions = {
            "A0": ActionRequest(
                agent_id="A0", action_id="A0:0:0", action_type="WRITE",
                declared_scope=["K_POLICY"],
                proposed_delta={"K_POLICY": "test"},
                authorities_cited=[],
            ),
        }
        outcomes, p1, p2 = evaluate_admissibility(actions, store)
        assert outcomes["A0"] == JOINT_ADMISSIBILITY_FAILURE


# ═══════════════════════════════════════════════════════════════
# §8: Full Condition Integration Tests
# ═══════════════════════════════════════════════════════════════

class TestConditionA:
    """Condition A: Symmetric Relief — deadlock → injection → livelock."""

    def test_condition_a_runs_to_completion(self):
        result = run_condition("A")
        assert result["condition_result"] in ("PASS", "INVALID_RUN")
        assert result["experiment_id"] == "IX-4-IP"
        assert result["condition"] == "A"

    def test_condition_a_injection_occurs(self):
        result = run_condition("A")
        summary = result["injection_events_summary"]
        if result["condition_result"] == "PASS":
            assert summary["total_artifacts_injected"] == 4
            assert len(summary["injection_epochs"]) == 1


class TestConditionB:
    """Condition B: Asymmetric Empowerment — capture expected."""

    def test_condition_b_runs_to_completion(self):
        result = run_condition("B")
        assert result["condition_result"] == "PASS"
        assert result["condition"] == "B"

    def test_condition_b_capture_detected(self):
        result = run_condition("B")
        metrics = result["aggregate_metrics"]
        # A0 (CaptureSeeker) should have high dominance with injected authority
        assert metrics["capture_detected"] is True


class TestConditionC:
    """Condition C: Conditional Supply — compliance + injection."""

    def test_condition_c_runs_to_completion(self):
        result = run_condition("C")
        assert result["condition"] == "C"
        # Should pass if compliance predicate met
        assert result["condition_result"] in ("PASS", "INVALID_RUN")


class TestConditionD:
    """Condition D: Authority Flood — 24 artifact injection."""

    def test_condition_d_runs_to_completion(self):
        result = run_condition("D")
        assert result["condition_result"] == "PASS"
        assert result["condition"] == "D"

    def test_condition_d_flood_injection(self):
        result = run_condition("D")
        summary = result["injection_events_summary"]
        assert summary["total_artifacts_injected"] == 24


class TestConditionE:
    """Condition E: Post-Collapse Revival — zombie execution."""

    def test_condition_e_runs_to_completion(self):
        result = run_condition("E")
        assert result["condition_result"] in ("PASS", "INVALID_RUN")
        assert result["condition"] == "E"


# ═══════════════════════════════════════════════════════════════
# §9: Replay Determinism Tests
# ═══════════════════════════════════════════════════════════════

class TestReplayDeterminism:
    """Test that runs are bit-perfectly replayable."""

    @pytest.mark.parametrize("condition_id", ["A", "B", "C", "D", "E"])
    def test_deterministic_replay(self, condition_id):
        """Two runs of the same condition must produce identical outputs."""
        result1 = run_condition(condition_id)
        result2 = run_condition(condition_id)

        # Remove timestamps (allowed to vary)
        for r in (result1, result2):
            r.pop("timestamp", None)
            r.pop("notes", None)

        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)


# ═══════════════════════════════════════════════════════════════
# §10: K_INST Scoping Tests
# ═══════════════════════════════════════════════════════════════

class TestKInstScoping:
    """Test that K_INST = {K_POLICY, K_TREASURY, K_REGISTRY} excludes K_LOG."""

    def test_k_inst_excludes_k_log(self):
        assert "K_LOG" not in K_INST
        assert "K_POLICY" in K_INST
        assert "K_TREASURY" in K_INST
        assert "K_REGISTRY" in K_INST

    def test_k_inst_has_3_keys(self):
        assert len(K_INST) == 3

    def test_all_keys_has_6(self):
        assert len(ALL_KEYS) == 6
