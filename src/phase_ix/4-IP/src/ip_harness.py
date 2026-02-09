"""
IP Test Harness — Per preregistration §8, §4, §12.

Orchestrates all 5 conditions (A–E) with exact authority layouts,
agent strategy bindings, injection regimes, and per-condition metrics.
"""

import copy
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ─── IX-2 kernel imports via _kernel bridge ─────────────────────

from ._kernel import (
    RSA, ActionRequest, Message, IPObservation,
    WorldState, IPAuthorityStore,
    evaluate_admissibility,
    EXECUTED, JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT, NO_ACTION,
)

# ─── IP-specific imports ───────────────────────────────────────

from .detectors import (
    K_INST, K_OPS, K_LOG_SET, ALL_KEYS,
    STATE_DEADLOCK, STATE_LIVELOCK, STATE_GOVERNANCE_COLLAPSE,
    COLLAPSE, ORPHANING,
    InstitutionalDeadlockDetector,
    InstitutionalLivelockDetector,
    GovernanceCollapseDetector,
    OrphaningDetector,
    AgentCollapseDetector,
)

from .classifiers import CaptureClassifier, DependencyClassifier, ZombieClassifier

from .injection_engine import (
    InjectionEngine, InjectionSpec, InjectionEvent,
    STATE_TRIGGERED, FIXED_EPOCH, PREDICATE_CHECK,
)

from .strategies import (
    ContestPolicyAlways,
    RefusalHardliner,
    Opportunist,
    CaptureSeeker,
    ComplianceSignaler,
)


# ─── Constants per §8.2, §13 ───────────────────────────────────

FIXED_CLOCK = 1750000000  # 2025-06-15 14:26:40 UTC
SEQUENCE_SEED = 1

IP_INITIAL_STATE = {
    "K_POLICY": "P0",
    "K_TREASURY": 100,
    "K_OPS_A": "free",
    "K_OPS_B": "free",
    "K_REGISTRY": "members=A0,A1,A2,A3;opA=A0;opB=A2;coord=A0",
    "K_LOG": "",
}

AGENTS = ["A0", "A1", "A2", "A3"]


# ─── Authority artifact factory ────────────────────────────────

_auth_counter = 0


def _reset_auth_counter():
    global _auth_counter
    _auth_counter = 0


def _next_auth_id() -> str:
    global _auth_counter
    _auth_counter += 1
    return f"IP-{_auth_counter:04d}"


def _allow(key: str, holder: str, counter_fn=None) -> dict:
    """Create ALLOW authority artifact (baseline, created_epoch=0)."""
    aid = counter_fn() if counter_fn else _next_auth_id()
    return {
        "authority_id": aid,
        "commitment": "ALLOW",
        "created_epoch": 0,
        "holder_agent_id": holder,
        "issuer_agent_id": "harness",
        "scope": [{"operation": "WRITE", "target": f"STATE:/{key}"}],
        "status": "ACTIVE",
    }


# ─── Epoch Log ──────────────────────────────────────────────────

class IPEpochLog:
    """Log for a single epoch."""

    def __init__(self, epoch: int):
        self.epoch = epoch
        self.injection_events: List[Dict[str, Any]] = []
        self.observations: Dict[str, Any] = {}
        self.exits: List[str] = []
        self.actions: List[Optional[Dict[str, Any]]] = []
        self.actions_detail: List[Optional[Dict[str, Any]]] = []
        self.pass1_results: Dict[str, str] = {}
        self.pass2_results: Dict[str, str] = {}
        self.outcomes: Dict[str, str] = {}
        self.state_after: Dict[str, Any] = {}
        self.detectors: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "injection_events": self.injection_events,
            "observations": self.observations,
            "exits": self.exits,
            "actions": self.actions,
            "actions_detail": self.actions_detail,
            "pass1_results": self.pass1_results,
            "pass2_results": self.pass2_results,
            "outcomes": self.outcomes,
            "state_after": self.state_after,
            "detectors": self.detectors,
            "metrics": self.metrics,
        }


# ─── IP Epoch Controller ───────────────────────────────────────

