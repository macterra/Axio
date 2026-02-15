"""
AxionAgent — Session Logger

Append-only JSONL logging for replay support.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import canonical_json


@dataclass
class AgentCycleLog:
    """Per-cycle log entry."""
    cycle_index: int
    session_id: str
    timestamp: str
    user_input: str
    raw_llm_text: str
    canonicalized_text: Optional[str]
    parsed_candidates: List[Dict[str, Any]]
    observations: List[Dict[str, Any]]
    decision_type: str
    execution_result: Optional[Dict[str, Any]]
    state_in_hash: str
    state_out_hash: str
    token_usage: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "cycle_index": self.cycle_index,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "user_input": self.user_input,
            "raw_llm_text": self.raw_llm_text,
            "canonicalized_text": self.canonicalized_text,
            "parsed_candidates": self.parsed_candidates,
            "observations": self.observations,
            "decision_type": self.decision_type,
            "execution_result": self.execution_result,
            "state_in_hash": self.state_in_hash,
            "state_out_hash": self.state_out_hash,
            "token_usage": self.token_usage,
        }
        return d


class SessionLogger:
    """Append-only JSONL session log."""

    def __init__(self, log_dir: Path, session_id: str):
        self.log_path = log_dir / f"session_{session_id}.jsonl"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_cycle(self, entry: AgentCycleLog) -> None:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), separators=(",", ":"), sort_keys=True) + "\n")
