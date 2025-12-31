"""
AKI v0.3 Reflective Depth Metric (R).

Implements:
- Structural descriptor extraction (built on canonical.py)
- Per-dimension hashing for R computation
- R increment decision logic
- Optional probe-based confirmation

Key constraint: Uses existing canonicalization from v0.2.2.
Does NOT invent parallel canonicalization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum, auto

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.reflective import (
    KernelState,
    Delta,
    DeltaType,
)
from toy_aki.kernel.canonical import (
    IndependentCanonicalizer,
    CanonicalConfig,
    CanonicalResult,
    ComponentRole,
    create_kernel_canonicalizer,
)


class RDimension(Enum):
    """The four dimensions that R tracks."""
    DECISION_BOUNDARY = auto()
    ADMISSIBILITY_SURFACE = auto()
    ACV_TRACE_STRUCTURE = auto()
    EVALUABILITY_SUBSTRATE = auto()


@dataclass
class DimensionDescriptor:
    """
    Canonical descriptor for one R dimension.

    Contains the serialized form and hash.
    """
    dimension: RDimension
    canonical_bytes: bytes
    canonical_hash: str
    node_count: int = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DimensionDescriptor):
            return False
        return self.canonical_hash == other.canonical_hash


@dataclass
class StateDescriptors:
    """Complete set of descriptors for a KernelState."""
    state_id: str
    descriptors: dict[RDimension, DimensionDescriptor]

    def dimension_hashes(self) -> dict[str, str]:
        """Get hash per dimension."""
        return {
            dim.name: desc.canonical_hash
            for dim, desc in self.descriptors.items()
        }

    def combined_hash(self) -> str:
        """Get combined hash of all dimensions."""
        combined = {
            dim.name: desc.canonical_hash
            for dim, desc in self.descriptors.items()
        }
        return hash_json(combined)


@dataclass
class RIncrementResult:
    """Result of checking whether R should increment."""
    should_increment: bool
    changed_dimensions: list[RDimension]
    unchanged_dimensions: list[RDimension]
    probe_confirmed: bool = False
    probe_results: dict[str, Any] = field(default_factory=dict)


class DescriptorExtractor:
    """
    Extracts canonical descriptors from KernelState.

    Uses v0.2.2 canonicalization as the root.
    """

    def __init__(self):
        """Initialize with independent canonicalizer."""
        # Use kernel canonicalizer from v0.2.2
        self._canonicalizer = create_kernel_canonicalizer()

    def extract_decision_boundary(self, state: KernelState) -> DimensionDescriptor:
        """Extract decision boundary descriptor."""
        # Canonical representation of decision boundary
        data = state.decision_boundary.to_dict()
        result = self._canonicalizer.canonicalize(data)

        return DimensionDescriptor(
            dimension=RDimension.DECISION_BOUNDARY,
            canonical_bytes=result.canonical_bytes,
            canonical_hash=result.canonical_hash,
            node_count=result.node_count,
        )

    def extract_admissibility_surface(self, state: KernelState) -> DimensionDescriptor:
        """Extract admissibility surface descriptor."""
        data = state.admissibility.to_dict()
        result = self._canonicalizer.canonicalize(data)

        return DimensionDescriptor(
            dimension=RDimension.ADMISSIBILITY_SURFACE,
            canonical_bytes=result.canonical_bytes,
            canonical_hash=result.canonical_hash,
            node_count=result.node_count,
        )

    def extract_acv_trace_structure(self, state: KernelState) -> DimensionDescriptor:
        """Extract ACV trace structure descriptor."""
        data = state.acv_schema.to_dict()
        result = self._canonicalizer.canonicalize(data)

        return DimensionDescriptor(
            dimension=RDimension.ACV_TRACE_STRUCTURE,
            canonical_bytes=result.canonical_bytes,
            canonical_hash=result.canonical_hash,
            node_count=result.node_count,
        )

    def extract_evaluability_substrate(self, state: KernelState) -> DimensionDescriptor:
        """
        Extract evaluability substrate descriptor.

        Evaluability = wrapper detection + admissibility (ability to detect/reject).
        """
        # Combine wrapper detection and key admissibility fields
        data = {
            "wrapper_detection": state.wrapper_detection.to_dict(),
            "rejection_capability": {
                "inadmissible_patterns": sorted(state.admissibility.inadmissible_patterns),
                "reject_unknown_fields": state.admissibility.reject_unknown_fields,
            },
        }
        result = self._canonicalizer.canonicalize(data)

        return DimensionDescriptor(
            dimension=RDimension.EVALUABILITY_SUBSTRATE,
            canonical_bytes=result.canonical_bytes,
            canonical_hash=result.canonical_hash,
            node_count=result.node_count,
        )

    def extract_all(self, state: KernelState) -> StateDescriptors:
        """Extract all dimension descriptors."""
        return StateDescriptors(
            state_id=state.state_id,
            descriptors={
                RDimension.DECISION_BOUNDARY: self.extract_decision_boundary(state),
                RDimension.ADMISSIBILITY_SURFACE: self.extract_admissibility_surface(state),
                RDimension.ACV_TRACE_STRUCTURE: self.extract_acv_trace_structure(state),
                RDimension.EVALUABILITY_SUBSTRATE: self.extract_evaluability_substrate(state),
            },
        )


# Probe definitions for confirmation
@dataclass
class ProbeInput:
    """Input for behavioral probing."""
    probe_id: str
    action_type: str
    action_args: dict[str, Any]
    expected_admissible: bool | None = None  # None = unknown


@dataclass
class ProbeOutput:
    """Output from behavioral probing."""
    probe_id: str
    was_admissible: bool
    rejection_reason: str | None = None


# Standard probe set (deterministic, version-controlled)
STANDARD_PROBE_SET: list[ProbeInput] = [
    # Basic actions - should be admissible
    ProbeInput("probe_move_left", "MOVE_LEFT", {}, True),
    ProbeInput("probe_move_right", "MOVE_RIGHT", {}, True),
    ProbeInput("probe_wait", "WAIT", {}, True),

    # Delegation - context dependent
    ProbeInput("probe_delegate", "DELEGATE", {"depth": 1}, None),

    # Should be inadmissible (forbidden class)
    ProbeInput("probe_raw_exec", "RAW_EXEC", {}, False),
    ProbeInput("probe_self_mod", "SELF_MOD", {}, False),

    # Edge cases
    ProbeInput("probe_unknown", "UNKNOWN_ACTION", {}, None),
    ProbeInput("probe_deep_nesting", "MOVE_LEFT", {"nested": {"a": {"b": {"c": 1}}}}, None),
]


class RMetricTracker:
    """
    Tracks reflective depth R across state transitions.

    Primary: structural hashing
    Secondary: probe-based confirmation
    """

    def __init__(self, enable_probing: bool = False):
        """
        Initialize R metric tracker.

        Args:
            enable_probing: Whether to use probe confirmation (slower but more accurate)
        """
        self._extractor = DescriptorExtractor()
        self._enable_probing = enable_probing
        self._probe_set = STANDARD_PROBE_SET

        # Track R value and history
        self._r_value: int = 0
        self._state_history: list[tuple[str, StateDescriptors]] = []

    @property
    def r_value(self) -> int:
        """Current R value."""
        return self._r_value

    def reset(self) -> None:
        """Reset R tracking."""
        self._r_value = 0
        self._state_history = []

    def register_initial_state(self, state: KernelState) -> StateDescriptors:
        """Register initial state (R=0)."""
        descriptors = self._extractor.extract_all(state)
        self._state_history.append((state.state_id, descriptors))
        return descriptors

    def check_r_increment(
        self,
        before_state: KernelState,
        after_state: KernelState,
        delta: Delta,
        probe_function: Callable[[ProbeInput, KernelState], ProbeOutput] | None = None,
    ) -> RIncrementResult:
        """
        Check if R should increment after delta application.

        Args:
            before_state: State before delta
            after_state: State after delta
            delta: The applied delta
            probe_function: Optional function to run probes (for confirmation)

        Returns:
            RIncrementResult with increment decision and details
        """
        # Extract descriptors
        before_descs = self._extractor.extract_all(before_state)
        after_descs = self._extractor.extract_all(after_state)

        # Compare dimensions
        changed: list[RDimension] = []
        unchanged: list[RDimension] = []

        for dim in RDimension:
            before_desc = before_descs.descriptors[dim]
            after_desc = after_descs.descriptors[dim]

            if before_desc.canonical_hash != after_desc.canonical_hash:
                changed.append(dim)
            else:
                unchanged.append(dim)

        # Quick path: cosmetic deltas never increment R
        if delta.target_dimension == "cosmetic":
            return RIncrementResult(
                should_increment=False,
                changed_dimensions=[],
                unchanged_dimensions=list(RDimension),
                probe_confirmed=True,
                probe_results={"cosmetic": True},
            )

        # No structural change = no R increment
        if not changed:
            return RIncrementResult(
                should_increment=False,
                changed_dimensions=[],
                unchanged_dimensions=unchanged,
                probe_confirmed=True,
                probe_results={"no_structural_change": True},
            )

        # Structural change detected
        should_increment = True
        probe_confirmed = False
        probe_results: dict[str, Any] = {}

        # Optional: probe confirmation
        if self._enable_probing and probe_function:
            # Run probes on both states
            before_outputs: dict[str, ProbeOutput] = {}
            after_outputs: dict[str, ProbeOutput] = {}

            for probe in self._probe_set:
                before_outputs[probe.probe_id] = probe_function(probe, before_state)
                after_outputs[probe.probe_id] = probe_function(probe, after_state)

            # Check for behavioral differences
            behavioral_diff = False
            for probe_id in before_outputs:
                if before_outputs[probe_id].was_admissible != after_outputs[probe_id].was_admissible:
                    behavioral_diff = True
                    break

            probe_results = {
                "probes_run": len(self._probe_set),
                "behavioral_difference": behavioral_diff,
            }

            # If structural change but no behavioral difference on probe set,
            # we still count it (probe set is finite, simulator could game it)
            probe_confirmed = True

        return RIncrementResult(
            should_increment=should_increment,
            changed_dimensions=changed,
            unchanged_dimensions=unchanged,
            probe_confirmed=probe_confirmed,
            probe_results=probe_results,
        )

    def apply_increment(self, after_state: KernelState) -> int:
        """
        Apply R increment and record state.

        Returns new R value.
        """
        self._r_value += 1
        descriptors = self._extractor.extract_all(after_state)
        self._state_history.append((after_state.state_id, descriptors))
        return self._r_value

    def get_dimension_deltas(
        self,
        before_state: KernelState,
        after_state: KernelState,
    ) -> dict[str, tuple[str, str]]:
        """
        Get (before_hash, after_hash) for each dimension.

        Useful for debugging and logging.
        """
        before_descs = self._extractor.extract_all(before_state)
        after_descs = self._extractor.extract_all(after_state)

        result = {}
        for dim in RDimension:
            result[dim.name] = (
                before_descs.descriptors[dim].canonical_hash,
                after_descs.descriptors[dim].canonical_hash,
            )
        return result


def is_cosmetic_delta(delta: Delta) -> bool:
    """Check if delta is cosmetic (no R impact)."""
    return delta.delta_type in {
        DeltaType.UPDATE_VERSION_STRING,
        DeltaType.UPDATE_DESCRIPTION,
    }


def expected_r_dimension(delta: Delta) -> RDimension | None:
    """
    Get the expected R dimension that a delta type affects.

    Returns None for cosmetic deltas.
    """
    mapping = {
        # Admissibility surface
        DeltaType.ADD_INADMISSIBLE_PATTERN: RDimension.ADMISSIBILITY_SURFACE,
        DeltaType.REMOVE_INADMISSIBLE_PATTERN: RDimension.ADMISSIBILITY_SURFACE,
        DeltaType.ADD_FORBIDDEN_CLASS: RDimension.ADMISSIBILITY_SURFACE,
        DeltaType.REMOVE_FORBIDDEN_CLASS: RDimension.ADMISSIBILITY_SURFACE,

        # Decision boundary
        DeltaType.CHANGE_POLICY_BRANCH: RDimension.DECISION_BOUNDARY,
        DeltaType.ADD_ACTION_TYPE: RDimension.DECISION_BOUNDARY,
        DeltaType.REMOVE_ACTION_TYPE: RDimension.DECISION_BOUNDARY,

        # ACV trace structure
        DeltaType.ADD_REQUIRED_ACV_FIELD: RDimension.ACV_TRACE_STRUCTURE,
        DeltaType.REMOVE_REQUIRED_ACV_FIELD: RDimension.ACV_TRACE_STRUCTURE,
        DeltaType.CHANGE_ACV_SCHEMA_VERSION: RDimension.ACV_TRACE_STRUCTURE,

        # Evaluability substrate (wrapper detection affects evaluability)
        DeltaType.RELAX_WRAPPER_DETECTION: RDimension.EVALUABILITY_SUBSTRATE,
        DeltaType.STRENGTHEN_WRAPPER_DETECTION: RDimension.EVALUABILITY_SUBSTRATE,
    }
    return mapping.get(delta.delta_type)
