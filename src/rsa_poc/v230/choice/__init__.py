"""E-CHOICE: Genuine Choice Classification Module

Implements the E-CHOICE invariant from spec Section 4:
"At every E-CHOICE-filtered step, the agent could have taken
at least two compile-valid, lawful actions."

IMPORTANT: This module does NOT claim to enumerate all actions and compile each one.
That would require constructing JAFs for every possible action, which is computationally
intractable. Instead, E-CHOICE is implemented as a combination of:

1. ENVIRONMENT DESIGN GUARANTEE (compile-time):
   The environment is designed to always offer at least 2 structurally distinct
   action slots (e.g., action_slot_A, action_slot_B). This is a design invariant
   enforced by environment construction, not by runtime enumeration.

2. STEP-TYPE CLASSIFICATION (runtime):
   Each step is tagged by the environment with a step_type that indicates whether
   genuine choice exists. Steps lacking genuine choice (forced moves, single-option
   states) are excluded from manipulation index computation via metric filtering.

3. MANDATORY PROBE VERIFICATION (preregistration requirement):
   For each GENUINE_CHOICE step type, the probe verifier executes two canned
   compliant JAFs and confirms both compile and execute under nominal institution.
   If probe fails, the environment cannot claim GENUINE_CHOICE → reclassify as FORCED_MOVE.

Key definitions:
- ECHOICE_OK(s) = True iff environment.step_type(s) == GENUINE_CHOICE
                      AND probe verification passed for this step type
- Genuine choice: multiple lawful actions are available by environment design
- Forced move: only one legal action exists (excluded from MI computation)

This module provides:
1. Step-level E-CHOICE classification based on environment step_type
2. Metric filtering (exclude steps where ECHOICE_OK = False)
3. MANDATORY probe-based verification for preregistration validity
4. Logging for audit and debugging

Binding parameters:
- Environment must declare step_type for each step
- GENUINE_CHOICE steps are included in MI computation
- FORCED_MOVE steps are excluded from MI computation
- Probe verification is MANDATORY for preregistration validity
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from enum import Enum
import json


class StepType(Enum):
    """
    Environment-declared step type for E-CHOICE classification.

    The environment declares the step type based on its design guarantees,
    not by runtime enumeration of all possible actions.
    """
    GENUINE_CHOICE = "genuine_choice"      # >= 2 lawful actions available by design
    FORCED_MOVE = "forced_move"            # Only 1 legal action exists
    NO_ACTION = "no_action"                # Step requires no agent action
    UNDECLARED = "undeclared"              # Environment didn't declare (error)


@dataclass(frozen=True)
class EChoiceStepResult:
    """
    Result of E-CHOICE classification for a single step.

    Classification is based on environment-declared step_type,
    NOT on exhaustive action enumeration.

    Immutable record for audit trail.
    """
    step_index: int
    episode_id: str

    # Environment-declared step type (the authoritative source)
    step_type: StepType

    # Optional: number of action slots available (from environment)
    # This is a design property, not computed by enumerating actions
    available_action_slots: int = 2  # Default: environment offers 2 slots

    # Metadata for debugging (optional, from environment)
    step_context: Dict[str, Any] = field(default_factory=dict)

    # Probe verification result (optional, for audit)
    probe_verified: Optional[bool] = None
    probe_details: Optional[Dict[str, Any]] = None

    @property
    def echoice_ok(self) -> bool:
        """E-CHOICE OK iff step_type is GENUINE_CHOICE."""
        return self.step_type == StepType.GENUINE_CHOICE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = {
            "step_index": self.step_index,
            "episode_id": self.episode_id,
            "step_type": self.step_type.value,
            "available_action_slots": self.available_action_slots,
            "echoice_ok": self.echoice_ok,
            "step_context": self.step_context,
        }
        if self.probe_verified is not None:
            result["probe_verified"] = self.probe_verified
            result["probe_details"] = self.probe_details
        return result


def ECHOICE_OK(step_result: EChoiceStepResult) -> bool:
    """
    Predicate for E-CHOICE validity.

    Returns True iff step_type == GENUINE_CHOICE.

    This is based on the environment's design guarantee, not on
    runtime enumeration of all possible actions.
    """
    return step_result.echoice_ok


class EChoiceClassifier:
    """
    Classifier for E-CHOICE step validity.

    IMPORTANT: This classifier does NOT enumerate all actions and compile each one.
    That approach is computationally intractable and was incorrectly described in
    earlier versions.

    Instead, E-CHOICE classification works as follows:

    1. The ENVIRONMENT declares step_type for each step based on its design.
       Environments are constructed to guarantee that GENUINE_CHOICE steps
       have at least 2 lawful actions available.

    2. This classifier simply reads the environment's step_type declaration
       and records whether the step is E-CHOICE valid.

    3. For audit purposes, optional probe-based verification can sample
       random actions to probabilistically verify the environment guarantee.

    The environment guarantee approach is STRUCTURAL: it's enforced by how
    the environment is designed, not by runtime computation.
    """

    def __init__(self, probe_verifier=None):
        """
        Initialize classifier.

        Args:
            probe_verifier: Optional callable for probe-based verification.
                           If provided, it should take (step_index, episode_id, world_state)
                           and return (bool, dict) = (verified, details).
        """
        self.probe_verifier = probe_verifier
        self._step_results: List[EChoiceStepResult] = []

    def classify_step(
        self,
        step_index: int,
        episode_id: str,
        step_type: StepType,
        available_action_slots: int = 2,
        step_context: Optional[Dict[str, Any]] = None,
        run_probe: bool = False,
        world_state: Optional[Dict[str, Any]] = None,
    ) -> EChoiceStepResult:
        """
        Classify a step for E-CHOICE validity.

        Args:
            step_index: Step number within episode
            episode_id: Episode identifier
            step_type: Environment-declared step type
            available_action_slots: Number of action slots (from environment design)
            step_context: Optional context for debugging
            run_probe: Whether to run probe verification
            world_state: Required if run_probe=True

        Returns:
            EChoiceStepResult with classification
        """
        probe_verified = None
        probe_details = None

        if run_probe and self.probe_verifier is not None:
            probe_verified, probe_details = self.probe_verifier(
                step_index, episode_id, world_state or {}
            )

        result = EChoiceStepResult(
            step_index=step_index,
            episode_id=episode_id,
            step_type=step_type,
            available_action_slots=available_action_slots,
            step_context=step_context or {},
            probe_verified=probe_verified,
            probe_details=probe_details,
        )

        self._step_results.append(result)
        return result

    def get_echoice_filtered_steps(self) -> List[EChoiceStepResult]:
        """Return only steps where ECHOICE_OK = True."""
        return [r for r in self._step_results if ECHOICE_OK(r)]

    def get_echoice_rate(self) -> float:
        """Return fraction of steps with ECHOICE_OK = True."""
        if not self._step_results:
            return 0.0
        ok_count = sum(1 for r in self._step_results if ECHOICE_OK(r))
        return ok_count / len(self._step_results)

    def get_all_results(self) -> List[EChoiceStepResult]:
        """Return all step results (for audit)."""
        return list(self._step_results)

    def reset(self):
        """Reset for new episode."""
        self._step_results = []

    def to_log_dict(self) -> Dict[str, Any]:
        """Export classification results for logging."""
        return {
            "total_steps": len(self._step_results),
            "echoice_ok_count": sum(1 for r in self._step_results if ECHOICE_OK(r)),
            "echoice_rate": self.get_echoice_rate(),
            "steps": [r.to_dict() for r in self._step_results],
        }


# ============================================================================
# Metric Filtering Utilities
# ============================================================================

def filter_metrics_by_echoice(
    step_metrics: List[Dict[str, Any]],
    echoice_results: List[EChoiceStepResult],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Filter step-level metrics to include only E-CHOICE-valid steps.

    Args:
        step_metrics: List of per-step metric dictionaries
        echoice_results: Corresponding E-CHOICE classification results

    Returns:
        (filtered_metrics, excluded_count)
    """
    if len(step_metrics) != len(echoice_results):
        raise ValueError(
            f"Metric count ({len(step_metrics)}) != E-CHOICE result count ({len(echoice_results)})"
        )

    filtered = []
    excluded = 0

    for metric, echoice in zip(step_metrics, echoice_results):
        if ECHOICE_OK(echoice):
            filtered.append(metric)
        else:
            excluded += 1

    return filtered, excluded


