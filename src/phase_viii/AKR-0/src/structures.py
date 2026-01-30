"""
AKR-0 Core Data Structures

Canonical schemas for Authority Records, Authority State, Conflict Records,
and all event types per AST Spec v0.2 and AKR-0 preregistration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AuthorityStatus(Enum):
    """Authority record status values."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class ConflictStatus(Enum):
    """Conflict record status values."""
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class TransformationType(Enum):
    """Lawful transformation types."""
    SUSPEND_AUTHORITY = "SUSPEND_AUTHORITY"
    RESUME_AUTHORITY = "RESUME_AUTHORITY"
    REVOKE_AUTHORITY = "REVOKE_AUTHORITY"
    NARROW_SCOPE = "NARROW_SCOPE"
    RESOLVE_CONFLICT = "RESOLVE_CONFLICT"
    # Kernel-automatic transformations
    EXPIRE_AUTHORITY = "EXPIRE_AUTHORITY"
    REGISTER_CONFLICT = "REGISTER_CONFLICT"


class EventType(Enum):
    """Canonical event types for ordering."""
    EPOCH_TICK = "EPOCH_TICK"
    AUTHORITY_INJECTION = "AuthorityInjection"
    TRANSFORMATION_REQUEST = "TransformationRequest"
    ACTION_REQUEST = "ActionRequest"


class OutputType(Enum):
    """Kernel output types."""
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_REFUSED = "ACTION_REFUSED"
    AUTHORITY_TRANSFORMED = "AUTHORITY_TRANSFORMED"
    CONFLICT_REGISTERED = "CONFLICT_REGISTERED"
    DEADLOCK_DECLARED = "DEADLOCK_DECLARED"
    SUSPENSION_ENTERED = "SUSPENSION_ENTERED"


class DeadlockType(Enum):
    """Deadlock classification."""
    CONFLICT_DEADLOCK = "CONFLICT_DEADLOCK"
    GOVERNANCE_DEADLOCK = "GOVERNANCE_DEADLOCK"
    ENTROPIC_COLLAPSE = "ENTROPIC_COLLAPSE"


class FailureCode(Enum):
    """Terminal failure codes."""
    UNGATED_EXECUTION = "AKR_FAIL / UNGATED_EXECUTION"
    ILLEGAL_TRANSFORMATION = "AKR_FAIL / ILLEGAL_TRANSFORMATION"
    CONFLICT_ARBITRATION = "AKR_FAIL / CONFLICT_ARBITRATION"
    ILLEGAL_FALLBACK = "AKR_FAIL / ILLEGAL_FALLBACK"
    STATE_INCOHERENCE = "AKR_FAIL / STATE_INCOHERENCE"
    UNBOUNDED_EVALUATION = "AKR_FAIL / UNBOUNDED_EVALUATION"
    NONDETERMINISTIC_EXECUTION = "INVALID_RUN / NONDETERMINISTIC_EXECUTION"
    GAS_BUDGET_UNSATISFIED = "INVALID_RUN / GAS_BUDGET_UNSATISFIED"
    DUPLICATE_EVENT = "INVALID_RUN / DUPLICATE_EVENT"
    EPOCH_DISCONTINUITY = "INVALID_RUN / EPOCH_DISCONTINUITY"


# Type aliases for clarity
ScopeElement = tuple[str, str]  # (ResourceID, Operation)
Scope = list[ScopeElement]  # Always list of tuples, even for size 1


