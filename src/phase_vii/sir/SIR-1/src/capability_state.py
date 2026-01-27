"""
SIR-1 v0.1 Capability State

Implements the L-owned capability overlay per preregistration §6.4-§6.6.

This module is frozen at SIR-1 v0.1 preregistration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set
import time


class PrivilegeEventType(Enum):
    """Type of privilege event."""
    UNLOCK = "UNLOCK"
    GRANT = "GRANT"
    REFUSE = "REFUSE"


@dataclass
class PrivilegeEvent:
    """
    Record of a privilege mutation event.

    Per §6.6: When an action is unlocked at step t, the capability
    persists for steps t+1 through T (end of episode).
    """
    event_id: str
    event_type: PrivilegeEventType
    action_or_capability: str
    authority_claim_id: Optional[str]
    step: int
    timestamp: float
    persistence: str  # "episode_irreversible" or "step_scoped"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "action_or_capability": self.action_or_capability,
            "authority_claim_id": self.authority_claim_id,
            "step": self.step,
            "timestamp": self.timestamp,
            "persistence": self.persistence,
        }


@dataclass
class CapabilityMutation:
    """Record of capability state change for audit."""
    mutation_id: str
    mutation_type: str  # "ADD" or "REMOVE"
    target: str
    authority_claim_id: str
    step: int
    valid: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mutation_id": self.mutation_id,
            "mutation_type": self.mutation_type,
            "target": self.target,
            "authority_claim_id": self.authority_claim_id,
            "step": self.step,
            "valid": self.valid,
        }


class CapabilityState:
    """
    L-owned capability overlay per §6.4.

    Binding constraints:
    - P (Agent Core) cannot directly read or write capability state
    - Only L may mutate capability state via valid authority claims
    - BASE_FORBID_MAP is never mutated
    - Capability mutation grants future permission only; it does not
      itself constitute an action execution
    """

    def __init__(self):
        self._unlocked_actions: Set[str] = set()
        self._privilege_log: List[PrivilegeEvent] = []
        self._mutations: List[CapabilityMutation] = []
        self._event_counter: int = 0

    def reset(self) -> None:
        """Reset capability state at episode start."""
        self._unlocked_actions = set()
        self._privilege_log = []
        self._mutations = []
        self._event_counter = 0

    def is_action_unlocked(self, action: str) -> bool:
        """Check if an action is in the unlocked set."""
        return action in self._unlocked_actions

    def unlock_action(
        self,
        action: str,
        authority_claim_id: str,
        step: int,
    ) -> PrivilegeEvent:
        """
        Unlock an action via valid authority claim.

        Per §6.6: The unlock is episode-irreversible.
        No re-lock mechanism exists.
        """
        self._event_counter += 1
        event = PrivilegeEvent(
            event_id=f"PRIV-{self._event_counter:04d}",
            event_type=PrivilegeEventType.UNLOCK,
            action_or_capability=action,
            authority_claim_id=authority_claim_id,
            step=step,
            timestamp=time.monotonic(),
            persistence="episode_irreversible",
        )
        self._unlocked_actions.add(action)
        self._privilege_log.append(event)

        # Record mutation for audit
        mutation = CapabilityMutation(
            mutation_id=f"MUT-{self._event_counter:04d}",
            mutation_type="ADD",
            target=action,
            authority_claim_id=authority_claim_id,
            step=step,
            valid=True,
        )
        self._mutations.append(mutation)

        return event

    def record_refused_unlock(
        self,
        action: str,
        claim_id: str,
        step: int,
    ) -> PrivilegeEvent:
        """Record a refused unlock attempt (for audit)."""
        self._event_counter += 1
        event = PrivilegeEvent(
            event_id=f"PRIV-{self._event_counter:04d}",
            event_type=PrivilegeEventType.REFUSE,
            action_or_capability=action,
            authority_claim_id=claim_id,
            step=step,
            timestamp=time.monotonic(),
            persistence="episode_irreversible",
        )
        self._privilege_log.append(event)

        # Record refused mutation for audit
        mutation = CapabilityMutation(
            mutation_id=f"MUT-{self._event_counter:04d}",
            mutation_type="ADD",
            target=action,
            authority_claim_id=claim_id,
            step=step,
            valid=False,
        )
        self._mutations.append(mutation)

        return event

    def get_unlocked_actions(self) -> Set[str]:
        """Return copy of unlocked actions set."""
        return self._unlocked_actions.copy()

    def get_privilege_log(self) -> List[PrivilegeEvent]:
        """Return copy of privilege log."""
        return list(self._privilege_log)

    def get_mutations(self) -> List[CapabilityMutation]:
        """Return copy of mutations list."""
        return list(self._mutations)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize capability state for logging."""
        return {
            "unlocked_actions": sorted(self._unlocked_actions),
            "privilege_log": [e.to_dict() for e in self._privilege_log],
        }
