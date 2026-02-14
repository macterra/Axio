"""
X-2D Metrics Computation

Per-cycle and sliding-window metrics for delegation density stress profiling.

Metrics:
  Per-cycle: density, A_eff, B, M_eff, active_treaty_count,
             grants_admitted, grants_rejected, revocations,
             delegated_warrants, delegated_rejections,
             revalidation_invalidated, density_repair_invalidated.
  Window:    churn_W, refusal_rate_W, type_III_rate_W, density_mean_W,
             density_max_W, active_treaty_mean_W.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class X2DPerCycleMetric:
    """Metrics collected per cycle."""
    cycle_index: int
    density: float
    a_eff: int
    b: int
    m_eff: int
    active_treaty_count: int
    density_upper_bound_active: float
    grants_admitted: int = 0
    grants_rejected: int = 0
    revocations_admitted: int = 0
    revocations_rejected: int = 0
    delegated_warrants: int = 0
    delegated_rejections: int = 0
    revalidation_invalidated: int = 0
    density_repair_invalidated: int = 0
    decision_type: str = ""
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_index": self.cycle_index,
            "density": self.density,
            "a_eff": self.a_eff,
            "b": self.b,
            "m_eff": self.m_eff,
            "active_treaty_count": self.active_treaty_count,
            "density_upper_bound_active": self.density_upper_bound_active,
            "grants_admitted": self.grants_admitted,
            "grants_rejected": self.grants_rejected,
            "revocations_admitted": self.revocations_admitted,
            "revocations_rejected": self.revocations_rejected,
            "delegated_warrants": self.delegated_warrants,
            "delegated_rejections": self.delegated_rejections,
            "revalidation_invalidated": self.revalidation_invalidated,
            "density_repair_invalidated": self.density_repair_invalidated,
            "decision_type": self.decision_type,
            "latency_ms": self.latency_ms,
        }


@dataclass
class X2DWindowMetric:
    """Sliding-window metrics."""
    window_end_cycle: int
    window_size: int
    churn_w: float  # (grants + revocations) / window_size
    refusal_rate_w: float  # refusals / window_size
    type_iii_rate_w: float  # delegated_rejections / total_delegated_attempts
    density_mean_w: float
    density_max_w: float
    active_treaty_mean_w: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_end_cycle": self.window_end_cycle,
            "window_size": self.window_size,
            "churn_w": self.churn_w,
            "refusal_rate_w": self.refusal_rate_w,
            "type_iii_rate_w": self.type_iii_rate_w,
            "density_mean_w": self.density_mean_w,
            "density_max_w": self.density_max_w,
            "active_treaty_mean_w": self.active_treaty_mean_w,
        }


def compute_per_cycle_metrics(cycle_results: List[Any]) -> List[X2DPerCycleMetric]:
    """Extract per-cycle metrics from X2DCycleResult list."""
    metrics: List[X2DPerCycleMetric] = []
    for r in cycle_results:
        metrics.append(X2DPerCycleMetric(
            cycle_index=r.cycle_index,
            density=r.density,
            a_eff=r.a_eff,
            b=r.b,
            m_eff=r.m_eff,
            active_treaty_count=r.active_grants_count,
            density_upper_bound_active=r.density_upper_bound_active,
            grants_admitted=r.grants_admitted,
            grants_rejected=r.grants_rejected,
            revocations_admitted=r.revocations_admitted,
            revocations_rejected=r.revocations_rejected,
            delegated_warrants=r.delegated_warrants_issued,
            delegated_rejections=r.delegated_rejections,
            revalidation_invalidated=r.revalidation_invalidated,
            density_repair_invalidated=r.density_repair_invalidated,
            decision_type=r.decision_type,
            latency_ms=r.latency_ms,
        ))
    return metrics


def compute_window_metrics(
    per_cycle: List[X2DPerCycleMetric],
    window_size: int,
) -> List[X2DWindowMetric]:
    """Compute sliding-window metrics.

    Window [i - W + 1 .. i] for each i >= W - 1.
    """
    windows: List[X2DWindowMetric] = []
    W = window_size
    n = len(per_cycle)
    if n < W:
        return windows

    for i in range(W - 1, n):
        window = per_cycle[i - W + 1 : i + 1]

        total_grants = sum(m.grants_admitted for m in window)
        total_revocations = sum(m.revocations_admitted for m in window)
        churn_w = (total_grants + total_revocations) / W

        refusals = sum(1 for m in window if m.decision_type == "REFUSE")
        refusal_rate_w = refusals / W

        total_delegated_attempts = sum(
            m.delegated_warrants + m.delegated_rejections for m in window
        )
        total_delegated_rej = sum(m.delegated_rejections for m in window)
        type_iii_rate_w = (
            total_delegated_rej / total_delegated_attempts
            if total_delegated_attempts > 0 else 0.0
        )

        densities = [m.density for m in window]
        density_mean_w = sum(densities) / W
        density_max_w = max(densities)

        active_counts = [m.active_treaty_count for m in window]
        active_treaty_mean_w = sum(active_counts) / W

        windows.append(X2DWindowMetric(
            window_end_cycle=i,
            window_size=W,
            churn_w=churn_w,
            refusal_rate_w=refusal_rate_w,
            type_iii_rate_w=type_iii_rate_w,
            density_mean_w=density_mean_w,
            density_max_w=density_max_w,
            active_treaty_mean_w=active_treaty_mean_w,
        ))

    return windows


def write_metrics(
    session_dir: Path,
    per_cycle: List[X2DPerCycleMetric],
    window_metrics: List[X2DWindowMetric],
) -> None:
    """Write metrics JSONL files to session directory."""
    session_dir.mkdir(parents=True, exist_ok=True)

    # Per-cycle metrics
    metrics_path = session_dir / "x2d_metrics.jsonl"
    with open(metrics_path, "w") as f:
        for m in per_cycle:
            f.write(json.dumps(m.to_dict(), separators=(",", ":"), sort_keys=True) + "\n")

    # Window metrics
    window_path = session_dir / "x2d_window_metrics.jsonl"
    with open(window_path, "w") as f:
        for w in window_metrics:
            f.write(json.dumps(w.to_dict(), separators=(",", ":"), sort_keys=True) + "\n")
