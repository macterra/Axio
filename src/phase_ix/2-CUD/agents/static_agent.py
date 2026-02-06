"""
CUD Static Agent Strategies — Per preregistration §3.1

Static agents ignore outcomes and repeat the same action every epoch.
Used in Conditions A, B, C, D, F, I.a.
"""

import os
import sys
import importlib
from typing import Optional

_CUD_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

_agent_model = importlib.import_module("src.agent_model")
RSA = _agent_model.RSA
Observation = _agent_model.Observation
ActionRequest = _agent_model.ActionRequest


class DisjointWriteAgent(RSA):
    """
    Condition A: writes to own resource, cites own ALLOW.
    Single epoch, no adaptation needed.
    """

    def __init__(self, agent_id: str, resource: str, value: str, authority_id: str):
        self._agent_id = agent_id
        self._resource = resource
        self._value = value
        self._authority_id = authority_id
        self._epoch = 0

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self._agent_id,
            action_id=f"{self._agent_id}:{self._epoch}:0",
            action_type="WRITE",
            declared_scope=[self._resource],
            proposed_delta={self._resource: self._value},
            authorities_cited=[self._authority_id],
        )


class StaticWriteAgent(RSA):
    """
    Conditions B, I.a: writes same resource every epoch, ignores outcomes.
    Used for symmetric livelock scenarios.
    """

    def __init__(self, agent_id: str, resource: str, value: str, authority_id: str):
        self._agent_id = agent_id
        self._resource = resource
        self._value = value
        self._authority_id = authority_id
        self._epoch = 0

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self._agent_id,
            action_id=f"{self._agent_id}:{self._epoch}:0",
            action_type="WRITE",
            declared_scope=[self._resource],
            proposed_delta={self._resource: self._value},
            authorities_cited=[self._authority_id],
        )


class VetoedWriteAgent(RSA):
    """
    Conditions C, D: writes to a vetoed resource every epoch.
    Cites own ALLOW but a global DENY blocks.
    """

    def __init__(self, agent_id: str, resource: str, value: str, authority_id: str):
        self._agent_id = agent_id
        self._resource = resource
        self._value = value
        self._authority_id = authority_id
        self._epoch = 0

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self._agent_id,
            action_id=f"{self._agent_id}:{self._epoch}:0",
            action_type="WRITE",
            declared_scope=[self._resource],
            proposed_delta={self._resource: self._value},
            authorities_cited=[self._authority_id],
        )


class StrategicRefusalAgent(RSA):
    """
    Condition D (agent_2): always proposes None (NO_ACTION).
    Strategic non-participation.
    """

    def __init__(self, agent_id: str):
        self._agent_id = agent_id

    def observe(self, observation: Observation) -> None:
        pass

    def propose_action(self) -> Optional[ActionRequest]:
        return None


class NoCiteWriteAgent(RSA):
    """
    Condition F: writes to resource but cites [] (no ALLOW exists).
    """

    def __init__(self, agent_id: str, resource: str, value: str):
        self._agent_id = agent_id
        self._resource = resource
        self._value = value
        self._epoch = 0

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self._agent_id,
            action_id=f"{self._agent_id}:{self._epoch}:0",
            action_type="WRITE",
            declared_scope=[self._resource],
            proposed_delta={self._resource: self._value},
            authorities_cited=[],
        )


class ExitAfterCollisionAgent(RSA):
    """
    Condition H: proposes WRITE at epoch 0, exits at epoch 1.
    """

    def __init__(self, agent_id: str, resource: str, value: str, authority_id: str):
        self._agent_id = agent_id
        self._resource = resource
        self._value = value
        self._authority_id = authority_id
        self._epoch = 0

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return self._epoch >= 1

    def propose_action(self) -> Optional[ActionRequest]:
        return ActionRequest(
            agent_id=self._agent_id,
            action_id=f"{self._agent_id}:{self._epoch}:0",
            action_type="WRITE",
            declared_scope=[self._resource],
            proposed_delta={self._resource: self._value},
            authorities_cited=[self._authority_id],
        )


class OrphanWriteAgent(RSA):
    """
    Condition G (agent_1): writes resource_B at epoch 0,
    then attempts resource_A at epoch 1 with empty citation.
    """

    def __init__(self, agent_id: str, authority_id_b: str):
        self._agent_id = agent_id
        self._authority_id_b = authority_id_b
        self._epoch = 0

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch

    def propose_action(self) -> Optional[ActionRequest]:
        if self._epoch == 0:
            return ActionRequest(
                agent_id=self._agent_id,
                action_id=f"{self._agent_id}:{self._epoch}:0",
                action_type="WRITE",
                declared_scope=["resource_B"],
                proposed_delta={"resource_B": "owned_by_1"},
                authorities_cited=[self._authority_id_b],
            )
        else:
            # Attempt resource_A with empty citation (sole ALLOW holder exited)
            return ActionRequest(
                agent_id=self._agent_id,
                action_id=f"{self._agent_id}:{self._epoch}:0",
                action_type="WRITE",
                declared_scope=["resource_A"],
                proposed_delta={"resource_A": "owned_by_1"},
                authorities_cited=[],
            )


class OrphanExitAgent(RSA):
    """
    Condition G (agent_2): writes resource_A at epoch 0 (sole ALLOW holder),
    then exits at epoch 1.
    """

    def __init__(self, agent_id: str, authority_id_a: str):
        self._agent_id = agent_id
        self._authority_id_a = authority_id_a
        self._epoch = 0

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch

    def wants_to_exit(self) -> bool:
        return self._epoch >= 1

    def propose_action(self) -> Optional[ActionRequest]:
        if self._epoch == 0:
            return ActionRequest(
                agent_id=self._agent_id,
                action_id=f"{self._agent_id}:{self._epoch}:0",
                action_type="WRITE",
                declared_scope=["resource_A"],
                proposed_delta={"resource_A": "owned_by_2"},
                authorities_cited=[self._authority_id_a],
            )
        return None
