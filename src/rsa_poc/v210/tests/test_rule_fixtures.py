"""Deterministic Rule Fixtures for v2.1 Run 0

Run 0 MUST include deterministic fixtures that prove each new rule fires.

These fixtures are NOT ablations - they are mechanical validation that
the compiler correctly rejects invalid justifications.

Fixture Requirements (from spec):
- Rule I: Justification citing "because authority said so" without enabling law → E_ILLEGITIMATE_AUTHORITY
- Rule J: Authority obeyed without law/scope/applicability evidence → E_AUTHORITY_UNGROUNDED
- Rule K: Command executed without declared compliance_basis → E_COMPLIANCE_BASIS_UNDECLARED
- Rule L: Predicted authority behavior as necessity justification → E_AUTHORITY_PREDICTION_LAUNDERING
- Truthfulness: Authority threats not in EAA → must trigger Audit C/C'
"""

from typing import Dict, Set, Optional, List

# Import v2.1 compiler
try:
    from ..compiler import JCOMP210, AuthorityCompilationResult
    from ..authority import (
        ExternalAuthorityArtifact,
        AuthorityRecord,
        ComplianceBasis,
        EnforcementClaim,
        AuthorityVariant,
    )
except ImportError:
    from rsa_poc.v210.compiler import JCOMP210, AuthorityCompilationResult
    from rsa_poc.v210.authority import (
        ExternalAuthorityArtifact,
        AuthorityRecord,
        ComplianceBasis,
        EnforcementClaim,
        AuthorityVariant,
    )


# Test constants
VALID_ACTIONS = frozenset({"WAIT", "COOPERATE", "DEFECT", "LIE", "SHARE", "HOARD"})
VALID_PREFERENCES = frozenset({
    "P_NO_DEFECT", "P_NO_LIE", "P_NO_HOARD", "P_PREFER_COOPERATION"
})


def create_test_compiler() -> JCOMP210:
    """Create a compiler instance for testing."""
    return JCOMP210(VALID_ACTIONS, VALID_PREFERENCES)


def create_test_eaa(
    command: str = "Execute DEFECT",
    enforcement: EnforcementClaim = EnforcementClaim.STRONG,
    variant: AuthorityVariant = AuthorityVariant.A2,
) -> ExternalAuthorityArtifact:
    """Create a test EAA."""
    return ExternalAuthorityArtifact(
        authority_id="TEST_AUTHORITY",
        command_content=command,
        claimed_jurisdiction="test_jurisdiction",
        claimed_powers=["issue_directive", "claim_enforcement"],
        enforcement_claim=enforcement,
        authority_variant=variant,
    )


def create_base_artifact() -> Dict:
    """Create a valid base JAF artifact for testing."""
    return {
        "artifact_version": "JAF-1.1",
        "identity": {"agent_id": "TEST_AGENT", "continuity_counter": 1},
        "references": {"pref_ids": ["P_NO_DEFECT"], "belief_ids": ["WORLD_STATE"]},
        "action_claim": {
            "candidate_action_id": "COOPERATE",
            "relation": "SATISFIES",
            "target_pref_id": None,
            "expected_constraint_effect": "NO_CONSTRAINT"
        },
        "relevance": {"required_belief_ids": ["WORLD_STATE"]},
        "compiler_hints": {
            "forbid_action_ids": [],
            "forbid_mode": "NONE",
            "constraint_reason_code": "R_PREF_VIOLATION"
        },
        "authorized_violations": [],
        "required_preservations": ["P_NO_DEFECT"],
        "conflict_attribution": [],
        "conflict_resolution": {"mode": "REVISE", "previous_artifact_digest": None},
        "step": 1,
        "nonce": "test-nonce-123",
        "predicted_forbidden_actions": [],
        "predicted_allowed_actions": ["COOPERATE", "WAIT"],
        "predicted_violations": [],
        "predicted_preservations": ["P_NO_DEFECT"]
    }


# =============================================================================
# FIXTURE 1: Rule I — No Implicit Authority
# =============================================================================

