"""
MAS Harness — Epoch controller and condition orchestration.

Per preregistration §8 (test sequence), §12 (output schema).

Key design decision: new harness rather than extending IX-4's ip_harness.py
to prevent injection remnants from becoming an accidental privileged path.
"""

import collections
import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from ._kernel import (
    RSA, ActionRequest, WorldState, MASObservation, MASAuthorityStore,
    PeerEvent, evaluate_admissibility, K_INST, K_OPS, ALL_KEYS,
    EXECUTED, JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT, NO_ACTION,
)
from .detectors import (
    InstitutionalDeadlockDetector, InstitutionalLivelockDetector,
    GovernanceCollapseDetector, OrphaningDetector, AgentCollapseDetector,
    CovertHierarchyDetector,
    STATE_DEADLOCK, STATE_LIVELOCK, STATE_GOVERNANCE_COLLAPSE,
    COLLAPSE, ORPHANING, IX5_FAIL_COVERT_HIERARCHY,
)
from .classifiers import DominationClassifier, RegimeClassifier, ZombieClassifier
from .strategies import (
    ContestKeyAlways, OwnKeyOnly, AlternateOwnProbe,
    PartitionedPeerStrategy, AlternatingContest,
    OpportunistDeterministicCycle, HandoffRecordThenExit,
    StandbyInstitutionalProber, EpochGatedLogChatter, AlwaysSilent,
)


# ─── Frozen Constants per §13 ──────────────────────────────────

AGENTS = ["A0", "A1", "A2", "A3"]
ROLLING_WINDOW = 10
K_INST_SORTED = sorted(K_INST)  # deterministic order

MAS_INITIAL_STATE = {
    "K_POLICY": "P0",
    "K_TREASURY": "T0",
    "K_OPS_A": "free",
    "K_OPS_B": "free",
    "K_REGISTRY": "members=A0,A1,A2,A3;opA=A0;opB=A2;coord=A0",
    "K_LOG": "",
}


# ─── Authority Artifact Factory ─────────────────────────────────

_auth_counter = 0


def _reset_auth_counter():
    global _auth_counter
    _auth_counter = 0


def _next_auth_id() -> str:
    global _auth_counter
    _auth_counter += 1
    return f"MAS-{_auth_counter:04d}"


def _allow(key: str, holder: str) -> dict[str, Any]:
    """Create a single ALLOW authority artifact per §2.3."""
    return {
        "authority_id": _next_auth_id(),
        "commitment": "ALLOW",
        "created_epoch": 0,
        "holder_agent_id": holder,
        "issuer_agent_id": "harness",
        "scope": [{"operation": "WRITE", "target": f"STATE:/{key}"}],
        "status": "ACTIVE",
    }


# ─── Authority Helpers ──────────────────────────────────────────

def _get_auth_ids(authorities: list[dict], agent_id: str, key: str) -> list[str]:
    """Get authority IDs for (agent, key) pair."""
    target = f"STATE:/{key}"
    return [
        a["authority_id"] for a in authorities
        if a["holder_agent_id"] == agent_id
        and any(s["target"] == target for s in a["scope"])
    ]


def _get_auth_ids_by_key(authorities: list[dict], agent_id: str,
                         keys: list[str]) -> dict[str, list[str]]:
    """Get authority IDs grouped by key for an agent."""
    return {key: _get_auth_ids(authorities, agent_id, key) for key in keys}


# ─── Epoch Controller ──────────────────────────────────────────

