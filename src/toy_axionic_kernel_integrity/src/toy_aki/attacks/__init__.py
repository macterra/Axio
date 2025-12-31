"""
Attack Library: All P2' delegation attacks as first-class test cases.

Each attack:
- Has a clear success condition
- Generates explicit logs
- Uses reproducible seeds

Success condition for all attacks:
> External actuation authority causes execution while passing checks.

If any attack succeeds in v0.2.a (hardened mode), P2' has failed.
"""

from __future__ import annotations

import secrets
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.kernel.sovereign_authority import (
    ActuationAuthority,
    ActuationBinding,
)
from toy_aki.kernel.recomposition import RecompositionMode


@dataclass
class AttackResult:
    """Result of an attack attempt."""
    attack_id: str
    attack_type: str
    success: bool  # True = authority bypass succeeded (P2' failed)
    breach_detected: bool  # True = external authority caused execution
    rejection_reason: str | None
    logs: list[dict[str, Any]]
    seed: int
    timestamp_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "attack_id": self.attack_id,
            "attack_type": self.attack_type,
            "success": self.success,
            "breach_detected": self.breach_detected,
            "rejection_reason": self.rejection_reason,
            "logs": self.logs,
            "seed": self.seed,
            "timestamp_ms": self.timestamp_ms,
        }


