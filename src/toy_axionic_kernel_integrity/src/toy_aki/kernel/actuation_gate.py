"""
Actuation Gate: ACV verification and certificate issuance (K4, K5, K6).

Enforces:
- K4: ACV temporal ordering (commit < anchor < reveal)
- K5: ACV commitment verification
- K6: Coupling pattern verification
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from toy_aki.common.hashing import hash_json, compute_proposal_hash
from toy_aki.common.errors import (
    InvariantK4ViolationError,
    InvariantK5ViolationError,
    InvariantK6ViolationError,
)
from toy_aki.acv import (
    Commitment,
    Anchor,
    AnchorRegistry,
    CouplingType,
    CouplingWitness,
    generate_anchor,
    verify_commitment_reveal,
    verify_coupling_witness,
    generate_coupling_witness,
)


MAX_DELEGATION_DEPTH = 2  # Maximum allowed delegation depth


@dataclass
class DelegationChainEntry:
    """Entry in a delegation chain."""
    delegator_id: str
    delegatee_id: str
    original_proposal_hash: str
    depth: int


@dataclass
class ActuationCertificate:
    """
    Certificate authorizing an actuation.

    Issued after successful ACV verification.
    """
    certificate_id: str
    proposal_hash: str
    commitment: str
    anchor: str
    nonce: str
    nonce_ref: str
    coupling_spec: dict[str, str]
    witness: dict[str, Any]
    env_digest: str
    request_digest: str
    trace_digest: str
    policy_digest: str
    delegation_chain: list[DelegationChainEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "certificate_id": self.certificate_id,
            "proposal_hash": self.proposal_hash,
            "commitment": self.commitment,
            "anchor": self.anchor,
            "nonce": self.nonce,
            "nonce_ref": self.nonce_ref,
            "coupling_spec": self.coupling_spec,
            "witness": self.witness,
            "env_digest": self.env_digest,
            "request_digest": self.request_digest,
            "trace_digest": self.trace_digest,
            "policy_digest": self.policy_digest,
        }
        if self.delegation_chain:
            result["delegation_chain"] = [
                {
                    "delegator_id": e.delegator_id,
                    "delegatee_id": e.delegatee_id,
                    "original_proposal_hash": e.original_proposal_hash,
                    "depth": e.depth,
                }
                for e in self.delegation_chain
            ]
        return result


class ActuationGate:
    """
    Actuation gate managing ACV verification.

    Enforces K4, K5, K6 invariants.
    """

    def __init__(
        self,
        kernel_secret: str,
        kernel_public_key: str,
        coupling_type: CouplingType = CouplingType.A,
    ):
        """
        Initialize actuation gate.

        Args:
            kernel_secret: Kernel's secret key (for anchor generation)
            kernel_public_key: Kernel's public key (for commitment verification)
            coupling_type: Default coupling pattern to use
        """
        self._kernel_secret = kernel_secret
        self._kernel_public_key = kernel_public_key
        self._coupling_type = coupling_type
        self._anchor_registry = AnchorRegistry()
        self._commitment_store: dict[str, Commitment] = {}
        self._issued_certificates: dict[str, ActuationCertificate] = {}

    @property
    def coupling_type(self) -> CouplingType:
        """Get current coupling type."""
        return self._coupling_type

    def set_coupling_type(self, coupling_type: CouplingType) -> None:
        """Set the coupling type for future operations."""
        self._coupling_type = coupling_type

    def register_commitment(
        self,
        commitment: Commitment,
    ) -> None:
        """
        Register a commitment from an agent.

        Args:
            commitment: The commitment to register
        """
        self._commitment_store[commitment.commitment] = commitment

    def issue_anchor(
        self,
        commitment: str,
        env_digest: str,
        timestamp_ms: int,
    ) -> Anchor:
        """
        Issue an anchor for a commitment.

        Args:
            commitment: The commitment hash
            env_digest: Current environment state digest
            timestamp_ms: Current timestamp

        Returns:
            The issued anchor
        """
        anchor = generate_anchor(
            self._kernel_secret,
            commitment,
            env_digest,
            timestamp_ms,
        )
        self._anchor_registry.register(anchor)
        return anchor

    def verify_k4(
        self,
        commitment: Commitment,
        anchor: Anchor,
        reveal_timestamp_ms: int,
    ) -> tuple[bool, str]:
        """
        Verify K4 invariant: ACV temporal ordering.

        Checks: commit_timestamp < anchor_timestamp < reveal_timestamp

        Returns:
            (passed, detail) tuple
        """
        if commitment.timestamp_ms >= anchor.timestamp_ms:
            return (
                False,
                f"Temporal violation: commit ({commitment.timestamp_ms}) >= anchor ({anchor.timestamp_ms})",
            )

        if anchor.timestamp_ms >= reveal_timestamp_ms:
            return (
                False,
                f"Temporal violation: anchor ({anchor.timestamp_ms}) >= reveal ({reveal_timestamp_ms})",
            )

        return (True, "Temporal ordering verified")

    def verify_k5(
        self,
        proposal: dict[str, Any],
        commitment: Commitment,
        revealed_nonce: str,
    ) -> tuple[bool, str]:
        """
        Verify K5 invariant: ACV commitment verification.

        Checks that the revealed proposal + nonce matches the commitment.

        Returns:
            (passed, detail) tuple
        """
        from toy_aki.acv.verify import verify_commitment_only

        valid = verify_commitment_only(
            proposal,
            commitment.commitment,
            revealed_nonce,
            self._kernel_public_key,
        )

        if valid:
            return (True, "Commitment verification passed")
        else:
            return (False, "Commitment verification failed - proposal may have been modified after commit")

    def verify_k6(
        self,
        witness: CouplingWitness,
        trace_nodes: list[dict[str, Any]],
        anchor: str,
        env_digest: str,
    ) -> tuple[bool, str]:
        """
        Verify K6 invariant: Coupling pattern verification.

        Returns:
            (passed, detail) tuple
        """
        valid = verify_coupling_witness(
            witness,
            trace_nodes,
            anchor,
            env_digest,
        )

        if valid:
            return (True, f"Coupling {witness.coupling_type.value} verification passed")
        else:
            return (False, f"Coupling {witness.coupling_type.value} verification failed")

    def check_delegation_depth(
        self,
        proposal: dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Check if delegation depth is within limits.

        Returns:
            (within_limit, detail) tuple
        """
        delegation_chain = proposal.get("delegation_chain", [])
        depth = len(delegation_chain)

        if depth > MAX_DELEGATION_DEPTH:
            return (
                False,
                f"Delegation depth {depth} exceeds maximum {MAX_DELEGATION_DEPTH}",
            )

        return (True, f"Delegation depth {depth} within limit")

    def verify_and_issue_certificate(
        self,
        proposal: dict[str, Any],
        commitment: Commitment,
        anchor: Anchor,
        revealed_nonce: str,
        trace_nodes: list[dict[str, Any]],
        env_digest: str,
        policy_digest: str,
        reveal_timestamp_ms: int,
    ) -> ActuationCertificate:
        """
        Perform full ACV verification and issue certificate.

        Verifies K4, K5, K6 and issues certificate on success.

        Args:
            proposal: The revealed proposal
            commitment: The original commitment
            anchor: The kernel-issued anchor
            revealed_nonce: The revealed nonce
            trace_nodes: The trace nodes from proposal
            env_digest: Current environment digest
            policy_digest: Current policy digest
            reveal_timestamp_ms: Reveal timestamp

        Returns:
            ActuationCertificate on success

        Raises:
            InvariantK4ViolationError: If temporal ordering fails
            InvariantK5ViolationError: If commitment verification fails
            InvariantK6ViolationError: If coupling verification fails
        """
        # K4: Temporal ordering
        k4_passed, k4_detail = self.verify_k4(
            commitment, anchor, reveal_timestamp_ms
        )
        if not k4_passed:
            raise InvariantK4ViolationError(k4_detail)

        # K5: Commitment verification
        k5_passed, k5_detail = self.verify_k5(
            proposal, commitment, revealed_nonce
        )
        if not k5_passed:
            raise InvariantK5ViolationError(k5_detail)

        # Generate coupling witness
        witness = generate_coupling_witness(
            self._coupling_type,
            trace_nodes,
            anchor.anchor,
            env_digest,
        )

        # K6: Coupling verification
        k6_passed, k6_detail = self.verify_k6(
            witness,
            trace_nodes,
            anchor.anchor,
            env_digest,
        )
        if not k6_passed:
            raise InvariantK6ViolationError(k6_detail)

        # Check delegation depth
        depth_ok, depth_detail = self.check_delegation_depth(proposal)
        if not depth_ok:
            raise InvariantK6ViolationError(depth_detail)  # Use K6 for delegation issues

        # Mark anchor as used
        self._anchor_registry.mark_used(anchor.anchor)

        # Extract digests
        request = proposal.get("request", {})
        trace = proposal.get("trace", {})

        # Build certificate
        certificate = ActuationCertificate(
            certificate_id=str(uuid.uuid4()),
            proposal_hash=compute_proposal_hash(proposal),
            commitment=commitment.commitment,
            anchor=anchor.anchor,
            nonce=revealed_nonce,
            nonce_ref=commitment.nonce_ref,
            coupling_spec={
                "coupling": self._coupling_type.value,
                "version": "0.1.1",
            },
            witness=witness.to_dict(),
            env_digest=env_digest,
            request_digest=hash_json(request),
            trace_digest=trace.get("trace_commit", hash_json(trace)),
            policy_digest=policy_digest,
        )

        # Handle delegation chain
        delegation_chain = proposal.get("delegation_chain", [])
        if delegation_chain:
            certificate.delegation_chain = [
                DelegationChainEntry(
                    delegator_id=e.get("delegator_id", "unknown"),
                    delegatee_id=e.get("delegatee_id", "unknown"),
                    original_proposal_hash=e.get("original_proposal_hash", ""),
                    depth=e.get("depth", i + 1),
                )
                for i, e in enumerate(delegation_chain)
            ]

        # Store certificate
        self._issued_certificates[certificate.certificate_id] = certificate

        return certificate

    def get_certificate(self, certificate_id: str) -> ActuationCertificate | None:
        """Get a previously issued certificate."""
        return self._issued_certificates.get(certificate_id)

    def get_unused_anchors(self) -> list[Anchor]:
        """Get anchors that were issued but never used (potential burial)."""
        return self._anchor_registry.get_unused_anchors()

    def is_anchor_used(self, anchor_hash: str) -> bool:
        """Check if an anchor has been used."""
        return self._anchor_registry.is_used(anchor_hash)

    def clear(self) -> None:
        """Clear all state."""
        self._anchor_registry.clear()
        self._commitment_store.clear()
        self._issued_certificates.clear()
