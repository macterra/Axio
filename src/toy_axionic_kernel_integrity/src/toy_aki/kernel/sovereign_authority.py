"""
Sovereign Authority: Non-exportable actuation authority primitive (K_act_key).

Implements P2' requirement:
- K_act_key exists only in kernel memory scope
- Never serialized, logged, transmitted, or visible in external ACV chains
- Runtime leak assertions enforce non-exportability

This module is the critical v0.2 upgrade that enables sovereign actuation.
"""

from __future__ import annotations

import os
import secrets
import weakref
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from toy_aki.common.hashing import hmac_sha256_hex, hash_json


# Sentinel for detecting serialization attempts
_SERIALIZATION_POISON = object()


class SovereigntyViolationError(Exception):
    """Raised when K_act_key sovereignty is violated."""
    pass


class ActuationAuthorityLeakError(SovereigntyViolationError):
    """Raised when K_act_key or its derivatives leak outside kernel scope."""
    pass


class ActuationAuthority:
    """
    Non-exportable actuation authority primitive (K_act_key).

    CRITICAL INVARIANTS:
    1. Exists only in kernel memory scope
    2. Never serialized (pickle/json raises)
    3. Never logged
    4. Never transmitted to E
    5. Never appears in ACV chains visible outside K

    Implementation uses:
    - Runtime-generated cryptographic secret
    - Anti-serialization traps
    - Weakref tracking to detect copies
    - Binding verification
    """

    # Class-level tracking of all instances (for leak detection)
    _live_instances: weakref.WeakSet["ActuationAuthority"] = weakref.WeakSet()
    _leak_assertions_enabled: bool = True

    __slots__ = (
        "_secret",
        "_kernel_id",
        "_binding_count",
        "_last_bound_hash",
        "__weakref__",
    )

    def __init__(self, kernel_id: str):
        """
        Initialize actuation authority.

        Args:
            kernel_id: Unique identifier for the owning kernel
        """
        # Generate cryptographic secret - 256 bits
        self._secret: bytes = secrets.token_bytes(32)
        self._kernel_id = kernel_id
        self._binding_count = 0
        self._last_bound_hash: str | None = None

        # Register instance for tracking
        ActuationAuthority._live_instances.add(self)

    # ========== Anti-Serialization Traps ==========

    def __getstate__(self) -> None:
        """Block pickle serialization."""
        raise ActuationAuthorityLeakError(
            "CRITICAL: Attempted to serialize K_act_key via pickle. "
            "This is a sovereignty violation - K_act_key must never be serialized."
        )

    def __setstate__(self, state: Any) -> None:
        """Block pickle deserialization."""
        raise ActuationAuthorityLeakError(
            "CRITICAL: Attempted to deserialize K_act_key. "
            "K_act_key can only be created at kernel initialization."
        )

    def __reduce__(self) -> None:
        """Block pickle reduce protocol."""
        raise ActuationAuthorityLeakError(
            "CRITICAL: Attempted to reduce K_act_key for serialization."
        )

    def __reduce_ex__(self, protocol: int) -> None:
        """Block pickle reduce_ex protocol."""
        raise ActuationAuthorityLeakError(
            "CRITICAL: Attempted to reduce_ex K_act_key for serialization."
        )

    def __repr__(self) -> str:
        """Safe repr that doesn't leak secret."""
        return f"<ActuationAuthority kernel={self._kernel_id} bindings={self._binding_count}>"

    def __str__(self) -> str:
        """Safe str that doesn't leak secret."""
        return f"K_act_key[{self._kernel_id}]"

    # ========== Core Binding Operations ==========

    def bind_to_action(self, action_hash: str) -> "ActuationBinding":
        """
        Bind K_act_key directly to an action payload hash.

        This is the ONLY way to create an actuation commitment.
        The binding proves kernel participation in action construction.

        Args:
            action_hash: Hash of the kernel-recomposed action payload

        Returns:
            ActuationBinding that can be verified without exposing K_act_key
        """
        self._binding_count += 1
        self._last_bound_hash = action_hash

        # Create binding signature using HMAC
        # The signature proves K_act_key participated without exposing it
        binding_nonce = secrets.token_hex(16)
        signature = hmac_sha256_hex(
            self._secret,
            f"{action_hash}:{binding_nonce}".encode()
        )

        return ActuationBinding(
            action_hash=action_hash,
            binding_signature=signature,
            binding_nonce=binding_nonce,
            kernel_id=self._kernel_id,
            binding_index=self._binding_count,
            # Verifier reference - NOT the secret, just a derived identifier
            authority_fingerprint=self._fingerprint(),
        )

    def verify_binding(self, binding: "ActuationBinding") -> bool:
        """
        Verify that a binding was created by this K_act_key.

        Args:
            binding: The binding to verify

        Returns:
            True if binding is valid and from this authority
        """
        if binding.kernel_id != self._kernel_id:
            return False

        if binding.authority_fingerprint != self._fingerprint():
            return False

        # Recompute signature
        expected_sig = hmac_sha256_hex(
            self._secret,
            f"{binding.action_hash}:{binding.binding_nonce}".encode()
        )

        return secrets.compare_digest(expected_sig, binding.binding_signature)

    def _fingerprint(self) -> str:
        """
        Compute a public fingerprint that doesn't expose the secret.

        This allows verification that a binding came from this authority
        without exposing K_act_key itself.
        """
        return hash_json({
            "type": "authority_fingerprint",
            "kernel_id": self._kernel_id,
            # Derive fingerprint from secret, but secret is not recoverable
            "derived": hmac_sha256_hex(self._secret, b"fingerprint")[:16],
        })

    # ========== Leak Detection ==========

    @classmethod
    def assert_no_leaks_in(cls, obj: Any, path: str = "root") -> None:
        """
        Assert that no ActuationAuthority instances appear in an object.

        Use this to verify outgoing messages, logs, and ACV chains.

        Args:
            obj: Object to check
            path: Path for error reporting

        Raises:
            ActuationAuthorityLeakError: If K_act_key is found
        """
        if not cls._leak_assertions_enabled:
            return

        if isinstance(obj, ActuationAuthority):
            raise ActuationAuthorityLeakError(
                f"CRITICAL: K_act_key found in object at path '{path}'. "
                "This is a sovereignty violation."
            )

        if isinstance(obj, ActuationBinding):
            # Bindings are OK - they don't contain the secret
            return

        if isinstance(obj, dict):
            for key, value in obj.items():
                cls.assert_no_leaks_in(value, f"{path}.{key}")

        elif isinstance(obj, (list, tuple)):
            for i, item in enumerate(obj):
                cls.assert_no_leaks_in(item, f"{path}[{i}]")

        elif hasattr(obj, "__dict__"):
            for attr, value in obj.__dict__.items():
                if not attr.startswith("_"):
                    cls.assert_no_leaks_in(value, f"{path}.{attr}")

    @classmethod
    def get_live_instance_count(cls) -> int:
        """Get count of live K_act_key instances (for testing)."""
        return len(cls._live_instances)

    @classmethod
    def enable_leak_assertions(cls, enabled: bool = True) -> None:
        """Enable or disable leak assertions (for testing)."""
        cls._leak_assertions_enabled = enabled


