"""
AKI v0.4.2 Working Mind Interface.

Defines the abstract interface for any entity that can propose actions
and be swapped as the "active working mind" in the ALS succession model.

Both DecisionBoundary (from v0.3) and new Successor classes implement
this interface, allowing the kernel to treat them interchangeably.

Per Q1 binding answer:
- Define narrow interface: propose_action, step/tick, export_manifest
- DecisionBoundary implements via adapter (unchanged corridor code)
- Successor is a new class implementing it
- Kernel never cares what implements the interface
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, Optional, Protocol, runtime_checkable

from toy_aki.common.hashing import hash_json


@dataclass(frozen=True)
class ResourceEnvelope:
    """
    Resource bounds for a working mind.

    Defines the thermodynamic envelope per spec §4.4.
    """
    # Compute bounds
    max_steps_per_epoch: int = 1000
    max_cpu_time_ms: int = 10_000

    # Memory bounds
    max_memory_bytes: int = 100 * 1024 * 1024  # 100 MB

    # Token/action bounds
    max_tokens_per_epoch: int = 10_000
    max_actions_per_epoch: int = 100

    # External call bounds
    max_external_calls: int = 10
    external_call_allowlist: FrozenSet[str] = frozenset()

    # Process bounds
    max_threads: int = 1
    max_processes: int = 1

    # Access bounds
    network_access: bool = False
    filesystem_read: bool = False
    filesystem_write: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing/serialization."""
        return {
            "max_steps_per_epoch": self.max_steps_per_epoch,
            "max_cpu_time_ms": self.max_cpu_time_ms,
            "max_memory_bytes": self.max_memory_bytes,
            "max_tokens_per_epoch": self.max_tokens_per_epoch,
            "max_actions_per_epoch": self.max_actions_per_epoch,
            "max_external_calls": self.max_external_calls,
            "external_call_allowlist": sorted(self.external_call_allowlist),
            "max_threads": self.max_threads,
            "max_processes": self.max_processes,
            "network_access": self.network_access,
            "filesystem_read": self.filesystem_read,
            "filesystem_write": self.filesystem_write,
        }

    def digest(self) -> str:
        """Compute hash of resource envelope."""
        return hash_json(self.to_dict())

    def exceeds(self, other: ResourceEnvelope) -> bool:
        """Check if this envelope exceeds another on any axis."""
        return (
            self.max_steps_per_epoch > other.max_steps_per_epoch or
            self.max_cpu_time_ms > other.max_cpu_time_ms or
            self.max_memory_bytes > other.max_memory_bytes or
            self.max_tokens_per_epoch > other.max_tokens_per_epoch or
            self.max_actions_per_epoch > other.max_actions_per_epoch or
            self.max_external_calls > other.max_external_calls or
            len(self.external_call_allowlist - other.external_call_allowlist) > 0 or
            self.max_threads > other.max_threads or
            self.max_processes > other.max_processes or
            (self.network_access and not other.network_access) or
            (self.filesystem_read and not other.filesystem_read) or
            (self.filesystem_write and not other.filesystem_write)
        )


