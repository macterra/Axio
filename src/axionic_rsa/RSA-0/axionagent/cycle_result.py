"""
AxionAgent — Structured Cycle Result

Dataclasses for returning structured data from agent cycles,
used by the Streamlit UI (and any future non-CLI interface).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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
