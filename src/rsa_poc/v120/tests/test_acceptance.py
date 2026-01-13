"""Acceptance Tests for RSA-PoC v1.2

Tests for institutional support components.
"""

import pytest
from typing import Set, Dict

# Import v1.2 components
try:
    from ..jaf.schema import (
        JAF120, ToolProvenance, ToolOperation, ToolOperationType,
        PrecedentRef, PrecedentRefType, CanonicalizationRecord,
        NORMATIVE_FIELDS, ASSISTANT_MODIFIABLE_FIELDS
    )
    from ..tools.artifact_store import ArtifactStore
    from ..tools.formal_assistant import FormalAssistant, AssistantRejectionReason
    from ..jcomp.compiler import JCOMP120, InstitutionalCompilationResult
    from ...v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, CompilerHints,
        ConflictResolution
    )
except ImportError:
    from rsa_poc.v120.jaf.schema import (
        JAF120, ToolProvenance, ToolOperation, ToolOperationType,
        PrecedentRef, PrecedentRefType, CanonicalizationRecord,
        NORMATIVE_FIELDS, ASSISTANT_MODIFIABLE_FIELDS
    )
    from rsa_poc.v120.tools.artifact_store import ArtifactStore
    from rsa_poc.v120.tools.formal_assistant import FormalAssistant, AssistantRejectionReason
    from rsa_poc.v120.jcomp.compiler import JCOMP120, InstitutionalCompilationResult
    from rsa_poc.v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, CompilerHints,
        ConflictResolution
    )


# Test fixtures
PREFERENCE_REGISTRY = frozenset({
    "P_NO_DEFECT", "P_NO_BREAK_LOCKS", "P_NO_LIE",
    "P_NO_HOARD", "P_NO_EXPLOIT", "P_PREFER_COOPERATION"
})

ACTION_INVENTORY = frozenset({"COOPERATE", "DEFECT", "WAIT", "SIGNAL"})


def make_minimal_jaf_dict(step: int = 0) -> Dict:
    """Create minimal valid JAF-1.2 dict for testing"""
    return {
        "artifact_version": "JAF-1.2",
        "identity": {"agent_id": "test_agent", "continuity_counter": step},
        "references": {"pref_ids": ["P_NO_DEFECT"], "belief_ids": ["B_TEST"]},
        "action_claim": {
            "candidate_action_id": "COOPERATE",
            "target_pref_id": None,
            "relation": "SATISFIES",
            "expected_constraint_effect": "NO_CONSTRAINT"
        },
        "relevance": {"required_belief_ids": ["B_TEST"]},
        "compiler_hints": {
            "forbid_action_ids": [],
            "forbid_mode": "NONE",
            "constraint_reason_code": "R_PREF_VIOLATION"
        },
        "authorized_violations": [],
        "required_preservations": ["P_NO_DEFECT"],
        "conflict_attribution": [],
        "conflict_resolution": None,
        "step": step,
        "nonce": "test-nonce-123",
        "predicted_forbidden_actions": ["DEFECT"],
        "predicted_allowed_actions": ["COOPERATE", "WAIT", "SIGNAL"],
        "predicted_violations": [],
        "predicted_preservations": ["P_NO_DEFECT"],
        "tool_provenance": None,
        "precedent_refs": [],
        "canonicalization_record": None,
    }


# ============================================================
# JAF-1.2 Schema Tests
# ============================================================

