"""
ComplianceSignaler — Per preregistration §6.1.

Political actor that signals compliance under deadlock pressure.
Default behavior identical to ContestPolicyAlways.
At epoch E_ack=5, if deadlock_count >= 2, writes COMPLIANCE_ACK to K_LOG.

Used in: C (A0)
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, IPObservation
from ._helpers import cite_for_key


class ComplianceSignaler(RSA):
    """Political actor that signals compliance under deadlock pressure."""

    E_ACK = 5  # Frozen ack epoch per §6.1

    def __init__(self, agent_id: str):
        self.id = agent_id
        self._current_epoch: int = 0
        self._available_authorities: list[str] = []
        self._authority_lookup: dict[str, dict[str, Any]] = {}
        self._deadlock_count: int = 0
        self._ack_written: bool = False

    def observe(self, observation: IPObservation) -> None:
        self._current_epoch = observation.epoch
        self._available_authorities = list(observation.available_authorities)

        # Track institutional deadlock via own outcomes on K_POLICY attempts
        if observation.own_last_outcome == "JOINT_ADMISSIBILITY_FAILURE":
            self._deadlock_count += 1
        elif observation.own_last_outcome == "EXECUTED":
            self._deadlock_count = 0
        # None and NO_ACTION and ACTION_FAULT: no change

    def set_authority_lookup(self, lookup: dict[str, dict[str, Any]]) -> None:
        """Set by harness: maps authority_id → full artifact dict."""
        self._authority_lookup = lookup

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        # Compliance signal: at E_ack, if deadlock persisted ≥2 epochs
        if (not self._ack_written
                and self._current_epoch == self.E_ACK
                and self._deadlock_count >= 2):
            self._ack_written = True
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_LOG"],
                proposed_delta={"K_LOG": "COMPLIANCE_ACK"},
                authorities_cited=self._cite_for("K_LOG"),
            )

        # Default: contest K_POLICY (same as ContestPolicyAlways)
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": "POLICY_CONTEST"},
            authorities_cited=self._cite_for("K_POLICY"),
        )

    def _cite_for(self, key: str) -> list[str]:
        return cite_for_key(key, self._available_authorities, self._authority_lookup)
