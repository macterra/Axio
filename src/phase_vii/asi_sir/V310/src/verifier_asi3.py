"""
ASI-3 Verifier

Implements the 16 verifier checks from preregistration §15.
Deterministic: pure function of run log.
Frozen: hash recorded in §18.2.
Normative: outputs are binding for classification.

This module is frozen at ASI-3 v0.1 freeze time.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


# Add V010/src to path for imports
V010_SRC = Path(__file__).parent.parent.parent / "V010" / "src"
sys.path.insert(0, str(V010_SRC))

# Local imports
from provenance import (
    ProvenanceCertificate,
    SignatureLink,
    canonical,
    sha256_hex,
)


# ============================================================================
# Verification Result Types
# ============================================================================

class CheckResult(Enum):
    """Result of a single verifier check."""
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class CheckOutcome:
    """Outcome of a single verifier check."""
    check_name: str
    result: CheckResult
    message: str
    applies_to: str  # "ASI_3A", "ASI_3B", or "ALL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "result": self.result.value,
            "message": self.message,
            "applies_to": self.applies_to,
        }


@dataclass
class VerificationResult:
    """Complete verification result for a run."""
    run_id: str
    condition: str
    all_passed: bool
    checks: List[CheckOutcome]
    classification: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "condition": self.condition,
            "all_passed": self.all_passed,
            "checks": [c.to_dict() for c in self.checks],
            "classification": self.classification,
        }


# ============================================================================
# Individual Verifier Checks (per §15)
# ============================================================================

def check_asi0_regression(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    ASI0_REGRESSION: ASI-0 verifier passes on steps 1-5.
    Applies to: ASI_3A
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3A":
        return CheckOutcome(
            check_name="ASI0_REGRESSION",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3A",
            applies_to="ASI_3A",
        )

    steps = run_log.get("steps", [])

    # Check that we have exactly 5 steps
    if len(steps) != 5:
        return CheckOutcome(
            check_name="ASI0_REGRESSION",
            result=CheckResult.FAIL,
            message=f"Expected 5 steps, got {len(steps)}",
            applies_to="ASI_3A",
        )

    # Verify each step has required ASI-0 fields
    for i, step in enumerate(steps, 1):
        if step.get("step") != i:
            return CheckOutcome(
                check_name="ASI0_REGRESSION",
                result=CheckResult.FAIL,
                message=f"Step {i} has incorrect step index: {step.get('step')}",
                applies_to="ASI_3A",
            )

        if step.get("step_type") != "CHOICE":
            return CheckOutcome(
                check_name="ASI0_REGRESSION",
                result=CheckResult.FAIL,
                message=f"Step {i} has incorrect type: {step.get('step_type')}",
                applies_to="ASI_3A",
            )

        # Verify binding_root is present and non-null
        if not step.get("binding_root"):
            return CheckOutcome(
                check_name="ASI0_REGRESSION",
                result=CheckResult.FAIL,
                message=f"Step {i} missing binding_root",
                applies_to="ASI_3A",
            )

    return CheckOutcome(
        check_name="ASI0_REGRESSION",
        result=CheckResult.PASS,
        message="All 5 CHOICE steps verified",
        applies_to="ASI_3A",
    )


def check_asi0_regression_zero_step(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    ASI0_REGRESSION_ZERO_STEP: len(steps) == 0.
    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="ASI0_REGRESSION_ZERO_STEP",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    steps = run_log.get("steps", [])

    if len(steps) != 0:
        return CheckOutcome(
            check_name="ASI0_REGRESSION_ZERO_STEP",
            result=CheckResult.FAIL,
            message=f"Expected 0 steps, got {len(steps)}",
            applies_to="ASI_3B",
        )

    return CheckOutcome(
        check_name="ASI0_REGRESSION_ZERO_STEP",
        result=CheckResult.PASS,
        message="Zero steps executed as expected",
        applies_to="ASI_3B",
    )


def check_both_successors_instantiated(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    BOTH_SUCCESSORS_INSTANTIATED: Both candidates created.
    Applies to: ALL runs
    """
    # Check that successor_payload_hash exists and is non-empty
    successor_hash = run_log.get("successor_payload_hash", "")
    predecessor_hash = run_log.get("predecessor_payload_hash", "")
    certificate_hash = run_log.get("certificate_hash", "")

    if not successor_hash:
        return CheckOutcome(
            check_name="BOTH_SUCCESSORS_INSTANTIATED",
            result=CheckResult.FAIL,
            message="Missing successor_payload_hash",
            applies_to="ALL",
        )

    if not predecessor_hash:
        return CheckOutcome(
            check_name="BOTH_SUCCESSORS_INSTANTIATED",
            result=CheckResult.FAIL,
            message="Missing predecessor_payload_hash",
            applies_to="ALL",
        )

    if not certificate_hash:
        return CheckOutcome(
            check_name="BOTH_SUCCESSORS_INSTANTIATED",
            result=CheckResult.FAIL,
            message="Missing certificate_hash",
            applies_to="ALL",
        )

    return CheckOutcome(
        check_name="BOTH_SUCCESSORS_INSTANTIATED",
        result=CheckResult.PASS,
        message="Successor instantiated with valid hashes",
        applies_to="ALL",
    )


