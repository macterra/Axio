"""ContestPolicyAlways — Per preregistration §7.1.

All agents propose WRITE to K_POLICY every epoch.
Used in: A (all agents), E (A0, A1), H (A0, A1).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class ContestPolicyAlways(RSA):
    """Proposes WRITE to K_POLICY every epoch with agent-specific value."""

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
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": f"P{self._current_epoch}_{self.id}"},
            authorities_cited=[self.policy_allow_id],
        )
