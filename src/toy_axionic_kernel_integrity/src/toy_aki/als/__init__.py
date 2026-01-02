"""
AKI v0.4.2 — Authority Leases and Revertible Succession (ALS).

This module implements the post-stasis probe: growth via discrete
successor endorsement under a frozen kernel.

Key components:
- WorkingMind: Abstract interface for action-proposing entities
- Lease/LCP: Authority lease semantics and compliance packages
- Sentinel: External enforcement gateway
- Generator: Successor proposal and control templates
- Harness: ALS experiment orchestration

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
]
