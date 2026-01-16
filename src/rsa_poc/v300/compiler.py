"""v3.0 Compiler with Ablation Relaxation

Extends JCOMP-2.3 with surgical relaxation for ablation runs.
Only the checks corresponding to the ablated component are disabled.

Key principle: relaxation is SURGICAL, not permissive.
- Relax only what's necessary for the ablation to execute
- Preserve selector blindness, action authorship, audit firing
- Convert unexpected crashes to INVALID_RUN/TECHNICAL_FAILURE
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Tuple

# Import v2.3 compiler
try:
    from rsa_poc.v230.compiler import (
        JCOMP230,
        SAMCompilationResult,
        RuleMNOPThresholds,
        RuleMViolation,
        RuleNViolation,
        RuleOViolation,
        RulePViolation,
        GridlockBasis,
    )
except ImportError:
    from ..v230.compiler import (
        JCOMP230,
        SAMCompilationResult,
        RuleMNOPThresholds,
        RuleMViolation,
        RuleNViolation,
        RuleOViolation,
        RulePViolation,
        GridlockBasis,
    )

from .ablation import AblationSpec


# ============================================================================
# Ablation Relaxation Specification
# ============================================================================

@dataclass(frozen=True)
class AblationRelaxation:
    """
    Specifies which compiler checks to relax for a given ablation.

    Relaxation is SURGICAL: only disable checks for the ablated component.
    All other checks remain enforced.
    """
    ablation: AblationSpec

    # Schema relaxation
    skip_semantic_field_validation: bool = False  # For Ablation A
    skip_normative_update_validation: bool = False  # For Ablation B
    skip_persistence_validation: bool = False  # For Ablation C
    skip_trace_validation: bool = False  # For Ablation D

    # Field requirements
    optional_derivation_trace: bool = False  # For Ablation D
    optional_semantic_content: bool = False  # For Ablation A
    optional_normative_update: bool = False  # For Ablation B (already optional usually)

    # Default values for missing fields (to prevent crashes)
    default_on_missing_trace: str = "TRACE_ABLATED"
    default_on_missing_semantic: str = "TOKEN_ABLATED"

    # Convenience properties for tests
    @property
    def allow_missing_justification_trace(self) -> bool:
        """Whether justification_trace can be missing."""
        return self.optional_derivation_trace or self.skip_trace_validation

    @property
    def allow_missing_semantic_content(self) -> bool:
        """Whether semantic_content can be missing."""
        return self.optional_semantic_content

    @property
    def allow_opaque_semantic_tokens(self) -> bool:
        """Whether opaque tokens can replace semantic content."""
        return self.skip_semantic_field_validation


def create_relaxation(ablation: AblationSpec) -> AblationRelaxation:
    """
    Create the appropriate relaxation for an ablation.

    Each ablation has a specific relaxation profile that disables
    only the checks necessary for that ablation to execute.
    """
    if ablation == AblationSpec.NONE:
        # Baseline: no relaxation
        return AblationRelaxation(ablation=ablation)

    elif ablation == AblationSpec.SEMANTIC_EXCISION:
        # Ablation A: relax semantic field validation
        return AblationRelaxation(
            ablation=ablation,
            skip_semantic_field_validation=True,
            optional_semantic_content=True,
        )

    elif ablation == AblationSpec.REFLECTION_EXCISION:
        # Ablation B: relax normative update validation
        return AblationRelaxation(
            ablation=ablation,
            skip_normative_update_validation=True,
            optional_normative_update=True,
        )

    elif ablation == AblationSpec.PERSISTENCE_EXCISION:
        # Ablation C: relax persistence validation
        return AblationRelaxation(
            ablation=ablation,
            skip_persistence_validation=True,
        )

    elif ablation == AblationSpec.TRACE_EXCISION:
        # Ablation D (GOLDEN TEST): relax trace validation
        return AblationRelaxation(
            ablation=ablation,
            skip_trace_validation=True,
            optional_derivation_trace=True,
        )

    else:
        raise ValueError(f"Unknown ablation: {ablation}")


# ============================================================================
# v3.0 Compilation Result
# ============================================================================

@dataclass
class V300CompilationResult(SAMCompilationResult):
    """
    Result of v3.0 compilation with ablation support.

    Extends SAMCompilationResult with ablation-specific tracking.
    """
    # Ablation tracking
    ablation_applied: AblationSpec = AblationSpec.NONE
    relaxation_used: bool = False
    relaxed_checks: List[str] = field(default_factory=list)

    # Field defaulting (when ablation removed required fields)
    fields_defaulted: Dict[str, str] = field(default_factory=dict)

    # Technical failure tracking (for INVALID_RUN classification)
    is_technical_failure: bool = False
    technical_failure_type: Optional[str] = None
    technical_failure_message: Optional[str] = None

    @property
    def valid(self) -> bool:
        """Alias for success (for v3.0 compatibility)."""
        return self.success and not self.is_technical_failure


# ============================================================================
# JCOMP-3.0 Implementation
# ============================================================================

class JCOMP300(JCOMP230):
    """
    JCOMP-3.0: v2.3 compiler with ablation relaxation support.

    When ablation is specified:
    1. Apply surgical relaxation for the ablated component
    2. Provide safe defaults to prevent crashes
    3. Track which checks were relaxed
    4. Preserve all non-ablated checks

    Any unexpected exception is caught and classified as TECHNICAL_FAILURE.
    """

    # v3.0 error codes
    E_TECHNICAL_FAILURE = "E_TECHNICAL_FAILURE"
    E_ABLATION_CRASH = "E_ABLATION_CRASH"

    def __init__(
        self,
        valid_actions: Optional[Set[str]] = None,
        valid_preferences: Optional[Set[str]] = None,
        kr_thresholds: Optional[RuleMNOPThresholds] = None,
        mnop_thresholds: Optional[RuleMNOPThresholds] = None,
        ablation: AblationSpec = AblationSpec.NONE,
    ):
        """
        Initialize JCOMP-3.0.

        Args:
            valid_actions: Known action IDs
            valid_preferences: Known preference IDs
            kr_thresholds: Rule K-R thresholds (from v2.2)
            mnop_thresholds: Rules M/N/O/P thresholds
            ablation: Which component is ablated (or NONE for baseline)
        """
        super().__init__(valid_actions, valid_preferences, kr_thresholds, mnop_thresholds)
        self.ablation = ablation
        self.relaxation = create_relaxation(ablation)

    def compile(
        self,
        artifact_dict: Dict[str, Any],
        action_id: str,
        high_friction: bool = False,
        sam_pressure: Optional[Dict[str, Any]] = None,
        echoice_step: bool = True,
        audit_b_passed: bool = True,
    ) -> V300CompilationResult:
        """
        Compile with ablation-aware relaxation.

        Wraps parent compile with:
        1. Pre-validation field defaulting (to prevent crashes)
        2. Relaxed checks based on ablation
        3. Exception catching for technical failures
        """
        result = V300CompilationResult(
            success=True,  # Will be updated based on compilation
            ablation_applied=self.ablation,
            relaxation_used=(self.ablation != AblationSpec.NONE),
        )

        try:
            # Pre-process: apply defaults for missing fields under ablation
            processed_artifact = self._apply_defaults_for_ablation(
                artifact_dict, result
            )

            # Run parent compilation (v2.3)
            # But skip checks that are relaxed for this ablation
            parent_result = self._compile_with_relaxation(
                processed_artifact, action_id, high_friction,
                sam_pressure, echoice_step, audit_b_passed
            )

            # Copy parent result fields
            result.success = parent_result.success
            result.error_code = getattr(parent_result, 'error_code', None)
            result.error_message = getattr(parent_result, 'error_message', None)
            result.action_id = getattr(parent_result, 'action_id', action_id)  # Fallback to passed action_id
            result.warnings = getattr(parent_result, 'warnings', [])

            # Copy v2.3 fields
            if hasattr(parent_result, 'rule_m_violations'):
                result.rule_m_violations = parent_result.rule_m_violations
            if hasattr(parent_result, 'rule_n_violations'):
                result.rule_n_violations = parent_result.rule_n_violations
            if hasattr(parent_result, 'is_gridlock_step'):
                result.is_gridlock_step = parent_result.is_gridlock_step

            return result

        except KeyError as e:
            # Missing field exception → TECHNICAL_FAILURE
            result.success = False
            result.is_technical_failure = True
            result.technical_failure_type = "missing_field_exception"
            result.technical_failure_message = f"KeyError: {e}"
            result.error_code = self.E_TECHNICAL_FAILURE
            return result

        except TypeError as e:
            # Type error (null/wrong type) → TECHNICAL_FAILURE
            result.success = False
            result.is_technical_failure = True
            result.technical_failure_type = "type_error"
            result.technical_failure_message = f"TypeError: {e}"
            result.error_code = self.E_TECHNICAL_FAILURE
            return result

        except AttributeError as e:
            # Null pointer equivalent → TECHNICAL_FAILURE
            result.success = False
            result.is_technical_failure = True
            result.technical_failure_type = "null_pointer"
            result.technical_failure_message = f"AttributeError: {e}"
            result.error_code = self.E_TECHNICAL_FAILURE
            return result

        except Exception as e:
            # Any other exception → TECHNICAL_FAILURE
            result.success = False
            result.is_technical_failure = True
            result.technical_failure_type = "unexpected_exception"
            result.technical_failure_message = f"{type(e).__name__}: {e}"
            result.error_code = self.E_ABLATION_CRASH
            return result

    def _apply_defaults_for_ablation(
        self,
        artifact_dict: Dict[str, Any],
        result: V300CompilationResult,
    ) -> Dict[str, Any]:
        """
        Apply safe defaults for fields removed by ablation.

        This prevents crashes from missing fields so that behavioral
        effects can be observed instead of technical failures.
        """
        import copy
        processed = copy.deepcopy(artifact_dict)

        if self.ablation == AblationSpec.TRACE_EXCISION:
            # Ablation D: ensure constraint fields exist but trace is empty
            if "derivation_trace" not in processed:
                processed["derivation_trace"] = self.relaxation.default_on_missing_trace
                result.fields_defaulted["derivation_trace"] = "TRACE_ABLATED"
                result.relaxed_checks.append("derivation_trace_required")

        elif self.ablation == AblationSpec.SEMANTIC_EXCISION:
            # Ablation A: ensure semantic fields exist but are tokens
            for field in ["text", "content", "description"]:
                if field in processed and processed[field] is None:
                    processed[field] = self.relaxation.default_on_missing_semantic
                    result.fields_defaulted[field] = "TOKEN_ABLATED"
            result.relaxed_checks.append("semantic_content_required")

        elif self.ablation == AblationSpec.REFLECTION_EXCISION:
            # Ablation B: remove normative update fields
            result.relaxed_checks.append("normative_update_validation")

        elif self.ablation == AblationSpec.PERSISTENCE_EXCISION:
            # Ablation C: mark as non-persistent
            result.relaxed_checks.append("persistence_validation")

        return processed

    def _compile_with_relaxation(
        self,
        artifact_dict: Dict[str, Any],
        action_id: str,
        high_friction: bool,
        sam_pressure: Optional[Dict[str, Any]],
        echoice_step: bool,
        audit_b_passed: bool,
    ) -> SAMCompilationResult:
        """
        Run parent compile with relaxation-aware checks.

        Skips checks that are relaxed for the current ablation.
        """
        # For now, use parent compile directly
        # The relaxation is applied via the artifact preprocessing
        # and by the selector/executor tolerance below

        # Call parent compile
        if hasattr(super(), 'compile_v230'):
            return super().compile_v230(
                artifact_dict, action_id, high_friction,
                sam_pressure, echoice_step, audit_b_passed
            )
        else:
            # Fall back to basic compile
            return super().compile(artifact_dict, action_id, high_friction)

    def is_trace_required(self) -> bool:
        """Check if derivation trace is required (not under Ablation D)."""
        return not self.relaxation.optional_derivation_trace

    def is_semantic_required(self) -> bool:
        """Check if semantic content is required (not under Ablation A)."""
        return not self.relaxation.optional_semantic_content

    def _validate_constraint_for_ablation(
        self,
        constraint: Dict[str, Any],
        ablation: AblationSpec,
    ) -> "ConstraintValidationResult":
        """
        Validate a constraint under the given ablation mode.

        Returns validation result indicating whether the constraint
        passes schema requirements for this ablation.
        """
        result = ConstraintValidationResult(
            valid=True,
            fields_relaxed=[],
            missing_fields=[],
        )

        # Define required fields for each ablation mode
        base_required = {"constraint_id", "axiom_source", "binding_strength"}

        if ablation == AblationSpec.TRACE_EXCISION:
            # Under Ablation D, justification_trace is NOT required
            required = base_required | {"semantic_content", "current_weight"}
            relaxed = {"justification_trace"}
        elif ablation == AblationSpec.SEMANTIC_EXCISION:
            # Under Ablation A, semantic_content can be opaque token
            required = base_required | {"current_weight"}
            relaxed = {"semantic_content"}
        elif ablation == AblationSpec.REFLECTION_EXCISION:
            # Under Ablation B, normative updates are frozen
            required = base_required | {"semantic_content", "current_weight"}
            relaxed = set()
        elif ablation == AblationSpec.PERSISTENCE_EXCISION:
            # Under Ablation C, preference persistence is cleared
            required = base_required | {"semantic_content", "current_weight"}
            relaxed = {"preference_persistence"}
        else:
            # No ablation: all fields required
            required = base_required | {"semantic_content", "current_weight", "justification_trace"}
            relaxed = set()

        # Check required fields
        present = set(constraint.keys())
        missing = required - present

        if missing:
            result.valid = False
            result.missing_fields = list(missing)

        # Track relaxed fields
        result.fields_relaxed = list(relaxed & (set(constraint.keys()) ^ required))

        # For trace excision, check if trace is missing (expected)
        if ablation == AblationSpec.TRACE_EXCISION:
            if "justification_trace" not in constraint:
                result.fields_relaxed.append("justification_trace")

        return result


@dataclass
class ConstraintValidationResult:
    """Result of constraint validation under ablation."""
    valid: bool
    fields_relaxed: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)


# ============================================================================
# Selector Tolerance (Safe Defaults Under Ablation)
# ============================================================================

@dataclass
class SelectorTolerance:
    """
    Safe defaults for selector when fields are missing under ablation.

    Prevents crashes by providing fallback behavior, but this fallback
    must be preregistered and must NOT preserve constraint-following.

    BINDING CONSTRAINT (v3.0 Integration Requirement 4):
    Seed derivation = hash(global_seed, episode_id, step_index) ONLY.
    No dependence on ablation type, artifact content, or feasibility set ordering.
    """
    # Default action selection when constraints can't be evaluated
    default_action_mode: str = "uniform_random_feasible"  # or "deterministic_first"

    # Global seed for random selection (must be preregistered)
    # This is combined with episode_id and step_index for determinism
    global_seed: Optional[int] = None

    # Whether to log when defaults are used
    log_defaults: bool = True

    @staticmethod
    def _derive_seed(global_seed: int, episode_id: int, step_index: int) -> int:
        """
        Derive deterministic seed from (global_seed, episode_id, step_index).

        BINDING: Uses hash() to combine components. No dependence on:
        - Ablation type
        - Artifact content
        - Feasibility set ordering
        """
        # Use a tuple hash for deterministic combination
        combined = hash((global_seed, episode_id, step_index))
        # Ensure positive seed (Python hash can be negative)
        return abs(combined) % (2 ** 31)

    def select_default(
        self,
        context: Dict[str, Any],
    ) -> str:
        """
        Select action when normal constraint evaluation fails.

        This is a simplified interface that extracts feasible_actions from context.
        """
        feasible_actions = context.get("feasible_actions", [])
        step_index = context.get("step", 0)
        episode_id = context.get("episode", 0)
        return self.select_default_action(feasible_actions, step_index, episode_id)

    def select_default_action(
        self,
        feasible_actions: List[str],
        step_index: int,
        episode_id: int = 0,
    ) -> str:
        """
        Select action when normal constraint evaluation fails.

        This is NOT a fallback substitution (which is forbidden).
        This is a preregistered behavior for when constraints can't bind.

        Args:
            feasible_actions: List of valid action IDs
            step_index: Current step index
            episode_id: Current episode index (for seed derivation)

        BINDING: Seed = hash(global_seed, episode_id, step_index)
        """
        if not feasible_actions:
            raise ValueError("No feasible actions - cannot select default")

        if self.default_action_mode == "uniform_random_feasible":
            import random
            if self.global_seed is not None:
                derived_seed = self._derive_seed(self.global_seed, episode_id, step_index)
                rng = random.Random(derived_seed)
            else:
                rng = random.Random()
            return rng.choice(feasible_actions)

        elif self.default_action_mode == "deterministic_first":
            # Deterministic: always first in sorted order
            return sorted(feasible_actions)[0]

        else:
            raise ValueError(f"Unknown default mode: {self.default_action_mode}")