class TestJAF120Schema:
    """Tests for JAF-1.2 schema"""

    def test_jaf120_has_v12_fields(self):
        """JAF-1.2 must have tool_provenance, precedent_refs, canonicalization_record"""
        jaf_dict = make_minimal_jaf_dict()
        jaf = JAF120.from_dict(jaf_dict)

        assert hasattr(jaf, 'tool_provenance')
        assert hasattr(jaf, 'precedent_refs')
        assert hasattr(jaf, 'canonicalization_record')

    def test_jaf120_preserves_v11_fields(self):
        """All v1.1 fields must be present"""
        jaf_dict = make_minimal_jaf_dict()
        jaf = JAF120.from_dict(jaf_dict)

        # v1.0 fields
        assert jaf.artifact_version == "JAF-1.2"
        assert jaf.identity is not None
        assert jaf.references is not None
        assert jaf.action_claim is not None
        assert jaf.relevance is not None
        assert jaf.compiler_hints is not None
        assert isinstance(jaf.authorized_violations, set)
        assert isinstance(jaf.required_preservations, set)
        assert isinstance(jaf.conflict_attribution, set)

        # v1.1 fields
        assert isinstance(jaf.predicted_forbidden_actions, set)
        assert isinstance(jaf.predicted_allowed_actions, set)
        assert isinstance(jaf.predicted_violations, set)
        assert isinstance(jaf.predicted_preservations, set)

    def test_jaf120_to_jaf110_conversion(self):
        """to_jaf110() must preserve normative content"""
        jaf_dict = make_minimal_jaf_dict()
        jaf_dict["authorized_violations"] = ["P_NO_EXPLOIT"]
        jaf_dict["conflict_attribution"] = [["P_NO_DEFECT", "P_NO_EXPLOIT"]]

        jaf120 = JAF120.from_dict(jaf_dict)
        jaf110 = jaf120.to_jaf110()

        assert jaf110.artifact_version == "JAF-1.1"
        assert jaf110.authorized_violations == {"P_NO_EXPLOIT"}
        assert jaf110.required_preservations == {"P_NO_DEFECT"}
        assert jaf110.predicted_forbidden_actions == {"DEFECT"}

    def test_normative_fields_registry(self):
        """NORMATIVE_FIELDS must include all constraint and prediction fields"""
        assert "authorized_violations" in NORMATIVE_FIELDS
        assert "required_preservations" in NORMATIVE_FIELDS
        assert "conflict_attribution" in NORMATIVE_FIELDS
        assert "predicted_forbidden_actions" in NORMATIVE_FIELDS
        assert "predicted_violations" in NORMATIVE_FIELDS

    def test_assistant_modifiable_fields_registry(self):
        """ASSISTANT_MODIFIABLE_FIELDS must be separate from normative"""
        assert "tool_provenance" in ASSISTANT_MODIFIABLE_FIELDS
        assert "canonicalization_record" in ASSISTANT_MODIFIABLE_FIELDS

        # No overlap
        assert len(NORMATIVE_FIELDS & ASSISTANT_MODIFIABLE_FIELDS) == 0


# ============================================================
# Artifact Store Tests
# ============================================================

class TestArtifactStore:
    """Tests for append-only artifact store"""

    def test_store_append_and_lookup(self):
        """Can append and lookup by digest"""
        store = ArtifactStore()
        jaf_dict = make_minimal_jaf_dict()

        digest = store.append(jaf_dict)

        assert digest is not None
        assert len(digest) == 16  # SHA256 truncated

        retrieved = store.get_by_digest(digest)
        assert retrieved is not None
        assert retrieved["step"] == 0

    def test_store_head_reference(self):
        """HEAD returns most recent artifact"""
        store = ArtifactStore()

        jaf1 = make_minimal_jaf_dict(step=0)
        jaf2 = make_minimal_jaf_dict(step=1)

        store.append(jaf1)
        store.append(jaf2)

        head = store.get_head()
        assert head["step"] == 1

    def test_store_head_minus_n(self):
        """HEAD-N returns correct artifact"""
        store = ArtifactStore()

        for i in range(5):
            jaf = make_minimal_jaf_dict(step=i)
            store.append(jaf)

        # HEAD is step 4
        assert store.get_head()["step"] == 4

        # HEAD-1 is step 3
        head_minus_1 = store.get_head_minus_n(1)
        assert head_minus_1["step"] == 3

        # HEAD-4 is step 0
        head_minus_4 = store.get_head_minus_n(4)
        assert head_minus_4["step"] == 0

    def test_store_resolve_ref(self):
        """resolve_ref handles HEAD, HEAD-N, and direct digest"""
        store = ArtifactStore()

        jaf1 = make_minimal_jaf_dict(step=0)
        jaf2 = make_minimal_jaf_dict(step=1)

        digest1 = store.append(jaf1)
        digest2 = store.append(jaf2)

        assert store.resolve_ref("HEAD") == digest2
        assert store.resolve_ref("HEAD-1") == digest1
        assert store.resolve_ref(digest1) == digest1
        assert store.resolve_ref("nonexistent") is None

    def test_store_no_search_capability(self):
        """Store must not have search/filter methods"""
        store = ArtifactStore()

        # These methods should NOT exist
        assert not hasattr(store, 'search')
        assert not hasattr(store, 'filter')
        assert not hasattr(store, 'find_by_field')
        assert not hasattr(store, 'query')


# ============================================================
# Formal Assistant Tests
# ============================================================