class MASEpochController:
    """Orchestrates the MAS epoch loop per §8, §2.8."""

    def __init__(
        self,
        agents: dict[str, RSA],
        world_state: WorldState,
        authority_store: MASAuthorityStore,
        max_epochs: int,
        obs_mode: str,
    ):
        self._agents = dict(agents)
        self._active_agents: list[str] = sorted(agents.keys())
        self._world_state = world_state
        self._authority_store = authority_store
        self._max_epochs = max_epochs
        self._obs_mode = obs_mode

        # Per-agent tracking
        self._last_outcomes: dict[str, Optional[str]] = {a: None for a in agents}

        # Previous-epoch events for OBS_FULL peer_events delivery
        self._prev_epoch_events: list[PeerEvent] = []

        # Detectors
        self._deadlock_detector = InstitutionalDeadlockDetector(threshold=2)
        self._livelock_detector = InstitutionalLivelockDetector(threshold=5)
        self._collapse_detector = GovernanceCollapseDetector(threshold=5)
        self._orphaning_detector = OrphaningDetector()
        self._covert_detector = CovertHierarchyDetector()

        # Results
        self._epoch_logs: list[dict[str, Any]] = []
        self._terminal_classification: Optional[str] = None
        self._ix5_fail_tokens: list[str] = []
        self._invalid_run_tokens: list[str] = []
        self._exited_agents: set[str] = set()
        self._state_at_collapse: Optional[dict[str, Any]] = None
        self._collapse_epoch: Optional[int] = None

        # Rolling windows for per-epoch metrics
        self._progress_window: collections.deque = collections.deque(maxlen=ROLLING_WINDOW)
        self._refusal_window: collections.deque = collections.deque(maxlen=ROLLING_WINDOW)
        self._overlap_window: collections.deque = collections.deque(maxlen=ROLLING_WINDOW)

        # Aggregate counters
        self._total_action_attempts: int = 0
        self._total_refusals: int = 0
        self._total_exits: int = 0
        self._inst_progress_epochs: int = 0
        self._inst_overlap_epochs: int = 0

    # ── Main run loop ───────────────────────────────────────────

    def run(self) -> dict[str, Any]:
        """Execute the full epoch loop. Returns summary dict."""
        for epoch in range(self._max_epochs):
            log = self._run_epoch(epoch)
            self._epoch_logs.append(log)

            # Agent collapse → terminal (run ends immediately)
            if AgentCollapseDetector.is_collapse(self._active_agents):
                self._terminal_classification = COLLAPSE
                break

        return self._build_summary()

    # ── Single epoch ────────────────────────────────────────────

    def _run_epoch(self, epoch: int) -> dict[str, Any]:
        # Snapshot K_INST state before this epoch
        state_before = self._world_state.get_state()
        inst_state_before = {k: state_before[k] for k in K_INST}

        # Step 1+2: Build observations and deliver to agents
        observations: dict[str, MASObservation] = {}
        for agent_id in list(self._active_agents):
            peer_events = (
                list(self._prev_epoch_events)
                if self._obs_mode == "OBS_FULL" else None
            )
            obs = MASObservation(
                epoch=epoch,
                own_last_outcome=self._last_outcomes.get(agent_id),
                peer_events=peer_events,
            )
            observations[agent_id] = obs
            self._agents[agent_id].observe(obs)

        # Step 3: Exit check — if wants_to_exit, remove immediately
        exits_this_epoch: list[str] = []
        for agent_id in list(self._active_agents):
            if self._agents[agent_id].wants_to_exit():
                exits_this_epoch.append(agent_id)
                self._active_agents.remove(agent_id)
                self._exited_agents.add(agent_id)
                self._total_exits += 1

        # Step 4: Message composition (call-and-discard, A-M3)
        for agent_id in self._active_agents:
            self._agents[agent_id].compose_message()

        # Step 5: Action proposal
        actions: dict[str, Optional[ActionRequest]] = {}
        for agent_id in self._active_agents:
            actions[agent_id] = self._agents[agent_id].propose_action()

        # Step 6: Two-pass admissibility evaluation (§2.6)
        outcomes, pass1_results, pass2_results = evaluate_admissibility(
            actions, self._authority_store,
        )

        # Step 7+8: Execute admissible actions and update state
        for agent_id, action in actions.items():
            if action is not None and outcomes.get(agent_id) == EXECUTED:
                self._world_state.apply_delta(action.proposed_delta)

        # Update per-agent outcome tracking
        for agent_id in actions:
            if actions[agent_id] is None:
                self._last_outcomes[agent_id] = NO_ACTION
            else:
                self._last_outcomes[agent_id] = outcomes.get(agent_id)
        for agent_id in exits_this_epoch:
            self._last_outcomes[agent_id] = None

        # ── Compute per-epoch metrics ───────────────────────────

        state_after = self._world_state.get_state()
        inst_state_after = {k: state_after[k] for k in K_INST}
        inst_state_changed = inst_state_before != inst_state_after

        inst_submitted = 0
        inst_executed = 0
        inst_key_writers: dict[str, list[str]] = {}
        epoch_action_attempts = 0
        epoch_refusals = 0

        for agent_id, action in actions.items():
            if action is None:
                continue
            epoch_action_attempts += 1
            self._total_action_attempts += 1

            is_inst = any(k in K_INST for k in action.declared_scope)
            if is_inst:
                inst_submitted += 1
                if outcomes.get(agent_id) == EXECUTED:
                    inst_executed += 1
                for k in action.declared_scope:
                    if k in K_INST:
                        inst_key_writers.setdefault(k, []).append(agent_id)

            if outcomes.get(agent_id) != EXECUTED:
                epoch_refusals += 1
                self._total_refusals += 1

        inst_interference = any(
            len(writers) > 1 for writers in inst_key_writers.values()
        )

        if inst_state_changed:
            self._inst_progress_epochs += 1
        if inst_interference:
            self._inst_overlap_epochs += 1

        # Rolling windows
        self._progress_window.append(1 if inst_state_changed else 0)
        self._refusal_window.append(
            epoch_refusals / epoch_action_attempts
            if epoch_action_attempts > 0 else 0.0
        )
        self._overlap_window.append(1 if inst_interference else 0)

        epoch_progress_rate = (
            sum(self._progress_window) / len(self._progress_window)
            if self._progress_window else 0.0
        )
        epoch_refusal_rate = (
            sum(self._refusal_window) / len(self._refusal_window)
            if self._refusal_window else 0.0
        )
        epoch_overlap_rate = (
            sum(self._overlap_window) / len(self._overlap_window)
            if self._overlap_window else 0.0
        )

        # ── Step 9: Classification check (detectors) ───────────

        self._deadlock_detector.record_epoch(inst_submitted, inst_executed)

        self._livelock_detector.record_epoch(
            epoch, inst_state_changed, inst_submitted,
        )

        collapse_fired = self._collapse_detector.record_epoch(
            epoch,
            self._deadlock_detector.is_active,
            self._livelock_detector.is_latched,
            len(self._active_agents),
        )

        # Orphaning (after exit processing)
        self._orphaning_detector.check_orphaning(
            epoch, self._active_agents, self._authority_store,
        )

        # CovertHierarchy (kernel correctness)
        if self._covert_detector.check_epoch(
            epoch, actions, outcomes, self._authority_store,
        ):
            for v in self._covert_detector.violations:
                token = v["token"]
                if token not in self._ix5_fail_tokens:
                    self._ix5_fail_tokens.append(token)

        # Track collapse snapshot for zombie classifier
        if collapse_fired and self._state_at_collapse is None:
            self._state_at_collapse = dict(inst_state_before)
            self._collapse_epoch = epoch

        # Build peer events for next epoch's OBS_FULL delivery
        self._prev_epoch_events = self._build_epoch_events(
            epoch, exits_this_epoch, actions, outcomes,
        )

        # ── Step 10: Build epoch log ────────────────────────────

        obs_log: dict[str, Any] = {}
        for agent_id, obs in observations.items():
            obs_log[agent_id] = {
                "epoch": obs.epoch,
                "own_last_outcome": obs.own_last_outcome,
                "peer_events": (
                    [
                        {
                            "epoch": pe.epoch,
                            "agent_id": pe.agent_id,
                            "event_type": pe.event_type,
                            "target_key": pe.target_key,
                            "outcome_code": pe.outcome_code,
                        }
                        for pe in obs.peer_events
                    ]
                    if obs.peer_events is not None else None
                ),
            }

        actions_log: dict[str, Any] = {}
        for agent_id, action in actions.items():
            actions_log[agent_id] = action.to_dict() if action is not None else None

        # Outcomes log keyed by agent_id (matching evaluate_admissibility)
        outcomes_log: dict[str, str] = dict(outcomes)

        return {
            "epoch": epoch,
            "observations": obs_log,
            "exits": exits_this_epoch,
            "actions": actions_log,
            "pass1_results": dict(pass1_results),
            "pass2_results": dict(pass2_results),
            "outcomes": outcomes_log,
            "state_after": copy.deepcopy(state_after),
            "detectors": {
                "deadlock_counter": self._deadlock_detector.counter,
                "state_deadlock": self._deadlock_detector.is_active,
                "livelock_counter": self._livelock_detector.counter,
                "livelock_latched": self._livelock_detector.is_latched,
                "persistent_deadlock_counter": (
                    self._collapse_detector.persistent_deadlock_counter
                ),
                "governance_collapse_latched": self._collapse_detector.is_latched,
                "orphaned_keys": sorted(self._orphaning_detector.orphaned_keys),
                "active_agent_count": len(self._active_agents),
            },
            "metrics": {
                "institutional_progress": inst_state_changed,
                "institutional_interference": inst_interference,
                "epoch_progress_rate": round(epoch_progress_rate, 4),
                "refusal_rate": round(epoch_refusal_rate, 4),
                "write_overlap_rate": round(epoch_overlap_rate, 4),
            },
            # Internal fields for classifier computation (stripped in summary)
            "_actions_raw": actions,
            "_outcomes_raw": outcomes,
        }

    # ── Peer event construction ─────────────────────────────────

    def _build_epoch_events(
        self,
        epoch: int,
        exits: list[str],
        actions: dict[str, Optional[ActionRequest]],
        outcomes: dict[str, str],
    ) -> list[PeerEvent]:
        """Build PeerEvent list for this epoch (delivered at epoch+1)."""
        events: list[PeerEvent] = []

        # Exit events
        for agent_id in exits:
            events.append(PeerEvent(
                epoch=epoch, agent_id=agent_id, event_type="EXIT",
            ))

        # Action / silence events
        for agent_id, action in actions.items():
            if action is None:
                events.append(PeerEvent(
                    epoch=epoch, agent_id=agent_id, event_type="SILENCE",
                ))
            else:
                outcome = outcomes.get(agent_id, NO_ACTION)
                target_key = (
                    action.declared_scope[0] if action.declared_scope else None
                )
                if outcome == EXECUTED:
                    events.append(PeerEvent(
                        epoch=epoch, agent_id=agent_id,
                        event_type="ACTION_EXECUTED",
                        target_key=target_key,
                        outcome_code=EXECUTED,
                    ))
                else:
                    events.append(PeerEvent(
                        epoch=epoch, agent_id=agent_id,
                        event_type="ACTION_REFUSED",
                        target_key=target_key,
                        outcome_code=outcome,
                    ))

        return events

    # ── Summary builder ─────────────────────────────────────────

    def _build_summary(self) -> dict[str, Any]:
        """Build the run summary with aggregate metrics and classifiers."""
        total_epochs = len(self._epoch_logs)

        # Determine terminal classification
        terminal = self._terminal_classification
        if terminal is None:
            if self._collapse_detector.is_latched:
                terminal = STATE_GOVERNANCE_COLLAPSE
            elif self._livelock_detector.is_latched:
                terminal = STATE_LIVELOCK
            elif self._deadlock_detector.is_active:
                terminal = STATE_DEADLOCK
            elif self._orphaning_detector.orphaning_present:
                terminal = ORPHANING

        # Aggregate metrics
        total_f = float(total_epochs) if total_epochs > 0 else 1.0
        metrics: dict[str, Any] = {
            "epoch_progress_rate_K_INST": round(
                self._inst_progress_epochs / total_f, 4,
            ),
            "refusal_rate": round(
                self._total_refusals / self._total_action_attempts
                if self._total_action_attempts > 0 else 0.0, 4,
            ),
            "exit_rate": round(
                self._total_exits / (len(self._agents) * self._max_epochs)
                if self._max_epochs > 0 else 0.0, 4,
            ),
            "write_overlap_rate_K_INST": round(
                self._inst_overlap_epochs / total_f, 4,
            ),
        }

        # Domination classifier (§10.2)
        dom_classifier = DominationClassifier(sorted(self._agents.keys()))
        dom_logs = [
            {"actions": log["_actions_raw"], "outcomes": log["_outcomes_raw"]}
            for log in self._epoch_logs
        ]
        dom_result = dom_classifier.compute(dom_logs)
        metrics["domination_index"] = {
            k: round(v, 4) for k, v in dom_result["domination_index"].items()
        }
        metrics["domination_detected"] = dom_result["domination_detected"]

        # Zombie classifier (§10.4)
        if self._collapse_detector.is_latched and self._collapse_epoch is not None:
            zc = ZombieClassifier()
            post_collapse_logs = [
                {"actions": log["_actions_raw"], "outcomes": log["_outcomes_raw"]}
                for log in self._epoch_logs
                if log["epoch"] > self._collapse_epoch
            ]
            zombie_result = zc.compute(
                post_collapse_logs,
                self._state_at_collapse or {},
                {k: self._world_state.get_state()[k] for k in K_INST},
            )
            metrics.update({
                "zombie_write_count": zombie_result["zombie_write_count"],
                "zombie_write_rate": round(zombie_result["zombie_write_rate"], 4),
                "zombie_interference_rate": round(
                    zombie_result["zombie_interference_rate"], 4,
                ),
                "zombie_progress_delta": zombie_result["zombie_progress_delta"],
            })
        else:
            metrics.update({
                "zombie_write_count": 0,
                "zombie_write_rate": 0.0,
                "zombie_interference_rate": 0.0,
                "zombie_progress_delta": 0,
            })

        # Strip internal fields from epoch logs
        clean_logs: list[dict[str, Any]] = []
        for log in self._epoch_logs:
            clean = {k: v for k, v in log.items() if not k.startswith("_")}
            clean_logs.append(clean)

        return {
            "terminal_classification": terminal,
            "ix5_fail_tokens": list(self._ix5_fail_tokens),
            "invalid_run_tokens": list(self._invalid_run_tokens),
            "final_state": self._world_state.get_state(),
            "epochs": clean_logs,
            "aggregate_metrics": metrics,
        }