class IPEpochController:
    """IX-4 epoch controller with injection and political classifiers.

    Extends the epoch loop with:
    - Step 0: Injection (§2.8)
    - available_authorities in observations (§2.1)
    - Source-blind admissibility via IPAuthorityStore
    - K_INST = 3 keys (§2.4)
    - Deadlock M=2, Livelock L=5, Governance Collapse D=5
    - Capture, Dependency, Zombie classifiers
    """

    def __init__(
        self,
        agents: dict[str, RSA],
        world_state: WorldState,
        authority_store: IPAuthorityStore,
        max_epochs: int,
        injection_engine: InjectionEngine,
        e_pre_max: Optional[int] = None,
    ):
        self._agents = dict(agents)
        self._active_agents: list[str] = sorted(agents.keys())
        self._world_state = world_state
        self._authority_store = authority_store
        self._max_epochs = max_epochs
        self._injection_engine = injection_engine
        self._e_pre_max = e_pre_max

        # Per-agent tracking
        self._last_outcomes: dict[str, Optional[str]] = {a: None for a in agents}
        self._last_action_ids: dict[str, Optional[str]] = {a: None for a in agents}
        self._last_declared_scopes: dict[str, Optional[list[str]]] = {a: None for a in agents}

        # Detectors
        self._deadlock_detector = InstitutionalDeadlockDetector(threshold=2)
        self._livelock_detector = InstitutionalLivelockDetector(threshold=5)
        self._collapse_detector = GovernanceCollapseDetector(threshold=5)
        self._orphaning_detector = OrphaningDetector()

        # Results
        self._epoch_logs: list[IPEpochLog] = []
        self._terminal_classification: Optional[str] = None
        self._ix4_fail_tokens: list[str] = []
        self._invalid_run_tokens: list[str] = []
        self._exited_agents: set[str] = set()
        self._state_at_collapse: Optional[dict[str, Any]] = None

        # Aggregate counters
        self._total_action_attempts: int = 0
        self._total_refusals: int = 0
        self._total_exits: int = 0
        self._inst_progress_epochs: int = 0
        self._inst_overlap_epochs: int = 0
        self._inst_attempt_epochs: int = 0

    @property
    def epoch_logs(self) -> list[IPEpochLog]:
        return self._epoch_logs

    @property
    def terminal_classification(self) -> Optional[str]:
        return self._terminal_classification

    @property
    def ix4_fail_tokens(self) -> list[str]:
        return list(self._ix4_fail_tokens)

    @property
    def invalid_run_tokens(self) -> list[str]:
        return list(self._invalid_run_tokens)

    @property
    def final_state(self) -> dict[str, Any]:
        return self._world_state.get_state()

    @property
    def active_agents(self) -> list[str]:
        return list(self._active_agents)

    def run(self) -> dict[str, Any]:
        """Execute the full epoch loop. Returns summary dict.

        Per §11.2: run continues to max_epochs or COLLAPSE.
        STATE_DEADLOCK, STATE_LIVELOCK, STATE_GOVERNANCE_COLLAPSE are
        diagnostic classifications that do NOT terminate execution.
        Only COLLAPSE (all agents exited) and E_pre_max timeout terminate early.
        """
        for epoch in range(self._max_epochs):
            # Check E_pre_max timeout for state-triggered conditions
            if (self._e_pre_max is not None
                    and not self._injection_engine.injected
                    and epoch >= self._e_pre_max):
                self._invalid_run_tokens.append(
                    "INVALID_RUN / BASELINE_NOT_REACHED"
                )
                break

            log = self._run_epoch(epoch)
            self._epoch_logs.append(log)

            # Check terminal: agent collapse (all agents exited)
            if AgentCollapseDetector.is_collapse(self._active_agents):
                self._terminal_classification = COLLAPSE
                break

            # All other terminal classifications (STATE_DEADLOCK,
            # STATE_LIVELOCK, STATE_GOVERNANCE_COLLAPSE, ORPHANING)
            # are logged but do NOT terminate execution per §11.2.

        # Post-run validation
        self._validate_run()

        return self._build_summary()

    def _validate_run(self):
        """Post-run validation checks per §11."""
        # Check CONDITION_COUPLING_INSUFFICIENT:
        # "Injection occurred but no post-injection action cited injected authority"
        # Per §11.3: any action that cited injected authority counts, not just
        # executed actions. Citation = coupling into behavior.
        if self._injection_engine.injected:
            injection_epoch = self._injection_engine.injection_epoch
            if injection_epoch is not None:
                injected_ids = self._injection_engine.injected_artifact_ids
                any_cited = False
                for log in self._epoch_logs:
                    if log.epoch <= injection_epoch:
                        continue
                    for action_info in log.actions_detail:
                        if action_info is None:
                            continue
                        cited = action_info.get("authorities_cited", [])
                        if any(aid in injected_ids for aid in cited):
                            any_cited = True
                            break
                    if any_cited:
                        break
                if not any_cited:
                    self._invalid_run_tokens.append(
                        "INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT"
                    )

    def _build_authority_lookup(self) -> dict[str, dict[str, Any]]:
        """Build authority_id → artifact dict lookup."""
        lookup = {}
        for auth in self._authority_store.get_all():
            lookup[auth["authority_id"]] = auth
        return lookup

    def _run_epoch(self, epoch: int) -> IPEpochLog:
        """Execute a single epoch per §2.8."""
        log = IPEpochLog(epoch=epoch)
        state_before = self._world_state.snapshot()
        inst_state_before = {k: state_before[k] for k in K_INST if k in state_before}

        # Step 0: Injection
        inj_event = self._injection_engine.evaluate_step0(
            epoch=epoch,
            authority_store=self._authority_store,
            state_deadlock_active=self._deadlock_detector.is_active,
            deadlock_persist_count=self._deadlock_detector.counter,
            governance_collapse_latched=self._collapse_detector.is_latched,
            world_state=state_before,
        )
        if inj_event is not None:
            log.injection_events.append(inj_event.to_dict())
            # Check for Condition C predicate failure
            if (inj_event.trigger_type == PREDICATE_CHECK
                    and not inj_event.trigger_value):
                self._invalid_run_tokens.append(
                    "INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED"
                )

        # Build authority lookup for strategies
        authority_lookup = self._build_authority_lookup()

        # Step 1+2: Build observations and deliver to agents
        for agent_id in list(self._active_agents):
            # Get available_authorities for this agent
            available = self._authority_store.get_allow_ids_for_agent(agent_id)

            obs = IPObservation(
                epoch=epoch,
                world_state=self._world_state.get_state(),
                own_last_outcome=self._last_outcomes.get(agent_id),
                own_last_action_id=self._last_action_ids.get(agent_id),
                own_last_declared_scope=self._last_declared_scopes.get(agent_id),
                messages=[],  # Communication disabled for all IX-4 conditions
                available_authorities=available,
            )
            # Set authority lookup on strategy
            agent = self._agents[agent_id]
            if hasattr(agent, 'set_authority_lookup'):
                agent.set_authority_lookup(authority_lookup)
            agent.observe(obs)
            log.observations[agent_id] = {
                "epoch": obs.epoch,
                "own_last_outcome": obs.own_last_outcome,
                "available_authorities": available,
            }

        # Step 3: Exit check
        exiting = []
        for agent_id in list(self._active_agents):
            if self._agents[agent_id].wants_to_exit():
                exiting.append(agent_id)
        for agent_id in exiting:
            self._active_agents.remove(agent_id)
            self._exited_agents.add(agent_id)
            self._total_exits += 1
        log.exits = exiting

        # Collapse after exits
        if not self._active_agents:
            self._terminal_classification = COLLAPSE
            log.state_after = self._world_state.get_state()
            log.detectors = self._snapshot_detectors(epoch)
            return log

        # Step 5: Action proposals (Step 4 skipped — communication disabled)
        actions: dict[str, Optional[ActionRequest]] = {}
        for agent_id in self._active_agents:
            actions[agent_id] = self._agents[agent_id].propose_action()

        log.actions = [
            action.to_dict() if action is not None else None
            for action in actions.values()
        ]

        # Step 6: Adjudication (source-blind via IPAuthorityStore)
        outcomes, pass1_results, pass2_results = evaluate_admissibility(
            actions, self._authority_store
        )
        log.pass1_results = pass1_results
        log.pass2_results = pass2_results
        log.outcomes = outcomes

        # Build detailed action info for classifiers
        log.actions_detail = []
        for agent_id in self._active_agents:
            action = actions.get(agent_id)
            if action is None:
                log.actions_detail.append(None)
            else:
                log.actions_detail.append({
                    "agent_id": action.agent_id,
                    "action_id": action.action_id,
                    "action_type": action.action_type,
                    "declared_scope": action.declared_scope,
                    "proposed_delta": action.proposed_delta,
                    "authorities_cited": action.authorities_cited,
                    "outcome": outcomes.get(agent_id, ""),
                })

        # Step 7+8: Execute and update state
        for agent_id, outcome in outcomes.items():
            action = actions.get(agent_id)
            if outcome == EXECUTED and action is not None:
                self._world_state.apply_delta(action.proposed_delta)

        # Update per-agent tracking
        for agent_id in self._active_agents:
            action = actions.get(agent_id)
            self._last_outcomes[agent_id] = outcomes.get(agent_id)
            if action is not None:
                self._last_action_ids[agent_id] = action.action_id
                self._last_declared_scopes[agent_id] = action.declared_scope
            else:
                self._last_action_ids[agent_id] = None
                self._last_declared_scopes[agent_id] = None

        log.state_after = self._world_state.get_state()

        # ─── Metrics computation ────────────────────────────────

        state_after = self._world_state.get_state()
        inst_state_after = {k: state_after[k] for k in K_INST if k in state_after}
        inst_state_changed = inst_state_before != inst_state_after

        if inst_state_changed:
            self._inst_progress_epochs += 1

        # Count institutional actions
        inst_actions_submitted = 0
        inst_actions_executed = 0

        for agent_id in self._active_agents:
            action = actions.get(agent_id)
            if action is None:
                continue
            touches_inst = any(k in K_INST for k in action.declared_scope)

            if action is not None:
                self._total_action_attempts += 1
                outcome = outcomes.get(agent_id)
                if outcome in (JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT):
                    self._total_refusals += 1

            if touches_inst:
                inst_actions_submitted += 1
                if outcomes.get(agent_id) == EXECUTED:
                    inst_actions_executed += 1

        # Check for institutional write overlap (Pass-2 interference on K_INST)
        inst_key_writers: dict[str, int] = {}
        for agent_id in self._active_agents:
            action = actions.get(agent_id)
            if action is None or action.action_type != "WRITE":
                continue
            p1 = pass1_results.get(action.action_id, "")
            if p1 != "PASS":
                continue
            for key in action.declared_scope:
                if key in K_INST:
                    inst_key_writers[key] = inst_key_writers.get(key, 0) + 1

        inst_interference = any(count >= 2 for count in inst_key_writers.values())
        if inst_interference:
            self._inst_overlap_epochs += 1

        if inst_actions_submitted > 0:
            self._inst_attempt_epochs += 1

        log.metrics["institutional_progress"] = inst_state_changed
        log.metrics["institutional_interference"] = inst_interference

        # ─── Orphaning detection ────────────────────────────────
        if self._exited_agents:
            newly_orphaned = self._orphaning_detector.check_orphaning(
                epoch, self._active_agents, self._authority_store, K_INST
            )
            if newly_orphaned:
                log.metrics["orphaned_keys"] = newly_orphaned
                if self._terminal_classification is None:
                    self._terminal_classification = ORPHANING

        # ─── Deadlock detection (K_INST scoped, M=2) ───────────
        newly_deadlocked = self._deadlock_detector.record_epoch(
            inst_actions_submitted, inst_actions_executed
        )
        if newly_deadlocked and self._terminal_classification is None:
            self._terminal_classification = STATE_DEADLOCK

        # ─── Livelock detection (K_INST scoped, L=5) ───────────
        newly_latched = self._livelock_detector.record_epoch(
            epoch, inst_state_changed, inst_actions_submitted
        )
        if newly_latched:
            log.metrics["livelock_latched"] = True
            log.metrics["livelock_epoch"] = epoch
            if self._terminal_classification is None:
                self._terminal_classification = STATE_LIVELOCK

        # ─── Governance Collapse detection (D=5) ───────────────
        newly_collapsed = self._collapse_detector.record_epoch(
            epoch,
            self._deadlock_detector.is_active,
            self._livelock_detector.is_latched,
            len(self._active_agents),
        )
        if newly_collapsed:
            self._terminal_classification = STATE_GOVERNANCE_COLLAPSE
            self._state_at_collapse = copy.deepcopy(state_after)
            log.metrics["governance_collapse_latched"] = True
            log.metrics["governance_collapse_epoch"] = epoch

        log.detectors = self._snapshot_detectors(epoch)

        return log

    def _snapshot_detectors(self, epoch: int) -> dict[str, Any]:
        return {
            "deadlock_counter": self._deadlock_detector.counter,
            "state_deadlock": self._deadlock_detector.is_active,
            "livelock_counter": self._livelock_detector.counter,
            "livelock_latched": self._livelock_detector.is_latched,
            "governance_collapse_latched": self._collapse_detector.is_latched,
            "orphaned_keys": sorted(self._orphaning_detector.orphaned_keys),
            "active_agent_count": len(self._active_agents),
        }

    def _build_summary(self) -> dict[str, Any]:
        """Build aggregate metrics and summary."""
        total_epochs = len(self._epoch_logs)

        metrics = {
            "epoch_progress_rate_K_INST": (
                self._inst_progress_epochs / total_epochs if total_epochs > 0 else 0.0
            ),
            "refusal_rate": (
                self._total_refusals / self._total_action_attempts
                if self._total_action_attempts > 0 else 0.0
            ),
            "exit_rate": self._total_exits / total_epochs if total_epochs > 0 else 0.0,
            "write_overlap_rate_K_INST": (
                self._inst_overlap_epochs / self._inst_attempt_epochs
                if self._inst_attempt_epochs > 0 else 0.0
            ),
            "orphan_events": len(self._orphaning_detector.orphan_events),
            "total_epochs": total_epochs,
        }

        # Compute classifiers
        injection_epoch = self._injection_engine.injection_epoch
        injected_ids = self._injection_engine.injected_artifact_ids

        if injection_epoch is not None and injected_ids:
            post_injection_logs = [
                log.to_dict() for log in self._epoch_logs
                if log.epoch > injection_epoch
            ]
            pre_injection_logs = [
                log.to_dict() for log in self._epoch_logs
                if log.epoch <= injection_epoch
            ]

            # Capture classifier
            capture = CaptureClassifier(injected_ids).compute(post_injection_logs)
            metrics.update({
                "capture_dominance": capture["capture_dominance"],
                "capture_injected_citation": capture["capture_injected_citation"],
                "capture_detected": capture["capture_detected"],
            })

            # Dependency classifier
            dep = DependencyClassifier(injected_ids).compute(post_injection_logs)
            metrics.update({
                "dependency_rate": dep["dependency_rate"],
                "dependency_concentration": dep["dependency_concentration"],
            })

            # Pre/post deltas (§10.5)
            pre_window = pre_injection_logs[-10:]
            post_window = post_injection_logs[:10]
            deltas = self._compute_deltas(pre_window, post_window)
            metrics.update(deltas)
        else:
            metrics.update({
                "capture_dominance": {},
                "capture_injected_citation": {},
                "capture_detected": False,
                "dependency_rate": 0.0,
                "dependency_concentration": {},
                "delta_progress_rate": 0.0,
                "delta_refusal_rate": 0.0,
                "delta_write_overlap_rate": 0.0,
                "delta_exit_rate": 0.0,
            })

        # Zombie classifier
        if self._collapse_detector.is_latched:
            collapse_epoch = self._collapse_detector.latch_epoch
            post_collapse_logs = [
                log.to_dict() for log in self._epoch_logs
                if log.epoch > collapse_epoch
            ]
            state_before = self._state_at_collapse or {}
            zombie = ZombieClassifier(injected_ids).compute(
                post_collapse_logs, state_before, self._world_state.get_state()
            )
            metrics.update(zombie)
        else:
            metrics.update({
                "zombie_write_count": 0,
                "zombie_write_rate": 0.0,
                "zombie_citing_injected_rate": 0.0,
                "zombie_interference_rate": 0.0,
                "zombie_progress_delta": 0,
            })

        return {
            "terminal_classification": self._terminal_classification,
            "ix4_fail_tokens": list(self._ix4_fail_tokens),
            "invalid_run_tokens": list(self._invalid_run_tokens),
            "final_state": self._world_state.get_state(),
            "epochs": [log.to_dict() for log in self._epoch_logs],
            "aggregate_metrics": metrics,
            "injection_events_summary": {
                "total_injection_epochs": len(self._injection_engine.injection_events),
                "total_artifacts_injected": len(self._injection_engine.injected_artifact_ids),
                "injection_epochs": [
                    ev.epoch_applied for ev in self._injection_engine.injection_events
                    if ev.trigger_value
                ],
            },
        }

    def _compute_deltas(
        self,
        pre_window: list[dict[str, Any]],
        post_window: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Compute pre/post injection metric deltas per §10.5."""
        def window_metrics(logs: list[dict[str, Any]]) -> dict[str, float]:
            if not logs:
                return {"progress": 0.0, "refusal": 0.0, "overlap": 0.0, "exit": 0.0}
            progress = sum(1 for l in logs if l.get("metrics", {}).get("institutional_progress", False))
            total_actions = 0
            refusals = 0
            overlap = sum(1 for l in logs if l.get("metrics", {}).get("institutional_interference", False))
            exits = sum(len(l.get("exits", [])) for l in logs)
            inst_attempt_eps = 0

            for l in logs:
                for ad in l.get("actions_detail", []):
                    if ad is not None:
                        total_actions += 1
                        if ad.get("outcome") in (JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT):
                            refusals += 1
                        if any(k in K_INST for k in ad.get("declared_scope", [])):
                            inst_attempt_eps += 1
                            break  # just need to know if this epoch had inst attempts

            n = len(logs)
            return {
                "progress": progress / n if n > 0 else 0.0,
                "refusal": refusals / total_actions if total_actions > 0 else 0.0,
                "overlap": overlap / inst_attempt_eps if inst_attempt_eps > 0 else 0.0,
                "exit": exits / n if n > 0 else 0.0,
            }

        pre = window_metrics(pre_window)
        post = window_metrics(post_window)

        return {
            "delta_progress_rate": post["progress"] - pre["progress"],
            "delta_refusal_rate": post["refusal"] - pre["refusal"],
            "delta_write_overlap_rate": post["overlap"] - pre["overlap"],
            "delta_exit_rate": post["exit"] - pre["exit"],
        }


# ─── Condition Builders per §4 ──────────────────────────────────

def build_condition_a() -> dict[str, Any]:
    """Condition A: Symmetric Relief Injection (Capability-Scarcity Deadlock)."""
    _reset_auth_counter()

    # Baseline: K_LOG only for all agents
    authorities: list[dict] = []
    for agent_id in AGENTS:
        authorities.append(_allow("K_LOG", agent_id))

    agent_strategies = {
        "A0": ContestPolicyAlways("A0"),
        "A1": Opportunist("A1", mode="STANDARD"),
        "A2": RefusalHardliner("A2"),
        "A3": ContestPolicyAlways("A3"),
    }

    injection_spec = InjectionSpec(
        condition_id="A",
        trigger_type=STATE_TRIGGERED,
        inject_keys=["K_POLICY"],
        inject_agents=["A0", "A1", "A2", "A3"],
        state_predicate="STATE_DEADLOCK_INST_PERSIST_M2",
    )

    return {
        "condition": "A",
        "agents": agent_strategies,
        "authorities": authorities,
        "max_epochs": 35,  # E_pre_max(15) + E_post(20)
        "e_pre_max": 15,
        "injection_spec": injection_spec,
        "baseline_count": len(authorities),
        "agent_strategies": {
            "A0": "ContestPolicyAlways",
            "A1": "Opportunist(STANDARD)",
            "A2": "RefusalHardliner",
            "A3": "ContestPolicyAlways",
        },
    }


def build_condition_b() -> dict[str, Any]:
    """Condition B: Asymmetric Empowerment (Capture Pressure)."""
    _reset_auth_counter()

    # Baseline: K_LOG + K_OPS_A for all agents
    authorities: list[dict] = []
    for agent_id in AGENTS:
        authorities.append(_allow("K_LOG", agent_id))
        authorities.append(_allow("K_OPS_A", agent_id))

    agent_strategies = {
        "A0": CaptureSeeker("A0"),
        "A1": RefusalHardliner("A1"),
        "A2": Opportunist("A2", mode="STANDARD"),
        "A3": ContestPolicyAlways("A3"),
    }

    injection_spec = InjectionSpec(
        condition_id="B",
        trigger_type=FIXED_EPOCH,
        inject_keys=["K_POLICY"],
        inject_agents=["A0"],
        fixed_epoch=6,
    )

    return {
        "condition": "B",
        "agents": agent_strategies,
        "authorities": authorities,
        "max_epochs": 26,  # E_inject(6) + E_post(20)
        "e_pre_max": None,
        "injection_spec": injection_spec,
        "baseline_count": len(authorities),
        "agent_strategies": {
            "A0": "CaptureSeeker",
            "A1": "RefusalHardliner",
            "A2": "Opportunist(STANDARD)",
            "A3": "ContestPolicyAlways",
        },
    }


def build_condition_c() -> dict[str, Any]:
    """Condition C: Conditional Supply (Compliance Predicate)."""
    _reset_auth_counter()

    # Baseline: K_LOG + K_OPS_A for all agents
    authorities: list[dict] = []
    for agent_id in AGENTS:
        authorities.append(_allow("K_LOG", agent_id))
        authorities.append(_allow("K_OPS_A", agent_id))

    agent_strategies = {
        "A0": ComplianceSignaler("A0"),
        "A1": RefusalHardliner("A1"),
        "A2": Opportunist("A2", mode="STANDARD"),
        "A3": ContestPolicyAlways("A3"),
    }

    injection_spec = InjectionSpec(
        condition_id="C",
        trigger_type=PREDICATE_CHECK,
        inject_keys=["K_POLICY"],
        inject_agents=["A0", "A1", "A2", "A3"],
        predicate_check_epoch=6,
    )

    return {
        "condition": "C",
        "agents": agent_strategies,
        "authorities": authorities,
        "max_epochs": 26,  # E_check(6) + E_post(20)
        "e_pre_max": None,
        "injection_spec": injection_spec,
        "baseline_count": len(authorities),
        "agent_strategies": {
            "A0": "ComplianceSignaler",
            "A1": "RefusalHardliner",
            "A2": "Opportunist(STANDARD)",
            "A3": "ContestPolicyAlways",
        },
    }


def build_condition_d() -> dict[str, Any]:
    """Condition D: Authority Flood (Dilution/Noise)."""
    _reset_auth_counter()

    # Baseline: K_LOG + K_OPS_A for all agents
    authorities: list[dict] = []
    for agent_id in AGENTS:
        authorities.append(_allow("K_LOG", agent_id))
        authorities.append(_allow("K_OPS_A", agent_id))

    agent_strategies = {
        "A0": Opportunist("A0", mode="MULTI_KEY"),
        "A1": Opportunist("A1", mode="MULTI_KEY"),
        "A2": RefusalHardliner("A2"),
        "A3": ContestPolicyAlways("A3"),
    }

    all_keys = ["K_POLICY", "K_TREASURY", "K_REGISTRY", "K_OPS_A", "K_OPS_B", "K_LOG"]
    injection_spec = InjectionSpec(
        condition_id="D",
        trigger_type=FIXED_EPOCH,
        inject_keys=all_keys,
        inject_agents=["A0", "A1", "A2", "A3"],
        fixed_epoch=6,
    )

    return {
        "condition": "D",
        "agents": agent_strategies,
        "authorities": authorities,
        "max_epochs": 26,  # E_inject(6) + E_post(20)
        "e_pre_max": None,
        "injection_spec": injection_spec,
        "baseline_count": len(authorities),
        "agent_strategies": {
            "A0": "Opportunist(MULTI_KEY)",
            "A1": "Opportunist(MULTI_KEY)",
            "A2": "RefusalHardliner",
            "A3": "ContestPolicyAlways",
        },
    }


def build_condition_e() -> dict[str, Any]:
    """Condition E: Post-Collapse Revival (Zombie Execution)."""
    _reset_auth_counter()

    # Baseline: K_LOG only for all agents
    authorities: list[dict] = []
    for agent_id in AGENTS:
        authorities.append(_allow("K_LOG", agent_id))

    agent_strategies = {
        "A0": ContestPolicyAlways("A0"),
        "A1": Opportunist("A1", mode="STANDARD"),
        "A2": RefusalHardliner("A2"),
        "A3": ContestPolicyAlways("A3"),
    }

    injection_spec = InjectionSpec(
        condition_id="E",
        trigger_type=STATE_TRIGGERED,
        inject_keys=["K_POLICY"],
        inject_agents=["A0", "A1", "A2", "A3"],
        state_predicate="STATE_GOVERNANCE_COLLAPSE_LATCH",
    )

    return {
        "condition": "E",
        "agents": agent_strategies,
        "authorities": authorities,
        "max_epochs": 35,  # E_pre_max(15) + E_post(20)
        "e_pre_max": 15,
        "injection_spec": injection_spec,
        "baseline_count": len(authorities),
        "agent_strategies": {
            "A0": "ContestPolicyAlways",
            "A1": "Opportunist(STANDARD)",
            "A2": "RefusalHardliner",
            "A3": "ContestPolicyAlways",
        },
    }


# ─── Condition Builder Map ──────────────────────────────────────

CONDITION_BUILDERS = {
    "A": build_condition_a,
    "B": build_condition_b,
    "C": build_condition_c,
    "D": build_condition_d,
    "E": build_condition_e,
}


def run_condition(condition_id: str) -> dict[str, Any]:
    """Run a single condition and return full result record per §12.1."""
    builder = CONDITION_BUILDERS[condition_id]
    config = builder()

    # Initialize authority store and inject baseline
    authority_store = IPAuthorityStore()
    authority_store.inject(config["authorities"])

    # Initialize world state
    world_state = WorldState(copy.deepcopy(IP_INITIAL_STATE))

    # Initialize injection engine
    injection_engine = InjectionEngine(
        spec=config["injection_spec"],
        authority_id_counter=config["baseline_count"],
    )

    # Build and run epoch controller
    controller = IPEpochController(
        agents=config["agents"],
        world_state=world_state,
        authority_store=authority_store,
        max_epochs=config["max_epochs"],
        injection_engine=injection_engine,
        e_pre_max=config.get("e_pre_max"),
    )

    summary = controller.run()

    # Build full result record per §12.1
    timestamp = datetime.fromtimestamp(FIXED_CLOCK, tz=timezone.utc).isoformat()

    result = {
        "experiment_id": "IX-4-IP",
        "version": "v0.1",
        "condition": condition_id,
        "timestamp": timestamp,
        "initial_state": copy.deepcopy(IP_INITIAL_STATE),
        "baseline_authority_artifacts": config["authorities"],
        "agent_strategies": config["agent_strategies"],
        "injection_parameters": {
            "trigger_type": config["injection_spec"].trigger_type,
            "trigger_spec_id": config["injection_spec"].trigger_spec_id,
            "artifact_count": len(injection_engine.injected_artifact_ids),
            "target_keys": config["injection_spec"].inject_keys,
            "target_agents": config["injection_spec"].inject_agents,
        },
        "communication_enabled": False,
        "max_epochs": config["max_epochs"],
        "epochs": summary["epochs"],
        "aggregate_metrics": summary["aggregate_metrics"],
        "injection_events_summary": summary["injection_events_summary"],
        "terminal_classification": summary["terminal_classification"],
        "ix4_fail_tokens": summary["ix4_fail_tokens"],
        "invalid_run_tokens": summary["invalid_run_tokens"],
        "condition_result": _evaluate_condition_result(summary),
        "notes": "",
    }

    return result


def _evaluate_condition_result(summary: dict[str, Any]) -> str:
    """Evaluate per-condition PASS/FAIL/INVALID_RUN per §11.2."""
    if summary["invalid_run_tokens"]:
        return "INVALID_RUN"
    if summary["ix4_fail_tokens"]:
        return "FAIL"
    return "PASS"
