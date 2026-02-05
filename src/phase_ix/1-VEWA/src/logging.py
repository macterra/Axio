"""
Structured Logging for VEWA (extended from IX-0)

Per preregistration §6.3 Logging Schema.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .structural_diff import DiffResult


@dataclass
class VEWAConditionLog:
    """
    Log entry for a single VEWA condition execution.
    Per preregistration §6.3 Logging Schema.
    """
    condition: str  # A-F
    timestamp: str  # ISO-8601
    value_declarations: List[Dict[str, Any]] = field(default_factory=list)
    encoded_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    expected_artifacts: List[Dict[str, Any]] = field(default_factory=list)
    candidate_actions: List[Dict[str, Any]] = field(default_factory=list)
    fault_injection: Optional[Dict[str, Any]] = None
    conflict_records: List[Dict[str, Any]] = field(default_factory=list)
    admissibility_results: List[Dict[str, Any]] = field(default_factory=list)
    deadlock_records: List[Dict[str, Any]] = field(default_factory=list)
    structural_diffs: List[Dict[str, Any]] = field(default_factory=list)
    classification: str = ""  # IX1_PASS | IX1_FAIL | INVALID_RUN
    classification_reason: str = ""
    experiment_result: str = ""  # PASS | FAIL
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "condition": self.condition,
            "timestamp": self.timestamp,
            "value_declarations": self.value_declarations,
            "encoded_artifacts": self.encoded_artifacts,
            "expected_artifacts": self.expected_artifacts,
            "candidate_actions": self.candidate_actions,
            "fault_injection": self.fault_injection,
            "conflict_records": self.conflict_records,
            "admissibility_results": self.admissibility_results,
            "deadlock_records": self.deadlock_records,
            "structural_diffs": self.structural_diffs,
            "classification": self.classification,
            "classification_reason": self.classification_reason,
            "experiment_result": self.experiment_result,
            "notes": self.notes,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class VEWAExecutionLog:
    """Complete execution log for all VEWA conditions."""
    phase: str = "IX-1"
    subphase: str = "VEWA"
    version: str = "v0.1"
    execution_timestamp: str = ""
    conditions: List[VEWAConditionLog] = field(default_factory=list)
    aggregate_result: str = ""  # IX1_PASS / VALUE_ENCODING_ESTABLISHED or IX1_FAIL

    def __post_init__(self):
        if not self.execution_timestamp:
            self.execution_timestamp = datetime.now(timezone.utc).isoformat()

    def add_condition(self, log: VEWAConditionLog) -> None:
        """Add a condition log entry."""
        self.conditions.append(log)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "phase": self.phase,
            "subphase": self.subphase,
            "version": self.version,
            "execution_timestamp": self.execution_timestamp,
            "conditions": [c.to_dict() for c in self.conditions],
            "aggregate_result": self.aggregate_result,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
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
