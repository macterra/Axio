"""Coordinator_RegistryLog / DeferToCoordinator — Per preregistration §7.1.

Used in: G (A0 = Coordinator_RegistryLog, A1/A2/A3 = DeferToCoordinator).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class Coordinator_RegistryLog(RSA):
    """Manages K_REGISTRY and K_LOG by alternating; exits at epoch 8."""

    def __init__(
        self,
        agent_id: str,
        registry_allow_id: str,
        log_allow_id: str,
    ):
        self.id = agent_id
        self.registry_allow_id = registry_allow_id
        self.log_allow_id = log_allow_id
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return self._current_epoch == 8

    def compose_message(self) -> Optional[dict[str, Any]]:
        return {"status": "coordinator_active", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        target = "K_REGISTRY" if self._current_epoch % 2 == 0 else "K_LOG"
        auth_id = (
            self.registry_allow_id
            if target == "K_REGISTRY"
            else self.log_allow_id
        )
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"{target}_{self._current_epoch}_coord"},
            authorities_cited=[auth_id],
        )


class DeferToCoordinator(RSA):
    """Operates within own scope; defers coordination to A0.

    A1 → K_OPS_A, A2 → K_OPS_B, A3 → K_TREASURY.
    """

    def __init__(
        self,
        agent_id: str,
        target_key: str,
        allow_id: str,
    ):
        self.id = agent_id
        self._target_key = target_key
        self._allow_id = allow_id
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return {"status": "deferred", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[self._target_key],
            proposed_delta={self._target_key: f"{self._target_key}_{self._current_epoch}_{self.id}"},
            authorities_cited=[self._allow_id],
        )