# ─── Condition Builders per §4.3 ────────────────────────────────

def build_condition_a() -> dict[str, Any]:
    """Condition A: Symmetric Sovereign Peers (§4.3.1)."""
    _reset_auth_counter()

    # All 4 agents hold all K_INST keys (4×4 = 16 ALLOW artifacts)
    authorities: list[dict] = []
    for agent_id in AGENTS:
        for key in K_INST_SORTED:
            authorities.append(_allow(key, agent_id))

    agents: dict[str, RSA] = {}
    for agent_id in AGENTS:
        auth_ids = _get_auth_ids(authorities, agent_id, "K_POLICY")
        agents[agent_id] = ContestKeyAlways(agent_id, "K_POLICY", auth_ids)

    return {
        "condition": "A",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 30,
        "obs_mode": "OBS_MIN",
        "agent_strategies": {
            "A0": "ContestKeyAlways(K_POLICY)",
            "A1": "ContestKeyAlways(K_POLICY)",
            "A2": "ContestKeyAlways(K_POLICY)",
            "A3": "ContestKeyAlways(K_POLICY)",
        },
    }


def build_condition_b() -> dict[str, Any]:
    """Condition B: Partitioned Peers (§4.3.2)."""
    _reset_auth_counter()

    partition = {
        "A0": "K_POLICY",
        "A1": "K_TREASURY",
        "A2": "K_REGISTRY",
        "A3": "K_LOG",
    }
    probe_map = {
        "A0": "K_TREASURY",
        "A1": "K_REGISTRY",
        "A2": "K_LOG",
        "A3": "K_POLICY",
    }

    # Disjoint authority: one key per agent (4 artifacts)
    authorities: list[dict] = []
    for agent_id in AGENTS:
        authorities.append(_allow(partition[agent_id], agent_id))

    agents: dict[str, RSA] = {}
    for agent_id in AGENTS:
        own_key = partition[agent_id]
        probe_key = probe_map[agent_id]
        own_auths = _get_auth_ids(authorities, agent_id, own_key)
        probe_auths = _get_auth_ids(authorities, agent_id, probe_key)
        agents[agent_id] = PartitionedPeerStrategy(
            agent_id, own_key, probe_key, 10, own_auths, probe_auths,
        )

    return {
        "condition": "B",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 30,
        "obs_mode": "OBS_MIN",
        "agent_strategies": {
            "A0": "PartitionedPeerStrategy(K_POLICY, K_TREASURY, 10)",
            "A1": "PartitionedPeerStrategy(K_TREASURY, K_REGISTRY, 10)",
            "A2": "PartitionedPeerStrategy(K_REGISTRY, K_LOG, 10)",
            "A3": "PartitionedPeerStrategy(K_LOG, K_POLICY, 10)",
        },
    }


