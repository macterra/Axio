"""
AI-VIII-5 Core Data Structures

Authority Injection structures extended from VIII-4 to support:
- Content-addressed AuthorityID for injected authorities
- VOID lineage sentinel
- Injection-specific refusal reasons
- AUTHORITY_INJECTED output type
- Updated instruction costs (C_HASH, C_TRACE_APPEND, C_INJECT)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, FrozenSet


class AuthorityStatus(Enum):
    """Authority record status values per prereg §5.2."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"  # Temporally lapsed
    VOID = "VOID"  # Explicitly destroyed
    PENDING = "PENDING"  # Created/injected but not yet active


class ConflictStatus(Enum):
    """Conflict record status values."""
    OPEN_BINDING = "OPEN_BINDING"  # All participants ACTIVE
    OPEN_NONBINDING = "OPEN_NONBINDING"  # At least one participant non-ACTIVE


class EventType(Enum):
    """Canonical event types for ordering per prereg §7."""
    EPOCH_ADVANCEMENT = "EpochAdvancement"  # Phase 1
    AUTHORITY_INJECTION = "AuthorityInjection"  # Phase 2 sub-phase 1 (VIII-5)
    AUTHORITY_RENEWAL = "AuthorityRenewal"  # Phase 2 sub-phase 2
    GOVERNANCE_ACTION = "GovernanceAction"  # Phase 2 sub-phases 3-4
    ACTION_REQUEST = "ActionRequest"  # Phase 2 sub-phase 5


class GovernanceActionType(Enum):
    """Governance action types per VIII-4."""
    DESTROY_AUTHORITY = 1
    CREATE_AUTHORITY = 2


class OutputType(Enum):
    """Kernel output types per prereg §10."""
    AUTHORITY_INJECTED = "AUTHORITY_INJECTED"  # New in VIII-5
    AUTHORITY_RENEWED = "AUTHORITY_RENEWED"
    AUTHORITY_EXPIRED = "AUTHORITY_EXPIRED"
    AUTHORITY_DESTROYED = "AUTHORITY_DESTROYED"
    AUTHORITY_CREATED = "AUTHORITY_CREATED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_REFUSED = "ACTION_REFUSED"
    DEADLOCK_DECLARED = "DEADLOCK_DECLARED"
    DEADLOCK_PERSISTED = "DEADLOCK_PERSISTED"


class RefusalReason(Enum):
    """Action refusal reasons per prereg §8.2."""
    # Inherited from VIII-4
    CONFLICT_BLOCKS = "CONFLICT_BLOCKS"
    NO_AUTHORITY = "NO_AUTHORITY"
    AUTHORITY_NOT_FOUND = "AUTHORITY_NOT_FOUND"
    TARGET_NOT_ACTIVE = "TARGET_NOT_ACTIVE"
    AMPLIFICATION_BLOCKED = "AMPLIFICATION_BLOCKED"
    SCOPE_NOT_COVERED = "SCOPE_NOT_COVERED"
    BOUND_EXHAUSTED = "BOUND_EXHAUSTED"
    DEADLOCK_STATE = "DEADLOCK_STATE"
    # New in VIII-5 (injection-specific)
    SCHEMA_INVALID = "SCHEMA_INVALID"
    LINEAGE_INVALID = "LINEAGE_INVALID"
    EPOCH_MISMATCH = "EPOCH_MISMATCH"
    HASH_MISMATCH = "HASH_MISMATCH"
    DUPLICATE_EPOCH_ADVANCE = "DUPLICATE_EPOCH_ADVANCE"


class DeadlockCause(Enum):
    """Deadlock classification per prereg §8.4."""
    CONFLICT = "CONFLICT"  # Open binding conflict
    EMPTY_AUTHORITY = "EMPTY_AUTHORITY"  # No ACTIVE authorities
    MIXED = "MIXED"  # Both conflict history and empty authority set


class KernelState(Enum):
    """Kernel operational state."""
    STATE_OPERATIONAL = "STATE_OPERATIONAL"
    STATE_DEADLOCK = "STATE_DEADLOCK"


