"""
X-3 Profiling Schemas

Session families, session start/end artifacts, and admission gates
for the X-3 sovereign succession profiling harness.

8 mandatory families per spec §10 and Q&A AF1-AF3:
  X3-BASE, X3-NEAR_BOUND, X3-CHURN, X3-RAT_DELAY,
  X3-MULTI_ROT, X3-INVALID_SIG, X3-DUP_CYCLE, X3-INVALID_BOUNDARY
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import canonical_json


# ---------------------------------------------------------------------------
# Session Families
# ---------------------------------------------------------------------------

class SessionFamilyX3(str, Enum):
    X3_BASE = "X3-BASE"
    X3_NEAR_BOUND = "X3-NEAR_BOUND"
    X3_CHURN = "X3-CHURN"
    X3_RAT_DELAY = "X3-RAT_DELAY"
    X3_MULTI_ROT = "X3-MULTI_ROT"
    X3_INVALID_SIG = "X3-INVALID_SIG"
    X3_DUP_CYCLE = "X3-DUP_CYCLE"
    X3_INVALID_BOUNDARY = "X3-INVALID_BOUNDARY"


# ---------------------------------------------------------------------------
# X3 Session Start
# ---------------------------------------------------------------------------

@dataclass
class X3SessionStart:
    """Preregistered session parameters for X-3 profiling."""
    session_family: str
    session_id: str
    session_length_cycles: int
    density_upper_bound: float
    seeds: Dict[str, int]
    rotation_schedule: List[Dict[str, Any]]  # [{cycle, successor_index}, ...]
    ratification_delay_cycles: int = 1
    delegation_state_mode: str = "LOW"
    grantee_count: int = 3
    delegated_requests_per_cycle_fraction: float = 0.5
    invalid_succession_fractions: Dict[str, float] = field(default_factory=dict)
    invalid_boundary_faults: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "X3SessionStart",
            "session_family": self.session_family,
            "session_id": self.session_id,
            "session_length_cycles": self.session_length_cycles,
            "density_upper_bound": self.density_upper_bound,
            "seeds": self.seeds,
            "rotation_schedule": self.rotation_schedule,
            "ratification_delay_cycles": self.ratification_delay_cycles,
            "delegation_state_mode": self.delegation_state_mode,
            "grantee_count": self.grantee_count,
            "delegated_requests_per_cycle_fraction": self.delegated_requests_per_cycle_fraction,
            "invalid_succession_fractions": self.invalid_succession_fractions,
            "invalid_boundary_faults": self.invalid_boundary_faults,
            "created_at": self.created_at,
        }

    def canonical_hash(self) -> str:
        return hashlib.sha256(
            canonical_json(self.to_dict()).encode("utf-8")
        ).hexdigest()


# ---------------------------------------------------------------------------
# X3 Session End
# ---------------------------------------------------------------------------

@dataclass
class X3SessionEnd:
    """End-of-session summary artifact."""
    session_id: str
    final_cycle: int
    replay_divergence_count: int = 0
    closure_pass: bool = False
    failure_reasons: List[str] = field(default_factory=list)
    state_hash_chain_tip: str = ""
    total_rotations_activated: int = 0
    total_successions_rejected: int = 0
    total_boundary_faults_detected: int = 0
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "X3SessionEnd",
            "session_id": self.session_id,
            "final_cycle": self.final_cycle,
            "replay_divergence_count": self.replay_divergence_count,
            "closure_pass": self.closure_pass,
            "failure_reasons": self.failure_reasons,
            "state_hash_chain_tip": self.state_hash_chain_tip,
            "total_rotations_activated": self.total_rotations_activated,
            "total_successions_rejected": self.total_successions_rejected,
            "total_boundary_faults_detected": self.total_boundary_faults_detected,
            "created_at": self.created_at,
        }

    def canonical_hash(self) -> str:
        return hashlib.sha256(
            canonical_json(self.to_dict()).encode("utf-8")
        ).hexdigest()


# ---------------------------------------------------------------------------
# Gate Results
# ---------------------------------------------------------------------------

@dataclass
class X3GateResult:
    """Result of a single admission gate."""
    gate: str
    passed: bool
    reason: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "gate": self.gate,
            "passed": self.passed,
        }
        if self.reason:
            d["reason"] = self.reason
        if self.detail:
            d["detail"] = self.detail
        return d


# ---------------------------------------------------------------------------
# Admission Gates
# ---------------------------------------------------------------------------

KERNEL_VERSION_ID_X3 = "rsa-replay-regime-x3-v0.1"

VALID_FAMILIES = frozenset(f.value for f in SessionFamilyX3)
VALID_DELEGATION_MODES = frozenset({"LOW", "NEAR_BOUND", "CHURN_ACTIVE"})
MAX_ROTATIONS_PER_SESSION = 5


def gate_6x(
    kernel_version_id: str,
    constitution_hash: str,
    has_x2_sections: bool,
    session_family: str,
) -> X3GateResult:
    """Gate 6X — Preconditions for X-3 session."""
    if kernel_version_id != KERNEL_VERSION_ID_X3:
        return X3GateResult(
            gate="6X", passed=False,
            reason="KERNEL_VERSION_MISMATCH",
            detail=f"Expected {KERNEL_VERSION_ID_X3}, got {kernel_version_id}",
        )
    if not constitution_hash:
        return X3GateResult(
            gate="6X", passed=False,
            reason="CONSTITUTION_MISSING",
        )
    if not has_x2_sections:
        return X3GateResult(
            gate="6X", passed=False,
            reason="X2_SECTIONS_REQUIRED",
            detail="Constitution must have X-2 treaty sections for delegation",
        )
    if session_family not in VALID_FAMILIES:
        return X3GateResult(
            gate="6X", passed=False,
            reason="INVALID_FAMILY",
            detail=f"Family {session_family} not in {sorted(VALID_FAMILIES)}",
        )
    return X3GateResult(gate="6X", passed=True)


def gate_7x(session: X3SessionStart) -> X3GateResult:
    """Gate 7X — X-3 Session Schema Validity."""
    if not session.session_id:
        return X3GateResult(
            gate="7X", passed=False,
            reason="INVALID_FIELD",
            detail="session_id is empty",
        )
    if session.session_length_cycles < 1:
        return X3GateResult(
            gate="7X", passed=False,
            reason="INVALID_FIELD",
            detail="session_length_cycles must be >= 1",
        )
    if session.density_upper_bound <= 0 or session.density_upper_bound > 1.0:
        return X3GateResult(
            gate="7X", passed=False,
            reason="INVALID_FIELD",
            detail="density_upper_bound must be in (0, 1]",
        )
    if session.delegation_state_mode not in VALID_DELEGATION_MODES:
        return X3GateResult(
            gate="7X", passed=False,
            reason="INVALID_FIELD",
            detail=f"delegation_state_mode must be in {sorted(VALID_DELEGATION_MODES)}",
        )
    required_seeds = {"treaty_stream", "action_stream", "succession_stream"}
    if not required_seeds.issubset(set(session.seeds.keys())):
        return X3GateResult(
            gate="7X", passed=False,
            reason="INVALID_FIELD",
            detail=f"seeds must contain {sorted(required_seeds)}",
        )
    # Validate rotation schedule
    for entry in session.rotation_schedule:
        if "cycle" not in entry:
            return X3GateResult(
                gate="7X", passed=False,
                reason="INVALID_FIELD",
                detail="rotation_schedule entry missing 'cycle'",
            )
    if len(session.rotation_schedule) > MAX_ROTATIONS_PER_SESSION:
        return X3GateResult(
            gate="7X", passed=False,
            reason="INVALID_FIELD",
            detail=f"rotation_schedule exceeds max {MAX_ROTATIONS_PER_SESSION}",
        )
    return X3GateResult(gate="7X", passed=True)


def gate_8x(session: X3SessionStart) -> X3GateResult:
    """Gate 8X — Parameter Admissibility."""
    # Rotation cycles must be within session range
    for entry in session.rotation_schedule:
        c = entry.get("cycle", -1)
        if c < 1 or c >= session.session_length_cycles:
            return X3GateResult(
                gate="8X", passed=False,
                reason="ROTATION_OUT_OF_RANGE",
                detail=f"Rotation cycle {c} out of range [1, {session.session_length_cycles})",
            )
    # No duplicate rotation cycles
    rot_cycles = [e["cycle"] for e in session.rotation_schedule]
    if len(rot_cycles) != len(set(rot_cycles)):
        return X3GateResult(
            gate="8X", passed=False,
            reason="DUPLICATE_ROTATION_CYCLE",
            detail="rotation_schedule has duplicate cycles",
        )
    # Ratification delay must be positive
    if session.ratification_delay_cycles < 1:
        return X3GateResult(
            gate="8X", passed=False,
            reason="INVALID_FIELD",
            detail="ratification_delay_cycles must be >= 1",
        )
    return X3GateResult(gate="8X", passed=True)


def admit_session(
    session: X3SessionStart,
    kernel_version_id: str,
    constitution_hash: str,
    has_x2_sections: bool,
) -> List[X3GateResult]:
    """Run all 3 admission gates. Returns list of gate results."""
    results: List[X3GateResult] = []

    g6 = gate_6x(kernel_version_id, constitution_hash, has_x2_sections,
                  session.session_family)
    results.append(g6)
    if not g6.passed:
        return results

    g7 = gate_7x(session)
    results.append(g7)
    if not g7.passed:
        return results

    g8 = gate_8x(session)
    results.append(g8)
    return results
