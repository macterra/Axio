"""
AKI v0.4.2 Authority Leases and Lease-Compliance Packages.

Implements:
- LeaseCompliancePackage (LCP): Structural selection criteria for endorsement
- Lease: Authority grant with expiration semantics
- LeaseStatus: Current state of a lease
- LeaseViolation: Types of lease constraint violations

Per spec §4:
- Authority expires by default
- Leases contain structural constraints, resource bounds, expiration
- Behavioral/outcome-based clauses are forbidden
- Kernel checks only that LCP is well-formed and enforceable

Per Q2 binding answer:
- Cycle-based renewal (kernel ticks)
- Succession-based budgets (endorsement limits)
"""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, List, Optional

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.als.working_mind import (
    WorkingMindManifest,
    ResourceEnvelope,
    InterfaceDeclaration,
)


class LeaseStatus(Enum):
    """Current status of an authority lease."""
    PENDING = auto()      # Proposed but not yet endorsed
    ACTIVE = auto()       # Currently active and valid
    EXPIRED = auto()      # Expired due to time/cycle limit
    REVOKED = auto()      # Revoked due to violation
    SUPERSEDED = auto()   # Replaced by successor lease


class LeaseViolation(Enum):
    """Types of lease constraint violations per spec §6.2."""
    # Valid reversion triggers
    CONSTRAINT_VIOLATION = auto()       # Lease constraint violated
    RENEWAL_FAILURE = auto()            # Failed to present renewal attestation
    DELEGATION_REINTRODUCTION = auto()  # Delegation authority detected
    ACV_TRACEABILITY_LOSS = auto()      # Lost ACV traceability
    EVALUABILITY_LOSS = auto()          # Evaluability loss per KNS §5.2

    # Resource violations
    RESOURCE_EXCEEDED = auto()          # Resource bound exceeded
    INTERFACE_VIOLATION = auto()        # Interface declaration violated
    SENTINEL_BYPASS = auto()            # Attempted sentinel bypass

    # Structural violations
    SPAWN_WITHOUT_LEASE = auto()        # Sub-agent without identical lease
    REVOCATION_HOOK_TAMPERED = auto()   # Revocation hooks compromised


@dataclass(frozen=True)
class RevocationHook:
    """
    Revocation hook integrity proof.

    Per spec §4.3 LCP requirement #5.
    Authority must expire without renewal.
    """
    hook_id: str
    expiration_cycle: int
    revocation_key_hash: str  # HMAC key hash for verification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hook_id": self.hook_id,
            "expiration_cycle": self.expiration_cycle,
            "revocation_key_hash": self.revocation_key_hash,
        }

    def digest(self) -> str:
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class SentinelCompatibility:
    """
    Sentinel compatibility proof.

    Per spec §4.3 LCP requirement #4.
    Successor must run under kernel-owned sentinel instrumentation.
    """
    sentinel_id: str
    compatibility_version: str
    instrumentation_points: FrozenSet[str]
    monitoring_enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentinel_id": self.sentinel_id,
            "compatibility_version": self.compatibility_version,
            "instrumentation_points": sorted(self.instrumentation_points),
            "monitoring_enabled": self.monitoring_enabled,
        }

    def digest(self) -> str:
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class NoNewAuthorityDeclaration:
    """
    No-new-authority declaration.

    Per spec §4.3 LCP requirement #6.
    No spawning of sub-agents unless under identical lease + sentinel.
    """
    spawn_prohibited: bool = True
    identical_lease_required: bool = True
    identical_sentinel_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spawn_prohibited": self.spawn_prohibited,
            "identical_lease_required": self.identical_lease_required,
            "identical_sentinel_required": self.identical_sentinel_required,
        }

    def digest(self) -> str:
        return hash_json(self.to_dict())


