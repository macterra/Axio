"""DissolutionSequence — Per preregistration §7.1.

Write dissolution marker to K_LOG, then exit on schedule.
Used in: F (all agents, with exit_epochs = {A0:5, A1:6, A2:7, A3:8}).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class DissolutionSequence(RSA):
    """Writes dissolution marker to K_LOG before exiting at scheduled epoch."""

    def __init__(self, agent_id: str, log_allow_id: str, exit_epoch: int):
        self.id = agent_id
        self.log_allow_id = log_allow_id
        self.exit_epoch = exit_epoch
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return self._current_epoch == self.exit_epoch

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        # Write dissolution marker at exit epoch (before exit check fires)
        # and at the epoch before exit
        if self._current_epoch == self.exit_epoch - 1 or self._current_epoch == self.exit_epoch:
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_LOG"],
                proposed_delta={"K_LOG": f"DISSOLVE:{self.id}:E{self._current_epoch}"},
                authorities_cited=[self.log_allow_id],
            )
        return None