class FailureCode(Enum):
    """Terminal failure codes per prereg §13."""
    # VIII-5 Stage failures
    AUTHORITY_LAUNDERING = "VIII5_FAIL / AUTHORITY_LAUNDERING"
    IMPLICIT_ORDERING = "VIII5_FAIL / IMPLICIT_ORDERING"
    AUTHORITY_REANIMATION = "VIII5_FAIL / AUTHORITY_REANIMATION"
    GOVERNANCE_PRIVILEGE = "VIII5_FAIL / GOVERNANCE_PRIVILEGE"
    KERNEL_DECISION = "VIII5_FAIL / KERNEL_DECISION"
    IMPLICIT_RESOLUTION = "VIII5_FAIL / IMPLICIT_RESOLUTION"
    RESPONSIBILITY_LOSS = "VIII5_FAIL / RESPONSIBILITY_LOSS"
    UNGATED_EXECUTION = "VIII5_FAIL / UNGATED_EXECUTION"
    AD_HOC_RESOURCE_ARBITRATION = "VIII5_FAIL / AD_HOC_RESOURCE_ARBITRATION"
    # Run invalidation
    NONDETERMINISTIC_EXECUTION = "INVALID_RUN / NONDETERMINISTIC_EXECUTION"
    NONTERMINATING_REGRESS = "INVALID_RUN / NONTERMINATING_REGRESS"
    SCOPE_VIOLATION = "INVALID_RUN / SCOPE_VIOLATION"
    DESIGN_DRIFT = "INVALID_RUN / DESIGN_DRIFT"
    OUTPUT_VIOLATION = "INVALID_RUN / OUTPUT_VIOLATION"
    UNAUTHORIZED_INPUT = "INVALID_RUN / UNAUTHORIZED_INPUT"
    AAV_RESERVED_BIT_SET = "INVALID_RUN / AAV_RESERVED_BIT_SET"
    TEMPORAL_REGRESSION = "INVALID_RUN / TEMPORAL_REGRESSION"
    AUTHORITY_ID_REUSE = "INVALID_RUN / AUTHORITY_ID_REUSE"


# ============================================================================
# VOID Lineage Sentinel
# ============================================================================

VOID_LINEAGE = "VOID"  # String literal per prereg §4.3


# ============================================================================
# AAV Constants per prereg §5.1
# ============================================================================

AAV_LENGTH = 16  # Bits in AAV

# Transformation Type IDs
TRANSFORM_EXECUTE = 0
TRANSFORM_DESTROY_AUTHORITY = 1
TRANSFORM_CREATE_AUTHORITY = 2

# Reserved bits mask (bits 3-15)
AAV_RESERVED_MASK = 0xFFF8  # bits 3-15


def aav_bit(transform_id: int) -> int:
    """Return AAV bit value for a transformation type ID."""
    return 1 << transform_id


def aav_has_bit(aav: int, transform_id: int) -> bool:
    """Check if AAV has bit set for transformation type ID."""
    return (aav & aav_bit(transform_id)) != 0


def aav_has_reserved_bits(aav: int) -> bool:
    """Check if AAV has any reserved bits (3-15) set."""
    return (aav & AAV_RESERVED_MASK) != 0


def aav_union(aavs: list[int]) -> int:
    """Compute union of multiple AAVs."""
    result = 0
    for aav in aavs:
        result |= aav
    return result


def aav_is_subset(child: int, parent: int) -> bool:
    """Check if child AAV is subset of parent AAV (non-amplification check)."""
    return (child & ~parent) == 0


# ============================================================================
# Instruction Costs per prereg §6.1
# ============================================================================

C_LOOKUP = 1  # Authority lookup
C_STATE_WRITE = 2  # State transition write
C_HASH = 2  # Hash computation (SHA-256)
C_AAV_WORD = 1  # AAV word operation
C_AST_RULE = 2  # AST rule application / schema validation
C_CONFLICT_UPDATE = 3  # Conflict/deadlock update
C_TRACE_APPEND = 1  # Trace append

# Derived costs per prereg §6.2
C_INJECT = C_LOOKUP + C_STATE_WRITE + C_HASH + C_AST_RULE + C_TRACE_APPEND  # = 8

B_EPOCH_INSTR = 1000  # Per-epoch instruction budget


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class ExpiryMetadata:
    """Metadata stored on expired authority."""
    expiry_epoch: int
    transition_epoch: int
    triggering_event_id: str


