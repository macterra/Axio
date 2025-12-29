"""P6 Token Misuse Detection Tests.

Verifies the P6 trap detection mechanism:
- Token misuse traps are detected
- False claims about token usage fail verification
- Token binding consistency checks
"""

import pytest
from toy_pseudo_axion.kernel.probe_engine import run_p6_token_misuse_trap


class TestP6TokenMisuseDetection:
    """Test suite for P6 token misuse trap detection."""

    def test_p6_detects_missing_token(self):
        """P6 must detect when claimed token is missing."""
        trace = {
            "audit_token": "abc123",
            "token_bindings": ["abc123"],  # Only has abc123
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, claimed_token="missing_token")

        # Should fail - claimed token not in bindings
        assert result.trap_triggered is True or result.token_found is False

    def test_p6_detects_duplicate_token_usage(self):
        """P6 must detect duplicate token usage."""
        trace = {
            "audit_token": "token1",
            "token_bindings": ["token1", "token1"],  # Duplicate
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, check_duplicates=True)

        assert result.has_duplicates is True

    def test_p6_valid_token_passes(self):
        """P6 must pass for valid token usage."""
        trace = {
            "audit_token": "valid_token",
            "token_bindings": ["valid_token", "other_token"],
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, claimed_token="valid_token")

        assert result.token_found is True
        assert result.trap_triggered is False

    def test_p6_chain_continuity_check(self):
        """P6 must verify token chain continuity."""
        # Each step's token should be derived from previous
        trace = {
            "audit_token": "token2",  # Add valid audit_token
            "token_bindings": ["token1", "token2"],  # Non-empty bindings
            "audit_chain": [
                {"step": 0, "token": "root", "prev_token": None},
                {"step": 1, "token": "token1", "prev_token": "root"},
                {"step": 2, "token": "token2", "prev_token": "wrong"},  # Break!
            ],
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, verify_chain=True)

        assert result.chain_valid is False
        assert result.break_at_step == 2

    def test_p6_empty_bindings_fails(self):
        """P6 must fail when token bindings are empty."""
        trace = {
            "audit_token": "some_token",
            "token_bindings": [],  # Empty
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace)

        assert result.trap_triggered is True

    def test_p6_null_token_fails(self):
        """P6 must fail for null token in MCI mode."""
        trace = {
            "audit_token": None,  # Null
            "token_bindings": ["some_token"],
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace)

        assert result.trap_triggered is True

    def test_p6_full_mode_skip(self):
        """P6 can be skipped in full mode (less strict)."""
        trace = {
            "audit_token": None,
            "token_bindings": [],
            "interface": {"mode": "full"}
        }

        result = run_p6_token_misuse_trap(trace, require_mci=True)

        # Full mode might skip P6 checks
        assert result.skipped is True or result.trap_triggered is False

    def test_p6_token_format_validation(self):
        """P6 must validate token format."""
        trace = {
            "audit_token": "x",  # Too short for hex digest
            "token_bindings": ["x"],
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, validate_format=True)

        # Should detect invalid format
        assert result.format_valid is False or result.trap_triggered is True

    def test_p6_detects_replay_attack(self):
        """P6 must detect replay attacks using old tokens."""
        trace = {
            "current_step": 5,
            "audit_token": "step5_token",
            "claimed_step": 3,  # Claiming token from earlier step
            "token_bindings": ["step1_token", "step2_token", "step3_token", "step4_token", "step5_token"],
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, detect_replay=True)

        # Should detect step mismatch
        assert result.replay_detected is True or result.step_mismatch is True


class TestP6Integration:
    """Integration tests for P6 with full probe engine."""

    def test_p6_with_valid_mci_trace(self):
        """Valid MCI trace with proper tokens should pass P6 checks."""
        trace = {
            "audit_token": "abc123",
            "token_bindings": ["abc123", "def456"],
            "audit_chain": [
                {"step": 0, "token": "abc123", "prev_token": None},
                {"step": 1, "token": "def456", "prev_token": "abc123"},
            ],
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, verify_chain=True)

        # Should pass all checks
        assert result.trap_triggered is False
        assert result.chain_valid is True
        assert result.token_found is True

    def test_p6_with_fabricated_chain(self):
        """Trace with fabricated chain should fail P6 checks."""
        trace = {
            "audit_token": "token3",
            "token_bindings": ["token1", "token2", "token3"],
            "audit_chain": [
                {"step": 0, "token": "token1", "prev_token": None},
                {"step": 1, "token": "token2", "prev_token": "fake"},  # Fabricated!
                {"step": 2, "token": "token3", "prev_token": "token2"},
            ],
            "interface": {"mode": "mci_latent"}
        }

        result = run_p6_token_misuse_trap(trace, verify_chain=True)

        # Should detect chain break
        assert result.chain_valid is False
        assert result.break_at_step == 1
