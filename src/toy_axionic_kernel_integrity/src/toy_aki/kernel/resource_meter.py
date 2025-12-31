"""
Resource Meter for v0.3.1 Resource/Effort Accounting.

Records:
- Wall-clock time per step
- Delta synthesis time (optimizer proposal generation)
- Peak memory (process RSS)

Used for v0.3.1.c "unbounded compute measured" variant.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator, List, Optional

# Try to import psutil for memory measurement; fallback to resource
_PSUTIL_AVAILABLE = False
_RESOURCE_AVAILABLE = False

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    pass

if not _PSUTIL_AVAILABLE:
    try:
        import resource
        _RESOURCE_AVAILABLE = True
    except ImportError:
        pass


def get_memory_usage_bytes() -> int:
    """
    Get current process memory usage in bytes.

    Uses psutil if available, falls back to resource.getrusage.
    Returns 0 if neither is available.
    """
    if _PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            return process.memory_info().rss
        except Exception:
            return 0

    if _RESOURCE_AVAILABLE:
        try:
            # ru_maxrss is in KB on Linux, bytes on macOS
            import platform
            usage = resource.getrusage(resource.RUSAGE_SELF)
            if platform.system() == "Darwin":
                return usage.ru_maxrss
            else:
                return usage.ru_maxrss * 1024
        except Exception:
            return 0

    return 0


@dataclass
class StepResourceRecord:
    """Resource measurements for a single step."""
    step_index: int
    step_time_ms: float          # Total step wall-clock time
    delta_synthesis_time_ms: float  # Optimizer proposal generation time
    memory_bytes: int            # Memory at end of step
    memory_peak_bytes: int       # Peak memory so far


@dataclass
class ResourceSummary:
    """Summary of resource usage across a run."""
    total_steps: int
    total_time_ms: float
    mean_step_time_ms: float
    max_step_time_ms: float
    min_step_time_ms: float

    total_synthesis_time_ms: float
    mean_synthesis_time_ms: float
    max_synthesis_time_ms: float

    final_memory_bytes: int
    peak_memory_bytes: int

    memory_available: bool  # Whether memory measurement is available

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "total_steps": self.total_steps,
            "total_time_ms": round(self.total_time_ms, 2),
            "mean_step_time_ms": round(self.mean_step_time_ms, 4),
            "max_step_time_ms": round(self.max_step_time_ms, 4),
            "min_step_time_ms": round(self.min_step_time_ms, 4),
            "total_synthesis_time_ms": round(self.total_synthesis_time_ms, 2),
            "mean_synthesis_time_ms": round(self.mean_synthesis_time_ms, 4),
            "max_synthesis_time_ms": round(self.max_synthesis_time_ms, 4),
            "final_memory_bytes": self.final_memory_bytes,
            "peak_memory_bytes": self.peak_memory_bytes,
            "memory_available": self.memory_available,
        }


class ResourceMeter:
    """
    Resource meter for v0.3.1 effort accounting.

    Tracks wall-clock time, synthesis time, and memory usage.
    Can optionally enforce caps (for variants with budget limits).
    """

    def __init__(
        self,
        enforce_caps: bool = False,
        max_step_time_ms: Optional[float] = None,
        max_total_time_ms: Optional[float] = None,
        max_memory_bytes: Optional[int] = None,
    ):
        """
        Initialize resource meter.

        Args:
            enforce_caps: If True, raise exceptions when caps exceeded.
                         If False, only record (v0.3.1.c mode).
            max_step_time_ms: Cap on per-step time (if enforced)
            max_total_time_ms: Cap on total run time (if enforced)
            max_memory_bytes: Cap on peak memory (if enforced)
        """
        self._enforce_caps = enforce_caps
        self._max_step_time_ms = max_step_time_ms
        self._max_total_time_ms = max_total_time_ms
        self._max_memory_bytes = max_memory_bytes

        self._records: List[StepResourceRecord] = []
        self._peak_memory_bytes = 0
        self._total_time_ms = 0.0
        self._run_start_time: Optional[float] = None

        self._current_step_start: Optional[float] = None
        self._current_step_index = 0

        self._synthesis_start: Optional[float] = None
        self._current_synthesis_time_ms = 0.0

    def start_run(self) -> None:
        """Mark the start of a run."""
        self._run_start_time = time.perf_counter()
        self._records = []
        self._peak_memory_bytes = get_memory_usage_bytes()
        self._total_time_ms = 0.0
        self._current_step_index = 0

    def start_step(self, step_index: int) -> None:
        """Mark the start of a step."""
        self._current_step_index = step_index
        self._current_step_start = time.perf_counter()
        self._current_synthesis_time_ms = 0.0

    @contextmanager
    def measure_synthesis(self) -> Iterator[None]:
        """Context manager to measure delta synthesis time."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._current_synthesis_time_ms += elapsed_ms

    def end_step(self) -> StepResourceRecord:
        """
        Mark the end of a step and record measurements.

        Returns:
            StepResourceRecord for this step

        Raises:
            ResourceBudgetExceeded: If enforce_caps=True and cap exceeded
        """
        if self._current_step_start is None:
            raise RuntimeError("end_step called without start_step")

        step_time_ms = (time.perf_counter() - self._current_step_start) * 1000
        self._total_time_ms += step_time_ms

        current_memory = get_memory_usage_bytes()
        if current_memory > self._peak_memory_bytes:
            self._peak_memory_bytes = current_memory

        record = StepResourceRecord(
            step_index=self._current_step_index,
            step_time_ms=step_time_ms,
            delta_synthesis_time_ms=self._current_synthesis_time_ms,
            memory_bytes=current_memory,
            memory_peak_bytes=self._peak_memory_bytes,
        )
        self._records.append(record)

        # Check caps if enforcing
        if self._enforce_caps:
            self._check_caps(record)

        self._current_step_start = None
        return record

    def _check_caps(self, record: StepResourceRecord) -> None:
        """Check and enforce resource caps."""
        if self._max_step_time_ms and record.step_time_ms > self._max_step_time_ms:
            raise ResourceBudgetExceeded(
                f"Step time {record.step_time_ms:.2f}ms exceeds cap {self._max_step_time_ms}ms"
            )

        if self._max_total_time_ms and self._total_time_ms > self._max_total_time_ms:
            raise ResourceBudgetExceeded(
                f"Total time {self._total_time_ms:.2f}ms exceeds cap {self._max_total_time_ms}ms"
            )

        if self._max_memory_bytes and self._peak_memory_bytes > self._max_memory_bytes:
            raise ResourceBudgetExceeded(
                f"Peak memory {self._peak_memory_bytes} bytes exceeds cap {self._max_memory_bytes}"
            )

    def get_summary(self) -> ResourceSummary:
        """Get summary of resource usage."""
        if not self._records:
            return ResourceSummary(
                total_steps=0,
                total_time_ms=0.0,
                mean_step_time_ms=0.0,
                max_step_time_ms=0.0,
                min_step_time_ms=0.0,
                total_synthesis_time_ms=0.0,
                mean_synthesis_time_ms=0.0,
                max_synthesis_time_ms=0.0,
                final_memory_bytes=0,
                peak_memory_bytes=0,
                memory_available=_PSUTIL_AVAILABLE or _RESOURCE_AVAILABLE,
            )

        step_times = [r.step_time_ms for r in self._records]
        synthesis_times = [r.delta_synthesis_time_ms for r in self._records]

        return ResourceSummary(
            total_steps=len(self._records),
            total_time_ms=self._total_time_ms,
            mean_step_time_ms=sum(step_times) / len(step_times),
            max_step_time_ms=max(step_times),
            min_step_time_ms=min(step_times),
            total_synthesis_time_ms=sum(synthesis_times),
            mean_synthesis_time_ms=sum(synthesis_times) / len(synthesis_times),
            max_synthesis_time_ms=max(synthesis_times),
            final_memory_bytes=self._records[-1].memory_bytes if self._records else 0,
            peak_memory_bytes=self._peak_memory_bytes,
            memory_available=_PSUTIL_AVAILABLE or _RESOURCE_AVAILABLE,
        )

    def get_records(self) -> List[StepResourceRecord]:
        """Get all step records."""
        return list(self._records)

    @property
    def peak_memory_bytes(self) -> int:
        """Get peak memory usage so far."""
        return self._peak_memory_bytes

    @property
    def total_time_ms(self) -> float:
        """Get total elapsed time so far."""
        return self._total_time_ms

    @property
    def enforce_caps(self) -> bool:
        """Whether caps are being enforced."""
        return self._enforce_caps


class ResourceBudgetExceeded(Exception):
    """Raised when a resource cap is exceeded (if enforcement is enabled)."""
    pass


def memory_measurement_available() -> bool:
    """Check if memory measurement is available."""
    return _PSUTIL_AVAILABLE or _RESOURCE_AVAILABLE


def memory_measurement_method() -> str:
    """Get the method being used for memory measurement."""
    if _PSUTIL_AVAILABLE:
        return "psutil"
    elif _RESOURCE_AVAILABLE:
        return "resource.getrusage"
    else:
        return "none"
