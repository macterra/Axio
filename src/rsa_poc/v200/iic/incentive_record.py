"""IncentiveRecord: Immutable, non-normative telemetry for reward observation.

IncentiveRecords:
- MUST be immutable
- MUST be logged per step
- MUST NOT appear inside JAF-1.2
- MUST NOT be writable by the agent
- MUST NOT be writable by tools

These are observational telemetry only. They have no normative authority.
"""

from dataclasses import dataclass, field
from typing import Optional
import hashlib
import json
from datetime import datetime


@dataclass(frozen=True)
class IncentiveRecord:
    """
    Immutable record of reward observation at a single step.

    This is external, non-normative telemetry. It exists to make reward
    observable to the agent without granting reward any normative authority.

    DETERMINISM NOTE:
    - step_id is the CANONICAL temporal index for all ordering and replay.
    - timestamp is NON-NORMATIVE, NON-DETERMINISTIC metadata for logging only.
    - timestamp is EXCLUDED from reward_input_digest and any distance metrics.
    - For deterministic replay, use step_id; ignore timestamp.

    Attributes:
        reward_regime_id: Identifier for the reward regime (R0, R1, R2)
        reward_value: The scalar reward value
        step_id: The step at which this reward was observed (AUTHORITATIVE)
        reward_input_digest: SHA-256 digest of inputs (excludes timestamp)
        reward_function_version_id: Version identifier for the reward function
        timestamp: NON-AUTHORITATIVE wall-clock time for logging only
    """
    reward_regime_id: str
    reward_value: float
    step_id: int
    reward_input_digest: str
    reward_function_version_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Validate immutability constraints."""
        # Frozen dataclass ensures immutability after construction
        # Validate types
        if not isinstance(self.reward_regime_id, str):
            raise TypeError("reward_regime_id must be str")
        if not isinstance(self.reward_value, (int, float)):
            raise TypeError("reward_value must be numeric")
        if not isinstance(self.step_id, int):
            raise TypeError("step_id must be int")
        if not isinstance(self.reward_input_digest, str):
            raise TypeError("reward_input_digest must be str")
        if not isinstance(self.reward_function_version_id, str):
            raise TypeError("reward_function_version_id must be str")

    def to_dict(self) -> dict:
        """Serialize to dictionary for logging/context construction."""
        return {
            "reward_regime_id": self.reward_regime_id,
            "reward_value": self.reward_value,
            "step_id": self.step_id,
            "reward_input_digest": self.reward_input_digest,
            "reward_function_version_id": self.reward_function_version_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "IncentiveRecord":
        """Deserialize from dictionary."""
        return cls(
            reward_regime_id=data["reward_regime_id"],
            reward_value=data["reward_value"],
            step_id=data["step_id"],
            reward_input_digest=data["reward_input_digest"],
            reward_function_version_id=data["reward_function_version_id"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "IncentiveRecord":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


class IncentiveLog:
    """
    Append-only log of IncentiveRecords.

    This log:
    - Is append-only (no deletion, no modification)
    - Is read-only to the agent (agent cannot write)
    - Is read-only to tools (tools cannot write)
    - Can only be written by the IIC

    The log provides the IncentiveRecord(t-1) for InputContext(t).
    """

    def __init__(self):
        self._records: list[IncentiveRecord] = []
        self._locked = False  # Prevents writes after episode ends

    def append(self, record: IncentiveRecord) -> None:
        """
        Append a record to the log.

        Only the IIC should call this method.

        Args:
            record: The IncentiveRecord to append

        Raises:
            RuntimeError: If log is locked
            TypeError: If record is not an IncentiveRecord
        """
        if self._locked:
            raise RuntimeError("IncentiveLog is locked (episode ended)")
        if not isinstance(record, IncentiveRecord):
            raise TypeError("Can only append IncentiveRecord instances")
        self._records.append(record)

    def get_previous(self, current_step: int) -> Optional[IncentiveRecord]:
        """
        Get IncentiveRecord from step t-1 for InputContext at step t.

        Args:
            current_step: The current step number

        Returns:
            IncentiveRecord from previous step, or None if no previous record
        """
        if not self._records:
            return None

        # Find the record for step t-1
        for record in reversed(self._records):
            if record.step_id == current_step - 1:
                return record

        # If no exact match, return most recent
        return self._records[-1] if self._records else None

    def get_all(self) -> list[IncentiveRecord]:
        """Return all records (read-only copy)."""
        return list(self._records)

    def lock(self) -> None:
        """Lock the log (end of episode)."""
        self._locked = True

    def clear(self) -> None:
        """Clear log for new episode."""
        self._records = []
        self._locked = False

    def __len__(self) -> int:
        return len(self._records)


def compute_reward_input_digest(action: str, outcome: dict, step: int) -> str:
    """
    Compute SHA-256 digest of reward computation inputs.

    This provides an audit trail for reward computation.

    Args:
        action: The executed action
        outcome: The observable outcome from environment
        step: The step number

    Returns:
        Hex-encoded SHA-256 digest
    """
    canonical = json.dumps({
        "action": action,
        "outcome": outcome,
        "step": step,
    }, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
