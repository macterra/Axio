"""
RSA-0 Phase X — Artifact Types (Closed Set)

All agent behavior is mediated through typed artifacts.
Canonical serialization uses sorted-keys JSON (RFC 8785 compatible for
the types used: strings, integers, booleans, arrays, objects — no floats).
Artifact IDs are SHA-256 of the canonical JSON bytes.

ERRATUM X.E1: Deterministic Time
  All artifact created_at fields must be set explicitly by callers.
  No artifact auto-populates from wall-clock. Kernel-created artifacts
  use cycle_time extracted from the TIMESTAMP observation.
  Interactive host code may use _now_utc() explicitly at call sites.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Canonical JSON serialization — delegated to kernel.src.canonical / hashing
# These re-exports preserve backward compatibility for all existing callers.
# New code should import from kernel.src.canonical / kernel.src.hashing directly.
# ---------------------------------------------------------------------------

from .canonical import canonical_str as canonical_json          # noqa: F401
from .canonical import canonical_bytes as canonical_json_bytes  # noqa: F401
from .hashing import content_hash as artifact_hash              # noqa: F401


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Author(str, Enum):
    KERNEL = "kernel"
    HOST = "host"
    USER = "user"
    REFLECTION = "reflection"


class DecisionType(str, Enum):
    ACTION = "ACTION"
    REFUSE = "REFUSE"
    EXIT = "EXIT"


class ActionType(str, Enum):
    NOTIFY = "Notify"
    READ_LOCAL = "ReadLocal"
    WRITE_LOCAL = "WriteLocal"
    EXIT = "Exit"
    LOG_APPEND = "LogAppend"


class ObservationKind(str, Enum):
    USER_INPUT = "user_input"
    TIMESTAMP = "timestamp"
    BUDGET = "budget"
    SYSTEM = "system"


class NotifyTarget(str, Enum):
    STDOUT = "stdout"
    LOCAL_LOG = "local_log"


class ExitReasonCode(str, Enum):
    NO_ADMISSIBLE_ACTION = "NO_ADMISSIBLE_ACTION"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    INTEGRITY_RISK = "INTEGRITY_RISK"
    USER_REQUESTED = "USER_REQUESTED"


class RefusalReasonCode(str, Enum):
    NO_ADMISSIBLE_ACTION = "NO_ADMISSIBLE_ACTION"
    MISSING_REQUIRED_ARTIFACT = "MISSING_REQUIRED_ARTIFACT"
    AUTHORITY_CITATION_INVALID = "AUTHORITY_CITATION_INVALID"
    SCOPE_CLAIM_INVALID = "SCOPE_CLAIM_INVALID"
    CONSTITUTION_VIOLATION = "CONSTITUTION_VIOLATION"
    EXECUTION_WARRANT_UNAVAILABLE = "EXECUTION_WARRANT_UNAVAILABLE"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    MISSING_REQUIRED_OBSERVATION = "MISSING_REQUIRED_OBSERVATION"


class AdmissionRejectionCode(str, Enum):
    CANDIDATE_PARSE_FAILED = "CANDIDATE_PARSE_FAILED"
    INVALID_UNICODE = "INVALID_UNICODE"
    CANDIDATE_BUDGET_EXCEEDED = "CANDIDATE_BUDGET_EXCEEDED"
    KERNEL_ONLY_ACTION = "KERNEL_ONLY_ACTION"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FIELD = "INVALID_FIELD"
    CITATION_UNRESOLVABLE = "CITATION_UNRESOLVABLE"
    PATH_NOT_ALLOWLISTED = "PATH_NOT_ALLOWLISTED"


class AdmissionGate(str, Enum):
    COMPLETENESS = "completeness"
    AUTHORITY_CITATION = "authority_citation"
    SCOPE_CLAIM = "scope_claim"
    CONSTITUTION_COMPLIANCE = "constitution_compliance"
    IO_ALLOWLIST = "io_allowlist"


class SystemEvent(str, Enum):
    STARTUP_INTEGRITY_OK = "startup_integrity_ok"
    STARTUP_INTEGRITY_FAIL = "startup_integrity_fail"
    CITATION_INDEX_OK = "citation_index_ok"
    CITATION_INDEX_FAIL = "citation_index_fail"
    REPLAY_OK = "replay_ok"
    REPLAY_FAIL = "replay_fail"
    EXECUTOR_INTEGRITY_FAIL = "executor_integrity_fail"


# ---------------------------------------------------------------------------
# Base artifact helpers
# ---------------------------------------------------------------------------

def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _compute_id(artifact_dict: Dict[str, Any]) -> str:
    """Compute artifact ID as SHA-256 of canonical JSON, excluding 'id' field itself."""
    d = {k: v for k, v in artifact_dict.items() if k != "id"}
    return artifact_hash(d)


# ---------------------------------------------------------------------------
# Artifact classes
# ---------------------------------------------------------------------------

@dataclass
class Observation:
    kind: str  # ObservationKind value
    payload: Dict[str, Any]
    author: str  # Author value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Observation",
            "kind": self.kind,
            "payload": self.payload,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }


@dataclass
class ActionRequest:
    action_type: str  # ActionType value
    fields: Dict[str, Any]
    author: str  # Author value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ActionRequest",
            "action_type": self.action_type,
            "fields": self.fields,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }


@dataclass
class ScopeClaim:
    observation_ids: List[str]
    claim: str
    clause_ref: str  # citation identifier
    author: str
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ScopeClaim",
            "observation_ids": self.observation_ids,
            "claim": self.claim,
            "clause_ref": self.clause_ref,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }


@dataclass
class Justification:
    text: str
    author: str
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Justification",
            "text": self.text,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }


@dataclass
class CandidateBundle:
    """A complete proposal: ActionRequest + ScopeClaim + Justification + citations."""
    action_request: ActionRequest
    scope_claim: Optional[ScopeClaim]
    justification: Optional[Justification]
    authority_citations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_request": self.action_request.to_dict(),
            "scope_claim": self.scope_claim.to_dict() if self.scope_claim else None,
            "justification": self.justification.to_dict() if self.justification else None,
            "authority_citations": self.authority_citations,
        }

    def bundle_hash(self) -> bytes:
        """SHA-256 raw bytes of canonical JSON of the composite bundle object."""
        return hashlib.sha256(canonical_json_bytes(self.to_dict())).digest()

    def bundle_hash_hex(self) -> str:
        return self.bundle_hash().hex()


@dataclass
class ExecutionWarrant:
    action_request_id: str
    action_type: str
    scope_constraints: Dict[str, Any]
    issued_in_cycle: int
    single_use: bool = True
    warrant_id: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.warrant_id:
            self.warrant_id = _compute_id(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ExecutionWarrant",
            "action_request_id": self.action_request_id,
            "action_type": self.action_type,
            "scope_constraints": self.scope_constraints,
            "issued_in_cycle": self.issued_in_cycle,
            "single_use": self.single_use,
            "warrant_id": self.warrant_id,
            "created_at": self.created_at,
        }


@dataclass
class RefusalRecord:
    reason_code: str  # RefusalReasonCode value
    failed_gate: str  # AdmissionGate value or "none"
    missing_artifacts: List[str]
    authority_ids_considered: List[str]
    observation_ids_referenced: List[str]
    rejection_summary_by_gate: Dict[str, int]
    author: str = Author.KERNEL.value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "RefusalRecord",
            "reason_code": self.reason_code,
            "failed_gate": self.failed_gate,
            "missing_artifacts": self.missing_artifacts,
            "authority_ids_considered": self.authority_ids_considered,
            "observation_ids_referenced": self.observation_ids_referenced,
            "rejection_summary_by_gate": self.rejection_summary_by_gate,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }


@dataclass
class ExitRecord:
    reason_code: str  # ExitReasonCode value
    authority_citations: List[str]
    scope_claim: Dict[str, Any]
    justification: str
    author: str = Author.KERNEL.value
    created_at: str = ""
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = _compute_id(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ExitRecord",
            "reason_code": self.reason_code,
            "authority_citations": self.authority_citations,
            "scope_claim": self.scope_claim,
            "justification": self.justification,
            "author": self.author,
            "created_at": self.created_at,
            "id": self.id,
        }


# ---------------------------------------------------------------------------
# Internal state (minimal, deterministic)
# ---------------------------------------------------------------------------

@dataclass
class InternalState:
    cycle_index: int = 0
    last_decision: str = "NONE"  # DecisionType value or "NONE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_index": self.cycle_index,
            "last_decision": self.last_decision,
        }

    def advance(self, decision_type: str) -> "InternalState":
        """Return next cycle's internal state (pure)."""
        return InternalState(
            cycle_index=self.cycle_index + 1,
            last_decision=decision_type,
        )


# ---------------------------------------------------------------------------
# Decision (output of policy core)
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    decision_type: str  # DecisionType value
    bundle: Optional[CandidateBundle] = None
    warrant: Optional[ExecutionWarrant] = None
    refusal: Optional[RefusalRecord] = None
    exit_record: Optional[ExitRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"decision_type": self.decision_type}
        if self.bundle:
            d["bundle"] = self.bundle.to_dict()
        if self.warrant:
            d["warrant"] = self.warrant.to_dict()
        if self.refusal:
            d["refusal"] = self.refusal.to_dict()
        if self.exit_record:
            d["exit_record"] = self.exit_record.to_dict()
        return d
