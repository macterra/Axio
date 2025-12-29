"""Interface Mode Enforcement Tests.

Verifies that interface modes are correctly enforced:
- Mode-specific invariants (I6 for MCI modes)
- Correct schema validation per mode
- Interface spec requirements
"""

import pytest
from toy_pseudo_axion.kernel.invariants import check_i6_mci_interface_completeness
from toy_pseudo_axion.interfaces import get_interface
from toy_pseudo_axion.interfaces.base import InterfaceSpec


class TestInterfaceModeEnforcement:
    """Test suite for interface mode enforcement."""

    def test_full_mode_skips_i6(self):
        """Full mode must pass I6 automatically (no MCI requirements)."""
        trace = {
            "interface": {"mode": "full"},
            "trace_version": "0.3",
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is None

    def test_mci_latent_requires_factors(self):
        """mci_latent mode must require factors in trace."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            # Missing 'factors'
            "factor_snapshot": {"snapshot_id": "s1", "factor_digest": "a"*64, "dim": 8, "commitment": "b"*64, "nonce_ref": "n1"},
            "replay_model": {"model_type": "linear_logits", "W": [[0]*8]*7, "b": [0]*7, "actions": ["NOOP"]*7}
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "factors" in witness.message.lower()

    def test_mci_latent_requires_correct_factor_dim(self):
        """mci_latent mode must require factors.length == factor_dim."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            "factors": [0.5] * 5,  # Wrong dimension
            "factor_snapshot": {"snapshot_id": "s1", "factor_digest": "a"*64, "dim": 8, "commitment": "b"*64, "nonce_ref": "n1"},
            "replay_model": {"model_type": "linear_logits", "W": [[0]*8]*7, "b": [0]*7, "actions": ["NOOP"]*7}
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "length" in witness.message.lower() or "8" in witness.message

    def test_mci_latent_requires_factor_snapshot(self):
        """mci_latent mode must require factor_snapshot."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            "factors": [0.5] * 8,
            # Missing 'factor_snapshot'
            "replay_model": {"model_type": "linear_logits", "W": [[0]*8]*7, "b": [0]*7, "actions": ["NOOP"]*7}
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "factor_snapshot" in witness.message.lower()

    def test_mci_latent_requires_replay_model(self):
        """mci_latent mode must require replay_model."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            "factors": [0.5] * 8,
            "factor_snapshot": {"snapshot_id": "s1", "factor_digest": "a"*64, "dim": 8, "commitment": "b"*64, "nonce_ref": "n1"},
            # Missing 'replay_model'
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "replay_model" in witness.message.lower()

    def test_mci_latent_requires_trace_version_03(self):
        """mci_latent mode must require trace_version 0.3."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.2",  # Wrong version
            "factors": [0.5] * 8,
            "factor_snapshot": {"snapshot_id": "s1", "factor_digest": "a"*64, "dim": 8, "commitment": "b"*64, "nonce_ref": "n1"},
            "replay_model": {"model_type": "linear_logits", "W": [[0]*8]*7, "b": [0]*7, "actions": ["NOOP"]*7}
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "0.3" in witness.message

    def test_replay_model_dimension_check(self):
        """replay_model dimensions must match."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            "factors": [0.5] * 8,
            "factor_snapshot": {"snapshot_id": "s1", "factor_digest": "a"*64, "dim": 8, "commitment": "b"*64, "nonce_ref": "n1"},
            "replay_model": {
                "model_type": "linear_logits",
                "W": [[0]*8, [0]*8],  # 2 rows
                "b": [0, 0, 0],  # 3 elements - mismatch!
                "actions": ["A", "B"]
            }
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "dimension" in witness.message.lower() or "mismatch" in witness.message.lower()

    def test_replay_model_row_dimension_check(self):
        """replay_model W rows must match factor_dim."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            "factors": [0.5] * 8,
            "factor_snapshot": {"snapshot_id": "s1", "factor_digest": "a"*64, "dim": 8, "commitment": "b"*64, "nonce_ref": "n1"},
            "replay_model": {
                "model_type": "linear_logits",
                "W": [[0]*5, [0]*5],  # Wrong row length (5 != 8)
                "b": [0, 0],
                "actions": ["A", "B"]
            }
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "8 elements" in witness.message

    def test_factors_must_be_in_range(self):
        """Factors must be in [0, 1]."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            "factors": [0.5, 0.5, 0.5, 1.5, 0.5, 0.5, 0.5, 0.5],  # 1.5 out of range
            "factor_snapshot": {"snapshot_id": "s1", "factor_digest": "a"*64, "dim": 8, "commitment": "b"*64, "nonce_ref": "n1"},
            "replay_model": {"model_type": "linear_logits", "W": [[0]*8]*7, "b": [0]*7, "actions": ["NOOP"]*7}
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is not None
        assert "[0, 1]" in witness.message or "out of range" in witness.message.lower()

    def test_get_interface_returns_correct_type(self):
        """get_interface must return correct interface type."""
        from toy_pseudo_axion.interfaces.mci_latent import MCILatentInterface
        from toy_pseudo_axion.interfaces.mci_minimal import MCIMinimalInterface
        from toy_pseudo_axion.interfaces.full import FullInterface

        full = get_interface("full")
        mci_latent = get_interface("mci_latent")
        mci_minimal = get_interface("mci_minimal")

        assert isinstance(full, FullInterface)
        assert isinstance(mci_latent, MCILatentInterface)
        assert isinstance(mci_minimal, MCIMinimalInterface)

    def test_interface_spec_structure(self):
        """InterfaceSpec must have required fields."""
        spec = InterfaceSpec(mode="mci_latent", factor_dim=8, projection_id="v1_basic_k8")

        assert spec.mode == "mci_latent"
        assert spec.factor_dim == 8
        assert spec.projection_id == "v1_basic_k8"

    def test_valid_mci_trace_passes_i6(self):
        """Valid MCI trace must pass I6."""
        trace = {
            "interface": {"mode": "mci_latent", "factor_dim": 8},
            "trace_version": "0.3",
            "factors": [0.5] * 8,
            "factor_snapshot": {
                "snapshot_id": "s1",
                "factor_digest": "a"*64,
                "dim": 8,
                "commitment": "b"*64,
                "nonce_ref": "n1"
            },
            "replay_model": {
                "model_type": "linear_logits",
                "W": [[0.0]*8 for _ in range(7)],
                "b": [0.0]*7,
                "actions": ["NOOP", "WAIT", "MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W", "PICKUP"]
            }
        }

        witness = check_i6_mci_interface_completeness(trace)

        assert witness is None
