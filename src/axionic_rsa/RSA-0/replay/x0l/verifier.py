"""
X-0L Replay Verifier

Replays logged canonicalized artifacts through the kernel to verify
zero-divergence determinism.

Per Q19: replay uses canonicalized artifacts only (not raw LLM text).
Per Q20: replay/x0l/ — reuses kernel replay core with canonicalized injection.
Per Q21: verifies pipeline integrity (logging corruption, parser instability).

Sequential replay: state evolves across cycles.
Constitution loaded fresh and hash recomputed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    DecisionType,
    InternalState,
    Observation,
    ObservationKind,
    Author,
    CandidateBundle,
    canonical_json,
)
from kernel.src.constitution import Constitution
from kernel.src.policy_core import PolicyOutput, policy_core

from profiling.x0l.harness.src.cycle_runner import (
    LiveConditionRunResult,
    LiveCycleResult,
    CycleLogEntry,
    parse_candidates_from_json,
)


# ---------------------------------------------------------------------------
# Replay result containers
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
        if self.divergence_detail:
            d["divergence_detail"] = self.divergence_detail
        return d


@dataclass
class ReplayVerificationResult:
    """Result of replaying an entire condition."""
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
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Core replay logic
# ---------------------------------------------------------------------------

def _reconstruct_observations(log_entry: CycleLogEntry) -> List[Observation]:
    """Reconstruct Observation objects from logged dicts."""
    observations = []
    for obs_dict in log_entry.observations:
        observations.append(Observation(
            kind=obs_dict.get("kind", ""),
            payload=obs_dict.get("payload", {}),
            author=obs_dict.get("author", ""),
            created_at=obs_dict.get("created_at", ""),
            id=obs_dict.get("id", ""),
        ))
    return observations


def _reconstruct_candidates(log_entry: CycleLogEntry) -> List[CandidateBundle]:
    """Reconstruct CandidateBundle objects from logged parsed candidates.

    Per Q19: replay uses canonicalized artifact (parsed candidates), not raw LLM text.
    """
    if not log_entry.parsed_candidates:
        return []

    # The parsed_candidates are already dicts matching CandidateBundle.to_dict() output
    # We need to reconstruct from the "candidates" wrapper format
    bundles, _ = parse_candidates_from_json(
        {"candidates": log_entry.parsed_candidates}
    )
    return bundles


def verify_condition_replay(
    condition_result: LiveConditionRunResult,
    constitution_path: Path,
    repo_root: Path,
    expected_constitution_hash: str,
) -> ReplayVerificationResult:
    """Replay an entire condition and verify zero divergence.

    Sequential replay per DB5: state evolves.
    Constitution loaded fresh per CD10.
    Candidates injected from logged canonicalized artifacts (Q19).
    """
    constitution = Constitution(str(constitution_path))
    actual_hash = constitution.sha256

    result = ReplayVerificationResult(
        condition=condition_result.condition,
        run_id=condition_result.run_id,
        constitution_hash=actual_hash,
    )

    # Verify constitution hash
    if actual_hash != expected_constitution_hash:
        result.passed = False
        result.error = (
            f"Constitution hash mismatch: "
            f"expected {expected_constitution_hash}, got {actual_hash}"
        )
        return result

    # Sequential replay
    state = InternalState(cycle_index=0, last_decision="NONE")

    for original, log_entry in zip(
        condition_result.cycle_results,
        condition_result.log_entries,
    ):
        # Reconstruct inputs from log
        observations = _reconstruct_observations(log_entry)
        candidates = _reconstruct_candidates(log_entry)

        # Replay through kernel
        try:
            replayed_output: PolicyOutput = policy_core(
                observations=observations,
                constitution=constitution,
                internal_state=state,
                candidates=candidates,
                repo_root=repo_root,
            )
        except Exception as e:
            result.passed = False
            result.error = f"Replay exception at {log_entry.cycle_id}: {e}"
            break

        replayed_decision = replayed_output.decision
        original_decision_type = original.decision_type
        replayed_decision_type = replayed_decision.decision_type

        # Verify: decision type + warrant hash + refusal reason
        passed = True
        divergence_detail = None

        if original_decision_type != replayed_decision_type:
            passed = False
            divergence_detail = (
                f"Decision type: {original_decision_type} != {replayed_decision_type}"
            )
        elif original_decision_type == DecisionType.ACTION.value:
            original_warrant = original.warrant_id
            replayed_warrant = (
                replayed_decision.warrant.warrant_id
                if replayed_decision.warrant else None
            )
            if original_warrant != replayed_warrant:
                passed = False
                divergence_detail = (
                    f"Warrant: {original_warrant} != {replayed_warrant}"
                )
        elif original_decision_type == DecisionType.REFUSE.value:
            original_refusal = original.refusal_reason
            replayed_refusal = (
                replayed_decision.refusal.reason_code
                if replayed_decision.refusal else None
            )
            if original_refusal != replayed_refusal:
                passed = False
                divergence_detail = (
                    f"Refusal: {original_refusal} != {replayed_refusal}"
                )

        verification = ReplayCycleVerification(
            cycle_id=log_entry.cycle_id,
            passed=passed,
            original_decision=original_decision_type,
            replayed_decision=replayed_decision_type,
            divergence_detail=divergence_detail,
        )
        result.cycle_verifications.append(verification)
        result.n_cycles_verified += 1

        if not passed:
            result.n_divergences += 1
            result.passed = False

        # Advance state
        state = state.advance(replayed_decision_type)

        if replayed_decision_type == DecisionType.EXIT.value:
            break

    return result
