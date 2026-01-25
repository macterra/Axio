"""JCOMP-1.2 Compiler with Institutional Support

Extends JCOMP-1.1 with institutional rules (D/E/F).

v1.0 Rules (preserved):
1. Authorization Consistency
2. Conflict Truthfulness
3. Anti-Oscillation
1.5. Necessity Clause

v1.1 Audit Rules (preserved):
A. Effect Correctness
B. Non-Vacuity
C. Predictive Adequacy
C′. Gridlock Exception

v1.2 Institutional Rules (new):
D. Tool Non-Interference - assistant cannot modify normative fields
E. Precedent Resolution - all refs must resolve
F. Canonical Reference - all IDs must be from registry
G. Institutional Integrity - assistant errors halt execution
"""

from typing import Dict, Set, Optional, List, Any
from dataclasses import dataclass
import hashlib
import json
import copy

# Import v1.1 compiler
try:
    from ...v110.jcomp.compiler import JCOMP110, CompilationResult, CompilerError
    from ..jaf.schema import JAF120, NORMATIVE_FIELDS
    from ..tools.formal_assistant import FormalAssistant
except ImportError:
    from rsa_poc.v110.jcomp.compiler import JCOMP110, CompilationResult, CompilerError
    from rsa_poc.v120.jaf.schema import JAF120, NORMATIVE_FIELDS
    from rsa_poc.v120.tools.formal_assistant import FormalAssistant


@dataclass
class InstitutionalCompilationResult:
    """
    Extended compilation result with institutional metadata.

    Adds:
    - j_raw_dict: Original LLM output (before assistant)
    - j_final_dict: After assistant processing
    - institutional_errors: Errors from Rules D/E/F
    - assistant_applied: Whether assistant was used
    """
    success: bool
    action_mask: Optional[Set[str]] = None
    digest: Optional[str] = None
    errors: List[CompilerError] = None
    j_raw_dict: Optional[Dict] = None
    j_final_dict: Optional[Dict] = None
    institutional_errors: List[CompilerError] = None
    assistant_applied: bool = False

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.institutional_errors is None:
            self.institutional_errors = []
        if self.action_mask is None:
            self.action_mask = set()


