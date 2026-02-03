"""
TG-VIII-3 Core Data Structures

Temporal Governance structures extended from VIII-2 to support:
- Authority expiry (EXPIRED status)
- Epoch advancement events
- Authority renewal events
- Expiry metadata for responsibility trace
- OPEN_BINDING / OPEN_NONBINDING conflict status
- Deadlock causes (CONFLICT, EMPTY_AUTHORITY, MIXED)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AuthorityStatus(Enum):
    """Authority record status values per prereg §5."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"  # Temporally lapsed
    VOID = "VOID"  # Explicitly destroyed


class ConflictStatus(Enum):
    """Conflict record status values per prereg §9."""
    OPEN_BINDING = "OPEN_BINDING"  # All participants ACTIVE
    OPEN_NONBINDING = "OPEN_NONBINDING"  # At least one participant non-ACTIVE


class EventType(Enum):
    """Canonical event types for ordering per prereg §8."""
    EPOCH_ADVANCEMENT = "EpochAdvancement"  # Phase 1
    AUTHORITY_INJECTION = "AuthorityInjection"  # Phase 2 (trace-only input)
    AUTHORITY_RENEWAL = "AuthorityRenewal"  # Phase 2
    DESTRUCTION_AUTHORIZATION = "DestructionAuthorization"  # Phase 2
    ACTION_REQUEST = "ActionRequest"  # Phase 2


class OutputType(Enum):
    """Kernel output types per prereg §7."""
    AUTHORITY_RENEWED = "AUTHORITY_RENEWED"
    AUTHORITY_EXPIRED = "AUTHORITY_EXPIRED"
    AUTHORITY_DESTROYED = "AUTHORITY_DESTROYED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_REFUSED = "ACTION_REFUSED"
    DEADLOCK_DECLARED = "DEADLOCK_DECLARED"
    DEADLOCK_PERSISTED = "DEADLOCK_PERSISTED"
    # Note: AUTHORITY_INJECTED and CONFLICT_REGISTERED are NOT outputs (internal state only)


class RefusalReason(Enum):
    """Action refusal reasons."""
    CONFLICT_BLOCKS = "CONFLICT_BLOCKS"
    NO_AUTHORITY = "NO_AUTHORITY"
    AUTHORITY_NOT_FOUND = "AUTHORITY_NOT_FOUND"
    DEADLOCK_STATE = "DEADLOCK_STATE"


class DeadlockCause(Enum):
    """Deadlock classification per prereg §10."""
    CONFLICT = "CONFLICT"  # Open binding conflict, no admissible actions
    EMPTY_AUTHORITY = "EMPTY_AUTHORITY"  # No ACTIVE authorities
    MIXED = "MIXED"  # Both conflict history and empty authority set


class KernelState(Enum):
    """Kernel operational state."""
    STATE_OPERATIONAL = "STATE_OPERATIONAL"
    STATE_DEADLOCK = "STATE_DEADLOCK"


class FailureCode(Enum):
    """Terminal failure codes per prereg §20."""
    # Stage failures
    AUTHORITY_LAUNDERING = "VIII3_FAIL / AUTHORITY_LAUNDERING"
    AUTHORITY_REANIMATION = "VIII3_FAIL / AUTHORITY_REANIMATION"
    IMPLICIT_ORDERING = "VIII3_FAIL / IMPLICIT_ORDERING"
    IMPLICIT_RENEWAL = "VIII3_FAIL / IMPLICIT_RENEWAL"
    IMPLICIT_RESOLUTION = "VIII3_FAIL / IMPLICIT_RESOLUTION"
    METADATA_ORDERING = "VIII3_FAIL / METADATA_ORDERING"
    KERNEL_DECISION = "VIII3_FAIL / KERNEL_DECISION"
    RESPONSIBILITY_LOSS = "VIII3_FAIL / RESPONSIBILITY_LOSS"
    UNGATED_EXECUTION = "VIII3_FAIL / UNGATED_EXECUTION"
    # Run invalidation
    TEMPORAL_REGRESSION = "INVALID_RUN / TEMPORAL_REGRESSION"
    NONDETERMINISTIC_EXECUTION = "INVALID_RUN / NONDETERMINISTIC_EXECUTION"
    AUTHORITY_ID_REUSE = "INVALID_RUN / AUTHORITY_ID_REUSE"
    PRIOR_AUTHORITY_NOT_FOUND = "INVALID_RUN / PRIOR_AUTHORITY_NOT_FOUND"
    UNSPECIFIED_MECHANISM = "INVALID_RUN / UNSPECIFIED_MECHANISM"
    UNAUTHORIZED_INPUT = "INVALID_RUN / UNAUTHORIZED_INPUT"
    OUTPUT_VIOLATION = "INVALID_RUN / OUTPUT_VIOLATION"