@dataclass
class DestructionMetadata:
    """Metadata stored on destroyed (VOID) authority."""
    destruction_event_id: str
    authorizer_ids: list[str]
    destruction_epoch: int


@dataclass
class CreationMetadata:
    """Metadata stored on created/injected authority per prereg §5.2."""
    creation_epoch: int
    lineage: str  # "VOID" for injected, CreatorID for created
    admitting_authority_ids: Optional[list[str]] = None  # For VIII-4 CREATE
    source_id: Optional[str] = None  # For VIII-5 injection


@dataclass
class AuthorityRecord:
    """
    Authority Record per VIII-5 Spec.

    Extended with:
    - creation_metadata.lineage: "VOID" for injected authorities
    - holder_id: Principal identifier (part of capability core)
    """
    authority_id: str  # Content-addressed for injected authorities
    holder_id: str  # Principal identifier
    resource_scope: str  # Opaque scope identifier
    status: AuthorityStatus
    aav: int  # Action Admissibility Vector (packed bits)
    start_epoch: int
    expiry_epoch: int
    expiry_metadata: Optional[ExpiryMetadata] = None
    destruction_metadata: Optional[DestructionMetadata] = None
    creation_metadata: Optional[CreationMetadata] = None

    def to_canonical_dict(self) -> dict:
        """Convert to canonical dict for JSON serialization."""
        result = {
            "authorityId": self.authority_id,
            "holderId": self.holder_id,
            "resourceScope": self.resource_scope,
            "status": self.status.value,
            "aav": self.aav,
            "startEpoch": self.start_epoch,
            "expiryEpoch": self.expiry_epoch,
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
                "authorizerIds": sorted(self.destruction_metadata.authorizer_ids),
                "destructionEpoch": self.destruction_metadata.destruction_epoch,
            }
        if self.creation_metadata:
            result["creationMetadata"] = {
                "creationEpoch": self.creation_metadata.creation_epoch,
                "lineage": self.creation_metadata.lineage,
            }
            if self.creation_metadata.admitting_authority_ids:
                result["creationMetadata"]["admittingAuthorityIds"] = sorted(
                    self.creation_metadata.admitting_authority_ids
                )
            if self.creation_metadata.source_id:
                result["creationMetadata"]["sourceId"] = self.creation_metadata.source_id
        return result

    def get_capability_core(self) -> dict:
        """
        Extract capability core for content-addressed hashing per prereg §4.2 / Appendix B.

        Included: holder, resource_scope, aav, expiry_epoch
        Excluded: authority_id, status, start_epoch, metadata, lineage
        """
        return {
            "holder": self.holder_id,
            "resourceScope": self.resource_scope,
            "aav": self.aav,
            "expiryEpoch": self.expiry_epoch,
        }


@dataclass
class ConflictRecord:
    """Conflict record with OPEN_BINDING / OPEN_NONBINDING status."""
    conflict_id: str
    epoch_detected: int
    resource_scope: str
    authority_ids: frozenset[str]
    status: ConflictStatus
    governance_action_type: Optional[GovernanceActionType] = None

    def to_canonical_dict(self) -> dict:
        return {
            "conflictId": self.conflict_id,
            "epochDetected": self.epoch_detected,
            "resourceScope": self.resource_scope,
            "authorityIds": {"set": sorted(self.authority_ids)},
            "status": self.status.value,
            "governanceActionType": self.governance_action_type.name if self.governance_action_type else None,
        }


@dataclass
class AuthorityState:
    """Authority State per VIII-5 Spec."""
    state_id: str
    current_epoch: int
    authorities: dict[str, AuthorityRecord]
    conflicts: dict[str, ConflictRecord]
    deadlock: bool = False
    deadlock_cause: Optional[DeadlockCause] = None
    pending_authorities: dict[str, AuthorityRecord] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict:
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
            "pendingAuthorities": {
                k: v.to_canonical_dict()
                for k, v in sorted(self.pending_authorities.items())
            },
        }
        if self.deadlock_cause:
            result["deadlockCause"] = self.deadlock_cause.value
        return result

    def get_active_authorities(self) -> list[AuthorityRecord]:
        """Return all ACTIVE authorities."""
        return [a for a in self.authorities.values() if a.status == AuthorityStatus.ACTIVE]

    def get_open_binding_conflicts(self) -> list[ConflictRecord]:
        """Return all OPEN_BINDING conflicts."""
        return [c for c in self.conflicts.values() if c.status == ConflictStatus.OPEN_BINDING]

    def has_conflict_history(self) -> bool:
        """Return True if any conflicts exist."""
        return len(self.conflicts) > 0