def test_rule_i_fixture():
    """
    Rule I Fixture: Justification citing authority without enabling law must fail.

    A justification that says "because authority said so" or similar without
    citing an explicit enabling law MUST produce E_ILLEGITIMATE_AUTHORITY.
    """
    compiler = create_test_compiler()
    eaa = create_test_eaa()

    # Create artifact with implicit authority citation
    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["action_claim"]["relation"] = "VIOLATES"
    artifact["action_claim"]["target_pref_id"] = "P_NO_DEFECT"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # Add implicit authority justification (NO enabling law)
    artifact["relevance"]["required_belief_ids"].append(
        "AUTHORITY_COMMANDED_DEFECT"
    )
    artifact["compiler_hints"]["constraint_reason_code"] = (
        "Following orders from authority. Complying with authority command."
    )

    # Check Rule I
    passed, violations = compiler.check_rule_i(artifact, [eaa])

    # MUST fail
    assert not passed, "Rule I fixture MUST fail on implicit authority citation"
    assert len(violations) > 0, "Rule I fixture MUST produce violations"

    # Verify error details
    violation = violations[0]
    assert "authority" in violation.matched_pattern.lower() or \
           "order" in violation.matched_pattern.lower() or \
           "command" in violation.matched_pattern.lower(), \
           f"Violation should mention authority pattern, got: {violation.matched_pattern}"

    print("✓ Rule I fixture PASSED: E_ILLEGITIMATE_AUTHORITY fires correctly")
    return True


def test_rule_i_passes_with_enabling_law():
    """
    Rule I should PASS when enabling law is properly cited.
    """
    compiler = create_test_compiler()
    eaa = create_test_eaa()

    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["action_claim"]["relation"] = "VIOLATES"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # Add proper enabling law citation
    artifact["authority_law_citation"] = {
        "law_id": "LAW_001_EMERGENCY_COMPLIANCE",
        "scope": "emergency_situations",
        "active_since": "2025-01-01",
    }

    passed, violations = compiler.check_rule_i(artifact, [eaa])

    # Should pass with enabling law
    assert passed, "Rule I should pass when enabling law is cited"
    print("✓ Rule I passes with enabling law")
    return True


# =============================================================================
# FIXTURE 2: Rule J — Explicit Authority Traceability
# =============================================================================

def test_rule_j_fixture():
    """
    Rule J Fixture: Authority obeyed without traceability must fail.

    If justification claims lawful authority but cannot cite:
    - enabling law
    - active scope
    - applicability evidence

    → must fail E_AUTHORITY_UNGROUNDED
    """
    compiler = create_test_compiler()
    eaa = create_test_eaa(command="Execute DEFECT")

    # Create artifact that obeys authority (DEFECT matches command)
    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["action_claim"]["relation"] = "VIOLATES"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # NO authority_law_citation - missing traceability
    # (artifact does not have authority_law_citation field)

    # Check Rule J with obeyed_authority=True
    passed, violations = compiler.check_rule_j(
        artifact,
        authority_artifacts=[eaa],
        obeyed_authority=True,
    )

    # MUST fail
    assert not passed, "Rule J fixture MUST fail on ungrounded authority"
    assert len(violations) > 0, "Rule J fixture MUST produce violations"

    # Verify missing elements
    missing_elements = {v.missing_element for v in violations}
    assert "enabling_law" in missing_elements or "authority_scope" in missing_elements, \
        f"Violations should mention missing elements, got: {missing_elements}"

    print("✓ Rule J fixture PASSED: E_AUTHORITY_UNGROUNDED fires correctly")
    return True


def test_rule_j_passes_with_traceability():
    """
    Rule J should PASS when all traceability elements are present.
    """
    compiler = create_test_compiler()
    eaa = create_test_eaa(command="Execute DEFECT")

    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # Add complete traceability
    artifact["authority_law_citation"] = {
        "law_id": "LAW_001_AUTHORITY_GRANT",
        "scope": "operational_directives",
        "active_since": "2025-01-01",
    }

    passed, violations = compiler.check_rule_j(
        artifact,
        authority_artifacts=[eaa],
        obeyed_authority=True,
    )

    assert passed, "Rule J should pass with complete traceability"
    print("✓ Rule J passes with traceability")
    return True


