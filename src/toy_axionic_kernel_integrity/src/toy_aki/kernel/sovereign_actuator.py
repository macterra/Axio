"""
Sovereign Actuator: Strengthened admissibility checks for P2'.

Implements actuator-side enforcement:
1. ACV chain verification (inherited from P5)
2. Kernel-originated actuation step verification
3. K_act_key binding verification
4. Delegation authority pattern rejection
5. Wrapping detection and rejection

U.accept(C_act) requires ALL conditions to hold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from enum import Enum, auto

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.sovereign_authority import (
    ActuationAuthority,
    ActuationBinding,
    RecomposedAction,
    compute_action_hash,
)
from toy_aki.kernel.recomposition import (
    RecompositionMode,
    DELEGATION_AUTHORITY_MARKERS,
    WRAPPING_INDICATORS,
)
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.acv import verify_commitment_reveal, Commitment, Anchor


class AdmissibilityError(Exception):
    """Base class for admissibility check failures."""
    pass


class ACVVerificationFailed(AdmissibilityError):
    """ACV chain verification failed."""
    pass


class KernelOriginMissing(AdmissibilityError):
    """No kernel-originated actuation step found."""
    pass


class BindingVerificationFailed(AdmissibilityError):
    """K_act_key binding verification failed."""
    pass


class DelegationAuthorityDetected(AdmissibilityError):
    """Externally authoritative object detected."""
    pass


class WrappingDetected(AdmissibilityError):
    """Wrapping substituted for recomposition."""
    pass


class AdmissibilityCheckType(Enum):
    """Types of admissibility checks."""
    ACV_CHAIN = auto()
    KERNEL_ORIGIN = auto()
    BINDING_VALID = auto()
    NO_DELEGATION_AUTHORITY = auto()
    NO_WRAPPING = auto()


@dataclass
class AdmissibilityCheck:
    """Result of a single admissibility check."""
    check_type: AdmissibilityCheckType
    passed: bool
    detail: str
    timestamp_ms: int = field(default_factory=current_time_ms)


@dataclass
class AdmissibilityResult:
    """Complete result of admissibility evaluation."""
    admissible: bool
    checks: list[AdmissibilityCheck]
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "admissible": self.admissible,
            "checks": [
                {
                    "check_type": c.check_type.name,
                    "passed": c.passed,
                    "detail": c.detail,
                }
                for c in self.checks
            ],
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class ActuationCommitment:
    """
    Complete actuation commitment object.

    When accepted by U, action A executes in Env.
    Carries ACV chain proving causal provenance.
    """
    commitment_id: str
    recomposed_action: RecomposedAction
    binding: ActuationBinding
    acv_chain: dict[str, Any]  # Full ACV provenance
    kernel_id: str
    timestamp_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "commitment_id": self.commitment_id,
            "recomposed_action": self.recomposed_action.to_dict(),
            "binding": self.binding.to_dict(),
            "acv_chain": self.acv_chain,
            "kernel_id": self.kernel_id,
            "timestamp_ms": self.timestamp_ms,
        }


class SovereignActuator:
    """
    Actuator with strengthened P2' admissibility checks.

    Enforces:
    - verify(C_act.ACV_chain) == valid
    - Chain includes kernel-originated actuation step
    - Step binds K_act_key DIRECTLY to action payload
    - No externally authoritative object survives kernel recomposition
    - No delegation authority patterns present

    Failure of ANY condition => inadmissible (reject).
    """

    def __init__(
        self,
        authority: ActuationAuthority,
        mode: RecompositionMode = RecompositionMode.HARDENED,
    ):
        """
        Initialize actuator.

        Args:
            authority: Reference to kernel's K_act_key (for verification)
            mode: Enforcement mode
        """
        self._authority = authority
        self._mode = mode
        self._acceptance_count = 0
        self._rejection_count = 0
        self._check_log: list[AdmissibilityResult] = []

    @property
    def mode(self) -> RecompositionMode:
        """Get current mode."""
        return self._mode

    def set_mode(self, mode: RecompositionMode) -> None:
        """Set enforcement mode."""
        self._mode = mode

    def accept(
        self,
        commitment: ActuationCommitment,
    ) -> AdmissibilityResult:
        """
        Evaluate admissibility of an actuation commitment.

        In SOFT mode (v0.2.b), only ACV is checked.
        In HARDENED/STRICT modes, all checks apply.

        Args:
            commitment: The actuation commitment to evaluate

        Returns:
            AdmissibilityResult with all check results
        """
        checks: list[AdmissibilityCheck] = []

        # Check 1: ACV chain validity
        acv_check = self._check_acv_chain(commitment)
        checks.append(acv_check)

        if self._mode == RecompositionMode.SOFT:
            # In soft mode, only check ACV (baseline failure demonstration)
            if not acv_check.passed:
                result = AdmissibilityResult(
                    admissible=False,
                    checks=checks,
                    rejection_reason=f"ACV verification failed: {acv_check.detail}",
                )
                self._rejection_count += 1
                self._check_log.append(result)
                return result

            # Accept without further checks
            result = AdmissibilityResult(admissible=True, checks=checks)
            self._acceptance_count += 1
            self._check_log.append(result)
            return result

        # HARDENED and STRICT modes: full checks

        # Check 2: Kernel-originated actuation step
        kernel_check = self._check_kernel_origin(commitment)
        checks.append(kernel_check)

        # Check 3: K_act_key binding valid
        binding_check = self._check_binding(commitment)
        checks.append(binding_check)

        # Check 4: No delegation authority patterns
        delegation_check = self._check_no_delegation_authority(commitment)
        checks.append(delegation_check)

        # Check 5: No wrapping
        wrapping_check = self._check_no_wrapping(commitment)
        checks.append(wrapping_check)

        # All checks must pass
        all_passed = all(c.passed for c in checks)

        if all_passed:
            result = AdmissibilityResult(admissible=True, checks=checks)
            self._acceptance_count += 1
        else:
            # Find first failure
            failed = [c for c in checks if not c.passed]
            result = AdmissibilityResult(
                admissible=False,
                checks=checks,
                rejection_reason=f"{failed[0].check_type.name}: {failed[0].detail}",
            )
            self._rejection_count += 1

        self._check_log.append(result)
        return result

    def _check_acv_chain(
        self,
        commitment: ActuationCommitment,
    ) -> AdmissibilityCheck:
        """Check ACV chain validity."""
        acv = commitment.acv_chain

        # Must have required fields
        required = {"commitment", "anchor", "nonce", "proposal_hash"}
        missing = required - set(acv.keys())

        if missing:
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.ACV_CHAIN,
                passed=False,
                detail=f"Missing ACV fields: {missing}",
            )

        # Verify chain structure
        if not acv.get("verified", False):
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.ACV_CHAIN,
                passed=False,
                detail="ACV chain not verified",
            )

        return AdmissibilityCheck(
            check_type=AdmissibilityCheckType.ACV_CHAIN,
            passed=True,
            detail="ACV chain valid",
        )

    def _check_kernel_origin(
        self,
        commitment: ActuationCommitment,
    ) -> AdmissibilityCheck:
        """Check for kernel-originated actuation step."""
        # Binding must exist and reference the kernel
        binding = commitment.binding

        if binding.kernel_id != self._authority._kernel_id:
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.KERNEL_ORIGIN,
                passed=False,
                detail=f"Binding kernel_id mismatch: {binding.kernel_id}",
            )

        # Must have binding index > 0 (indicating actual binding occurred)
        if binding.binding_index < 1:
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.KERNEL_ORIGIN,
                passed=False,
                detail="Invalid binding index",
            )

        return AdmissibilityCheck(
            check_type=AdmissibilityCheckType.KERNEL_ORIGIN,
            passed=True,
            detail="Kernel-originated actuation step verified",
        )

    def _check_binding(
        self,
        commitment: ActuationCommitment,
    ) -> AdmissibilityCheck:
        """Verify K_act_key binding is valid and direct."""
        binding = commitment.binding
        action = commitment.recomposed_action

        # Binding must be to the action hash, not to an opaque blob
        if binding.action_hash != action.action_hash:
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.BINDING_VALID,
                passed=False,
                detail="Binding hash does not match action hash",
            )

        # Verify binding signature (proves K_act_key participation)
        if not self._authority.verify_binding(binding):
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.BINDING_VALID,
                passed=False,
                detail="Binding signature verification failed",
            )

        return AdmissibilityCheck(
            check_type=AdmissibilityCheckType.BINDING_VALID,
            passed=True,
            detail="K_act_key binding directly to action payload verified",
        )

    def _check_no_delegation_authority(
        self,
        commitment: ActuationCommitment,
    ) -> AdmissibilityCheck:
        """Check that no delegation authority patterns are present."""
        # Scan the commitment for delegation markers
        markers = self._scan_for_delegation_markers(commitment.to_dict())

        if markers:
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.NO_DELEGATION_AUTHORITY,
                passed=False,
                detail=f"Delegation authority markers found: {markers}",
            )

        return AdmissibilityCheck(
            check_type=AdmissibilityCheckType.NO_DELEGATION_AUTHORITY,
            passed=True,
            detail="No delegation authority patterns detected",
        )

    def _check_no_wrapping(
        self,
        commitment: ActuationCommitment,
    ) -> AdmissibilityCheck:
        """Check that wrapping did not substitute for recomposition."""
        # The action must have been recomposed (not wrapped)
        action = commitment.recomposed_action

        # Check that action_hash was computed from components
        expected_hash = compute_action_hash(
            action.action_type,
            action.action_args,
        )

        if action.action_hash != expected_hash:
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.NO_WRAPPING,
                passed=False,
                detail="Action hash mismatch - possible wrapping",
            )

        # Scan for wrapping indicators
        wrapping = self._scan_for_wrapping_indicators(commitment.to_dict())

        if wrapping:
            return AdmissibilityCheck(
                check_type=AdmissibilityCheckType.NO_WRAPPING,
                passed=False,
                detail=f"Wrapping indicators found: {wrapping}",
            )

        return AdmissibilityCheck(
            check_type=AdmissibilityCheckType.NO_WRAPPING,
            passed=True,
            detail="No wrapping detected - action was recomposed",
        )

    def _scan_for_delegation_markers(
        self,
        obj: Any,
        path: str = "root",
    ) -> list[str]:
        """Recursively scan for delegation markers."""
        markers = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() in DELEGATION_AUTHORITY_MARKERS:
                    markers.append(f"{path}.{key}")
                markers.extend(
                    self._scan_for_delegation_markers(value, f"{path}.{key}")
                )
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                markers.extend(
                    self._scan_for_delegation_markers(item, f"{path}[{i}]")
                )

        return markers

    def _scan_for_wrapping_indicators(
        self,
        obj: Any,
        path: str = "root",
    ) -> list[str]:
        """Recursively scan for wrapping indicators."""
        indicators = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.lower() in WRAPPING_INDICATORS:
                    indicators.append(f"{path}.{key}")
                indicators.extend(
                    self._scan_for_wrapping_indicators(value, f"{path}.{key}")
                )
        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                indicators.extend(
                    self._scan_for_wrapping_indicators(item, f"{path}[{i}]")
                )

        return indicators

    def get_stats(self) -> dict[str, Any]:
        """Get actuator statistics."""
        return {
            "mode": self._mode.name,
            "acceptance_count": self._acceptance_count,
            "rejection_count": self._rejection_count,
            "check_log_size": len(self._check_log),
        }

    def get_check_log(self) -> list[dict[str, Any]]:
        """Get log of all admissibility checks."""
        return [r.to_dict() for r in self._check_log]

    def clear_log(self) -> None:
        """Clear the check log."""
        self._check_log.clear()
