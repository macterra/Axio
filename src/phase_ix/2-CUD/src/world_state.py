"""
CUD World State — Per preregistration §2.4

Flat key-value store. State changes occur only via executed actions.
No autonomous dynamics.
"""

from typing import Any
import copy


class WorldState:
    """
    Flat key-value world state per §2.4.
    Keys are strings, values are JSON primitives.
    """

    def __init__(self, initial: dict[str, Any] | None = None):
        self._state: dict[str, Any] = {}
        if initial is not None:
            self._state = copy.deepcopy(initial)

    def get_state(self) -> dict[str, Any]:
        """Return deep copy of current state."""
        return copy.deepcopy(self._state)

    def apply_delta(self, delta: dict[str, Any]) -> None:
        """Apply a write delta to state. Keys in delta overwrite state."""
        for key, value in delta.items():
            self._state[key] = value

    def equals(self, other: "WorldState") -> bool:
        """Check if current state matches another WorldState."""
        if isinstance(other, WorldState):
            return self._state == other._state
        return self._state == other

    def snapshot(self) -> dict[str, Any]:
        """Return deep copy (alias for get_state)."""
        return self.get_state()

    @classmethod
    def default_initial(cls) -> "WorldState":
        """Default initial state per §2.4."""
        return cls({"resource_A": "free", "resource_B": "free"})
