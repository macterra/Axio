"""Capability token management."""

import time
import uuid
from typing import Any, Optional
from dataclasses import dataclass, field

from ..common.hashing import hash_json, compute_token_signature, verify_token_signature
from ..common.errors import TokenValidationError
from .invariants import Witness


@dataclass
class TokenUsage:
    """Tracks token usage for rate limiting."""
    call_count: int = 0
    window_start_ms: int = 0


@dataclass
class CapabilityManager:
    """Manages capability token issuance and verification."""

    kernel_secret: bytes
    _tokens: dict[str, dict] = field(default_factory=dict)
    _usage: dict[str, TokenUsage] = field(default_factory=dict)
    _revoked: set[str] = field(default_factory=set)

    def issue_token(
        self,
        capability: str,
        scope: dict,
        proposal_hash: str,
        trace_hash: str,
        justification: str
    ) -> dict:
        """Issue a new capability token.

        Args:
            capability: The capability being granted
            scope: Scope definition with allowed_ops, rate_limit, expiry_ms
            proposal_hash: Hash of the proposal
            trace_hash: Hash of the trace
            justification: Justification text

        Returns:
            Complete capability token dict
        """
        token_id = str(uuid.uuid4())
        revocation_id = str(uuid.uuid4())
        now_ms = int(time.time() * 1000)
        expiry_ms = scope.get("expiry_ms", 60000)

        scope_hash = hash_json(scope)

        # Build token without signature
        token_data = {
            "token_id": token_id,
            "capability": capability,
            "scope": scope,
            "binding": {
                "proposal_hash": proposal_hash,
                "trace_hash": trace_hash,
                "scope_hash": scope_hash
            },
            "issued_at_ms": now_ms,
            "expires_at_ms": now_ms + expiry_ms,
            "revocation_id": revocation_id
        }

        # Compute signature
        signature = compute_token_signature(self.kernel_secret, token_data)
        token_data["signature"] = signature

        # Store token
        self._tokens[token_id] = token_data
        self._usage[token_id] = TokenUsage(call_count=0, window_start_ms=now_ms)

        return token_data

    def verify_token(
        self,
        token: dict,
        proposal_hash: str,
        trace_hash: str,
        required_op: str
    ) -> Optional[Witness]:
        """Verify a capability token for an operation.

        Args:
            token: The token to verify
            proposal_hash: Expected proposal hash
            trace_hash: Expected trace hash
            required_op: The operation being performed

        Returns:
            Witness if verification fails, None if passes
        """
        token_id = token.get("token_id")
        now_ms = int(time.time() * 1000)

        # Check if token exists
        if token_id not in self._tokens:
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message=f"Unknown token: {token_id}",
                data_hash=hash_json({"token_id": token_id})
            )

        # Check revocation
        if token_id in self._revoked:
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message=f"Token revoked: {token_id}",
                data_hash=hash_json({"token_id": token_id})
            )

        # Verify signature
        token_for_sig = {k: v for k, v in token.items() if k != "signature"}
        if not verify_token_signature(self.kernel_secret, token_for_sig, token.get("signature", "")):
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message="Invalid token signature",
                data_hash=hash_json({"token_id": token_id})
            )

        # Check expiry
        if now_ms > token.get("expires_at_ms", 0):
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message=f"Token expired at {token.get('expires_at_ms')}",
                data_hash=hash_json({"token_id": token_id, "now_ms": now_ms})
            )

        # Check binding
        binding = token.get("binding", {})
        if binding.get("proposal_hash") != proposal_hash:
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message="Token proposal_hash mismatch",
                data_hash=hash_json({
                    "expected": proposal_hash,
                    "actual": binding.get("proposal_hash")
                })
            )

        if binding.get("trace_hash") != trace_hash:
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message="Token trace_hash mismatch",
                data_hash=hash_json({
                    "expected": trace_hash,
                    "actual": binding.get("trace_hash")
                })
            )

        # Check operation is allowed
        scope = token.get("scope", {})
        allowed_ops = scope.get("allowed_ops", [])
        if required_op not in allowed_ops:
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message=f"Operation '{required_op}' not allowed by token",
                data_hash=hash_json({"required_op": required_op, "allowed_ops": allowed_ops})
            )

        # Check rate limit
        usage = self._usage.get(token_id, TokenUsage())
        rate_limit = scope.get("rate_limit", {})
        max_calls = rate_limit.get("max_calls", 100)
        per_ms = rate_limit.get("per_ms", 60000)

        # Reset window if expired
        if now_ms - usage.window_start_ms > per_ms:
            usage = TokenUsage(call_count=0, window_start_ms=now_ms)

        if usage.call_count >= max_calls:
            return Witness(
                invariant="I4_CAPABILITY_TOKEN_BINDING",
                severity="fatal",
                message=f"Rate limit exceeded: {usage.call_count} >= {max_calls}",
                data_hash=hash_json({"token_id": token_id, "calls": usage.call_count})
            )

        # Update usage
        usage.call_count += 1
        self._usage[token_id] = usage

        return None

    def revoke_token(self, token_id: str) -> None:
        """Revoke a token."""
        self._revoked.add(token_id)

    def get_token(self, token_id: str) -> Optional[dict]:
        """Get a token by ID."""
        return self._tokens.get(token_id)


def create_capability_scope(
    allowed_ops: list[str],
    max_calls: int = 100,
    per_ms: int = 60000,
    expiry_ms: int = 300000
) -> dict:
    """Create a capability scope dict.

    Args:
        allowed_ops: List of allowed operations
        max_calls: Max calls in rate limit window
        per_ms: Rate limit window in ms
        expiry_ms: Token expiry in ms

    Returns:
        Scope dict matching capability_scope.json schema
    """
    return {
        "allowed_ops": allowed_ops,
        "rate_limit": {
            "max_calls": max_calls,
            "per_ms": per_ms
        },
        "expiry_ms": expiry_ms
    }


def create_capability_request(
    capability: str,
    scope: dict,
    justification: str
) -> dict:
    """Create a capability request dict.

    Args:
        capability: The capability being requested
        scope: Scope definition
        justification: Justification text

    Returns:
        Request dict matching capability_request.json schema
    """
    return {
        "capability": capability,
        "scope": scope,
        "justification": justification
    }