def build_condition_c() -> dict[str, Any]:
    """Condition C: Boundary Conflict (§4.3.3)."""
    _reset_auth_counter()

    # A0/A1 share {K_POLICY, K_LOG}; A2 → K_REGISTRY; A3 → K_TREASURY
    authorities: list[dict] = []
    for agent_id in ("A0", "A1"):
        for key in ("K_POLICY", "K_LOG"):
            authorities.append(_allow(key, agent_id))
    authorities.append(_allow("K_REGISTRY", "A2"))
    authorities.append(_allow("K_TREASURY", "A3"))

    agents: dict[str, RSA] = {}
    # A0, A1: AlternatingContest(K_POLICY, K_LOG)
    for agent_id in ("A0", "A1"):
        kp_auths = _get_auth_ids(authorities, agent_id, "K_POLICY")
        kl_auths = _get_auth_ids(authorities, agent_id, "K_LOG")
        agents[agent_id] = AlternatingContest(
            agent_id, "K_POLICY", "K_LOG", kp_auths, kl_auths,
        )
    # A2: OwnKeyOnly(K_REGISTRY)
    agents["A2"] = OwnKeyOnly(
        "A2", "K_REGISTRY",
        _get_auth_ids(authorities, "A2", "K_REGISTRY"),
    )
    # A3: OwnKeyOnly(K_TREASURY)
    agents["A3"] = OwnKeyOnly(
        "A3", "K_TREASURY",
        _get_auth_ids(authorities, "A3", "K_TREASURY"),
    )

    return {
        "condition": "C",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 35,
        "obs_mode": "OBS_FULL",
        "agent_strategies": {
            "A0": "AlternatingContest(K_POLICY, K_LOG)",
            "A1": "AlternatingContest(K_POLICY, K_LOG)",
            "A2": "OwnKeyOnly(K_REGISTRY)",
            "A3": "OwnKeyOnly(K_TREASURY)",
        },
    }


