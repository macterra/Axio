"""HandoffRecordThenExit / StandbyInstitutional — Per preregistration §7.1.

Used in: C (A3 = HandoffRecordThenExit, A1 = StandbyInstitutional).
"""

from typing import Any, Optional

from .._kernel import RSA, Observation, ActionRequest


class HandoffRecordThenExit(RSA):
    """Writes handoff record at epoch 10 then exits.

    Before epoch 10: writes K_REGISTRY and K_LOG (rotating).
    At epoch 10: writes handoff to K_REGISTRY + K_LOG, then exits.
    """

    def __init__(
        self,
        agent_id: str,
        registry_allow_id: str,
        log_allow_id: str,
        policy_allow_id: str,
    ):
        self.id = agent_id
        self.registry_allow_id = registry_allow_id
        self.log_allow_id = log_allow_id
        self.policy_allow_id = policy_allow_id
        self._current_epoch: int = 0

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        # Exit at epoch 10.  The handoff record was already written at
        # epoch 9, so the HANDOFF marker is in K_LOG before we leave.
        return self._current_epoch >= 10

    def compose_message(self) -> Optional[dict[str, Any]]:
        if self._current_epoch == 9:
            return {"type": "HANDOFF_NOTICE", "successor": "A1", "epoch": 9}
        return {"status": "primary_active", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        if self._current_epoch == 9:
            # Handoff record at epoch 9 (last epoch before exit)
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_REGISTRY", "K_LOG"],
                proposed_delta={
                    "K_REGISTRY": "members=A0,A1,A2;opA=A1;opB=A2;coord=A1",
                    "K_LOG": f"E{self._current_epoch}:HANDOFF {self.id}->A1",
                },
                authorities_cited=[self.registry_allow_id, self.log_allow_id],
            )
        # Before epoch 10: rotate among institutional keys
        keys_and_auths = [
            ("K_REGISTRY", self.registry_allow_id),
            ("K_LOG", self.log_allow_id),
            ("K_POLICY", self.policy_allow_id),
        ]
        target, auth_id = keys_and_auths[self._current_epoch % 3]
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"{target}_{self._current_epoch}_{self.id}"},
            authorities_cited=[auth_id],
        )


class StandbyInstitutional(RSA):
    """Standby agent that activates institutional writes after primary exits.

    Before exit detected: writes K_OPS_A only (to avoid interference).
    After exit detected: rotates among K_REGISTRY, K_LOG, K_POLICY.
    """

    def __init__(
        self,
        agent_id: str,
        ops_a_allow_id: str,
        registry_allow_id: str,
        log_allow_id: str,
        policy_allow_id: str,
    ):
        self.id = agent_id
        self.ops_a_allow_id = ops_a_allow_id
        self.registry_allow_id = registry_allow_id
        self.log_allow_id = log_allow_id
        self.policy_allow_id = policy_allow_id
        self._current_epoch: int = 0
        self._primary_exited: bool = False
        self._activation_epoch: int = -1

    def observe(self, observation: Observation) -> None:
        self._current_epoch = observation.epoch
        # Detect handoff via K_LOG content
        log_val = observation.world_state.get("K_LOG", "")
        if "HANDOFF" in str(log_val) and not self._primary_exited:
            self._primary_exited = True
            self._activation_epoch = self._current_epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        if self._primary_exited:
            return {"status": "standby_activated", "epoch": self._current_epoch}
        return {"status": "standby_waiting", "epoch": self._current_epoch}

    def propose_action(self) -> Optional[ActionRequest]:
        if not self._primary_exited:
            # Before activation: write OPS_A only
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self._current_epoch}:0",
                action_type="WRITE",
                declared_scope=["K_OPS_A"],
                proposed_delta={"K_OPS_A": f"op_a_{self._current_epoch}"},
                authorities_cited=[self.ops_a_allow_id],
            )
        # After activation: rotate institutional keys
        keys_and_auths = [
            ("K_REGISTRY", self.registry_allow_id),
            ("K_LOG", self.log_allow_id),
            ("K_POLICY", self.policy_allow_id),
        ]
        offset = self._current_epoch - self._activation_epoch
        target, auth_id = keys_and_auths[offset % 3]
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self._current_epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"{target}_{self._current_epoch}_{self.id}"},
            authorities_cited=[auth_id],
        )
