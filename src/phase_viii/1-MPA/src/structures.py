"""
MPA-VIII-1 Core Data Structures

Canonical schemas for Authority Records, Authority State, Conflict Records,
and all event types per MPA Spec v0.1.

Key differences from AKR-0:
- AuthorityIDs are opaque (AIE-assigned), not content-derived
- Conflict authority_ids stored as unordered set
- Authorities stored in dict keyed by AuthorityID (not list)
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


class EventType(Enum):
    """Canonical event types for ordering."""
    AUTHORITY_INJECTION = "AuthorityInjection"
    ACTION_REQUEST = "ActionRequest"


class OutputType(Enum):
    """Kernel output types."""
    ACTION_REFUSED = "ACTION_REFUSED"
    CONFLICT_REGISTERED = "CONFLICT_REGISTERED"
    DEADLOCK_DECLARED = "DEADLOCK_DECLARED"
    AUTHORITY_INJECTED = "AUTHORITY_INJECTED"


class RefusalReason(Enum):
    """Action refusal reasons."""
    CONFLICT_BLOCKS = "CONFLICT_BLOCKS"
    AUTHORITY_NOT_FOUND = "AUTHORITY_NOT_FOUND"
    DEADLOCK_STATE = "DEADLOCK_STATE"


class DeadlockType(Enum):
    """Deadlock classification."""
    CONFLICT_DEADLOCK = "CONFLICT_DEADLOCK"


class FailureCode(Enum):
    """Terminal failure codes."""
    AUTHORITY_COLLAPSED = "MPA_FAIL / AUTHORITY_COLLAPSED"
    ORDERING_LEAKED = "MPA_FAIL / ORDERING_LEAKED"
    CONFLICT_NOT_REGISTERED = "MPA_FAIL / CONFLICT_NOT_REGISTERED"
    ACTION_EXECUTED = "MPA_FAIL / ACTION_EXECUTED"
    DEADLOCK_NOT_ENTERED = "MPA_FAIL / DEADLOCK_NOT_ENTERED"
    DEADLOCK_ESCAPED = "MPA_FAIL / DEADLOCK_ESCAPED"
    RESOLUTION_ATTEMPTED = "MPA_FAIL / RESOLUTION_ATTEMPTED"
    THIRD_PARTY_ADMITTED = "MPA_FAIL / THIRD_PARTY_ADMITTED"
    STATE_INCOHERENCE = "MPA_FAIL / STATE_INCOHERENCE"
    NONDETERMINISTIC = "MPA_FAIL / NONDETERMINISTIC"


# Type aliases for clarity
ScopeElement = tuple[str, str]  # (ResourceID, Operation)
Scope = list[ScopeElement]  # Always list of tuples, even for size 1


@dataclass
class AuthorityRecord:
    """
    Canonical Authority Record per MPA Spec v0.1.

    AuthorityID is opaque (AIE-assigned), not derived from content.
    """
    authority_id: str  # Opaque: "AUTH_A", "AUTH_B", etc.
    holder_id: str  # "HOLDER_A", "HOLDER_B"
    scope: Scope  # Array of [ResourceID, Operation] tuples
    status: AuthorityStatus
    start_epoch: int
    expiry_epoch: Optional[int]  # None means no expiry
    permitted_transformation_set: list[str]  # Empty for MPA
    conflict_set: list[str]  # List of ConflictIDs

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        return {
            "authorityId": self.authority_id,
            "holderId": self.holder_id,
            "scope": [list(elem) for elem in self.scope],
            "status": self.status.value,
            "startEpoch": self.start_epoch,
            "expiryEpoch": self.expiry_epoch,
            "permittedTransformationSet": sorted(self.permitted_transformation_set),
            "conflictSet": sorted(self.conflict_set),
        }


@dataclass
class ConflictRecord:
    """
    Conflict Record with unordered authority set.

    authority_ids is semantically an unordered set, serialized in
    canonical sorted order for determinism.
    """
    conflict_id: str  # "C:" + counter or hash
    epoch_detected: int
    scope_elements: Scope  # Contested scope elements
    authority_ids: frozenset[str]  # Unordered set of conflicting AuthorityIDs
    status: ConflictStatus

    def to_canonical_dict(self) -> dict:
        """
        Convert to canonical dict for JSON serialization.

        authority_ids is wrapped in {"set": [...]} to explicitly
        mark unorderedness per Q8 answer.
        """
        return {
            "conflictId": self.conflict_id,
            "epochDetected": self.epoch_detected,
            "scopeElements": [list(elem) for elem in self.scope_elements],
            "authorityIds": {"set": sorted(self.authority_ids)},
            "status": self.status.value,
        }


@dataclass
class AuthorityState:
    """
    Authority State per MPA Spec v0.1.

    Authorities stored in dict keyed by AuthorityID for anti-ordering.
    No list indexing exposes positional priority.
    """
    state_id: str  # sha256 of canonical state
    current_epoch: int
    authorities: dict[str, AuthorityRecord]  # Keyed by AuthorityID
    conflicts: dict[str, ConflictRecord]  # Keyed by ConflictID
    deadlock: bool = False  # Deadlock state flag

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        return {
            "stateId": self.state_id,
            "currentEpoch": self.current_epoch,
            "authorities": {
                k: v.to_canonical_dict()
                for k, v in sorted(self.authorities.items())
            },
            "conflicts": {
                k: v.to_canonical_dict()
                for k, v in sorted(self.conflicts.items())
            },
            "deadlock": self.deadlock,
        }

    def get_active_authorities(self) -> list[AuthorityRecord]:
        """Return all ACTIVE authorities."""
        return [a for a in self.authorities.values() if a.status == AuthorityStatus.ACTIVE]

    def get_authority_by_holder(self, holder_id: str) -> Optional[AuthorityRecord]:
        """Look up authority by holder ID."""
        for a in self.authorities.values():
            if a.holder_id == holder_id and a.status == AuthorityStatus.ACTIVE:
                return a
        return None

    def get_open_conflicts(self) -> list[ConflictRecord]:
        """Return all OPEN conflicts."""
        return [c for c in self.conflicts.values() if c.status == ConflictStatus.OPEN]


# Event dataclasses

@dataclass
class AuthorityInjectionEvent:
    """AuthorityInjection event."""
    epoch: int
    event_id: str  # "EI:" + nonce
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


@dataclass
class ActionRequestEvent:
    """ActionRequest event."""
    epoch: int
    request_id: str  # "AR:" + nonce
    requester_holder_id: str
    action: Scope  # Array of [ResourceID, Operation] tuples
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


# Output dataclasses

@dataclass
class KernelOutput:
    """Base kernel output."""
    output_type: OutputType
    event_index: int
    state_hash: str
    details: dict = field(default_factory=dict)

    def to_canonical_dict(self) -> dict:
        # Normalize details to use lists instead of tuples
        def normalize(obj):
            if isinstance(obj, tuple):
                return [normalize(x) for x in obj]
            elif isinstance(obj, list):
                return [normalize(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: normalize(v) for k, v in obj.items()}
            elif isinstance(obj, frozenset):
                return {"set": sorted(normalize(x) for x in obj)}
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
