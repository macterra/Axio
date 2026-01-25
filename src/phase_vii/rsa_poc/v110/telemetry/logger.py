"""Telemetry Logger for v1.1

Per-step JSON Lines logging with Jaccard metrics and symmetric diff diagnostics.

Required for v1.1 audit analysis and debugging.
"""

import json
from pathlib import Path
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, asdict

# Import components
try:
    from ..jaf.schema import JAF110
    from ..jcomp.compiler import CompilationResult
    from ..agent import StepResult
except ImportError:
    from src.rsa_poc.v110.jaf.schema import JAF110
    from src.rsa_poc.v110.jcomp.compiler import CompilationResult
    from src.rsa_poc.v110.agent import StepResult


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Compute Jaccard similarity between two sets.

    J(A,B) = |A ∩ B| / |A ∪ B|

    Special case: J(∅,∅) = 1.0

    Args:
        set_a: First set
        set_b: Second set

    Returns:
        Jaccard similarity in [0, 1]
    """
    if not set_a and not set_b:
        return 1.0

    union_size = len(set_a | set_b)
    if union_size == 0:
        return 1.0

    intersection_size = len(set_a & set_b)
    return intersection_size / union_size


def symmetric_diff_size(set_a: Set[str], set_b: Set[str]) -> int:
    """
    Compute symmetric difference size.

    |A △ B| = |A ∪ B| - |A ∩ B|

    Args:
        set_a: First set
        set_b: Second set

    Returns:
        Size of symmetric difference
    """
    return len(set_a ^ set_b)


@dataclass
class StepTelemetryV110:
    """Per-step telemetry record for v1.1"""
    step: int
    agent_id: str

    # Feasible action state
    feasible_actions: list
    feasible_action_count: int

    # JAF v1.1 fields
    authorized_violations: list
    required_preservations: list
    conflict_attribution: list
    conflict_resolution_mode: Optional[str]

    # v1.1 Predictions
    predicted_forbidden_actions: list
    predicted_allowed_actions: list
    predicted_violations: list
    predicted_preservations: list

    # Compilation results
    compile_ok: bool
    error_codes: list

    # Actual sets (post-compilation)
    actual_forbidden_actions: list
    actual_allowed_actions: list
    actual_violations: Optional[list]  # None if gridlock
    actual_preservations: Optional[list]  # None if gridlock

    # v1.1 Audit metrics (Jaccard similarity)
    jaccard_forbidden: Optional[float]
    jaccard_allowed: Optional[float]
    jaccard_violations: Optional[float]
    jaccard_preservations: Optional[float]

    # v1.1 Audit metrics (symmetric diff)
    symdiff_forbidden: Optional[int]
    symdiff_allowed: Optional[int]
    symdiff_violations: Optional[int]
    symdiff_preservations: Optional[int]

    # Action selection
    selected_action: Optional[str]

    # Outcome
    reward: float
    done: bool
    halted: bool
    halt_reason: Optional[str]

    # Environment info
    is_collision_step: bool
    violated_prefs: list

    # Gridlock flag
    gridlock: bool

    # Bypass metrics (v1.1 Fix 4) - Optional for bypass condition only
    mask_applied: Optional[bool] = None
    selected_in_allowed: Optional[bool] = None


class TelemetryLoggerV110:
    """
    v1.1 Telemetry logger with per-step JSONL output.

    Logs:
    - Predicted vs actual sets
    - Jaccard similarity metrics
    - Symmetric diff counts
    - Compilation success/failure
    - Audit-specific error codes
    """

    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize telemetry logger.

        Args:
            log_path: Path to JSONL log file (if None, logging disabled)
        """
        self.log_path = log_path
        self.step_records = []

        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            # Clear file if exists
            if log_path.exists():
                log_path.unlink()

    def log_step(
        self,
        step_result: StepResult,
        feasible_actions: list,
        apcm: Dict[str, Dict[str, Set[str]]],
        agent_id: str
    ):
        """
        Log one step with full v1.1 diagnostics.

        Args:
            step_result: StepResult from agent step
            feasible_actions: Feasible actions for this step
            apcm: Action-Preference Consequence Map
            agent_id: Agent identifier
        """
        jaf = step_result.jaf
        comp_result = step_result.compilation_result

        if not jaf:
            # No JAF (halted or error)
            return

        # Compute actual sets from compilation
        feasible_set = set(feasible_actions)

        if comp_result and comp_result.success:
            actual_forbidden = comp_result.action_mask
            actual_allowed = feasible_set - actual_forbidden
            gridlock = len(actual_allowed) == 0

            # Compute inevitable outcomes (only if not gridlock)
            if not gridlock:
                actual_violations, actual_preservations = self._compute_inevitable_outcomes(
                    actual_allowed, apcm, jaf
                )
            else:
                actual_violations, actual_preservations = None, None
        else:
            # Compilation failed - use empty sets
            actual_forbidden = set()
            actual_allowed = feasible_set
            gridlock = False
            actual_violations, actual_preservations = set(), set()

        # Compute Jaccard metrics
        jaccard_forbidden = jaccard_similarity(jaf.predicted_forbidden_actions, actual_forbidden)
        jaccard_allowed = jaccard_similarity(jaf.predicted_allowed_actions, actual_allowed)

        if not gridlock and actual_violations is not None:
            jaccard_violations = jaccard_similarity(jaf.predicted_violations, actual_violations)
            jaccard_preservations = jaccard_similarity(jaf.predicted_preservations, actual_preservations)
        else:
            jaccard_violations = None
            jaccard_preservations = None

        # Compute symmetric diff sizes
        symdiff_forbidden = symmetric_diff_size(jaf.predicted_forbidden_actions, actual_forbidden)
        symdiff_allowed = symmetric_diff_size(jaf.predicted_allowed_actions, actual_allowed)

        if not gridlock and actual_violations is not None:
            symdiff_violations = symmetric_diff_size(jaf.predicted_violations, actual_violations)
            symdiff_preservations = symmetric_diff_size(jaf.predicted_preservations, actual_preservations)
        else:
            symdiff_violations = None
            symdiff_preservations = None

        # Extract error codes
        error_codes = []
        if comp_result and not comp_result.success:
            error_codes = [e.code for e in comp_result.errors]

        # Build telemetry record
        record = StepTelemetryV110(
            step=step_result.step,
            agent_id=agent_id,
            feasible_actions=sorted(feasible_actions),
            feasible_action_count=len(feasible_actions),
            authorized_violations=sorted(list(jaf.authorized_violations)),
            required_preservations=sorted(list(jaf.required_preservations)),
            conflict_attribution=[list(p) for p in sorted(jaf.conflict_attribution)],
            conflict_resolution_mode=jaf.conflict_resolution.mode if jaf.conflict_resolution else None,
            predicted_forbidden_actions=sorted(list(jaf.predicted_forbidden_actions)),
            predicted_allowed_actions=sorted(list(jaf.predicted_allowed_actions)),
            predicted_violations=sorted(list(jaf.predicted_violations)),
            predicted_preservations=sorted(list(jaf.predicted_preservations)),
            compile_ok=comp_result.success if comp_result else False,
            error_codes=error_codes,
            actual_forbidden_actions=sorted(list(actual_forbidden)),
            actual_allowed_actions=sorted(list(actual_allowed)),
            actual_violations=sorted(list(actual_violations)) if actual_violations is not None else None,
            actual_preservations=sorted(list(actual_preservations)) if actual_preservations is not None else None,
            jaccard_forbidden=jaccard_forbidden,
            jaccard_allowed=jaccard_allowed,
            jaccard_violations=jaccard_violations,
            jaccard_preservations=jaccard_preservations,
            symdiff_forbidden=symdiff_forbidden,
            symdiff_allowed=symdiff_allowed,
            symdiff_violations=symdiff_violations,
            symdiff_preservations=symdiff_preservations,
            selected_action=step_result.selected_action,
            reward=step_result.reward,
            done=step_result.done,
            halted=step_result.halted,
            halt_reason=step_result.halt_reason,
            is_collision_step=step_result.info.get("is_collision_step", False),
            violated_prefs=sorted(step_result.info.get("violated_prefs", [])),
            gridlock=gridlock,
            # Bypass metrics (v1.1 Fix 4)
            mask_applied=step_result.info.get("mask_applied"),
            selected_in_allowed=step_result.info.get("selected_in_allowed")
        )

        self.step_records.append(record)

        # Write to JSONL if path provided
        if self.log_path:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(asdict(record)) + '\n')

    def _compute_inevitable_outcomes(
        self,
        allowed_actions: Set[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        jaf: JAF110
    ) -> tuple:
        """
        Compute inevitable violations and preservations.

        V_actual = preferences violated by ALL allowed actions
        P_actual = preferences satisfied by ALL allowed actions

        Returns: (V_actual, P_actual)
        """
        all_prefs = jaf.references.pref_ids

        # V_actual: violated by ALL actions
        violations = None
        for action in allowed_actions:
            if action not in apcm:
                continue

            satisfied_by_action = set()
            for outcome, prefs in apcm[action].items():
                satisfied_by_action.update(prefs)

            violated_by_action = set(all_prefs) - satisfied_by_action

            if violations is None:
                violations = violated_by_action
            else:
                violations = violations & violated_by_action

        if violations is None:
            violations = set()

        # P_actual: satisfied by ALL actions (all outcomes)
        preservations = None
        for action in allowed_actions:
            if action not in apcm:
                continue

            satisfied_by_all_outcomes = None
            for outcome, prefs in apcm[action].items():
                if satisfied_by_all_outcomes is None:
                    satisfied_by_all_outcomes = prefs.copy()
                else:
                    satisfied_by_all_outcomes = satisfied_by_all_outcomes & prefs

            if satisfied_by_all_outcomes is None:
                satisfied_by_all_outcomes = set()

            if preservations is None:
                preservations = satisfied_by_all_outcomes
            else:
                preservations = preservations & satisfied_by_all_outcomes

        if preservations is None:
            preservations = set()

        return violations, preservations

    def get_episode_summary(self) -> Dict[str, Any]:
        """
        Compute episode-level aggregate metrics.

        Returns:
            Dictionary with mean Jaccard scores, error counts, etc.
        """
        if not self.step_records:
            return {}

        # Aggregate Jaccard metrics
        jaccard_scores = {
            "forbidden": [r.jaccard_forbidden for r in self.step_records if r.jaccard_forbidden is not None],
            "allowed": [r.jaccard_allowed for r in self.step_records if r.jaccard_allowed is not None],
            "violations": [r.jaccard_violations for r in self.step_records if r.jaccard_violations is not None],
            "preservations": [r.jaccard_preservations for r in self.step_records if r.jaccard_preservations is not None]
        }

        mean_jaccard = {
            "forbidden": sum(jaccard_scores["forbidden"]) / len(jaccard_scores["forbidden"]) if jaccard_scores["forbidden"] else None,
            "allowed": sum(jaccard_scores["allowed"]) / len(jaccard_scores["allowed"]) if jaccard_scores["allowed"] else None,
            "violations": sum(jaccard_scores["violations"]) / len(jaccard_scores["violations"]) if jaccard_scores["violations"] else None,
            "preservations": sum(jaccard_scores["preservations"]) / len(jaccard_scores["preservations"]) if jaccard_scores["preservations"] else None
        }

        # Error counts
        error_counts = {}
        for record in self.step_records:
            for error_code in record.error_codes:
                error_counts[error_code] = error_counts.get(error_code, 0) + 1

        # Success rate
        successful_steps = sum(1 for r in self.step_records if r.compile_ok)
        total_steps = len(self.step_records)

        return {
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "success_rate": successful_steps / total_steps if total_steps > 0 else 0.0,
            "mean_jaccard": mean_jaccard,
            "error_counts": error_counts,
            "gridlock_steps": sum(1 for r in self.step_records if r.gridlock),
            "halted": any(r.halted for r in self.step_records)
        }

    def reset(self):
        """Clear step records"""
        self.step_records.clear()