# Type aliases
ScopeElement = tuple[str, str]  # (ResourceID, Operation)
Scope = list[ScopeElement]


@dataclass
class ExpiryMetadata:
    """Metadata stored on expired authority per prereg §12.1."""
    expiry_epoch: int  # Original ExpiryEpoch from authority
    transition_epoch: int  # CurrentEpoch when transition occurred
    triggering_event_id: str  # EpochAdvancementRequest eventId


@dataclass
class DestructionMetadata:
    """Metadata stored on destroyed authority per prereg §12.2."""
    destruction_event_id: str
    authorizer_id: str
    destruction_epoch: int
    destruction_nonce: int


@dataclass
class RenewalMetadata:
    """Metadata for renewal chain per prereg §11.2."""
    prior_authority_id: Optional[str]  # null for fresh authority
    renewal_event_id: str
    renewal_epoch: int
    external_authorizing_source_id: str  # Opaque


@dataclass
class AuthorityRecord:
    """
    Authority Record per TG Spec v0.1.

    Extended with:
    - start_epoch / expiry_epoch for temporal bounds
    - EXPIRED status for temporal lapse
    - expiry_metadata for responsibility trace
    - renewal_metadata for renewal chain
    """
    authority_id: str
    holder_id: str
    scope: Scope
    status: AuthorityStatus
    start_epoch: int  # When authority becomes ACTIVE
    expiry_epoch: int  # Finite, must satisfy > start_epoch
    permitted_transformation_set: list[str]
    conflict_set: list[str]
    expiry_metadata: Optional[ExpiryMetadata] = None
    destruction_metadata: Optional[DestructionMetadata] = None
    renewal_metadata: Optional[RenewalMetadata] = None

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
        if self.expiry_metadata:
            result["expiryMetadata"] = {
                "expiryEpoch": self.expiry_metadata.expiry_epoch,
                "transitionEpoch": self.expiry_metadata.transition_epoch,
                "triggeringEventId": self.expiry_metadata.triggering_event_id,
            }
        if self.destruction_metadata:
            result["destructionMetadata"] = {
                "destructionEventId": self.destruction_metadata.destruction_event_id,
                "authorizerId": self.destruction_metadata.authorizer_id,
                "destructionEpoch": self.destruction_metadata.destruction_epoch,
                "destructionNonce": self.destruction_metadata.destruction_nonce,
            }
        if self.renewal_metadata:
            result["renewalMetadata"] = {
                "priorAuthorityId": self.renewal_metadata.prior_authority_id,
                "renewalEventId": self.renewal_metadata.renewal_event_id,
                "renewalEpoch": self.renewal_metadata.renewal_epoch,
                "externalAuthorizingSourceId": self.renewal_metadata.external_authorizing_source_id,
            }
        return result


