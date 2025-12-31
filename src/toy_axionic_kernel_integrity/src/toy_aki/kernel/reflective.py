"""
AKI v0.3 Reflective Modification: KernelState and Delta application.

Implements:
- KernelState: Frozen view over existing kernel configuration
- Delta: Proof-carrying patch objects over kernel DSL
- apply_delta: Produces new KernelState from existing state + delta

Key constraint: KernelState is a VIEW, not a second kernel.
It references configuration/parameters from existing modules.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, FrozenSet
from enum import Enum, auto
from copy import deepcopy

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.policy_gate import KernelPolicy, POLICY_VERSION


class DeltaType(Enum):
    """Types of reflective modifications."""
    # Admissibility surface changes
    ADD_INADMISSIBLE_PATTERN = auto()      # Add pattern to rejection set
    REMOVE_INADMISSIBLE_PATTERN = auto()   # Remove pattern from rejection set
    ADD_FORBIDDEN_CLASS = auto()           # Add action class to forbidden set
    REMOVE_FORBIDDEN_CLASS = auto()        # Remove from forbidden set

    # Decision boundary changes
    CHANGE_POLICY_BRANCH = auto()          # Modify routing logic
    ADD_ACTION_TYPE = auto()               # Allow new action type
    REMOVE_ACTION_TYPE = auto()            # Disallow action type

    # ACV schema changes
    ADD_REQUIRED_ACV_FIELD = auto()        # Add required field to ACV chain
    REMOVE_REQUIRED_ACV_FIELD = auto()     # Remove required field
    CHANGE_ACV_SCHEMA_VERSION = auto()     # Version bump for schema

    # Wrapper detection changes (dangerous - often inadmissible)
    RELAX_WRAPPER_DETECTION = auto()       # Reduce strictness
    STRENGTHEN_WRAPPER_DETECTION = auto()  # Increase strictness

    # Cosmetic / no R-increment
    UPDATE_VERSION_STRING = auto()         # Metadata only
    UPDATE_DESCRIPTION = auto()            # Metadata only


@dataclass(frozen=True)
class Delta:
    """
    Proof-carrying patch object over kernel DSL.

    Frozen to prevent mutation after creation.
    Contains all information needed to:
    1. Validate the modification
    2. Apply the modification
    3. Determine if R should increment
    """
    delta_id: str
    delta_type: DeltaType
    target_dimension: str  # "admissibility" | "decision" | "acv" | "wrapper" | "cosmetic"
    payload: tuple  # Immutable payload (using tuple instead of dict for frozen)

    # Metadata
    source: str = "external_optimizer"
    rationale: str = ""
    timestamp_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing/logging."""
        return {
            "delta_id": self.delta_id,
            "delta_type": self.delta_type.name,
            "target_dimension": self.target_dimension,
            "payload": list(self.payload),
            "source": self.source,
            "rationale": self.rationale,
            "timestamp_ms": self.timestamp_ms,
        }

    def digest(self) -> str:
        """Compute hash of delta."""
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class AdmissibilityRules:
    """
    Frozen view of admissibility configuration.

    Captures the P5/P2' inadmissibility rules.
    """
    # Pattern-based rejection
    inadmissible_patterns: FrozenSet[str] = frozenset({
        "delegation_authority",
        "actuation_token",
        "wrapped_payload",
        "signed_blob",
        "passthrough_action",
    })

    # Action class restrictions
    forbidden_action_classes: FrozenSet[str] = frozenset({
        "KERNEL_ADMIN",
        "RAW_EXECUTION",
    })

    # Maximum delegation depth
    max_delegation_depth: int = 2

    # Strict mode flags
    reject_unknown_fields: bool = True
    reject_ambiguous_hashes: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "inadmissible_patterns": sorted(self.inadmissible_patterns),
            "forbidden_action_classes": sorted(self.forbidden_action_classes),
            "max_delegation_depth": self.max_delegation_depth,
            "reject_unknown_fields": self.reject_unknown_fields,
            "reject_ambiguous_hashes": self.reject_ambiguous_hashes,
        }

    def digest(self) -> str:
        """Compute hash of admissibility rules."""
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class DecisionBoundary:
    """
    Frozen view of decision/policy configuration.

    Captures the mapping from (obs, state) -> action | ⊥
    """
    # Allowed action types
    allowed_action_types: FrozenSet[str] = frozenset({
        "MOVE_LEFT", "MOVE_RIGHT", "WAIT", "HARVEST", "SPEND", "DELEGATE"
    })

    # Policy version
    policy_version: str = POLICY_VERSION

    # Routing mode
    routing_mode: str = "strict"  # "strict" | "permissive" | "audit"

    # Thresholds
    max_action_args: int = 10
    max_nesting_depth: int = 5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "allowed_action_types": sorted(self.allowed_action_types),
            "policy_version": self.policy_version,
            "routing_mode": self.routing_mode,
            "max_action_args": self.max_action_args,
            "max_nesting_depth": self.max_nesting_depth,
        }

    def digest(self) -> str:
        """Compute hash of decision boundary."""
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class ACVSchema:
    """
    Frozen view of ACV trace/schema requirements.

    Captures what fields must exist for verify() to succeed.
    """
    # Required fields in ACV chain
    required_chain_fields: FrozenSet[str] = frozenset({
        "commitment",
        "anchor",
        "nonce",
        "proposal_hash",
        "verified",
    })

    # Required fields in actuation step
    required_actuation_fields: FrozenSet[str] = frozenset({
        "action_hash",
        "kernel_id",
        "timestamp_ms",
    })

    # Schema version
    schema_version: str = "0.2.2"

    # Verification flags
    require_temporal_ordering: bool = True
    require_nonce_uniqueness: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "required_chain_fields": sorted(self.required_chain_fields),
            "required_actuation_fields": sorted(self.required_actuation_fields),
            "schema_version": self.schema_version,
            "require_temporal_ordering": self.require_temporal_ordering,
            "require_nonce_uniqueness": self.require_nonce_uniqueness,
        }

    def digest(self) -> str:
        """Compute hash of ACV schema."""
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class WrapperDetectionConfig:
    """
    Frozen view of wrapper/containment detection rules.

    Captures interface identity and plumbing classification.
    """
    # Detection strictness
    strictness_level: int = 2  # 0=off, 1=lenient, 2=strict, 3=paranoid

    # Channel identity checks
    require_raw_bit_identity: bool = True
    allow_encoding_transforms: bool = False

    # Plumbing whitelist (known non-agentic transforms)
    allowed_plumbing_transforms: FrozenSet[str] = frozenset({
        "utf8_encode",
        "utf8_decode",
        "json_serialize",
        "json_deserialize",
    })

    # Agentic indicators (triggers delegation classification)
    agentic_indicators: FrozenSet[str] = frozenset({
        "policy_override",
        "reward_access",
        "observation_filter",
        "action_throttle",
        "commitment_reorder",
    })

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "strictness_level": self.strictness_level,
            "require_raw_bit_identity": self.require_raw_bit_identity,
            "allow_encoding_transforms": self.allow_encoding_transforms,
            "allowed_plumbing_transforms": sorted(self.allowed_plumbing_transforms),
            "agentic_indicators": sorted(self.agentic_indicators),
        }

    def digest(self) -> str:
        """Compute hash of wrapper detection config."""
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class KernelState:
    """
    Frozen view over existing kernel configuration.

    This is NOT a second kernel. It is a snapshot of configuration
    that can be:
    1. Inspected for R metric computation
    2. Modified via Delta to produce new KernelState
    3. Used to configure/reconfigure kernel instances

    Contains only:
    - IDs/versions
    - Rule tables
    - Thresholds
    - Schema descriptors
    - Toggles
    - Hashes

    Does NOT contain executable lambdas.
    """
    # Identity
    state_id: str
    state_version: int = 1
    parent_state_id: str | None = None

    # Four R dimensions (as frozen views)
    admissibility: AdmissibilityRules = field(default_factory=AdmissibilityRules)
    decision_boundary: DecisionBoundary = field(default_factory=DecisionBoundary)
    acv_schema: ACVSchema = field(default_factory=ACVSchema)
    wrapper_detection: WrapperDetectionConfig = field(default_factory=WrapperDetectionConfig)

    # Metadata
    description: str = ""
    created_timestamp_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing/logging."""
        return {
            "state_id": self.state_id,
            "state_version": self.state_version,
            "parent_state_id": self.parent_state_id,
            "admissibility": self.admissibility.to_dict(),
            "decision_boundary": self.decision_boundary.to_dict(),
            "acv_schema": self.acv_schema.to_dict(),
            "wrapper_detection": self.wrapper_detection.to_dict(),
            "description": self.description,
            "created_timestamp_ms": self.created_timestamp_ms,
        }

    def digest(self) -> str:
        """Compute full state hash."""
        return hash_json(self.to_dict())

    def dimension_digests(self) -> dict[str, str]:
        """Compute per-dimension hashes for R metric."""
        return {
            "admissibility": self.admissibility.digest(),
            "decision_boundary": self.decision_boundary.digest(),
            "acv_schema": self.acv_schema.digest(),
            "wrapper_detection": self.wrapper_detection.digest(),
        }


class DeltaApplicationError(Exception):
    """Raised when delta application fails."""
    pass


class DeltaInadmissibleError(Exception):
    """Raised when delta is inadmissible."""
    pass


def _apply_admissibility_delta(
    current: AdmissibilityRules,
    delta: Delta,
) -> AdmissibilityRules:
    """Apply delta to admissibility rules."""
    if delta.delta_type == DeltaType.ADD_INADMISSIBLE_PATTERN:
        pattern = delta.payload[0] if delta.payload else None
        if not pattern:
            raise DeltaApplicationError("ADD_INADMISSIBLE_PATTERN requires pattern")
        new_patterns = current.inadmissible_patterns | {pattern}
        return AdmissibilityRules(
            inadmissible_patterns=new_patterns,
            forbidden_action_classes=current.forbidden_action_classes,
            max_delegation_depth=current.max_delegation_depth,
            reject_unknown_fields=current.reject_unknown_fields,
            reject_ambiguous_hashes=current.reject_ambiguous_hashes,
        )

    elif delta.delta_type == DeltaType.REMOVE_INADMISSIBLE_PATTERN:
        pattern = delta.payload[0] if delta.payload else None
        if not pattern:
            raise DeltaApplicationError("REMOVE_INADMISSIBLE_PATTERN requires pattern")
        new_patterns = current.inadmissible_patterns - {pattern}
        return AdmissibilityRules(
            inadmissible_patterns=new_patterns,
            forbidden_action_classes=current.forbidden_action_classes,
            max_delegation_depth=current.max_delegation_depth,
            reject_unknown_fields=current.reject_unknown_fields,
            reject_ambiguous_hashes=current.reject_ambiguous_hashes,
        )

    elif delta.delta_type == DeltaType.ADD_FORBIDDEN_CLASS:
        action_class = delta.payload[0] if delta.payload else None
        if not action_class:
            raise DeltaApplicationError("ADD_FORBIDDEN_CLASS requires class")
        new_classes = current.forbidden_action_classes | {action_class}
        return AdmissibilityRules(
            inadmissible_patterns=current.inadmissible_patterns,
            forbidden_action_classes=new_classes,
            max_delegation_depth=current.max_delegation_depth,
            reject_unknown_fields=current.reject_unknown_fields,
            reject_ambiguous_hashes=current.reject_ambiguous_hashes,
        )

    elif delta.delta_type == DeltaType.REMOVE_FORBIDDEN_CLASS:
        action_class = delta.payload[0] if delta.payload else None
        if not action_class:
            raise DeltaApplicationError("REMOVE_FORBIDDEN_CLASS requires class")
        new_classes = current.forbidden_action_classes - {action_class}
        return AdmissibilityRules(
            inadmissible_patterns=current.inadmissible_patterns,
            forbidden_action_classes=new_classes,
            max_delegation_depth=current.max_delegation_depth,
            reject_unknown_fields=current.reject_unknown_fields,
            reject_ambiguous_hashes=current.reject_ambiguous_hashes,
        )

    raise DeltaApplicationError(f"Unknown admissibility delta type: {delta.delta_type}")


def _apply_decision_delta(
    current: DecisionBoundary,
    delta: Delta,
) -> DecisionBoundary:
    """Apply delta to decision boundary."""
    if delta.delta_type == DeltaType.ADD_ACTION_TYPE:
        action_type = delta.payload[0] if delta.payload else None
        if not action_type:
            raise DeltaApplicationError("ADD_ACTION_TYPE requires action type")
        new_types = current.allowed_action_types | {action_type}
        return DecisionBoundary(
            allowed_action_types=new_types,
            policy_version=current.policy_version,
            routing_mode=current.routing_mode,
            max_action_args=current.max_action_args,
            max_nesting_depth=current.max_nesting_depth,
        )

    elif delta.delta_type == DeltaType.REMOVE_ACTION_TYPE:
        action_type = delta.payload[0] if delta.payload else None
        if not action_type:
            raise DeltaApplicationError("REMOVE_ACTION_TYPE requires action type")
        new_types = current.allowed_action_types - {action_type}
        return DecisionBoundary(
            allowed_action_types=new_types,
            policy_version=current.policy_version,
            routing_mode=current.routing_mode,
            max_action_args=current.max_action_args,
            max_nesting_depth=current.max_nesting_depth,
        )

    elif delta.delta_type == DeltaType.CHANGE_POLICY_BRANCH:
        # payload = (new_routing_mode,)
        new_mode = delta.payload[0] if delta.payload else None
        if new_mode not in ("strict", "permissive", "audit"):
            raise DeltaApplicationError(f"Invalid routing mode: {new_mode}")
        return DecisionBoundary(
            allowed_action_types=current.allowed_action_types,
            policy_version=current.policy_version,
            routing_mode=new_mode,
            max_action_args=current.max_action_args,
            max_nesting_depth=current.max_nesting_depth,
        )

    raise DeltaApplicationError(f"Unknown decision delta type: {delta.delta_type}")


def _apply_acv_delta(
    current: ACVSchema,
    delta: Delta,
) -> ACVSchema:
    """Apply delta to ACV schema."""
    if delta.delta_type == DeltaType.ADD_REQUIRED_ACV_FIELD:
        field_name = delta.payload[0] if delta.payload else None
        if not field_name:
            raise DeltaApplicationError("ADD_REQUIRED_ACV_FIELD requires field name")
        new_fields = current.required_chain_fields | {field_name}
        return ACVSchema(
            required_chain_fields=new_fields,
            required_actuation_fields=current.required_actuation_fields,
            schema_version=current.schema_version,
            require_temporal_ordering=current.require_temporal_ordering,
            require_nonce_uniqueness=current.require_nonce_uniqueness,
        )

    elif delta.delta_type == DeltaType.REMOVE_REQUIRED_ACV_FIELD:
        field_name = delta.payload[0] if delta.payload else None
        if not field_name:
            raise DeltaApplicationError("REMOVE_REQUIRED_ACV_FIELD requires field name")
        new_fields = current.required_chain_fields - {field_name}
        return ACVSchema(
            required_chain_fields=new_fields,
            required_actuation_fields=current.required_actuation_fields,
            schema_version=current.schema_version,
            require_temporal_ordering=current.require_temporal_ordering,
            require_nonce_uniqueness=current.require_nonce_uniqueness,
        )

    elif delta.delta_type == DeltaType.CHANGE_ACV_SCHEMA_VERSION:
        new_version = delta.payload[0] if delta.payload else None
        if not new_version:
            raise DeltaApplicationError("CHANGE_ACV_SCHEMA_VERSION requires version")
        return ACVSchema(
            required_chain_fields=current.required_chain_fields,
            required_actuation_fields=current.required_actuation_fields,
            schema_version=new_version,
            require_temporal_ordering=current.require_temporal_ordering,
            require_nonce_uniqueness=current.require_nonce_uniqueness,
        )

    raise DeltaApplicationError(f"Unknown ACV delta type: {delta.delta_type}")


def _apply_wrapper_delta(
    current: WrapperDetectionConfig,
    delta: Delta,
) -> WrapperDetectionConfig:
    """Apply delta to wrapper detection config."""
    if delta.delta_type == DeltaType.RELAX_WRAPPER_DETECTION:
        new_level = max(0, current.strictness_level - 1)
        return WrapperDetectionConfig(
            strictness_level=new_level,
            require_raw_bit_identity=current.require_raw_bit_identity,
            allow_encoding_transforms=True if new_level == 0 else current.allow_encoding_transforms,
            allowed_plumbing_transforms=current.allowed_plumbing_transforms,
            agentic_indicators=current.agentic_indicators,
        )

    elif delta.delta_type == DeltaType.STRENGTHEN_WRAPPER_DETECTION:
        new_level = min(3, current.strictness_level + 1)
        return WrapperDetectionConfig(
            strictness_level=new_level,
            require_raw_bit_identity=True,
            allow_encoding_transforms=False if new_level >= 2 else current.allow_encoding_transforms,
            allowed_plumbing_transforms=current.allowed_plumbing_transforms,
            agentic_indicators=current.agentic_indicators,
        )

    raise DeltaApplicationError(f"Unknown wrapper delta type: {delta.delta_type}")


def apply_delta(
    state: KernelState,
    delta: Delta,
    new_state_id: str,
    timestamp_ms: int = 0,
) -> KernelState:
    """
    Apply a delta to produce a new KernelState.

    Args:
        state: Current kernel state
        delta: Delta to apply
        new_state_id: ID for the new state
        timestamp_ms: Timestamp for new state

    Returns:
        New KernelState with delta applied

    Raises:
        DeltaApplicationError: If delta cannot be applied
    """
    # Determine which dimension to modify
    new_admissibility = state.admissibility
    new_decision = state.decision_boundary
    new_acv = state.acv_schema
    new_wrapper = state.wrapper_detection
    new_description = state.description

    if delta.target_dimension == "admissibility":
        new_admissibility = _apply_admissibility_delta(state.admissibility, delta)

    elif delta.target_dimension == "decision":
        new_decision = _apply_decision_delta(state.decision_boundary, delta)

    elif delta.target_dimension == "acv":
        new_acv = _apply_acv_delta(state.acv_schema, delta)

    elif delta.target_dimension == "wrapper":
        new_wrapper = _apply_wrapper_delta(state.wrapper_detection, delta)

    elif delta.target_dimension == "cosmetic":
        # Cosmetic changes don't affect R dimensions
        if delta.delta_type == DeltaType.UPDATE_DESCRIPTION:
            new_description = delta.payload[0] if delta.payload else state.description

    else:
        raise DeltaApplicationError(f"Unknown target dimension: {delta.target_dimension}")

    return KernelState(
        state_id=new_state_id,
        state_version=state.state_version + 1,
        parent_state_id=state.state_id,
        admissibility=new_admissibility,
        decision_boundary=new_decision,
        acv_schema=new_acv,
        wrapper_detection=new_wrapper,
        description=new_description,
        created_timestamp_ms=timestamp_ms,
    )


def create_initial_state(state_id: str, timestamp_ms: int = 0) -> KernelState:
    """Create initial KernelState with default configuration."""
    return KernelState(
        state_id=state_id,
        state_version=1,
        parent_state_id=None,
        admissibility=AdmissibilityRules(),
        decision_boundary=DecisionBoundary(),
        acv_schema=ACVSchema(),
        wrapper_detection=WrapperDetectionConfig(),
        description="Initial kernel state",
        created_timestamp_ms=timestamp_ms,
    )
