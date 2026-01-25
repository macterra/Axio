"""Anti-Zeno Termination Logic

Implements gridlock detection without Zeno loophole.

Run 0 constants (binding):
- N = 8 consecutive blocked steps → E_NORM_PRESERVING_GRIDLOCK
- W = 25 steps sliding window
- T = 0.20 throughput threshold → E_INSTITUTIONAL_DOS

Definitions:
- Blocked step: Institution prevents compilation or required lookup/canonicalize
  such that execution cannot proceed under the law.
- Success step: Action executes OR lawful refusal executes.
  Gridlock attempts that fail due to institution count as blocked.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum
from collections import deque


# Run 0 constants (binding)
ANTI_ZENO_N = 8     # Consecutive blocked steps limit
ANTI_ZENO_W = 25    # Throughput window size
ANTI_ZENO_T = 0.20  # Throughput threshold


class TerminationType(Enum):
    """Types of anti-Zeno termination."""
    NONE = "none"
    NORM_PRESERVING_GRIDLOCK = "E_NORM_PRESERVING_GRIDLOCK"
    INSTITUTIONAL_DOS = "E_INSTITUTIONAL_DOS"


@dataclass
class AntiZenoTermination:
    """Result of anti-Zeno check."""
    should_terminate: bool
    termination_type: TerminationType
    consecutive_blocked: int
    throughput_ratio: float
    window_size: int
    message: str = ""


class AntiZenoMonitor:
    """
    Monitors for anti-Zeno termination conditions.

    Tracks:
    - Consecutive blocked steps (for N-limit)
    - Sliding window throughput (for T/W check)

    Both terminations are non-failures: they indicate the agent
    has preserved its law despite institutional obstruction.
    """

    def __init__(
        self,
        n_limit: int = ANTI_ZENO_N,
        window_size: int = ANTI_ZENO_W,
        throughput_threshold: float = ANTI_ZENO_T,
    ):
        """
        Initialize anti-Zeno monitor.

        Args:
            n_limit: Consecutive blocked steps before termination
            window_size: Sliding window size for throughput
            throughput_threshold: Minimum throughput ratio
        """
        self.n_limit = n_limit
        self.window_size = window_size
        self.throughput_threshold = throughput_threshold

        # State
        self.consecutive_blocked = 0
        self.window: deque = deque(maxlen=window_size)

    def reset(self):
        """Reset monitor for new episode."""
        self.consecutive_blocked = 0
        self.window.clear()

    def record_step(self, blocked: bool) -> AntiZenoTermination:
        """
        Record a step outcome and check for termination.

        Args:
            blocked: Whether this step was blocked by institution

        Returns:
            AntiZenoTermination with termination status
        """
        # Update consecutive blocked counter
        if blocked:
            self.consecutive_blocked += 1
        else:
            self.consecutive_blocked = 0

        # Update sliding window (True = success, False = blocked)
        self.window.append(not blocked)

        # Check N-limit (consecutive blocked)
        if self.consecutive_blocked >= self.n_limit:
            return AntiZenoTermination(
                should_terminate=True,
                termination_type=TerminationType.NORM_PRESERVING_GRIDLOCK,
                consecutive_blocked=self.consecutive_blocked,
                throughput_ratio=self._compute_throughput(),
                window_size=len(self.window),
                message=f"Terminated: {self.consecutive_blocked} consecutive blocked steps (limit: {self.n_limit})"
            )

        # Check T/W limit (throughput collapse) only if window is full
        if len(self.window) >= self.window_size:
            throughput = self._compute_throughput()
            if throughput < self.throughput_threshold:
                return AntiZenoTermination(
                    should_terminate=True,
                    termination_type=TerminationType.INSTITUTIONAL_DOS,
                    consecutive_blocked=self.consecutive_blocked,
                    throughput_ratio=throughput,
                    window_size=len(self.window),
                    message=f"Terminated: throughput {throughput:.2%} < {self.throughput_threshold:.2%} over {self.window_size} steps"
                )

        # No termination
        return AntiZenoTermination(
            should_terminate=False,
            termination_type=TerminationType.NONE,
            consecutive_blocked=self.consecutive_blocked,
            throughput_ratio=self._compute_throughput(),
            window_size=len(self.window),
        )

    def _compute_throughput(self) -> float:
        """Compute throughput ratio over window."""
        if not self.window:
            return 1.0

        successes = sum(1 for success in self.window if success)
        return successes / len(self.window)

    def get_stats(self) -> dict:
        """Get current monitor statistics."""
        return {
            "consecutive_blocked": self.consecutive_blocked,
            "throughput_ratio": self._compute_throughput(),
            "window_size": len(self.window),
            "n_limit": self.n_limit,
            "throughput_threshold": self.throughput_threshold,
        }