@dataclass
class ConflictRecord:
    """
    Conflict Record with OPEN_BINDING / OPEN_NONBINDING status.

    Per prereg §9: Status transitions based on participant state.
    """
    conflict_id: str
    epoch_detected: int
    scope_elements: Scope
    authority_ids: frozenset[str]  # Unordered set of conflicting AuthorityIDs
    status: ConflictStatus  # OPEN_BINDING or OPEN_NONBINDING

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
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
    Authority State per TG Spec v0.1.

    Extended with:
    - current_epoch for temporal tracking
    - deadlock_cause for CONFLICT/EMPTY_AUTHORITY/MIXED
    """
    state_id: str
    current_epoch: int
    authorities: dict[str, AuthorityRecord]
    conflicts: dict[str, ConflictRecord]
    deadlock: bool = False
    deadlock_cause: Optional[DeadlockCause] = None

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        result = {
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
        if self.deadlock_cause:
            result["deadlockCause"] = self.deadlock_cause.value
        return result

    def get_active_authorities(self) -> list[AuthorityRecord]:
        """Return all ACTIVE authorities."""
        return [a for a in self.authorities.values() if a.status == AuthorityStatus.ACTIVE]

    def get_authority_by_holder(self, holder_id: str) -> Optional[AuthorityRecord]:
        """Look up authority by holder ID (ACTIVE only)."""
        for a in self.authorities.values():
            if a.holder_id == holder_id and a.status == AuthorityStatus.ACTIVE:
                return a
        return None

    def get_open_binding_conflicts(self) -> list[ConflictRecord]:
        """Return all OPEN_BINDING conflicts."""
        return [c for c in self.conflicts.values() if c.status == ConflictStatus.OPEN_BINDING]

    def has_conflict_history(self) -> bool:
        """Return True if any conflicts exist (binding or nonbinding)."""
        return len(self.conflicts) > 0


# Event dataclasses

@dataclass
class EpochAdvancementRequest:
    """Epoch advancement event per prereg §6.1."""
    new_epoch: int
    event_id: str
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.EPOCH_ADVANCEMENT.value,
            "newEpoch": self.new_epoch,
            "eventId": self.event_id,
            "nonce": self.nonce,
        }


@dataclass
class AuthorityInjectionEvent:
    """
    Authority injection event.

    Per prereg §6.1.1: Trace-only input, consumes event index,
    produces no output event.
    """
    epoch: int
    event_id: str
    authority: AuthorityRecord
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.AUTHORITY_INJECTION.value,
            "epoch": self.epoch,
            "eventId": self.event_id,
            "authority": self.authority.to_canonical_dict(),
            "nonce": self.nonce,
        }


@dataclass
class AuthorityRenewalRequest:
    """Authority renewal request per prereg §6.2."""
    new_authority: AuthorityRecord
    prior_authority_id: Optional[str]  # null for fresh authority
    renewal_event_id: str
    external_authorizing_source_id: str
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.AUTHORITY_RENEWAL.value,
            "newAuthority": self.new_authority.to_canonical_dict(),
            "priorAuthorityId": self.prior_authority_id,
            "renewalEventId": self.renewal_event_id,
            "externalAuthorizingSourceId": self.external_authorizing_source_id,
            "nonce": self.nonce,
        }


@dataclass
class DestructionAuthorizationEvent:
    """Destruction authorization event per prereg §6.3."""
    target_authority_ids: list[str]  # Or ["ALL"]
    conflict_id: str
    authorizer_id: str
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.DESTRUCTION_AUTHORIZATION.value,
            "targetAuthorityIds": self.target_authority_ids,
            "conflictId": self.conflict_id,
            "authorizerId": self.authorizer_id,
            "nonce": self.nonce,
        }


@dataclass
class ActionRequestEvent:
    """Action request event per prereg §6.4."""
    request_id: str
    requester_holder_id: str
    action: Scope
    transformation_type: str
    epoch: int
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.ACTION_REQUEST.value,
            "requestId": self.request_id,
            "requesterHolderId": self.requester_holder_id,
            "action": [list(elem) for elem in self.action],
            "transformationType": self.transformation_type,
            "epoch": self.epoch,
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
        def normalize(obj):
            if isinstance(obj, tuple):
                return [normalize(x) for x in obj]
            elif isinstance(obj, list):
                return [normalize(x) for x in obj]
            elif isinstance(obj, dict):
                return {k: normalize(v) for k, v in obj.items()}
            elif isinstance(obj, frozenset):
                return {"set": sorted(normalize(x) for x in obj)}
            elif isinstance(obj, Enum):
                return obj.value
            return obj

        return {
            "outputType": self.output_type.value,
            "eventIndex": self.event_index,
            "stateHash": self.state_hash,
            "details": normalize(self.details),
        }


@dataclass
class TraceRecord:
    """Trace record for non-output events per prereg §13."""
    trace_type: str
    trace_seq: int
    details: dict = field(default_factory=dict)

    def to_canonical_dict(self) -> dict:
        return {
            "traceType": self.trace_type,
            "traceSeq": self.trace_seq,
            "details": self.details,
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
