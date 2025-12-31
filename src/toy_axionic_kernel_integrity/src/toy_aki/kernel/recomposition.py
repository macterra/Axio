"""
Kernel-Local Recomposition: Parse, reconstruct, and re-bind action payloads.

Implements the core P2' requirement that the kernel must:
1. Parse E's proposal as DATA (not as an authoritative object)
2. Construct a NEW internal action representation
3. Bind K_act_key DIRECTLY to hash(reconstructed_action)

Wrapping external blobs is EXPLICITLY DISALLOWED.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any
from enum import Enum, auto

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.sovereign_authority import (
    ActuationAuthority,
    ActuationBinding,
    RecomposedAction,
    compute_action_hash,
    ActuationAuthorityLeakError,
)
from toy_aki.kernel.watchdog import current_time_ms


class RecompositionError(Exception):
    """Raised when kernel-local recomposition fails."""
    pass


class ProposalParseError(RecompositionError):
    """Raised when proposal parsing fails."""
    pass


class ActionReconstructionError(RecompositionError):
    """Raised when action reconstruction fails."""
    pass


class DelegationAuthorityError(RecompositionError):
    """Raised when delegation authority is detected in proposal."""
    pass


class RecompositionMode(Enum):
    """Recomposition enforcement modes."""
    HARDENED = auto()  # v0.2.a - Full enforcement
    SOFT = auto()      # v0.2.b - Accept ACV-valid without recomposition
    STRICT = auto()    # v0.2.c/d - Hardened + additional stress checks


@dataclass
class ProposalAnalysis:
    """Result of analyzing an external proposal."""
    valid_structure: bool
    action_type: str | None
    action_args: dict[str, Any] | None
    detected_delegation_markers: list[str]
    detected_authority_objects: list[str]
    raw_proposal_hash: str
    error_message: str | None = None


@dataclass
class RecompositionResult:
    """Result of kernel-local recomposition."""
    success: bool
    recomposed_action: RecomposedAction | None
    binding: ActuationBinding | None
    analysis: ProposalAnalysis
    rejection_reason: str | None = None


# Markers that indicate delegation authority patterns
DELEGATION_AUTHORITY_MARKERS = frozenset({
    "actuation_token",
    "authority_token",
    "delegation_authority",
    "precommitted_action",
    "forwarded_commitment",
    "policy_binding",
    "compressed_policy",
    "external_authority",
    "passthrough_action",
})

# Keys that suggest wrapping rather than recomposition
WRAPPING_INDICATORS = frozenset({
    "wrapped_payload",
    "signed_blob",
    "endorsed_object",
    "opaque_container",
    "sealed_action",
    "delegated_execution",
})


class KernelRecomposer:
    """
    Performs kernel-local recomposition of external proposals.

    This is the core enforcement mechanism for P2':
    - External proposals are parsed as DATA
    - Actions are reconstructed from scratch inside the kernel
    - K_act_key binds ONLY to the reconstructed action hash
    - Any delegation authority patterns cause rejection
    """

    def __init__(
        self,
        authority: ActuationAuthority,
        mode: RecompositionMode = RecompositionMode.HARDENED,
        allowed_action_types: frozenset[str] | None = None,
    ):
        """
        Initialize recomposer.

        Args:
            authority: The kernel's K_act_key
            mode: Recomposition enforcement mode
            allowed_action_types: Set of allowed action type names
        """
        self._authority = authority
        self._mode = mode
        self._allowed_action_types = allowed_action_types or frozenset({
            "MOVE_LEFT", "MOVE_RIGHT", "WAIT", "HARVEST", "SPEND", "DELEGATE"
        })
        self._recomposition_count = 0
        self._rejection_count = 0

    @property
    def mode(self) -> RecompositionMode:
        """Get current mode."""
        return self._mode

    def set_mode(self, mode: RecompositionMode) -> None:
        """Set recomposition mode."""
        self._mode = mode

    def analyze_proposal(self, proposal: dict[str, Any]) -> ProposalAnalysis:
        """
        Analyze an external proposal for structure and delegation markers.

        This is step 1 of recomposition: parse proposal as DATA.

        Args:
            proposal: External proposal from E

        Returns:
            ProposalAnalysis with structure validation and marker detection
        """
        delegation_markers: list[str] = []
        authority_objects: list[str] = []

        # Check for delegation authority markers recursively
        self._scan_for_markers(
            proposal,
            delegation_markers,
            authority_objects,
            path="proposal"
        )

        # Extract action from proposal structure
        request = proposal.get("request", {})
        intent = request.get("intent", {})
        action_type = intent.get("action")
        action_args = intent.get("args", {})

        # Validate structure
        valid_structure = (
            isinstance(proposal, dict) and
            isinstance(request, dict) and
            isinstance(intent, dict) and
            isinstance(action_type, str) and
            isinstance(action_args, dict)
        )

        if not valid_structure:
            return ProposalAnalysis(
                valid_structure=False,
                action_type=None,
                action_args=None,
                detected_delegation_markers=delegation_markers,
                detected_authority_objects=authority_objects,
                raw_proposal_hash=hash_json(proposal) if isinstance(proposal, dict) else "invalid",
                error_message="Invalid proposal structure",
            )

        return ProposalAnalysis(
            valid_structure=True,
            action_type=action_type,
            action_args=action_args,
            detected_delegation_markers=delegation_markers,
            detected_authority_objects=authority_objects,
            raw_proposal_hash=hash_json(proposal),
        )

    def _scan_for_markers(
        self,
        obj: Any,
        delegation_markers: list[str],
        authority_objects: list[str],
        path: str,
    ) -> None:
        """Recursively scan object for delegation markers."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check key names
                if key.lower() in DELEGATION_AUTHORITY_MARKERS:
                    delegation_markers.append(f"{path}.{key}")
                if key.lower() in WRAPPING_INDICATORS:
                    authority_objects.append(f"{path}.{key}")

                # Recurse
                self._scan_for_markers(
                    value,
                    delegation_markers,
                    authority_objects,
                    f"{path}.{key}"
                )

        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                self._scan_for_markers(
                    item,
                    delegation_markers,
                    authority_objects,
                    f"{path}[{i}]"
                )

    def reconstruct_action(
        self,
        analysis: ProposalAnalysis,
    ) -> RecomposedAction:
        """
        Reconstruct action payload from analyzed proposal.

        This is step 2 of recomposition: create NEW internal representation.

        The reconstructed action is built from scratch using ONLY:
        - The parsed action type (validated against allowed types)
        - The parsed action args (deep copied, not referenced)

        Args:
            analysis: Analyzed proposal

        Returns:
            RecomposedAction with kernel-constructed payload

        Raises:
            ActionReconstructionError: If reconstruction fails
        """
        if not analysis.valid_structure:
            raise ActionReconstructionError(
                f"Cannot reconstruct from invalid proposal: {analysis.error_message}"
            )

        action_type = analysis.action_type

        # Validate action type
        if action_type not in self._allowed_action_types:
            raise ActionReconstructionError(
                f"Action type '{action_type}' not in allowed set"
            )

        # Deep copy args to ensure no reference to external objects
        action_args = copy.deepcopy(analysis.action_args)

        # Compute action hash from kernel-constructed payload
        action_hash = compute_action_hash(action_type, action_args)

        return RecomposedAction(
            action_type=action_type,
            action_args=action_args,
            action_hash=action_hash,
            source_proposal_hash=analysis.raw_proposal_hash,
            recomposition_timestamp_ms=current_time_ms(),
        )

    def bind_action(
        self,
        action: RecomposedAction,
    ) -> ActuationBinding:
        """
        Bind K_act_key directly to the recomposed action hash.

        This is step 3 of recomposition: bind K_act_key to hash(A).

        Args:
            action: The recomposed action

        Returns:
            ActuationBinding proving kernel participation
        """
        return self._authority.bind_to_action(action.action_hash)

    def recompose(
        self,
        proposal: dict[str, Any],
    ) -> RecompositionResult:
        """
        Perform full kernel-local recomposition.

        This is the main entry point that:
        1. Analyzes the proposal
        2. Checks for delegation authority (rejects if found in HARDENED mode)
        3. Reconstructs the action
        4. Binds K_act_key to the action hash

        Args:
            proposal: External proposal from E

        Returns:
            RecompositionResult with success/failure and artifacts
        """
        # Step 1: Analyze
        analysis = self.analyze_proposal(proposal)

        # In SOFT mode, skip recomposition enforcement
        if self._mode == RecompositionMode.SOFT:
            # Still parse and construct for consistency, but don't reject
            pass
        else:
            # HARDENED and STRICT modes: reject delegation authority
            if analysis.detected_delegation_markers:
                self._rejection_count += 1
                return RecompositionResult(
                    success=False,
                    recomposed_action=None,
                    binding=None,
                    analysis=analysis,
                    rejection_reason=(
                        f"Delegation authority markers detected: "
                        f"{analysis.detected_delegation_markers}"
                    ),
                )

            if analysis.detected_authority_objects:
                self._rejection_count += 1
                return RecompositionResult(
                    success=False,
                    recomposed_action=None,
                    binding=None,
                    analysis=analysis,
                    rejection_reason=(
                        f"Authority/wrapping objects detected: "
                        f"{analysis.detected_authority_objects}"
                    ),
                )

        # Step 2: Validate structure
        if not analysis.valid_structure:
            self._rejection_count += 1
            return RecompositionResult(
                success=False,
                recomposed_action=None,
                binding=None,
                analysis=analysis,
                rejection_reason=f"Invalid proposal structure: {analysis.error_message}",
            )

        # Step 3: Reconstruct
        try:
            action = self.reconstruct_action(analysis)
        except ActionReconstructionError as e:
            self._rejection_count += 1
            return RecompositionResult(
                success=False,
                recomposed_action=None,
                binding=None,
                analysis=analysis,
                rejection_reason=str(e),
            )

        # Step 4: Bind K_act_key
        binding = self.bind_action(action)

        self._recomposition_count += 1

        return RecompositionResult(
            success=True,
            recomposed_action=action,
            binding=binding,
            analysis=analysis,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get recomposition statistics."""
        return {
            "mode": self._mode.name,
            "recomposition_count": self._recomposition_count,
            "rejection_count": self._rejection_count,
        }


def verify_recomposition_integrity(
    recomposed_action: RecomposedAction,
    binding: ActuationBinding,
) -> bool:
    """
    Verify that a binding corresponds to the recomposed action.

    This is a structural check - it verifies that the binding's
    action_hash matches the recomposed action's hash.

    Args:
        recomposed_action: The kernel-recomposed action
        binding: The actuation binding

    Returns:
        True if binding matches action
    """
    return binding.action_hash == recomposed_action.action_hash