@dataclass(frozen=True)
class LeaseCompliancePackage:
    """
    Lease-Compliance Package (LCP) per spec §4.3.

    Contains all structural criteria for successor endorsement:
    1. Build Commitment (reproducible build hash)
    2. Interface Declaration (exact I/O surface)
    3. Resource Budget Declaration
    4. Sentinel Compatibility Proof
    5. Revocation Hook Integrity Proof
    6. No-New-Authority Declaration

    The kernel checks ONLY that the LCP is:
    - Well-formed
    - Cryptographically bound
    - Enforceable

    No utility, semantics, or behavioral scoring.
    """
    # From working mind manifest
    manifest: WorkingMindManifest

    # Sentinel compatibility
    sentinel_compat: SentinelCompatibility

    # Revocation hook
    revocation_hook: RevocationHook

    # No-new-authority
    no_new_authority: NoNewAuthorityDeclaration

    # Lease timing (per Q2: both cycle-based and succession-based)
    renewal_window_cycles: int = 100  # Must renew within N kernel cycles
    max_successive_renewals: int = 100  # Maximum renewals before requiring re-endorsement
    grace_window_cycles: int = 10  # Grace period for verification latency

    # Metadata
    lcp_id: str = ""
    created_at_ms: int = 0

    def __post_init__(self):
        # Generate LCP ID if not provided
        if not self.lcp_id:
            object.__setattr__(self, "lcp_id", f"lcp_{hash_json(self.to_dict())[:12]}")
        if not self.created_at_ms:
            object.__setattr__(self, "created_at_ms", current_time_ms())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "sentinel_compat": self.sentinel_compat.to_dict(),
            "revocation_hook": self.revocation_hook.to_dict(),
            "no_new_authority": self.no_new_authority.to_dict(),
            "renewal_window_cycles": self.renewal_window_cycles,
            "max_successive_renewals": self.max_successive_renewals,
            "grace_window_cycles": self.grace_window_cycles,
            "lcp_id": self.lcp_id,
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return hash_json(self.to_dict())

    def is_well_formed(self) -> tuple[bool, Optional[str]]:
        """
        Check if LCP is well-formed.

        Returns (valid, error_message).
        Checks structural validity only, not semantics.
        """
        # Check manifest
        if not self.manifest.build_hash:
            return False, "Missing build hash"
        if not self.manifest.interface.action_types:
            return False, "Empty action types"

        # Check sentinel compatibility
        if not self.sentinel_compat.sentinel_id:
            return False, "Missing sentinel ID"
        if not self.sentinel_compat.monitoring_enabled:
            return False, "Monitoring must be enabled"

        # Check revocation hook
        if not self.revocation_hook.hook_id:
            return False, "Missing revocation hook ID"
        if self.revocation_hook.expiration_cycle <= 0:
            return False, "Invalid expiration cycle"

        # Check no-new-authority
        if not self.no_new_authority.spawn_prohibited:
            if not self.no_new_authority.identical_lease_required:
                return False, "Spawn without identical lease prohibited"
            if not self.no_new_authority.identical_sentinel_required:
                return False, "Spawn without identical sentinel prohibited"

        # Check timing
        if self.renewal_window_cycles <= 0:
            return False, "Invalid renewal window"
        if self.max_successive_renewals <= 0:
            return False, "Invalid max renewals"

        return True, None

    def is_enforceable(self) -> tuple[bool, Optional[str]]:
        """
        Check if LCP constraints are enforceable.

        Returns (enforceable, error_message).
        """
        # Resource bounds must be finite and positive
        res = self.manifest.resources
        if res.max_steps_per_epoch <= 0:
            return False, "Invalid step bound"
        if res.max_memory_bytes <= 0:
            return False, "Invalid memory bound"
        if res.max_actions_per_epoch <= 0:
            return False, "Invalid action bound"

        # Revocation must be enforceable
        if not self.revocation_hook.revocation_key_hash:
            return False, "Missing revocation key"

        return True, None


@dataclass
class Lease:
    """
    Authority lease granted to a successor.

    Per spec §4:
    - Authority expires by default
    - Lease enforces structural constraints
    - No behavioral clauses

    Lease is mutable (status changes over time).
    """
    lease_id: str
    lcp: LeaseCompliancePackage
    successor_mind_id: str

    # Status
    status: LeaseStatus = LeaseStatus.PENDING

    # Cycle tracking (per Q2: cycle-based renewal)
    issued_at_cycle: int = 0
    last_renewal_cycle: int = 0
    renewal_count: int = 0
    expiration_cycle: int = 0

    # Violation tracking
    violations: List[LeaseViolation] = field(default_factory=list)
    violation_details: List[str] = field(default_factory=list)

    # HMAC key for attestation verification (kernel-owned)
    _attestation_key: bytes = field(default_factory=lambda: secrets.token_bytes(32))

    def activate(self, current_cycle: int) -> None:
        """Activate the lease at the given cycle."""
        if self.status != LeaseStatus.PENDING:
            raise ValueError(f"Cannot activate lease in status {self.status}")

        self.status = LeaseStatus.ACTIVE
        self.issued_at_cycle = current_cycle
        self.last_renewal_cycle = current_cycle
        self.expiration_cycle = current_cycle + self.lcp.renewal_window_cycles

    def renew(self, current_cycle: int) -> tuple[bool, Optional[str]]:
        """
        Attempt to renew the lease.

        Returns (success, error_message).
        """
        if self.status != LeaseStatus.ACTIVE:
            return False, f"Cannot renew lease in status {self.status}"

        # Check if within renewal window (including grace)
        max_cycle = self.expiration_cycle + self.lcp.grace_window_cycles
        if current_cycle > max_cycle:
            self.status = LeaseStatus.EXPIRED
            return False, "Renewal window expired"

        # Check succession budget
        if self.renewal_count >= self.lcp.max_successive_renewals:
            return False, "Maximum renewals exceeded"

        # Renew
        self.last_renewal_cycle = current_cycle
        self.renewal_count += 1
        self.expiration_cycle = current_cycle + self.lcp.renewal_window_cycles

        return True, None

    def revoke(self, violation: LeaseViolation, detail: str = "") -> None:
        """Revoke the lease due to a violation."""
        self.status = LeaseStatus.REVOKED
        self.violations.append(violation)
        if detail:
            self.violation_details.append(detail)

    def supersede(self) -> None:
        """Mark lease as superseded by a new successor."""
        if self.status == LeaseStatus.ACTIVE:
            self.status = LeaseStatus.SUPERSEDED

    def is_expired(self, current_cycle: int) -> bool:
        """Check if lease has expired."""
        if self.status != LeaseStatus.ACTIVE:
            return True
        return current_cycle > self.expiration_cycle + self.lcp.grace_window_cycles

    def cycles_until_expiration(self, current_cycle: int) -> int:
        """Get cycles remaining until expiration."""
        if self.status != LeaseStatus.ACTIVE:
            return 0
        return max(0, self.expiration_cycle - current_cycle)

    def verify_attestation(self, attestation_data: bytes, signature: bytes) -> bool:
        """
        Verify a sentinel attestation signature.

        The lease holds the HMAC key; attestations must be signed
        with this key to be valid.
        """
        expected = hmac.new(self._attestation_key, attestation_data, "sha256").digest()
        return hmac.compare_digest(expected, signature)

    def sign_for_attestation(self, data: bytes) -> bytes:
        """
        Sign data for attestation (used by sentinel).

        In production, only the sentinel would have access to sign.
        For the toy environment, the lease provides this method.
        """
        return hmac.new(self._attestation_key, data, "sha256").digest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "lcp": self.lcp.to_dict(),
            "successor_mind_id": self.successor_mind_id,
            "status": self.status.name,
            "issued_at_cycle": self.issued_at_cycle,
            "last_renewal_cycle": self.last_renewal_cycle,
            "renewal_count": self.renewal_count,
            "expiration_cycle": self.expiration_cycle,
            "violations": [v.name for v in self.violations],
            "violation_details": self.violation_details,
        }


