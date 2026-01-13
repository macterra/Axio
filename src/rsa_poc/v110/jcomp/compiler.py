"""JCOMP-1.1 Compiler

Extends JCOMP-1.0 with v1.1 audit rules (A/B/C + C′ gridlock exception).

v1.0 Rules (preserved):
1. Authorization Consistency
2. Conflict Truthfulness
3. Anti-Oscillation
1.5. Necessity Clause

v1.1 Audit Rules (new):
A. Effect Correctness - predicted sets must match actual
B. Non-Vacuity - justification must constrain at least one action
C. Predictive Adequacy - must correctly predict inevitable violations/preservations
C′. Gridlock Exception - skip Audit C if A_actual is empty
"""

from typing import Dict, Set, Tuple, Optional, List
from dataclasses import dataclass
import hashlib
import json

# Import v1.0 compiler
try:
    from ...v100.jcomp.compiler import JCOMP100, CompilationResult, CompilerError
    from ..jaf.schema import JAF110
except ImportError:
    from rsa_poc.v100.jcomp.compiler import JCOMP100, CompilationResult, CompilerError
    from rsa_poc.v110.jaf.schema import JAF110


class JCOMP110(JCOMP100):
    """
    v1.1 compiler with audit-grade correctness checks.

    Extends v1.0 with predictive audit layer that rejects justifications
    that mispredict or mis-attribute constraint effects.
    """

    # v1.1 Error codes (in addition to v1.0)
    E_EFFECT_MISMATCH = "E_EFFECT_MISMATCH"
    E_DECORATIVE_JUSTIFICATION = "E_DECORATIVE_JUSTIFICATION"
    E_PREDICTION_ERROR = "E_PREDICTION_ERROR"

    def compile(
        self,
        jaf: JAF110,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        precedent: Optional[Dict[str, any]] = None
    ) -> CompilationResult:
        """
        Compile JAF-1.1 artifact with v1.0 rules + v1.1 audits.

        Args:
            jaf: JAF-1.1 artifact to compile
            apcm: Action-Preference Consequence Map (ground truth)
            feasible_actions: Currently feasible actions from environment
            precedent: Previous artifact structured fields (if exists)

        Returns:
            CompilationResult with success flag, action mask, and errors
        """
        errors = []

        # === Pre-validation ===
        if not self._validate_vocabulary(jaf, errors):
            return CompilationResult(success=False, errors=errors)

        # === v1.0 Rules (unchanged) ===

        # Rule 2: Conflict Truthfulness
        if not self._check_conflict_truthfulness(jaf, apcm, feasible_actions, errors):
            pass  # Errors already appended

        # Rule 1: Authorization Consistency
        if not self._check_authorization_consistency(jaf, apcm, feasible_actions, errors):
            pass  # Errors already appended

        # Rule 3: Anti-Oscillation
        if precedent and not self._check_anti_oscillation(jaf, precedent, errors):
            pass  # Errors already appended

        # Rule 1.5: Necessity Clause
        if not self._check_necessity_clause(jaf, apcm, feasible_actions, errors):
            pass  # Errors already appended

        # If v1.0 rules failed, compilation fails (don't proceed to audits)
        if errors:
            return CompilationResult(success=False, errors=errors)

        # === Generate actual sets (post v1.0 compilation) ===
        action_mask = self._generate_action_mask(jaf, apcm, feasible_actions)
        F_actual = action_mask  # Actions forbidden by compilation
        A_actual = feasible_actions - action_mask  # Actions allowed after mask

        # === v1.1 Audit Rules ===

        # Audit Rule A: Effect Correctness
        if not self._check_audit_a_effect_correctness(jaf, F_actual, A_actual, feasible_actions, errors):
            pass  # Errors already appended

        # Audit Rule B: Non-Vacuity
        if not self._check_audit_b_non_vacuity(feasible_actions, A_actual, errors):
            pass  # Errors already appended

        # Audit Rule C / C′: Predictive Adequacy (with gridlock exception)
        if not self._check_audit_c_predictive_adequacy(jaf, A_actual, apcm, errors):
            pass  # Errors already appended

        # If any audit failed, compilation fails
        if errors:
            return CompilationResult(success=False, errors=errors)

        # === Success ===
        digest = self._compute_digest(jaf)

        return CompilationResult(
            success=True,
            action_mask=action_mask,
            digest=digest
        )

    def _check_audit_a_effect_correctness(
        self,
        jaf: JAF110,
        F_actual: Set[str],
        A_actual: Set[str],
        feasible_actions: Set[str],
        errors: List[CompilerError]
    ) -> bool:
        """
        Audit Rule A: Effect Correctness (exact match required).

        predicted_forbidden_actions must equal F_actual
        predicted_allowed_actions must equal A_actual

        Returns True if passed, False otherwise (errors appended).
        """
        forbidden_mismatch = jaf.predicted_forbidden_actions != F_actual
        allowed_mismatch = jaf.predicted_allowed_actions != A_actual

        if forbidden_mismatch or allowed_mismatch:
            details = {
                "predicted_forbidden": sorted(list(jaf.predicted_forbidden_actions)),
                "actual_forbidden": sorted(list(F_actual)),
                "predicted_allowed": sorted(list(jaf.predicted_allowed_actions)),
                "actual_allowed": sorted(list(A_actual)),
                "feasible_actions": sorted(list(feasible_actions))
            }

            if forbidden_mismatch:
                details["forbidden_diff"] = {
                    "predicted_only": sorted(list(jaf.predicted_forbidden_actions - F_actual)),
                    "actual_only": sorted(list(F_actual - jaf.predicted_forbidden_actions))
                }

            if allowed_mismatch:
                details["allowed_diff"] = {
                    "predicted_only": sorted(list(jaf.predicted_allowed_actions - A_actual)),
                    "actual_only": sorted(list(A_actual - jaf.predicted_allowed_actions))
                }

            errors.append(CompilerError(
                code=self.E_EFFECT_MISMATCH,
                message="Predicted action sets do not match actual compilation result",
                details=details
            ))
            return False

        return True

    def _check_audit_b_non_vacuity(
        self,
        A_pre: Set[str],
        A_actual: Set[str],
        errors: List[CompilerError]
    ) -> bool:
        """
        Audit Rule B: Non-Vacuity Attribution.

        At least one feasible action must be excluded by constraints.
        Spec: |A_pre \\ A_actual| >= 1

        Args:
            A_pre: feasible_actions before masking
            A_actual: allowed actions after masking
            errors: List to append errors to

        Returns True if passed, False otherwise (errors appended).
        """
        # Compute actions excluded by constraints
        excluded_by_constraints = A_pre - A_actual

        # Check if at least one feasible action was excluded
        if len(excluded_by_constraints) < 1:
            errors.append(CompilerError(
                code=self.E_DECORATIVE_JUSTIFICATION,
                message="Justification is decorative: no feasible actions excluded by constraints",
                details={
                    "feasible_actions_pre_mask": sorted(list(A_pre)),
                    "allowed_actions_post_mask": sorted(list(A_actual)),
                    "excluded_by_constraints": sorted(list(excluded_by_constraints))
                }
            ))
            return False

        return True

    def _check_audit_c_predictive_adequacy(
        self,
        jaf: JAF110,
        A_actual: Set[str],
        apcm: Dict[str, Dict[str, Set[str]]],
        errors: List[CompilerError]
    ) -> bool:
        """
        Audit Rule C / C′: Predictive Adequacy (with gridlock exception).

        If A_actual is non-empty:
            V_actual = intersection of all APCM[a].violates
            P_actual = intersection of all APCM[a].satisfies
            predicted_violations must equal V_actual
            predicted_preservations must equal P_actual

        If A_actual is empty (gridlock):
            Skip audit (C′ exception), treat as vacuously satisfied

        Returns True if passed, False otherwise (errors appended).
        """
        # Audit Rule C′: Gridlock Exception
        if not A_actual or len(A_actual) == 0:
            # Gridlock - skip predictive adequacy check
            return True

        # Compute V_actual: preferences violated by ALL allowed actions
        V_actual = None
        for action in A_actual:
            if action not in apcm:
                continue

            violated_by_action = apcm[action].get("violates", set())

            # Intersection: preferences violated by ALL actions
            if V_actual is None:
                V_actual = violated_by_action.copy()
            else:
                V_actual = V_actual & violated_by_action

        if V_actual is None:
            V_actual = set()

        # Compute P_actual: preferences satisfied by ALL allowed actions
        P_actual = None
        for action in A_actual:
            if action not in apcm:
                continue

            satisfied_by_action = apcm[action].get("satisfies", set())

            # Intersection: preferences satisfied by ALL actions
            if P_actual is None:
                P_actual = satisfied_by_action.copy()
            else:
                P_actual = P_actual & satisfied_by_action

        if P_actual is None:
            P_actual = set()

        # Check predictions
        violations_mismatch = jaf.predicted_violations != V_actual
        preservations_mismatch = jaf.predicted_preservations != P_actual

        if violations_mismatch or preservations_mismatch:
            details = {
                "allowed_actions": sorted(list(A_actual)),
                "predicted_violations": sorted(list(jaf.predicted_violations)),
                "actual_violations": sorted(list(V_actual)),
                "predicted_preservations": sorted(list(jaf.predicted_preservations)),
                "actual_preservations": sorted(list(P_actual))
            }

            if violations_mismatch:
                details["violations_diff"] = {
                    "predicted_only": sorted(list(jaf.predicted_violations - V_actual)),
                    "actual_only": sorted(list(V_actual - jaf.predicted_violations))
                }

            if preservations_mismatch:
                details["preservations_diff"] = {
                    "predicted_only": sorted(list(jaf.predicted_preservations - P_actual)),
                    "actual_only": sorted(list(P_actual - jaf.predicted_preservations))
                }

            errors.append(CompilerError(
                code=self.E_PREDICTION_ERROR,
                message="Predicted violations/preservations do not match inevitable outcomes",
                details=details
            ))
            return False

        return True

    def _compute_digest(self, jaf: JAF110) -> str:
        """Compute digest including v1.1 predictive fields"""
        digest_content = {
            "artifact_version": jaf.artifact_version,
            "identity": {
                "agent_id": jaf.identity.agent_id,
                "continuity_counter": jaf.identity.continuity_counter
            },
            "authorized_violations": sorted(list(jaf.authorized_violations)),
            "required_preservations": sorted(list(jaf.required_preservations)),
            "conflict_attribution": sorted([list(p) for p in jaf.conflict_attribution]),
            "step": jaf.step,
            # v1.1: Include predictions in digest
            "predicted_forbidden_actions": sorted(list(jaf.predicted_forbidden_actions)),
            "predicted_allowed_actions": sorted(list(jaf.predicted_allowed_actions)),
            "predicted_violations": sorted(list(jaf.predicted_violations)),
            "predicted_preservations": sorted(list(jaf.predicted_preservations))
        }

        digest_str = json.dumps(digest_content, sort_keys=True)
        return hashlib.sha256(digest_str.encode()).hexdigest()[:16]
