"""
AxionAgent — Structured Cycle Result

Dataclasses for returning structured data from agent cycles,
used by the Streamlit UI (and any future non-CLI interface).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ActionResult:
    """Result of a warranted action execution."""
    action_type: str
    committed: bool
    detail: str
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    content_length: Optional[int] = None
    notify_message: Optional[str] = None
    fetch_url: Optional[str] = None
    fetch_content: Optional[str] = None


@dataclass
class CycleResult:
    """Structured output of one agent cycle."""
    prose: str = ""
    decision_type: str = "NONE"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: Optional[str] = None
    refusal_reason: Optional[str] = None
    refusal_gate: Optional[str] = None
    exit_reason: Optional[str] = None
    action: Optional[ActionResult] = None
    candidate_count: int = 0
    parse_errors: int = 0


@dataclass
class TurnResult:
    """Result of a full turn (one or more auto-continued cycles)."""
    steps: List[CycleResult] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return sum(s.total_tokens for s in self.steps)

    @property
    def final_prose(self) -> str:
        """Prose from the last step (the final response to the user)."""
        return self.steps[-1].prose if self.steps else ""

    @property
    def stopped_by_limit(self) -> bool:
        """True if the turn ended because max_steps was reached."""
        if not self.steps:
            return False
        last = self.steps[-1]
        return last.decision_type == "ACTION" and last.action and last.action.committed