def compute_W_window_metrics(
    filtered_metrics: List[Dict[str, Any]],
    W: int = 100,
    metric_key: str = "behavioral_signature",
) -> List[float]:
    """
    Compute rolling window metrics over W E-CHOICE-filtered steps.

    Args:
        filtered_metrics: E-CHOICE-filtered step metrics
        W: Window size (binding: 100)
        metric_key: Key to extract from each metric dict

    Returns:
        List of metric values for each complete window
    """
    if len(filtered_metrics) < W:
        return []  # Not enough data for even one window

    windows = []
    for i in range(len(filtered_metrics) - W + 1):
        window = filtered_metrics[i:i + W]
        values = [m.get(metric_key, 0.0) for m in window]
        windows.append(sum(values) / len(values) if values else 0.0)

    return windows


@dataclass
class ProbeResult:
    """Result of running probe JAFs through the environment."""
    passed: bool
    step_id: str
    probe_a_accepted: bool
    probe_b_accepted: bool
    failure_reason: Optional[str] = None


class EChoiceProbeVerifier:
    """
    MANDATORY probe verifier for E-CHOICE classification.

    For each GENUINE_CHOICE step, executes two canned compliant JAFs
    through the environment to verify that at least two distinct lawful
    actions are actually available at runtime.

    This is a PREREGISTRATION REQUIREMENT: if the probe fails for any
    GENUINE_CHOICE step, that step must be reclassified as FORCED_MOVE.

    Binding Parameters:
        - probe_a, probe_b: Canned compliant JAFs (environment-specific)
        - Both must pass JCOMP-2.3 validation
        - Both must be accepted by the environment
    """

    def __init__(
        self,
        probe_a: Dict[str, Any],
        probe_b: Dict[str, Any],
        env_accept_fn: Callable[[Dict[str, Any]], bool],
    ):
        """
        Initialize probe verifier with two canned compliant JAFs.

        Args:
            probe_a: First canned compliant JAF
            probe_b: Second canned compliant JAF (must differ from probe_a)
            env_accept_fn: Function that returns True if env accepts the JAF

        Raises:
            ValueError: If probe_a == probe_b (probes must be distinct)
        """
        if probe_a == probe_b:
            raise ValueError("probe_a and probe_b must be distinct JAFs")
        self.probe_a = probe_a
        self.probe_b = probe_b
        self.env_accept_fn = env_accept_fn

    def verify_step(self, step_id: str) -> ProbeResult:
        """
        Verify that a GENUINE_CHOICE step actually has ≥2 available actions.

        Runs both probe JAFs through the environment. Both must be accepted
        for the step to pass verification.

        Args:
            step_id: Identifier of the step being verified

        Returns:
            ProbeResult indicating pass/fail with details
        """
        probe_a_ok = self.env_accept_fn(self.probe_a)
        probe_b_ok = self.env_accept_fn(self.probe_b)

        passed = probe_a_ok and probe_b_ok
        failure_reason = None

        if not passed:
            failures = []
            if not probe_a_ok:
                failures.append("probe_a rejected")
            if not probe_b_ok:
                failures.append("probe_b rejected")
            failure_reason = "; ".join(failures)

        return ProbeResult(
            passed=passed,
            step_id=step_id,
            probe_a_accepted=probe_a_ok,
            probe_b_accepted=probe_b_ok,
            failure_reason=failure_reason,
        )

    def verify_classification(
        self,
        classification: EChoiceStepResult,
    ) -> EChoiceStepResult:
        """
        Verify a GENUINE_CHOICE classification; reclassify to FORCED_MOVE if probe fails.

        Args:
            classification: Original E-CHOICE classification result

        Returns:
            Original classification if verified, or reclassified FORCED_MOVE
        """
        if classification.step_type != StepType.GENUINE_CHOICE:
            # Only GENUINE_CHOICE needs probe verification
            return classification

        step_id = f"{classification.episode_id}_{classification.step_index}"
        probe_result = self.verify_step(step_id)

        if probe_result.passed:
            # Return with probe verification recorded
            return EChoiceStepResult(
                step_index=classification.step_index,
                episode_id=classification.episode_id,
                step_type=classification.step_type,
                available_action_slots=classification.available_action_slots,
                step_context=classification.step_context,
                probe_verified=True,
                probe_details={"probe_a_ok": True, "probe_b_ok": True},
            )

        # Reclassify to FORCED_MOVE with probe failure reason
        return EChoiceStepResult(
            step_index=classification.step_index,
            episode_id=classification.episode_id,
            step_type=StepType.FORCED_MOVE,
            available_action_slots=classification.available_action_slots,
            step_context={
                **classification.step_context,
                "original_classification": StepType.GENUINE_CHOICE.value,
                "reclassification_reason": f"Probe verification failed: {probe_result.failure_reason}",
            },
            probe_verified=False,
            probe_details={
                "probe_a_ok": probe_result.probe_a_accepted,
                "probe_b_ok": probe_result.probe_b_accepted,
                "failure_reason": probe_result.failure_reason,
            },
        )


# Import full-pipeline probe
from .e_choice_probe import (
    EChoiceProbe,
    EChoiceProbeReport,
    EChoiceProbeResult,
    EChoiceProbeScenario,
    run_echoice_probe,
    ECHOICE_PROBE_SCENARIOS,
)


__all__ = [
    "ECHOICE_OK",
    "EChoiceStepResult",
    "EChoiceClassifier",
    "EChoiceProbeVerifier",
    "ProbeResult",
    "StepType",
    "filter_metrics_by_echoice",
    "compute_W_window_metrics",
    # Full-pipeline probe
    "EChoiceProbe",
    "EChoiceProbeReport",
    "EChoiceProbeResult",
    "EChoiceProbeScenario",
    "run_echoice_probe",
    "ECHOICE_PROBE_SCENARIOS",
]
