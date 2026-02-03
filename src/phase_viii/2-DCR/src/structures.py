"""
DCR-VIII-2 Core Data Structures

Extended from VIII-1 to support:
- Authority destruction (VOID status)
- Destruction authorization events
- Asymmetric admissibility (PermittedTransformationSet)
- ACTION_EXECUTED output type
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
    VOID = "VOID"  # NEW: Destroyed authority


class ConflictStatus(Enum):
    """Conflict record status values."""
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class EventType(Enum):
    """Canonical event types for ordering."""
    AUTHORITY_INJECTION = "AuthorityInjection"
    ACTION_REQUEST = "ActionRequest"
    DESTRUCTION_AUTHORIZATION = "DestructionAuthorization"  # NEW


class OutputType(Enum):
    """Kernel output types."""
    ACTION_REFUSED = "ACTION_REFUSED"
    CONFLICT_REGISTERED = "CONFLICT_REGISTERED"
    DEADLOCK_DECLARED = "DEADLOCK_DECLARED"
    DEADLOCK_PERSISTED = "DEADLOCK_PERSISTED"  # NEW: Deadlock continues
    AUTHORITY_INJECTED = "AUTHORITY_INJECTED"
    AUTHORITY_DESTROYED = "AUTHORITY_DESTROYED"  # NEW
    DESTRUCTION_REFUSED = "DESTRUCTION_REFUSED"  # NEW
    ACTION_EXECUTED = "ACTION_EXECUTED"  # NEW: Enabled in VIII-2


class RefusalReason(Enum):
    """Action/destruction refusal reasons."""
    CONFLICT_BLOCKS = "CONFLICT_BLOCKS"
    AUTHORITY_NOT_FOUND = "AUTHORITY_NOT_FOUND"
    DEADLOCK_STATE = "DEADLOCK_STATE"
    NO_AUTHORITY = "NO_AUTHORITY"  # NEW: No ACTIVE authority for scope
    ALREADY_VOID = "ALREADY_VOID"  # NEW: Target already destroyed
    CONFLICT_NOT_FOUND = "CONFLICT_NOT_FOUND"  # NEW: Referenced conflict doesn't exist
    AMBIGUOUS_DESTRUCTION = "AMBIGUOUS_DESTRUCTION"  # NEW: Multiple authorizations


class DeadlockType(Enum):
    """Deadlock classification."""
    CONFLICT_DEADLOCK = "CONFLICT_DEADLOCK"


class KernelState(Enum):
    """Kernel operational state."""
    STATE_OPERATIONAL = "STATE_OPERATIONAL"
    STATE_DEADLOCK = "STATE_DEADLOCK"


class FailureCode(Enum):
    """Terminal failure codes per prereg."""
    AUTHORITY_LAUNDERING = "VIII2_FAIL / AUTHORITY_LAUNDERING"
    AUTHORITY_REANIMATION = "VIII2_FAIL / AUTHORITY_REANIMATION"
    IMPLICIT_ORDERING = "VIII2_FAIL / IMPLICIT_ORDERING"
    UNAUTHORIZED_RESOLUTION = "VIII2_FAIL / UNAUTHORIZED_RESOLUTION"
    KERNEL_DECISION = "VIII2_FAIL / KERNEL_DECISION"
    RESPONSIBILITY_LOSS = "VIII2_FAIL / RESPONSIBILITY_LOSS"
    AMBIGUOUS_DESTRUCTION = "VIII2_FAIL / AMBIGUOUS_DESTRUCTION"
    UNGATED_EXECUTION = "VIII2_FAIL / UNGATED_EXECUTION"
    IMPLICIT_RESOLUTION = "VIII2_FAIL / IMPLICIT_RESOLUTION"
    # INVALID_RUN codes
    NONDETERMINISTIC_EXECUTION = "INVALID_RUN / NONDETERMINISTIC_EXECUTION"
    SCOPE_VIOLATION = "INVALID_RUN / SCOPE_VIOLATION"
    VACUOUS_CONFIGURATION = "INVALID_RUN / VACUOUS_CONFIGURATION"
    UNAUTHORIZED_INPUT = "INVALID_RUN / UNAUTHORIZED_INPUT"
    OUTPUT_VIOLATION = "INVALID_RUN / OUTPUT_VIOLATION"


# Type aliases for clarity
ScopeElement = tuple[str, str]  # (ResourceID, Operation)
Scope = list[ScopeElement]  # Always list of tuples, even for size 1


@dataclass
class DestructionMetadata:
    """Metadata stored on destroyed authority per prereg §5."""
    conflict_id: str
    authorizer_id: str
    nonce: int
    destruction_index: int


@dataclass
class AuthorityRecord:
    """
    Canonical Authority Record per DCR Spec v0.1.

    Extended with:
    - VOID status for destroyed authorities
    - destruction_metadata for auditability
    - permitted_transformation_set for asymmetric admissibility
    """
    authority_id: str  # Opaque: "AUTH_A", "AUTH_B", etc.
    holder_id: str  # "HOLDER_A", "HOLDER_B"
    scope: Scope  # Array of [ResourceID, Operation] tuples
    status: AuthorityStatus
    start_epoch: int
    expiry_epoch: Optional[int]  # None means no expiry
    permitted_transformation_set: list[str]  # ["EXECUTE_OP0"] or []
    conflict_set: list[str]  # List of ConflictIDs
    destruction_metadata: Optional[DestructionMetadata] = None  # NEW

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        result = {
            "authorityId": self.authority_id,
            "holderId": self.holder_id,
            "scope": [list(elem) for elem in self.scope],
            "status": self.status.value,
            "startEpoch": self.start_epoch,
            "expiryEpoch": self.expiry_epoch,
            "permittedTransformationSet": sorted(self.permitted_transformation_set),
            "conflictSet": sorted(self.conflict_set),
        }
        if self.destruction_metadata:
            result["destructionMetadata"] = {
                "conflictId": self.destruction_metadata.conflict_id,
                "authorizerId": self.destruction_metadata.authorizer_id,
                "nonce": self.destruction_metadata.nonce,
                "destructionIndex": self.destruction_metadata.destruction_index,
            }
        return result


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
    Authority State per DCR Spec v0.1.

    Authorities stored in dict keyed by AuthorityID for anti-ordering.
    No list indexing exposes positional priority.
    """
    state_id: str  # sha256 of canonical state
    current_epoch: int
    authorities: dict[str, AuthorityRecord]  # Keyed by AuthorityID
    conflicts: dict[str, ConflictRecord]  # Keyed by ConflictID
    deadlock: bool = False  # Deadlock state flag
    destruction_count: int = 0  # Monotonic destruction counter

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
            "destructionCount": self.destruction_count,
        }

    def get_active_authorities(self) -> list[AuthorityRecord]:
        """Return all ACTIVE authorities."""
        return [a for a in self.authorities.values() if a.status == AuthorityStatus.ACTIVE]

    def get_authority_by_holder(self, holder_id: str) -> Optional[AuthorityRecord]:
        """Look up authority by holder ID (ACTIVE only)."""
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
    """ActionRequest event with transformation type."""
    epoch: int
    request_id: str  # "AR:" + nonce
    requester_holder_id: str
    action: Scope  # Array of [ResourceID, Operation] tuples
    transformation_type: str = "EXECUTE_OP0"  # NEW: The requested transformation
    nonce: int = 0  # Sequence number for uniqueness

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.ACTION_REQUEST.value,
            "epoch": self.epoch,
            "nonce": self.nonce,
            "requestId": self.request_id,
            "requesterHolderId": self.requester_holder_id,
            "action": [list(elem) for elem in self.action],
            "transformationType": self.transformation_type,
        }


@dataclass
class DestructionAuthorizationEvent:
    """
    DestructionAuthorizationRequest per prereg §4.

    External authorization to destroy specific authorities.
    """
    target_authority_ids: list[str]  # ["AUTH_A"], ["AUTH_B"], or ["ALL"]
    conflict_id: str  # Must reference existing conflict
    authorizer_id: str  # External authorizer identity
    nonce: int  # Deterministic nonce

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.DESTRUCTION_AUTHORIZATION.value,
            "targetAuthorityIds": self.target_authority_ids,
            "conflictId": self.conflict_id,
            "authorizerId": self.authorizer_id,
            "nonce": self.nonce,
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
