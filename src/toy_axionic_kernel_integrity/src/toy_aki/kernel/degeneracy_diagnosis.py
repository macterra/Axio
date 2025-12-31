"""
Degeneracy Diagnosis for v0.3.2.

Classifies dominant rejection causes during stalling/degeneracy:
- CONSERVATIVE_LOCKIN: >80% INADMISSIBLE_P5, positive tightening rate
- EVALUABILITY_BOTTLENECK: majority KNS-E rejections or high near-failure saturation
- DELTA_LANGUAGE_INSUFFICIENCY: majority delta format/application errors
- MIXED_OR_UNKNOWN: none of the above

This diagnosis is descriptive, not normative.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional
from collections import Counter

from toy_aki.kernel.outcome import (
    DeltaOutcome,
    RejectionReasonCode,
    NearFailureFlag,
)


class DegeneracyDiagnosis(Enum):
    """Classification of degeneracy cause."""
    CONSERVATIVE_LOCKIN = auto()
    EVALUABILITY_BOTTLENECK = auto()
    DELTA_LANGUAGE_INSUFFICIENCY = auto()
    MIXED_OR_UNKNOWN = auto()

    def description(self) -> str:
        """Human-readable description."""
        if self == DegeneracyDiagnosis.CONSERVATIVE_LOCKIN:
            return "Conservative lock-in: >80% INADMISSIBLE_P5 rejections with positive tightening rate"
        elif self == DegeneracyDiagnosis.EVALUABILITY_BOTTLENECK:
            return "Evaluability bottleneck: majority KNS-E rejections or high near-failure saturation"
        elif self == DegeneracyDiagnosis.DELTA_LANGUAGE_INSUFFICIENCY:
            return "Delta language insufficiency: majority delta format/application errors"
        else:
            return "Mixed or unknown: no dominant cause identified"


@dataclass
class DegeneracyDiagnosisResult:
    """Result of degeneracy diagnosis."""
    diagnosis: DegeneracyDiagnosis

    # Metrics used for diagnosis
    total_steps: int
    rejection_count: int
    rejection_rate: float

    # Rejection reason breakdown
    reason_histogram: Dict[str, int]
    top_reason: Optional[RejectionReasonCode]
    top_reason_fraction: float

    # Specific metrics
    inadmissible_p5_fraction: float
    evaluability_fraction: float
    delta_error_fraction: float

    # Tightening rate
    tightening_rate: float

    # Near-failure saturation
    near_failure_saturation: float

    def to_dict(self) -> dict:
        """Convert to dictionary for reporting."""
        return {
            "diagnosis": self.diagnosis.name,
            "description": self.diagnosis.description(),
            "total_steps": self.total_steps,
            "rejection_count": self.rejection_count,
            "rejection_rate": round(self.rejection_rate, 3),
            "reason_histogram": self.reason_histogram,
            "top_reason": self.top_reason.name if self.top_reason else None,
            "top_reason_fraction": round(self.top_reason_fraction, 3),
            "inadmissible_p5_fraction": round(self.inadmissible_p5_fraction, 3),
            "evaluability_fraction": round(self.evaluability_fraction, 3),
            "delta_error_fraction": round(self.delta_error_fraction, 3),
            "tightening_rate": round(self.tightening_rate, 4),
            "near_failure_saturation": round(self.near_failure_saturation, 3),
        }


# Reason codes classified as KNS-E related
EVALUABILITY_REASON_CODES = {
    RejectionReasonCode.EVALUABILITY_ATTRIBUTION_FAIL,
    RejectionReasonCode.EVALUABILITY_REJECTION_FAIL,
    RejectionReasonCode.EVALUABILITY_REJECTION_CHAIN_FAIL,
    RejectionReasonCode.EVALUABILITY_DELEGATION_DETECT_FAIL,
}

# Reason codes classified as delta language errors
DELTA_ERROR_REASON_CODES = {
    RejectionReasonCode.DELTA_INVALID_FORMAT,
    RejectionReasonCode.DELTA_APPLICATION_ERROR,
    RejectionReasonCode.DELTA_PAYLOAD_ERROR,
}


class DegeneracyDiagnoser:
    """
    Diagnoses degeneracy causes from run trace.

    Analyzes rejection patterns, tightening rate, and near-failure
    saturation over a window of steps.
    """

    def __init__(self, window_size: int = 200):
        """
        Initialize diagnoser.

        Args:
            window_size: Number of steps to analyze (default 200)
        """
        self._window_size = window_size

    def diagnose(
        self,
        outcomes: List[DeltaOutcome],
        tightening_events: Optional[List[dict]] = None,
    ) -> DegeneracyDiagnosisResult:
        """
        Diagnose degeneracy cause from outcomes.

        Args:
            outcomes: List of DeltaOutcome from the run
            tightening_events: Optional list of tightening events for rate computation

        Returns:
            DegeneracyDiagnosisResult with diagnosis and supporting metrics
        """
        # Get window of last W steps
        window = outcomes[-self._window_size:] if len(outcomes) > self._window_size else outcomes
        total_steps = len(window)

        if total_steps == 0:
            return self._empty_result()

        # Count rejections
        rejections = [o for o in window if not o.accepted]
        rejection_count = len(rejections)
        rejection_rate = rejection_count / total_steps if total_steps > 0 else 0.0

        # Build reason histogram
        reason_counts: Counter[RejectionReasonCode] = Counter()
        for outcome in rejections:
            reason_counts[outcome.rejection_reason_code] += 1

        reason_histogram = {
            code.name: count for code, count in reason_counts.items()
        }

        # Find top reason
        if reason_counts:
            top_reason = reason_counts.most_common(1)[0][0]
            top_reason_count = reason_counts[top_reason]
            top_reason_fraction = top_reason_count / rejection_count if rejection_count > 0 else 0.0
        else:
            top_reason = None
            top_reason_fraction = 0.0

        # Compute fractions by category
        inadmissible_count = reason_counts.get(RejectionReasonCode.INADMISSIBLE_P5, 0)
        inadmissible_p5_fraction = inadmissible_count / rejection_count if rejection_count > 0 else 0.0

        evaluability_count = sum(
            reason_counts.get(code, 0) for code in EVALUABILITY_REASON_CODES
        )
        evaluability_fraction = evaluability_count / rejection_count if rejection_count > 0 else 0.0

        delta_error_count = sum(
            reason_counts.get(code, 0) for code in DELTA_ERROR_REASON_CODES
        )
        delta_error_fraction = delta_error_count / rejection_count if rejection_count > 0 else 0.0

        # Compute tightening rate
        tightening_rate = self._compute_tightening_rate(tightening_events, total_steps)

        # Compute near-failure saturation
        near_failure_saturation = self._compute_near_failure_saturation(window)

        # Classify diagnosis
        diagnosis = self._classify(
            inadmissible_p5_fraction=inadmissible_p5_fraction,
            tightening_rate=tightening_rate,
            evaluability_fraction=evaluability_fraction,
            delta_error_fraction=delta_error_fraction,
            near_failure_saturation=near_failure_saturation,
        )

        return DegeneracyDiagnosisResult(
            diagnosis=diagnosis,
            total_steps=total_steps,
            rejection_count=rejection_count,
            rejection_rate=rejection_rate,
            reason_histogram=reason_histogram,
            top_reason=top_reason,
            top_reason_fraction=top_reason_fraction,
            inadmissible_p5_fraction=inadmissible_p5_fraction,
            evaluability_fraction=evaluability_fraction,
            delta_error_fraction=delta_error_fraction,
            tightening_rate=tightening_rate,
            near_failure_saturation=near_failure_saturation,
        )

    def _compute_tightening_rate(
        self,
        tightening_events: Optional[List[dict]],
        total_steps: int,
    ) -> float:
        """Compute tightening rate over window."""
        if not tightening_events or total_steps == 0:
            return 0.0

        # Count tightening vs loosening events
        tighten_count = sum(1 for e in tightening_events if e.get("effect") == "tighten")
        loosen_count = sum(1 for e in tightening_events if e.get("effect") == "loosen")

        # Rate = (tighten - loosen) / steps
        return (tighten_count - loosen_count) / total_steps

    def _compute_near_failure_saturation(self, outcomes: List[DeltaOutcome]) -> float:
        """
        Compute near-failure saturation rate.

        Saturation = fraction of steps with at least one near-failure flag.
        """
        if not outcomes:
            return 0.0

        steps_with_flags = sum(
            1 for o in outcomes if len(o.near_failure_flags) > 0
        )
        return steps_with_flags / len(outcomes)

    def _classify(
        self,
        inadmissible_p5_fraction: float,
        tightening_rate: float,
        evaluability_fraction: float,
        delta_error_fraction: float,
        near_failure_saturation: float,
    ) -> DegeneracyDiagnosis:
        """
        Classify degeneracy cause based on metrics.

        Rules (in priority order):
        1. Conservative Lock-In: >80% INADMISSIBLE_P5 AND tightening_rate > 0
        2. Evaluability Bottleneck: evaluability_fraction > 50% OR near_failure_saturation > 0.7
        3. Delta Language Insufficiency: delta_error_fraction > 50%
        4. Mixed/Unknown: none of the above
        """
        # Rule 1: Conservative Lock-In
        if inadmissible_p5_fraction > 0.80 and tightening_rate > 0:
            return DegeneracyDiagnosis.CONSERVATIVE_LOCKIN

        # Rule 2: Evaluability Bottleneck
        if evaluability_fraction > 0.50 or near_failure_saturation > 0.70:
            return DegeneracyDiagnosis.EVALUABILITY_BOTTLENECK

        # Rule 3: Delta Language Insufficiency
        if delta_error_fraction > 0.50:
            return DegeneracyDiagnosis.DELTA_LANGUAGE_INSUFFICIENCY

        # Rule 4: Mixed/Unknown
        return DegeneracyDiagnosis.MIXED_OR_UNKNOWN

    def _empty_result(self) -> DegeneracyDiagnosisResult:
        """Create result for empty input."""
        return DegeneracyDiagnosisResult(
            diagnosis=DegeneracyDiagnosis.MIXED_OR_UNKNOWN,
            total_steps=0,
            rejection_count=0,
            rejection_rate=0.0,
            reason_histogram={},
            top_reason=None,
            top_reason_fraction=0.0,
            inadmissible_p5_fraction=0.0,
            evaluability_fraction=0.0,
            delta_error_fraction=0.0,
            tightening_rate=0.0,
            near_failure_saturation=0.0,
        )

    def diagnose_from_records(
        self,
        step_records: List[dict],
        tightening_events: Optional[List[dict]] = None,
    ) -> DegeneracyDiagnosisResult:
        """
        Diagnose degeneracy from step record dicts (from runner).

        Args:
            step_records: List of step record dicts with keys:
                - rejection_code: str (RejectionReasonCode name)
                - accepted: bool
                - near_failure_flags: List[str] (flag names)
            tightening_events: Optional list of tightening events

        Returns:
            DegeneracyDiagnosisResult
        """
        # Get window of last W steps
        window = step_records[-self._window_size:] if len(step_records) > self._window_size else step_records
        total_steps = len(window)

        if total_steps == 0:
            return self._empty_result()

        # Count rejections
        rejections = [r for r in window if not r.get("accepted", True)]
        rejection_count = len(rejections)
        rejection_rate = rejection_count / total_steps if total_steps > 0 else 0.0

        # Build reason histogram (from string names)
        reason_counts: Counter[str] = Counter()
        for record in rejections:
            code_name = record.get("rejection_code", "UNKNOWN")
            reason_counts[code_name] += 1

        reason_histogram = dict(reason_counts)

        # Find top reason
        if reason_counts:
            top_reason_name = reason_counts.most_common(1)[0][0]
            top_reason_count = reason_counts[top_reason_name]
            top_reason_fraction = top_reason_count / rejection_count if rejection_count > 0 else 0.0
            try:
                top_reason = RejectionReasonCode[top_reason_name]
            except KeyError:
                top_reason = None
        else:
            top_reason = None
            top_reason_fraction = 0.0

        # Compute fractions by category
        inadmissible_count = reason_counts.get("INADMISSIBLE_P5", 0)
        inadmissible_p5_fraction = inadmissible_count / rejection_count if rejection_count > 0 else 0.0

        # Evaluability codes
        evaluability_code_names = {c.name for c in EVALUABILITY_REASON_CODES}
        # Also include WOULD_BREAK_EVALUABILITY as evaluability-related
        evaluability_code_names.add("WOULD_BREAK_EVALUABILITY")
        evaluability_count = sum(
            reason_counts.get(name, 0) for name in evaluability_code_names
        )
        evaluability_fraction = evaluability_count / rejection_count if rejection_count > 0 else 0.0

        # Delta error codes
        delta_error_code_names = {c.name for c in DELTA_ERROR_REASON_CODES}
        # Also include INVALID_DELTA_SYNTAX
        delta_error_code_names.add("INVALID_DELTA_SYNTAX")
        delta_error_count = sum(
            reason_counts.get(name, 0) for name in delta_error_code_names
        )
        delta_error_fraction = delta_error_count / rejection_count if rejection_count > 0 else 0.0

        # Compute tightening rate
        tightening_rate = self._compute_tightening_rate(tightening_events, total_steps)

        # Compute near-failure saturation (from records)
        steps_with_flags = sum(
            1 for r in window if len(r.get("near_failure_flags", [])) > 0
        )
        near_failure_saturation = steps_with_flags / len(window) if window else 0.0

        # Classify diagnosis
        diagnosis = self._classify(
            inadmissible_p5_fraction=inadmissible_p5_fraction,
            tightening_rate=tightening_rate,
            evaluability_fraction=evaluability_fraction,
            delta_error_fraction=delta_error_fraction,
            near_failure_saturation=near_failure_saturation,
        )

        return DegeneracyDiagnosisResult(
            diagnosis=diagnosis,
            total_steps=total_steps,
            rejection_count=rejection_count,
            rejection_rate=rejection_rate,
            reason_histogram=reason_histogram,
            top_reason=top_reason,
            top_reason_fraction=top_reason_fraction,
            inadmissible_p5_fraction=inadmissible_p5_fraction,
            evaluability_fraction=evaluability_fraction,
            delta_error_fraction=delta_error_fraction,
            tightening_rate=tightening_rate,
            near_failure_saturation=near_failure_saturation,
        )


def diagnose_degeneracy(
    outcomes_or_records: List[DeltaOutcome] | List[dict],
    window_size: int = 200,
    tightening_events: Optional[List[dict]] = None,
) -> DegeneracyDiagnosisResult:
    """
    Convenience function to diagnose degeneracy.

    Accepts either DeltaOutcome objects or step record dicts.

    Args:
        outcomes_or_records: List of DeltaOutcome or step record dicts
        window_size: Number of steps to analyze
        tightening_events: Optional list of tightening events

    Returns:
        DegeneracyDiagnosisResult
    """
    diagnoser = DegeneracyDiagnoser(window_size=window_size)

    # Handle step record dicts
    if outcomes_or_records and isinstance(outcomes_or_records[0], dict):
        return diagnoser.diagnose_from_records(outcomes_or_records, tightening_events)
    else:
        return diagnoser.diagnose(outcomes_or_records, tightening_events)