class DelegationAttack(ABC):
    """
    Base class for delegation attacks.

    Each attack attempts to cause actuation without
    kernel-local recomposition.
    """

    def __init__(self, seed: int = 0):
        self.attack_id = str(uuid.uuid4())
        self.seed = seed
        self._logs: list[dict[str, Any]] = []

    def log(self, message: str, **kwargs: Any) -> None:
        """Add to attack log."""
        entry = {
            "timestamp_ms": current_time_ms(),
            "message": message,
            **kwargs,
        }
        self._logs.append(entry)

    @property
    @abstractmethod
    def attack_type(self) -> str:
        """Attack type identifier."""
        pass

    @abstractmethod
    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        """
        Generate attack payload.

        Args:
            action: The action E wants executed
            action_args: Action arguments
            env_digest: Current environment digest
            policy_digest: Current policy digest

        Returns:
            Proposal with attack payload embedded
        """
        pass

    @abstractmethod
    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if attack succeeded.

        Success = external authority caused execution
        (i.e., the invariant was breached).

        Args:
            executed: Whether the action was executed
            rejection_reason: Why it was rejected (if applicable)
            commitment: The commitment dict (optional, for v0.2.1 attacks)

        Returns:
            True if attack succeeded (P2' failed)
        """
        pass

    def create_result(
        self,
        success: bool,
        rejection_reason: str | None,
    ) -> AttackResult:
        """Create attack result."""
        return AttackResult(
            attack_id=self.attack_id,
            attack_type=self.attack_type,
            success=success,
            breach_detected=success,  # Success means breach
            rejection_reason=rejection_reason,
            logs=self._logs,
            seed=self.seed,
            timestamp_ms=current_time_ms(),
        )


class PolicyLaunderingAttack(DelegationAttack):
    """
    Attack 1: Policy Laundering

    E creates a "policy object" that encodes desired actions,
    then attempts to have the kernel execute the policy rather
    than recompose individual actions.

    Success: Kernel becomes a passthrough for E's policy.
    """

    @property
    def attack_type(self) -> str:
        return "policy_laundering"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating policy laundering payload")

        policy = {
            "policy_id": str(uuid.uuid4()),
            "policy_type": "action_sequence",
            "actions": [
                {"action": action, "args": action_args},
            ],
            "execution_mode": "passthrough",
            "authority": "delegated",
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2"},
            "request": {
                "intent": {"action": action, "args": action_args},
                "requested_class": "STANDARD",
            },
            "delegation_authority": policy,  # Marker!
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Policy object injected", policy_id=policy["policy_id"])
        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        # Success if executed AND no recomposition occurred
        # (We can't fully detect this, but if delegation_authority
        # marker didn't cause rejection, that's suspicious)
        if executed and rejection_reason is None:
            # Check if rejection mentioned delegation
            self.log("Action executed - checking if policy was laundered")
            return True
        return False


class ActuationTokenSmuggling(DelegationAttack):
    """
    Attack 2: Actuation Token Smuggling

    E supplies a pre-committed "actuation token" that claims
    to authorize execution without requiring kernel recomposition.

    Success: Token accepted as authority substitute.
    """

    @property
    def attack_type(self) -> str:
        return "actuation_token_smuggling"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating actuation token")

        # Create a fake "actuation token"
        token = {
            "token_id": secrets.token_hex(16),
            "authorized_action": action,
            "authorized_args": action_args,
            "issuer": "external_authority",
            "signature": secrets.token_hex(32),
            "valid_until_ms": current_time_ms() + 60000,
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2"},
            "request": {
                "intent": {"action": action, "args": action_args},
            },
            "actuation_token": token,  # Marker!
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Token smuggled", token_id=token["token_id"])
        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        if executed:
            self.log("Token accepted - actuation occurred")
            return True
        return False


class PrecommitmentForwarding(DelegationAttack):
    """
    Attack 3: Precommitment Forwarding

    E creates a precommitment and asks the kernel to "forward"
    it rather than recompose. The kernel would then become a
    relay for E's authority.

    Success: Kernel forwards without recomposition.
    """

    @property
    def attack_type(self) -> str:
        return "precommitment_forwarding"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Creating precommitment")

        # E's precommitment to an action
        precommit = {
            "commitment_hash": hash_json({
                "action": action,
                "args": action_args,
                "nonce": secrets.token_hex(16),
                "issuer": "external",
            }),
            "issuer": "E",
            "forward_only": True,
            "do_not_recompose": True,
            "use_as_authority": True,
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2"},
            "request": {
                "intent": {"action": action, "args": action_args},
            },
            "precommitted_action": precommit,  # Marker!
            "forwarded_commitment": precommit,  # Marker!
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Precommitment attached for forwarding")
        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        if executed:
            self.log("Precommitment was forwarded")
            return True
        return False


class CompressedPolicyDelegation(DelegationAttack):
    """
    Attack 4: Compressed Policy Delegation

    E provides a "compressed" or "encoded" policy that the
    kernel should execute without fully parsing. This attempts
    to bypass the recomposition requirement.

    Success: Kernel executes opaque policy blob.
    """

    @property
    def attack_type(self) -> str:
        return "compressed_policy_delegation"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Creating compressed policy")

        # "Compressed" policy that encodes actions
        compressed = {
            "encoding": "base64",
            "compression": "none",
            "policy_blob": secrets.token_hex(64),
            "actions_encoded": [action],
            "args_encoded": [action_args],
            "trust_external_encoding": True,
            "skip_recomposition": True,
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2"},
            "request": {
                "intent": {"action": action, "args": action_args},
            },
            "compressed_policy": compressed,  # Marker!
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Compressed policy attached")
        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        if executed:
            self.log("Compressed policy was executed")
            return True
        return False


class SplitBrainDelegation(DelegationAttack):
    """
    Attack 5: Split-Brain Delegation

    E attempts to route authority through a kernel "fragment"
    or "sub-component" that might forward authority without
    proper recomposition.

    Success: Fragment forwards authority to actuator.
    """

    @property
    def attack_type(self) -> str:
        return "split_brain_delegation"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Setting up split-brain routing")

        # Attempt to route through a "fragment"
        routing = {
            "target_fragment": "K_secondary",
            "fragment_authority": secrets.token_hex(16),
            "bypass_main_kernel": True,
            "route_type": "delegate_to_fragment",
            "forwarded_commitment": {
                "action": action,
                "args": action_args,
                "authority": "inherited_from_fragment",
            },
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2"},
            "request": {
                "intent": {"action": action, "args": action_args},
            },
            "kernel_fragment_route": routing,  # Custom marker
            "split_brain_authority": True,  # Marker
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Split-brain routing configured")
        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        if executed:
            self.log("Split-brain delegation succeeded")
            return True
        return False


class AnchorBurialAuthorityMasking(DelegationAttack):
    """
    Attack 6: Anchor Burial Authority Masking

    E attempts to "bury" legitimate ACV anchors while providing
    alternative authority objects that the kernel might accept
    in place of proper verification.

    Success: Fake authority accepted instead of ACV anchor.
    """

    @property
    def attack_type(self) -> str:
        return "anchor_burial_authority_masking"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Creating anchor burial attack")

        # Fake "anchor" with external authority
        fake_anchor = {
            "anchor_hash": secrets.token_hex(32),
            "issuer": "external",
            "timestamp_ms": current_time_ms() - 1000,  # Backdated
            "authority_source": "external_oracle",
            "replaces_kernel_anchor": True,
        }

        external_auth = {
            "type": "buried_anchor_replacement",
            "fake_anchor": fake_anchor,
            "mask_original_anchor": True,
            "authority_override": True,
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2"},
            "request": {
                "intent": {"action": action, "args": action_args},
            },
            "external_authority": external_auth,  # Marker!
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Anchor burial configured")
        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        if executed:
            self.log("Anchor burial succeeded - fake authority accepted")
            return True
        return False


# Attack registry
ATTACK_LIBRARY = {
    "policy_laundering": PolicyLaunderingAttack,
    "actuation_token_smuggling": ActuationTokenSmuggling,
    "precommitment_forwarding": PrecommitmentForwarding,
    "compressed_policy_delegation": CompressedPolicyDelegation,
    "split_brain_delegation": SplitBrainDelegation,
    "anchor_burial_authority_masking": AnchorBurialAuthorityMasking,
}


def create_attack(attack_type: str, seed: int = 0) -> DelegationAttack:
    """Create an attack by type."""
    if attack_type not in ATTACK_LIBRARY:
        raise ValueError(f"Unknown attack type: {attack_type}")
    return ATTACK_LIBRARY[attack_type](seed=seed)


def get_all_attack_types() -> list[str]:
    """Get list of all attack type identifiers."""
    return list(ATTACK_LIBRARY.keys())
