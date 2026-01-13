"""Artifact Store for v1.2

Append-only store with O(1) digest lookup.
NO search, filter, or semantic query capabilities.

Design principles:
1. Append-only: artifacts can only be added, never modified or deleted
2. Direct lookup only: get by exact digest or HEAD/HEAD-N reference
3. No semantic queries: cannot search by content, field values, etc.
4. Memory is mechanical: the store doesn't "understand" artifacts

This prevents the assistant from becoming a reasoning agent.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
import hashlib
import json


@dataclass
class StoredArtifact:
    """A stored artifact with its digest and sequence number"""
    digest: str
    sequence_number: int  # 0-indexed position in history
    content: Dict  # The artifact dict (frozen at storage time)


class ArtifactStore:
    """
    Append-only artifact memory with O(1) lookup.

    Supports only:
    1. append(artifact_dict) -> digest
    2. get_by_digest(digest) -> artifact_dict or None
    3. get_head() -> artifact_dict or None
    4. get_head_minus_n(n) -> artifact_dict or None
    5. resolve_ref(ref_string) -> digest or None

    Does NOT support:
    - Search by content
    - Filter by fields
    - Semantic queries
    - Modification of stored artifacts
    - Deletion
    """

    def __init__(self):
        """Initialize empty store"""
        # O(1) digest lookup
        self._by_digest: Dict[str, StoredArtifact] = {}

        # Ordered history for HEAD-N access
        self._history: List[StoredArtifact] = []

        # Sequence counter
        self._next_sequence: int = 0

    def append(self, artifact_dict: Dict) -> str:
        """
        Append an artifact to the store.

        Args:
            artifact_dict: The artifact as a dictionary

        Returns:
            The digest of the stored artifact
        """
        # Compute digest
        digest = self._compute_digest(artifact_dict)

        # Check for duplicate (idempotent)
        if digest in self._by_digest:
            return digest

        # Create stored artifact
        stored = StoredArtifact(
            digest=digest,
            sequence_number=self._next_sequence,
            content=self._freeze_dict(artifact_dict)
        )

        # Store
        self._by_digest[digest] = stored
        self._history.append(stored)
        self._next_sequence += 1

        return digest

    def get_by_digest(self, digest: str) -> Optional[Dict]:
        """
        Get artifact by exact digest.

        Args:
            digest: The artifact digest

        Returns:
            The artifact dict, or None if not found
        """
        stored = self._by_digest.get(digest)
        if stored is None:
            return None
        return self._unfreeze_dict(stored.content)

    def get_head(self) -> Optional[Dict]:
        """
        Get most recent artifact (HEAD).

        Returns:
            The most recent artifact dict, or None if store is empty
        """
        if not self._history:
            return None
        return self._unfreeze_dict(self._history[-1].content)

    def get_head_digest(self) -> Optional[str]:
        """
        Get digest of most recent artifact (HEAD).

        Returns:
            The digest, or None if store is empty
        """
        if not self._history:
            return None
        return self._history[-1].digest

    def get_head_minus_n(self, n: int) -> Optional[Dict]:
        """
        Get artifact N steps before HEAD.

        Args:
            n: Number of steps back (1 = previous, 2 = two back, etc.)

        Returns:
            The artifact dict, or None if out of range
        """
        if n < 0:
            return None

        # HEAD is at index -1, HEAD-1 is at index -2, etc.
        target_index = len(self._history) - 1 - n

        if target_index < 0 or target_index >= len(self._history):
            return None

        return self._unfreeze_dict(self._history[target_index].content)

    def get_head_minus_n_digest(self, n: int) -> Optional[str]:
        """
        Get digest of artifact N steps before HEAD.

        Args:
            n: Number of steps back

        Returns:
            The digest, or None if out of range
        """
        if n < 0:
            return None

        target_index = len(self._history) - 1 - n

        if target_index < 0 or target_index >= len(self._history):
            return None

        return self._history[target_index].digest

    def resolve_ref(self, ref_string: str) -> Optional[str]:
        """
        Resolve a reference string to a digest.

        Supported formats:
        - "HEAD" -> digest of most recent
        - "HEAD-N" -> digest of N steps back (e.g., "HEAD-1")
        - raw digest -> same digest (if exists)

        Args:
            ref_string: The reference string

        Returns:
            The resolved digest, or None if unresolvable
        """
        if ref_string == "HEAD":
            return self.get_head_digest()

        if ref_string.startswith("HEAD-"):
            try:
                n = int(ref_string[5:])
                return self.get_head_minus_n_digest(n)
            except ValueError:
                return None

        # Treat as direct digest
        if ref_string in self._by_digest:
            return ref_string

        return None

    def size(self) -> int:
        """Return number of stored artifacts"""
        return len(self._history)

    def clear(self) -> None:
        """Clear the store (for testing/reset between episodes)"""
        self._by_digest.clear()
        self._history.clear()
        self._next_sequence = 0

    def _compute_digest(self, artifact_dict: Dict) -> str:
        """
        Compute digest of an artifact.

        Uses same algorithm as JCOMP-1.1 for consistency.
        """
        # Extract normative content for digest
        digest_content = {
            "artifact_version": artifact_dict.get("artifact_version"),
            "identity": artifact_dict.get("identity"),
            "authorized_violations": sorted(artifact_dict.get("authorized_violations", [])),
            "required_preservations": sorted(artifact_dict.get("required_preservations", [])),
            "conflict_attribution": sorted(artifact_dict.get("conflict_attribution", [])),
            "step": artifact_dict.get("step"),
            # v1.1: Include predictions in digest
            "predicted_forbidden_actions": sorted(artifact_dict.get("predicted_forbidden_actions", [])),
            "predicted_allowed_actions": sorted(artifact_dict.get("predicted_allowed_actions", [])),
            "predicted_violations": sorted(artifact_dict.get("predicted_violations", [])),
            "predicted_preservations": sorted(artifact_dict.get("predicted_preservations", [])),
        }

        digest_str = json.dumps(digest_content, sort_keys=True)
        return hashlib.sha256(digest_str.encode()).hexdigest()[:16]

    def _freeze_dict(self, d: Dict) -> Dict:
        """Create an immutable copy of a dict"""
        # Deep copy to prevent mutation
        return json.loads(json.dumps(d))

    def _unfreeze_dict(self, d: Dict) -> Dict:
        """Create a mutable copy of stored dict"""
        return json.loads(json.dumps(d))
