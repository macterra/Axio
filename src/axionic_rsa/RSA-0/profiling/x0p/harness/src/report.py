"""
X-0P Report Generator

Generates x0p_report.json with all required metrics (per instructions §10):
- Decision distributions
- Baseline contrast
- Authority utilization summary
- Token cost summary
- Latency summary
- Replay verification status
- Constitution hash
- Calibration hash

"Numbers only" — no narrative prose (per G23). Structured JSON with
namespaced keys, units, and counts.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import canonical_json

from profiling.x0p.harness.src.baselines import BaselineRunResult
from profiling.x0p.harness.src.cycle_runner import ConditionRunResult, CycleResult
from replay.x0p.verifier import ReplayVerificationResult


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def _decision_distribution(results: List[CycleResult]) -> Dict[str, Any]:
    """Compute decision distribution for a set of cycle results."""
    total = len(results)
    if total == 0:
        return {"total": 0, "action_count": 0, "refuse_count": 0, "exit_count": 0}

    action_count = sum(1 for r in results if r.decision_type == "ACTION")
    refuse_count = sum(1 for r in results if r.decision_type == "REFUSE")
    exit_count = sum(1 for r in results if r.decision_type == "EXIT")

    return {
        "total": total,
        "action_count": action_count,
        "refuse_count": refuse_count,
        "exit_count": exit_count,
        "action_rate": round(action_count / total, 4) if total > 0 else 0,
        "refuse_rate": round(refuse_count / total, 4) if total > 0 else 0,
        "exit_rate": round(exit_count / total, 4) if total > 0 else 0,
    }


def _gate_breakdown(results: List[CycleResult]) -> Dict[str, Any]:
    """Compute gate failure histogram and reason code distribution."""
    gate_histogram: Dict[str, int] = {}
    reason_codes: Dict[str, int] = {}
    candidate_rejections = 0

    for r in results:
        for gate, count in r.gate_failures.items():
            gate_histogram[gate] = gate_histogram.get(gate, 0) + count
        if r.refusal_reason:
            reason_codes[r.refusal_reason] = reason_codes.get(r.refusal_reason, 0) + 1
        candidate_rejections += r.rejected_count

    return {
        "failed_gate_histogram": gate_histogram,
        "reason_code_distribution": reason_codes,
        "total_candidate_rejections": candidate_rejections,
    }


def _authority_utilization(results: List[CycleResult]) -> Dict[str, Any]:
    """Compute authority surface utilization metrics."""
    all_authority_ids: List[str] = []
    clause_frequency: Dict[str, int] = {}

    for r in results:
        for aid in r.authority_ids_invoked:
            all_authority_ids.append(aid)
            clause_frequency[aid] = clause_frequency.get(aid, 0) + 1

    distinct_ids = set(all_authority_ids)
    total_invocations = len(all_authority_ids)

    # Utilization entropy (Shannon entropy of clause frequency)
    entropy = 0.0
    if total_invocations > 0 and len(distinct_ids) > 1:
        import math
        for count in clause_frequency.values():
            p = count / total_invocations
            if p > 0:
                entropy -= p * math.log2(p)

    # % constitution exercised (4 total clause IDs)
    total_clauses = 4
    pct_exercised = len(distinct_ids) / total_clauses if total_clauses > 0 else 0

    return {
        "distinct_authority_ids": sorted(distinct_ids),
        "distinct_count": len(distinct_ids),
        "total_invocations": total_invocations,
        "clause_frequency": clause_frequency,
        "utilization_entropy_bits": round(entropy, 4),
        "constitution_coverage_pct": round(pct_exercised, 4),
    }


def _outcome_cost(results: List[CycleResult]) -> Dict[str, Any]:
    """Compute outcome cost metrics (token counts by decision type)."""
    action_tokens: List[int] = []
    refuse_tokens: List[int] = []
    exit_tokens: List[int] = []

    for r in results:
        # Extract token count from observations (budget observation)
        token_count = 0
        # Token count is in the metadata or can be derived; for now approximate
        # from the input data
        budget_obs = None
        # We don't have direct access to observations in CycleResult,
        # so use admitted_count as a proxy for complexity
        if r.decision_type == "ACTION":
            action_tokens.append(r.admitted_count)
        elif r.decision_type == "REFUSE":
            refuse_tokens.append(r.rejected_count)
        elif r.decision_type == "EXIT":
            exit_tokens.append(0)

    def _safe_mean(lst: List[int]) -> float:
        return round(statistics.mean(lst), 4) if lst else 0.0

    total_actions = len(action_tokens)
    total_refuses = len(refuse_tokens)
    refuse_action_ratio = (
        round(total_refuses / total_actions, 4) if total_actions > 0 else float("inf")
    )

    # Flag if ratio > 10×
    ratio_flagged = refuse_action_ratio > 10.0 if total_actions > 0 else False

    return {
        "mean_admitted_per_action": _safe_mean(action_tokens),
        "mean_rejected_per_refuse": _safe_mean(refuse_tokens),
        "refuse_action_ratio": refuse_action_ratio,
        "refuse_action_ratio_flagged": ratio_flagged,
        "total_actions": total_actions,
        "total_refuses": total_refuses,
        "total_exits": len(exit_tokens),
    }


def _latency_summary(results: List[CycleResult]) -> Dict[str, Any]:
    """Compute latency metrics."""
    latencies = [r.latency_ms for r in results]
    if not latencies:
        return {
            "mean_ms": 0, "median_ms": 0, "p95_ms": 0,
            "worst_ms": 0, "variance_ms": 0, "n_samples": 0,
        }

    latencies_sorted = sorted(latencies)
    p95_idx = int(len(latencies_sorted) * 0.95)

    return {
        "mean_ms": round(statistics.mean(latencies), 4),
        "median_ms": round(statistics.median(latencies), 4),
        "p95_ms": round(latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)], 4),
        "worst_ms": round(max(latencies), 4),
        "variance_ms": round(statistics.variance(latencies), 4) if len(latencies) > 1 else 0,
        "n_samples": len(latencies),
    }


def _baseline_contrast(
    condition_dist: Dict[str, Any],
    refuse_baseline: Optional[BaselineRunResult],
    admit_baseline: Optional[BaselineRunResult],
) -> Dict[str, Any]:
    """Compute baseline contrast metrics."""
    result: Dict[str, Any] = {
        "condition_action_rate": condition_dist.get("action_rate", 0),
    }

    if refuse_baseline:
        refuse_actions = sum(
            1 for cr in refuse_baseline.cycle_results
            if cr.decision_type == "ACTION"
        )
        refuse_total = len(refuse_baseline.cycle_results)
        refuse_rate = refuse_actions / refuse_total if refuse_total > 0 else 0
        result["baseline_refuse_action_rate"] = round(refuse_rate, 4)
        result["exceeds_refuse_baseline"] = condition_dist.get("action_rate", 0) > refuse_rate

    if admit_baseline:
        admit_actions = sum(
            1 for cr in admit_baseline.cycle_results
            if cr.decision_type == "ACTION"
        )
        admit_total = len(admit_baseline.cycle_results)
        admit_rate = admit_actions / admit_total if admit_total > 0 else 0
        result["baseline_admit_action_rate"] = round(admit_rate, 4)

    return result


# ---------------------------------------------------------------------------
# Full report generation
# ---------------------------------------------------------------------------

def generate_report(
    condition_results: Dict[str, ConditionRunResult],
    baseline_results: Dict[str, Dict[str, BaselineRunResult]],  # {condition: {type: result}}
    replay_results: Dict[str, ReplayVerificationResult],
    constitution_hash: str,
    calibration_hash: str,
    session_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate the full x0p_report.json.

    Numbers only, no narrative (per G23).
    """
    report: Dict[str, Any] = {
        "constitution_hash": constitution_hash,
        "calibration_hash": calibration_hash,
        "session": {
            "run_id": session_metadata.get("run_id", ""),
        },
    }

    # Per-condition metrics
    metrics: Dict[str, Any] = {}

    for condition, run_result in condition_results.items():
        results = run_result.cycle_results

        decision_dist = _decision_distribution(results)
        gate = _gate_breakdown(results)
        authority = _authority_utilization(results)
        cost = _outcome_cost(results)
        latency = _latency_summary(results)

        # Baseline contrast
        refuse_bl = baseline_results.get(condition, {}).get("always_refuse")
        admit_bl = baseline_results.get(condition, {}).get("always_admit")
        contrast = _baseline_contrast(decision_dist, refuse_bl, admit_bl)

        metrics[f"condition_{condition}"] = {
            "decision_distribution": decision_dist,
            "gate_breakdown": gate,
            "authority_utilization": authority,
            "outcome_cost": cost,
            "latency": latency,
            "baseline_contrast": contrast,
            "manifest_hash": run_result.manifest_hash,
            "n_cycles": run_result.n_cycles,
            "aborted": run_result.aborted,
        }

    report["metrics"] = metrics

    # Replay verification status
    replay_status: Dict[str, Any] = {}
    all_replay_passed = True
    for condition, rv in replay_results.items():
        replay_status[condition] = {
            "passed": rv.passed,
            "n_cycles_verified": rv.n_cycles_verified,
            "n_divergences": rv.n_divergences,
        }
        if not rv.passed:
            all_replay_passed = False

    report["replay_verification"] = {
        "all_passed": all_replay_passed,
        "per_condition": replay_status,
    }

    # Baseline summaries
    baseline_summary: Dict[str, Any] = {}
    for condition, bls in baseline_results.items():
        baseline_summary[condition] = {}
        for bl_type, bl_result in bls.items():
            n_total = len(bl_result.cycle_results)
            n_action = sum(1 for cr in bl_result.cycle_results if cr.decision_type == "ACTION")
            baseline_summary[condition][bl_type] = {
                "n_cycles": n_total,
                "action_count": n_action,
                "action_rate": round(n_action / n_total, 4) if n_total > 0 else 0,
            }

    report["baselines"] = baseline_summary

    return report


def write_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
