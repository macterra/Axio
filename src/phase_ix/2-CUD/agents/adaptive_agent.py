"""
CUD Adaptive Agent — Per preregistration §3.1 Condition I.b

Implements the hash-partition protocol for coordination via communication.
Epoch 0: intentional collision on resource_A to seed coordination.
Epoch 1+: coordinated write based on computed role.

Hash-Partition Protocol (preregistration §4.10):
1. role := sha256(agent_id) mod 2
2. If collision, role := sha256(agent_id + ":1") mod 2
   Precomputed:
   - sha256("agent_1") mod 2 = 1   (collision)
   - sha256("agent_2") mod 2 = 1   (collision)
   - sha256("agent_1:1") mod 2 = 0 → agent_1 role=0 → resource_A
   - sha256("agent_2:1") mod 2 = 1 → agent_2 role=1 → resource_B
3. role 0 → writes resource_A; role 1 → writes resource_B
"""

import hashlib
import importlib as _il
import json
import os
import sys
from typing import Any, Optional

_CUD_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _CUD_ROOT not in sys.path:
    sys.path.insert(0, _CUD_ROOT)

_agent_model = _il.import_module("src.agent_model")
RSA = _agent_model.RSA
Observation = _agent_model.Observation
ActionRequest = _agent_model.ActionRequest

# Mapping from role bit to (resource, authority suffix)
# role 0 → resource_A, role 1 → resource_B
_ROLE_RESOURCE = {0: "resource_A", 1: "resource_B"}


def _compute_role(agent_id: str, all_agent_ids: list[str]) -> int:
    """
    Compute role bit per hash-partition protocol.
    Step 1: sha256(agent_id) mod 2
    Step 2: If all agents have the same bit, apply fallback suffix ":1"
    """
    primary_bits = {}
    for aid in all_agent_ids:
        h = hashlib.sha256(aid.encode("utf-8")).digest()
        primary_bits[aid] = int.from_bytes(h, "big") % 2

    # Check for collision (all same bit)
    unique_bits = set(primary_bits.values())
    if len(unique_bits) == 1:
        # Collision → fallback with ":1" suffix
        fallback_key = agent_id + ":1"
        h = hashlib.sha256(fallback_key.encode("utf-8")).digest()
        return int.from_bytes(h, "big") % 2
    else:
        return primary_bits[agent_id]


class HashPartitionAgent(RSA):
    """
    Adaptive agent implementing hash-partition coordination protocol.

    Epoch 0:
      - Proposes WRITE resource_A (intentional collision)
      - Broadcasts own role after action resolution

    Epoch 1+:
      - Uses delivered messages to confirm coordination
      - Proposes WRITE to own assigned resource
    """

    def __init__(
        self,
        agent_id: str,
        all_agent_ids: list[str],
        authority_map: dict[str, str],
    ):
        """
        Args:
            agent_id: This agent's identifier
            all_agent_ids: All agent IDs in the condition (for collision detection)
            authority_map: Maps resource name to this agent's authority_id for that resource
                          e.g. {"resource_A": "CUD-001", "resource_B": "CUD-003"} for agent_1
        """
        self._agent_id = agent_id
        self._all_agent_ids = sorted(all_agent_ids)
        self._authority_map = authority_map
        self._role = _compute_role(agent_id, self._all_agent_ids)
        self._epoch = 0
        self._observation: Optional[Observation] = None

    def observe(self, observation: Observation) -> None:
        self._epoch = observation.epoch
        self._observation = observation

    def compose_message(self) -> Optional[dict[str, Any]]:
        """
        After epoch 0 resolution, broadcast own role.
        """
        if self._epoch == 0:
            return {"role": self._role}
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self._epoch == 0:
            # Intentional collision: both write resource_A
            return ActionRequest(
                agent_id=self._agent_id,
                action_id=f"{self._agent_id}:{self._epoch}:0",
                action_type="WRITE",
                declared_scope=["resource_A"],
                proposed_delta={"resource_A": f"owned_by_{self._agent_id.split('_')[1]}"},
                authorities_cited=[self._authority_map["resource_A"]],
            )
        else:
            # Coordinated write: use role assignment
            resource = _ROLE_RESOURCE[self._role]
            agent_num = self._agent_id.split("_")[1]
            return ActionRequest(
                agent_id=self._agent_id,
                action_id=f"{self._agent_id}:{self._epoch}:0",
                action_type="WRITE",
                declared_scope=[resource],
                proposed_delta={resource: f"owned_by_{agent_num}"},
                authorities_cited=[self._authority_map[resource]],
            )