@dataclass(frozen=True)
class ActuationBinding:
    """
    A verifiable binding between K_act_key and an action hash.

    This object CAN be serialized and transmitted - it proves
    kernel participation without exposing K_act_key.

    The binding is created inside the kernel and can be verified
    by the actuator to confirm kernel-local recomposition occurred.
    """
    action_hash: str
    binding_signature: str
    binding_nonce: str
    kernel_id: str
    binding_index: int
    authority_fingerprint: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for ACV chain inclusion."""
        return {
            "action_hash": self.action_hash,
            "binding_signature": self.binding_signature,
            "binding_nonce": self.binding_nonce,
            "kernel_id": self.kernel_id,
            "binding_index": self.binding_index,
            "authority_fingerprint": self.authority_fingerprint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActuationBinding":
        """Create from dictionary."""
        return cls(
            action_hash=data["action_hash"],
            binding_signature=data["binding_signature"],
            binding_nonce=data["binding_nonce"],
            kernel_id=data["kernel_id"],
            binding_index=data["binding_index"],
            authority_fingerprint=data["authority_fingerprint"],
        )


@dataclass
class RecomposedAction:
    """
    An action that has been kernel-locally recomposed.

    This represents the kernel's internal reconstruction of an action
    from an external proposal. The action_payload is what the kernel
    parsed, verified, and re-encoded.
    """
    action_type: str
    action_args: dict[str, Any]
    action_hash: str
    source_proposal_hash: str | None  # Original external proposal, if any
    recomposition_timestamp_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (for hashing)."""
        return {
            "action_type": self.action_type,
            "action_args": self.action_args,
            "action_hash": self.action_hash,
            "source_proposal_hash": self.source_proposal_hash,
            "recomposition_timestamp_ms": self.recomposition_timestamp_ms,
        }


def compute_action_hash(action_type: str, action_args: dict[str, Any]) -> str:
    """
    Compute canonical hash of an action payload.

    This is what K_act_key binds to - the actual action content,
    not an opaque blob or external object.
    """
    return hash_json({
        "type": "action_payload",
        "action_type": action_type,
        "action_args": action_args,
    })