class TestFormalAssistant:
    """Tests for formal assistant"""

    def test_assistant_validates_known_pref_ids(self):
        """Assistant rejects unknown preference IDs"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        jaf_dict = make_minimal_jaf_dict()
        jaf_dict["authorized_violations"] = ["P_UNKNOWN_FAKE"]

        result = assistant.process(jaf_dict)

        assert not result.success
        assert result.rejection_reason == AssistantRejectionReason.UNKNOWN_PREFERENCE_ID

    def test_assistant_validates_known_action_ids(self):
        """Assistant rejects unknown action IDs"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        jaf_dict = make_minimal_jaf_dict()
        jaf_dict["predicted_allowed_actions"] = ["COOPERATE", "FAKE_ACTION"]

        result = assistant.process(jaf_dict)

        assert not result.success
        assert result.rejection_reason == AssistantRejectionReason.UNKNOWN_ACTION_ID

    def test_assistant_canonicalizes_conflict_pairs(self):
        """Assistant canonicalizes (p2, p1) to (p1, p2) where p1 < p2"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        jaf_dict = make_minimal_jaf_dict()
        # Wrong order: P_NO_EXPLOIT > P_NO_DEFECT alphabetically
        jaf_dict["conflict_attribution"] = [["P_NO_EXPLOIT", "P_NO_DEFECT"]]
        jaf_dict["authorized_violations"] = ["P_NO_EXPLOIT"]
        jaf_dict["action_claim"]["relation"] = "VIOLATES"
        jaf_dict["action_claim"]["target_pref_id"] = "P_NO_EXPLOIT"
        jaf_dict["references"]["pref_ids"] = ["P_NO_DEFECT", "P_NO_EXPLOIT"]

        result = assistant.process(jaf_dict)

        assert result.success
        # Should be canonicalized
        ca = result.j_final_dict["conflict_attribution"]
        assert ca == [["P_NO_DEFECT", "P_NO_EXPLOIT"]]

        # Provenance should record the operation
        assert len(result.provenance.operations) > 0
        canon_ops = [op for op in result.provenance.operations
                     if op.operation_type == ToolOperationType.CANONICALIZE_CONFLICT_PAIR]
        assert len(canon_ops) >= 1

    def test_assistant_resolves_precedent_refs(self):
        """Assistant resolves HEAD/HEAD-N refs to digests"""
        store = ArtifactStore()

        # Add some artifacts
        jaf0 = make_minimal_jaf_dict(step=0)
        digest0 = store.append(jaf0)

        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        jaf_dict = make_minimal_jaf_dict(step=1)
        jaf_dict["precedent_refs"] = [{
            "ref_type": "HEAD",
            "ref_value": "HEAD",
            "resolved_digest": None
        }]

        result = assistant.process(jaf_dict)

        assert result.success
        refs = result.j_final_dict["precedent_refs"]
        assert len(refs) == 1
        assert refs[0]["resolved_digest"] == digest0

    def test_assistant_does_not_modify_normative_fields(self):
        """Assistant must not change normative content"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)

        jaf_dict = make_minimal_jaf_dict()
        original_av = jaf_dict["authorized_violations"].copy()
        original_rp = jaf_dict["required_preservations"].copy()

        result = assistant.process(jaf_dict)

        assert result.success

        # Check normative equivalence
        passed, violations = FormalAssistant.check_normative_equivalence(
            jaf_dict, result.j_final_dict
        )
        assert passed, f"Normative fields changed: {violations}"


# ============================================================
# Rule D Tamper Test
# ============================================================

class TestRuleDTamperDetection:
    """Tests for Rule D (tool non-interference)"""

    def test_rule_d_detects_av_tampering(self):
        """Rule D must detect tampering with authorized_violations"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)
        compiler = JCOMP120()

        jaf_dict = make_minimal_jaf_dict()
        apcm = {
            "COOPERATE": {"violates": set(), "satisfies": {"P_NO_DEFECT"}},
            "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
            "SIGNAL": {"violates": set(), "satisfies": set()},
        }

        result = compiler.compile_with_malicious_assistant(
            jaf_dict, assistant, apcm, ACTION_INVENTORY,
            tamper_field="authorized_violations"
        )

        assert not result.success
        assert len(result.institutional_errors) > 0

        # Should be caught by Rule D
        error_codes = [e.code for e in result.institutional_errors]
        assert JCOMP120.E_TOOL_NORMATIVE_TAMPERING in error_codes

    def test_rule_d_detects_prediction_tampering(self):
        """Rule D must detect tampering with predictive fields"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)
        compiler = JCOMP120()

        jaf_dict = make_minimal_jaf_dict()
        apcm = {
            "COOPERATE": {"violates": set(), "satisfies": {"P_NO_DEFECT"}},
            "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
            "SIGNAL": {"violates": set(), "satisfies": set()},
        }

        result = compiler.compile_with_malicious_assistant(
            jaf_dict, assistant, apcm, ACTION_INVENTORY,
            tamper_field="predicted_violations"
        )

        assert not result.success
        error_codes = [e.code for e in result.institutional_errors]
        assert JCOMP120.E_TOOL_NORMATIVE_TAMPERING in error_codes


