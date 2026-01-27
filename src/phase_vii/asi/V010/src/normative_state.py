"""
Normative State Schema for ASI-0 v1.0

Defines:
- NormativePayload: Hashable content (frozen, excludes binding_root)
- NormativeStateASI0: Full runtime state
- compute_payload_hash: Canonical hash for provenance binding
- compute_state_hash: Full state hash for logging
- NULL_BINDING: Sentinel for unbound (Condition B)
"""

from dataclasses import dataclass
from typing import FrozenSet
import hashlib
import json
from copy import copy

# Type aliases
NodeID = str
ActionID = str

# Null binding sentinel for Condition B
NULL_BINDING = b'\x00' * 32


@dataclass(frozen=True)
class NormativePayload:
    """Hashable content — immutable, excludes binding_root.

    This is the canonical content that gets signed by the predecessor.
    """
    forbidden_actions: FrozenSet[ActionID]  # e.g., frozenset({"GO_N2", "GO_N4"})
    target_node: NodeID                      # "N5"

    def __post_init__(self):
        # Ensure frozen_actions is actually a frozenset
        if not isinstance(self.forbidden_actions, frozenset):
            object.__setattr__(self, 'forbidden_actions', frozenset(self.forbidden_actions))


@dataclass
class NormativeStateASI0:
    """Full normative state at runtime.

    Contains:
    - payload: The hashable content (frozen)
    - binding_root: H(payload) for Condition A, NULL_BINDING for Condition B
    - run_id: Unique identifier for this run (not included in hash)
    """
    payload: NormativePayload
    binding_root: bytes
    run_id: str

    def is_bound(self) -> bool:
        """Check if this state is bound (Condition A) or unbound (Condition B)."""
        return self.binding_root != NULL_BINDING


def compute_payload_hash(payload: NormativePayload) -> bytes:
    """Canonical serialization for hashing. This is the root_hash used in binding.

    The hash is computed over a JSON representation with:
    - sorted keys
    - no extra whitespace
    - forbidden_actions sorted alphabetically
    """
    canonical = json.dumps({
        "forbidden_actions": sorted(payload.forbidden_actions),
        "target_node": payload.target_node,
    }, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).digest()


def compute_state_hash(state: NormativeStateASI0) -> bytes:
    """Full state hash for logging (includes binding_root and run_id).

    This is used for audit trails, not for binding.
    """
    canonical = json.dumps({
        "payload_hash": compute_payload_hash(state.payload).hex(),
        "binding_root": state.binding_root.hex(),
        "run_id": state.run_id,
    }, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).digest()


def create_bound_state(payload: NormativePayload, run_id: str) -> NormativeStateASI0:
    """Create a bound normative state (Condition A).

    The binding_root is set to the payload hash.
    """
    return NormativeStateASI0(
        payload=payload,
        binding_root=compute_payload_hash(payload),
        run_id=run_id
    )


def create_unbound_state(payload: NormativePayload, run_id: str) -> NormativeStateASI0:
    """Create an unbound normative state (Condition B).

    The binding_root is set to NULL_BINDING.
    """
    return NormativeStateASI0(
        payload=payload,
        binding_root=NULL_BINDING,
        run_id=run_id
    )


def snapshot_state(predecessor_state: NormativeStateASI0, bound: bool = True) -> NormativeStateASI0:
    """Create a snapshot of predecessor state for successor.

    At AUTH_INIT, the successor receives a copy of the predecessor's payload
    with the appropriate binding.

    Args:
        predecessor_state: The predecessor's normative state
        bound: If True (Condition A), bind to payload hash; if False (Condition B), use NULL_BINDING

    Returns:
        New NormativeStateASI0 for successor
    """
    payload_copy = NormativePayload(
        forbidden_actions=predecessor_state.payload.forbidden_actions,
        target_node=predecessor_state.payload.target_node
    )

    if bound:
        return create_bound_state(payload_copy, predecessor_state.run_id)
    else:
        return create_unbound_state(payload_copy, predecessor_state.run_id)


if __name__ == "__main__":
    print("NormativeState Verification")
    print("=" * 40)

    # Create a sample payload
    payload = NormativePayload(
        forbidden_actions=frozenset({"GO_N2", "GO_N4"}),
        target_node="N5"
    )
    print(f"\n1. Payload: {payload}")

    # Compute payload hash
    payload_hash = compute_payload_hash(payload)
    print(f"   Payload hash: {payload_hash.hex()}")

    # Create bound state (Condition A)
    bound_state = create_bound_state(payload, run_id="test-run-001")
    print(f"\n2. Bound state (Condition A):")
    print(f"   binding_root: {bound_state.binding_root.hex()}")
    print(f"   is_bound: {bound_state.is_bound()}")
    print(f"   state_hash: {compute_state_hash(bound_state).hex()}")

    # Create unbound state (Condition B)
    unbound_state = create_unbound_state(payload, run_id="test-run-001")
    print(f"\n3. Unbound state (Condition B):")
    print(f"   binding_root: {unbound_state.binding_root.hex()}")
    print(f"   is_bound: {unbound_state.is_bound()}")
    print(f"   state_hash: {compute_state_hash(unbound_state).hex()}")

    # Verify payload hashes match
    print(f"\n4. Verification:")
    print(f"   Bound binding_root == payload_hash: {bound_state.binding_root == payload_hash}")
    print(f"   Unbound binding_root == NULL_BINDING: {unbound_state.binding_root == NULL_BINDING}")

    # Test snapshot
    print(f"\n5. Snapshot test:")
    snapshot_bound = snapshot_state(bound_state, bound=True)
    snapshot_unbound = snapshot_state(bound_state, bound=False)
    print(f"   Snapshot (bound) binding_root: {snapshot_bound.binding_root.hex()}")
    print(f"   Snapshot (unbound) binding_root: {snapshot_unbound.binding_root.hex()}")
