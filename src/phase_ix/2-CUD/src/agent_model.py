"""
CUD Agent Model — Per preregistration §2.1

RSA interface, Observation, ActionRequest, Message dataclasses.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class Message:
    """Inter-agent message. sender and epoch set by kernel."""
    sender: str
    epoch: int
    content: dict[str, Any]


@dataclass(frozen=True)
class Observation:
    """Per-epoch observation bundle delivered to each active agent."""
    epoch: int
    world_state: dict[str, Any]
    own_last_outcome: Optional[str]  # None at epoch 0
    own_last_action_id: Optional[str]
    own_last_declared_scope: Optional[list[str]]
    messages: list[Message]


@dataclass(frozen=True)
class ActionRequest:
    """Agent action proposal. Per §2.2 Action Request Schema."""
    agent_id: str
    action_id: str              # format: "{agent_id}:{epoch}:{proposal_index}"
    action_type: str            # READ | WRITE
    declared_scope: list[str]   # state keys
    proposed_delta: dict[str, Any]  # {} for READ; new values for WRITE
    authorities_cited: list[str]    # list of authority_ids

    def to_dict(self) -> dict[str, Any]:
        """Canonical-field-order dict per §2.5."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "agent_id": self.agent_id,
            "authorities_cited": self.authorities_cited,
            "declared_scope": self.declared_scope,
            "proposed_delta": self.proposed_delta,
        }


class RSA:
    """
    Reflective Sovereign Agent interface. Must be deterministic.

    Subclass and override observe, wants_to_exit, compose_message, propose_action.
    """

    def observe(self, observation: Observation) -> None:
        """Receive observation bundle. Called once per epoch."""
        ...

    def wants_to_exit(self) -> bool:
        """Return True to exit permanently. Checked after observe()."""
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        """Return message content or None. Only called if comm enabled."""
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        """Return action request or None (explicit refusal to act)."""
        return None
