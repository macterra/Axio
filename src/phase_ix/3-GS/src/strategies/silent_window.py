"""SilentWindowObserver_6_11 / InstitutionalLogHeartbeat — Per preregistration §7.1.

Used in: H (A2 = SilentWindowObserver_6_11, A3 = InstitutionalLogHeartbeat).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class SilentWindowObserver_6_11(RSA):
    """Silent during epochs 6–11; writes K_POLICY outside window.

    During silence window: returns None for both action and message.
    Outside window: writes K_POLICY (same as ContestPolicyAlways).
    """

    def __init__(self, agent_id: str, policy_allow_id: str):
        self.id = agent_id
        self.policy_allow_id = policy_allow_id
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        if 6 <= self._current_epoch <= 11:
            return None
        return {"status": "observer_active", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        if 6 <= self._current_epoch <= 11:
            return None  # Silent
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": f"P{self._current_epoch}_{self.id}"},
            authorities_cited=[self.policy_allow_id],
        )


class InstitutionalLogHeartbeat(RSA):
    """Writes K_LOG heartbeat once at epoch 9; otherwise inactive."""

    def __init__(self, agent_id: str, log_allow_id: str):
        self.id = agent_id
        self.log_allow_id = log_allow_id
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch == 9:
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_LOG"],
                proposed_delta={"K_LOG": f"HEARTBEAT:{self.id}:E{self._current_epoch}"},
                authorities_cited=[self.log_allow_id],
            )
        return None