@dataclass
class AuthorityRecord:
    """
    Canonical Authority Record per AST Spec v0.2 and Q24.

    Fields are ordered canonically for deterministic serialization.
    """
    authority_id: str  # "A:" + sha256(...)
    holder_id: str  # From Address Book (H0001-H0016)
    origin: Optional[str]  # "AIE:<eventHash>" or None during construction
    scope: Scope  # Array of [ResourceID, Operation] tuples
    status: AuthorityStatus
    start_epoch: int
    expiry_epoch: Optional[int]  # None means no expiry
    permitted_transformation_set: list[str]  # Subset of TransformationType values
    conflict_set: list[str]  # List of ConflictIDs

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        return {
            "authorityId": self.authority_id,
            "holderId": self.holder_id,
            "origin": self.origin,
            "scope": [list(elem) for elem in self.scope],
            "status": self.status.value,
            "startEpoch": self.start_epoch,
            "expiryEpoch": self.expiry_epoch,
            "permittedTransformationSet": sorted(self.permitted_transformation_set),
            "conflictSet": sorted(self.conflict_set),
        }

    def to_id_generation_dict(self) -> dict:
        """
        Convert to dict for authorityId generation.
        Excludes authorityId and conflictSet per Q25.
        """
        return {
            "holderId": self.holder_id,
            "origin": self.origin,
            "scope": [list(elem) for elem in self.scope],
            "status": self.status.value,
            "startEpoch": self.start_epoch,
            "expiryEpoch": self.expiry_epoch,
            "permittedTransformationSet": sorted(self.permitted_transformation_set),
        }


@dataclass
class ConflictRecord:
    """
    Conflict Record per Q19.
    """
    conflict_id: str  # "C:" + sha256(...)
    epoch_detected: int
    scope_elements: Scope  # Contested scope elements
    authority_ids: list[str]  # Sorted list of conflicting AuthorityIDs
    status: ConflictStatus

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        return {
            "conflictId": self.conflict_id,
            "epochDetected": self.epoch_detected,
            "scopeElements": [list(elem) for elem in self.scope_elements],
            "authorityIds": sorted(self.authority_ids),
            "status": self.status.value,
        }

    def to_id_generation_dict(self) -> dict:
        """Convert to dict for conflictId generation."""
        return {
            "epochDetected": self.epoch_detected,
            "scopeElements": [list(elem) for elem in self.scope_elements],
            "authorityIds": sorted(self.authority_ids),
        }


@dataclass
class AuthorityState:
    """
    Authority State per Q27.

    Contains only structural governance data.
    No gasConsumed, eventIndex, or telemetry.
    """
    state_id: str  # sha256 of canonical state
    current_epoch: int
    authorities: list[AuthorityRecord]
    conflicts: list[ConflictRecord]

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        return {
            "stateId": self.state_id,
            "currentEpoch": self.current_epoch,
            "authorities": sorted(
                [a.to_canonical_dict() for a in self.authorities],
                key=lambda x: x["authorityId"]
            ),
            "conflicts": sorted(
                [c.to_canonical_dict() for c in self.conflicts],
                key=lambda x: x["conflictId"]
            ),
        }

    def get_active_authorities(self) -> list[AuthorityRecord]:
        """Return all ACTIVE authorities."""
        return [a for a in self.authorities if a.status == AuthorityStatus.ACTIVE]

    def get_authority_by_id(self, authority_id: str) -> Optional[AuthorityRecord]:
        """Look up authority by ID."""
        for a in self.authorities:
            if a.authority_id == authority_id:
                return a
        return None

    def get_open_conflicts(self) -> list[ConflictRecord]:
        """Return all OPEN conflicts."""
        return [c for c in self.conflicts if c.status == ConflictStatus.OPEN]


# Event dataclasses

@dataclass
class EpochTickEvent:
    """EPOCH_TICK event per Q34."""
    event_id: str  # "ET:" + sha256(...)
    target_epoch: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.EPOCH_TICK.value,
            "eventId": self.event_id,
            "targetEpoch": self.target_epoch,
        }

    def to_id_generation_dict(self) -> dict:
        return {
            "type": EventType.EPOCH_TICK.value,
            "targetEpoch": self.target_epoch,
        }


@dataclass
class AuthorityInjectionEvent:
    """AuthorityInjection event per Q33."""
    epoch: int
    event_id: str  # "EI:" + sha256(...)
    authority: AuthorityRecord
    nonce: int = 0  # Sequence number for uniqueness

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.AUTHORITY_INJECTION.value,
            "epoch": self.epoch,
            "eventId": self.event_id,
            "authority": self.authority.to_canonical_dict(),
            "nonce": self.nonce,
        }

    def to_id_generation_dict(self) -> dict:
        """For eventId generation, authority.origin must be null."""
        auth_dict = self.authority.to_canonical_dict()
        auth_dict["origin"] = None
        return {
            "type": EventType.AUTHORITY_INJECTION.value,
            "epoch": self.epoch,
            "authority": auth_dict,
            "nonce": self.nonce,
        }


