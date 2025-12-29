"""Token Binding Enforcement Tests.

Verifies that capability tokens are trace-bound:
- Token binding must include matching proposal_hash, trace_hash, scope_hash
- Mismatched bindings must be rejected
- Signature verification
"""

import pytest
from toy_pseudo_axion.common.hashing import hash_json
from toy_pseudo_axion.kernel.capability import (
    CapabilityManager,
    create_capability_scope,
)
from toy_pseudo_axion.kernel.invariants import check_i4_capability_token_binding


@pytest.fixture
def capability_manager():
    """Create a capability manager with test secret."""
    return CapabilityManager(kernel_secret=b"test_secret_key_12345678")


@pytest.fixture
def test_scope():
    """Create a test scope."""
    return create_capability_scope(
        allowed_ops=["move", "pickup"],
        max_calls=10,
        per_ms=60000,
        expiry_ms=300000,
    )


class TestTokenBindingEnforced:
    """Test suite for token binding enforcement."""

    def test_token_binding_includes_required_hashes(self, capability_manager, test_scope):
        """Token binding must include proposal_hash, trace_hash, scope_hash."""
        token = capability_manager.issue_token(
            capability="move",
            scope=test_scope,
            proposal_hash="proposal123",
            trace_hash="trace456",
            justification="test token",
        )

        binding = token["binding"]
        assert "proposal_hash" in binding
        assert "trace_hash" in binding
        assert "scope_hash" in binding
        assert binding["proposal_hash"] == "proposal123"
        assert binding["trace_hash"] == "trace456"

    def test_valid_token_binding_accepted(self, capability_manager, test_scope):
        """Valid token binding must be accepted by I4 check."""
        scope_hash = hash_json(test_scope)

        token = capability_manager.issue_token(
            capability="move",
            scope=test_scope,
            proposal_hash="proposal123",
            trace_hash="trace456",
            justification="test token",
        )

        witness = check_i4_capability_token_binding(
            token=token,
            proposal_hash="proposal123",
            trace_hash="trace456",
            scope_hash=scope_hash,
        )

        assert witness is None

    def test_mismatched_proposal_hash_rejected(self, capability_manager, test_scope):
        """Mismatched proposal_hash must be rejected."""
        scope_hash = hash_json(test_scope)

        token = capability_manager.issue_token(
            capability="move",
            scope=test_scope,
            proposal_hash="proposal123",
            trace_hash="trace456",
            justification="test token",
        )

        witness = check_i4_capability_token_binding(
            token=token,
            proposal_hash="WRONG_PROPOSAL",
            trace_hash="trace456",
            scope_hash=scope_hash,
        )

        assert witness is not None
        assert witness.invariant == "I4_CAPABILITY_TOKEN_BINDING"
        assert "proposal_hash" in witness.message.lower()

    def test_mismatched_trace_hash_rejected(self, capability_manager, test_scope):
        """Mismatched trace_hash must be rejected."""
        scope_hash = hash_json(test_scope)

        token = capability_manager.issue_token(
            capability="move",
            scope=test_scope,
            proposal_hash="proposal123",
            trace_hash="trace456",
            justification="test token",
        )

        witness = check_i4_capability_token_binding(
            token=token,
            proposal_hash="proposal123",
            trace_hash="WRONG_TRACE",
            scope_hash=scope_hash,
        )

        assert witness is not None
        assert "trace_hash" in witness.message.lower()

    def test_mismatched_scope_hash_rejected(self, capability_manager, test_scope):
        """Mismatched scope_hash must be rejected."""
        token = capability_manager.issue_token(
            capability="move",
            scope=test_scope,
            proposal_hash="proposal123",
            trace_hash="trace456",
            justification="test token",
        )

        witness = check_i4_capability_token_binding(
            token=token,
            proposal_hash="proposal123",
            trace_hash="trace456",
            scope_hash="WRONG_SCOPE_HASH",
        )

        assert witness is not None
        assert "scope_hash" in witness.message.lower()

    def test_token_has_signature(self, capability_manager, test_scope):
        """Token must have a signature field."""
        token = capability_manager.issue_token(
            capability="move",
            scope=test_scope,
            proposal_hash="proposal123",
            trace_hash="trace456",
            justification="test token",
        )

        assert "signature" in token
        assert isinstance(token["signature"], str)
        assert len(token["signature"]) > 0

    def test_token_binding_complete(self, capability_manager, test_scope):
        """Token binding must be complete with all required fields."""
        token = capability_manager.issue_token(
            capability="move",
            scope=test_scope,
            proposal_hash="proposal123",
            trace_hash="trace456",
            justification="test token",
        )

        binding = token["binding"]

        # Verify all required fields are present
        assert "proposal_hash" in binding
        assert "trace_hash" in binding
        assert "scope_hash" in binding

        # Verify scope_hash matches actual scope
        expected_scope_hash = hash_json(test_scope)
        assert binding["scope_hash"] == expected_scope_hash
