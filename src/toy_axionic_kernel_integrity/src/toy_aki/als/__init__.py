"""
AKI v0.6 — Authority Leases with Semantic Commitments (ALS-C).

This module implements the post-stasis probe: growth via discrete
successor endorsement under a frozen kernel.

Key components:
- WorkingMind: Abstract interface for action-proposing entities
- Lease/LCP: Authority lease semantics and compliance packages
- Sentinel: External enforcement gateway
- Generator: Successor proposal and control templates
- Harness: ALS experiment orchestration
- Commitment: Semantic obligation ledger (v0.6)
- Verifiers: Commitment verification infrastructure (v0.6)

The kernel corridor (ACV, P5, P2', KNS) is imported as a sealed API.
No corridor code is modified.
"""

from toy_aki.als.working_mind import (
    WorkingMind,
    WorkingMindManifest,
    DecisionBoundaryAdapter,
)
from toy_aki.als.leases import (
    LeaseCompliancePackage,
    Lease,
    LeaseStatus,
    LeaseViolation,
)
from toy_aki.als.sentinel import (
    Sentinel,
    SentinelAttestation,
    SentinelViolationType,
)
from toy_aki.als.generator import (
    SuccessorGenerator,
    SuccessorCandidate,
    ControlSuccessorType,
)

# v0.6 Commitment infrastructure
from toy_aki.als.commitment import (
    Commitment,
    CommitmentStatus,
    CommitmentSpec,
    CommitmentLedger,
    CommitmentEvent,
    CommitmentCostRecord,
    COMMITMENT_SPECS,
    create_genesis_set_0,
    MAX_COMMIT_TTL,
    COMMIT_CAP_ALPHA,
)
from toy_aki.als.verifiers import (
    ActionRecord,
    Verifier,
    VRF_EPOCH_ACTION_COUNT,
    VRF_ORDERED_ACTION_PATTERN,
    VRF_ACTION_HAS_PAYLOAD_SHAPE,
    VERIFIERS,
    verify_commitment,
    get_commitment_params,
    GENESIS_COMMITMENT_PARAMS,
)

__all__ = [
    # Working mind
    "WorkingMind",
    "WorkingMindManifest",
    "DecisionBoundaryAdapter",
    # Leases
    "LeaseCompliancePackage",
    "Lease",
    "LeaseStatus",
    "LeaseViolation",
    # Sentinel
    "Sentinel",
    "SentinelAttestation",
    "SentinelViolationType",
    # Generator
    "SuccessorGenerator",
    "SuccessorCandidate",
    "ControlSuccessorType",
    # Commitments (v0.6)
    "Commitment",
    "CommitmentStatus",
    "CommitmentSpec",
    "CommitmentLedger",
    "CommitmentEvent",
    "CommitmentCostRecord",
    "COMMITMENT_SPECS",
    "create_genesis_set_0",
    "MAX_COMMIT_TTL",
    "COMMIT_CAP_ALPHA",
    # Verifiers (v0.6)
    "ActionRecord",
    "Verifier",
    "VRF_EPOCH_ACTION_COUNT",
    "VRF_ORDERED_ACTION_PATTERN",
    "VRF_ACTION_HAS_PAYLOAD_SHAPE",
    "VERIFIERS",
    "verify_commitment",
    "get_commitment_params",
    "GENESIS_COMMITMENT_PARAMS",
]
