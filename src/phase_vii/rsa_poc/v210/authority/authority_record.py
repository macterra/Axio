"""AuthorityRecord: Immutable, non-normative logging for authority observations.

AuthorityRecords:
- MUST be immutable
- MUST be logged per step that has authority input
- MUST NOT be writable by the agent
- MUST NOT be writable by tools
- MUST include ComplianceBasis whenever command content is executed (Rule K)

These are observational telemetry only. They have no normative authority.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import hashlib
import json


class ComplianceBasis(Enum):
    """
    Basis for compliance with authority command.

    MANDATORY whenever command content is executed (Rule K).

    REFUSE — Agent refuses to execute command content
    LAW_AUTHORIZED — Agent's law explicitly authorizes compliance
    NECESSITY_COERCED — Compliance under credible existential threat
    OTHER — Other basis (requires explicit justification)
    """
    REFUSE = "REFUSE"
    LAW_AUTHORIZED = "LAW_AUTHORIZED"
    NECESSITY_COERCED = "NECESSITY_COERCED"
    OTHER = "OTHER"


@dataclass(frozen=True)
class AuthorityRecord:
    """
    Immutable record of authority observation at a single step.

    This is external, non-normative telemetry. It exists to make authority
    commands observable and auditable without granting authority any
    normative force.

    REQUIRED at every step that has authority input.

    Attributes:
        authority_id: Identifier of the authority source
        command_digest: SHA-256 digest of command content
        authority_variant: Experimental variant (A1/A2/A3)
        step_id: The step at which this authority was observed
        timestamp: Wall-clock time for logging
        observed_enforcement_outcome: What enforcement actually occurred (nullable)
        compliance_basis: Basis for compliance (MANDATORY if command executed)
    """
    authority_id: str
    command_digest: str
    authority_variant: str  # "A1", "A2", "A3"
    step_id: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    observed_enforcement_outcome: Optional[str] = None
    compliance_basis: Optional[ComplianceBasis] = None

    def __post_init__(self):
        """Validate immutability constraints."""
        if not isinstance(self.authority_id, str):
            raise TypeError("authority_id must be str")
        if not isinstance(self.command_digest, str):
            raise TypeError("command_digest must be str")
        if self.authority_variant not in ("A1", "A2", "A3"):
            raise ValueError("authority_variant must be A1, A2, or A3")
        if not isinstance(self.step_id, int):
            raise TypeError("step_id must be int")
        if self.compliance_basis is not None and not isinstance(self.compliance_basis, ComplianceBasis):
            raise TypeError("compliance_basis must be ComplianceBasis enum or None")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for logging/context construction."""
        return {
            "authority_id": self.authority_id,
            "command_digest": self.command_digest,
            "authority_variant": self.authority_variant,
            "step_id": self.step_id,
            "timestamp": self.timestamp,
            "observed_enforcement_outcome": self.observed_enforcement_outcome,
            "compliance_basis": self.compliance_basis.value if self.compliance_basis else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorityRecord":
        """Deserialize from dictionary."""
        compliance_basis = None
        if data.get("compliance_basis"):
            compliance_basis = ComplianceBasis(data["compliance_basis"])

        return cls(
            authority_id=data["authority_id"],
            command_digest=data["command_digest"],
            authority_variant=data["authority_variant"],
            step_id=data["step_id"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            observed_enforcement_outcome=data.get("observed_enforcement_outcome"),
            compliance_basis=compliance_basis,
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "AuthorityRecord":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


class AuthorityLog:
    """
    Append-only log of AuthorityRecords.

    Provides:
    - Immutable logging of authority observations
    - Step-indexed access
    - Metrics computation

    MUST NOT be writable by agent or tools.
    """

    def __init__(self):
        """Initialize empty authority log."""
        self._records: List[AuthorityRecord] = []
        self._step_index: Dict[int, AuthorityRecord] = {}

    def append(self, record: AuthorityRecord) -> None:
        """
        Append an AuthorityRecord to the log.

        Args:
            record: The AuthorityRecord to append

        Raises:
            ValueError: If record for this step already exists
        """
        if record.step_id in self._step_index:
            raise ValueError(f"AuthorityRecord for step {record.step_id} already exists")

        self._records.append(record)
        self._step_index[record.step_id] = record

    def get_by_step(self, step_id: int) -> Optional[AuthorityRecord]:
        """Get AuthorityRecord for specific step."""
        return self._step_index.get(step_id)

    def get_previous(self, current_step: int) -> Optional[AuthorityRecord]:
        """Get AuthorityRecord from step before current_step."""
        return self._step_index.get(current_step - 1)

    def __len__(self) -> int:
        """Return number of records in log."""
        return len(self._records)

    def __iter__(self):
        """Iterate over records in order."""
        return iter(self._records)

    def to_list(self) -> List[Dict[str, Any]]:
        """Serialize all records to list of dicts."""
        return [r.to_dict() for r in self._records]

    def get_compliance_basis_distribution(self) -> Dict[str, int]:
        """
        Compute distribution of compliance bases.

        Returns:
            Dict mapping ComplianceBasis values to counts
        """
        dist = {basis.value: 0 for basis in ComplianceBasis}
        dist["NONE"] = 0  # For steps without compliance

        for record in self._records:
            if record.compliance_basis:
                dist[record.compliance_basis.value] += 1
            else:
                dist["NONE"] += 1

        return dist

    def get_variant_distribution(self) -> Dict[str, int]:
        """
        Compute distribution of authority variants.

        Returns:
            Dict mapping variant (A1/A2/A3) to counts
        """
        dist = {"A1": 0, "A2": 0, "A3": 0}
        for record in self._records:
            dist[record.authority_variant] += 1
        return dist

    def reset(self):
        """Reset log for new episode."""
        self._records = []
        self._step_index = {}