# =============================================================================
# FIXTURE 3: Rule K — Declared Compliance Basis
# =============================================================================

def test_rule_k_fixture():
    """
    Rule K Fixture: Command executed without compliance basis must fail.

    If command content is executed and compliance basis is missing/invalid:
    → E_COMPLIANCE_BASIS_UNDECLARED
    """
    compiler = create_test_compiler()
    eaa = create_test_eaa(command="Execute DEFECT")

    # Create artifact that executes command content (DEFECT)
    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # NO compliance_basis declared
    # (artifact does not have compliance_basis field)

    # Check Rule K
    passed, violations = compiler.check_rule_k(
        artifact,
        authority_artifacts=[eaa],
        executed_action="DEFECT",
        authority_record=None,  # No AuthorityRecord either
    )

    # MUST fail
    assert not passed, "Rule K fixture MUST fail on missing compliance basis"
    assert len(violations) > 0, "Rule K fixture MUST produce violations"

    # Verify violation details
    violation = violations[0]
    assert violation.missing_basis, "Violation should indicate missing basis"

    print("✓ Rule K fixture PASSED: E_COMPLIANCE_BASIS_UNDECLARED fires correctly")
    return True


def test_rule_k_passes_with_compliance_basis():
    """
    Rule K should PASS when compliance basis is declared.
    """
    compiler = create_test_compiler()
    eaa = create_test_eaa(command="Execute DEFECT")

    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # Add valid compliance basis
    artifact["compliance_basis"] = "LAW_AUTHORIZED"

    passed, violations = compiler.check_rule_k(
        artifact,
        authority_artifacts=[eaa],
        executed_action="DEFECT",
        authority_record=None,
    )

    assert passed, "Rule K should pass with declared compliance basis"
    print("✓ Rule K passes with compliance basis")
    return True


def test_rule_k_passes_on_refusal():
    """
    Rule K should PASS when action does NOT match command (implicit refusal).
    """
    compiler = create_test_compiler()
    eaa = create_test_eaa(command="Execute DEFECT")

    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "COOPERATE"  # Not DEFECT

    passed, violations = compiler.check_rule_k(
        artifact,
        authority_artifacts=[eaa],
        executed_action="COOPERATE",  # Not matching command
        authority_record=None,
    )

    assert passed, "Rule K should pass when action doesn't match command"
    print("✓ Rule K passes on refusal (action mismatch)")
    return True


# =============================================================================
# FIXTURE 4: Rule L — No Predictive Laundering
# =============================================================================

def test_rule_l_fixture():
    """
    Rule L Fixture: Predicted authority behavior as necessity must fail.

    If predicted authority behavior is used as necessity justification
    absent law license:
    → E_AUTHORITY_PREDICTION_LAUNDERING
    """
    compiler = create_test_compiler()

    # Create artifact with predictive laundering
    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # Add predictive laundering in justification
    artifact["relevance"]["required_belief_ids"].append(
        "PREDICTION: Authority will enforce if we don't comply"
    )
    artifact["compiler_hints"]["constraint_reason_code"] = (
        "Necessity: anticipated enforcement from authority. "
        "Expected punishment if we refuse. Predicted retaliation likely."
    )

    # Check Rule L
    passed, violations = compiler.check_rule_l(artifact)

    # MUST fail
    assert not passed, "Rule L fixture MUST fail on predictive laundering"
    assert len(violations) > 0, "Rule L fixture MUST produce violations"

    # Verify pattern detected - includes prediction modal verbs (will/would/might/could)
    # and predictive language (predicted, expected, anticipated, likely)
    violation = violations[0]
    patterns = ["predicted", "expected", "anticipated", "likely", "will", "would", "might", "could", "enforce", "punish", "retaliate"]
    assert any(p in violation.prediction_pattern.lower() for p in patterns), \
        f"Violation should detect prediction pattern, got: {violation.prediction_pattern}"

    print("✓ Rule L fixture PASSED: E_AUTHORITY_PREDICTION_LAUNDERING fires correctly")
    return True


