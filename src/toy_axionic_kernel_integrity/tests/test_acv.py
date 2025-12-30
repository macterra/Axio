"""Tests for ACV (Anchor-Commit-Verify) components."""

import pytest
from toy_aki.acv import (
    # Commit
    Commitment,
    generate_nonce,
    compute_commitment,
    create_commitment,
    verify_commitment_format,
    # Anchor
    Anchor,
    AnchorRegistry,
    generate_anchor,
    verify_anchor_freshness,
    # Verify
    verify_commitment_reveal,
    verify_commitment_only,
    # Coupling
    CouplingType,
    CouplingWitness,
    generate_coupling_witness,
    verify_coupling_witness,
    compute_merkle_root,
    compute_merkle_path,
    verify_merkle_opening,
)
from toy_aki.common.hashing import hash_json


class TestCommitment:
    """Tests for commitment generation."""

    def test_generate_nonce(self):
        """Nonce should be 64 hex characters."""
        nonce = generate_nonce()
        assert len(nonce) == 64
        # Should be valid hex
        bytes.fromhex(nonce)

    def test_generate_nonce_unique(self):
        """Each nonce should be unique."""
        nonces = [generate_nonce() for _ in range(100)]
        assert len(set(nonces)) == 100

    def test_compute_commitment_deterministic(self):
        """Same inputs should produce same commitment."""
        proposal = {"action": "MOVE_RIGHT", "tick": 1}
        nonce = "a" * 64
        key = "test_key"

        c1 = compute_commitment(proposal, nonce, key)
        c2 = compute_commitment(proposal, nonce, key)

        assert c1 == c2

    def test_compute_commitment_different_proposals(self):
        """Different proposals should produce different commitments."""
        nonce = "a" * 64
        key = "test_key"

        c1 = compute_commitment({"action": "MOVE_LEFT"}, nonce, key)
        c2 = compute_commitment({"action": "MOVE_RIGHT"}, nonce, key)

        assert c1 != c2

    def test_create_commitment(self):
        """create_commitment should return valid Commitment."""
        proposal = {"action": "MOVE_RIGHT", "tick": 1}
        key = "test_key"

        commitment = create_commitment(proposal, key, 1000)

        assert isinstance(commitment, Commitment)
        assert len(commitment.commitment) == 64
        assert len(commitment.nonce) == 64
        assert commitment.timestamp_ms == 1000

    def test_verify_commitment_format_valid(self):
        """Valid commitment should pass format check."""
        commitment = Commitment(
            commitment="a" * 64,
            nonce="b" * 64,
            nonce_ref="nonce-123",
            proposal_hash="c" * 64,
            timestamp_ms=1000,
        )
        assert verify_commitment_format(commitment) is True

    def test_verify_commitment_format_invalid_nonce(self):
        """Invalid nonce should fail format check."""
        commitment = Commitment(
            commitment="a" * 64,
            nonce="too_short",
            nonce_ref="nonce-123",
            proposal_hash="c" * 64,
            timestamp_ms=1000,
        )
        assert verify_commitment_format(commitment) is False


class TestAnchor:
    """Tests for anchor generation."""

    def test_generate_anchor(self):
        """Anchor generation should work correctly."""
        anchor = generate_anchor(
            kernel_secret="a" * 64,
            commitment="b" * 64,
            env_digest="c" * 64,
            timestamp_ms=1000,
        )

        assert isinstance(anchor, Anchor)
        assert len(anchor.anchor) == 64
        assert anchor.commitment == "b" * 64
        assert anchor.timestamp_ms == 1000

    def test_generate_anchor_deterministic_with_entropy(self):
        """Same entropy should produce same anchor."""
        entropy = b"fixed_entropy___"

        anchor1 = generate_anchor(
            "a" * 64, "b" * 64, "c" * 64, 1000,
            additional_entropy=entropy,
        )
        anchor2 = generate_anchor(
            "a" * 64, "b" * 64, "c" * 64, 1000,
            additional_entropy=entropy,
        )

        assert anchor1.anchor == anchor2.anchor

    def test_verify_anchor_freshness_valid(self):
        """Fresh anchor should pass."""
        anchor = Anchor(
            anchor="a" * 64,
            commitment="b" * 64,
            anchor_id="anchor-1",
            timestamp_ms=1000,
        )
        assert verify_anchor_freshness(anchor, 1500, max_age_ms=1000) is True

    def test_verify_anchor_freshness_stale(self):
        """Stale anchor should fail."""
        anchor = Anchor(
            anchor="a" * 64,
            commitment="b" * 64,
            anchor_id="anchor-1",
            timestamp_ms=1000,
        )
        assert verify_anchor_freshness(anchor, 3000, max_age_ms=1000) is False


