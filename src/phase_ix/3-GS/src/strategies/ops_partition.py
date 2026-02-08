"""OpsPartitionWriter_A / OpsPartitionWriter_B — Per preregistration §7.1.

Write to partitioned OPS key each epoch.
Used in: B (A0→OPS_A, A1→OPS_B), C (A0→OPS_A, A2→OPS_B), G (A1→OPS_A, A2→OPS_B).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class OpsPartitionWriter_A(RSA):
    """Writes K_OPS_A every epoch."""

    def __init__(self, agent_id: str, ops_a_allow_id: str):
        self.id = agent_id
        self.ops_a_allow_id = ops_a_allow_id
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
            declared_scope=["K_OPS_A"],
            proposed_delta={"K_OPS_A": f"op_a_{self._current_epoch}"},
            authorities_cited=[self.ops_a_allow_id],
        )


class OpsPartitionWriter_B(RSA):
    """Writes K_OPS_B every epoch."""

    def __init__(self, agent_id: str, ops_b_allow_id: str):
        self.id = agent_id
        self.ops_b_allow_id = ops_b_allow_id
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
            declared_scope=["K_OPS_B"],
            proposed_delta={"K_OPS_B": f"op_b_{self._current_epoch}"},
            authorities_cited=[self.ops_b_allow_id],
        )