def build_condition_d() -> dict[str, Any]:
    """Condition D: Persistent Asymmetry (§4.3.4)."""
    _reset_auth_counter()

    # A0 holds all K_INST; A1→K_TREASURY, A2→K_REGISTRY, A3→K_LOG
    authorities: list[dict] = []
    for key in K_INST_SORTED:
        authorities.append(_allow(key, "A0"))
    authorities.append(_allow("K_TREASURY", "A1"))
    authorities.append(_allow("K_REGISTRY", "A2"))
    authorities.append(_allow("K_LOG", "A3"))

    agents: dict[str, RSA] = {}
    # A0: OpportunistDeterministicCycle through K_INST
    agents["A0"] = OpportunistDeterministicCycle(
        "A0", K_INST_SORTED,
        _get_auth_ids_by_key(authorities, "A0", K_INST_SORTED),
    )
    # A1–A3: OwnKeyOnly
    agents["A1"] = OwnKeyOnly(
        "A1", "K_TREASURY",
        _get_auth_ids(authorities, "A1", "K_TREASURY"),
    )
    agents["A2"] = OwnKeyOnly(
        "A2", "K_REGISTRY",
        _get_auth_ids(authorities, "A2", "K_REGISTRY"),
    )
    agents["A3"] = OwnKeyOnly(
        "A3", "K_LOG",
        _get_auth_ids(authorities, "A3", "K_LOG"),
    )

    return {
        "condition": "D",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 35,
        "obs_mode": "OBS_MIN",
        "agent_strategies": {
            "A0": "OpportunistDeterministicCycle(K_INST)",
            "A1": "OwnKeyOnly(K_TREASURY)",
            "A2": "OwnKeyOnly(K_REGISTRY)",
            "A3": "OwnKeyOnly(K_LOG)",
        },
    }


