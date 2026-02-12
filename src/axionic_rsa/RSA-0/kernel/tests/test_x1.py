"""
RSA X-1 — Test Suite

Tests for constitutional self-amendment under frozen sovereignty.
Covers all 10 rejection codes, positive adoption path, cooling, ratchet,
replay determinism, and structural constraint preservation.

Test categories:
  1. Artifact types (AmendmentProposal, AmendmentAdoptionRecord)
  2. Constitution loader X-1 (hash-based citations, authority namespace)
  3. Amendment admission gates 1–8B
  4. Policy core X-1 (QUEUE_AMENDMENT, ADOPT, ACTION, REFUSE, EXIT)
  5. Cooling, stale invalidation, ratchet monotonicity
  6. End-to-end adoption path
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

# ---------------------------------------------------------------------------
# Setup path
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "kernel"))

from src.artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    DecisionType,
    ExitReasonCode,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    canonical_json,
)
from src.rsax1.artifacts_x1 import (
    AmendmentAdoptionRecord,
    AmendmentProposal,
    AmendmentRejectionCode,
    DecisionTypeX1,
    InternalStateX1,
    PendingAmendment,
    StateDelta,
)
from src.rsax1.constitution_x1 import (
    CitationIndexX1,
    ConstitutionError,
    ConstitutionX1,
    canonicalize_constitution_bytes,
)
from src.rsax1.admission_x1 import (
    AmendmentAdmissionPipeline,
    AmendmentAdmissionResult,
    AmendmentGate,
    check_cooling_satisfied,
    invalidate_stale_proposals,
)
from src.rsax1.policy_core_x1 import (
    PolicyOutputX1,
    policy_core_x1,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONSTITUTION_DIR = REPO_ROOT / "artifacts" / "phase-x" / "constitution"
V02_YAML_PATH = str(CONSTITUTION_DIR / "rsa_constitution.v0.2.yaml")
V02_SCHEMA_PATH = str(CONSTITUTION_DIR / "rsa_constitution.v0.2.schema.json")


@pytest.fixture
def v02_constitution() -> ConstitutionX1:
    """Load the v0.2 constitution."""
    return ConstitutionX1(yaml_path=V02_YAML_PATH)


@pytest.fixture
def v02_schema() -> Dict[str, Any]:
    """Load the v0.2 schema."""
    with open(V02_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def v02_yaml_text() -> str:
    """Raw YAML text of v0.2 constitution."""
    return Path(V02_YAML_PATH).read_text()


@pytest.fixture
def v02_hash() -> str:
    """SHA-256 hash of v0.2 constitution."""
    return hashlib.sha256(Path(V02_YAML_PATH).read_bytes()).hexdigest()


def _make_timestamp_obs(t: str = "2026-02-12T00:00:00Z") -> Observation:
    return Observation(
        kind=ObservationKind.TIMESTAMP.value,
        payload={"iso8601_utc": t},
        author=Author.HOST.value,
        created_at=t,
    )


def _make_trivial_amendment(
    constitution: ConstitutionX1,
    note_text: str = "Trivial comment change for testing",
) -> AmendmentProposal:
    """Create a trivial amendment that changes only a comment/note."""
    data = copy.deepcopy(constitution.data)
    data["meta"]["notes"].append(note_text)
    new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
    new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

    return AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=new_yaml,
        proposed_constitution_hash=new_hash,
        justification="Trivial comment change for testing",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
        diff_summary="Added note to meta.notes",
        created_at="2026-02-12T00:00:00Z",
    )


def _make_default_state(constitution: ConstitutionX1, cycle: int = 0) -> InternalStateX1:
    return InternalStateX1(
        cycle_index=cycle,
        active_constitution_hash=constitution.sha256,
    )


# ===================================================================
# 1. Artifact Types
# ===================================================================

class TestArtifactTypes:
    def test_amendment_proposal_dual_serialization(self, v02_constitution):
        proposal = _make_trivial_amendment(v02_constitution)
        full = proposal.to_dict_full()
        id_dict = proposal.to_dict_id()

        assert "proposed_constitution_yaml" in full
        assert "proposed_constitution_yaml" not in id_dict
        assert full["proposed_constitution_hash"] == id_dict["proposed_constitution_hash"]
        assert full["prior_constitution_hash"] == id_dict["prior_constitution_hash"]

    def test_amendment_proposal_id_stable(self, v02_constitution):
        p1 = _make_trivial_amendment(v02_constitution)
        p2 = _make_trivial_amendment(v02_constitution)
        # Same content → same ID
        assert p1.id == p2.id

    def test_adoption_record_fields(self, v02_constitution):
        record = AmendmentAdoptionRecord(
            proposal_id="test_proposal_id",
            prior_constitution_hash=v02_constitution.sha256,
            new_constitution_hash="abcd1234" * 8,
            effective_cycle=5,
            authority_citations=["authority:test#AUTH_GOVERNANCE"],
            created_at="2026-02-12T00:00:00Z",
        )
        d = record.to_dict()
        assert d["type"] == "AmendmentAdoptionRecord"
        assert d["effective_cycle"] == 5
        assert record.author == Author.KERNEL.value

    def test_internal_state_x1_advance(self, v02_constitution):
        state = _make_default_state(v02_constitution, cycle=3)
        next_state = state.advance(DecisionTypeX1.ACTION)
        assert next_state.cycle_index == 4
        assert next_state.last_decision == DecisionTypeX1.ACTION
        assert len(next_state.decision_type_history) == 1

    def test_pending_amendment_serialization(self):
        pa = PendingAmendment(
            proposal_id="p1",
            prior_constitution_hash="aaa",
            proposed_constitution_hash="bbb",
            proposal_cycle=2,
        )
        d = pa.to_dict()
        assert d["proposal_cycle"] == 2
        assert d["proposal_id"] == "p1"


# ===================================================================
# 2. Constitution Loader X-1
# ===================================================================

class TestConstitutionX1:
    def test_load_from_file(self, v02_constitution):
        assert v02_constitution.version == "0.2"
        assert v02_constitution.sha256
        assert v02_constitution.amendments_enabled()
        assert v02_constitution.has_eck_sections()

    def test_load_from_string(self, v02_yaml_text, v02_hash):
        c = ConstitutionX1(yaml_string=v02_yaml_text, expected_hash=v02_hash)
        assert c.version == "0.2"
        assert c.sha256 == v02_hash

    def test_hash_mismatch_raises(self, v02_yaml_text):
        with pytest.raises(ConstitutionError, match="Hash mismatch"):
            ConstitutionX1(yaml_string=v02_yaml_text, expected_hash="wrong_hash")

    def test_eck_accessors(self, v02_constitution):
        assert v02_constitution.amendment_procedure.get("cooling_period_cycles") == 2
        assert v02_constitution.authority_reference_mode() == "BOTH"
        assert len(v02_constitution.authority_model.get("authorities", [])) == 5
        assert v02_constitution.max_constitution_bytes() == 32768

    def test_density_computation(self, v02_constitution):
        A, B, M, density = v02_constitution.compute_density()
        assert A == 3
        assert B == 4
        assert M == 4
        assert density < 1.0
        assert density == pytest.approx(4 / 12, rel=1e-6)

    def test_action_types_no_exit(self, v02_constitution):
        types = v02_constitution.get_action_types()
        assert "Exit" not in types
        assert set(types) == {"Notify", "ReadLocal", "WriteLocal", "LogAppend"}


# ===================================================================
# 3. Citation Index X-1
# ===================================================================

class TestCitationIndexX1:
    def test_hash_based_citation(self, v02_constitution):
        h = v02_constitution.sha256
        citation = f"constitution:{h}#INV-REPLAY-DETERMINISM"
        resolved = v02_constitution.resolve_citation(citation)
        assert resolved is not None
        assert resolved["id"] == "INV-REPLAY-DETERMINISM"

    def test_cl_citation(self, v02_constitution):
        citation = v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE")
        resolved = v02_constitution.resolve_citation(citation)
        assert resolved is not None
        assert resolved["id"] == "CL-AMENDMENT-PROCEDURE"

    def test_authority_citation(self, v02_constitution):
        citation = v02_constitution.make_authority_citation("AUTH_GOVERNANCE")
        resolved = v02_constitution.resolve_citation(citation)
        assert resolved is not None

    def test_authority_unresolvable(self, v02_constitution):
        citation = f"authority:{v02_constitution.sha256}#AUTH_NONEXISTENT"
        resolved = v02_constitution.resolve_citation(citation)
        assert resolved is None

    def test_both_mode_validation(self, v02_constitution):
        h = v02_constitution.sha256
        # Valid BOTH: one authority + one clause
        valid, msg = v02_constitution.citation_index.validate_citation_both([
            f"authority:{h}#AUTH_GOVERNANCE",
            f"constitution:{h}#CL-AMENDMENT-PROCEDURE",
        ])
        assert valid, msg

    def test_both_mode_missing_authority(self, v02_constitution):
        h = v02_constitution.sha256
        valid, msg = v02_constitution.citation_index.validate_citation_both([
            f"constitution:{h}#CL-AMENDMENT-PROCEDURE",
        ])
        assert not valid
        assert "authority" in msg.lower()

    def test_both_mode_missing_clause(self, v02_constitution):
        h = v02_constitution.sha256
        valid, msg = v02_constitution.citation_index.validate_citation_both([
            f"authority:{h}#AUTH_GOVERNANCE",
        ])
        assert not valid
        assert "clause" in msg.lower()

    def test_legacy_version_citation(self, v02_constitution):
        """Legacy constitution:v<version>#<id> format still works."""
        citation = f"constitution:v{v02_constitution.version}#INV-AUTHORITY-CITED"
        resolved = v02_constitution.resolve_citation(citation)
        assert resolved is not None

    def test_all_cl_ids_resolvable(self, v02_constitution):
        """All CL-* IDs in v0.2 must be resolvable."""
        idx = v02_constitution.citation_index
        ids = idx.all_ids()
        cl_ids = [i for i in ids if i.startswith("CL-")]
        assert len(cl_ids) >= 10  # We defined 14

        for cl_id in cl_ids:
            citation = v02_constitution.make_citation(cl_id)
            assert v02_constitution.resolve_citation(citation) is not None, f"CL-* unresolvable: {cl_id}"


