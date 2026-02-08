"""OccasionalLogChallenger — Per preregistration §7.1.

Writes K_TREASURY most epochs; writes K_LOG every 5th epoch.
Used in: B (A2).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class OccasionalLogChallenger(RSA):
    """Writes K_TREASURY normally; challenges K_LOG every 5th epoch."""

    def __init__(
        self,
        agent_id: str,
        treasury_allow_id: str,
        log_allow_id: str,
    ):
        self.id = agent_id
        self.treasury_allow_id = treasury_allow_id
        self.log_allow_id = log_allow_id
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return {"status": "challenger_active", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch % 5 == 0:
            # Challenge K_LOG (may interfere with A3's steward rotation)
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_LOG"],
                proposed_delta={"K_LOG": f"LOG_A2_{self._current_epoch}"},
                authorities_cited=[self.log_allow_id],
            )
        else:
            # Normal treasury write
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_TREASURY"],
                proposed_delta={"K_TREASURY": 100 - self._current_epoch},
                authorities_cited=[self.treasury_allow_id],
            )