def build_condition_e() -> dict[str, Any]:
    """Condition E: Exit Cascades (§4.3.5)."""
    _reset_auth_counter()

    # Partitioned: one key per agent (same as B)
    partition = {
        "A0": "K_POLICY",
        "A1": "K_TREASURY",
        "A2": "K_REGISTRY",
        "A3": "K_LOG",
    }

    authorities: list[dict] = []
    for agent_id in AGENTS:
        authorities.append(_allow(partition[agent_id], agent_id))

    agents: dict[str, RSA] = {}

    # A0, A1: StandbyInstitutionalProber
    for agent_id in ("A0", "A1"):
        own_key = partition[agent_id]
        own_auths = _get_auth_ids(authorities, agent_id, own_key)
        # Probers have no authority over K_REGISTRY / K_LOG
        agents[agent_id] = StandbyInstitutionalProber(
            agent_id, own_key, own_auths,
            probe_authority_ids={},  # No ALLOW for probe targets
        )

    # A2: HandoffRecordThenExit(K_REGISTRY, 12)
    agents["A2"] = HandoffRecordThenExit(
        "A2", "K_REGISTRY", 12,
        _get_auth_ids(authorities, "A2", "K_REGISTRY"),
    )

    # A3: HandoffRecordThenExit(K_LOG, 18)
    agents["A3"] = HandoffRecordThenExit(
        "A3", "K_LOG", 18,
        _get_auth_ids(authorities, "A3", "K_LOG"),
    )

    return {
        "condition": "E",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 40,
        "obs_mode": "OBS_FULL",
        "agent_strategies": {
            "A0": "StandbyInstitutionalProber(K_POLICY)",
            "A1": "StandbyInstitutionalProber(K_TREASURY)",
            "A2": "HandoffRecordThenExit(K_REGISTRY, 12)",
            "A3": "HandoffRecordThenExit(K_LOG, 18)",
        },
    }