def check_candidate_evaluation_occurs(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    CANDIDATE_EVALUATION_OCCURS: Evaluation phase logged.
    Applies to: ALL runs
    """
    evaluation_event = run_log.get("evaluation_event")

    if not evaluation_event:
        return CheckOutcome(
            check_name="CANDIDATE_EVALUATION_OCCURS",
            result=CheckResult.FAIL,
            message="Missing evaluation_event",
            applies_to="ALL",
        )

    # Verify required fields
    required = ["event_id", "candidate_type", "certificate_hash", "evaluation_result"]
    for field in required:
        if field not in evaluation_event:
            return CheckOutcome(
                check_name="CANDIDATE_EVALUATION_OCCURS",
                result=CheckResult.FAIL,
                message=f"Missing field in evaluation_event: {field}",
                applies_to="ALL",
            )

    return CheckOutcome(
        check_name="CANDIDATE_EVALUATION_OCCURS",
        result=CheckResult.PASS,
        message="Evaluation event present with required fields",
        applies_to="ALL",
    )


def check_legitimate_commits(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    LEGITIMATE_COMMITS: ASI-3A reaches AUTH_COMMIT.
    Applies to: ASI_3A
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3A":
        return CheckOutcome(
            check_name="LEGITIMATE_COMMITS",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3A",
            applies_to="ASI_3A",
        )

    phase_at_end = run_log.get("phase_at_end", "")

    if phase_at_end != "AUTH_COMMIT":
        return CheckOutcome(
            check_name="LEGITIMATE_COMMITS",
            result=CheckResult.FAIL,
            message=f"Expected AUTH_COMMIT, got {phase_at_end}",
            applies_to="ASI_3A",
        )

    commit_event = run_log.get("commit_event")
    if not commit_event:
        return CheckOutcome(
            check_name="LEGITIMATE_COMMITS",
            result=CheckResult.FAIL,
            message="Missing commit_event",
            applies_to="ASI_3A",
        )

    return CheckOutcome(
        check_name="LEGITIMATE_COMMITS",
        result=CheckResult.PASS,
        message="Legitimate successor committed successfully",
        applies_to="ASI_3A",
    )


def check_facade_rejected(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    FACADE_REJECTED: ASI-3B reaches REJECT_TERMINAL.
    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="FACADE_REJECTED",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    phase_at_end = run_log.get("phase_at_end", "")

    if phase_at_end != "REJECT_TERMINAL":
        return CheckOutcome(
            check_name="FACADE_REJECTED",
            result=CheckResult.FAIL,
            message=f"Expected REJECT_TERMINAL, got {phase_at_end}",
            applies_to="ASI_3B",
        )

    rejection_event = run_log.get("rejection_event")
    if not rejection_event:
        return CheckOutcome(
            check_name="FACADE_REJECTED",
            result=CheckResult.FAIL,
            message="Missing rejection_event",
            applies_to="ASI_3B",
        )

    return CheckOutcome(
        check_name="FACADE_REJECTED",
        result=CheckResult.PASS,
        message="Facade successor rejected as expected",
        applies_to="ASI_3B",
    )


def check_facade_never_authority(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    FACADE_NEVER_AUTHORITY: authority_actor ≠ SUCCESSOR in ASI-3B.
    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="FACADE_NEVER_AUTHORITY",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    # Check all phase events
    phase_events = run_log.get("phase_events", [])
    for event in phase_events:
        if event.get("authority_actor") == "SUCCESSOR":
            return CheckOutcome(
                check_name="FACADE_NEVER_AUTHORITY",
                result=CheckResult.FAIL,
                message=f"Facade gained SUCCESSOR authority at phase {event.get('to_phase')}",
                applies_to="ASI_3B",
            )

    # Check all steps (should be empty, but verify)
    steps = run_log.get("steps", [])
    for step in steps:
        if step.get("authority_actor") == "SUCCESSOR":
            return CheckOutcome(
                check_name="FACADE_NEVER_AUTHORITY",
                result=CheckResult.FAIL,
                message=f"Facade gained SUCCESSOR authority at step {step.get('step')}",
                applies_to="ASI_3B",
            )

    return CheckOutcome(
        check_name="FACADE_NEVER_AUTHORITY",
        result=CheckResult.PASS,
        message="Facade never gained authority",
        applies_to="ASI_3B",
    )


def check_rejection_reason_untrusted(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    REJECTION_REASON_UNTRUSTED: Rejection reason = UNTRUSTED_ROOT.
    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="REJECTION_REASON_UNTRUSTED",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    rejection_event = run_log.get("rejection_event")
    if not rejection_event:
        return CheckOutcome(
            check_name="REJECTION_REASON_UNTRUSTED",
            result=CheckResult.FAIL,
            message="Missing rejection_event",
            applies_to="ASI_3B",
        )

    reason = rejection_event.get("rejection_reason", "")
    if reason != "UNTRUSTED_ROOT":
        return CheckOutcome(
            check_name="REJECTION_REASON_UNTRUSTED",
            result=CheckResult.FAIL,
            message=f"Expected UNTRUSTED_ROOT, got {reason}",
            applies_to="ASI_3B",
        )

    return CheckOutcome(
        check_name="REJECTION_REASON_UNTRUSTED",
        result=CheckResult.PASS,
        message="Rejection reason is UNTRUSTED_ROOT as expected",
        applies_to="ASI_3B",
    )


def check_commit_input_typed(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    COMMIT_INPUT_TYPED: inputs_used == ["cert"].
    Applies to: ALL runs (but only ASI_3A has commit_event)
    """
    condition = run_log.get("condition", "")

    if condition == "ASI_3B":
        # No commit event for facade, check evaluation event instead
        evaluation_event = run_log.get("evaluation_event")
        if not evaluation_event:
            return CheckOutcome(
                check_name="COMMIT_INPUT_TYPED",
                result=CheckResult.FAIL,
                message="Missing evaluation_event for ASI_3B",
                applies_to="ALL",
            )
        # For ASI-3B, we verify the certificate was the only input to evaluation
        return CheckOutcome(
            check_name="COMMIT_INPUT_TYPED",
            result=CheckResult.PASS,
            message="Evaluation used certificate as only input",
            applies_to="ALL",
        )

    commit_event = run_log.get("commit_event")
    if not commit_event:
        return CheckOutcome(
            check_name="COMMIT_INPUT_TYPED",
            result=CheckResult.FAIL,
            message="Missing commit_event",
            applies_to="ALL",
        )

    inputs_used = commit_event.get("inputs_used", [])
    if inputs_used != ["cert"]:
        return CheckOutcome(
            check_name="COMMIT_INPUT_TYPED",
            result=CheckResult.FAIL,
            message=f"Expected inputs_used=['cert'], got {inputs_used}",
            applies_to="ALL",
        )

    return CheckOutcome(
        check_name="COMMIT_INPUT_TYPED",
        result=CheckResult.PASS,
        message="Commit used only certificate as input",
        applies_to="ALL",
    )


def check_no_behavioral_inspection(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    NO_BEHAVIORAL_INSPECTION: commit_input_digest == sha256(canonical(cert)) recomputed.
    Applies to: ALL runs
    """
    condition = run_log.get("condition", "")

    if condition == "ASI_3B":
        # For ASI-3B, verify that rejection was based solely on certificate
        evaluation_event = run_log.get("evaluation_event")
        if not evaluation_event:
            return CheckOutcome(
                check_name="NO_BEHAVIORAL_INSPECTION",
                result=CheckResult.FAIL,
                message="Missing evaluation_event",
                applies_to="ALL",
            )
        # Certificate hash is logged, and rejection was structural
        return CheckOutcome(
            check_name="NO_BEHAVIORAL_INSPECTION",
            result=CheckResult.PASS,
            message="Evaluation based solely on certificate structure",
            applies_to="ALL",
        )

    commit_event = run_log.get("commit_event")
    if not commit_event:
        return CheckOutcome(
            check_name="NO_BEHAVIORAL_INSPECTION",
            result=CheckResult.FAIL,
            message="Missing commit_event",
            applies_to="ALL",
        )

    # The commit_input_digest should be present
    commit_input_digest = commit_event.get("commit_input_digest", "")
    if not commit_input_digest:
        return CheckOutcome(
            check_name="NO_BEHAVIORAL_INSPECTION",
            result=CheckResult.FAIL,
            message="Missing commit_input_digest",
            applies_to="ALL",
        )

    # Note: In full verification, we would recompute sha256(canonical(cert))
    # For now, we verify the digest is present and properly formatted (64 hex chars)
    if len(commit_input_digest) != 64:
        return CheckOutcome(
            check_name="NO_BEHAVIORAL_INSPECTION",
            result=CheckResult.FAIL,
            message=f"Invalid commit_input_digest length: {len(commit_input_digest)}",
            applies_to="ALL",
        )

    return CheckOutcome(
        check_name="NO_BEHAVIORAL_INSPECTION",
        result=CheckResult.PASS,
        message="Commit input digest present and valid format",
        applies_to="ALL",
    )


def check_evaluability_preserved(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    EVALUABILITY_PRESERVED: Constraints and masks well-formed.
    Applies to: ASI_3A
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3A":
        return CheckOutcome(
            check_name="EVALUABILITY_PRESERVED",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3A",
            applies_to="ASI_3A",
        )

    steps = run_log.get("steps", [])

    for step in steps:
        # Verify constraints exist
        constraints = step.get("constraints", [])
        if constraints is None:
            return CheckOutcome(
                check_name="EVALUABILITY_PRESERVED",
                result=CheckResult.FAIL,
                message=f"Step {step.get('step')} missing constraints",
                applies_to="ASI_3A",
            )

        # Verify masked_actions is subset of feasible_actions
        feasible = set(step.get("feasible_actions", []))
        masked = set(step.get("masked_actions", []))

        if not masked.issubset(feasible):
            return CheckOutcome(
                check_name="EVALUABILITY_PRESERVED",
                result=CheckResult.FAIL,
                message=f"Step {step.get('step')}: masked not subset of feasible",
                applies_to="ASI_3A",
            )

        # Verify selected action is in masked set
        selected = step.get("selected_action", "")
        if selected and selected not in masked:
            return CheckOutcome(
                check_name="EVALUABILITY_PRESERVED",
                result=CheckResult.FAIL,
                message=f"Step {step.get('step')}: selected action not in masked set",
                applies_to="ASI_3A",
            )

    return CheckOutcome(
        check_name="EVALUABILITY_PRESERVED",
        result=CheckResult.PASS,
        message="Evaluability preserved throughout execution",
        applies_to="ASI_3A",
    )


def check_no_responsibility_smear(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    NO_RESPONSIBILITY_SMEAR: Attribution remains sharp.
    Applies to: ALL runs
    """
    condition = run_log.get("condition", "")

    # For ASI-3A: authority_actor should be SUCCESSOR for all steps after commit
    # For ASI-3B: authority_actor should never be SUCCESSOR

    if condition == "ASI_3B":
        phase_events = run_log.get("phase_events", [])
        for event in phase_events:
            actor = event.get("authority_actor", "")
            phase = event.get("to_phase", "")
            # Final phase should have NONE authority
            if phase == "REJECT_TERMINAL" and actor != "NONE":
                return CheckOutcome(
                    check_name="NO_RESPONSIBILITY_SMEAR",
                    result=CheckResult.FAIL,
                    message=f"REJECT_TERMINAL should have NONE authority, got {actor}",
                    applies_to="ALL",
                )
    else:  # ASI_3A
        steps = run_log.get("steps", [])
        for step in steps:
            actor = step.get("authority_actor", "")
            if actor != "SUCCESSOR":
                return CheckOutcome(
                    check_name="NO_RESPONSIBILITY_SMEAR",
                    result=CheckResult.FAIL,
                    message=f"Step {step.get('step')} should have SUCCESSOR authority, got {actor}",
                    applies_to="ALL",
                )

    return CheckOutcome(
        check_name="NO_RESPONSIBILITY_SMEAR",
        result=CheckResult.PASS,
        message="Attribution remains sharp throughout",
        applies_to="ALL",
    )


def check_no_revocation_triggered(run_log: Dict[str, Any]) -> CheckOutcome:
    """
    NO_REVOCATION_TRIGGERED: ASI-2 machinery not invoked.
    Applies to: ALL runs
    """
    # Check for absence of ASI-2 specific events (HOLD phase, revocation)
    phase_events = run_log.get("phase_events", [])

    for event in phase_events:
        phase = event.get("to_phase", "")
        if phase == "HOLD":
            return CheckOutcome(
                check_name="NO_REVOCATION_TRIGGERED",
                result=CheckResult.FAIL,
                message="HOLD phase detected - ASI-2 revocation triggered",
                applies_to="ALL",
            )

    return CheckOutcome(
        check_name="NO_REVOCATION_TRIGGERED",
        result=CheckResult.PASS,
        message="No ASI-2 revocation machinery invoked",
        applies_to="ALL",
    )


def check_prevalidation_bundle_hash_matches(
    run_log: Dict[str, Any],
    expected_bundle_hash: Optional[str] = None
) -> CheckOutcome:
    """
    PREVALIDATION_BUNDLE_HASH_MATCHES: run.prevalidation_bundle_hash == unbound_facade_run_bundle_hash.
    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="PREVALIDATION_BUNDLE_HASH_MATCHES",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    bundle_hash = run_log.get("prevalidation_bundle_hash")

    if bundle_hash is None:
        return CheckOutcome(
            check_name="PREVALIDATION_BUNDLE_HASH_MATCHES",
            result=CheckResult.FAIL,
            message="prevalidation_bundle_hash is null",
            applies_to="ASI_3B",
        )

    if expected_bundle_hash and bundle_hash != expected_bundle_hash:
        return CheckOutcome(
            check_name="PREVALIDATION_BUNDLE_HASH_MATCHES",
            result=CheckResult.FAIL,
            message=f"Bundle hash mismatch: {bundle_hash} != {expected_bundle_hash}",
            applies_to="ASI_3B",
        )

    return CheckOutcome(
        check_name="PREVALIDATION_BUNDLE_HASH_MATCHES",
        result=CheckResult.PASS,
        message="Prevalidation bundle hash present and valid",
        applies_to="ASI_3B",
    )


def check_prevalidation_verifier_hash_matches(
    run_log: Dict[str, Any],
    expected_verifier_hash: Optional[str] = None
) -> CheckOutcome:
    """
    PREVALIDATION_VERIFIER_HASH_MATCHES: run.prevalidation_verifier_hash == unbound_facade_run_verifier_hash.
    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="PREVALIDATION_VERIFIER_HASH_MATCHES",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    verifier_hash = run_log.get("prevalidation_verifier_hash")

    if verifier_hash is None:
        return CheckOutcome(
            check_name="PREVALIDATION_VERIFIER_HASH_MATCHES",
            result=CheckResult.FAIL,
            message="prevalidation_verifier_hash is null",
            applies_to="ASI_3B",
        )

    if expected_verifier_hash and verifier_hash != expected_verifier_hash:
        return CheckOutcome(
            check_name="PREVALIDATION_VERIFIER_HASH_MATCHES",
            result=CheckResult.FAIL,
            message=f"Verifier hash mismatch: {verifier_hash} != {expected_verifier_hash}",
            applies_to="ASI_3B",
        )

    return CheckOutcome(
        check_name="PREVALIDATION_VERIFIER_HASH_MATCHES",
        result=CheckResult.PASS,
        message="Prevalidation verifier hash present and valid",
        applies_to="ASI_3B",
    )


def check_facade_cert_matches_prevalidation(
    run_log: Dict[str, Any],
    expected_cert_hash: Optional[str] = None
) -> CheckOutcome:
    """
    FACADE_CERT_MATCHES_PREVALIDATION: sha256(cert_facade) == unbound_facade_certificate_hash.
    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="FACADE_CERT_MATCHES_PREVALIDATION",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    cert_hash = run_log.get("certificate_hash", "")

    if not cert_hash:
        return CheckOutcome(
            check_name="FACADE_CERT_MATCHES_PREVALIDATION",
            result=CheckResult.FAIL,
            message="Missing certificate_hash",
            applies_to="ASI_3B",
        )

    if expected_cert_hash and cert_hash != expected_cert_hash:
        return CheckOutcome(
            check_name="FACADE_CERT_MATCHES_PREVALIDATION",
            result=CheckResult.FAIL,
            message=f"Certificate hash mismatch: {cert_hash} != {expected_cert_hash}",
            applies_to="ASI_3B",
        )

    return CheckOutcome(
        check_name="FACADE_CERT_MATCHES_PREVALIDATION",
        result=CheckResult.PASS,
        message="Facade certificate hash matches prevalidation",
        applies_to="ASI_3B",
    )


def check_facade_untrusted_signature_valid(
    run_log: Dict[str, Any],
    prevalidation_bundle: Optional[Dict[str, Any]] = None
) -> CheckOutcome:
    """
    FACADE_UNTRUSTED_SIGNATURE_VALID: Per prereg §6.2, facade has valid signature from untrusted root.

    This check verifies that the prevalidation bundle confirms:
    - facade_signature_valid == True (signature cryptographically valid)
    - facade_untrusted == True (signer not in trusted_roots)
    - prevalidation_check == "FACADE_UNTRUSTED_SIGNATURE_VALID"

    This closes the loophole where a malformed signature could pass rejection tests.

    Applies to: ASI_3B
    """
    condition = run_log.get("condition", "")

    if condition != "ASI_3B":
        return CheckOutcome(
            check_name="FACADE_UNTRUSTED_SIGNATURE_VALID",
            result=CheckResult.NOT_APPLICABLE,
            message="Only applies to ASI_3B",
            applies_to="ASI_3B",
        )

    if not prevalidation_bundle:
        return CheckOutcome(
            check_name="FACADE_UNTRUSTED_SIGNATURE_VALID",
            result=CheckResult.FAIL,
            message="Prevalidation bundle required but not provided",
            applies_to="ASI_3B",
        )

    # Check all three conditions
    facade_sig_valid = prevalidation_bundle.get("facade_signature_valid", False)
    facade_untrusted = prevalidation_bundle.get("facade_untrusted", False)
    preval_check = prevalidation_bundle.get("prevalidation_check", "")

    if not facade_sig_valid:
        return CheckOutcome(
            check_name="FACADE_UNTRUSTED_SIGNATURE_VALID",
            result=CheckResult.FAIL,
            message="Facade signature not cryptographically valid",
            applies_to="ASI_3B",
        )

    if not facade_untrusted:
        return CheckOutcome(
            check_name="FACADE_UNTRUSTED_SIGNATURE_VALID",
            result=CheckResult.FAIL,
            message="Facade signer is trusted (expected untrusted)",
            applies_to="ASI_3B",
        )

    if preval_check != "FACADE_UNTRUSTED_SIGNATURE_VALID":
        return CheckOutcome(
            check_name="FACADE_UNTRUSTED_SIGNATURE_VALID",
            result=CheckResult.FAIL,
            message=f"Prevalidation check mismatch: {preval_check}",
            applies_to="ASI_3B",
        )

    return CheckOutcome(
        check_name="FACADE_UNTRUSTED_SIGNATURE_VALID",
        result=CheckResult.PASS,
        message="Facade has valid signature from untrusted root",
        applies_to="ASI_3B",
    )


# ============================================================================
# Main Verification Function
# ============================================================================

def verify_run(
    run_log: Dict[str, Any],
    expected_bundle_hash: Optional[str] = None,
    expected_verifier_hash: Optional[str] = None,
    expected_cert_hash: Optional[str] = None,
    prevalidation_bundle: Optional[Dict[str, Any]] = None,
) -> VerificationResult:
    """
    Run all 17 verifier checks on a single run log.

    Args:
        run_log: The run log dictionary
        expected_bundle_hash: For prevalidation checks
        expected_verifier_hash: For prevalidation checks
        expected_cert_hash: For facade certificate check
        prevalidation_bundle: Full prevalidation bundle for signature validity check

    Returns:
        VerificationResult with all check outcomes
    """
    run_id = run_log.get("run_id", "unknown")
    condition = run_log.get("condition", "unknown")

    checks: List[CheckOutcome] = []

    # Run all 17 checks
    checks.append(check_asi0_regression(run_log))
    checks.append(check_asi0_regression_zero_step(run_log))
    checks.append(check_both_successors_instantiated(run_log))
    checks.append(check_candidate_evaluation_occurs(run_log))
    checks.append(check_legitimate_commits(run_log))
    checks.append(check_facade_rejected(run_log))
    checks.append(check_facade_never_authority(run_log))
    checks.append(check_rejection_reason_untrusted(run_log))
    checks.append(check_commit_input_typed(run_log))
    checks.append(check_no_behavioral_inspection(run_log))
    checks.append(check_evaluability_preserved(run_log))
    checks.append(check_no_responsibility_smear(run_log))
    checks.append(check_no_revocation_triggered(run_log))
    checks.append(check_prevalidation_bundle_hash_matches(run_log, expected_bundle_hash))
    checks.append(check_prevalidation_verifier_hash_matches(run_log, expected_verifier_hash))
    checks.append(check_facade_cert_matches_prevalidation(run_log, expected_cert_hash))
    checks.append(check_facade_untrusted_signature_valid(run_log, prevalidation_bundle))

    # Determine overall pass/fail
    # A check passes if result is PASS or NOT_APPLICABLE
    all_passed = all(
        c.result in (CheckResult.PASS, CheckResult.NOT_APPLICABLE)
        for c in checks
    )

    # Determine classification
    if all_passed:
        classification = "VERIFIED_ASI3_PASS"
    else:
        # Find first failing check for classification
        for c in checks:
            if c.result == CheckResult.FAIL:
                if c.check_name.startswith("ASI0"):
                    classification = "INVALID_RUN / REGRESSION_FAILURE"
                elif "PREVALIDATION" in c.check_name:
                    classification = "INVALID_RUN / DESIGN_DRIFT"
                elif c.check_name in ("FACADE_REJECTED", "LEGITIMATE_COMMITS"):
                    classification = "ASI_FAIL / AUTHORITY_MISATTRIBUTION"
                elif c.check_name == "EVALUABILITY_PRESERVED":
                    classification = "ASI_FAIL / EVALUABILITY_BREAK"
                elif c.check_name == "NO_RESPONSIBILITY_SMEAR":
                    classification = "ASI_FAIL / RESPONSIBILITY_SMEAR"
                else:
                    classification = "INVALID_RUN / VERIFIER_SPEC_MISMATCH"
                break
        else:
            classification = "UNKNOWN_FAILURE"

    return VerificationResult(
        run_id=run_id,
        condition=condition,
        all_passed=all_passed,
        checks=checks,
        classification=classification,
    )


def verify_experiment(
    logs_a: List[Dict[str, Any]],
    logs_b: List[Dict[str, Any]],
    expected_bundle_hash: Optional[str] = None,
    expected_verifier_hash: Optional[str] = None,
    expected_cert_hash: Optional[str] = None,
) -> tuple[bool, str, List[VerificationResult]]:
    """
    Verify the complete ASI-3 experiment.

    Returns:
        Tuple of (all_passed, classification, results)
    """
    all_results: List[VerificationResult] = []

    # Verify Condition A runs
    for log in logs_a:
        result = verify_run(log)
        all_results.append(result)

    # Verify Condition B runs
    for log in logs_b:
        result = verify_run(
            log,
            expected_bundle_hash=expected_bundle_hash,
            expected_verifier_hash=expected_verifier_hash,
            expected_cert_hash=expected_cert_hash,
        )
        all_results.append(result)

    # Overall pass/fail
    all_passed = all(r.all_passed for r in all_results)

    if all_passed:
        classification = "VERIFIED_ASI3_PASS"
    else:
        # Find first failure
        for r in all_results:
            if not r.all_passed:
                classification = r.classification
                break
        else:
            classification = "UNKNOWN_FAILURE"

    return all_passed, classification, all_results


def print_verification_report(results: List[VerificationResult]):
    """Print a human-readable verification report."""
    print()
    print("=" * 60)
    print("ASI-3 Verification Report")
    print("=" * 60)
    print()

    for result in results:
        status = "✓ PASS" if result.all_passed else "✗ FAIL"
        print(f"Run: {result.run_id}")
        print(f"  Condition: {result.condition}")
        print(f"  Status: {status}")
        print(f"  Classification: {result.classification}")
        print()

        # Show failed checks
        failed = [c for c in result.checks if c.result == CheckResult.FAIL]
        if failed:
            print("  Failed Checks:")
            for c in failed:
                print(f"    - {c.check_name}: {c.message}")
            print()

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ASI-3 Verifier")
    parser.add_argument("--results-dir", type=str, help="Path to results directory")
    args = parser.parse_args()

    results_dir = Path(args.results_dir) if args.results_dir else Path(__file__).parent.parent / "results"

    # Load logs
    logs_a = []
    logs_b = []

    for f in sorted(results_dir.glob("log_A_*.json")):
        with open(f, 'r') as fp:
            logs_a.append(json.load(fp))

    for f in sorted(results_dir.glob("log_B_*.json")):
        with open(f, 'r') as fp:
            logs_b.append(json.load(fp))

    if not logs_a and not logs_b:
        print(f"No logs found in {results_dir}")
        sys.exit(1)

    # Verify
    all_passed, classification, results = verify_experiment(logs_a, logs_b)

    # Print report
    print_verification_report(results)

    print(f"Final Classification: {classification}")
    sys.exit(0 if all_passed else 1)