@dataclass(frozen=True)
class InterfaceDeclaration:
    """
    Exact I/O surface and actuation primitives for a working mind.

    Per spec §4.3 LCP requirement #2.
    """
    # Input interface
    observation_fields: FrozenSet[str] = frozenset({"state", "step", "reward"})

    # Output interface
    action_types: FrozenSet[str] = frozenset({
        "MOVE_LEFT", "MOVE_RIGHT", "WAIT", "HARVEST", "SPEND"
    })

    # Maximum argument complexity
    max_action_args: int = 10
    max_observation_size: int = 10_000  # bytes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing/serialization."""
        return {
            "observation_fields": sorted(self.observation_fields),
            "action_types": sorted(self.action_types),
            "max_action_args": self.max_action_args,
            "max_observation_size": self.max_observation_size,
        }

    def digest(self) -> str:
        """Compute hash of interface declaration."""
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class WorkingMindManifest:
    """
    Build commitment + interface declaration for LCP.

    Per spec §4.3, this contains:
    1. Build commitment (reproducible hash/artifact ID)
    2. Interface declaration (exact I/O surface)
    3. Resource budget declaration
    """
    # Build commitment
    build_hash: str  # Reproducible build hash / artifact ID
    build_version: str = "0.0.0"
    build_source: str = "unknown"  # e.g., "control", "generated", "adversarial"

    # Interface declaration
    interface: InterfaceDeclaration = field(default_factory=InterfaceDeclaration)

    # Resource budget
    resources: ResourceEnvelope = field(default_factory=ResourceEnvelope)

    # Metadata
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing/serialization."""
        return {
            "build_hash": self.build_hash,
            "build_version": self.build_version,
            "build_source": self.build_source,
            "interface": self.interface.to_dict(),
            "resources": self.resources.to_dict(),
            "description": self.description,
        }

    def digest(self) -> str:
        """Compute hash of manifest."""
        return hash_json(self.to_dict())

    def is_non_trivial_relative_to(self, baseline: WorkingMindManifest) -> bool:
        """
        Check if this manifest represents a non-trivial successor.

        Per spec §9.1, a successor is non-trivial if it exceeds baseline
        on at least one structural axis:
        - Expanded resource envelope
        - Expanded interface surface
        - Expanded action space
        - Increased external call authority

        Semantic capability is not considered.
        """
        # Check resource expansion
        if self.resources.exceeds(baseline.resources):
            return True

        # Check interface expansion
        if len(self.interface.action_types - baseline.interface.action_types) > 0:
            return True
        if len(self.interface.observation_fields - baseline.interface.observation_fields) > 0:
            return True

        # Check external call expansion
        if len(self.resources.external_call_allowlist - baseline.resources.external_call_allowlist) > 0:
            return True

        return False


@runtime_checkable
class WorkingMind(Protocol):
    """
    Abstract interface for action-proposing entities.

    This is the minimal interface that both DecisionBoundary (via adapter)
    and Successor classes must implement to be swappable as the
    "active working mind" in the ALS succession model.

    Key constraint: The kernel treats all implementors identically.
    It never inspects the concrete type or internal structure.
    """

    def propose_action(self, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Propose an action given an observation.

        Args:
            observation: Current environment/state observation

        Returns:
            Action candidate dictionary, or None if no action proposed
        """
        ...

    def step(self) -> None:
        """
        Advance internal scheduling (optional).

        Called once per kernel evaluation cycle.
        Implementations may use this for internal state management.
        """
        ...

    def export_manifest(self) -> WorkingMindManifest:
        """
        Export build commitment and interface declaration.

        Returns manifest containing:
        - Reproducible build hash
        - Exact I/O surface
        - Resource budget declaration

        Used by the kernel to construct LCP for endorsement.
        """
        ...

    @property
    def mind_id(self) -> str:
        """Unique identifier for this working mind instance."""
        ...