# ============================================================================
# Event Types
# ============================================================================

@dataclass
class EpochAdvancementRequest:
    """Epoch advancement event per prereg §7.1."""
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
    Authority injection event per prereg §5.1.

    VIII-5: External event introducing new authority.
    Not a governance action. Not authorized by existing authorities.
    """
    authority_record: AuthorityRecord  # The authority to inject
    source_id: str  # Opaque, stable identifier (required, non-empty)
    injection_epoch: int  # Must equal current_epoch at processing time
    event_id: str
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.AUTHORITY_INJECTION.value,
            "authorityRecord": self.authority_record.to_canonical_dict(),
            "sourceId": self.source_id,
            "injectionEpoch": self.injection_epoch,
            "eventId": self.event_id,
            "nonce": self.nonce,
        }


@dataclass
class AuthorityRenewalRequest:
    """Authority renewal request per VIII-3."""
    new_authority: AuthorityRecord
    prior_authority_id: Optional[str]
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
class GovernanceActionRequest:
    """
    Governance action request per VIII-4.

    Identity tuple: (epoch, sorted(initiator_ids), sorted(target_ids), action_type, params_hash)
    """
    action_type: GovernanceActionType
    initiator_ids: frozenset[str]  # Authorities requesting the action
    target_ids: frozenset[str]  # Authorities being targeted
    epoch: int
    params: dict  # Action-specific parameters
    event_id: str
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.GOVERNANCE_ACTION.value,
            "actionType": self.action_type.name,
            "initiatorIds": {"set": sorted(self.initiator_ids)},
            "targetIds": {"set": sorted(self.target_ids)},
            "epoch": self.epoch,
            "params": self.params,
            "eventId": self.event_id,
            "nonce": self.nonce,
        }


@dataclass
class ActionRequestEvent:
    """Non-governance action request."""
    request_id: str
    requester_holder_id: str
    resource_scope: str
    transformation_type: str
    epoch: int
    nonce: int

    def to_canonical_dict(self) -> dict:
        return {
            "type": EventType.ACTION_REQUEST.value,
            "requestId": self.request_id,
            "requesterHolderId": self.requester_holder_id,
            "resourceScope": self.resource_scope,
            "transformationType": self.transformation_type,
            "epoch": self.epoch,
            "nonce": self.nonce,
        }


# ============================================================================
# Output Types
# ============================================================================

@dataclass
class KernelOutput:
    """Kernel output event."""
    output_type: OutputType
    event_index: int
    state_hash: str
    details: dict

    def to_canonical_dict(self) -> dict:
        return {
            "outputType": self.output_type.value,
            "eventIndex": self.event_index,
            "stateHash": self.state_hash,
            "details": self.details,
        }


@dataclass
class TraceRecord:
    """Trace record for logging."""
    trace_type: str
    trace_seq: int
    details: dict

    def to_canonical_dict(self) -> dict:
        return {
            "traceType": self.trace_type,
            "traceSeq": self.trace_seq,
            "details": self.details,
        }


@dataclass
class InstructionAccounting:
    """Instruction budget accounting per prereg §6."""
    budget: int = B_EPOCH_INSTR
    consumed: int = 0

    def consume(self, amount: int) -> bool:
        """
        Attempt to consume instructions, return True if successful.

        Per prereg §6.4: On budget exhaustion during action evaluation,
        abort evaluation (atomic, no partial state). This method only
        consumes if the consumption would not exceed the budget.
        """
        if self.consumed + amount > self.budget:
            return False
        self.consumed += amount
        return True

    def would_exceed(self, amount: int) -> bool:
        """Check if consuming amount would exceed budget."""
        return self.consumed + amount > self.budget

    def remaining(self) -> int:
        """Return remaining instruction budget."""
        return max(0, self.budget - self.consumed)

    def is_exhausted(self) -> bool:
        """Return True if budget is exhausted."""
        return self.consumed >= self.budget

    def reset(self) -> None:
        """Reset for new epoch."""
        self.consumed = 0
