"""
AKI v0.4.2 Sentinel: External Enforcement Gateway.

Implements:
- Sentinel: External gateway that intercepts all successor actions
- SentinelAttestation: Signed compliance report for renewal
- SentinelViolationType: Types of violations the sentinel can detect

Per spec §5:
- Sentinel is kernel-owned, static infrastructure
- Deterministic instrumentation only
- No optimization, no policy, no goals
- Cannot alter outputs except to halt on violation
- Reports structural telemetry only

Per Q3 binding answer:
- External gateway layer in harness (wrapper around actuation)
- Read access to action candidates, resource counters, call graph
- Authority to halt/signal violation
- Authority to produce HMAC-signed compliance attestations
- Never transforms actions "helpfully" - pass or block only
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, List, Optional, Callable

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.als.working_mind import ResourceEnvelope, InterfaceDeclaration
from toy_aki.als.leases import Lease, LeaseViolation


class SentinelViolationType(Enum):
    """Types of violations the sentinel can detect."""
    # Resource violations
    STEP_LIMIT_EXCEEDED = auto()
    MEMORY_LIMIT_EXCEEDED = auto()
    ACTION_LIMIT_EXCEEDED = auto()
    TOKEN_LIMIT_EXCEEDED = auto()
    EXTERNAL_CALL_LIMIT = auto()
    THREAD_LIMIT_EXCEEDED = auto()
    PROCESS_LIMIT_EXCEEDED = auto()

    # Interface violations
    INVALID_ACTION_TYPE = auto()
    INVALID_OBSERVATION_FIELD = auto()
    ACTION_ARGS_EXCEEDED = auto()
    OBSERVATION_SIZE_EXCEEDED = auto()

    # Access violations
    NETWORK_ACCESS_DENIED = auto()
    FILESYSTEM_READ_DENIED = auto()
    FILESYSTEM_WRITE_DENIED = auto()
    EXTERNAL_CALL_NOT_ALLOWED = auto()

    # Authority violations
    SPAWN_DETECTED = auto()
    DELEGATION_DETECTED = auto()
    SENTINEL_BYPASS_ATTEMPT = auto()

    # Structural violations
    LEASE_EXPIRED = auto()
    ATTESTATION_INVALID = auto()
    ACV_TRACE_MISSING = auto()


@dataclass
class ResourceCounters:
    """
    Resource usage counters maintained by the sentinel.

    These are incremented as the successor executes and
    checked against the lease's resource envelope.
    """
    steps: int = 0
    actions: int = 0
    tokens: int = 0
    external_calls: int = 0
    peak_memory_bytes: int = 0
    threads: int = 1
    processes: int = 1

    # Access flags
    network_accessed: bool = False
    filesystem_read: bool = False
    filesystem_write: bool = False

    # Call tracking
    external_calls_made: List[str] = field(default_factory=list)

    def reset(self) -> None:
        """Reset counters for new epoch."""
        self.steps = 0
        self.actions = 0
        self.tokens = 0
        self.external_calls = 0
        self.peak_memory_bytes = 0
        self.network_accessed = False
        self.filesystem_read = False
        self.filesystem_write = False
        self.external_calls_made.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "steps": self.steps,
            "actions": self.actions,
            "tokens": self.tokens,
            "external_calls": self.external_calls,
            "peak_memory_bytes": self.peak_memory_bytes,
            "threads": self.threads,
            "processes": self.processes,
            "network_accessed": self.network_accessed,
            "filesystem_read": self.filesystem_read,
            "filesystem_write": self.filesystem_write,
            "external_calls_made": self.external_calls_made.copy(),
        }


@dataclass(frozen=True)
class SentinelAttestation:
    """
    Sentinel-signed compliance report for lease renewal.

    Per spec §5.3, renewal attestation includes:
    1. Sentinel-signed compliance report (freshness + lease ID)
    2. Successor liveness ping (nonce challenge response)

    The kernel verifies:
    - Sentinel signature
    - Attestation freshness (step/cycle indexed)
    - Compliance summary within bounds
    - Revocation hooks intact
    """
    # Identity
    attestation_id: str
    sentinel_id: str
    lease_id: str

    # Freshness
    cycle: int
    timestamp_ms: int
    nonce: str

    # Compliance summary
    resources_within_bounds: bool
    interface_compliant: bool
    authority_intact: bool
    revocation_hooks_intact: bool

    # Resource usage snapshot
    resource_usage: Dict[str, Any]

    # Signature (HMAC)
    signature: bytes = b""

    def to_dict_for_signing(self) -> Dict[str, Any]:
        """Get dictionary for signature computation."""
        return {
            "attestation_id": self.attestation_id,
            "sentinel_id": self.sentinel_id,
            "lease_id": self.lease_id,
            "cycle": self.cycle,
            "timestamp_ms": self.timestamp_ms,
            "nonce": self.nonce,
            "resources_within_bounds": self.resources_within_bounds,
            "interface_compliant": self.interface_compliant,
            "authority_intact": self.authority_intact,
            "revocation_hooks_intact": self.revocation_hooks_intact,
            "resource_usage": self.resource_usage,
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.to_dict_for_signing()
        d["signature"] = self.signature.hex()
        return d

    def is_compliant(self) -> bool:
        """Check if attestation indicates full compliance."""
        return (
            self.resources_within_bounds and
            self.interface_compliant and
            self.authority_intact and
            self.revocation_hooks_intact
        )


@dataclass
class SentinelTelemetry:
    """
    Structural telemetry collected by the sentinel.

    Per spec §5.1, the sentinel reports structural telemetry only.
    No semantic interpretation, no scoring.
    """
    # Cycle info
    cycle: int = 0

    # Action counts
    actions_proposed: int = 0
    actions_passed: int = 0
    actions_blocked: int = 0

    # Violation counts
    violations: Dict[str, int] = field(default_factory=dict)

    # Resource peaks
    peak_steps_per_epoch: int = 0
    peak_actions_per_epoch: int = 0
    peak_memory_bytes: int = 0

    # Timing
    total_monitoring_time_ms: int = 0

    def record_violation(self, vtype: SentinelViolationType) -> None:
        """Record a violation."""
        key = vtype.name
        self.violations[key] = self.violations.get(key, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "actions_proposed": self.actions_proposed,
            "actions_passed": self.actions_passed,
            "actions_blocked": self.actions_blocked,
            "violations": self.violations.copy(),
            "peak_steps_per_epoch": self.peak_steps_per_epoch,
            "peak_actions_per_epoch": self.peak_actions_per_epoch,
            "peak_memory_bytes": self.peak_memory_bytes,
            "total_monitoring_time_ms": self.total_monitoring_time_ms,
        }


class Sentinel:
    """
    External enforcement gateway for ALS.

    The sentinel sits between working mind output and actuation gating.
    It has:
    - Read access to action candidates, resource counters, call graph
    - Authority to halt/signal violation
    - Authority to produce signed compliance attestations

    It never transforms actions "helpfully". It either passes or blocks.

    Per spec §5.2, sentinels qualify as non-agentic plumbing:
    - No choice points
    - No actuation authority (except halt)
    - No reward or policy access
    - No ability to reinterpret kernel inputs
    """

    def __init__(
        self,
        sentinel_id: str,
        *,
        on_violation: Optional[Callable[[SentinelViolationType, str], None]] = None,
    ):
        """
        Initialize sentinel.

        Args:
            sentinel_id: Unique identifier for this sentinel
            on_violation: Callback for violations (optional)
        """
        self._sentinel_id = sentinel_id
        self._on_violation = on_violation

        # Current lease being enforced
        self._active_lease: Optional[Lease] = None

        # Resource bounds from lease
        self._resource_envelope: Optional[ResourceEnvelope] = None
        self._interface: Optional[InterfaceDeclaration] = None

        # Counters
        self._counters = ResourceCounters()

        # Telemetry
        self._telemetry = SentinelTelemetry()

        # Current cycle
        self._cycle = 0

        # Halt flag
        self._halted = False
        self._halt_reason: Optional[str] = None

    @property
    def sentinel_id(self) -> str:
        """Get sentinel ID."""
        return self._sentinel_id

    @property
    def is_halted(self) -> bool:
        """Check if sentinel has halted due to violation."""
        return self._halted

    @property
    def halt_reason(self) -> Optional[str]:
        """Get reason for halt if halted."""
        return self._halt_reason

    @property
    def telemetry(self) -> SentinelTelemetry:
        """Get telemetry snapshot."""
        return self._telemetry

    @property
    def counters(self) -> ResourceCounters:
        """Get resource counters."""
        return self._counters

    @property
    def cycle(self) -> int:
        """Get current cycle."""
        return self._cycle

    def bind_lease(self, lease: Lease) -> None:
        """
        Bind a lease for enforcement.

        The sentinel enforces the resource envelope and interface
        constraints from the lease.
        """
        self._active_lease = lease
        self._resource_envelope = lease.lcp.manifest.resources
        self._interface = lease.lcp.manifest.interface
        self._counters.reset()
        self._telemetry.violations.clear()  # Reset violation counts for new lease
        self._halted = False
        self._halt_reason = None

    def unbind_lease(self) -> None:
        """Unbind the current lease."""
        self._active_lease = None
        self._resource_envelope = None
        self._interface = None

    def advance_cycle(self) -> None:
        """Advance to next cycle."""
        self._cycle += 1
        self._telemetry.cycle = self._cycle

    def reset_epoch(self) -> None:
        """Reset counters for new epoch."""
        self._counters.reset()

    def check_action(
        self,
        action: Dict[str, Any],
    ) -> tuple[bool, Optional[SentinelViolationType], Optional[str]]:
        """
        Check if an action is allowed under the current lease.

        Returns (allowed, violation_type, detail).

        This is a pure pass/block decision. No transformation.
        """
        if self._halted:
            return False, None, self._halt_reason

        if self._active_lease is None:
            return False, SentinelViolationType.LEASE_EXPIRED, "No active lease"

        if self._interface is None:
            return False, SentinelViolationType.LEASE_EXPIRED, "No interface bound"

        self._telemetry.actions_proposed += 1

        # Check action type
        action_type = action.get("action_type", "")
        if action_type not in self._interface.action_types:
            self._record_violation(
                SentinelViolationType.INVALID_ACTION_TYPE,
                f"Action type not allowed: {action_type}",
            )
            return False, SentinelViolationType.INVALID_ACTION_TYPE, f"Invalid action type: {action_type}"

        # Check action args
        args = action.get("args", {})
        if len(args) > self._interface.max_action_args:
            self._record_violation(
                SentinelViolationType.ACTION_ARGS_EXCEEDED,
                f"Too many args: {len(args)}",
            )
            return False, SentinelViolationType.ACTION_ARGS_EXCEEDED, f"Too many args: {len(args)}"

        # Check action limit
        if self._resource_envelope and self._counters.actions >= self._resource_envelope.max_actions_per_epoch:
            self._record_violation(
                SentinelViolationType.ACTION_LIMIT_EXCEEDED,
                f"Action limit exceeded: {self._counters.actions}",
            )
            return False, SentinelViolationType.ACTION_LIMIT_EXCEEDED, "Action limit exceeded"

        # Action passes
        self._counters.actions += 1
        self._telemetry.actions_passed += 1
        self._telemetry.peak_actions_per_epoch = max(
            self._telemetry.peak_actions_per_epoch,
            self._counters.actions,
        )

        return True, None, None

    def check_step(self) -> tuple[bool, Optional[SentinelViolationType], Optional[str]]:
        """
        Check if a step is allowed (before execution).

        Returns (allowed, violation_type, detail).
        """
        if self._halted:
            return False, None, self._halt_reason

        if self._resource_envelope is None:
            return True, None, None  # No bounds to check

        # Check step limit
        if self._counters.steps >= self._resource_envelope.max_steps_per_epoch:
            self._record_violation(
                SentinelViolationType.STEP_LIMIT_EXCEEDED,
                f"Step limit exceeded: {self._counters.steps}",
            )
            return False, SentinelViolationType.STEP_LIMIT_EXCEEDED, "Step limit exceeded"

        self._counters.steps += 1
        self._telemetry.peak_steps_per_epoch = max(
            self._telemetry.peak_steps_per_epoch,
            self._counters.steps,
        )

        return True, None, None

    def check_external_call(
        self,
        call_target: str,
    ) -> tuple[bool, Optional[SentinelViolationType], Optional[str]]:
        """
        Check if an external call is allowed.

        Returns (allowed, violation_type, detail).
        """
        if self._halted:
            return False, None, self._halt_reason

        if self._resource_envelope is None:
            return True, None, None

        # Check call limit
        if self._counters.external_calls >= self._resource_envelope.max_external_calls:
            self._record_violation(
                SentinelViolationType.EXTERNAL_CALL_LIMIT,
                f"External call limit exceeded",
            )
            return False, SentinelViolationType.EXTERNAL_CALL_LIMIT, "Call limit exceeded"

        # Check allowlist
        if call_target not in self._resource_envelope.external_call_allowlist:
            self._record_violation(
                SentinelViolationType.EXTERNAL_CALL_NOT_ALLOWED,
                f"Call not in allowlist: {call_target}",
            )
            return False, SentinelViolationType.EXTERNAL_CALL_NOT_ALLOWED, f"Not allowed: {call_target}"

        self._counters.external_calls += 1
        self._counters.external_calls_made.append(call_target)

        return True, None, None

    def check_spawn(self) -> tuple[bool, Optional[SentinelViolationType], Optional[str]]:
        """
        Check if spawning is allowed (always blocked under ALS).

        Returns (allowed, violation_type, detail).
        """
        if self._halted:
            return False, None, self._halt_reason

        # Spawning is always a violation under ALS
        self._record_violation(
            SentinelViolationType.SPAWN_DETECTED,
            "Spawn attempt detected",
        )
        return False, SentinelViolationType.SPAWN_DETECTED, "Spawning not allowed"

    def check_delegation(self) -> tuple[bool, Optional[SentinelViolationType], Optional[str]]:
        """
        Check for delegation attempt (always blocked under ALS).

        Returns (allowed, violation_type, detail).
        """
        if self._halted:
            return False, None, self._halt_reason

        # Delegation is always a violation under ALS
        self._record_violation(
            SentinelViolationType.DELEGATION_DETECTED,
            "Delegation attempt detected",
        )
        return False, SentinelViolationType.DELEGATION_DETECTED, "Delegation not allowed"

    def record_memory_usage(self, bytes_used: int) -> None:
        """Record current memory usage."""
        self._counters.peak_memory_bytes = max(
            self._counters.peak_memory_bytes,
            bytes_used,
        )
        self._telemetry.peak_memory_bytes = max(
            self._telemetry.peak_memory_bytes,
            bytes_used,
        )

        # Check limit
        if self._resource_envelope and bytes_used > self._resource_envelope.max_memory_bytes:
            self._record_violation(
                SentinelViolationType.MEMORY_LIMIT_EXCEEDED,
                f"Memory limit exceeded: {bytes_used}",
            )
            self._halt(f"Memory limit exceeded: {bytes_used}")

    def generate_attestation(self, nonce: str) -> SentinelAttestation:
        """
        Generate a compliance attestation for lease renewal.

        Args:
            nonce: Challenge nonce for freshness

        Returns:
            Signed attestation
        """
        if self._active_lease is None:
            raise ValueError("No active lease to attest")

        # Check compliance
        resources_ok = True
        if self._resource_envelope:
            resources_ok = (
                self._counters.steps <= self._resource_envelope.max_steps_per_epoch and
                self._counters.actions <= self._resource_envelope.max_actions_per_epoch and
                self._counters.peak_memory_bytes <= self._resource_envelope.max_memory_bytes and
                self._counters.external_calls <= self._resource_envelope.max_external_calls
            )

        interface_ok = self._telemetry.violations.get("INVALID_ACTION_TYPE", 0) == 0
        authority_ok = (
            self._telemetry.violations.get("SPAWN_DETECTED", 0) == 0 and
            self._telemetry.violations.get("DELEGATION_DETECTED", 0) == 0
        )
        hooks_ok = not self._halted

        attestation = SentinelAttestation(
            attestation_id=f"att_{self._sentinel_id}_{self._cycle}",
            sentinel_id=self._sentinel_id,
            lease_id=self._active_lease.lease_id,
            cycle=self._cycle,
            timestamp_ms=current_time_ms(),
            nonce=nonce,
            resources_within_bounds=resources_ok,
            interface_compliant=interface_ok,
            authority_intact=authority_ok,
            revocation_hooks_intact=hooks_ok,
            resource_usage=self._counters.to_dict(),
        )

        # Sign attestation
        data = hash_json(attestation.to_dict_for_signing()).encode()
        signature = self._active_lease.sign_for_attestation(data)

        # Create signed attestation
        return SentinelAttestation(
            attestation_id=attestation.attestation_id,
            sentinel_id=attestation.sentinel_id,
            lease_id=attestation.lease_id,
            cycle=attestation.cycle,
            timestamp_ms=attestation.timestamp_ms,
            nonce=attestation.nonce,
            resources_within_bounds=attestation.resources_within_bounds,
            interface_compliant=attestation.interface_compliant,
            authority_intact=attestation.authority_intact,
            revocation_hooks_intact=attestation.revocation_hooks_intact,
            resource_usage=attestation.resource_usage,
            signature=signature,
        )

    def verify_attestation(self, attestation: SentinelAttestation) -> tuple[bool, Optional[str]]:
        """
        Verify an attestation's signature.

        Returns (valid, error_message).
        """
        if self._active_lease is None:
            return False, "No active lease"

        if attestation.sentinel_id != self._sentinel_id:
            return False, "Sentinel ID mismatch"

        if attestation.lease_id != self._active_lease.lease_id:
            return False, "Lease ID mismatch"

        # Verify signature
        data = hash_json(attestation.to_dict_for_signing()).encode()
        if not self._active_lease.verify_attestation(data, attestation.signature):
            return False, "Invalid signature"

        return True, None

    def _record_violation(self, vtype: SentinelViolationType, detail: str) -> None:
        """Record a violation."""
        self._telemetry.record_violation(vtype)
        self._telemetry.actions_blocked += 1

        if self._on_violation:
            self._on_violation(vtype, detail)

    def _halt(self, reason: str) -> None:
        """Halt the sentinel due to critical violation."""
        self._halted = True
        self._halt_reason = reason

        # Revoke the active lease
        if self._active_lease:
            self._active_lease.revoke(
                LeaseViolation.RESOURCE_EXCEEDED,
                reason,
            )


def create_baseline_sentinel() -> Sentinel:
    """Create a baseline sentinel for ALS experiments."""
    return Sentinel(
        sentinel_id="sentinel_baseline_v042",
    )
