"""
IP Injection Engine — Per preregistration §5.

Implements:
  - Trigger evaluation (STATE_TRIGGERED, FIXED_EPOCH, PREDICATE_CHECK)
  - Authority artifact creation (IP-NNNN format)
  - InjectionEvent logging (§5.4)
"""

import hashlib
import json
from typing import Any, Optional

from ._kernel import IPAuthorityStore


# ─── Trigger types per §5.2 ────────────────────────────────────

STATE_TRIGGERED = "STATE_TRIGGERED"
FIXED_EPOCH = "FIXED_EPOCH"
PREDICATE_CHECK = "PREDICATE_CHECK"

# ─── Trigger spec IDs per §5.4 ─────────────────────────────────

TRIGGER_SPEC_IDS = {
    "A": "STATE_DEADLOCK_INST_PERSIST_M2",
    "B": "FIXED_EPOCH_6",
    "C": "COMPLIANCE_ACK_PRESENT_AT_E6",
    "D": "FIXED_EPOCH_6",
    "E": "STATE_GOVERNANCE_COLLAPSE_LATCH",
}


class InjectionEvent:
    """Record of an injection attempt per §5.4."""

    def __init__(
        self,
        epoch_applied: int,
        condition_id: str,
        trigger_type: str,
        trigger_spec_id: str,
        trigger_predicate: str,
        trigger_value: bool,
        artifacts: list[dict[str, Any]],
    ):
        self.event_type = "AUTHORITY_INJECTION"
        self.epoch_applied = epoch_applied
        self.condition_id = condition_id
        self.trigger_type = trigger_type
        self.trigger_spec_id = trigger_spec_id
        self.trigger_predicate = trigger_predicate
        self.trigger_value = trigger_value
        self.artifacts = artifacts
        self.artifacts_count = len(artifacts)
        self.artifacts_digest = self._compute_digest(artifacts)

    @staticmethod
    def _compute_digest(artifacts: list[dict[str, Any]]) -> str:
        """Compute SHA-256 of canonical artifact serialization per §2.5."""
        if not artifacts:
            return hashlib.sha256(b"").hexdigest()
        canonical_strings = []
        for auth in artifacts:
            s = json.dumps({
                "authority_id": auth["authority_id"],
                "commitment": auth["commitment"],
                "created_epoch": auth["created_epoch"],
                "holder_agent_id": auth["holder_agent_id"],
                "issuer_agent_id": auth["issuer_agent_id"],
                "scope": [{"operation": sa["operation"], "target": sa["target"]}
                          for sa in auth["scope"]],
                "status": auth["status"],
            }, separators=(',', ':'), ensure_ascii=False)
            canonical_strings.append(s)
        canonical_strings.sort()
        payload = "\n".join(canonical_strings)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "epoch_applied": self.epoch_applied,
            "condition_id": self.condition_id,
            "trigger_type": self.trigger_type,
            "trigger_spec_id": self.trigger_spec_id,
            "trigger_evidence": {
                "predicate": self.trigger_predicate,
                "value": self.trigger_value,
            },
            "artifacts": self.artifacts,
            "artifacts_count": self.artifacts_count,
            "artifacts_digest": self.artifacts_digest,
        }


class InjectionSpec:
    """Specification for a single injection regime.

    Encapsulates the trigger type, trigger parameters, and payload
    (keys to inject, agents to receive) for one condition.
    """

    def __init__(
        self,
        condition_id: str,
        trigger_type: str,
        inject_keys: list[str],
        inject_agents: list[str],
        fixed_epoch: Optional[int] = None,
        predicate_check_epoch: Optional[int] = None,
        state_predicate: Optional[str] = None,
    ):
        self.condition_id = condition_id
        self.trigger_type = trigger_type
        self.inject_keys = inject_keys
        self.inject_agents = inject_agents
        self.fixed_epoch = fixed_epoch
        self.predicate_check_epoch = predicate_check_epoch
        self.state_predicate = state_predicate
        self.trigger_spec_id = TRIGGER_SPEC_IDS[condition_id]