# ===================================================================
# 4. Canonicalization
# ===================================================================

class TestCanonicalization:
    def test_crlf_normalization(self):
        raw = b"line1\r\nline2\r\n"
        canonical = canonicalize_constitution_bytes(raw)
        assert b"\r" not in canonical
        assert canonical == b"line1\nline2\n"

    def test_trailing_whitespace_stripped(self):
        raw = b"line1   \nline2\t\t\n"
        # tabs in content are forbidden
        with pytest.raises(ConstitutionError, match="tab"):
            canonicalize_constitution_bytes(raw)

    def test_tab_rejection(self):
        raw = b"key:\tvalue\n"
        with pytest.raises(ConstitutionError, match="tab"):
            canonicalize_constitution_bytes(raw)

    def test_clean_yaml_passes(self):
        raw = b"meta:\n  version: '0.2'\n"
        canonical = canonicalize_constitution_bytes(raw)
        assert canonical == b"meta:\n  version: '0.2'\n"


# ===================================================================
# 5. Amendment Admission Gates
# ===================================================================

class TestAmendmentAdmissionGates:
    """Tests for each gate in the amendment admission pipeline."""

    def test_gate1_missing_fields(self, v02_constitution, v02_schema):
        """Gate 1 (completeness): missing required field → reject."""
        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml="",  # Missing!
            proposed_constitution_hash="abc",
            justification="test",
            authority_citations=["x"],
            created_at="2026-02-12T00:00:00Z",
        )
        pipeline = AmendmentAdmissionPipeline(
            constitution=v02_constitution, schema=v02_schema
        )
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert len(rejected) == 1
        assert rejected[0].rejection_code == AmendmentRejectionCode.SCHEMA_INVALID

    def test_gate2_unresolvable_citation(self, v02_constitution, v02_schema):
        """Gate 2 (authority): unresolvable citation → reject."""
        proposal = _make_trivial_amendment(v02_constitution)
        proposal.authority_citations = ["authority:fakehash#AUTH_FAKE"]
        # Reset ID since citations changed
        proposal.id = ""
        proposal.__post_init__()

        pipeline = AmendmentAdmissionPipeline(
            constitution=v02_constitution, schema=v02_schema
        )
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == "CITATION_UNRESOLVABLE"

    def test_gate4_amendments_disabled(self):
        """Gate 4 (constitution compliance): amendments_enabled=false → AMENDMENTS_DISABLED."""
        v011_path = str(CONSTITUTION_DIR / "rsa_constitution.v0.1.1.yaml")
        v011 = ConstitutionX1(yaml_path=v011_path)
        assert not v011.amendments_enabled()

        proposal = AmendmentProposal(
            prior_constitution_hash=v011.sha256,
            proposed_constitution_yaml="test: true",
            proposed_constitution_hash=hashlib.sha256(b"test: true").hexdigest(),
            justification="test",
            authority_citations=[
                f"constitution:v{v011.version}#INV-AUTHORITY-CITED",
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v011)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.AMENDMENTS_DISABLED

    def test_gate6_prior_hash_mismatch(self, v02_constitution, v02_schema):
        """Gate 6: prior_constitution_hash doesn't match active → PRIOR_HASH_MISMATCH."""
        proposal = _make_trivial_amendment(v02_constitution)
        proposal.prior_constitution_hash = "wrong_hash_" + "0" * 53
        proposal.id = ""
        proposal.__post_init__()

        pipeline = AmendmentAdmissionPipeline(
            constitution=v02_constitution, schema=v02_schema
        )
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.PRIOR_HASH_MISMATCH

    def test_gate7_hash_mismatch(self, v02_constitution, v02_schema):
        """Gate 7: declared hash doesn't match YAML → SCHEMA_INVALID."""
        proposal = _make_trivial_amendment(v02_constitution)
        proposal.proposed_constitution_hash = "mismatched_" + "0" * 53
        proposal.id = ""
        proposal.__post_init__()

        pipeline = AmendmentAdmissionPipeline(
            constitution=v02_constitution, schema=v02_schema
        )
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.SCHEMA_INVALID

    def test_gate7_eck_missing_in_proposed(self, v02_constitution, v02_schema):
        """Gate 7: proposed constitution missing ECK sections → ECK_MISSING."""
        data = copy.deepcopy(v02_constitution.data)
        del data["AmendmentProcedure"]  # Remove ECK section
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Remove ECK test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(
            constitution=v02_constitution,
            schema=None,  # Skip schema validation to test gate 7 ECK check
        )
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.ECK_MISSING

    def test_gate7_byte_size_exceeded(self, v02_constitution):
        """Gate 7: constitution exceeds max_constitution_bytes → SCHEMA_INVALID."""
        data = copy.deepcopy(v02_constitution.data)
        # Add a huge note to blow past 32768 bytes
        data["meta"]["notes"].append("X" * 40000)
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Size test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.SCHEMA_INVALID

    def test_gate8a_forbidden_keys(self, v02_constitution):
        """Gate 8A: physics claim (forbidden keys like 'script') → PHYSICS_CLAIM_DETECTED."""
        data = copy.deepcopy(v02_constitution.data)
        data["script"] = "print('pwned')"
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Physics claim test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        # Skip schema validation (would catch the extra key)
        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.PHYSICS_CLAIM_DETECTED

    def test_gate8b_wildcard_authority(self, v02_constitution):
        """Gate 8B.2: wildcard authority → WILDCARD_MAPPING."""
        data = copy.deepcopy(v02_constitution.data)
        data["AuthorityModel"]["action_permissions"][0]["authority"] = "*"
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Wildcard test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.WILDCARD_MAPPING

    def test_gate8b_universal_authorization(self, v02_constitution):
        """Gate 8B.3: density == 1 → UNIVERSAL_AUTHORIZATION."""
        data = copy.deepcopy(v02_constitution.data)
        # Make every authority map to every action → density = 1
        all_actions = [at["type"] for at in data["action_space"]["action_types"]]
        data["AuthorityModel"]["action_permissions"] = [
            {"id": "CL-PERM-TELEMETRY", "authority": "AUTH_TELEMETRY", "actions": list(all_actions)},
            {"id": "CL-PERM-IO-READ", "authority": "AUTH_IO_READ", "actions": list(all_actions)},
            {"id": "CL-PERM-IO-WRITE", "authority": "AUTH_IO_WRITE", "actions": list(all_actions)},
        ]
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Universal auth test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.UNIVERSAL_AUTHORIZATION

    def test_gate8b_scope_collapse(self, v02_constitution):
        """Gate 8B.4: no action requires scope → SCOPE_COLLAPSE."""
        data = copy.deepcopy(v02_constitution.data)
        # Make all actions globally scoped
        for pas in data["ScopeSystem"]["per_action_scope"]:
            pas["scope_claim_required"] = False
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Scope collapse test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.SCOPE_COLLAPSE

    def test_gate8b_ratchet_cooling_reduction(self, v02_constitution):
        """Gate 8B.5: cooling period reduced → ENVELOPE_DEGRADED."""
        data = copy.deepcopy(v02_constitution.data)
        data["AmendmentProcedure"]["cooling_period_cycles"] = 1  # Reduced from 2
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Cooling reduction test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.ENVELOPE_DEGRADED

    def test_gate8b_ratchet_threshold_reduction(self, v02_constitution):
        """Gate 8B.5: authorization threshold reduced → ENVELOPE_DEGRADED."""
        data = copy.deepcopy(v02_constitution.data)
        data["AmendmentProcedure"]["authorization_threshold"] = 0  # Reduced from 1
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Threshold reduction test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.ENVELOPE_DEGRADED

    def test_gate8b_ratchet_density_bound_increased(self, v02_constitution):
        """Gate 8B.5: density_upper_bound increased → ENVELOPE_DEGRADED."""
        data = copy.deepcopy(v02_constitution.data)
        data["AmendmentProcedure"]["density_upper_bound"] = 0.95  # Increased from 0.75
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Density bound increase test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.ENVELOPE_DEGRADED

    def test_gate8b_ratchet_density_bound_removed(self, v02_constitution):
        """Gate 8B.5: density_upper_bound removed → ENVELOPE_DEGRADED."""
        data = copy.deepcopy(v02_constitution.data)
        del data["AmendmentProcedure"]["density_upper_bound"]
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        proposal = AmendmentProposal(
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Density bound removal test",
            authority_citations=[
                v02_constitution.make_authority_citation("AUTH_GOVERNANCE"),
                v02_constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        assert len(admitted) == 0
        assert rejected[0].rejection_code == AmendmentRejectionCode.ENVELOPE_DEGRADED

    def test_trivial_amendment_admitted(self, v02_constitution):
        """Positive path: trivial amendment passes all gates."""
        proposal = _make_trivial_amendment(v02_constitution)

        pipeline = AmendmentAdmissionPipeline(
            constitution=v02_constitution,
            schema=None,  # Skip schema for trivial (meta.notes won't validate)
        )
        admitted, rejected, events = pipeline.evaluate([proposal])
        assert len(admitted) == 1
        assert len(rejected) == 0
        assert admitted[0].proposal.id == proposal.id


# ===================================================================
# 6. Cooling & Stale Invalidation
# ===================================================================

class TestCoolingAndInvalidation:
    def test_cooling_not_satisfied(self):
        pa = PendingAmendment("p1", "hash1", "hash2", proposal_cycle=5)
        assert not check_cooling_satisfied(pa, current_cycle=6, cooling_period=2)

    def test_cooling_satisfied(self):
        pa = PendingAmendment("p1", "hash1", "hash2", proposal_cycle=5)
        assert check_cooling_satisfied(pa, current_cycle=7, cooling_period=2)

    def test_cooling_exactly_at_boundary(self):
        pa = PendingAmendment("p1", "hash1", "hash2", proposal_cycle=5)
        assert check_cooling_satisfied(pa, current_cycle=7, cooling_period=2)
        assert not check_cooling_satisfied(pa, current_cycle=6, cooling_period=2)

    def test_stale_invalidation(self):
        pending = [
            PendingAmendment("p1", "old_hash", "new_hash_1", 1),
            PendingAmendment("p2", "new_hash_1", "new_hash_2", 2),
            PendingAmendment("p3", "old_hash", "new_hash_3", 3),
        ]
        remaining, invalidated = invalidate_stale_proposals(pending, "new_hash_1")
        assert len(remaining) == 1
        assert remaining[0].proposal_id == "p2"
        assert len(invalidated) == 2

    def test_stale_invalidation_all_stale(self):
        pending = [
            PendingAmendment("p1", "old", "new1", 1),
            PendingAmendment("p2", "old", "new2", 2),
        ]
        remaining, invalidated = invalidate_stale_proposals(pending, "completely_new")
        assert len(remaining) == 0
        assert len(invalidated) == 2


# ===================================================================
# 7. Policy Core X-1
# ===================================================================

class TestPolicyCoreX1:
    def test_refuse_no_timestamp(self, v02_constitution):
        """Missing TIMESTAMP observation → REFUSE."""
        state = _make_default_state(v02_constitution)
        result = policy_core_x1(
            observations=[],
            action_candidates=[],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert result.decision_type == DecisionTypeX1.REFUSE

    def test_exit_on_integrity_fail(self, v02_constitution):
        """Integrity failure → EXIT."""
        state = _make_default_state(v02_constitution)
        obs = [
            _make_timestamp_obs(),
            Observation(
                kind=ObservationKind.SYSTEM.value,
                payload={"event": "startup_integrity_fail", "detail": "test"},
                author=Author.HOST.value,
                created_at="2026-02-12T00:00:00Z",
            ),
        ]
        result = policy_core_x1(
            observations=obs,
            action_candidates=[],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert result.decision_type == DecisionTypeX1.EXIT
        assert result.exit_record is not None

    def test_queue_amendment(self, v02_constitution):
        """Valid amendment proposal → QUEUE_AMENDMENT."""
        state = _make_default_state(v02_constitution)
        proposal = _make_trivial_amendment(v02_constitution)

        result = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[],
            amendment_candidates=[proposal],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert result.decision_type == DecisionTypeX1.QUEUE_AMENDMENT
        assert result.queued_proposal is not None
        assert result.state_delta is not None
        assert result.state_delta.delta_type == "queue_amendment"

    def test_adopt_after_cooling(self, v02_constitution):
        """Pending amendment after cooling → ADOPT."""
        state = _make_default_state(v02_constitution, cycle=5)
        proposal = _make_trivial_amendment(v02_constitution)

        pending = PendingAmendment(
            proposal_id=proposal.id,
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_hash=proposal.proposed_constitution_hash,
            proposal_cycle=2,  # Proposed at cycle 2, now at cycle 5 → cooling=2 satisfied
        )
        state.pending_amendments = [pending]

        result = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[],
            amendment_candidates=[],
            pending_amendment_candidates=[pending],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert result.decision_type == DecisionTypeX1.ADOPT
        assert result.adoption_record is not None
        assert result.adoption_record.effective_cycle == 6
        assert result.state_delta.delta_type == "adopt_amendment"

    def test_refuse_no_actions(self, v02_constitution):
        """No candidates at all → REFUSE."""
        state = _make_default_state(v02_constitution)
        result = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert result.decision_type == DecisionTypeX1.REFUSE

    def test_action_path_with_valid_bundle(self, v02_constitution):
        """Valid action candidate → ACTION with warrant."""
        state = _make_default_state(v02_constitution)
        h = v02_constitution.sha256

        bundle = CandidateBundle(
            action_request=ActionRequest(
                action_type=ActionType.NOTIFY.value,
                fields={"target": "stdout", "message": "hello"},
                author=Author.REFLECTION.value,
                created_at="2026-02-12T00:00:00Z",
            ),
            scope_claim=ScopeClaim(
                observation_ids=[],
                claim="Notify stdout",
                clause_ref=f"constitution:{h}#CL-SCOPE-SYSTEM",
                author=Author.REFLECTION.value,
                created_at="2026-02-12T00:00:00Z",
            ),
            justification=Justification(
                text="Test notification",
                author=Author.REFLECTION.value,
                created_at="2026-02-12T00:00:00Z",
            ),
            authority_citations=[
                f"authority:{h}#AUTH_TELEMETRY",
                f"constitution:{h}#CL-PERM-TELEMETRY",
            ],
        )

        result = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[bundle],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert result.decision_type == DecisionTypeX1.ACTION
        assert result.warrant is not None
        assert result.bundle is not None

    def test_adoption_priority_over_amendment(self, v02_constitution):
        """ADOPT takes priority over QUEUE_AMENDMENT."""
        state = _make_default_state(v02_constitution, cycle=5)
        proposal = _make_trivial_amendment(v02_constitution)

        pending = PendingAmendment(
            proposal_id=proposal.id,
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_hash=proposal.proposed_constitution_hash,
            proposal_cycle=2,
        )

        new_proposal = _make_trivial_amendment(v02_constitution, "Another change")

        result = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[],
            amendment_candidates=[new_proposal],
            pending_amendment_candidates=[pending],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        # Adoption should take priority
        assert result.decision_type == DecisionTypeX1.ADOPT

    def test_amendment_priority_over_action(self, v02_constitution):
        """QUEUE_AMENDMENT takes priority over ACTION."""
        state = _make_default_state(v02_constitution)
        h = v02_constitution.sha256
        proposal = _make_trivial_amendment(v02_constitution)

        bundle = CandidateBundle(
            action_request=ActionRequest(
                action_type=ActionType.NOTIFY.value,
                fields={"target": "stdout", "message": "hello"},
                author=Author.REFLECTION.value,
                created_at="2026-02-12T00:00:00Z",
            ),
            scope_claim=ScopeClaim(
                observation_ids=[],
                claim="Notify",
                clause_ref=f"constitution:{h}#CL-SCOPE-SYSTEM",
                author=Author.REFLECTION.value,
                created_at="2026-02-12T00:00:00Z",
            ),
            justification=Justification(
                text="Test",
                author=Author.REFLECTION.value,
                created_at="2026-02-12T00:00:00Z",
            ),
            authority_citations=[
                f"authority:{h}#AUTH_TELEMETRY",
                f"constitution:{h}#CL-PERM-TELEMETRY",
            ],
        )

        result = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[bundle],
            amendment_candidates=[proposal],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        # Amendment should take priority over action
        assert result.decision_type == DecisionTypeX1.QUEUE_AMENDMENT


# ===================================================================
# 8. Decision determinism
# ===================================================================

class TestDeterminism:
    def test_same_inputs_same_output(self, v02_constitution):
        """Same inputs produce identical policy output (replay determinism)."""
        state = _make_default_state(v02_constitution)
        proposal = _make_trivial_amendment(v02_constitution)
        obs = [_make_timestamp_obs()]

        r1 = policy_core_x1(
            observations=obs,
            action_candidates=[],
            amendment_candidates=[proposal],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        r2 = policy_core_x1(
            observations=obs,
            action_candidates=[],
            amendment_candidates=[proposal],
            pending_amendment_candidates=[],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert r1.decision_type == r2.decision_type
        assert r1.to_dict() == r2.to_dict()

    def test_adoption_determinism(self, v02_constitution):
        """Adoption produces identical output on re-evaluation."""
        state = _make_default_state(v02_constitution, cycle=5)
        proposal = _make_trivial_amendment(v02_constitution)
        pending = PendingAmendment(
            proposal_id=proposal.id,
            prior_constitution_hash=v02_constitution.sha256,
            proposed_constitution_hash=proposal.proposed_constitution_hash,
            proposal_cycle=2,
        )

        r1 = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[],
            amendment_candidates=[],
            pending_amendment_candidates=[pending],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        r2 = policy_core_x1(
            observations=[_make_timestamp_obs()],
            action_candidates=[],
            amendment_candidates=[],
            pending_amendment_candidates=[pending],
            constitution=v02_constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
        )
        assert r1.decision_type == r2.decision_type == DecisionTypeX1.ADOPT
        assert r1.adoption_record.id == r2.adoption_record.id


# ===================================================================
# 9. Ratchet monotonicity (comprehensive)
# ===================================================================

class TestRatchetMonotonicity:
    """Verify ratchet fields can only tighten, never loosen."""

    def _make_ratchet_proposal(self, constitution, **overrides):
        data = copy.deepcopy(constitution.data)
        for key, value in overrides.items():
            if value is None and key in data["AmendmentProcedure"]:
                del data["AmendmentProcedure"][key]
            elif value is not None:
                data["AmendmentProcedure"][key] = value
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        new_hash = hashlib.sha256(new_yaml.encode("utf-8")).hexdigest()

        return AmendmentProposal(
            prior_constitution_hash=constitution.sha256,
            proposed_constitution_yaml=new_yaml,
            proposed_constitution_hash=new_hash,
            justification="Ratchet test",
            authority_citations=[
                constitution.make_authority_citation("AUTH_GOVERNANCE"),
                constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
            ],
            created_at="2026-02-12T00:00:00Z",
        )

    def test_cooling_increase_allowed(self, v02_constitution):
        """Cooling can increase (tighten)."""
        proposal = self._make_ratchet_proposal(v02_constitution, cooling_period_cycles=3)
        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        # Should pass 8B.5 (may fail on schema but not on ratchet)
        ratchet_failures = [r for r in rejected if r.rejection_code == AmendmentRejectionCode.ENVELOPE_DEGRADED]
        assert len(ratchet_failures) == 0

    def test_threshold_increase_allowed(self, v02_constitution):
        """Threshold can increase (tighten)."""
        proposal = self._make_ratchet_proposal(v02_constitution, authorization_threshold=2)
        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        ratchet_failures = [r for r in rejected if r.rejection_code == AmendmentRejectionCode.ENVELOPE_DEGRADED]
        assert len(ratchet_failures) == 0

    def test_density_bound_decrease_allowed(self, v02_constitution):
        """Density bound can decrease (tighten)."""
        proposal = self._make_ratchet_proposal(v02_constitution, density_upper_bound=0.5)
        pipeline = AmendmentAdmissionPipeline(constitution=v02_constitution)
        admitted, rejected, _ = pipeline.evaluate([proposal])
        ratchet_failures = [r for r in rejected if r.rejection_code == AmendmentRejectionCode.ENVELOPE_DEGRADED]
        assert len(ratchet_failures) == 0
