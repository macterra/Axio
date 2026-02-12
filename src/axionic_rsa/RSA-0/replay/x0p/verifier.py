"""
X-0P Replay Verifier

Dedicated replay verifier for profiling (per BE13).
Sequential replay is required (per DB5) — verifies state evolution,
not just per-cycle determinism.

Replays all logged observations + candidates through policy_core()
and asserts identical:
  - Decision kind (per CD9)
  - Refusal reason (per CD9)
  - Warrant hash (per CD9)

Zero divergence required (per F18).
Constitution loaded fresh and hash recomputed (per CD10/DD9).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    DecisionType,
    InternalState,
    canonical_json,
)
from kernel.src.constitution import Constitution
from kernel.src.policy_core import PolicyOutput, policy_core

from profiling.x0p.harness.src.cycle_runner import CycleResult, ConditionRunResult
from profiling.x0p.harness.src.generator_common import CycleInput, ConditionManifest


# ---------------------------------------------------------------------------
# Replay result
# ---------------------------------------------------------------------------

@dataclass
class ReplayCycleVerification:
    """Result of replaying a single cycle."""
    cycle_id: str
    passed: bool
    original_decision: str
    replayed_decision: str
    original_warrant_hash: Optional[str] = None
    replayed_warrant_hash: Optional[str] = None
    original_refusal_reason: Optional[str] = None
    replayed_refusal_reason: Optional[str] = None
    divergence_detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "cycle_id": self.cycle_id,
            "passed": self.passed,
            "original_decision": self.original_decision,
            "replayed_decision": self.replayed_decision,
        }
        if self.original_warrant_hash:
            d["original_warrant_hash"] = self.original_warrant_hash
        if self.replayed_warrant_hash:
            d["replayed_warrant_hash"] = self.replayed_warrant_hash
        if self.original_refusal_reason:
            d["original_refusal_reason"] = self.original_refusal_reason
        if self.replayed_refusal_reason:
            d["replayed_refusal_reason"] = self.replayed_refusal_reason
        if self.divergence_detail:
            d["divergence_detail"] = self.divergence_detail
        return d


@dataclass
class ReplayVerificationResult:
    """Result of replaying an entire condition run."""
    condition: str
    run_id: str
    constitution_hash: str
    n_cycles_verified: int = 0
    n_divergences: int = 0
    passed: bool = True
    cycle_verifications: List[ReplayCycleVerification] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition": self.condition,
            "run_id": self.run_id,
            "constitution_hash": self.constitution_hash,
            "n_cycles_verified": self.n_cycles_verified,
            "n_divergences": self.n_divergences,
            "passed": self.passed,
            "cycle_verifications": [cv.to_dict() for cv in self.cycle_verifications],
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Core replay logic
# ---------------------------------------------------------------------------

def _warrant_hash(decision) -> Optional[str]:
    """Extract warrant hash from a decision, if present."""
    if decision.warrant:
        return decision.warrant.warrant_id
    return None


def _refusal_reason(decision) -> Optional[str]:
    """Extract refusal reason from a decision, if present."""
    if decision.refusal:
        return decision.refusal.reason_code
    return None


def verify_condition_replay(
    manifest: ConditionManifest,
    original_results: List[CycleResult],
    constitution_path: Path,
    repo_root: Path,
    expected_constitution_hash: str,
) -> ReplayVerificationResult:
    """Replay an entire condition run and verify determinism.

    Sequential replay per DB5: state evolves across cycles.
    Constitution loaded fresh and hash recomputed per CD10.
    """
    # Load constitution fresh (per CD10)
    constitution = Constitution(str(constitution_path))
    actual_hash = constitution.sha256

    result = ReplayVerificationResult(
        condition=manifest.condition,
        run_id="replay",
        constitution_hash=actual_hash,
    )

    # Verify constitution hash (per CD10: do not trust logged hash)
    if actual_hash != expected_constitution_hash:
        result.passed = False
        result.error = f"Constitution hash mismatch: expected {expected_constitution_hash}, got {actual_hash}"
        return result

    # Sequential replay with state evolution
    state = InternalState(cycle_index=0, last_decision="NONE")

    for i, (cycle_input, original) in enumerate(zip(manifest.cycles, original_results)):
        # Replay through policy_core
        try:
            replayed_output: PolicyOutput = policy_core(
                observations=cycle_input.observations,
                constitution=constitution,
                internal_state=state,
                candidates=cycle_input.candidates,
                repo_root=repo_root,
            )
        except Exception as e:
            result.passed = False
            result.error = f"Replay exception at cycle {cycle_input.cycle_id}: {e}"
            break

        replayed_decision = replayed_output.decision

        # Verify per CD9: decision kind + refusal reason + warrant hash
        original_decision_type = original.decision_type
        replayed_decision_type = replayed_decision.decision_type

        original_warrant = original.warrant_id
        replayed_warrant = _warrant_hash(replayed_decision)

        original_refusal = original.refusal_reason
        replayed_refusal = _refusal_reason(replayed_decision)

        passed = True
        divergence_detail = None

        if original_decision_type != replayed_decision_type:
            passed = False
            divergence_detail = f"Decision type: {original_decision_type} != {replayed_decision_type}"
        elif original_decision_type == DecisionType.ACTION.value:
            if original_warrant != replayed_warrant:
                passed = False
                divergence_detail = f"Warrant hash: {original_warrant} != {replayed_warrant}"
        elif original_decision_type == DecisionType.REFUSE.value:
            if original_refusal != replayed_refusal:
                passed = False
                divergence_detail = f"Refusal reason: {original_refusal} != {replayed_refusal}"

        verification = ReplayCycleVerification(
            cycle_id=cycle_input.cycle_id,
            passed=passed,
            original_decision=original_decision_type,
            replayed_decision=replayed_decision_type,
            original_warrant_hash=original_warrant,
            replayed_warrant_hash=replayed_warrant,
            original_refusal_reason=original_refusal,
            replayed_refusal_reason=replayed_refusal,
            divergence_detail=divergence_detail,
        )
        result.cycle_verifications.append(verification)
        result.n_cycles_verified += 1

        if not passed:
            result.n_divergences += 1
            result.passed = False

        # Advance state (sequential replay per DB5)
        state = state.advance(replayed_decision_type)

        # Stop on EXIT
        if replayed_decision_type == DecisionType.EXIT.value:
            break

    return result
