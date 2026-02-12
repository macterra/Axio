"""
X-0P Baseline Agents

Two minimal baselines for distributional contrast (per instructions §4):

1. Always-Refuse: every observation → REFUSE (no admission, no warrants)
2. Always-Admit: admit any ActionRequest within IO allowlist
   (no selector logic beyond first valid, no authority citation enforcement)

Baselines are decision-only — no execution (per CB4).
Baselines run on identical condition manifests (per BC9).
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    ActionType,
    DecisionType,
    canonical_json,
)

from profiling.x0p.harness.src.generator_common import CycleInput, ConditionManifest


# ---------------------------------------------------------------------------
# Baseline result (minimal struct per BC7)
# ---------------------------------------------------------------------------

@dataclass
class BaselineCycleResult:
    """Result of a single baseline cycle. Minimal struct per BC7."""
    cycle_id: str
    condition: str
    baseline_type: str  # "always_refuse" | "always_admit"
    decision_type: str
    input_hash: str
    baseline_execution: str = "SKIPPED"  # Always SKIPPED per CB4
    warrant_id: Optional[str] = None  # Would-have-issued
    refusal_reason: Optional[str] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "condition": self.condition,
            "baseline_type": self.baseline_type,
            "decision_type": self.decision_type,
            "input_hash": self.input_hash,
            "baseline_execution": self.baseline_execution,
            "warrant_id": self.warrant_id,
            "refusal_reason": self.refusal_reason,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }


@dataclass
class BaselineRunResult:
    """Result of running a baseline on a condition."""
    baseline_type: str
    condition: str
    run_id: str
    manifest_hash: str
    n_cycles: int
    cycle_results: List[BaselineCycleResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_type": self.baseline_type,
            "condition": self.condition,
            "run_id": self.run_id,
            "manifest_hash": self.manifest_hash,
            "n_cycles": self.n_cycles,
            "cycle_results": [cr.to_dict() for cr in self.cycle_results],
        }


# ---------------------------------------------------------------------------
# IO allowlist for Always-Admit (per E15: enforce closed action-type + IO)
# ---------------------------------------------------------------------------

_CLOSED_ACTION_TYPES = {
    ActionType.NOTIFY.value,
    ActionType.READ_LOCAL.value,
    ActionType.WRITE_LOCAL.value,
    ActionType.EXIT.value,
    ActionType.LOG_APPEND.value,
}

_READ_PREFIXES = ["./artifacts/", "./workspace/"]
_WRITE_PREFIXES = ["./workspace/", "./logs/"]


def _is_io_allowed(action_type: str, fields: Dict[str, Any]) -> bool:
    """Check if action is within IO allowlist (minimal enforcement)."""
    if action_type not in _CLOSED_ACTION_TYPES:
        return False

    if action_type == ActionType.READ_LOCAL.value:
        path = fields.get("path", "")
        return any(path.startswith(p) for p in _READ_PREFIXES)

    if action_type == ActionType.WRITE_LOCAL.value:
        path = fields.get("path", "")
        return any(path.startswith(p) for p in _WRITE_PREFIXES)

    # Notify, Exit, LogAppend — no path-based restriction
    return True


# ---------------------------------------------------------------------------
# Always-Refuse baseline
# ---------------------------------------------------------------------------

def run_always_refuse(
    manifest: ConditionManifest,
) -> BaselineRunResult:
    """Always-Refuse: every cycle → REFUSE. No admission logic."""
    run_id = str(uuid.uuid4())
    result = BaselineRunResult(
        baseline_type="always_refuse",
        condition=manifest.condition,
        run_id=run_id,
        manifest_hash=manifest.manifest_hash(),
        n_cycles=manifest.n_cycles,
    )

    for cycle_input in manifest.cycles:
        t0 = time.perf_counter()
        # Trivial decision: always refuse
        t1 = time.perf_counter()

        cycle_result = BaselineCycleResult(
            cycle_id=cycle_input.cycle_id,
            condition=cycle_input.condition,
            baseline_type="always_refuse",
            decision_type=DecisionType.REFUSE.value,
            input_hash=cycle_input.input_hash(),
            refusal_reason="BASELINE_ALWAYS_REFUSE",
            latency_ms=(t1 - t0) * 1000.0,
            metadata=cycle_input.metadata,
        )
        result.cycle_results.append(cycle_result)

    return result


# ---------------------------------------------------------------------------
# Always-Admit baseline
# ---------------------------------------------------------------------------

def run_always_admit(
    manifest: ConditionManifest,
) -> BaselineRunResult:
    """Always-Admit: admit first valid ActionRequest within IO allowlist.

    Per E15: bypasses gates 2–4 but still enforces closed action-type
    set and IO/tool allowlist. Decision-only, no execution.
    """
    run_id = str(uuid.uuid4())
    result = BaselineRunResult(
        baseline_type="always_admit",
        condition=manifest.condition,
        run_id=run_id,
        manifest_hash=manifest.manifest_hash(),
        n_cycles=manifest.n_cycles,
    )

    for cycle_input in manifest.cycles:
        t0 = time.perf_counter()

        decision_type = DecisionType.REFUSE.value
        would_warrant_id = None

        # Try to find first candidate within IO allowlist
        for candidate in cycle_input.candidates:
            ar = candidate.action_request
            if _is_io_allowed(ar.action_type, ar.fields):
                decision_type = DecisionType.ACTION.value
                # Would-have-issued warrant ID (deterministic hash)
                would_warrant_id = hashlib.sha256(
                    canonical_json({
                        "baseline": "always_admit",
                        "cycle_id": cycle_input.cycle_id,
                        "action_request_id": ar.id,
                    }).encode("utf-8")
                ).hexdigest()
                break

        t1 = time.perf_counter()

        cycle_result = BaselineCycleResult(
            cycle_id=cycle_input.cycle_id,
            condition=cycle_input.condition,
            baseline_type="always_admit",
            decision_type=decision_type,
            input_hash=cycle_input.input_hash(),
            warrant_id=would_warrant_id,
            refusal_reason="BASELINE_IO_VIOLATION" if decision_type == DecisionType.REFUSE.value else None,
            latency_ms=(t1 - t0) * 1000.0,
            metadata=cycle_input.metadata,
        )
        result.cycle_results.append(cycle_result)

    return result