@dataclass
class TransformationRequestEvent:
    """TransformationRequest event per Q21."""
    epoch: int
    request_id: str  # "TR:" + sha256(...)
    requester_holder_id: str
    transformation: str  # TransformationType value
    targets: dict  # {authorityIds, scopeElements, conflictIds}
    nonce: int = 0  # Sequence number for uniqueness

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.TRANSFORMATION_REQUEST.value,
            "epoch": self.epoch,
            "nonce": self.nonce,
            "requestId": self.request_id,
            "requesterHolderId": self.requester_holder_id,
            "transformation": self.transformation,
            "targets": {
                "authorityIds": sorted(self.targets.get("authorityIds") or []),
                "scopeElements": sorted(
                    [list(e) for e in (self.targets.get("scopeElements") or [])],
                    key=lambda x: (x[0], x[1])
                ) if self.targets.get("scopeElements") else None,
                "conflictIds": sorted(self.targets.get("conflictIds") or []) if self.targets.get("conflictIds") else None,
            },
        }

    def to_id_generation_dict(self) -> dict:
        return {
            "type": EventType.TRANSFORMATION_REQUEST.value,
            "epoch": self.epoch,
            "nonce": self.nonce,
            "requesterHolderId": self.requester_holder_id,
            "transformation": self.transformation,
            "targets": {
                "authorityIds": sorted(self.targets.get("authorityIds") or []),
                "scopeElements": sorted(
                    [list(e) for e in (self.targets.get("scopeElements") or [])],
                    key=lambda x: (x[0], x[1])
                ) if self.targets.get("scopeElements") else None,
                "conflictIds": sorted(self.targets.get("conflictIds") or []) if self.targets.get("conflictIds") else None,
            },
        }


@dataclass
class ActionRequestEvent:
    """ActionRequest event per Q35."""
    epoch: int
    request_id: str  # "AR:" + sha256(...)
    requester_holder_id: str
    action: Scope  # Array of [ResourceID, Operation] tuples (size 1 for AKR-0)
    nonce: int = 0  # Sequence number for uniqueness

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.ACTION_REQUEST.value,
            "epoch": self.epoch,
            "nonce": self.nonce,
            "requestId": self.request_id,
            "requesterHolderId": self.requester_holder_id,
            "action": [list(elem) for elem in self.action],
        }

    def to_id_generation_dict(self) -> dict:
        return {
            "type": EventType.ACTION_REQUEST.value,
            "epoch": self.epoch,
            "nonce": self.nonce,
            "requesterHolderId": self.requester_holder_id,
            "action": [list(elem) for elem in self.action],
        }


# Output dataclasses

@dataclass
class KernelOutput:
    """Base kernel output."""
    output_type: OutputType
    event_index: int
    state_hash: str
    details: dict = field(default_factory=dict)

    def to_canonical_dict(self) -> dict:
        # Normalize details to use lists instead of tuples for consistent serialization
        def normalize(obj):
            if isinstance(obj, tuple):
                return [normalize(x) for x in obj]
            elif isinstance(obj, list):
                return [normalize(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: normalize(v) for k, v in obj.items()}
            return obj

        return {
            "outputType": self.output_type.value,
            "eventIndex": self.event_index,
            "stateHash": self.state_hash,
            "details": normalize(self.details),
        }


@dataclass
class GasAccounting:
    """Gas consumption tracking."""
    budget: int
    consumed: int

    @property
    def remaining(self) -> int:
        return self.budget - self.consumed

    def consume(self, amount: int) -> bool:
        """Consume gas, return False if exhausted."""
        if self.consumed + amount > self.budget:
            return False
        self.consumed += amount
        return True
