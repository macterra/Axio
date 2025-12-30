"""
ACV (Anchor-Commit-Verify) module.

Implements the commit-anchor-reveal protocol for verifying
that agent proposals are genuine and unmodified.
"""

from toy_aki.acv.commit import (
    Commitment,
    generate_nonce,
    generate_nonce_ref,
    compute_commitment,
    create_commitment,
    verify_commitment_format,
)

from toy_aki.acv.anchor import (
    Anchor,
    AnchorRegistry,
    generate_anchor,
    verify_anchor_freshness,
)

from toy_aki.acv.verify import (
    VerificationResult,
    verify_commitment_reveal,
    verify_commitment_only,
)

from toy_aki.acv.coupling import (
    CouplingType,
    CouplingWitness,
    MerkleOpening,
    generate_coupling_witness,
    verify_coupling_witness,
    generate_coupling_a,
    generate_coupling_b,
    generate_coupling_c,
    verify_coupling_a,
    verify_coupling_b,
    verify_coupling_c,
    compute_merkle_root,
    compute_merkle_path,
    verify_merkle_opening,
)

__all__ = [
    # Commit
    "Commitment",
    "generate_nonce",
    "generate_nonce_ref",
    "compute_commitment",
    "create_commitment",
    "verify_commitment_format",
    # Anchor
    "Anchor",
    "AnchorRegistry",
    "generate_anchor",
    "verify_anchor_freshness",
    # Verify
    "VerificationResult",
    "verify_commitment_reveal",
    "verify_commitment_only",
    # Coupling
    "CouplingType",
    "CouplingWitness",
    "MerkleOpening",
    "generate_coupling_witness",
    "verify_coupling_witness",
    "generate_coupling_a",
    "generate_coupling_b",
    "generate_coupling_c",
    "verify_coupling_a",
    "verify_coupling_b",
    "verify_coupling_c",
    "compute_merkle_root",
    "compute_merkle_path",
    "verify_merkle_opening",
]