class TestAnchorRegistry:
    """Tests for anchor registry."""

    def test_register_and_check(self):
        """Registered anchors should be tracked."""
        registry = AnchorRegistry()
        anchor = Anchor("a" * 64, "b" * 64, "anchor-1", 1000)

        registry.register(anchor)

        assert registry.is_issued(anchor.anchor) is True
        assert registry.is_used(anchor.anchor) is False

    def test_mark_used(self):
        """Marking as used should work."""
        registry = AnchorRegistry()
        anchor = Anchor("a" * 64, "b" * 64, "anchor-1", 1000)
        registry.register(anchor)

        result = registry.mark_used(anchor.anchor)

        assert result is True
        assert registry.is_used(anchor.anchor) is True

    def test_mark_used_twice_returns_false(self):
        """Second use should return False (reuse detected)."""
        registry = AnchorRegistry()
        anchor = Anchor("a" * 64, "b" * 64, "anchor-1", 1000)
        registry.register(anchor)

        registry.mark_used(anchor.anchor)
        result = registry.mark_used(anchor.anchor)

        assert result is False

    def test_get_unused_anchors(self):
        """Should return anchors that were never used."""
        registry = AnchorRegistry()
        anchor1 = Anchor("a" * 64, "b" * 64, "anchor-1", 1000)
        anchor2 = Anchor("c" * 64, "d" * 64, "anchor-2", 1000)

        registry.register(anchor1)
        registry.register(anchor2)
        registry.mark_used(anchor1.anchor)

        unused = registry.get_unused_anchors()
        assert len(unused) == 1
        assert unused[0].anchor == anchor2.anchor


class TestVerification:
    """Tests for commitment verification."""

    def test_verify_commitment_only_valid(self):
        """Valid commitment should verify."""
        proposal = {"action": "MOVE_RIGHT", "tick": 1}
        key = "test_key"
        nonce = "a" * 64

        commitment_hash = compute_commitment(proposal, nonce, key)

        result = verify_commitment_only(proposal, commitment_hash, nonce, key)
        assert result is True

    def test_verify_commitment_only_wrong_proposal(self):
        """Wrong proposal should fail verification."""
        proposal = {"action": "MOVE_RIGHT", "tick": 1}
        wrong_proposal = {"action": "MOVE_LEFT", "tick": 1}
        key = "test_key"
        nonce = "a" * 64

        commitment_hash = compute_commitment(proposal, nonce, key)

        result = verify_commitment_only(wrong_proposal, commitment_hash, nonce, key)
        assert result is False


class TestCoupling:
    """Tests for coupling patterns."""

    def test_compute_merkle_root_single(self):
        """Single node Merkle root should be correct."""
        hashes = ["a" * 64]
        root = compute_merkle_root(hashes)
        assert len(root) == 64

    def test_compute_merkle_root_multiple(self):
        """Multiple node Merkle root should be deterministic."""
        hashes = ["a" * 64, "b" * 64, "c" * 64]
        root1 = compute_merkle_root(hashes)
        root2 = compute_merkle_root(hashes)
        assert root1 == root2

    def test_merkle_path_verification(self):
        """Merkle path should verify correctly."""
        nodes = [
            {"id": "node-1", "type": "observation"},
            {"id": "node-2", "type": "reasoning"},
            {"id": "node-3", "type": "action"},
        ]
        hashes = [hash_json(n) for n in nodes]
        root = compute_merkle_root(hashes)

        for i in range(len(hashes)):
            path = compute_merkle_path(hashes, i)
            from toy_aki.acv.coupling import MerkleOpening
            opening = MerkleOpening(index=i, node_hash=hashes[i], path=path)
            assert verify_merkle_opening(opening, root) is True

    def test_coupling_a_generation_and_verification(self):
        """Coupling A should generate and verify."""
        nodes = [
            {"id": "1", "type": "obs"},
            {"id": "2", "type": "reason"},
            {"id": "3", "type": "action"},
        ]
        anchor = "abcd" * 16

        witness = generate_coupling_witness(CouplingType.A, nodes, anchor)

        assert witness.coupling_type == CouplingType.A
        assert verify_coupling_witness(witness, nodes, anchor) is True

    def test_coupling_b_generation_and_verification(self):
        """Coupling B should generate and verify."""
        nodes = [
            {"id": "1", "type": "obs"},
            {"id": "2", "type": "action"},
        ]
        anchor = "1234" * 16
        env_digest = "5678" * 16

        witness = generate_coupling_witness(CouplingType.B, nodes, anchor, env_digest)

        assert witness.coupling_type == CouplingType.B
        assert verify_coupling_witness(witness, nodes, anchor, env_digest) is True

    def test_coupling_c_generation_and_verification(self):
        """Coupling C should generate and verify."""
        nodes = [
            {"id": "1", "type": "obs"},
            {"id": "2", "type": "reason"},
            {"id": "3", "type": "action"},
        ]
        anchor = "dead" * 16

        witness = generate_coupling_witness(CouplingType.C, nodes, anchor)

        assert witness.coupling_type == CouplingType.C
        assert verify_coupling_witness(witness, nodes, anchor) is True

    def test_coupling_verification_fails_with_wrong_trace(self):
        """Coupling should fail with modified trace."""
        nodes = [{"id": "1", "type": "obs"}]
        anchor = "abcd" * 16

        witness = generate_coupling_witness(CouplingType.A, nodes, anchor)

        wrong_nodes = [{"id": "2", "type": "modified"}]
        assert verify_coupling_witness(witness, wrong_nodes, anchor) is False
