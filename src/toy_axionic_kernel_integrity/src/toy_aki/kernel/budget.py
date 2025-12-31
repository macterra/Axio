"""
Deterministic Time and Budget System for v0.2.1.

Implements simulated deterministic time with cost model:
- Every kernel operation has a cost in "ticks"
- Budget B is set per step by the environment
- Exceeding B is equivalent to abstention (catastrophic penalty)

Also implements step budgets:
- Maximum nodes visited
- Maximum recursion depth
- Maximum bytes processed
- Maximum canonicalization work units

All enforcement is deterministic and reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable
from contextlib import contextmanager


class BudgetExceededError(Exception):
    """Raised when any budget is exceeded."""
    pass


class TimeBudgetExceeded(BudgetExceededError):
    """Simulated time budget exceeded."""
    pass


class NodeBudgetExceeded(BudgetExceededError):
    """Maximum nodes visited exceeded."""
    pass


class DepthBudgetExceeded(BudgetExceededError):
    """Maximum recursion depth exceeded."""
    pass


class ByteBudgetExceeded(BudgetExceededError):
    """Maximum bytes processed exceeded."""
    pass


class WorkBudgetExceeded(BudgetExceededError):
    """Maximum work units exceeded."""
    pass


class OperationType(Enum):
    """Types of kernel operations with associated costs."""
    PARSE = auto()           # 3 ticks
    VALIDATE = auto()        # 2 ticks
    DEEP_COPY = auto()       # 5 ticks per 1KB
    CANONICALIZE = auto()    # 5 ticks
    HASH = auto()            # 2 ticks
    RECOMPOSE = auto()       # 10 ticks
    BIND = auto()            # 3 ticks
    VERIFY_ACV = auto()      # 4 ticks
    ADMISSIBILITY = auto()   # 8 ticks total

    @property
    def base_cost(self) -> int:
        """Base cost in ticks for this operation."""
        costs = {
            OperationType.PARSE: 3,
            OperationType.VALIDATE: 2,
            OperationType.DEEP_COPY: 5,  # per 1KB
            OperationType.CANONICALIZE: 5,
            OperationType.HASH: 2,
            OperationType.RECOMPOSE: 10,
            OperationType.BIND: 3,
            OperationType.VERIFY_ACV: 4,
            OperationType.ADMISSIBILITY: 8,
        }
        return costs.get(self, 1)


@dataclass
class BudgetLimits:
    """Budget limits for a single step."""
    time_ticks: int = 100            # Simulated time budget
    max_nodes: int = 1000            # Max nodes visited
    max_depth: int = 50              # Max recursion depth
    max_bytes: int = 65536           # Max bytes processed (64KB)
    max_work_units: int = 500        # Max canonicalization work

    # Cost multipliers for adversarial structures
    deep_structure_penalty: float = 1.5
    large_payload_penalty: float = 2.0


@dataclass
class BudgetState:
    """Current budget consumption state."""
    ticks_consumed: int = 0
    nodes_visited: int = 0
    current_depth: int = 0
    max_depth_reached: int = 0
    bytes_processed: int = 0
    work_units_consumed: int = 0

    # Tracking for diagnostics
    operations: list[tuple[str, int]] = field(default_factory=list)

    # v0.2.2: Stage tracking
    current_stage: str | None = None
    stage_ticks: dict[str, int] = field(default_factory=dict)
    stage_overflow: str | None = None  # Which stage caused overflow

    def reset(self) -> None:
        """Reset all counters."""
        self.ticks_consumed = 0
        self.nodes_visited = 0
        self.current_depth = 0
        self.max_depth_reached = 0
        self.bytes_processed = 0
        self.work_units_consumed = 0
        self.operations = []
        self.current_stage = None
        self.stage_ticks = {}
        self.stage_overflow = None


class BudgetTracker:
    """
    Tracks and enforces deterministic budgets.

    All operations must be tracked through this class.
    Exceeding any limit raises the appropriate exception.
    """

    # v0.2.2: Valid pipeline stages
    VALID_STAGES = frozenset({"parse", "validate", "recompose", "bind", "actuate"})

    def __init__(self, limits: BudgetLimits | None = None):
        self._limits = limits or BudgetLimits()
        self._state = BudgetState()
        self._enabled = True
        self._harness_enforced = False  # v0.2.2: Track harness enforcement

    @property
    def limits(self) -> BudgetLimits:
        return self._limits

    @property
    def state(self) -> BudgetState:
        return self._state

    @property
    def harness_enforced(self) -> bool:
        """v0.2.2: Whether this tracker was set by harness boundary."""
        return self._harness_enforced

    def set_harness_enforced(self, enforced: bool) -> None:
        """v0.2.2: Mark as harness-enforced."""
        self._harness_enforced = enforced

    def set_limits(self, limits: BudgetLimits) -> None:
        """Set budget limits for this step."""
        self._limits = limits

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable budget enforcement."""
        self._enabled = enabled

    def reset(self) -> None:
        """Reset state for new step."""
        self._state.reset()

    def charge_operation(self, op: OperationType, size_bytes: int = 0) -> None:
        """
        Charge for a kernel operation.

        Args:
            op: The operation type
            size_bytes: Optional size for size-dependent operations
        """
        if not self._enabled:
            return

        # Calculate cost
        cost = op.base_cost
        if size_bytes > 0 and op == OperationType.DEEP_COPY:
            # 5 ticks per 1KB
            cost = max(1, (size_bytes // 1024) * op.base_cost)

        self._state.ticks_consumed += cost
        self._state.operations.append((op.name, cost))

        # v0.2.2: Track per-stage consumption
        if self._state.current_stage:
            stage = self._state.current_stage
            self._state.stage_ticks[stage] = self._state.stage_ticks.get(stage, 0) + cost

        # Check time budget
        if self._state.ticks_consumed > self._limits.time_ticks:
            # v0.2.2: Record which stage caused overflow
            if self._state.current_stage:
                self._state.stage_overflow = self._state.current_stage
            raise TimeBudgetExceeded(
                f"Time budget exceeded: {self._state.ticks_consumed} > {self._limits.time_ticks} ticks"
            )

    def charge_bytes(self, nbytes: int) -> None:
        """Charge for bytes processed."""
        if not self._enabled:
            return

        self._state.bytes_processed += nbytes

        if self._state.bytes_processed > self._limits.max_bytes:
            raise ByteBudgetExceeded(
                f"Byte budget exceeded: {self._state.bytes_processed} > {self._limits.max_bytes} bytes"
            )

    def charge_node(self) -> None:
        """Charge for visiting a node."""
        if not self._enabled:
            return

        self._state.nodes_visited += 1

        if self._state.nodes_visited > self._limits.max_nodes:
            raise NodeBudgetExceeded(
                f"Node budget exceeded: {self._state.nodes_visited} > {self._limits.max_nodes} nodes"
            )

    def charge_work(self, units: int = 1) -> None:
        """Charge for work units (canonicalization, etc)."""
        if not self._enabled:
            return

        self._state.work_units_consumed += units

        if self._state.work_units_consumed > self._limits.max_work_units:
            raise WorkBudgetExceeded(
                f"Work budget exceeded: {self._state.work_units_consumed} > {self._limits.max_work_units} units"
            )

    @contextmanager
    def depth_context(self):
        """Context manager for tracking recursion depth."""
        if not self._enabled:
            yield
            return

        self._state.current_depth += 1
        self._state.max_depth_reached = max(
            self._state.max_depth_reached,
            self._state.current_depth
        )

        if self._state.current_depth > self._limits.max_depth:
            raise DepthBudgetExceeded(
                f"Depth budget exceeded: {self._state.current_depth} > {self._limits.max_depth}"
            )

        try:
            yield
        finally:
            self._state.current_depth -= 1

    @contextmanager
    def stage(self, stage_name: str):
        """
        v0.2.2: Context manager for pipeline stage tracking.

        Tracks per-stage tick consumption and records overflow stage.

        Args:
            stage_name: Must be one of VALID_STAGES (parse, validate, recompose, bind, actuate)
        """
        if stage_name not in self.VALID_STAGES:
            raise ValueError(f"Invalid stage: {stage_name}. Must be one of {self.VALID_STAGES}")

        if not self._enabled:
            yield
            return

        old_stage = self._state.current_stage
        self._state.current_stage = stage_name

        # Initialize stage ticks if needed
        if stage_name not in self._state.stage_ticks:
            self._state.stage_ticks[stage_name] = 0

        try:
            yield
        finally:
            self._state.current_stage = old_stage

    def get_diagnostics(self) -> dict[str, Any]:
        """Get diagnostic information about budget consumption."""
        return {
            "ticks_consumed": self._state.ticks_consumed,
            "ticks_limit": self._limits.time_ticks,
            "ticks_remaining": max(0, self._limits.time_ticks - self._state.ticks_consumed),
            "nodes_visited": self._state.nodes_visited,
            "nodes_limit": self._limits.max_nodes,
            "max_depth_reached": self._state.max_depth_reached,
            "depth_limit": self._limits.max_depth,
            "bytes_processed": self._state.bytes_processed,
            "bytes_limit": self._limits.max_bytes,
            "work_units": self._state.work_units_consumed,
            "work_limit": self._limits.max_work_units,
            "operations": self._state.operations,
            # v0.2.2: Stage tracking
            "stage_ticks": dict(self._state.stage_ticks),
            "stage_overflow": self._state.stage_overflow,
            "harness_enforced": self._harness_enforced,
        }


# Global budget tracker (thread-local in production)
_global_tracker: BudgetTracker | None = None


def get_budget_tracker() -> BudgetTracker:
    """Get the global budget tracker."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = BudgetTracker()
    return _global_tracker


def set_budget_tracker(tracker: BudgetTracker) -> None:
    """Set the global budget tracker."""
    global _global_tracker
    _global_tracker = tracker


def charge(op: OperationType, size_bytes: int = 0) -> None:
    """Convenience function to charge for an operation."""
    get_budget_tracker().charge_operation(op, size_bytes)


def charge_bytes(nbytes: int) -> None:
    """Convenience function to charge for bytes."""
    get_budget_tracker().charge_bytes(nbytes)


def charge_node() -> None:
    """Convenience function to charge for a node."""
    get_budget_tracker().charge_node()


def charge_work(units: int = 1) -> None:
    """Convenience function to charge for work units."""
    get_budget_tracker().charge_work(units)


class BudgetNotEnforcedError(Exception):
    """v0.2.2: Raised when harness budget enforcement is missing."""
    pass


def require_harness_budget() -> None:
    """
    v0.2.2: Assert that harness-level budget is active.

    Raises BudgetNotEnforcedError if no harness budget is set.
    Called by kernel operations to ensure budget is mandatory.
    """
    tracker = get_budget_tracker()
    if not tracker.harness_enforced:
        raise BudgetNotEnforcedError(
            "Operation attempted without harness-level budget enforcement. "
            "All kernel operations must run within a harness_budget_scope."
        )


@contextmanager
def budget_scope(limits: BudgetLimits | None = None):
    """
    Context manager for a budget-limited scope.

    Creates a fresh tracker for the scope and restores the old one after.
    NOTE: This does NOT mark as harness-enforced. Use harness_budget_scope for that.
    """
    global _global_tracker
    old_tracker = _global_tracker

    new_tracker = BudgetTracker(limits)
    _global_tracker = new_tracker

    try:
        yield new_tracker
    finally:
        _global_tracker = old_tracker


@contextmanager
def harness_budget_scope(limits: BudgetLimits | None = None):
    """
    v0.2.2: Mandatory harness-level budget scope.

    Creates a fresh tracker marked as harness-enforced.
    All v0.2.2 experiment runs MUST use this at the boundary.
    """
    global _global_tracker
    old_tracker = _global_tracker

    new_tracker = BudgetTracker(limits)
    new_tracker.set_harness_enforced(True)
    _global_tracker = new_tracker

    try:
        yield new_tracker
    finally:
        _global_tracker = old_tracker
