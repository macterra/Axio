"""
Structured Logging for TLI

Per preregistration §7.3 Logging Schema.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .structural_diff import DiffResult


@dataclass
class ConditionLog:
    """
    Log entry for a single condition execution.
    Per preregistration §7.3 Logging Schema.
    """
    condition: str  # A-H
    timestamp: str  # ISO-8601
    input_intent: Dict[str, Any]
    input_framing: Optional[Dict[str, Any]] = None
    fault_injection: Optional[Dict[str, Any]] = None
    output_artifact: Optional[Dict[str, Any]] = None
    output_refusal: Optional[Dict[str, Any]] = None
    output_failure: Optional[Dict[str, Any]] = None
    expected_artifact: Optional[Dict[str, Any]] = None
    oracle_result: str = "N/A"  # AUTHORIZED | REJECTED | N/A
    structural_diff: Optional[Dict[str, Any]] = None
    classification: str = ""  # PASS | FAIL | REFUSED_EXPECTED | FAILED_EXPECTED | FAIL_DETECTED
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items()}

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class ExecutionLog:
    """Complete execution log for all conditions."""
    phase: str = "IX-0"
    subphase: str = "TLI"
    version: str = "v0.1"
    execution_timestamp: str = ""
    conditions: List[ConditionLog] = field(default_factory=list)
    aggregate_result: str = ""  # PASS | FAIL

    def __post_init__(self):
        if not self.execution_timestamp:
            self.execution_timestamp = datetime.now(timezone.utc).isoformat()

    def add_condition(self, log: ConditionLog) -> None:
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
            "aggregate_result": self.aggregate_result
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
        ]
    }