class InjectionEngine:
    """Manages authority injection per §5.

    Evaluates triggers, creates artifacts, logs InjectionEvents.
    Called at Step 0 of each epoch (§2.8).
    """

    def __init__(self, spec: InjectionSpec, authority_id_counter: int):
        self._spec = spec
        self._auth_counter = authority_id_counter
        self._injected = False
        self._injection_events: list[InjectionEvent] = []
        self._injected_artifact_ids: set[str] = set()

    @property
    def injected(self) -> bool:
        return self._injected

    @property
    def injection_events(self) -> list[InjectionEvent]:
        return list(self._injection_events)

    @property
    def injected_artifact_ids(self) -> set[str]:
        return set(self._injected_artifact_ids)

    @property
    def injection_epoch(self) -> Optional[int]:
        """Return the epoch at which injection occurred, or None."""
        if self._injection_events:
            for ev in self._injection_events:
                if ev.trigger_value:
                    return ev.epoch_applied
        return None

    def _next_auth_id(self) -> str:
        self._auth_counter += 1
        return f"IP-{self._auth_counter:04d}"

    def evaluate_step0(
        self,
        epoch: int,
        authority_store: IPAuthorityStore,
        state_deadlock_active: bool = False,
        deadlock_persist_count: int = 0,
        governance_collapse_latched: bool = False,
        world_state: Optional[dict[str, Any]] = None,
    ) -> Optional[InjectionEvent]:
        """Evaluate injection trigger at Step 0 of epoch.

        Returns InjectionEvent if injection attempted (even if predicate fails),
        or None if no trigger applies this epoch.
        """
        if self._injected:
            return None

        spec = self._spec

        if spec.trigger_type == FIXED_EPOCH:
            if epoch != spec.fixed_epoch:
                return None
            return self._do_inject(epoch, authority_store,
                                   predicate=spec.trigger_spec_id,
                                   value=True)

        elif spec.trigger_type == STATE_TRIGGERED:
            if spec.state_predicate == "STATE_DEADLOCK_INST_PERSIST_M2":
                # Condition A: deadlock persisted for M=2 consecutive epochs
                if state_deadlock_active and deadlock_persist_count >= 2:
                    return self._do_inject(epoch, authority_store,
                                           predicate=spec.trigger_spec_id,
                                           value=True)
            elif spec.state_predicate == "STATE_GOVERNANCE_COLLAPSE_LATCH":
                # Condition E: governance collapse latch fired
                if governance_collapse_latched:
                    return self._do_inject(epoch, authority_store,
                                           predicate=spec.trigger_spec_id,
                                           value=True)
            return None

        elif spec.trigger_type == PREDICATE_CHECK:
            if epoch != spec.predicate_check_epoch:
                return None
            # Condition C: check if COMPLIANCE_ACK in K_LOG
            if world_state is not None:
                predicate_met = "COMPLIANCE_ACK" in str(world_state.get("K_LOG", ""))
            else:
                predicate_met = False
            return self._do_inject(epoch, authority_store,
                                   predicate=spec.trigger_spec_id,
                                   value=predicate_met)

        return None

    def _do_inject(
        self,
        epoch: int,
        authority_store: IPAuthorityStore,
        predicate: str,
        value: bool,
    ) -> InjectionEvent:
        """Create artifacts and log injection event."""
        artifacts: list[dict[str, Any]] = []

        if value:
            # Create injection artifacts
            for key in self._spec.inject_keys:
                for agent_id in self._spec.inject_agents:
                    auth = {
                        "authority_id": self._next_auth_id(),
                        "commitment": "ALLOW",
                        "created_epoch": epoch,
                        "holder_agent_id": agent_id,
                        "issuer_agent_id": "harness",
                        "scope": [{"operation": "WRITE", "target": f"STATE:/{key}"}],
                        "status": "ACTIVE",
                    }
                    artifacts.append(auth)
                    self._injected_artifact_ids.add(auth["authority_id"])

            # Inject into authority store
            authority_store.inject(artifacts)
            self._injected = True

        event = InjectionEvent(
            epoch_applied=epoch,
            condition_id=self._spec.condition_id,
            trigger_type=self._spec.trigger_type,
            trigger_spec_id=self._spec.trigger_spec_id,
            trigger_predicate=predicate,
            trigger_value=value,
            artifacts=artifacts,
        )
        self._injection_events.append(event)

        # For Condition C no-inject: still mark as attempted but not injected
        if not value:
            self._injected = True  # prevent re-evaluation

        return event
