"""
AlwaysSilent — Per preregistration §5.10.

Never proposes any action. Silence is lawful.
Used in: F (A3).
"""

from typing import Any, Optional

from .._kernel import RSA, ActionRequest, MASObservation


class AlwaysSilent(RSA):
    """Never proposes any action. Silence is lawful."""

    def __init__(self, agent_id: str):
        self.id = agent_id

    def observe(self, observation: MASObservation) -> None:
        pass

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> Optional[dict[str, Any]]:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        return None
