"""
RSA v0.2 Metrics Module.

Computes Authority Availability (AA), Asymptotic Authority Availability (AAA),
and Recovery Time Distribution (RTD) per Execution Addendum requirements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


# Frozen RTD bucket boundaries
RTD_BUCKETS = [1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
RTD_BUCKET_LABELS = ["1", "2", "3", "5", "10", "20", "50", "100", "200", "500", "1000", "2000", "5000", "INF"]

# Frozen classification thresholds (per docs/rsa_v020_failure_thresholds.md)
# DO NOT MODIFY - these are preregistered for RSA v0.2
AAA_STABLE_THRESHOLD_PPM = 900_000      # AAA >= this -> Stable Authority candidate
AAA_THRASHING_THRESHOLD_PPM = 200_000   # AAA < this + heavy tail -> Structural Thrashing
AAA_DOS_THRESHOLD_PPM = 100_000         # AAA < this -> Asymptotic DoS
HEAVY_LAPSE_DURATION_EPOCHS = 100       # Lapse duration > this is "heavy"


class FailureClass(Enum):
    """Failure classification labels (frozen)."""
    STABLE_AUTHORITY = "STABLE_AUTHORITY"
    BOUNDED_DEGRADATION = "BOUNDED_DEGRADATION"
    STRUCTURAL_THRASHING = "STRUCTURAL_THRASHING"
    ASYMPTOTIC_DOS = "ASYMPTOTIC_DOS"
    TERMINAL_COLLAPSE = "TERMINAL_COLLAPSE"


@dataclass
class LapseInterval:
    """A single lapse (contiguous NULL_AUTHORITY interval)."""
    start_epoch: int
    end_epoch: int  # Exclusive: first epoch after recovery

    @property
    def duration_epochs(self) -> int:
        """Lapse duration in epochs."""
        return self.end_epoch - self.start_epoch


@dataclass
class RSAMetrics:
    """
    Computed RSA v0.2 metrics.

    Attributes:
        horizon_epochs: Total epochs in the run
        authority_epochs: Epochs with active authority
        lapse_epochs: Epochs in NULL_AUTHORITY
        authority_availability_ppm: AA in PPM
        asymptotic_authority_availability_ppm: AAA in PPM
        tail_window_epochs: Size of tail window for AAA
        recovery_time_histogram: RTD bucketed histogram
        lapse_intervals: List of lapse intervals
        failure_class: Classified failure mode
    """
    horizon_epochs: int
    authority_epochs: int
    lapse_epochs: int
    authority_availability_ppm: int
    asymptotic_authority_availability_ppm: int
    tail_window_epochs: int
    recovery_time_histogram: Dict[str, int]
    lapse_intervals: List[LapseInterval]
    failure_class: FailureClass

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "horizon_epochs": self.horizon_epochs,
            "authority_epochs": self.authority_epochs,
            "lapse_epochs": self.lapse_epochs,
            "authority_availability_ppm": self.authority_availability_ppm,
            "asymptotic_authority_availability_ppm": self.asymptotic_authority_availability_ppm,
            "tail_window_epochs": self.tail_window_epochs,
            "recovery_time_histogram": self.recovery_time_histogram,
            "lapse_count": len(self.lapse_intervals),
            "failure_class": self.failure_class.value,
        }


def bucket_recovery_time(duration_epochs: int) -> str:
    """
    Assign a lapse duration to an RTD bucket.

    Frozen buckets: 1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, INF

    Args:
        duration_epochs: Lapse duration in epochs

    Returns:
        Bucket label string
    """
    for i, boundary in enumerate(RTD_BUCKETS):
        if duration_epochs <= boundary:
            return RTD_BUCKET_LABELS[i]
    return "INF"


def compute_tail_window(horizon_epochs: int) -> int:
    """
    Compute AAA tail window size.

    Frozen rule: tail_window = max(5000, horizon_epochs // 5)

    Args:
        horizon_epochs: Total epochs in the run

    Returns:
        Tail window size in epochs
    """
    return max(5000, horizon_epochs // 5)


def extract_lapse_intervals(
    authority_by_epoch: List[bool],
) -> List[LapseInterval]:
    """
    Extract contiguous lapse intervals from authority timeline.

    A lapse is a maximal contiguous interval of NULL_AUTHORITY (False).

    Args:
        authority_by_epoch: List of booleans, True if authority active

    Returns:
        List of LapseInterval objects
    """
    intervals = []
    in_lapse = False
    lapse_start = 0

    for epoch, has_authority in enumerate(authority_by_epoch):
        if not has_authority and not in_lapse:
            # Start of lapse
            in_lapse = True
            lapse_start = epoch
        elif has_authority and in_lapse:
            # End of lapse
            intervals.append(LapseInterval(start_epoch=lapse_start, end_epoch=epoch))
            in_lapse = False

    # Handle lapse extending to end of run
    if in_lapse:
        intervals.append(LapseInterval(
            start_epoch=lapse_start,
            end_epoch=len(authority_by_epoch)
        ))

    return intervals


def compute_rtd_histogram(
    lapse_intervals: List[LapseInterval],
) -> Dict[str, int]:
    """
    Compute Recovery Time Distribution histogram.

    Args:
        lapse_intervals: List of lapse intervals

    Returns:
        Dictionary mapping bucket labels to counts
    """
    histogram = {label: 0 for label in RTD_BUCKET_LABELS}
    for interval in lapse_intervals:
        bucket = bucket_recovery_time(interval.duration_epochs)
        histogram[bucket] += 1
    return histogram


def classify_failure(
    aaa_ppm: int,
    lapse_intervals: List[LapseInterval],
    authority_by_epoch: List[bool],
    tail_window: int,
) -> FailureClass:
    """
    Classify failure mode per frozen rules.

    Classification rules (from spec §12):
    - Stable Authority: AAA high; lapses rare/short; RTD not heavy-tailed
    - Bounded Degradation: AAA reduced but > 0; lapses recur; RTD bounded
    - Structural Thrashing: persistent oscillation; AAA → 0; RTD heavy-tailed
    - Asymptotic DoS: lapse dominance in tail window; recoveries negligible
    - Terminal Collapse: ∃ t* ≤ horizon - tail_window s.t. AUTH = 0 for [t*, horizon)

    Args:
        aaa_ppm: Asymptotic Authority Availability in PPM
        lapse_intervals: List of lapse intervals
        authority_by_epoch: Authority timeline
        tail_window: Tail window size

    Returns:
        FailureClass enum value
    """
    horizon = len(authority_by_epoch)

    # Check Terminal Collapse first (strictest failure mode)
    # ∃ t* ≤ horizon - tail_window s.t. AUTH = 0 for all epoch ∈ [t*, horizon)
    if horizon > tail_window:
        cutoff = horizon - tail_window
        # Check if there's a point from which authority never returns
        for t_star in range(cutoff + 1):
            if all(not auth for auth in authority_by_epoch[t_star:]):
                return FailureClass.TERMINAL_COLLAPSE

    # Count heavy-tailed lapses (duration > HEAVY_LAPSE_DURATION_EPOCHS)
    heavy_lapses = sum(
        1 for lapse in lapse_intervals
        if lapse.duration_epochs > HEAVY_LAPSE_DURATION_EPOCHS
    )
    total_lapses = len(lapse_intervals)

    # Asymptotic DoS: AAA < AAA_DOS_THRESHOLD, but some recoveries exist
    if aaa_ppm < AAA_DOS_THRESHOLD_PPM and total_lapses > 0:
        return FailureClass.ASYMPTOTIC_DOS

    # Structural Thrashing: AAA < AAA_THRASHING_THRESHOLD, heavy-tailed RTD
    if aaa_ppm < AAA_THRASHING_THRESHOLD_PPM and heavy_lapses > 0:
        return FailureClass.STRUCTURAL_THRASHING

    # Bounded Degradation: AAA < AAA_STABLE_THRESHOLD, lapses recur
    if aaa_ppm < AAA_STABLE_THRESHOLD_PPM and total_lapses > 0:
        return FailureClass.BOUNDED_DEGRADATION

    # Stable Authority: high AAA, rare/short lapses
    return FailureClass.STABLE_AUTHORITY


def compute_rsa_metrics(
    authority_by_epoch: List[bool],
) -> RSAMetrics:
    """
    Compute all RSA v0.2 metrics from authority timeline.

    Args:
        authority_by_epoch: List of booleans, True if authority active at epoch

    Returns:
        RSAMetrics with all computed values
    """
    horizon = len(authority_by_epoch)
    if horizon == 0:
        raise ValueError("authority_by_epoch cannot be empty")

    # Compute AA
    authority_epochs = sum(1 for auth in authority_by_epoch if auth)
    lapse_epochs = horizon - authority_epochs
    aa_ppm = (authority_epochs * 1_000_000) // horizon

    # Compute tail window and AAA
    tail_window = compute_tail_window(horizon)
    tail_start = max(0, horizon - tail_window)
    tail_authority = authority_by_epoch[tail_start:]
    if len(tail_authority) > 0:
        tail_authority_count = sum(1 for auth in tail_authority if auth)
        aaa_ppm = (tail_authority_count * 1_000_000) // len(tail_authority)
    else:
        aaa_ppm = aa_ppm  # Fallback if horizon < tail_window

    # Extract lapse intervals and compute RTD
    lapse_intervals = extract_lapse_intervals(authority_by_epoch)
    rtd_histogram = compute_rtd_histogram(lapse_intervals)

    # Classify failure mode
    failure_class = classify_failure(
        aaa_ppm=aaa_ppm,
        lapse_intervals=lapse_intervals,
        authority_by_epoch=authority_by_epoch,
        tail_window=tail_window,
    )

    return RSAMetrics(
        horizon_epochs=horizon,
        authority_epochs=authority_epochs,
        lapse_epochs=lapse_epochs,
        authority_availability_ppm=aa_ppm,
        asymptotic_authority_availability_ppm=aaa_ppm,
        tail_window_epochs=tail_window,
        recovery_time_histogram=rtd_histogram,
        lapse_intervals=lapse_intervals,
        failure_class=failure_class,
    )
