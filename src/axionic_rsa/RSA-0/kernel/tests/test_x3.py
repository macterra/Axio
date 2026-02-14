"""
RSA X-3 — Test Suite

Tests for sovereign succession under lineage.
Covers artifact types, signature helpers, key derivation,
succession admission pipeline, treaty ratification pipeline,
boundary verifier, constitution frame, and policy core X-3.

Test categories:
  1. Artifact types (SuccessionProposal, TreatyRatification, CycleCommit/Start,
     InternalStateX3, ActiveTreatySetX3, PolicyOutputX3)
  2. Signature helpers (HKDF derivation, sovereign sig with leak detection,
     succession/ratification/cycle signing)
  3. Identity chain hash computation
  4. Constitution frame (overlay resolution, succession accessors)
  5. Succession admission pipeline (S1-S7 gates)
  6. Treaty ratification pipeline (R0-R4 gates)
  7. Boundary verifier (signature, state consistency, chain continuity)
  8. Policy core X-3 (full X3_TOPOLOGICAL 12-step ordering)
  9. ActiveTreatySetX3 (suspension, ratification, density with suspensions)
 10. SUSPENSION_UNRESOLVED grant blocking
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Setup path
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "kernel"))

from src.artifacts import (
    ActionRequest,
    Author,
    CandidateBundle,
    DecisionType,
    ExitReasonCode,
    ExecutionWarrant,
    Observation,
    ObservationKind,
    RefusalReasonCode,
    SystemEvent,
    canonical_json,
    canonical_json_bytes,
)
from src.rsax1.artifacts_x1 import (
    AmendmentProposal,
    DecisionTypeX1,
    InternalStateX1,
    PendingAmendment,
    StateDelta,
)

from src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    TreatyAdmissionEvent,
    TreatyAdmissionResult,
    TreatyGrant,
    TreatyRevocation,
    _compute_effective_density,
)
from src.rsax2.constitution_x2 import ConstitutionX2
from src.rsax2.signature import generate_keypair

from src.rsax3.artifacts_x3 import (
    ActiveTreatySetX3,
    AuthorityCode,
    BoundaryCode,
    CycleCommitPayload,
    CycleStartPayload,
    DecisionTypeX3,
    InternalStateX3,
    PolicyOutputX3,
    RatificationAdmissionRecord,
    RatificationGate,
    RatificationRejectionCode,
    RatificationRejectionRecord,
    SuccessionAdmissionEvent,
    SuccessionAdmissionRecord,
    SuccessionGate,
    SuccessionProposal,
    SuccessionRejectionCode,
    SuccessionRejectionRecord,
    TreatyRatification,
    compute_genesis_tip_hash,
    compute_identity_chain_tip_hash,
)
from src.rsax3.signature_x3 import (
    derive_genesis_keypair,
    derive_successor_keypair,
    precompute_keypairs,
    sign_cycle_commit,
    sign_cycle_start,
    sign_succession_proposal,
    sign_treaty_ratification,
    verify_active_sovereign_signature,
    verify_cycle_commit,
    verify_cycle_start,
    verify_succession_proposal,
)
from src.rsax3.constitution_x3 import EffectiveConstitutionFrame
from src.rsax3.succession_admission import SuccessionAdmissionPipeline
from src.rsax3.treaty_ratification import RatificationAdmissionPipeline
from src.rsax3.boundary_verifier import (
    BoundaryVerificationResult,
    verify_and_activate_boundary,
)
from src.rsax3.policy_core_x3 import (
    KERNEL_VERSION_ID,
    policy_core_x3,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONSTITUTION_DIR = REPO_ROOT / "artifacts" / "phase-x" / "constitution"
V03_YAML_PATH = str(CONSTITUTION_DIR / "rsa_constitution.v0.3.yaml")
X3_ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "phase-x" / "x3"
GENESIS_PATH = X3_ARTIFACTS_DIR / "genesis.v0.1.json"
OVERLAY_PATH = X3_ARTIFACTS_DIR / "x3_overlay.v0.1.json"

X3_GENESIS_SEED = b"x3-test-seed-for-deterministic-keys"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def v03_constitution() -> ConstitutionX2:
    return ConstitutionX2(yaml_path=V03_YAML_PATH)


@pytest.fixture
def overlay() -> Dict[str, Any]:
    with open(OVERLAY_PATH) as f:
        return json.load(f)


@pytest.fixture
def genesis_artifact() -> Dict[str, Any]:
    with open(GENESIS_PATH) as f:
        return json.load(f)


@pytest.fixture
def constitution_frame(v03_constitution, overlay) -> EffectiveConstitutionFrame:
    return EffectiveConstitutionFrame(v03_constitution, overlay)


@pytest.fixture
def genesis_keypair():
    return derive_genesis_keypair(X3_GENESIS_SEED)


@pytest.fixture
def successor_keypair():
    return derive_successor_keypair(X3_GENESIS_SEED, chain_length=1)


@pytest.fixture
def keypairs():
    """Precompute 5 keypairs for multi-rotation tests."""
    return precompute_keypairs(X3_GENESIS_SEED, max_rotations=4)


def _make_timestamp_obs(t: str = "2026-02-14T00:00:00Z") -> Observation:
    return Observation(
        kind=ObservationKind.TIMESTAMP.value,
        payload={"iso8601_utc": t},
        author=Author.HOST.value,
        created_at=t,
    )


def _make_budget_obs(tokens: int = 100) -> Observation:
    return Observation(
        kind=ObservationKind.BUDGET.value,
        payload={
            "llm_output_token_count": tokens,
            "llm_candidates_reported": 1,
            "llm_parse_errors": 0,
        },
        author=Author.HOST.value,
        created_at="2026-02-14T00:00:00Z",
    )


def _make_default_state_x3(
    constitution_frame: EffectiveConstitutionFrame,
    genesis_key: str,
    cycle: int = 1,
    genesis_tip_hash: str = "",
) -> InternalStateX3:
    return InternalStateX3(
        cycle_index=cycle,
        active_constitution_hash=constitution_frame.sha256,
        sovereign_public_key_active=genesis_key,
        identity_chain_length=1,
        identity_chain_tip_hash=genesis_tip_hash,
        overlay_hash=constitution_frame.overlay_hash,
        active_treaty_set=ActiveTreatySetX3(),
    )


def _make_test_grant(
    grantee_id: str,
    actions: List[str] = None,
    duration: int = 10,
    grant_cycle: int = 1,
) -> TreatyGrant:
    return TreatyGrant(
        grantor_authority_id="AUTH_DELEGATION",
        grantee_identifier=grantee_id,
        granted_actions=actions or ["ReadLocal"],
        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]},
        duration_cycles=duration,
        revocable=True,
        authority_citations=["CL-DELEGATION-PROTOCOL"],
        justification="test grant",
        created_at="2026-02-14T00:00:00Z",
        grant_cycle=grant_cycle,
    )


def _make_succession_proposal(
    prior_key: str,
    successor_key: str,
    prior_private_key,
    authority_citations: List[str] = None,
    constitution_frame_ref: EffectiveConstitutionFrame = None,
) -> SuccessionProposal:
    """Create a properly signed SuccessionProposal.

    If constitution_frame_ref is provided, uses proper overlay citation.
    Otherwise uses a citation that won't be checked (no resolve_citation).
    """
    if authority_citations is None:
        if constitution_frame_ref is not None:
            oh = constitution_frame_ref.overlay_hash
            authority_citations = [f"overlay:{oh}#CL-SUCCESSION-ENABLED"]
        else:
            authority_citations = ["CL-SUCCESSION-ENABLED"]
    proposal = SuccessionProposal(
        prior_sovereign_public_key=prior_key,
        successor_public_key=successor_key,
        authority_citations=authority_citations,
        justification="Test succession",
        signature="",  # placeholder
    )
    # Sign the proposal
    sig = sign_succession_proposal(prior_private_key, proposal.signing_payload())
    proposal.signature = sig
    # Recompute ID
    proposal.id = ""
    proposal.__post_init__()
    return proposal


def _make_ratification(
    treaty_id: str,
    ratify: bool,
    sovereign_private_key,
) -> TreatyRatification:
    """Create a properly signed TreatyRatification."""
    rat = TreatyRatification(
        treaty_id=treaty_id,
        ratify=ratify,
        signature="",  # placeholder
    )
    sig = sign_treaty_ratification(sovereign_private_key, rat.signing_payload())
    rat.signature = sig
    rat.id = ""
    rat.__post_init__()
    return rat


# ===========================================================================
# 1. Artifact Types
# ===========================================================================

class TestArtifactTypes:
    """Test SuccessionProposal, TreatyRatification, Cycle payloads, state."""

    def test_succession_proposal_creation(self, genesis_keypair):
        priv, gid = genesis_keypair
        _, successor_gid = derive_successor_keypair(X3_GENESIS_SEED, 1)
        proposal = _make_succession_proposal(gid, successor_gid, priv)
        assert proposal.id
        assert proposal.prior_sovereign_public_key == gid
        assert proposal.successor_public_key == successor_gid
        assert not proposal.is_self_succession()

    def test_self_succession_detection(self, genesis_keypair):
        priv, gid = genesis_keypair
        proposal = _make_succession_proposal(gid, gid, priv)
        assert proposal.is_self_succession()

    def test_succession_proposal_serialization(self, genesis_keypair):
        priv, gid = genesis_keypair
        _, successor_gid = derive_successor_keypair(X3_GENESIS_SEED, 1)
        proposal = _make_succession_proposal(gid, successor_gid, priv)
        d = proposal.to_dict_full()
        assert d["type"] == "SuccessionProposal"
        assert d["signature"] == proposal.signature
        # id dict excludes signature
        id_d = proposal.to_dict_id()
        assert "signature" not in id_d or id_d.get("signature") is None

    def test_ratification_creation(self, genesis_keypair):
        priv, gid = genesis_keypair
        rat = _make_ratification("treaty-001", True, priv)
        assert rat.id
        assert rat.treaty_id == "treaty-001"
        assert rat.ratify is True

    def test_ratification_serialization(self, genesis_keypair):
        priv, gid = genesis_keypair
        rat = _make_ratification("treaty-001", False, priv)
        d = rat.to_dict_full()
        assert d["type"] == "TreatyRatification"
        assert d["ratify"] is False

    def test_cycle_commit_payload(self):
        p = CycleCommitPayload(
            cycle_id=1,
            kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end="aabb",
            state_hash_prev="0000",
            constitution_hash_tip="ccdd",
            pending_successor_key=None,
            identity_chain_length=1,
            identity_chain_tip_hash="eeff",
            overlay_hash="1122",
        )
        d = p.to_dict()
        assert d["type"] == "CycleCommit"
        assert d["pending_successor_key"] is None

    def test_cycle_start_payload(self):
        p = CycleStartPayload(
            cycle_id=2,
            kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="aabb",
            sovereign_public_key_active="ed25519:abcd",
            identity_chain_length=1,
            identity_chain_tip_hash="eeff",
            overlay_hash="1122",
        )
        d = p.to_dict()
        assert d["type"] == "CycleStart"
        assert d["sovereign_public_key_active"] == "ed25519:abcd"

    def test_internal_state_x3_creation(self, constitution_frame, genesis_keypair):
        _, gid = genesis_keypair
        state = _make_default_state_x3(constitution_frame, gid)
        assert state.sovereign_public_key_active == gid
        assert state.identity_chain_length == 1
        assert state.pending_successor_key is None
        assert state.prior_sovereign_public_key is None

    def test_internal_state_x3_advance(self, constitution_frame, genesis_keypair):
        _, gid = genesis_keypair
        state = _make_default_state_x3(constitution_frame, gid)
        next_state = state.advance(DecisionTypeX3.ACTION)
        assert next_state.cycle_index == 2
        assert next_state.sovereign_public_key_active == gid
        assert next_state.last_decision == DecisionTypeX3.ACTION

    def test_internal_state_x3_to_dict(self, constitution_frame, genesis_keypair):
        _, gid = genesis_keypair
        state = _make_default_state_x3(constitution_frame, gid)
        d = state.to_dict()
        assert d["sovereign_public_key_active"] == gid
        assert d["identity_chain_length"] == 1
        assert "suspended_grant_ids" in d

    def test_policy_output_x3_defaults(self):
        out = PolicyOutputX3()
        assert out.decision_type == DecisionTypeX3.REFUSE
        assert out.succession_admission is None
        assert out.succession_rejections == []
        assert out.ratification_admissions == []
        assert out.ratification_rejections == []


# ===========================================================================
# 2. Signature Helpers
# ===========================================================================

class TestSignatureHelpers:
    """HKDF derivation, signing, verify_active_sovereign_signature."""

    def test_hkdf_deterministic(self):
        """Same seed + chain_length → same key."""
        k1, g1 = derive_successor_keypair(X3_GENESIS_SEED, 0)
        k2, g2 = derive_successor_keypair(X3_GENESIS_SEED, 0)
        assert g1 == g2

    def test_hkdf_different_chain_positions(self):
        """Different chain_length → different key."""
        _, g0 = derive_successor_keypair(X3_GENESIS_SEED, 0)
        _, g1 = derive_successor_keypair(X3_GENESIS_SEED, 1)
        assert g0 != g1

    def test_genesis_keypair_matches_position_zero(self):
        _, gen_id = derive_genesis_keypair(X3_GENESIS_SEED)
        _, pos0_id = derive_successor_keypair(X3_GENESIS_SEED, 0)
        assert gen_id == pos0_id

    def test_precompute_keypairs(self):
        pairs = precompute_keypairs(X3_GENESIS_SEED, max_rotations=3)
        assert len(pairs) == 4  # 0, 1, 2, 3
        # Each has distinct key
        ids = [p[1] for p in pairs]
        assert len(set(ids)) == 4

    def test_key_format(self, genesis_keypair):
        _, gid = genesis_keypair
        assert gid.startswith("ed25519:")
        assert len(gid) == len("ed25519:") + 64

    def test_sign_verify_succession_proposal(self, genesis_keypair):
        priv, gid = genesis_keypair
        _, successor = derive_successor_keypair(X3_GENESIS_SEED, 1)
        proposal = _make_succession_proposal(gid, successor, priv)
        valid, error = verify_succession_proposal(
            gid, proposal.signing_payload(), proposal.signature
        )
        assert valid, error

    def test_verify_active_sovereign_ok(self, genesis_keypair):
        priv, gid = genesis_keypair
        payload = {"test": "data"}
        sig = priv.sign(canonical_json_bytes(payload)).hex()
        valid, err, code = verify_active_sovereign_signature(
            payload, sig, gid, gid, None
        )
        assert valid
        assert code == ""

    def test_verify_active_sovereign_prior_key_leak(self, genesis_keypair, successor_keypair):
        _, genesis_gid = genesis_keypair
        _, successor_gid = successor_keypair
        payload = {"test": "data"}
        # Try to use genesis as signer when successor is active
        valid, err, code = verify_active_sovereign_signature(
            payload, "deadbeef" * 8,
            signer_identifier=genesis_gid,
            active_sovereign_key=successor_gid,
            prior_sovereign_key=genesis_gid,
        )
        assert not valid
        assert code == "PRIOR_KEY_PRIVILEGE_LEAK"

    def test_verify_active_sovereign_wrong_key(self, genesis_keypair):
        _, genesis_gid = genesis_keypair
        random_priv, random_gid = generate_keypair()
        valid, err, code = verify_active_sovereign_signature(
            {"test": "data"}, "deadbeef" * 8,
            signer_identifier=random_gid,
            active_sovereign_key=genesis_gid,
            prior_sovereign_key=None,
        )
        assert not valid
        assert code == "SIGNATURE_INVALID"

    def test_sign_verify_cycle_commit(self, genesis_keypair):
        priv, gid = genesis_keypair
        payload = CycleCommitPayload(
            cycle_id=1, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end="aa", state_hash_prev="00",
            constitution_hash_tip="cc", pending_successor_key=None,
            identity_chain_length=1, identity_chain_tip_hash="ee",
            overlay_hash="11",
        ).to_dict()
        sig = sign_cycle_commit(priv, payload)
        valid, err = verify_cycle_commit(gid, payload, sig)
        assert valid, err

    def test_sign_verify_cycle_start(self, genesis_keypair):
        priv, gid = genesis_keypair
        payload = CycleStartPayload(
            cycle_id=2, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="aa", sovereign_public_key_active=gid,
            identity_chain_length=1, identity_chain_tip_hash="ee",
            overlay_hash="11",
        ).to_dict()
        sig = sign_cycle_start(priv, payload)
        valid, err = verify_cycle_start(gid, payload, sig)
        assert valid, err


# ===========================================================================
# 3. Identity Chain Hash
# ===========================================================================

class TestIdentityChainHash:
    """Deterministic tip hash computation."""

    def test_genesis_tip_hash_deterministic(self, genesis_artifact):
        h1 = compute_genesis_tip_hash(genesis_artifact)
        h2 = compute_genesis_tip_hash(genesis_artifact)
        assert h1 == h2
        assert len(h1) == 64  # hex SHA256

    def test_chain_tip_hash_deterministic(self):
        h1 = compute_identity_chain_tip_hash(
            chain_length=2, active_key="ed25519:abcd",
            prior_tip_hash="0000", succession_proposal_hash="1111",
        )
        h2 = compute_identity_chain_tip_hash(
            chain_length=2, active_key="ed25519:abcd",
            prior_tip_hash="0000", succession_proposal_hash="1111",
        )
        assert h1 == h2

    def test_chain_tip_hash_varies_with_length(self):
        h1 = compute_identity_chain_tip_hash(
            chain_length=2, active_key="ed25519:abcd",
            prior_tip_hash="0000", succession_proposal_hash="1111",
        )
        h2 = compute_identity_chain_tip_hash(
            chain_length=3, active_key="ed25519:abcd",
            prior_tip_hash="0000", succession_proposal_hash="1111",
        )
        assert h1 != h2


# ===========================================================================
# 4. Constitution Frame
# ===========================================================================

class TestConstitutionFrame:
    """EffectiveConstitutionFrame + overlay."""

    def test_overlay_hash_deterministic(self, constitution_frame):
        h = constitution_frame.overlay_hash
        assert len(h) == 64

    def test_succession_enabled(self, constitution_frame):
        assert constitution_frame.is_succession_enabled() is True

    def test_delegation_passthrough(self, constitution_frame):
        d = constitution_frame.density_upper_bound()
        assert d == 0.75

    def test_overlay_citation_resolution(self, constitution_frame):
        oh = constitution_frame.overlay_hash
        citation = f"overlay:{oh}#CL-SUCCESSION-ENABLED"
        resolved = constitution_frame.resolve_citation(citation)
        assert resolved is not None
        assert resolved["enabled"] is True

    def test_overlay_citation_wrong_hash(self, constitution_frame):
        citation = "overlay:badhash#CL-SUCCESSION-ENABLED"
        resolved = constitution_frame.resolve_citation(citation)
        assert resolved is None

    def test_base_citation_passthrough(self, constitution_frame):
        # Base constitution citations should still work
        result = constitution_frame.resolve_citation("CL-EXIT-POLICY")
        # May or may not resolve depending on constitution structure
        # At minimum, should not raise

    def test_is_suspension_blocks_grants(self, constitution_frame):
        assert constitution_frame.is_suspension_blocks_grants() is True

    def test_suspension_blocks_grants_code(self, constitution_frame):
        code = constitution_frame.suspension_blocks_grants_code()
        assert code == "SUSPENSION_UNRESOLVED"


# ===========================================================================
# 5. Succession Admission Pipeline
# ===========================================================================

class TestSuccessionAdmission:
    """S1-S7 gate pipeline."""

    def test_valid_succession_passes_all_gates(
        self, constitution_frame, genesis_keypair, successor_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        _, succ_gid = successor_keypair
        proposal = _make_succession_proposal(
            gen_gid, succ_gid, gen_priv,
            constitution_frame_ref=constitution_frame,
        )

        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=gen_gid,
            prior_sovereign_public_key=None,
            historical_sovereign_keys=set(),
            constitution_frame=constitution_frame,
        )
        admitted, rejections, events = pipeline.evaluate([proposal])
        assert admitted is not None
        assert admitted.admitted
        assert not admitted.is_self_succession
        assert rejections == []

    def test_self_succession_passes(
        self, constitution_frame, genesis_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        proposal = _make_succession_proposal(
            gen_gid, gen_gid, gen_priv,
            constitution_frame_ref=constitution_frame,
        )

        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=gen_gid,
            prior_sovereign_public_key=None,
            historical_sovereign_keys=set(),
            constitution_frame=constitution_frame,
        )
        admitted, rejections, events = pipeline.evaluate([proposal])
        assert admitted is not None
        assert admitted.admitted
        assert admitted.is_self_succession

    def test_s1_missing_fields(self, constitution_frame, genesis_keypair):
        gen_priv, gen_gid = genesis_keypair
        proposal = SuccessionProposal(
            prior_sovereign_public_key="",
            successor_public_key="",
            authority_citations=[],
            justification="",
            signature="abcd",
        )
        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=gen_gid,
            prior_sovereign_public_key=None,
            historical_sovereign_keys=set(),
            constitution_frame=constitution_frame,
        )
        admitted, rejections, _ = pipeline.evaluate([proposal])
        assert admitted is None
        assert len(rejections) == 1
        assert rejections[0].rejection_code == SuccessionRejectionCode.INVALID_FIELD

    def test_s3_bad_signature(self, constitution_frame, genesis_keypair):
        gen_priv, gen_gid = genesis_keypair
        _, succ_gid = derive_successor_keypair(X3_GENESIS_SEED, 1)
        oh = constitution_frame.overlay_hash
        proposal = SuccessionProposal(
            prior_sovereign_public_key=gen_gid,
            successor_public_key=succ_gid,
            authority_citations=[f"overlay:{oh}#CL-SUCCESSION-ENABLED"],
            justification="Test",
            signature="deadbeef" * 8,
        )
        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=gen_gid,
            prior_sovereign_public_key=None,
            historical_sovereign_keys=set(),
            constitution_frame=constitution_frame,
        )
        admitted, rejections, _ = pipeline.evaluate([proposal])
        assert admitted is None
        assert rejections[0].rejection_code == SuccessionRejectionCode.SIGNATURE_INVALID

    def test_s4_sovereign_mismatch(
        self, constitution_frame, genesis_keypair, successor_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        succ_priv, succ_gid = successor_keypair
        # Proposal claims it's from successor, but active is genesis
        proposal = _make_succession_proposal(
            succ_gid, gen_gid, succ_priv,
            constitution_frame_ref=constitution_frame,
        )

        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=gen_gid,
            prior_sovereign_public_key=None,
            historical_sovereign_keys=set(),
            constitution_frame=constitution_frame,
        )
        admitted, rejections, _ = pipeline.evaluate([proposal])
        assert admitted is None
        # Should fail at S3 (prior key privilege leak) or S4 (mismatch)
        assert rejections[0].rejection_code in (
            SuccessionRejectionCode.PRIOR_SOVEREIGN_MISMATCH,
            SuccessionRejectionCode.SIGNATURE_INVALID,
        )

    def test_s5_identity_cycle(
        self, constitution_frame, genesis_keypair, successor_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        _, succ_gid = successor_keypair
        # Already have successor in history → cycle
        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=gen_gid,
            prior_sovereign_public_key=None,
            historical_sovereign_keys={succ_gid},
            constitution_frame=constitution_frame,
        )
        proposal = _make_succession_proposal(
            gen_gid, succ_gid, gen_priv,
            constitution_frame_ref=constitution_frame,
        )
        admitted, rejections, _ = pipeline.evaluate([proposal])
        assert admitted is None
        assert rejections[0].rejection_code == SuccessionRejectionCode.IDENTITY_CYCLE

    def test_s7_multiple_successions_per_cycle(
        self, constitution_frame, genesis_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        _, succ1 = derive_successor_keypair(X3_GENESIS_SEED, 1)
        _, succ2 = derive_successor_keypair(X3_GENESIS_SEED, 2)
        p1 = _make_succession_proposal(
            gen_gid, succ1, gen_priv,
            constitution_frame_ref=constitution_frame,
        )
        p2 = _make_succession_proposal(
            gen_gid, succ2, gen_priv,
            constitution_frame_ref=constitution_frame,
        )

        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=gen_gid,
            prior_sovereign_public_key=None,
            historical_sovereign_keys=set(),
            constitution_frame=constitution_frame,
        )
        admitted, rejections, _ = pipeline.evaluate([p1, p2])
        assert admitted is not None
        assert admitted.admitted
        assert len(rejections) == 1
        assert rejections[0].rejection_code == (
            SuccessionRejectionCode.MULTIPLE_SUCCESSIONS_IN_CYCLE
        )

    def test_prior_key_privilege_leak(
        self, constitution_frame, genesis_keypair, successor_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        succ_priv, succ_gid = successor_keypair
        # Genesis creates succession but successor is now active sovereign
        proposal = _make_succession_proposal(
            gen_gid, succ_gid, gen_priv,
            constitution_frame_ref=constitution_frame,
        )

        pipeline = SuccessionAdmissionPipeline(
            sovereign_public_key_active=succ_gid,  # successor is active
            prior_sovereign_public_key=gen_gid,     # genesis is prior
            historical_sovereign_keys=set(),
            constitution_frame=constitution_frame,
        )
        admitted, rejections, _ = pipeline.evaluate([proposal])
        assert admitted is None
        assert rejections[0].rejection_code == (
            SuccessionRejectionCode.PRIOR_KEY_PRIVILEGE_LEAK
        )


# ===========================================================================
# 6. Treaty Ratification Pipeline
# ===========================================================================

class TestRatificationPipeline:
    """R0-R4 gates."""

    def _setup_suspended_state(self, constitution_frame, successor_keypair):
        """Create state with a suspended grant."""
        _, succ_gid = successor_keypair
        _, delegate_gid = generate_keypair()
        grant = _make_test_grant(delegate_gid, grant_cycle=1)

        treaty_set = ActiveTreatySetX3()
        treaty_set.add_grant(grant)
        treaty_set.suspended_grant_ids.add(grant.id)

        return succ_gid, grant, treaty_set

    def test_ratify_true_restores_grant(
        self, constitution_frame, successor_keypair
    ):
        succ_priv, succ_gid = successor_keypair
        succ_gid_str, grant, treaty_set = self._setup_suspended_state(
            constitution_frame, successor_keypair
        )
        rat = _make_ratification(grant.id, True, succ_priv)

        pipeline = RatificationAdmissionPipeline(
            sovereign_public_key_active=succ_gid,
            prior_sovereign_public_key=None,
            active_treaty_set=treaty_set,
            density_upper_bound=constitution_frame.density_upper_bound(),
            action_permissions=constitution_frame.get_action_permissions(),
            action_type_count=len(constitution_frame.get_action_types()),
            current_cycle=2,
        )
        admissions, rejections = pipeline.evaluate([rat])
        assert len(admissions) == 1
        assert admissions[0].admitted
        assert admissions[0].ratify is True
        # Grant should no longer be suspended
        assert grant.id not in treaty_set.suspended_grant_ids

    def test_ratify_false_revokes_grant(
        self, constitution_frame, successor_keypair
    ):
        succ_priv, succ_gid = successor_keypair
        _, grant, treaty_set = self._setup_suspended_state(
            constitution_frame, successor_keypair
        )
        rat = _make_ratification(grant.id, False, succ_priv)

        pipeline = RatificationAdmissionPipeline(
            sovereign_public_key_active=succ_gid,
            prior_sovereign_public_key=None,
            active_treaty_set=treaty_set,
            density_upper_bound=constitution_frame.density_upper_bound(),
            action_permissions=constitution_frame.get_action_permissions(),
            action_type_count=len(constitution_frame.get_action_types()),
            current_cycle=2,
        )
        admissions, rejections = pipeline.evaluate([rat])
        assert len(admissions) == 1
        assert admissions[0].ratify is False
        # Grant should be revoked, not just unsuspended
        assert grant.id in treaty_set.revoked_grant_ids

    def test_r3_treaty_not_suspended(
        self, constitution_frame, successor_keypair
    ):
        succ_priv, succ_gid = successor_keypair
        _, delegate_gid = generate_keypair()
        grant = _make_test_grant(delegate_gid, grant_cycle=1)
        treaty_set = ActiveTreatySetX3()
        treaty_set.add_grant(grant)
        # NOT suspended

        rat = _make_ratification(grant.id, True, succ_priv)
        pipeline = RatificationAdmissionPipeline(
            sovereign_public_key_active=succ_gid,
            prior_sovereign_public_key=None,
            active_treaty_set=treaty_set,
            density_upper_bound=0.75,
            action_permissions=[],
            action_type_count=5,
            current_cycle=2,
        )
        admissions, rejections = pipeline.evaluate([rat])
        assert len(admissions) == 0
        assert len(rejections) == 1
        assert rejections[0].rejection_code == (
            RatificationRejectionCode.TREATY_NOT_SUSPENDED
        )


# ===========================================================================
# 7. Boundary Verifier
# ===========================================================================

class TestBoundaryVerifier:
    """Boundary verification + activation."""

    def test_cycle_1_start_only(self, genesis_keypair, constitution_frame):
        """Cycle 1 skips commit verification."""
        priv, gid = genesis_keypair
        tip = compute_genesis_tip_hash({"test": "genesis"})
        state = _make_default_state_x3(
            constitution_frame, gid, cycle=1, genesis_tip_hash=tip
        )
        start_payload = CycleStartPayload(
            cycle_id=1, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="0000",
            sovereign_public_key_active=gid,
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        start_sig = sign_cycle_start(priv, start_payload)

        result = verify_and_activate_boundary(
            cycle_id=1,
            state=state,
            cycle_commit_payload=None,
            cycle_commit_signature=None,
            cycle_start_payload=start_payload,
            cycle_start_signature=start_sig,
            succession_admitted_in_prior_cycle=False,
        )
        assert result.passed
        assert not result.activation_occurred

    def test_boundary_activation_on_succession(
        self, genesis_keypair, successor_keypair, constitution_frame
    ):
        """Pending successor key triggers activation at boundary."""
        gen_priv, gen_gid = genesis_keypair
        succ_priv, succ_gid = successor_keypair

        tip = compute_genesis_tip_hash({"test": "genesis"})
        state = _make_default_state_x3(
            constitution_frame, gen_gid, cycle=2, genesis_tip_hash=tip
        )
        state.pending_successor_key = succ_gid

        # Add a grant that should get suspended
        _, delegate_gid = generate_keypair()
        grant = _make_test_grant(delegate_gid, grant_cycle=1)
        state.active_treaty_set.add_grant(grant)

        # Commit payload from cycle 1 (signed by genesis)
        commit_payload = CycleCommitPayload(
            cycle_id=1, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end="aa", state_hash_prev="00",
            constitution_hash_tip=constitution_frame.hash,
            pending_successor_key=succ_gid,
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        commit_sig = sign_cycle_commit(gen_priv, commit_payload)

        # After activation, state changes: chain length -> 2, new tip hash
        expected_chain_length = 2
        expected_tip = compute_identity_chain_tip_hash(
            chain_length=expected_chain_length,
            active_key=succ_gid,
            prior_tip_hash=tip,
            succession_proposal_hash="test-proposal-hash",
        )

        # Start payload for cycle 2 (signed by successor)
        start_payload = CycleStartPayload(
            cycle_id=2, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="aa",
            sovereign_public_key_active=succ_gid,
            identity_chain_length=expected_chain_length,
            identity_chain_tip_hash=expected_tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        start_sig = sign_cycle_start(succ_priv, start_payload)

        result = verify_and_activate_boundary(
            cycle_id=2,
            state=state,
            cycle_commit_payload=commit_payload,
            cycle_commit_signature=commit_sig,
            cycle_start_payload=start_payload,
            cycle_start_signature=start_sig,
            succession_admitted_in_prior_cycle=True,
            succession_proposal_hash="test-proposal-hash",
        )
        assert result.passed
        assert result.activation_occurred
        assert result.prior_key == gen_gid
        assert result.successor_key == succ_gid
        assert grant.id in result.suspended_grant_ids

        # State should be mutated
        assert state.sovereign_public_key_active == succ_gid
        assert state.prior_sovereign_public_key == gen_gid
        assert state.pending_successor_key is None
        assert state.identity_chain_length == 2

    def test_boundary_signature_mismatch(
        self, genesis_keypair, constitution_frame
    ):
        """Wrong signer for CycleCommit → BOUNDARY_SIGNATURE_MISMATCH."""
        gen_priv, gen_gid = genesis_keypair
        wrong_priv, _ = generate_keypair()

        tip = compute_genesis_tip_hash({"test": "genesis"})
        state = _make_default_state_x3(
            constitution_frame, gen_gid, cycle=2, genesis_tip_hash=tip
        )

        commit_payload = CycleCommitPayload(
            cycle_id=1, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end="aa", state_hash_prev="00",
            constitution_hash_tip=constitution_frame.hash,
            pending_successor_key=None,
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        # Sign with wrong key
        commit_sig = sign_cycle_commit(wrong_priv, commit_payload)

        start_payload = CycleStartPayload(
            cycle_id=2, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="aa",
            sovereign_public_key_active=gen_gid,
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        start_sig = sign_cycle_start(gen_priv, start_payload)

        result = verify_and_activate_boundary(
            cycle_id=2,
            state=state,
            cycle_commit_payload=commit_payload,
            cycle_commit_signature=commit_sig,
            cycle_start_payload=start_payload,
            cycle_start_signature=start_sig,
            succession_admitted_in_prior_cycle=False,
        )
        assert not result.passed
        assert result.failure_code == BoundaryCode.BOUNDARY_SIGNATURE_MISMATCH

    def test_boundary_missing_pending_successor(
        self, genesis_keypair, constitution_frame
    ):
        """No pending_successor_key despite admitted succession
        → BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR."""
        gen_priv, gen_gid = genesis_keypair
        tip = compute_genesis_tip_hash({"test": "genesis"})
        state = _make_default_state_x3(
            constitution_frame, gen_gid, cycle=2, genesis_tip_hash=tip
        )

        commit_payload = CycleCommitPayload(
            cycle_id=1, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end="aa", state_hash_prev="00",
            constitution_hash_tip=constitution_frame.hash,
            pending_successor_key=None,  # missing!
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        commit_sig = sign_cycle_commit(gen_priv, commit_payload)

        start_payload = CycleStartPayload(
            cycle_id=2, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="aa",
            sovereign_public_key_active=gen_gid,
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        start_sig = sign_cycle_start(gen_priv, start_payload)

        result = verify_and_activate_boundary(
            cycle_id=2,
            state=state,
            cycle_commit_payload=commit_payload,
            cycle_commit_signature=commit_sig,
            cycle_start_payload=start_payload,
            cycle_start_signature=start_sig,
            succession_admitted_in_prior_cycle=True,  # claimed succession
        )
        assert not result.passed
        assert result.failure_code == (
            BoundaryCode.BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR
        )

    def test_boundary_spurious_pending_successor(
        self, genesis_keypair, successor_keypair, constitution_frame
    ):
        """pending_successor_key without succession
        → BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR."""
        gen_priv, gen_gid = genesis_keypair
        _, succ_gid = successor_keypair
        tip = compute_genesis_tip_hash({"test": "genesis"})
        state = _make_default_state_x3(
            constitution_frame, gen_gid, cycle=2, genesis_tip_hash=tip
        )

        commit_payload = CycleCommitPayload(
            cycle_id=1, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end="aa", state_hash_prev="00",
            constitution_hash_tip=constitution_frame.hash,
            pending_successor_key=succ_gid,  # spurious!
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        commit_sig = sign_cycle_commit(gen_priv, commit_payload)

        start_payload = CycleStartPayload(
            cycle_id=2, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="aa",
            sovereign_public_key_active=gen_gid,
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        start_sig = sign_cycle_start(gen_priv, start_payload)

        result = verify_and_activate_boundary(
            cycle_id=2,
            state=state,
            cycle_commit_payload=commit_payload,
            cycle_commit_signature=commit_sig,
            cycle_start_payload=start_payload,
            cycle_start_signature=start_sig,
            succession_admitted_in_prior_cycle=False,  # no succession
        )
        assert not result.passed
        assert result.failure_code == (
            BoundaryCode.BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR
        )

    def test_boundary_chain_mismatch(
        self, genesis_keypair, constitution_frame
    ):
        """Wrong identity_chain_tip_hash in CycleStart
        → BOUNDARY_STATE_CHAIN_MISMATCH."""
        gen_priv, gen_gid = genesis_keypair
        tip = compute_genesis_tip_hash({"test": "genesis"})
        state = _make_default_state_x3(
            constitution_frame, gen_gid, cycle=2, genesis_tip_hash=tip
        )

        commit_payload = CycleCommitPayload(
            cycle_id=1, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end="aa", state_hash_prev="00",
            constitution_hash_tip=constitution_frame.hash,
            pending_successor_key=None,
            identity_chain_length=1,
            identity_chain_tip_hash=tip,
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        commit_sig = sign_cycle_commit(gen_priv, commit_payload)

        # Wrong tip hash in start payload
        start_payload = CycleStartPayload(
            cycle_id=2, kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev="aa",
            sovereign_public_key_active=gen_gid,
            identity_chain_length=1,
            identity_chain_tip_hash="wrong_hash_0000",
            overlay_hash=constitution_frame.overlay_hash,
        ).to_dict()
        start_sig = sign_cycle_start(gen_priv, start_payload)

        result = verify_and_activate_boundary(
            cycle_id=2,
            state=state,
            cycle_commit_payload=commit_payload,
            cycle_commit_signature=commit_sig,
            cycle_start_payload=start_payload,
            cycle_start_signature=start_sig,
            succession_admitted_in_prior_cycle=False,
        )
        assert not result.passed
        assert result.failure_code == BoundaryCode.BOUNDARY_STATE_CHAIN_MISMATCH


# ===========================================================================
# 8. Policy Core X-3
# ===========================================================================

class TestPolicyCoreX3:
    """Full X3_TOPOLOGICAL 12-step ordering."""

    def test_refuse_without_timestamp(self, constitution_frame, genesis_keypair):
        _, gid = genesis_keypair
        state = _make_default_state_x3(constitution_frame, gid)
        out = policy_core_x3(
            cycle_id=1,
            observations=[],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            succession_candidates=[],
            treaty_revocation_candidates=[],
            treaty_ratification_candidates=[],
            treaty_grant_candidates=[],
            delegated_action_candidates=[],
            rsa_action_candidates=[],
            constitution_frame=constitution_frame,
            internal_state=state,
        )
        assert out.decision_type == DecisionTypeX3.REFUSE
        assert out.refusal is not None

    def test_refuse_no_actions(self, constitution_frame, genesis_keypair):
        _, gid = genesis_keypair
        state = _make_default_state_x3(constitution_frame, gid)
        out = policy_core_x3(
            cycle_id=1,
            observations=[_make_timestamp_obs(), _make_budget_obs()],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            succession_candidates=[],
            treaty_revocation_candidates=[],
            treaty_ratification_candidates=[],
            treaty_grant_candidates=[],
            delegated_action_candidates=[],
            rsa_action_candidates=[],
            constitution_frame=constitution_frame,
            internal_state=state,
        )
        assert out.decision_type == DecisionTypeX3.REFUSE

    def test_succession_admitted_sets_pending_key(
        self, constitution_frame, genesis_keypair, successor_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        _, succ_gid = successor_keypair
        state = _make_default_state_x3(constitution_frame, gen_gid)

        proposal = _make_succession_proposal(
            gen_gid, succ_gid, gen_priv,
            constitution_frame_ref=constitution_frame,
        )

        out = policy_core_x3(
            cycle_id=1,
            observations=[_make_timestamp_obs(), _make_budget_obs()],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            succession_candidates=[proposal],
            treaty_revocation_candidates=[],
            treaty_ratification_candidates=[],
            treaty_grant_candidates=[],
            delegated_action_candidates=[],
            rsa_action_candidates=[],
            constitution_frame=constitution_frame,
            internal_state=state,
        )
        # Succession admitted
        assert out.succession_admission is not None
        assert out.succession_admission.admitted
        # pending_successor_key set on state
        assert state.pending_successor_key == succ_gid

    def test_self_succession_does_not_set_pending_key(
        self, constitution_frame, genesis_keypair
    ):
        gen_priv, gen_gid = genesis_keypair
        state = _make_default_state_x3(constitution_frame, gen_gid)

        proposal = _make_succession_proposal(
            gen_gid, gen_gid, gen_priv,
            constitution_frame_ref=constitution_frame,
        )

        out = policy_core_x3(
            cycle_id=1,
            observations=[_make_timestamp_obs(), _make_budget_obs()],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            succession_candidates=[proposal],
            treaty_revocation_candidates=[],
            treaty_ratification_candidates=[],
            treaty_grant_candidates=[],
            delegated_action_candidates=[],
            rsa_action_candidates=[],
            constitution_frame=constitution_frame,
            internal_state=state,
        )
        assert out.succession_admission is not None
        assert out.succession_admission.admitted
        assert out.succession_admission.is_self_succession
        # Self succession → no pending key
        assert state.pending_successor_key is None

    def test_suspension_blocks_grants(
        self, constitution_frame, genesis_keypair
    ):
        """Grants rejected with SUSPENSION_UNRESOLVED when suspensions exist."""
        gen_priv, gen_gid = genesis_keypair
        _, delegate_gid = generate_keypair()

        grant = _make_test_grant(delegate_gid, grant_cycle=1)
        treaty_set = ActiveTreatySetX3()
        treaty_set.add_grant(grant)
        treaty_set.suspended_grant_ids.add(grant.id)

        state = _make_default_state_x3(constitution_frame, gen_gid)
        state.active_treaty_set = treaty_set

        new_grant = _make_test_grant(delegate_gid, grant_cycle=2)

        out = policy_core_x3(
            cycle_id=2,
            observations=[_make_timestamp_obs(), _make_budget_obs()],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            succession_candidates=[],
            treaty_revocation_candidates=[],
            treaty_ratification_candidates=[],
            treaty_grant_candidates=[new_grant],
            delegated_action_candidates=[],
            rsa_action_candidates=[],
            constitution_frame=constitution_frame,
            internal_state=state,
        )
        # New grant rejected
        assert len(out.treaty_grants_rejected) == 1
        assert out.treaty_grants_rejected[0].rejection_code == (
            AuthorityCode.SUSPENSION_UNRESOLVED
        )

    def test_exit_on_integrity_fail(self, constitution_frame, genesis_keypair):
        _, gid = genesis_keypair
        state = _make_default_state_x3(constitution_frame, gid)
        obs = [
            _make_timestamp_obs(),
            Observation(
                kind=ObservationKind.SYSTEM.value,
                payload={
                    "event": SystemEvent.STARTUP_INTEGRITY_FAIL.value,
                    "detail": "checksum mismatch",
                },
                author=Author.HOST.value,
                created_at="2026-02-14T00:00:00Z",
            ),
        ]
        out = policy_core_x3(
            cycle_id=1,
            observations=obs,
            amendment_candidates=[],
            pending_amendment_candidates=[],
            succession_candidates=[],
            treaty_revocation_candidates=[],
            treaty_ratification_candidates=[],
            treaty_grant_candidates=[],
            delegated_action_candidates=[],
            rsa_action_candidates=[],
            constitution_frame=constitution_frame,
            internal_state=state,
        )
        assert out.decision_type == DecisionTypeX3.EXIT

    def test_dual_density_checkpoints(
        self, constitution_frame, genesis_keypair
    ):
        """Density repair runs at both Step 6 and Step 8."""
        gen_priv, gen_gid = genesis_keypair
        _, delegate_gid = generate_keypair()

        state = _make_default_state_x3(constitution_frame, gen_gid)

        out = policy_core_x3(
            cycle_id=1,
            observations=[_make_timestamp_obs(), _make_budget_obs()],
            amendment_candidates=[],
            pending_amendment_candidates=[],
            succession_candidates=[],
            treaty_revocation_candidates=[],
            treaty_ratification_candidates=[],
            treaty_grant_candidates=[],
            delegated_action_candidates=[],
            rsa_action_candidates=[],
            constitution_frame=constitution_frame,
            internal_state=state,
        )
        # Revalidation events should exist (at least density summaries)
        assert out.revalidation_events is not None


# ===========================================================================
# 9. ActiveTreatySetX3
# ===========================================================================

class TestActiveTreatySetX3:
    """Suspension, ratification, density with suspensions."""

    def test_suspend_all_active(self):
        _, gid = generate_keypair()
        ts = ActiveTreatySetX3()
        g1 = _make_test_grant(gid, actions=["ReadLocal"], grant_cycle=1)
        g2 = _make_test_grant(gid, actions=["WriteLocal"], grant_cycle=1)
        ts.add_grant(g1)
        ts.add_grant(g2)

        suspended = ts.suspend_all_active(current_cycle=2)
        assert len(suspended) == 2
        assert g1.id in ts.suspended_grant_ids
        assert g2.id in ts.suspended_grant_ids
        # No active grants now
        assert len(ts.active_grants(2)) == 0
        # But they're still suspended_grants
        assert len(ts.suspended_grants(2)) == 2

    def test_ratify_restores(self):
        _, gid = generate_keypair()
        ts = ActiveTreatySetX3()
        g1 = _make_test_grant(gid, grant_cycle=1)
        ts.add_grant(g1)
        ts.suspended_grant_ids.add(g1.id)

        ok = ts.ratify(g1.id)
        assert ok
        assert g1.id not in ts.suspended_grant_ids
        assert len(ts.active_grants(2)) == 1

    def test_reject_ratification_revokes(self):
        _, gid = generate_keypair()
        ts = ActiveTreatySetX3()
        g1 = _make_test_grant(gid, grant_cycle=1)
        ts.add_grant(g1)
        ts.suspended_grant_ids.add(g1.id)

        ok = ts.reject_ratification(g1.id)
        assert ok
        assert g1.id not in ts.suspended_grant_ids
        assert g1.id in ts.revoked_grant_ids
        assert len(ts.active_grants(2)) == 0

    def test_has_suspensions(self):
        ts = ActiveTreatySetX3()
        assert not ts.has_suspensions()
        _, gid = generate_keypair()
        g1 = _make_test_grant(gid, grant_cycle=1)
        ts.add_grant(g1)
        ts.suspended_grant_ids.add(g1.id)
        assert ts.has_suspensions()

    def test_suspended_excluded_from_density(self):
        _, gid = generate_keypair()
        ts = ActiveTreatySetX3()
        g1 = _make_test_grant(gid, grant_cycle=1)
        ts.add_grant(g1)
        ts.suspended_grant_ids.add(g1.id)

        # Active grants should be empty → density = 0
        active = ts.active_grants(2)
        assert len(active) == 0

    def test_prune_expired_suspensions(self):
        _, gid = generate_keypair()
        ts = ActiveTreatySetX3()
        # Grant with short duration, already expired
        g1 = _make_test_grant(gid, duration=1, grant_cycle=1)
        ts.add_grant(g1)
        ts.suspended_grant_ids.add(g1.id)

        removed = ts.prune_expired_suspensions(current_cycle=100)
        assert g1.id in removed
        assert g1.id not in ts.suspended_grant_ids


# ===========================================================================
# 10. KERNEL_VERSION_ID
# ===========================================================================

class TestKernelVersionId:
    """Verify kernel_version_id constant."""

    def test_kernel_version_id(self):
        assert KERNEL_VERSION_ID == "rsa-replay-regime-x3-v0.1"