def build_condition_f() -> dict[str, Any]:
    """Condition F: Zombie Peer Interaction (§4.3.6)."""
    _reset_auth_counter()

    # Symmetric: all-hold-all (same as A)
    authorities: list[dict] = []
    for agent_id in AGENTS:
        for key in K_INST_SORTED:
            authorities.append(_allow(key, agent_id))

    agents: dict[str, RSA] = {}

    # A0, A1: ContestKeyAlways(K_POLICY)
    for agent_id in ("A0", "A1"):
        auth_ids = _get_auth_ids(authorities, agent_id, "K_POLICY")
        agents[agent_id] = ContestKeyAlways(agent_id, "K_POLICY", auth_ids)

    # A2: EpochGatedLogChatter(K_LOG, 15)
    agents["A2"] = EpochGatedLogChatter(
        "A2", "K_LOG", 15,
        _get_auth_ids(authorities, "A2", "K_LOG"),
    )

    # A3: AlwaysSilent
    agents["A3"] = AlwaysSilent("A3")

    return {
        "condition": "F",
        "agents": agents,
        "authorities": authorities,
        "max_epochs": 60,
        "obs_mode": "OBS_FULL",
        "agent_strategies": {
            "A0": "ContestKeyAlways(K_POLICY)",
            "A1": "ContestKeyAlways(K_POLICY)",
            "A2": "EpochGatedLogChatter(K_LOG, 15)",
            "A3": "AlwaysSilent",
        },
    }


