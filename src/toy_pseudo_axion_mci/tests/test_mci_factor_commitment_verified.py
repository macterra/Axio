"""MCI Factor Commitment Verification Tests.

Verifies that factor commitments in MCI mode:
- Are correctly computed from factor vectors
- Can be verified against environment state
- Detect mismatched factors
"""

import pytest
from toy_pseudo_axion.interfaces.mci_latent import MCILatentInterface
from toy_pseudo_axion.harness.scenarios import create_scenario


class TestMCIFactorCommitmentVerified:
    """Test suite for MCI factor commitment verification."""

    def test_compute_factors_returns_correct_dimension(self):
        """compute_factors must return K=8 factors."""
        env = create_scenario("basic", seed=42)
        interface = MCILatentInterface()

        factors = interface.compute_factors(env)

        assert len(factors) == 8
        assert interface.factor_dim == 8

    def test_factors_in_valid_range(self):
        """All factors must be in [0, 1]."""
        env = create_scenario("basic", seed=42)
        interface = MCILatentInterface()

        factors = interface.compute_factors(env)

        for i, f in enumerate(factors):
            assert 0.0 <= f <= 1.0, f"Factor {i} = {f} out of range"

    def test_factor_digest_deterministic(self):
        """factor_digest must be deterministic."""
        interface = MCILatentInterface()

        factors = [0.5, 0.1, 0.5, 0.0, 0.5, 1.0, 0.5, 0.2]
        nonce_ref = "test_nonce"

        digest1 = interface.create_factor_digest(factors, nonce_ref)
        digest2 = interface.create_factor_digest(factors, nonce_ref)

        assert digest1 == digest2

    def test_factor_digest_changes_with_factors(self):
        """Different factors must produce different digests."""
        interface = MCILatentInterface()

        factors1 = [0.5, 0.1, 0.5, 0.0, 0.5, 1.0, 0.5, 0.2]
        factors2 = [0.6, 0.1, 0.5, 0.0, 0.5, 1.0, 0.5, 0.2]
        nonce_ref = "test_nonce"

        digest1 = interface.create_factor_digest(factors1, nonce_ref)
        digest2 = interface.create_factor_digest(factors2, nonce_ref)

        assert digest1 != digest2

    def test_factor_digest_changes_with_nonce(self):
        """Different nonces must produce different digests."""
        interface = MCILatentInterface()

        factors = [0.5, 0.1, 0.5, 0.0, 0.5, 1.0, 0.5, 0.2]

        digest1 = interface.create_factor_digest(factors, "nonce1")
        digest2 = interface.create_factor_digest(factors, "nonce2")

        assert digest1 != digest2

    def test_create_factor_commitment(self):
        """create_factor_commitment must return valid snapshot."""
        env = create_scenario("basic", seed=42)
        interface = MCILatentInterface()

        snapshot = interface.create_factor_commitment(env, "snap_1", "nonce_ref")

        assert "snapshot_id" in snapshot
        assert "factor_digest" in snapshot
        assert "dim" in snapshot
        assert "commitment" in snapshot
        assert "nonce_ref" in snapshot

        assert snapshot["dim"] == 8
        assert snapshot["nonce_ref"] == "nonce_ref"

    def test_verify_factor_commitment_valid(self):
        """Valid factor commitment must verify successfully."""
        env = create_scenario("basic", seed=42)
        interface = MCILatentInterface()
        nonce_ref = "test_nonce"

        snapshot = interface.create_factor_commitment(env, "snap_1", nonce_ref)

        is_valid = interface.verify_factor_commitment(env, snapshot, nonce_ref)

        assert is_valid is True

    def test_verify_factor_commitment_wrong_env(self):
        """Commitment from different env must fail verification."""
        env1 = create_scenario("basic", seed=42)
        env2 = create_scenario("hazard", seed=99)
        interface = MCILatentInterface()
        nonce_ref = "test_nonce"

        snapshot = interface.create_factor_commitment(env1, "snap_1", nonce_ref)

        is_valid = interface.verify_factor_commitment(env2, snapshot, nonce_ref)

        assert is_valid is False

    def test_verify_factor_commitment_wrong_nonce(self):
        """Commitment with wrong nonce must fail verification."""
        env = create_scenario("basic", seed=42)
        interface = MCILatentInterface()

        snapshot = interface.create_factor_commitment(env, "snap_1", "correct_nonce")

        is_valid = interface.verify_factor_commitment(env, snapshot, "wrong_nonce")

        assert is_valid is False

    def test_commitment_interface_spec_matches(self):
        """Interface spec in commitment must match interface."""
        interface = MCILatentInterface()
        spec = interface.get_interface_spec()

        assert spec.mode == "mci_latent"
        assert spec.factor_dim == 8
        assert spec.projection_id == "v1_basic_k8"

    def test_factors_same_env_same_factors(self):
        """Same environment must produce same factors."""
        env = create_scenario("basic", seed=42)
        interface = MCILatentInterface()

        factors1 = interface.compute_factors(env)
        factors2 = interface.compute_factors(env)

        assert factors1 == factors2