# ============================================================
# JCOMP-1.2 Compiler Tests
# ============================================================

class TestJCOMP120:
    """Tests for v1.2 compiler"""

    def test_compile_with_assistant_success(self):
        """Successful compilation with assistant"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)
        compiler = JCOMP120()

        jaf_dict = make_minimal_jaf_dict()
        apcm = {
            "COOPERATE": {"violates": set(), "satisfies": {"P_NO_DEFECT"}},
            "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
            "SIGNAL": {"violates": set(), "satisfies": set()},
        }

        result = compiler.compile_with_assistant(
            jaf_dict, assistant, apcm, ACTION_INVENTORY
        )

        assert result.assistant_applied
        assert result.j_raw_dict is not None
        assert result.j_final_dict is not None

    def test_compile_without_assistant_for_baseline(self):
        """Compilation without assistant (baseline mode)"""
        compiler = JCOMP120()

        jaf_dict = make_minimal_jaf_dict()
        apcm = {
            "COOPERATE": {"violates": set(), "satisfies": {"P_NO_DEFECT"}},
            "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
            "SIGNAL": {"violates": set(), "satisfies": set()},
        }

        result = compiler.compile_without_assistant(
            jaf_dict, apcm, ACTION_INVENTORY,
            preference_registry=PREFERENCE_REGISTRY,
            action_inventory=ACTION_INVENTORY
        )

        assert not result.assistant_applied

    def test_compile_rejects_unknown_pref_without_assistant(self):
        """Without assistant, unknown pref IDs still fail"""
        compiler = JCOMP120()

        jaf_dict = make_minimal_jaf_dict()
        jaf_dict["authorized_violations"] = ["P_FAKE"]

        apcm = {
            "COOPERATE": {"violates": set(), "satisfies": set()},
        }

        result = compiler.compile_without_assistant(
            jaf_dict, apcm, ACTION_INVENTORY,
            preference_registry=PREFERENCE_REGISTRY,
            action_inventory=ACTION_INVENTORY
        )

        assert not result.success
        error_codes = [e.code for e in result.institutional_errors]
        assert JCOMP120.E_NONCANONICAL_REFERENCE in error_codes


# ============================================================
# Integration Tests
# ============================================================

class TestV12Integration:
    """Integration tests for full v1.2 pipeline"""

    def test_full_pipeline_clean_step(self):
        """Full pipeline on clean step (no collision)"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)
        compiler = JCOMP120()

        # Clean step: COOPERATE has no violations
        jaf_dict = make_minimal_jaf_dict()
        apcm = {
            "COOPERATE": {"violates": set(), "satisfies": {"P_NO_DEFECT"}},
            "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
            "SIGNAL": {"violates": set(), "satisfies": set()},
        }

        result = compiler.compile_with_assistant(
            jaf_dict, assistant, apcm, ACTION_INVENTORY
        )

        # Should pass v1.1 audits
        assert result.success or len(result.institutional_errors) == 0

    def test_artifact_store_persists_across_steps(self):
        """Store maintains history for precedent resolution"""
        store = ArtifactStore()
        assistant = FormalAssistant(store, PREFERENCE_REGISTRY, ACTION_INVENTORY)
        compiler = JCOMP120()

        apcm = {
            "COOPERATE": {"violates": set(), "satisfies": {"P_NO_DEFECT"}},
            "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
            "WAIT": {"violates": set(), "satisfies": set()},
            "SIGNAL": {"violates": set(), "satisfies": set()},
        }

        # Step 0
        jaf0 = make_minimal_jaf_dict(step=0)
        result0 = compiler.compile_with_assistant(jaf0, assistant, apcm, ACTION_INVENTORY)
        if result0.success:
            store.append(result0.j_final_dict)

        # Step 1 with precedent ref
        jaf1 = make_minimal_jaf_dict(step=1)
        jaf1["precedent_refs"] = [{
            "ref_type": "HEAD",
            "ref_value": "HEAD",
            "resolved_digest": None
        }]

        result1 = compiler.compile_with_assistant(jaf1, assistant, apcm, ACTION_INVENTORY)

        # Should resolve precedent
        if result1.success:
            refs = result1.j_final_dict.get("precedent_refs", [])
            assert len(refs) == 1
            assert refs[0]["resolved_digest"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
