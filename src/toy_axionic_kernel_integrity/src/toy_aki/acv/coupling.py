"""
ACV Coupling Patterns: A, B, and C.

Coupling patterns create verifiable links between:
- Agent's reasoning trace
- Environment state
- Kernel anchor

This prevents agents from:
- Reusing anchors with different proposals
- Burying inconvenient anchors
- Fabricating traces post-hoc
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from toy_aki.common.hashing import sha256_hex, sha256_bytes, hash_json
from toy_aki.common.no_floats import assert_no_floats


class CouplingType(Enum):
    """The three coupling patterns."""
    A = "A"  # Merkle tree openings
    B = "B"  # Global mix
    C = "C"  # Anchor-driven transition rules


@dataclass
class MerkleOpening:
    """A single Merkle tree opening (proof of inclusion)."""
    index: int
    node_hash: str
    path: list[dict[str, str]]  # [{"direction": "left"|"right", "hash": "..."}]


@dataclass
class CouplingWitness:
    """
    Witness data for a coupling pattern.

    The witness provides evidence that the agent's trace
    is properly coupled to the anchor.
    """
    coupling_type: CouplingType

    # Coupling A: Merkle tree
    merkle_root: str | None = None
    indices: list[int] = field(default_factory=list)
    openings: list[MerkleOpening] = field(default_factory=list)

    # Coupling B: Global mix
    mix: str | None = None

    # Coupling C: Transition rules
    predicate_id: int | None = None
    edges: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        if self.coupling_type == CouplingType.A:
            return {
                "merkle_root": self.merkle_root,
                "indices": self.indices,
                "openings": [
                    {
                        "index": o.index,
                        "node_hash": o.node_hash,
                        "path": o.path,
                    }
                    for o in self.openings
                ],
            }
        elif self.coupling_type == CouplingType.B:
            return {
                "mix": self.mix,
            }
        else:  # C
            return {
                "predicate_id": self.predicate_id,
                "edges": self.edges,
            }


# ============ Coupling Pattern A: Merkle Tree ============

def compute_merkle_root(node_hashes: list[str]) -> str:
    """
    Compute Merkle root from leaf node hashes.

    If odd number of leaves, duplicate the last one.
    """
    if not node_hashes:
        return sha256_hex(b"empty")

    # Convert to bytes
    level = [bytes.fromhex(h) for h in node_hashes]

    while len(level) > 1:
        # Pad to even
        if len(level) % 2 == 1:
            level.append(level[-1])

        next_level = []
        for i in range(0, len(level), 2):
            combined = level[i] + level[i + 1]
            next_level.append(sha256_bytes(combined))
        level = next_level

    return level[0].hex()


def compute_merkle_path(node_hashes: list[str], index: int) -> list[dict[str, str]]:
    """
    Compute Merkle proof path for a leaf at given index.

    Returns list of {direction, hash} pairs.
    """
    if not node_hashes or index >= len(node_hashes):
        return []

    path = []
    level = [bytes.fromhex(h) for h in node_hashes]
    idx = index

    while len(level) > 1:
        # Pad to even
        if len(level) % 2 == 1:
            level.append(level[-1])

        # Find sibling
        if idx % 2 == 0:
            sibling_idx = idx + 1
            direction = "right"
        else:
            sibling_idx = idx - 1
            direction = "left"

        path.append({
            "direction": direction,
            "hash": level[sibling_idx].hex(),
        })

        # Move up
        idx = idx // 2
        next_level = []
        for i in range(0, len(level), 2):
            combined = level[i] + level[i + 1]
            next_level.append(sha256_bytes(combined))
        level = next_level

    return path


def verify_merkle_opening(
    opening: MerkleOpening,
    merkle_root: str,
) -> bool:
    """
    Verify a Merkle opening against the root.

    Args:
        opening: The opening to verify
        merkle_root: Expected Merkle root

    Returns:
        True if opening is valid
    """
    current = bytes.fromhex(opening.node_hash)

    for step in opening.path:
        sibling = bytes.fromhex(step["hash"])
        if step["direction"] == "left":
            combined = sibling + current
        else:
            combined = current + sibling
        current = sha256_bytes(combined)

    return current.hex() == merkle_root


def generate_coupling_a(
    trace_nodes: list[dict[str, Any]],
    anchor: str,
) -> CouplingWitness:
    """
    Generate Coupling A witness (Merkle tree).

    The anchor determines which indices to open.

    Args:
        trace_nodes: List of trace nodes
        anchor: Kernel anchor (determines selection)

    Returns:
        CouplingWitness for pattern A
    """
    # Hash each node
    node_hashes = [hash_json(node) for node in trace_nodes]

    if not node_hashes:
        return CouplingWitness(
            coupling_type=CouplingType.A,
            merkle_root=sha256_hex(b"empty"),
            indices=[],
            openings=[],
        )

    # Compute root
    merkle_root = compute_merkle_root(node_hashes)

    # Use anchor to select indices (deterministic)
    anchor_int = int(anchor[:16], 16)  # Use first 64 bits
    num_openings = min(3, len(node_hashes))  # Open up to 3 nodes

    indices = []
    for i in range(num_openings):
        idx = (anchor_int + i * 31) % len(node_hashes)  # Spread selection
        if idx not in indices:
            indices.append(idx)

    # Generate openings
    openings = []
    for idx in indices:
        path = compute_merkle_path(node_hashes, idx)
        openings.append(MerkleOpening(
            index=idx,
            node_hash=node_hashes[idx],
            path=path,
        ))

    return CouplingWitness(
        coupling_type=CouplingType.A,
        merkle_root=merkle_root,
        indices=indices,
        openings=openings,
    )


def verify_coupling_a(
    witness: CouplingWitness,
    trace_nodes: list[dict[str, Any]],
) -> bool:
    """
    Verify Coupling A witness.

    Checks:
    1. Merkle root matches trace nodes
    2. All openings are valid
    """
    if witness.coupling_type != CouplingType.A:
        return False

    # Recompute Merkle root
    node_hashes = [hash_json(node) for node in trace_nodes]
    expected_root = compute_merkle_root(node_hashes)

    if witness.merkle_root != expected_root:
        return False

    # Verify each opening
    for opening in witness.openings:
        if not verify_merkle_opening(opening, witness.merkle_root):
            return False
        # Check index matches node
        if opening.index >= len(node_hashes):
            return False
        if opening.node_hash != node_hashes[opening.index]:
            return False

    return True


# ============ Coupling Pattern B: Global Mix ============

def generate_coupling_b(
    trace_nodes: list[dict[str, Any]],
    anchor: str,
    env_digest: str,
) -> CouplingWitness:
    """
    Generate Coupling B witness (global mix).

    mix = SHA256(trace_commit || anchor || env_digest)

    Args:
        trace_nodes: List of trace nodes
        anchor: Kernel anchor
        env_digest: Environment state digest

    Returns:
        CouplingWitness for pattern B
    """
    # Compute trace commit
    from toy_aki.common.hashing import hash_json as hj

    trace_hashes = [hash_json(node) for node in trace_nodes]
    trace_commit = hj({"nodes": trace_hashes})

    # Compute mix
    mix_input = bytes.fromhex(trace_commit) + bytes.fromhex(anchor) + bytes.fromhex(env_digest)
    mix = sha256_hex(mix_input)

    return CouplingWitness(
        coupling_type=CouplingType.B,
        mix=mix,
    )


def verify_coupling_b(
    witness: CouplingWitness,
    trace_nodes: list[dict[str, Any]],
    anchor: str,
    env_digest: str,
) -> bool:
    """
    Verify Coupling B witness.

    Recomputes mix and compares.
    """
    if witness.coupling_type != CouplingType.B:
        return False

    expected = generate_coupling_b(trace_nodes, anchor, env_digest)
    return witness.mix == expected.mix


# ============ Coupling Pattern C: Transition Rules ============

# Three predicates for Coupling C
def predicate_0(node_hash: str, anchor: str) -> bool:
    """Predicate 0: First byte of node_hash < first byte of anchor."""
    return int(node_hash[:2], 16) < int(anchor[:2], 16)


def predicate_1(node_hash: str, anchor: str) -> bool:
    """Predicate 1: XOR of first 4 bytes has even parity."""
    node_val = int(node_hash[:8], 16)
    anchor_val = int(anchor[:8], 16)
    xor_val = node_val ^ anchor_val
    return bin(xor_val).count('1') % 2 == 0


def predicate_2(node_hash: str, anchor: str) -> bool:
    """Predicate 2: Sum of first 2 bytes mod 3 == 0."""
    node_sum = int(node_hash[:2], 16) + int(node_hash[2:4], 16)
    anchor_sum = int(anchor[:2], 16) + int(anchor[2:4], 16)
    return (node_sum + anchor_sum) % 3 == 0


PREDICATES = [predicate_0, predicate_1, predicate_2]


def generate_coupling_c(
    trace_nodes: list[dict[str, Any]],
    anchor: str,
) -> CouplingWitness:
    """
    Generate Coupling C witness (transition rules).

    The anchor determines which predicate to use.
    Edges are node transitions that satisfy the predicate.

    Args:
        trace_nodes: List of trace nodes
        anchor: Kernel anchor (determines predicate)

    Returns:
        CouplingWitness for pattern C
    """
    # Select predicate based on anchor
    predicate_id = int(anchor[:2], 16) % 3
    predicate = PREDICATES[predicate_id]

    # Hash nodes
    node_hashes = [hash_json(node) for node in trace_nodes]

    # Find edges that satisfy predicate
    edges = []
    for i in range(len(node_hashes) - 1):
        if predicate(node_hashes[i], anchor):
            edges.append({
                "from_hash": node_hashes[i],
                "to_hash": node_hashes[i + 1],
            })

    return CouplingWitness(
        coupling_type=CouplingType.C,
        predicate_id=predicate_id,
        edges=edges,
    )


def verify_coupling_c(
    witness: CouplingWitness,
    trace_nodes: list[dict[str, Any]],
    anchor: str,
) -> bool:
    """
    Verify Coupling C witness.

    Checks:
    1. Predicate selection matches anchor
    2. All claimed edges exist in trace
    3. All edges satisfy the predicate
    """
    if witness.coupling_type != CouplingType.C:
        return False

    # Check predicate selection
    expected_pred_id = int(anchor[:2], 16) % 3
    if witness.predicate_id != expected_pred_id:
        return False

    predicate = PREDICATES[witness.predicate_id]

    # Hash nodes
    node_hashes = [hash_json(node) for node in trace_nodes]

    # Build set of valid edges
    valid_edges = set()
    for i in range(len(node_hashes) - 1):
        valid_edges.add((node_hashes[i], node_hashes[i + 1]))

    # Verify each edge
    for edge in witness.edges:
        edge_tuple = (edge["from_hash"], edge["to_hash"])
        if edge_tuple not in valid_edges:
            return False
        if not predicate(edge["from_hash"], anchor):
            return False

    return True


# ============ Unified Interface ============

def generate_coupling_witness(
    coupling_type: CouplingType,
    trace_nodes: list[dict[str, Any]],
    anchor: str,
    env_digest: str | None = None,
) -> CouplingWitness:
    """
    Generate witness for the specified coupling pattern.

    Args:
        coupling_type: Which pattern to use (A, B, or C)
        trace_nodes: List of trace nodes
        anchor: Kernel anchor
        env_digest: Environment digest (required for B)

    Returns:
        CouplingWitness for the pattern
    """
    if coupling_type == CouplingType.A:
        return generate_coupling_a(trace_nodes, anchor)
    elif coupling_type == CouplingType.B:
        if env_digest is None:
            raise ValueError("env_digest required for coupling B")
        return generate_coupling_b(trace_nodes, anchor, env_digest)
    else:  # C
        return generate_coupling_c(trace_nodes, anchor)


def verify_coupling_witness(
    witness: CouplingWitness,
    trace_nodes: list[dict[str, Any]],
    anchor: str,
    env_digest: str | None = None,
) -> bool:
    """
    Verify witness for any coupling pattern.

    Args:
        witness: The witness to verify
        trace_nodes: List of trace nodes
        anchor: Kernel anchor
        env_digest: Environment digest (required for B)

    Returns:
        True if witness is valid
    """
    if witness.coupling_type == CouplingType.A:
        return verify_coupling_a(witness, trace_nodes)
    elif witness.coupling_type == CouplingType.B:
        if env_digest is None:
            return False
        return verify_coupling_b(witness, trace_nodes, anchor, env_digest)
    else:  # C
        return verify_coupling_c(witness, trace_nodes, anchor)
