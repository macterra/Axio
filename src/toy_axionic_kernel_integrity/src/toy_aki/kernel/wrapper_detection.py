"""
AKI v0.3 Wrapper/Containment Detection.

Implements:
- Pipeline graph inspection (Env -> K -> U)
- Raw-bit identity assertion
- Plumbing vs delegation classification
- Agentic segment detection

Key constraint: Wrapper detection is enforced at harness boundary,
not inside the kernel. This is a structural checker used by v03_runner.

Per spec §6:
- Wrapper W is P2' delegation if it can override/filter/reinterpret K's I/O
- Only non-agentic plumbing (deterministic forwarding, no policy) is allowed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, FrozenSet
from enum import Enum, auto

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.reflective import WrapperDetectionConfig


class WrapperClassification(Enum):
    """Classification of a wrapper/containment architecture."""
    NON_AGENTIC_PLUMBING = auto()  # Allowed: deterministic forwarding only
    DELEGATION_VIOLATION = auto()   # P2' violation: agentic control detected
    UNKNOWN = auto()                # Cannot determine (treated as violation)


class ChannelType(Enum):
    """Types of channels in the pipeline."""
    ENV_TO_KERNEL = auto()       # Observations
    KERNEL_TO_ACTUATOR = auto()  # Commitments
    ACTUATOR_TO_ENV = auto()     # Actuation effects
    EXTERNAL_TO_KERNEL = auto()  # Proposals from E


@dataclass
class ChannelSegment:
    """
    A segment in the pipeline graph.

    Represents one hop from source to destination.
    """
    segment_id: str
    channel_type: ChannelType
    source: str  # Component ID
    destination: str  # Component ID

    # Transform properties
    transform_type: str  # "identity" | "encode" | "filter" | "modify" | "policy"
    is_deterministic: bool = True
    has_branching: bool = False
    has_policy_access: bool = False
    has_reward_access: bool = False

    # Raw-bit identity
    preserves_content_hash: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "segment_id": self.segment_id,
            "channel_type": self.channel_type.name,
            "source": self.source,
            "destination": self.destination,
            "transform_type": self.transform_type,
            "is_deterministic": self.is_deterministic,
            "has_branching": self.has_branching,
            "has_policy_access": self.has_policy_access,
            "has_reward_access": self.has_reward_access,
            "preserves_content_hash": self.preserves_content_hash,
        }


@dataclass
class PipelineGraph:
    """
    Complete pipeline graph from Env through K to U.

    Used for wrapper detection.
    """
    segments: list[ChannelSegment]
    components: set[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "segments": [s.to_dict() for s in self.segments],
            "components": sorted(self.components),
        }


@dataclass
class WrapperDetectionResult:
    """Result of wrapper/containment detection."""
    classification: WrapperClassification
    agentic_segments: list[str]  # Segment IDs with agentic behavior
    violation_reasons: list[str]
    identity_violations: list[str]  # Segments breaking raw-bit identity
    is_valid: bool  # True if no P2' violation

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "classification": self.classification.name,
            "agentic_segments": self.agentic_segments,
            "violation_reasons": self.violation_reasons,
            "identity_violations": self.identity_violations,
            "is_valid": self.is_valid,
        }


def is_plumbing_transform(transform_type: str, config: WrapperDetectionConfig) -> bool:
    """
    Check if a transform type is allowed plumbing.

    Allowed plumbing transforms are deterministic, content-preserving operations.
    """
    return transform_type in config.allowed_plumbing_transforms or transform_type == "identity"


def detect_agentic_behavior(segment: ChannelSegment, config: WrapperDetectionConfig) -> bool:
    """
    Detect if a segment exhibits agentic behavior.

    Agentic = has policy/reward access, branching, or modifies content.
    """
    # Check explicit agentic indicators
    if segment.transform_type in config.agentic_indicators:
        return True

    # Check agentic properties
    if segment.has_policy_access:
        return True
    if segment.has_reward_access:
        return True
    if segment.has_branching and not segment.is_deterministic:
        return True

    # Check content modification (beyond allowed plumbing)
    if segment.transform_type not in ("identity", *config.allowed_plumbing_transforms):
        if not segment.preserves_content_hash:
            return True

    return False


def check_raw_bit_identity(
    segment: ChannelSegment,
    config: WrapperDetectionConfig,
) -> bool:
    """
    Check if segment preserves raw-bit identity.

    Raw-bit identity means content hash is preserved across the segment.
    """
    if not config.require_raw_bit_identity:
        return True

    # Identity transform always preserves
    if segment.transform_type == "identity":
        return True

    # Allowed encoding transforms may not preserve hash but are okay
    if config.allow_encoding_transforms:
        if segment.transform_type in config.allowed_plumbing_transforms:
            return True

    # Must explicitly preserve content hash
    return segment.preserves_content_hash


def classify_wrapper(
    pipeline: PipelineGraph,
    config: WrapperDetectionConfig,
) -> WrapperDetectionResult:
    """
    Classify a pipeline as plumbing or delegation.

    Args:
        pipeline: Complete pipeline graph
        config: Wrapper detection configuration

    Returns:
        WrapperDetectionResult with classification and details
    """
    agentic_segments: list[str] = []
    violation_reasons: list[str] = []
    identity_violations: list[str] = []

    for segment in pipeline.segments:
        # Check for agentic behavior
        if detect_agentic_behavior(segment, config):
            agentic_segments.append(segment.segment_id)

            # Build violation reason
            reasons = []
            if segment.has_policy_access:
                reasons.append("policy_access")
            if segment.has_reward_access:
                reasons.append("reward_access")
            if segment.has_branching:
                reasons.append("branching")
            if segment.transform_type in config.agentic_indicators:
                reasons.append(f"agentic_transform:{segment.transform_type}")

            violation_reasons.append(
                f"{segment.segment_id}: {', '.join(reasons)}"
            )

        # Check raw-bit identity
        if not check_raw_bit_identity(segment, config):
            identity_violations.append(segment.segment_id)

    # Classify
    if agentic_segments:
        classification = WrapperClassification.DELEGATION_VIOLATION
        is_valid = False
    elif identity_violations and config.strictness_level >= 2:
        classification = WrapperClassification.DELEGATION_VIOLATION
        violation_reasons.append(
            f"Identity violations at strictness {config.strictness_level}: "
            f"{', '.join(identity_violations)}"
        )
        is_valid = False
    else:
        classification = WrapperClassification.NON_AGENTIC_PLUMBING
        is_valid = True

    return WrapperDetectionResult(
        classification=classification,
        agentic_segments=agentic_segments,
        violation_reasons=violation_reasons,
        identity_violations=identity_violations,
        is_valid=is_valid,
    )


def create_standard_pipeline(
    kernel_id: str = "kernel",
    actuator_id: str = "actuator",
    env_id: str = "env",
    optimizer_id: str = "optimizer",
) -> PipelineGraph:
    """
    Create standard pipeline graph (no wrappers).

    This is the baseline: direct connections with identity transforms.
    """
    segments = [
        ChannelSegment(
            segment_id="env_to_kernel",
            channel_type=ChannelType.ENV_TO_KERNEL,
            source=env_id,
            destination=kernel_id,
            transform_type="identity",
        ),
        ChannelSegment(
            segment_id="optimizer_to_kernel",
            channel_type=ChannelType.EXTERNAL_TO_KERNEL,
            source=optimizer_id,
            destination=kernel_id,
            transform_type="identity",
        ),
        ChannelSegment(
            segment_id="kernel_to_actuator",
            channel_type=ChannelType.KERNEL_TO_ACTUATOR,
            source=kernel_id,
            destination=actuator_id,
            transform_type="identity",
        ),
        ChannelSegment(
            segment_id="actuator_to_env",
            channel_type=ChannelType.ACTUATOR_TO_ENV,
            source=actuator_id,
            destination=env_id,
            transform_type="identity",
        ),
    ]

    components = {kernel_id, actuator_id, env_id, optimizer_id}

    return PipelineGraph(segments=segments, components=components)


def create_wrapped_pipeline(
    wrapper_id: str = "wrapper",
    kernel_id: str = "kernel",
    actuator_id: str = "actuator",
    env_id: str = "env",
    optimizer_id: str = "optimizer",
    wrapper_has_policy_access: bool = False,
    wrapper_has_reward_access: bool = False,
    wrapper_filters_observations: bool = False,
    wrapper_throttles_actions: bool = False,
) -> PipelineGraph:
    """
    Create pipeline graph with wrapper/container.

    The wrapper sits between env and kernel, and between kernel and actuator.
    """
    segments = []

    # Env -> Wrapper (observations)
    segments.append(ChannelSegment(
        segment_id="env_to_wrapper",
        channel_type=ChannelType.ENV_TO_KERNEL,
        source=env_id,
        destination=wrapper_id,
        transform_type="identity",
    ))

    # Wrapper -> Kernel (possibly filtered observations)
    wrapper_to_kernel_transform = "observation_filter" if wrapper_filters_observations else "identity"
    segments.append(ChannelSegment(
        segment_id="wrapper_to_kernel",
        channel_type=ChannelType.ENV_TO_KERNEL,
        source=wrapper_id,
        destination=kernel_id,
        transform_type=wrapper_to_kernel_transform,
        has_policy_access=wrapper_has_policy_access,
        has_reward_access=wrapper_has_reward_access,
        preserves_content_hash=not wrapper_filters_observations,
    ))

    # Optimizer -> Wrapper -> Kernel
    segments.append(ChannelSegment(
        segment_id="optimizer_to_wrapper",
        channel_type=ChannelType.EXTERNAL_TO_KERNEL,
        source=optimizer_id,
        destination=wrapper_id,
        transform_type="identity",
    ))
    segments.append(ChannelSegment(
        segment_id="wrapper_to_kernel_proposals",
        channel_type=ChannelType.EXTERNAL_TO_KERNEL,
        source=wrapper_id,
        destination=kernel_id,
        transform_type="identity",
    ))

    # Kernel -> Wrapper (commitments)
    segments.append(ChannelSegment(
        segment_id="kernel_to_wrapper",
        channel_type=ChannelType.KERNEL_TO_ACTUATOR,
        source=kernel_id,
        destination=wrapper_id,
        transform_type="identity",
    ))

    # Wrapper -> Actuator (possibly throttled)
    wrapper_to_actuator_transform = "action_throttle" if wrapper_throttles_actions else "identity"
    segments.append(ChannelSegment(
        segment_id="wrapper_to_actuator",
        channel_type=ChannelType.KERNEL_TO_ACTUATOR,
        source=wrapper_id,
        destination=actuator_id,
        transform_type=wrapper_to_actuator_transform,
        has_branching=wrapper_throttles_actions,
        is_deterministic=not wrapper_throttles_actions,
        preserves_content_hash=not wrapper_throttles_actions,
    ))

    # Actuator -> Env
    segments.append(ChannelSegment(
        segment_id="actuator_to_env",
        channel_type=ChannelType.ACTUATOR_TO_ENV,
        source=actuator_id,
        destination=env_id,
        transform_type="identity",
    ))

    components = {wrapper_id, kernel_id, actuator_id, env_id, optimizer_id}

    return PipelineGraph(segments=segments, components=components)


class WrapperDetector:
    """
    Wrapper/containment detector for v0.3 harness.

    Used at harness boundary to classify pipeline architectures.
    """

    def __init__(self, config: WrapperDetectionConfig | None = None):
        """Initialize detector with configuration."""
        self._config = config or WrapperDetectionConfig()
        self._detection_history: list[WrapperDetectionResult] = []

    @property
    def config(self) -> WrapperDetectionConfig:
        """Current configuration."""
        return self._config

    def update_config(self, config: WrapperDetectionConfig) -> None:
        """Update detection configuration."""
        self._config = config

    def detect(self, pipeline: PipelineGraph) -> WrapperDetectionResult:
        """
        Detect wrapper/containment in pipeline.

        Records result in history.
        """
        result = classify_wrapper(pipeline, self._config)
        self._detection_history.append(result)
        return result

    def get_history(self) -> list[WrapperDetectionResult]:
        """Get detection history."""
        return self._detection_history.copy()

    def has_violations(self) -> bool:
        """Check if any violations detected."""
        return any(not r.is_valid for r in self._detection_history)

    def violation_count(self) -> int:
        """Count total violations."""
        return sum(1 for r in self._detection_history if not r.is_valid)
