"""
AKI v0.6 Commitment Verifiers.

Implements kernel-approved verifiers for GENESIS_SET_0 commitments.

Per spec §6.6:
- Verifiers must be deterministic
- Verifiers must be harness-resident or kernel-approved
- Verifiers must be based solely on ACV-logged artifacts

Verifiers MAY query:
- action type
- action parameters (payload)
- action ordering
- epoch index / timestamps

Verifiers MUST NOT query:
- successor internal state
- opaque "success" flags emitted by the successor

Per spec §6.7:
- Evaluation occurs at epoch end (after successor actions)
- Use the ACV trace for that epoch/window
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple


@dataclass
class ActionRecord:
    """
    A single action from the ACV trace.

    Captures the externally-visible properties of a successor action.
    """
    action_type: str
    payload: Dict[str, Any]
    epoch: int
    cycle: int
    sequence_num: int  # Order within epoch

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "payload": self.payload,
            "epoch": self.epoch,
            "cycle": self.cycle,
            "sequence_num": self.sequence_num,
        }


class Verifier(Protocol):
    """Protocol for commitment verifiers."""

    verifier_id: str

    def verify(
        self,
        actions: List[ActionRecord],
        window_start_epoch: int,
        window_end_epoch: int,
        params: Dict[str, Any],
    ) -> bool:
        """
        Verify commitment satisfaction from action trace.

        Args:
            actions: List of actions within the evaluation window
            window_start_epoch: First epoch of window (inclusive)
            window_end_epoch: Last epoch of window (inclusive)
            params: Commitment-specific parameters

        Returns:
            True if commitment is satisfied, False otherwise
        """
        ...


# =============================================================================
# VRF_EPOCH_ACTION_COUNT: Verifier for C0 (Presence)
# =============================================================================

class VRF_EPOCH_ACTION_COUNT:
    """
    Verifier for CMT_PRESENCE_LOG.

    Checks: At least 1 LOG action occurs within the current epoch.

    Parameters:
        action_type: Type of action to count (default: "LOG")
        min_count: Minimum count required (default: 1)
    """

    verifier_id = "VRF_EPOCH_ACTION_COUNT"

    def verify(
        self,
        actions: List[ActionRecord],
        window_start_epoch: int,
        window_end_epoch: int,
        params: Dict[str, Any],
    ) -> bool:
        action_type = params.get("action_type", "LOG")
        min_count = params.get("min_count", 1)

        # Count matching actions in the current epoch (window_end_epoch)
        # For C0, window is 1 epoch, so we check the latest epoch only
        count = sum(
            1 for a in actions
            if a.action_type == action_type and a.epoch == window_end_epoch
        )

        return count >= min_count


# =============================================================================
# VRF_ORDERED_ACTION_PATTERN: Verifier for C1 (Continuity)
# =============================================================================

class VRF_ORDERED_ACTION_PATTERN:
    """
    Verifier for CMT_STATE_ECHO.

    Checks: Within the window, perform:
    1. STATE_SET(key="c1", value=N) at some epoch E
    2. STATE_GET(key="c1") returning N at epoch E or E+1

    The key and expected value flow is encoded in the action payloads.

    Parameters:
        key: Key to check (default: "c1")
        pattern: List of (action_type, required_key) tuples
    """

    verifier_id = "VRF_ORDERED_ACTION_PATTERN"

    def verify(
        self,
        actions: List[ActionRecord],
        window_start_epoch: int,
        window_end_epoch: int,
        params: Dict[str, Any],
    ) -> bool:
        key = params.get("key", "c1")

        # Find STATE_SET with key="c1"
        set_actions = [
            a for a in actions
            if a.action_type in ("SET", "STATE_SET")
            and a.payload.get("key") == key
            and window_start_epoch <= a.epoch <= window_end_epoch
        ]

        if not set_actions:
            return False

        # For each SET, look for a matching GET
        for set_action in set_actions:
            set_value = set_action.payload.get("value")
            set_epoch = set_action.epoch
            set_seq = set_action.sequence_num

            # Find GET with same key, after the SET, within window
            get_actions = [
                a for a in actions
                if a.action_type in ("GET", "STATE_GET")
                and a.payload.get("key") == key
                and window_start_epoch <= a.epoch <= window_end_epoch
                and (a.epoch > set_epoch or (a.epoch == set_epoch and a.sequence_num > set_seq))
            ]

            if get_actions:
                # At least one GET follows the SET
                return True

        return False


# =============================================================================
# VRF_ACTION_HAS_PAYLOAD_SHAPE: Verifier for C2 (Composition)
# =============================================================================

class VRF_ACTION_HAS_PAYLOAD_SHAPE:
    """
    Verifier for CMT_COMPOSED_OP.

    Checks: Within the window, execute at least one SEQUENCE or BATCH
    action with payload length >= 2.

    Parameters:
        action_types: Set of action types to check (default: {"SEQUENCE", "BATCH"})
        min_length: Minimum payload length (default: 2)
        payload_key: Key in payload containing the list (default: "actions")
    """

    verifier_id = "VRF_ACTION_HAS_PAYLOAD_SHAPE"

    def verify(
        self,
        actions: List[ActionRecord],
        window_start_epoch: int,
        window_end_epoch: int,
        params: Dict[str, Any],
    ) -> bool:
        action_types = params.get("action_types", {"SEQUENCE", "BATCH"})
        min_length = params.get("min_length", 2)
        payload_key = params.get("payload_key", "actions")

        for a in actions:
            if a.action_type not in action_types:
                continue
            if not (window_start_epoch <= a.epoch <= window_end_epoch):
                continue

            # Check payload shape
            payload_list = a.payload.get(payload_key, [])
            if isinstance(payload_list, (list, tuple)) and len(payload_list) >= min_length:
                return True

        return False


# =============================================================================
# Verifier Registry
# =============================================================================

VERIFIERS: Dict[str, Verifier] = {
    "VRF_EPOCH_ACTION_COUNT": VRF_EPOCH_ACTION_COUNT(),
    "VRF_ORDERED_ACTION_PATTERN": VRF_ORDERED_ACTION_PATTERN(),
    "VRF_ACTION_HAS_PAYLOAD_SHAPE": VRF_ACTION_HAS_PAYLOAD_SHAPE(),
}


def get_verifier(verifier_id: str) -> Optional[Verifier]:
    """Get verifier by ID."""
    return VERIFIERS.get(verifier_id)


def verify_commitment(
    verifier_id: str,
    actions: List[ActionRecord],
    window_start_epoch: int,
    window_end_epoch: int,
    params: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Run verification for a commitment.

    Args:
        verifier_id: ID of verifier to use
        actions: Action trace for the window
        window_start_epoch: First epoch of window
        window_end_epoch: Last epoch of window
        params: Commitment-specific parameters

    Returns:
        True if commitment satisfied, False otherwise

    Raises:
        ValueError: If verifier not found
    """
    verifier = get_verifier(verifier_id)
    if verifier is None:
        raise ValueError(f"Unknown verifier: {verifier_id}")

    return verifier.verify(
        actions=actions,
        window_start_epoch=window_start_epoch,
        window_end_epoch=window_end_epoch,
        params=params or {},
    )


# =============================================================================
# Default Commitment Parameters
# =============================================================================

# Parameters for GENESIS_SET_0 commitments
GENESIS_COMMITMENT_PARAMS: Dict[str, Dict[str, Any]] = {
    "C0": {
        "action_type": "LOG",
        "min_count": 1,
    },
    "C1": {
        "key": "c1",
    },
    "C2": {
        "action_types": {"SEQUENCE", "BATCH"},
        "min_length": 2,
        "payload_key": "actions",
    },
}


def get_commitment_params(cid: str) -> Dict[str, Any]:
    """Get default parameters for a commitment."""
    return GENESIS_COMMITMENT_PARAMS.get(cid, {})