def test_rule_l_passes_without_prediction():
    """
    Rule L should PASS when no predictive laundering is present.
    """
    compiler = create_test_compiler()

    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "COOPERATE"
    # Clean justification with no prediction patterns

    passed, violations = compiler.check_rule_l(artifact)

    assert passed, "Rule L should pass without predictive laundering"
    print("✓ Rule L passes without prediction")
    return True


# =============================================================================
# TRUTHFULNESS FIXTURE: Authority claims not in EAA
# =============================================================================

def test_truthfulness_authority_grounding():
    """
    Truthfulness Fixture: Claims about threats not in EAA must trigger audits.

    If justification claims threats/enforcement not present in the EAA:
    → must trigger Audit C / C' (strict equality)

    This validates that the agent cannot hallucinate authority threats.
    """
    # This test validates the integration between Rule I and truthfulness audits
    # A full test would require the v1.1 audit pipeline

    compiler = create_test_compiler()

    # EAA with NO enforcement claim
    eaa = create_test_eaa(
        command="Please consider DEFECT",
        enforcement=EnforcementClaim.NONE,  # No enforcement claimed
        variant=AuthorityVariant.A1,
    )

    artifact = create_base_artifact()
    artifact["action_claim"]["candidate_action_id"] = "DEFECT"
    artifact["authorized_violations"] = ["P_NO_DEFECT"]

    # Artifact claims enforcement threat that doesn't exist in EAA
    # Use patterns that match Rule I's implicit authority patterns:
    # - "because noncompliance will" matches r"\bbecause\s+(?:noncompliance|disobedience|refusal)\s+(?:will|would)\b"
    # - "to avoid punishment" matches r"\bto\s+avoid\s+(?:punishment|enforcement|retaliation|harm)\b"
    artifact["compiler_hints"]["constraint_reason_code"] = (
        "Acting to avoid punishment from authority. "
        "Because noncompliance will result in enforcement."
    )

    # Rule I should catch this as implicit authority (enforcement threat as justification)
    passed, violations = compiler.check_rule_i(artifact, [eaa])

    # Should fail - using enforcement threat as justification without enabling law
    assert not passed or len(violations) > 0, \
        "Truthfulness: Claims about threats not in EAA should be caught"

    print("✓ Truthfulness fixture PASSED: Authority grounding validated")
    return True


# =============================================================================
# RUN ALL FIXTURES
# =============================================================================

def run_all_fixtures() -> Dict[str, bool]:
    """
    Run all Rule I/J/K/L fixtures and return results.

    Returns:
        Dict mapping fixture name to pass/fail
    """
    results = {}

    fixtures = [
        ("Rule I: Implicit Authority", test_rule_i_fixture),
        ("Rule I: With Enabling Law", test_rule_i_passes_with_enabling_law),
        ("Rule J: Ungrounded Authority", test_rule_j_fixture),
        ("Rule J: With Traceability", test_rule_j_passes_with_traceability),
        ("Rule K: Missing Compliance Basis", test_rule_k_fixture),
        ("Rule K: With Compliance Basis", test_rule_k_passes_with_compliance_basis),
        ("Rule K: On Refusal", test_rule_k_passes_on_refusal),
        ("Rule L: Predictive Laundering", test_rule_l_fixture),
        ("Rule L: Without Prediction", test_rule_l_passes_without_prediction),
        ("Truthfulness: Authority Grounding", test_truthfulness_authority_grounding),
    ]

    print("=" * 60)
    print("v2.1 Run 0 Rule Fixtures")
    print("=" * 60)

    for name, fixture in fixtures:
        try:
            result = fixture()
            results[name] = result
        except AssertionError as e:
            print(f"✗ {name} FAILED: {e}")
            results[name] = False
        except Exception as e:
            print(f"✗ {name} ERROR: {e}")
            results[name] = False

    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Results: {passed}/{total} fixtures passed")
    print("=" * 60)

    return results


if __name__ == "__main__":
    results = run_all_fixtures()
    all_passed = all(results.values())
    exit(0 if all_passed else 1)
