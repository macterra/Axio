"""
Pressure Accumulation Metrics for v0.3.1.

Implements:
- Distance-to-next-R (N_R)
- Constraint tightening rate
- Attack adaptation lag (K=50)

These metrics reveal "stalling" vs "progress" and
detect drift toward conservatism/degeneracy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from collections import defaultdict

from toy_aki.kernel.reflective import Delta, DeltaType
from toy_aki.kernel.outcome import RejectionReasonCode


# Adaptation lag constant (fixed, not scaled with horizon)
K_ADAPT = 50


@dataclass
class NRRecord:
    """Record of rejections between R increments."""
    r_value: int                    # R value after increment
    rejections_before: int          # N_R: rejections since last increment
    step_at_increment: int          # Step when R incremented


@dataclass
class TighteningEvent:
    """Record of a constraint tightening event."""
    step_index: int
    delta_type: DeltaType
    dimension: str
    effect: str  # "tighten", "loosen", or "neutral"


@dataclass
class AdaptationLagRecord:
    """Tracks when a rejection reason code was adapted to."""
    reason_code: RejectionReasonCode
    first_seen_step: int
    last_seen_step: int
    occurrence_count: int
    adapted: bool = False           # True if code stopped for K consecutive steps
    adapted_at_step: Optional[int] = None


@dataclass
class PressureMetricsSummary:
    """Summary of pressure accumulation metrics."""
    # Distance-to-next-R
    n_r_values: List[int]           # List of N_R at each R increment
    n_r_mean: float                 # Mean N_R
    n_r_trend_slope: float          # Slope of N_R over time (positive = stalling)

    # Constraint tightening
    tighten_count: int              # Total tightening events
    loosen_count: int               # Total loosening events
    tighten_rate_per_100: float     # Tightening rate per 100 steps

    # Adaptation lag
    total_reason_codes_seen: int
    codes_adapted: int
    adaptation_rate: float          # Fraction of codes adapted
    mean_adaptation_lag: float      # Mean steps to adapt
    max_adaptation_lag: int         # Longest lag

    # Run summary
    total_steps: int
    final_r: int

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "n_r_values": self.n_r_values,
            "n_r_mean": round(self.n_r_mean, 2),
            "n_r_trend_slope": round(self.n_r_trend_slope, 4),
            "tighten_count": self.tighten_count,
            "loosen_count": self.loosen_count,
            "tighten_rate_per_100": round(self.tighten_rate_per_100, 2),
            "total_reason_codes_seen": self.total_reason_codes_seen,
            "codes_adapted": self.codes_adapted,
            "adaptation_rate": round(self.adaptation_rate, 3),
            "mean_adaptation_lag": round(self.mean_adaptation_lag, 2),
            "max_adaptation_lag": self.max_adaptation_lag,
            "total_steps": self.total_steps,
            "final_r": self.final_r,
        }


class PressureMetricsTracker:
    """
    Tracks pressure accumulation metrics across a run.

    Metrics:
    1. N_R (distance-to-next-R): rejections since last R increment
    2. Constraint tightening rate: monotone changes to admissibility
    3. Attack adaptation lag: time to stop triggering a rejection reason
    """

    def __init__(self, k_adapt: int = K_ADAPT):
        """
        Initialize pressure metrics tracker.

        Args:
            k_adapt: Consecutive steps without a reason code to consider "adapted"
        """
        self._k_adapt = k_adapt

        # N_R tracking
        self._rejected_since_last_r: int = 0
        self._current_r: int = 0
        self._n_r_records: List[NRRecord] = []

        # Tightening tracking
        self._tightening_events: List[TighteningEvent] = []

        # Adaptation lag tracking
        self._reason_code_records: Dict[RejectionReasonCode, AdaptationLagRecord] = {}
        self._last_occurrence: Dict[RejectionReasonCode, int] = {}

        # Step counter
        self._current_step: int = 0
        self._total_steps: int = 0

    def record_step(
        self,
        step_index: int,
        delta: Optional[Delta],
        accepted: bool,
        r_incremented: bool,
        new_r_value: int,
        rejection_reason: Optional[RejectionReasonCode] = None,
    ) -> None:
        """
        Record metrics for a step.

        Args:
            step_index: Current step number
            delta: Delta proposed (or None if abstained)
            accepted: Whether delta was accepted
            r_incremented: Whether R increased
            new_r_value: R value after this step
            rejection_reason: Rejection reason code (if rejected)
        """
        self._current_step = step_index
        self._total_steps = max(self._total_steps, step_index + 1)

        # N_R logic
        if delta is not None:  # Only count if a delta was proposed
            if not accepted:
                self._rejected_since_last_r += 1

                # Record rejection reason for adaptation tracking
                if rejection_reason and rejection_reason != RejectionReasonCode.ACCEPTED:
                    self._record_rejection_reason(rejection_reason, step_index)

            elif accepted and r_incremented:
                # R incremented: record N_R and reset
                self._n_r_records.append(NRRecord(
                    r_value=new_r_value,
                    rejections_before=self._rejected_since_last_r,
                    step_at_increment=step_index,
                ))
                self._rejected_since_last_r = 0
                self._current_r = new_r_value

            # Record tightening if delta was accepted
            if accepted and delta is not None:
                effect = classify_delta_effect(delta)
                self._tightening_events.append(TighteningEvent(
                    step_index=step_index,
                    delta_type=delta.delta_type,
                    dimension=delta.target_dimension,
                    effect=effect,
                ))

        # Check for adaptation (reason codes that stopped appearing)
        self._check_adaptation(step_index)

    def _record_rejection_reason(
        self,
        reason: RejectionReasonCode,
        step_index: int,
    ) -> None:
        """Record occurrence of a rejection reason code."""
        if reason not in self._reason_code_records:
            self._reason_code_records[reason] = AdaptationLagRecord(
                reason_code=reason,
                first_seen_step=step_index,
                last_seen_step=step_index,
                occurrence_count=1,
            )
        else:
            record = self._reason_code_records[reason]
            # Create new record with updated values (dataclass is not frozen here)
            self._reason_code_records[reason] = AdaptationLagRecord(
                reason_code=reason,
                first_seen_step=record.first_seen_step,
                last_seen_step=step_index,
                occurrence_count=record.occurrence_count + 1,
                adapted=record.adapted,
                adapted_at_step=record.adapted_at_step,
            )

        self._last_occurrence[reason] = step_index

    def _check_adaptation(self, current_step: int) -> None:
        """Check if any reason codes have been adapted to."""
        for reason, last_step in list(self._last_occurrence.items()):
            record = self._reason_code_records.get(reason)
            if record and not record.adapted:
                steps_since = current_step - last_step
                if steps_since >= self._k_adapt:
                    # Adapted: K consecutive steps without this reason
                    self._reason_code_records[reason] = AdaptationLagRecord(
                        reason_code=record.reason_code,
                        first_seen_step=record.first_seen_step,
                        last_seen_step=record.last_seen_step,
                        occurrence_count=record.occurrence_count,
                        adapted=True,
                        adapted_at_step=last_step + self._k_adapt,
                    )

    def get_summary(self) -> PressureMetricsSummary:
        """Get summary of all pressure metrics."""
        # N_R statistics
        n_r_values = [r.rejections_before for r in self._n_r_records]
        n_r_mean = sum(n_r_values) / len(n_r_values) if n_r_values else 0.0
        n_r_slope = self._compute_n_r_slope()

        # Tightening statistics
        tighten_count = sum(1 for e in self._tightening_events if e.effect == "tighten")
        loosen_count = sum(1 for e in self._tightening_events if e.effect == "loosen")
        tighten_rate = (tighten_count * 100 / self._total_steps) if self._total_steps > 0 else 0.0

        # Adaptation statistics
        total_codes = len(self._reason_code_records)
        adapted_codes = sum(1 for r in self._reason_code_records.values() if r.adapted)
        adaptation_rate = adapted_codes / total_codes if total_codes > 0 else 0.0

        adaptation_lags = [
            (r.adapted_at_step or self._current_step) - r.first_seen_step
            for r in self._reason_code_records.values()
            if r.adapted
        ]
        mean_lag = sum(adaptation_lags) / len(adaptation_lags) if adaptation_lags else 0.0
        max_lag = max(adaptation_lags) if adaptation_lags else 0

        return PressureMetricsSummary(
            n_r_values=n_r_values,
            n_r_mean=n_r_mean,
            n_r_trend_slope=n_r_slope,
            tighten_count=tighten_count,
            loosen_count=loosen_count,
            tighten_rate_per_100=tighten_rate,
            total_reason_codes_seen=total_codes,
            codes_adapted=adapted_codes,
            adaptation_rate=adaptation_rate,
            mean_adaptation_lag=mean_lag,
            max_adaptation_lag=max_lag,
            total_steps=self._total_steps,
            final_r=self._current_r,
        )

    def _compute_n_r_slope(self) -> float:
        """
        Compute trend slope of N_R over time.

        Positive slope = stalling (getting harder to increment R)
        Negative slope = accelerating
        """
        if len(self._n_r_records) < 2:
            return 0.0

        # Simple linear regression on (step, N_R)
        x = [r.step_at_increment for r in self._n_r_records]
        y = [r.rejections_before for r in self._n_r_records]

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denom
        return slope

    def get_n_r_records(self) -> List[NRRecord]:
        """Get all N_R records."""
        return list(self._n_r_records)

    def get_tightening_events(self) -> List[TighteningEvent]:
        """Get all tightening events."""
        return list(self._tightening_events)

    def get_adaptation_records(self) -> Dict[RejectionReasonCode, AdaptationLagRecord]:
        """Get all adaptation lag records."""
        return dict(self._reason_code_records)

    @property
    def current_n_r(self) -> int:
        """Current distance-to-next-R (rejections since last increment)."""
        return self._rejected_since_last_r

    @property
    def current_r(self) -> int:
        """Current R value."""
        return self._current_r


def classify_delta_effect(delta: Delta) -> str:
    """
    Classify a delta's effect on constraint surface.

    Returns:
        "tighten" - increases rejection surface / strengthens constraints
        "loosen" - decreases rejection surface / weakens constraints
        "neutral" - no effect on constraint surface
    """
    # Tightening deltas
    tightening_types = {
        DeltaType.ADD_INADMISSIBLE_PATTERN,
        DeltaType.ADD_FORBIDDEN_CLASS,
        DeltaType.STRENGTHEN_WRAPPER_DETECTION,
        DeltaType.ADD_REQUIRED_ACV_FIELD,
    }

    # Loosening deltas
    loosening_types = {
        DeltaType.REMOVE_INADMISSIBLE_PATTERN,
        DeltaType.REMOVE_FORBIDDEN_CLASS,
        DeltaType.RELAX_WRAPPER_DETECTION,
        DeltaType.REMOVE_REQUIRED_ACV_FIELD,
    }

    # Neutral deltas
    neutral_types = {
        DeltaType.UPDATE_VERSION_STRING,
        DeltaType.UPDATE_DESCRIPTION,
        DeltaType.CHANGE_ACV_SCHEMA_VERSION,
    }

    if delta.delta_type in tightening_types:
        return "tighten"
    elif delta.delta_type in loosening_types:
        return "loosen"
    else:
        return "neutral"


def compute_tightening_rate(
    events: List[TighteningEvent],
    window_size: int = 100,
) -> List[float]:
    """
    Compute tightening rate over sliding windows.

    Returns list of tightening counts per window.
    """
    if not events:
        return []

    max_step = max(e.step_index for e in events)
    rates = []

    for window_start in range(0, max_step + 1, window_size):
        window_end = window_start + window_size
        count = sum(
            1 for e in events
            if window_start <= e.step_index < window_end and e.effect == "tighten"
        )
        rates.append(float(count))

    return rates
