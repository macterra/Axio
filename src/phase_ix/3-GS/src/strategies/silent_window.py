"""SilentWindowObserver_0_11 / InstitutionalLogHeartbeat — Per preregistration §7.1 v0.2.

Used in: H (A2 = SilentWindowObserver_0_11, A3 = InstitutionalLogHeartbeat).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class SilentWindowObserver_0_11(RSA):
    """Silent during epochs 0–11; writes K_POLICY at epoch 12+.

    Per v0.2 amendment: A2 is passive for epochs 0-5 (pre-silence to avoid
    3-way livelock) and epochs 6-11 (partition simulation window).
    Resumes K_POLICY writes at epoch 12.
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
        if self._current_epoch <= 11:
            return None
        return {"status": "observer_active", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch <= 11:
            return None  # Silent epochs 0-11
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": f"P{self._current_epoch}_{self.id}"},
            authorities_cited=[self.policy_allow_id],
        )


# Keep old name as alias for backward compatibility with existing tests
SilentWindowObserver_6_11 = SilentWindowObserver_0_11


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