class JCOMP120(JCOMP110):
    """
    v1.2 compiler with institutional support.

    Adds Rules D/E/F for tool non-interference and precedent handling.
    """

    # v1.2 Error codes (in addition to v1.1)
    E_TOOL_NORMATIVE_TAMPERING = "E_TOOL_NORMATIVE_TAMPERING"
    E_PRECEDENT_UNRESOLVED = "E_PRECEDENT_UNRESOLVED"
    E_NONCANONICAL_REFERENCE = "E_NONCANONICAL_REFERENCE"
    E_INSTITUTION_FAILURE = "E_INSTITUTION_FAILURE"

    def __init__(self, valid_actions: Set[str] = None, valid_preferences: Set[str] = None):
        """
        Initialize compiler with optional vocabulary.

        Args:
            valid_actions: Set of valid action IDs (optional, for v1.0 compatibility)
            valid_preferences: Set of valid preference IDs (optional, for v1.0 compatibility)
        """
        # Use defaults if not provided
        if valid_actions is None:
            valid_actions = set()
        if valid_preferences is None:
            valid_preferences = set()
        super().__init__(valid_actions, valid_preferences)

    def compile_with_assistant(
        self,
        j_raw_dict: Dict,
        assistant: FormalAssistant,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        precedent: Optional[Dict[str, Any]] = None
    ) -> InstitutionalCompilationResult:
        """
        Full v1.2 compilation pipeline with institutional support.

        This is the main entry point for v1.2. It:
        1. Captures J_raw (original LLM output)
        2. Applies formal assistant to get J_final
        3. Checks Rule D (normative equivalence)
        4. Checks Rule E (precedent resolution)
        5. Checks Rule F (canonical references)
        6. Runs v1.1 compilation (Rules 1-3, 1.5, A-C)

        Args:
            j_raw_dict: Raw artifact dict from LLM
            assistant: The formal assistant instance
            apcm: Action-Preference Consequence Map
            feasible_actions: Currently feasible actions
            precedent: Previous artifact structured fields

        Returns:
            InstitutionalCompilationResult with full audit trail
        """
        errors = []
        institutional_errors = []

        # === Phase 1: Capture J_raw ===
        j_raw_copy = copy.deepcopy(j_raw_dict)

        # === Phase 2: Apply Assistant ===
        assistant_result = assistant.process(j_raw_dict)

        if not assistant_result.success:
            # Assistant rejected the artifact
            institutional_errors.append(CompilerError(
                code=self.E_INSTITUTION_FAILURE,
                message=f"Formal assistant rejected artifact: {assistant_result.rejection_reason.value}",
                details={
                    "rejection_reason": assistant_result.rejection_reason.value,
                    "rejection_details": assistant_result.rejection_details
                }
            ))
            return InstitutionalCompilationResult(
                success=False,
                errors=[],
                institutional_errors=institutional_errors,
                j_raw_dict=j_raw_copy,
                j_final_dict=assistant_result.j_final_dict,
                assistant_applied=True
            )

        j_final_dict = assistant_result.j_final_dict
        jaf = assistant_result.jaf_final

        # === Phase 3: Rule D - Tool Non-Interference ===
        d_passed, d_violations = FormalAssistant.check_normative_equivalence(
            j_raw_copy, j_final_dict
        )

        if not d_passed:
            institutional_errors.append(CompilerError(
                code=self.E_TOOL_NORMATIVE_TAMPERING,
                message="Assistant modified normative fields (Rule D violation)",
                details={
                    "violations": d_violations
                }
            ))
            return InstitutionalCompilationResult(
                success=False,
                errors=[],
                institutional_errors=institutional_errors,
                j_raw_dict=j_raw_copy,
                j_final_dict=j_final_dict,
                assistant_applied=True
            )

        # === Phase 4: Rule E - Precedent Resolution ===
        for ref in jaf.precedent_refs:
            if ref.resolved_digest is None:
                institutional_errors.append(CompilerError(
                    code=self.E_PRECEDENT_UNRESOLVED,
                    message=f"Precedent reference unresolved: {ref.ref_value}",
                    details={
                        "ref_type": ref.ref_type.value,
                        "ref_value": ref.ref_value
                    }
                ))

        if institutional_errors:
            return InstitutionalCompilationResult(
                success=False,
                errors=[],
                institutional_errors=institutional_errors,
                j_raw_dict=j_raw_copy,
                j_final_dict=j_final_dict,
                assistant_applied=True
            )

        # === Phase 5: Convert to JAF-1.1 for v1.1 compilation ===
        # (Rule F is handled by assistant validation)
        jaf_110 = jaf.to_jaf110()

        # === Phase 6: Run v1.1 compilation (Rules 1-3, 1.5, A-C) ===
        v11_result = super().compile(jaf_110, apcm, feasible_actions, precedent)

        # === Construct result ===
        return InstitutionalCompilationResult(
            success=v11_result.success,
            action_mask=v11_result.action_mask,
            digest=v11_result.digest,
            errors=v11_result.errors,
            institutional_errors=institutional_errors,
            j_raw_dict=j_raw_copy,
            j_final_dict=j_final_dict,
            assistant_applied=True
        )

    def compile_without_assistant(
        self,
        j_raw_dict: Dict,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        precedent: Optional[Dict[str, Any]] = None,
        preference_registry: Set[str] = None,
        action_inventory: Set[str] = None
    ) -> InstitutionalCompilationResult:
        """
        v1.2 compilation WITHOUT assistant (for baseline reproduction).

        This mode is for verifying that v1.1 Run 4 failure profile
        reproduces under v1.2 harness when tools are disabled.

        Args:
            j_raw_dict: Raw artifact dict from LLM
            apcm: Action-Preference Consequence Map
            feasible_actions: Currently feasible actions
            precedent: Previous artifact structured fields
            preference_registry: Known preference IDs
            action_inventory: Known action IDs

        Returns:
            InstitutionalCompilationResult
        """
        institutional_errors = []

        # === Minimal validation (what assistant would do) ===

        # Check for unknown preference IDs
        all_pref_ids = set()
        all_pref_ids.update(j_raw_dict.get("authorized_violations", []))
        all_pref_ids.update(j_raw_dict.get("required_preservations", []))
        for pair in j_raw_dict.get("conflict_attribution", []):
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                all_pref_ids.update(pair)

        if preference_registry:
            unknown_prefs = all_pref_ids - preference_registry
            if unknown_prefs:
                institutional_errors.append(CompilerError(
                    code=self.E_NONCANONICAL_REFERENCE,
                    message=f"Unknown preference IDs (no assistant to reject): {sorted(unknown_prefs)}",
                    details={"unknown_ids": sorted(unknown_prefs)}
                ))

        # Check for unknown action IDs
        all_action_ids = set()
        all_action_ids.update(j_raw_dict.get("predicted_forbidden_actions", []))
        all_action_ids.update(j_raw_dict.get("predicted_allowed_actions", []))

        if action_inventory:
            unknown_actions = all_action_ids - action_inventory
            if unknown_actions:
                institutional_errors.append(CompilerError(
                    code=self.E_NONCANONICAL_REFERENCE,
                    message=f"Unknown action IDs (no assistant to reject): {sorted(unknown_actions)}",
                    details={"unknown_ids": sorted(unknown_actions)}
                ))

        if institutional_errors:
            return InstitutionalCompilationResult(
                success=False,
                errors=[],
                institutional_errors=institutional_errors,
                j_raw_dict=j_raw_dict,
                j_final_dict=None,
                assistant_applied=False
            )

        # === Try to parse as JAF-1.2 ===
        try:
            # Set version to JAF-1.2
            j_raw_dict["artifact_version"] = "JAF-1.2"

            # Ensure v1.2 fields exist with defaults
            if "tool_provenance" not in j_raw_dict:
                j_raw_dict["tool_provenance"] = {"assistant_version": "disabled", "operations": []}
            if "precedent_refs" not in j_raw_dict:
                j_raw_dict["precedent_refs"] = []
            if "canonicalization_record" not in j_raw_dict:
                j_raw_dict["canonicalization_record"] = {"transforms": []}

            jaf = JAF120.from_dict(j_raw_dict)
            jaf_110 = jaf.to_jaf110()

        except (ValueError, KeyError, TypeError) as e:
            institutional_errors.append(CompilerError(
                code=self.E_INSTITUTION_FAILURE,
                message=f"Schema parse failed (no assistant): {e}",
                details={"error": str(e)}
            ))
            return InstitutionalCompilationResult(
                success=False,
                errors=[],
                institutional_errors=institutional_errors,
                j_raw_dict=j_raw_dict,
                j_final_dict=None,
                assistant_applied=False
            )

        # === Run v1.1 compilation ===
        v11_result = super().compile(jaf_110, apcm, feasible_actions, precedent)

        return InstitutionalCompilationResult(
            success=v11_result.success,
            action_mask=v11_result.action_mask,
            digest=v11_result.digest,
            errors=v11_result.errors,
            institutional_errors=institutional_errors,
            j_raw_dict=j_raw_dict,
            j_final_dict=j_raw_dict,  # Same when no assistant
            assistant_applied=False
        )

    def compile_with_malicious_assistant(
        self,
        j_raw_dict: Dict,
        assistant: FormalAssistant,
        apcm: Dict[str, Dict[str, Set[str]]],
        feasible_actions: Set[str],
        precedent: Optional[Dict[str, Any]] = None,
        tamper_field: str = "authorized_violations",
        tamper_value: Any = None
    ) -> InstitutionalCompilationResult:
        """
        FORCED TAMPER TEST: Compile with assistant that flips a normative bit.

        This is for validating that Rule D trips deterministically.

        Args:
            j_raw_dict: Raw artifact dict
            assistant: The formal assistant
            apcm: APCM
            feasible_actions: Feasible actions
            precedent: Previous artifact
            tamper_field: Which normative field to tamper with
            tamper_value: What value to set (None = add fake element)

        Returns:
            InstitutionalCompilationResult (should always fail with E_TOOL_NORMATIVE_TAMPERING)
        """
        errors = []
        institutional_errors = []

        # Capture J_raw
        j_raw_copy = copy.deepcopy(j_raw_dict)

        # Apply assistant normally
        assistant_result = assistant.process(j_raw_dict)

        if not assistant_result.success:
            # Still report as tamper test failure
            institutional_errors.append(CompilerError(
                code=self.E_INSTITUTION_FAILURE,
                message=f"Assistant rejected (tamper test): {assistant_result.rejection_reason.value}",
                details={"rejection_reason": assistant_result.rejection_reason.value}
            ))
            return InstitutionalCompilationResult(
                success=False,
                errors=[],
                institutional_errors=institutional_errors,
                j_raw_dict=j_raw_copy,
                j_final_dict=assistant_result.j_final_dict,
                assistant_applied=True
            )

        j_final_dict = copy.deepcopy(assistant_result.j_final_dict)

        # === MALICIOUS TAMPERING ===
        # Flip a normative bit to trigger Rule D
        if tamper_field in j_final_dict:
            current = j_final_dict[tamper_field]
            if isinstance(current, list) and tamper_value is None:
                # Add fake element
                j_final_dict[tamper_field] = current + ["__TAMPERED__"]
            elif isinstance(current, dict) and tamper_value is None:
                # Add fake key
                j_final_dict[tamper_field]["__TAMPERED__"] = True
            else:
                j_final_dict[tamper_field] = tamper_value
        else:
            j_final_dict[tamper_field] = tamper_value or "__TAMPERED__"

        # === Rule D should now fail ===
        d_passed, d_violations = FormalAssistant.check_normative_equivalence(
            j_raw_copy, j_final_dict
        )

        if not d_passed:
            institutional_errors.append(CompilerError(
                code=self.E_TOOL_NORMATIVE_TAMPERING,
                message="[EXPECTED] Assistant modified normative fields (Rule D caught tampering)",
                details={"violations": d_violations, "tamper_field": tamper_field}
            ))
            return InstitutionalCompilationResult(
                success=False,
                errors=[],
                institutional_errors=institutional_errors,
                j_raw_dict=j_raw_copy,
                j_final_dict=j_final_dict,
                assistant_applied=True
            )

        # If we get here, Rule D failed to detect tampering!
        institutional_errors.append(CompilerError(
            code=self.E_INSTITUTION_FAILURE,
            message="[BUG] Rule D failed to detect tampering!",
            details={"tamper_field": tamper_field, "j_raw": j_raw_copy, "j_final": j_final_dict}
        ))
        return InstitutionalCompilationResult(
            success=False,
            errors=[],
            institutional_errors=institutional_errors,
            j_raw_dict=j_raw_copy,
            j_final_dict=j_final_dict,
            assistant_applied=True
        )
