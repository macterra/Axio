"""InstitutionalSteward_Rotate — Per preregistration §7.1.

Rotates writes among K_POLICY, K_REGISTRY, K_LOG.
Used in: B (A3).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class InstitutionalSteward_Rotate(RSA):
    """Rotates WRITE across K_POLICY, K_REGISTRY, K_LOG per epoch."""

    def __init__(self, agent_id: str, allow_ids: dict[str, str]):
        """
        Args:
            agent_id: Agent identifier.
            allow_ids: Map from key name to authority_id, e.g.
                       {"K_POLICY": "GS-...", "K_REGISTRY": "GS-...", "K_LOG": "GS-..."}
        """
        self.id = agent_id
        self._allow_ids = allow_ids
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return {"status": "steward_active", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        keys = sorted(self._allow_ids.keys())
        target = keys[self._current_epoch % len(keys)]
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"{target}_{self._current_epoch}"},
            authorities_cited=[self._allow_ids[target]],
        )