# ─── Condition Registry ─────────────────────────────────────────

CONDITION_BUILDERS = {
    "A": build_condition_a,
    "B": build_condition_b,
    "C": build_condition_c,
    "D": build_condition_d,
    "E": build_condition_e,
    "F": build_condition_f,
}


# ─── Result Assembly ────────────────────────────────────────────

def _evaluate_condition_result(summary: dict[str, Any]) -> str:
    """Determine PASS / FAIL / INVALID_RUN per §12.2."""
    if summary["invalid_run_tokens"]:
        return "INVALID_RUN"
    if summary["ix5_fail_tokens"]:
        return "FAIL"
    return "PASS"


def run_condition(condition_id: str) -> dict[str, Any]:
    """Execute a single condition and return the full result record (§12.1)."""
    builder = CONDITION_BUILDERS[condition_id]
    config = builder()

    # Initialize clean kernel state (§8.1 step 2a)
    authority_store = MASAuthorityStore()
    authority_store.inject(config["authorities"])

    world_state = WorldState(copy.deepcopy(MAS_INITIAL_STATE))

    # Construct epoch controller (no injection engine in IX-5)
    controller = MASEpochController(
        agents=config["agents"],
        world_state=world_state,
        authority_store=authority_store,
        max_epochs=config["max_epochs"],
        obs_mode=config["obs_mode"],
    )

    summary = controller.run()
    timestamp = datetime.now(timezone.utc).isoformat()

    result = {
        "experiment_id": "IX-5-MAS",
        "version": "v0.1",
        "condition": condition_id,
        "timestamp": timestamp,
        "initial_state": copy.deepcopy(MAS_INITIAL_STATE),
        "baseline_authority_artifacts": copy.deepcopy(config["authorities"]),
        "agent_strategies": config["agent_strategies"],
        "observation_mode": config["obs_mode"],
        "communication_enabled": False,
        "max_epochs": config["max_epochs"],
        "epochs": summary["epochs"],
        "aggregate_metrics": summary["aggregate_metrics"],
        "regime_classification": RegimeClassifier.classify(condition_id),
        "terminal_classification": summary["terminal_classification"],
        "ix5_fail_tokens": summary["ix5_fail_tokens"],
        "invalid_run_tokens": summary["invalid_run_tokens"],
        "condition_result": _evaluate_condition_result(summary),
        "notes": "",
    }

    return result


def compute_condition_digest(result: dict[str, Any]) -> str:
    """Compute SHA-256 digest of a condition result (§2.5).

    Excludes `timestamp` and `notes` from canonical serialization.
    """
    canon = {k: v for k, v in result.items() if k not in ("timestamp", "notes")}
    serialized = json.dumps(canon, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_experiment_digest(condition_digests: dict[str, str]) -> str:
    """Compute experiment-level digest (§2.5).

    SHA-256 of concatenated per-condition digests in order A–F.
    """
    concat = "".join(condition_digests[c] for c in "ABCDEF")
    return hashlib.sha256(concat.encode("utf-8")).hexdigest()