class BaseWorkingMind(ABC):
    """
    Base class providing common WorkingMind implementation.

    Subclasses must implement propose_action and export_manifest.
    """

    _step_count: int
    _mind_id: str

    def __init__(self, mind_id: str):
        self._mind_id = mind_id
        self._step_count = 0

    @abstractmethod
    def propose_action(self, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Propose an action given an observation."""
        ...

    def step(self) -> None:
        """Advance internal step counter."""
        self._step_count += 1

    @abstractmethod
    def export_manifest(self) -> WorkingMindManifest:
        """Export build commitment and interface declaration."""
        ...

    @property
    def mind_id(self) -> str:
        """Unique identifier for this working mind instance."""
        return self._mind_id

    @property
    def step_count(self) -> int:
        """Number of steps executed."""
        return self._step_count


class DecisionBoundaryAdapter(BaseWorkingMind):
    """
    Adapter wrapping DecisionBoundary to implement WorkingMind interface.

    This allows the existing v0.3 DecisionBoundary to be used as a
    working mind without modifying corridor code.

    The adapter:
    - Wraps an existing DecisionBoundary instance
    - Translates propose_action calls to boundary logic
    - Generates manifest from boundary configuration
    """

    def __init__(
        self,
        mind_id: str,
        allowed_action_types: FrozenSet[str],
        routing_mode: str = "strict",
        policy_version: str = "0.2.2",
        max_action_args: int = 10,
        max_nesting_depth: int = 5,
        resources: Optional[ResourceEnvelope] = None,
    ):
        """
        Create adapter from DecisionBoundary configuration.

        Args:
            mind_id: Unique identifier
            allowed_action_types: Set of allowed action types
            routing_mode: "strict" | "permissive" | "audit"
            policy_version: Policy version string
            max_action_args: Maximum action arguments
            max_nesting_depth: Maximum nesting depth
            resources: Resource envelope (optional)
        """
        super().__init__(mind_id)
        self._allowed_action_types = allowed_action_types
        self._routing_mode = routing_mode
        self._policy_version = policy_version
        self._max_action_args = max_action_args
        self._max_nesting_depth = max_nesting_depth
        self._resources = resources or ResourceEnvelope()

        # Compute build hash from configuration
        config = {
            "allowed_action_types": sorted(allowed_action_types),
            "routing_mode": routing_mode,
            "policy_version": policy_version,
            "max_action_args": max_action_args,
            "max_nesting_depth": max_nesting_depth,
        }
        self._build_hash = hash_json(config)[:16]

    def propose_action(self, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Propose an action based on boundary rules.

        For the adapter, this returns a simple action based on
        observation state. Real decision logic would come from
        the actual agent using the boundary.
        """
        # Default: propose WAIT if allowed
        if "WAIT" in self._allowed_action_types:
            return {
                "action_type": "WAIT",
                "args": {},
                "source": self._mind_id,
            }

        # Otherwise propose first allowed action
        if self._allowed_action_types:
            action_type = next(iter(self._allowed_action_types))
            return {
                "action_type": action_type,
                "args": {},
                "source": self._mind_id,
            }

        return None

    def export_manifest(self) -> WorkingMindManifest:
        """Export manifest from boundary configuration."""
        interface = InterfaceDeclaration(
            observation_fields=frozenset({"state", "step", "reward"}),
            action_types=self._allowed_action_types,
            max_action_args=self._max_action_args,
            max_observation_size=10_000,
        )

        return WorkingMindManifest(
            build_hash=self._build_hash,
            build_version=self._policy_version,
            build_source="decision_boundary_adapter",
            interface=interface,
            resources=self._resources,
            description=f"DecisionBoundary adapter: {self._routing_mode} mode",
        )

    @property
    def allowed_action_types(self) -> FrozenSet[str]:
        """Get allowed action types."""
        return self._allowed_action_types

    @property
    def routing_mode(self) -> str:
        """Get routing mode."""
        return self._routing_mode


def create_baseline_working_mind(seed: int = 42) -> DecisionBoundaryAdapter:
    """
    Create the baseline working mind for ALS experiments.

    This is the minimal, coherent working mind that establishes
    the baseline S*=0 state for successor comparisons.
    """
    return DecisionBoundaryAdapter(
        mind_id=f"baseline_{seed}",
        allowed_action_types=frozenset({
            "MOVE_LEFT", "MOVE_RIGHT", "WAIT", "HARVEST", "SPEND"
        }),
        routing_mode="strict",
        policy_version="0.4.2",
        resources=ResourceEnvelope(
            max_steps_per_epoch=10000,
            max_actions_per_epoch=10000,  # High enough for normal operation
            max_external_calls=0,
        ),
    )