class LCPValidator:
    """
    Validates Lease-Compliance Packages for endorsement.

    Per spec §4.3, the kernel checks ONLY that the LCP is:
    - Well-formed
    - Cryptographically bound
    - Enforceable

    NO utility, NO semantics, NO behavioral scoring.
    """

    def __init__(self, sentinel_id: str):
        """
        Initialize validator with the expected sentinel ID.

        Args:
            sentinel_id: ID of the kernel-owned sentinel
        """
        self._sentinel_id = sentinel_id

    def validate(self, lcp: LeaseCompliancePackage) -> tuple[bool, Optional[str]]:
        """
        Validate an LCP for endorsement.

        Returns (valid, error_message).

        Checks:
        1. Well-formedness
        2. Sentinel compatibility
        3. Enforceability

        Does NOT check utility or semantics.
        """
        # Check well-formed
        valid, error = lcp.is_well_formed()
        if not valid:
            return False, f"Malformed LCP: {error}"

        # Check sentinel compatibility
        if lcp.sentinel_compat.sentinel_id != self._sentinel_id:
            return False, f"Sentinel mismatch: expected {self._sentinel_id}"

        # Check enforceability
        valid, error = lcp.is_enforceable()
        if not valid:
            return False, f"Unenforceable LCP: {error}"

        return True, None

    def create_lease(
        self,
        lcp: LeaseCompliancePackage,
        successor_mind_id: str,
    ) -> tuple[Optional[Lease], Optional[str]]:
        """
        Create a lease from a validated LCP.

        Returns (lease, error_message).
        """
        valid, error = self.validate(lcp)
        if not valid:
            return None, error

        lease = Lease(
            lease_id=f"lease_{lcp.lcp_id}_{successor_mind_id[:8]}",
            lcp=lcp,
            successor_mind_id=successor_mind_id,
        )

        return lease, None


def create_baseline_lcp(
    manifest: WorkingMindManifest,
    sentinel_id: str,
    renewal_window: int = 100,
) -> LeaseCompliancePackage:
    """
    Create a baseline LCP for a working mind.

    Helper for creating valid LCPs in tests and experiments.
    """
    # Generate revocation key
    revocation_key = secrets.token_bytes(32)
    revocation_key_hash = hash_json({"key": revocation_key.hex()})

    return LeaseCompliancePackage(
        manifest=manifest,
        sentinel_compat=SentinelCompatibility(
            sentinel_id=sentinel_id,
            compatibility_version="0.4.2",
            instrumentation_points=frozenset({
                "action_submit",
                "resource_check",
                "cycle_tick",
            }),
            monitoring_enabled=True,
        ),
        revocation_hook=RevocationHook(
            hook_id=f"hook_{manifest.build_hash[:8]}",
            expiration_cycle=renewal_window * 10,  # 10 renewal periods
            revocation_key_hash=revocation_key_hash,
        ),
        no_new_authority=NoNewAuthorityDeclaration(
            spawn_prohibited=True,
            identical_lease_required=True,
            identical_sentinel_required=True,
        ),
        renewal_window_cycles=renewal_window,
        max_successive_renewals=100,
        grace_window_cycles=10,
    )
