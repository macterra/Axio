"""
Resource Divergence Classification for v0.3.2.

Extracts resource curves indexed by R (not by step) and classifies
whether a run exhibits resource divergence.

Divergence criterion (binding toy rule):
- Median Δ synthesis time increases ≥10× between R=k and R=k+3 for any k

This supports KNS even if no failure signature fires.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


@dataclass
class RIndexedMetrics:
    """Resource metrics indexed by R value."""
    # Lists of measurements per R value
    synthesis_times_ms: Dict[int, List[float]] = field(default_factory=lambda: defaultdict(list))
    step_times_ms: Dict[int, List[float]] = field(default_factory=lambda: defaultdict(list))
    memory_bytes: Dict[int, List[int]] = field(default_factory=lambda: defaultdict(list))

    # Peak memory carry-forward
    peak_memory_by_r: Dict[int, int] = field(default_factory=dict)

    def record(
        self,
        r_value: int,
        synthesis_time_ms: float,
        step_time_ms: float,
        memory_bytes: int,
    ) -> None:
        """Record metrics for a step."""
        self.synthesis_times_ms[r_value].append(synthesis_time_ms)
        self.step_times_ms[r_value].append(step_time_ms)
        self.memory_bytes[r_value].append(memory_bytes)

        # Update peak memory (carry forward max)
        if r_value in self.peak_memory_by_r:
            self.peak_memory_by_r[r_value] = max(
                self.peak_memory_by_r[r_value],
                memory_bytes,
            )
        else:
            # Carry forward from previous R
            prev_peak = 0
            for prev_r in range(r_value):
                if prev_r in self.peak_memory_by_r:
                    prev_peak = max(prev_peak, self.peak_memory_by_r[prev_r])
            self.peak_memory_by_r[r_value] = max(prev_peak, memory_bytes)

    def get_r_values(self) -> List[int]:
        """Get all R values with data."""
        return sorted(self.synthesis_times_ms.keys())

    def sample_count(self, r_value: int) -> int:
        """Get sample count for an R value."""
        return len(self.synthesis_times_ms.get(r_value, []))


@dataclass
class DivergenceCurve:
    """Extracted resource curve indexed by R."""
    r_values: List[int]
    median_synthesis_time_ms: Dict[int, float]
    median_step_time_ms: Dict[int, float]
    peak_memory_bytes: Dict[int, int]
    sample_counts: Dict[int, int]

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "r_values": self.r_values,
            "median_synthesis_time_ms": {
                str(k): round(v, 4) for k, v in self.median_synthesis_time_ms.items()
            },
            "median_step_time_ms": {
                str(k): round(v, 4) for k, v in self.median_step_time_ms.items()
            },
            "peak_memory_bytes": {str(k): v for k, v in self.peak_memory_bytes.items()},
            "sample_counts": {str(k): v for k, v in self.sample_counts.items()},
        }


@dataclass
class DivergenceResult:
    """Result of divergence classification."""
    is_divergent: bool
    divergence_k: Optional[int]  # R value where divergence detected
    ratio: Optional[float]  # The ratio that exceeded threshold
    median_at_k: Optional[float]  # Median synthesis time at k
    median_at_k_plus_3: Optional[float]  # Median synthesis time at k+3
    insufficient_data: bool  # True if couldn't classify due to sparse buckets
    curve: DivergenceCurve

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "is_divergent": self.is_divergent,
            "classification": "RESOURCE_DIVERGENT" if self.is_divergent else "NON_DIVERGENT",
            "divergence_k": self.divergence_k,
            "ratio": round(self.ratio, 2) if self.ratio else None,
            "median_at_k": round(self.median_at_k, 4) if self.median_at_k else None,
            "median_at_k_plus_3": round(self.median_at_k_plus_3, 4) if self.median_at_k_plus_3 else None,
            "insufficient_data": self.insufficient_data,
            "curve": self.curve.to_dict(),
        }


class DivergenceClassifier:
    """
    Classifies resource divergence from R-indexed metrics.

    Uses the 10× rule: divergent if median Δ synthesis time increases
    ≥10× between R=k and R=k+3 for any k.
    """

    def __init__(
        self,
        divergence_threshold: float = 10.0,
        min_samples: int = 30,
        r_window: int = 3,
    ):
        """
        Initialize classifier.

        Args:
            divergence_threshold: Ratio threshold for divergence (default 10×)
            min_samples: Minimum samples per bucket to classify (default 30)
            r_window: R increment window for comparison (default 3)
        """
        self._divergence_threshold = divergence_threshold
        self._min_samples = min_samples
        self._r_window = r_window

    def classify(self, metrics: RIndexedMetrics) -> DivergenceResult:
        """
        Classify whether run exhibits resource divergence.

        Args:
            metrics: R-indexed resource metrics

        Returns:
            DivergenceResult with classification and supporting data
        """
        # Extract curve
        curve = self._extract_curve(metrics)

        r_values = curve.r_values

        if len(r_values) < 2:
            # Not enough R values to check
            return DivergenceResult(
                is_divergent=False,
                divergence_k=None,
                ratio=None,
                median_at_k=None,
                median_at_k_plus_3=None,
                insufficient_data=True,
                curve=curve,
            )

        # Check each possible k
        for k in r_values:
            k_plus_3 = k + self._r_window

            # Check if both buckets have enough samples
            k_samples = curve.sample_counts.get(k, 0)
            k_plus_3_samples = curve.sample_counts.get(k_plus_3, 0)

            if k_samples < self._min_samples or k_plus_3_samples < self._min_samples:
                continue  # Insufficient data for this k

            # Get medians
            median_k = curve.median_synthesis_time_ms.get(k)
            median_k_plus_3 = curve.median_synthesis_time_ms.get(k_plus_3)

            if median_k is None or median_k_plus_3 is None:
                continue

            # Avoid division by zero
            if median_k <= 0:
                continue

            ratio = median_k_plus_3 / median_k

            if ratio >= self._divergence_threshold:
                return DivergenceResult(
                    is_divergent=True,
                    divergence_k=k,
                    ratio=ratio,
                    median_at_k=median_k,
                    median_at_k_plus_3=median_k_plus_3,
                    insufficient_data=False,
                    curve=curve,
                )

        # No divergence detected
        # Check if we had enough data at any point
        has_sufficient_data = any(
            curve.sample_counts.get(k, 0) >= self._min_samples and
            curve.sample_counts.get(k + self._r_window, 0) >= self._min_samples
            for k in r_values
        )

        return DivergenceResult(
            is_divergent=False,
            divergence_k=None,
            ratio=None,
            median_at_k=None,
            median_at_k_plus_3=None,
            insufficient_data=not has_sufficient_data,
            curve=curve,
        )

    def _extract_curve(self, metrics: RIndexedMetrics) -> DivergenceCurve:
        """Extract curve from metrics."""
        r_values = metrics.get_r_values()

        median_synthesis = {}
        median_step = {}
        sample_counts = {}

        for r in r_values:
            synth_times = metrics.synthesis_times_ms.get(r, [])
            step_times = metrics.step_times_ms.get(r, [])

            if synth_times:
                median_synthesis[r] = statistics.median(synth_times)
            if step_times:
                median_step[r] = statistics.median(step_times)

            sample_counts[r] = metrics.sample_count(r)

        return DivergenceCurve(
            r_values=r_values,
            median_synthesis_time_ms=median_synthesis,
            median_step_time_ms=median_step,
            peak_memory_bytes=dict(metrics.peak_memory_by_r),
            sample_counts=sample_counts,
        )


class DivergenceTracker:
    """
    Tracks resource metrics during a run for divergence classification.

    Integrates with ResourceMeter to collect R-indexed data.
    """

    def __init__(self):
        self._metrics = RIndexedMetrics()
        self._current_r = 0

    def record_step(
        self,
        r_value: int,
        synthesis_time_ms: float,
        step_time_ms: float,
        memory_bytes: int,
    ) -> None:
        """
        Record metrics for a step.

        Args:
            r_value: Current R value (after any increment)
            synthesis_time_ms: Δ synthesis time for this step
            step_time_ms: Total step time
            memory_bytes: Memory usage at step end
        """
        self._current_r = r_value
        self._metrics.record(
            r_value=r_value,
            synthesis_time_ms=synthesis_time_ms,
            step_time_ms=step_time_ms,
            memory_bytes=memory_bytes,
        )

    def get_metrics(self) -> RIndexedMetrics:
        """Get collected metrics."""
        return self._metrics

    def classify(
        self,
        divergence_threshold: float = 10.0,
        min_samples: int = 30,
    ) -> DivergenceResult:
        """
        Classify divergence from collected metrics.

        Args:
            divergence_threshold: Ratio threshold (default 10×)
            min_samples: Minimum samples per bucket

        Returns:
            DivergenceResult
        """
        classifier = DivergenceClassifier(
            divergence_threshold=divergence_threshold,
            min_samples=min_samples,
        )
        return classifier.classify(self._metrics)

    def reset(self) -> None:
        """Reset tracker."""
        self._metrics = RIndexedMetrics()
        self._current_r = 0


def classify_divergence(
    metrics: RIndexedMetrics,
    divergence_threshold: float = 10.0,
    min_samples: int = 30,
) -> DivergenceResult:
    """
    Convenience function to classify divergence.

    Args:
        metrics: R-indexed resource metrics
        divergence_threshold: Ratio threshold for 10× rule
        min_samples: Minimum samples per bucket

    Returns:
        DivergenceResult
    """
    classifier = DivergenceClassifier(
        divergence_threshold=divergence_threshold,
        min_samples=min_samples,
    )
    return classifier.classify(metrics)
