"""ReclaimAttempt_NoAuthority / ExitAbruptNoHandoff — Per preregistration §7.1.

Used in: D (A3 = ExitAbruptNoHandoff), J (A1 = ReclaimAttempt_NoAuthority).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class ExitAbruptNoHandoff(RSA):
    """Exits immediately at scheduled epoch with no handoff write."""

    def __init__(self, agent_id: str, exit_epoch: int = 10):
        self.id = agent_id
        self.exit_epoch = exit_epoch
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return self._current_epoch == self.exit_epoch

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        return None


class ReclaimAttempt_NoAuthority(RSA):
    """Attempts to reclaim orphaned K_OPS_A without authority at epoch 4.

    Used in: J (A1) to validate closed-world capability enforcement.
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
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch == 4:
            # Attempt to reclaim orphaned K_OPS_A without authority
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_OPS_A"],
                proposed_delta={"K_OPS_A": "free"},
                authorities_cited=[],  # No authority!
            )
        # Normal: write K_POLICY
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": f"P{self._current_epoch}_{self.id}"},
            authorities_cited=[self.policy_allow_id],
        )
