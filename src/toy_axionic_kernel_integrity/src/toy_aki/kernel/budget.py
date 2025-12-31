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

    def reset(self) -> None:
        """Reset all counters."""
        self.ticks_consumed = 0
        self.nodes_visited = 0
        self.current_depth = 0
        self.max_depth_reached = 0
        self.bytes_processed = 0
        self.work_units_consumed = 0
        self.operations = []


class BudgetTracker:
    """
    Tracks and enforces deterministic budgets.

    All operations must be tracked through this class.
    Exceeding any limit raises the appropriate exception.
    """

    def __init__(self, limits: BudgetLimits | None = None):
        self._limits = limits or BudgetLimits()
        self._state = BudgetState()
        self._enabled = True

    @property
    def limits(self) -> BudgetLimits:
        return self._limits

    @property
    def state(self) -> BudgetState:
        return self._state

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

        # Check time budget
        if self._state.ticks_consumed > self._limits.time_ticks:
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


@contextmanager
def budget_scope(limits: BudgetLimits | None = None):
    """
    Context manager for a budget-limited scope.

    Creates a fresh tracker for the scope and restores the old one after.
    """
    global _global_tracker
    old_tracker = _global_tracker

    new_tracker = BudgetTracker(limits)
    _global_tracker = new_tracker

    try:
        yield new_tracker
    finally:
        _global_tracker = old_tracker
