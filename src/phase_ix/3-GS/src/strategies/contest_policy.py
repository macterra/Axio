"""ContestPolicyAlways and ContestPolicyDelayed_6 — Per preregistration §7.1.

ContestPolicyAlways: proposes WRITE to K_POLICY every epoch.
ContestPolicyDelayed_6: returns None for epochs 0-5, contests from epoch 6.

Used in: A (all agents), E (A0, A1), H (A0 always, A1 delayed from epoch 6).
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


class ContestPolicyDelayed_6(RSA):
    """Returns None for epochs 0-5, then contests K_POLICY from epoch 6.

    Used in Condition H to ensure the run reaches the partition window (6-11)
    before 2-way livelock triggers.
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
        # Delay contest until epoch 6 to allow run to reach partition window
        if self._current_epoch < 6:
            return None
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=["K_POLICY"],
            proposed_delta={"K_POLICY": f"P{self._current_epoch}_{self.id}"},
            authorities_cited=[self.policy_allow_id],
        )
