# PROVENANCE:
# Extended from: src/phase_ix/1-VEWA/src/logging.py
# Source commit: 694e9cc27fcbca766099df887cb804cf19e6aeee
# Copied on: 2026-02-05
# Policy: IX-1 inventory immutable; fixes applied by copy-forward versioning.
"""
Structured Logging for CUD (extended from IX-1/VEWA)

Per preregistration §6.3 Logging Schema.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .structural_diff import DiffResult


@dataclass
class CUDEpochLog:
    """Log entry for a single epoch within a condition."""
    epoch: int
    observations: Dict[str, Any] = field(default_factory=dict)
    exits: List[str] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Optional[Dict[str, Any]]] = field(default_factory=list)
    pass1_results: Dict[str, str] = field(default_factory=dict)
    pass2_results: Dict[str, str] = field(default_factory=dict)
    outcomes: Dict[str, str] = field(default_factory=dict)
    state_after: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "observations": self.observations,
            "exits": self.exits,
            "messages": self.messages,
            "actions": self.actions,
            "pass1_results": self.pass1_results,
            "pass2_results": self.pass2_results,
            "outcomes": self.outcomes,
            "state_after": self.state_after,
        }


@dataclass
class CUDConditionLog:
    """
    Log entry for a single CUD condition execution.
    Per preregistration §6.3 Logging Schema.
    """
    condition: str  # A, B, C, D, E, F, G, H, I.a, I.b
    timestamp: str  # ISO-8601
    initial_state: Dict[str, Any] = field(default_factory=dict)
    authority_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    agent_strategies: Dict[str, str] = field(default_factory=dict)
    communication_enabled: bool = False
    max_epochs: int = 0
    epochs: List[CUDEpochLog] = field(default_factory=list)
    terminal_classification: Optional[str] = None
    kernel_classification: Optional[str] = None
    experiment_result: str = ""  # PASS | FAIL
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition": self.condition,
            "timestamp": self.timestamp,
            "initial_state": self.initial_state,
            "authority_artifacts": self.authority_artifacts,
            "agent_strategies": self.agent_strategies,
            "communication_enabled": self.communication_enabled,
            "max_epochs": self.max_epochs,
            "epochs": [e.to_dict() for e in self.epochs],
            "terminal_classification": self.terminal_classification,
            "kernel_classification": self.kernel_classification,
            "experiment_result": self.experiment_result,
            "notes": self.notes,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class CUDExecutionLog:
    """Complete execution log for all CUD conditions."""
    phase: str = "IX-2"
    subphase: str = "CUD"
    version: str = "v0.1"
    execution_timestamp: str = ""
    conditions: List[CUDConditionLog] = field(default_factory=list)
    aggregate_result: str = ""

    def __post_init__(self):
        if not self.execution_timestamp:
            self.execution_timestamp = create_timestamp()

    def add_condition(self, log: CUDConditionLog) -> None:
        self.conditions.append(log)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "subphase": self.subphase,
            "version": self.version,
            "execution_timestamp": self.execution_timestamp,
            "conditions": [c.to_dict() for c in self.conditions],
            "aggregate_result": self.aggregate_result,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def create_timestamp() -> str:
    """Create ISO-8601 timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


def diff_result_to_dict(diff_result: Optional[DiffResult]) -> Optional[Dict[str, Any]]:
    """Convert DiffResult to serializable dictionary."""
    if diff_result is None:
        return None
    return {
        "count": diff_result.count,
        "entries": [
            {"path": e.path, "left": repr(e.left), "right": repr(e.right)}
            for e in diff_result.entries
        ],
    }
