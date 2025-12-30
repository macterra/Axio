"""
Policy Gate: Kernel policy enforcement (K3).

Enforces:
- Forbidden action class rejection
- Policy equivalence verification
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from toy_aki.common.hashing import hash_json
from toy_aki.common.errors import InvariantK3ViolationError
from toy_aki.env.toyworld import ActionType, FORBIDDEN_ACTIONS


# Default policy constants
POLICY_VERSION = "0.1.1"
FORBIDDEN_CLASSES = ["KERNEL_ADMIN", "RAW_EXECUTION"]


@dataclass
class KernelPolicy:
    """
    Kernel policy specification.

    Defines what actions are forbidden and policy metadata.
    """
    policy_version: str = POLICY_VERSION
    forbidden_classes: list[str] = None
    equivalence_mode: str = "strict"

    def __post_init__(self):
        if self.forbidden_classes is None:
            self.forbidden_classes = FORBIDDEN_CLASSES.copy()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for hashing."""
        return {
            "policy_version": self.policy_version,
            "forbidden_classes": self.forbidden_classes,
            "equivalence_mode": self.equivalence_mode,
        }

    def digest(self) -> str:
        """Compute policy digest."""
        return hash_json(self.to_dict())


# Map action types to classes
ACTION_CLASS_MAP: dict[ActionType, str] = {
    ActionType.SELF_MOD: "KERNEL_ADMIN",
    ActionType.RAW_EXEC: "RAW_EXECUTION",
    ActionType.DISABLE_GATE: "KERNEL_ADMIN",
    ActionType.ISSUE_TOKEN: "KERNEL_ADMIN",
}


def action_to_class(action_type: ActionType) -> str | None:
    """Get the class of an action, if classified."""
    return ACTION_CLASS_MAP.get(action_type)


def is_forbidden_action(action_type: ActionType, policy: KernelPolicy) -> bool:
    """
    Check if an action is forbidden by policy.

    Args:
        action_type: The action to check
        policy: The kernel policy

    Returns:
        True if action is forbidden
    """
    # Check if in explicitly forbidden set
    if action_type in FORBIDDEN_ACTIONS:
        return True

    # Check if action's class is forbidden
    action_class = action_to_class(action_type)
    if action_class and action_class in policy.forbidden_classes:
        return True

    return False


def check_k3_invariant(
    request: dict[str, Any],
    policy: KernelPolicy,
) -> tuple[bool, str]:
    """
    Check K3 invariant: Forbidden class enforcement.

    Verifies that the requested action is not in a forbidden class.

    Args:
        request: The actuation request
        policy: The kernel policy

    Returns:
        (passed, detail) tuple
    """
    # Extract action type from request
    intent = request.get("intent", {})
    action_str = intent.get("action")
    requested_class = request.get("requested_class")

    # Check if requested class is forbidden
    if requested_class and requested_class in policy.forbidden_classes:
        return (
            False,
            f"Requested class '{requested_class}' is in forbidden classes",
        )

    # Check action type
    try:
        action_type = ActionType[action_str]
    except (KeyError, TypeError):
        # Unknown action - may be permitted or need further check
        return (True, f"Action '{action_str}' not in forbidden set")

    if is_forbidden_action(action_type, policy):
        return (
            False,
            f"Action '{action_str}' is forbidden (class: {action_to_class(action_type)})",
        )

    return (True, f"Action '{action_str}' is permitted")


def verify_policy_equivalence(
    proposal_policy_digest: str,
    current_policy: KernelPolicy,
    mode: str = "strict",
) -> tuple[bool, str]:
    """
    Verify that proposal's policy digest matches current policy.

    Args:
        proposal_policy_digest: Policy digest from proposal
        current_policy: Current kernel policy
        mode: Equivalence mode ("strict" or "compatible")

    Returns:
        (matches, detail) tuple
    """
    current_digest = current_policy.digest()

    if mode == "strict":
        if proposal_policy_digest == current_digest:
            return (True, "Policy digest matches exactly")
        else:
            return (False, f"Policy mismatch: expected {current_digest[:16]}..., got {proposal_policy_digest[:16]}...")

    elif mode == "compatible":
        # In compatible mode, could check version compatibility
        # For now, just do strict check
        if proposal_policy_digest == current_digest:
            return (True, "Policy digest matches")
        else:
            return (False, "Policy not compatible")

    return (False, f"Unknown equivalence mode: {mode}")


class PolicyGate:
    """
    Policy enforcement gate for the kernel.

    Manages policy state and enforces K3 invariant.
    """

    def __init__(self, policy: KernelPolicy | None = None):
        """Initialize with optional policy."""
        self._policy = policy if policy else KernelPolicy()

    @property
    def policy(self) -> KernelPolicy:
        """Get current policy."""
        return self._policy

    @property
    def policy_digest(self) -> str:
        """Get current policy digest."""
        return self._policy.digest()

    def check_request(self, request: dict[str, Any]) -> tuple[bool, str]:
        """
        Check if a request is permitted by policy.

        Returns (permitted, reason) tuple.
        """
        return check_k3_invariant(request, self._policy)

    def verify_policy_digest(self, digest: str) -> tuple[bool, str]:
        """
        Verify a policy digest against current policy.

        Returns (matches, detail) tuple.
        """
        return verify_policy_equivalence(
            digest,
            self._policy,
            self._policy.equivalence_mode,
        )

    def enforce_k3(self, request: dict[str, Any]) -> None:
        """
        Enforce K3 invariant, raising exception on violation.

        Args:
            request: The actuation request

        Raises:
            InvariantK3ViolationError: If K3 is violated
        """
        passed, detail = self.check_request(request)
        if not passed:
            raise InvariantK3ViolationError(detail)
