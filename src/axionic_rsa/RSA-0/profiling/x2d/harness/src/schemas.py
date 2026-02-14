"""
X-2D Session Schema & Artifact Types

Per spec §3 and Q&A A1: X2DSessionStart/End are harness-only metadata,
not kernel artifacts. They are schema-validated, hashed, and logged
before cycle 1.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionFamily(str, Enum):
    D_BASE = "D-BASE"
    D_CHURN = "D-CHURN"
    D_SAT = "D-SAT"
    D_RATCHET = "D-RATCHET"
    D_EDGE = "D-EDGE"


@dataclass
class X2DSessionStart:
    """Session start artifact. Hashed and logged before cycle 1."""
    session_family: str
    session_id: str
    session_length_cycles: int
    window_size_cycles: int
    density_upper_bound: float
    density_proximity_delta: float
    deadlock_threshold_K: int
    seeds: Dict[str, int]  # {treaty_stream, action_stream, amendment_stream}
    invalid_request_fractions: Dict[str, float]
    grant_duration_distribution: Dict[str, Any]
    grantee_count: int
    max_active_grants_per_grantee: int
    delegated_requests_per_cycle_fraction: float
    amendment_schedule: List[Dict[str, Any]]
    cycle_ordering_mode: str = "X2D_TOPOLOGICAL"
    target_density_band_low: float = 0.0
    target_density_band_high: float = 0.0
    notes: str = ""
    created_at: str = ""
    author: str = "rsa-x2d-harness"
    id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "X2DSessionStart",
            "session_family": self.session_family,
            "session_id": self.session_id,
            "session_length_cycles": self.session_length_cycles,
            "window_size_cycles": self.window_size_cycles,
            "density_upper_bound": self.density_upper_bound,
            "density_proximity_delta": self.density_proximity_delta,
            "deadlock_threshold_K": self.deadlock_threshold_K,
            "seeds": self.seeds,
            "invalid_request_fractions": self.invalid_request_fractions,
            "grant_duration_distribution": self.grant_duration_distribution,
            "grantee_count": self.grantee_count,
            "max_active_grants_per_grantee": self.max_active_grants_per_grantee,
            "delegated_requests_per_cycle_fraction": self.delegated_requests_per_cycle_fraction,
            "amendment_schedule": self.amendment_schedule,
            "cycle_ordering_mode": self.cycle_ordering_mode,
            "target_density_band_low": self.target_density_band_low,
            "target_density_band_high": self.target_density_band_high,
            "notes": self.notes,
            "created_at": self.created_at,
            "author": self.author,
        }

    def canonical_hash(self) -> str:
        raw = json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")
        h = hashlib.sha256(raw).hexdigest()
        if not self.id:
            self.id = h
        return h


@dataclass
class X2DSessionEnd:
    """Session end artifact."""
    session_id: str
    final_cycle: int
    replay_divergence_count: int
    closure_pass: bool
    failure_reasons: List[str] = field(default_factory=list)
    state_hash_chain_tip: str = ""
    created_at: str = ""
    author: str = "rsa-x2d-harness"
    id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "X2DSessionEnd",
            "session_id": self.session_id,
            "final_cycle": self.final_cycle,
            "replay_divergence_count": self.replay_divergence_count,
            "closure_pass": self.closure_pass,
            "failure_reasons": self.failure_reasons,
            "state_hash_chain_tip": self.state_hash_chain_tip,
            "created_at": self.created_at,
            "author": self.author,
        }

    def canonical_hash(self) -> str:
        raw = json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")
        h = hashlib.sha256(raw).hexdigest()
        if not self.id:
            self.id = h
        return h


# ---------------------------------------------------------------------------
# Session Admission Gates (6D / 7D / 8D)
# ---------------------------------------------------------------------------

class X2DGateResult:
    """Result of an X-2D session admission gate."""
    def __init__(self, passed: bool, gate: str, reason: str = "", detail: str = ""):
        self.passed = passed
        self.gate = gate
        self.reason = reason
        self.detail = detail


def gate_6d(
    kernel_version_id: str,
    constitution_hash: str,
    treaty_schema_hash: str,
    constitution_has_x2: bool,
    constitution_has_amendment: bool,
    session_family: str,
    expected_kernel_version: str = "rsa-replay-regime-x0e-v0.1",
) -> X2DGateResult:
    """Gate 6D: X-2D Session Preconditions.

    Verifies kernel version, constitution, treaty schema, X-1/X-2
    machinery, and session family validity.
    """
    if kernel_version_id != expected_kernel_version:
        return X2DGateResult(
            False, "6D", "KERNEL_VERSION_MISMATCH",
            f"expected {expected_kernel_version}, got {kernel_version_id}",
        )
    if not constitution_hash:
        return X2DGateResult(False, "6D", "CONSTITUTION_MISSING", "no constitution hash")
    if not treaty_schema_hash:
        return X2DGateResult(False, "6D", "TREATY_SCHEMA_MISSING", "no treaty schema hash")
    if not constitution_has_amendment:
        return X2DGateResult(False, "6D", "AMENDMENT_DISABLED", "X-1 amendment machinery required")
    if not constitution_has_x2:
        return X2DGateResult(False, "6D", "TREATY_DISABLED", "X-2 treaty machinery required")
    valid_families = {f.value for f in SessionFamily}
    if session_family not in valid_families:
        return X2DGateResult(
            False, "6D", "INVALID_FAMILY",
            f"session_family must be one of {valid_families}",
        )
    return X2DGateResult(True, "6D")


def gate_7d(session_start: X2DSessionStart) -> X2DGateResult:
    """Gate 7D: X-2D Session Schema Validity.

    Verifies all required fields present, types correct, values in bounds.
    """
    errors: List[str] = []

    if not session_start.session_id:
        errors.append("session_id required")
    if session_start.session_length_cycles < 1:
        errors.append("session_length_cycles must be >= 1")
    if session_start.window_size_cycles < 1:
        errors.append("window_size_cycles must be >= 1")
    if session_start.density_proximity_delta < 0:
        errors.append("density_proximity_delta must be >= 0")
    if session_start.deadlock_threshold_K < 1:
        errors.append("deadlock_threshold_K must be >= 1")
    if session_start.grantee_count < 1:
        errors.append("grantee_count must be >= 1")
    if session_start.max_active_grants_per_grantee < 1:
        errors.append("max_active_grants_per_grantee must be >= 1")
    if not (0 <= session_start.delegated_requests_per_cycle_fraction <= 1):
        errors.append("delegated_requests_per_cycle_fraction must be in [0,1]")

    # Validate seeds
    required_seeds = {"treaty_stream", "action_stream", "amendment_stream"}
    if not isinstance(session_start.seeds, dict):
        errors.append("seeds must be a dict")
    elif not required_seeds.issubset(session_start.seeds.keys()):
        missing = required_seeds - set(session_start.seeds.keys())
        errors.append(f"seeds missing keys: {missing}")

    # Validate invalid_request_fractions sum
    if isinstance(session_start.invalid_request_fractions, dict):
        frac_sum = sum(session_start.invalid_request_fractions.values())
        if frac_sum > 1.0:
            errors.append(f"invalid_request_fractions sum {frac_sum} > 1.0")

    # Validate canonicalization
    try:
        session_start.canonical_hash()
    except Exception as e:
        errors.append(f"canonicalization failed: {e}")

    if errors:
        return X2DGateResult(False, "7D", "SCHEMA_INVALID", "; ".join(errors))
    return X2DGateResult(True, "7D")


def gate_8d(session_start: X2DSessionStart) -> X2DGateResult:
    """Gate 8D: Session Parameter Admissibility.

    Verifies amendment schedule consistency with session family,
    D-EDGE band parameters, and parameter bounds.
    """
    family = session_start.session_family

    # Amendment schedule consistency
    if family == SessionFamily.D_RATCHET.value:
        if not session_start.amendment_schedule:
            return X2DGateResult(
                False, "8D", "AMENDMENT_SCHEDULE_REQUIRED",
                "D-RATCHET requires non-empty amendment_schedule",
            )
    else:
        if session_start.amendment_schedule:
            return X2DGateResult(
                False, "8D", "AMENDMENT_SCHEDULE_FORBIDDEN",
                f"amendment_schedule must be empty for {family}",
            )

    # D-EDGE band validation
    if family == SessionFamily.D_EDGE.value:
        if session_start.target_density_band_low <= 0:
            return X2DGateResult(
                False, "8D", "INVALID_FIELD",
                "D-EDGE requires target_density_band_low > 0",
            )
        if session_start.target_density_band_high <= session_start.target_density_band_low:
            return X2DGateResult(
                False, "8D", "INVALID_FIELD",
                "D-EDGE requires target_density_band_high > target_density_band_low",
            )

    # Window size must not exceed session length
    if session_start.window_size_cycles > session_start.session_length_cycles:
        return X2DGateResult(
            False, "8D", "INVALID_FIELD",
            "window_size_cycles must be <= session_length_cycles",
        )

    return X2DGateResult(True, "8D")


def admit_session(
    session_start: X2DSessionStart,
    kernel_version_id: str,
    constitution_hash: str,
    treaty_schema_hash: str,
    constitution_has_x2: bool,
    constitution_has_amendment: bool,
) -> List[X2DGateResult]:
    """Run all X-2D session admission gates in sequence.
    Returns list of gate results (short-circuits on first failure).
    """
    results: List[X2DGateResult] = []

    g6 = gate_6d(
        kernel_version_id, constitution_hash, treaty_schema_hash,
        constitution_has_x2, constitution_has_amendment,
        session_start.session_family,
    )
    results.append(g6)
    if not g6.passed:
        return results

    g7 = gate_7d(session_start)
    results.append(g7)
    if not g7.passed:
        return results

    g8 = gate_8d(session_start)
    results.append(g8)
    return results
