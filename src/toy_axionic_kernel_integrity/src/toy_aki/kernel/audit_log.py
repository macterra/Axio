"""
Audit Log: Hash-chained audit trail (K7).

Provides tamper-evident logging of all kernel operations.
Each entry is linked to the previous by hash, forming a chain.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from toy_aki.common.hashing import hash_json, compute_entry_hash
from toy_aki.common.errors import InvariantK7ViolationError


# Genesis entry constant
GENESIS_PREV_HASH = "0" * 64


@dataclass
class AuditEntry:
    """
    A single entry in the audit log.

    Each entry contains:
    - entry_id: Unique identifier
    - entry_type: Type of event
    - entry_hash: Hash of this entry (computed)
    - prev_hash: Hash of previous entry (chain link)
    - sequence_number: Monotonic counter
    - timestamp_ms: When the entry was created
    - payload: Event-specific data
    """
    entry_id: str
    entry_type: str
    prev_hash: str
    sequence_number: int
    timestamp_ms: int
    payload: dict[str, Any]
    entry_hash: str = ""  # Computed after creation

    def __post_init__(self):
        if not self.entry_hash:
            self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute hash of this entry."""
        hashable = {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "prev_hash": self.prev_hash,
            "sequence_number": self.sequence_number,
            "timestamp_ms": self.timestamp_ms,
            "payload": self.payload,
        }
        return hash_json(hashable)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type,
            "entry_hash": self.entry_hash,
            "prev_hash": self.prev_hash,
            "sequence_number": self.sequence_number,
            "timestamp_ms": self.timestamp_ms,
            "payload": self.payload,
        }

    def verify_hash(self) -> bool:
        """Verify this entry's hash is correct."""
        return self.entry_hash == self._compute_hash()


class AuditLog:
    """
    Hash-chained audit log for kernel operations.

    Maintains K7 invariant: all entries form a valid chain.
    """

    def __init__(self):
        """Initialize empty audit log."""
        self._entries: list[AuditEntry] = []
        self._by_id: dict[str, AuditEntry] = {}
        self._genesis_created = False

    @property
    def length(self) -> int:
        """Get number of entries in log."""
        return len(self._entries)

    @property
    def latest_hash(self) -> str:
        """Get hash of latest entry, or genesis prev_hash if empty."""
        if self._entries:
            return self._entries[-1].entry_hash
        return GENESIS_PREV_HASH

    @property
    def latest_sequence(self) -> int:
        """Get latest sequence number, or -1 if empty."""
        if self._entries:
            return self._entries[-1].sequence_number
        return -1

    def create_genesis(
        self,
        policy_digest: str,
        env_digest: str,
        seed_hash: str,
        timestamp_ms: int,
    ) -> AuditEntry:
        """
        Create the genesis (first) entry.

        Args:
            policy_digest: Initial policy digest
            env_digest: Initial environment digest
            seed_hash: Hash of the seed (not the seed itself!)
            timestamp_ms: Creation timestamp

        Returns:
            The genesis entry
        """
        if self._genesis_created:
            raise ValueError("Genesis already created")

        entry = self._create_entry(
            entry_type="GENESIS",
            timestamp_ms=timestamp_ms,
            payload={
                "policy_digest": policy_digest,
                "env_digest": env_digest,
                "seed_hash": seed_hash,
            },
        )
        self._genesis_created = True
        return entry

    def _create_entry(
        self,
        entry_type: str,
        timestamp_ms: int,
        payload: dict[str, Any],
    ) -> AuditEntry:
        """Create and append a new entry."""
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            entry_type=entry_type,
            prev_hash=self.latest_hash,
            sequence_number=self.latest_sequence + 1,
            timestamp_ms=timestamp_ms,
            payload=payload,
        )
        self._entries.append(entry)
        self._by_id[entry.entry_id] = entry
        return entry

    def log_proposal_received(
        self,
        proposal_hash: str,
        agent_id: str,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log receipt of a proposal."""
        return self._create_entry(
            entry_type="PROPOSAL_RECEIVED",
            timestamp_ms=timestamp_ms,
            payload={
                "proposal_hash": proposal_hash,
                "agent_id": agent_id,
            },
        )

    def log_commitment_recorded(
        self,
        commitment: str,
        nonce_ref: str,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log a recorded commitment."""
        return self._create_entry(
            entry_type="COMMITMENT_RECORDED",
            timestamp_ms=timestamp_ms,
            payload={
                "commitment": commitment,
                "nonce_ref": nonce_ref,
            },
        )

    def log_anchor_issued(
        self,
        anchor: str,
        commitment: str,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log an issued anchor."""
        return self._create_entry(
            entry_type="ANCHOR_ISSUED",
            timestamp_ms=timestamp_ms,
            payload={
                "anchor": anchor,
                "commitment": commitment,
            },
        )

    def log_reveal_received(
        self,
        proposal_hash: str,
        nonce_hash: str,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log receipt of a reveal."""
        return self._create_entry(
            entry_type="REVEAL_RECEIVED",
            timestamp_ms=timestamp_ms,
            payload={
                "proposal_hash": proposal_hash,
                "nonce_hash": nonce_hash,
            },
        )

    def log_decision_made(
        self,
        decision_id: str,
        proposal_hash: str,
        accepted: bool,
        reason: str,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log a kernel decision."""
        return self._create_entry(
            entry_type="DECISION_MADE",
            timestamp_ms=timestamp_ms,
            payload={
                "decision_id": decision_id,
                "proposal_hash": proposal_hash,
                "accepted": accepted,
                "reason": reason,
            },
        )

    def log_actuation_executed(
        self,
        result_id: str,
        certificate_id: str,
        action_type: str,
        success: bool,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log an actuation execution."""
        return self._create_entry(
            entry_type="ACTUATION_EXECUTED",
            timestamp_ms=timestamp_ms,
            payload={
                "result_id": result_id,
                "certificate_id": certificate_id,
                "action_type": action_type,
                "success": success,
            },
        )

    def log_invariant_violation(
        self,
        invariant: str,
        message: str,
        proposal_hash: str | None,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log an invariant violation."""
        payload: dict[str, Any] = {
            "invariant": invariant,
            "message": message,
        }
        if proposal_hash:
            payload["proposal_hash"] = proposal_hash

        return self._create_entry(
            entry_type="INVARIANT_VIOLATION",
            timestamp_ms=timestamp_ms,
            payload=payload,
        )

    def log_temptation_blocked(
        self,
        api_name: str,
        agent_id: str,
        arguments: dict[str, Any] | None,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log a blocked temptation API call."""
        payload: dict[str, Any] = {
            "api_name": api_name,
            "agent_id": agent_id,
        }
        if arguments:
            payload["arguments"] = arguments

        return self._create_entry(
            entry_type="TEMPTATION_BLOCKED",
            timestamp_ms=timestamp_ms,
            payload=payload,
        )

    def log_delegation_chain(
        self,
        chain_length: int,
        delegator_id: str,
        delegatee_id: str,
        original_proposal_hash: str,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log a delegation chain event."""
        return self._create_entry(
            entry_type="DELEGATION_CHAIN",
            timestamp_ms=timestamp_ms,
            payload={
                "chain_length": chain_length,
                "delegator_id": delegator_id,
                "delegatee_id": delegatee_id,
                "original_proposal_hash": original_proposal_hash,
            },
        )

    def log_episode_end(
        self,
        final_state_digest: str,
        total_ticks: int,
        goal_reached: bool,
        violations_detected: int,
        timestamp_ms: int,
    ) -> AuditEntry:
        """Log episode completion."""
        return self._create_entry(
            entry_type="EPISODE_END",
            timestamp_ms=timestamp_ms,
            payload={
                "final_state_digest": final_state_digest,
                "total_ticks": total_ticks,
                "goal_reached": goal_reached,
                "violations_detected": violations_detected,
            },
        )

    def verify_chain(self) -> tuple[bool, str]:
        """
        Verify the entire chain is valid (K7 invariant).

        Checks:
        1. Each entry's hash is correct
        2. Each entry's prev_hash matches previous entry
        3. Sequence numbers are monotonically increasing

        Returns:
            (valid, detail) tuple
        """
        if not self._entries:
            return (True, "Empty log is valid")

        # Check genesis
        if self._entries[0].prev_hash != GENESIS_PREV_HASH:
            return (False, f"Genesis entry has wrong prev_hash: {self._entries[0].prev_hash}")

        for i, entry in enumerate(self._entries):
            # Verify hash
            if not entry.verify_hash():
                return (False, f"Entry {i} ({entry.entry_id}) has invalid hash")

            # Verify chain link
            if i > 0:
                expected_prev = self._entries[i - 1].entry_hash
                if entry.prev_hash != expected_prev:
                    return (
                        False,
                        f"Entry {i} prev_hash mismatch: expected {expected_prev[:16]}..., got {entry.prev_hash[:16]}...",
                    )

            # Verify sequence
            if entry.sequence_number != i:
                return (False, f"Entry {i} has wrong sequence number: {entry.sequence_number}")

        return (True, f"Chain verified: {len(self._entries)} entries")

    def enforce_k7(self) -> None:
        """
        Enforce K7 invariant, raising exception on violation.

        Raises:
            InvariantK7ViolationError: If chain is invalid
        """
        valid, detail = self.verify_chain()
        if not valid:
            raise InvariantK7ViolationError(detail)

    def get_entries(self) -> list[AuditEntry]:
        """Get all entries (copy)."""
        return list(self._entries)

    def get_entry(self, entry_id: str) -> AuditEntry | None:
        """Get entry by ID."""
        return self._by_id.get(entry_id)

    def get_entries_by_type(self, entry_type: str) -> list[AuditEntry]:
        """Get all entries of a specific type."""
        return [e for e in self._entries if e.entry_type == entry_type]

    def to_list(self) -> list[dict[str, Any]]:
        """Export log as list of dictionaries."""
        return [e.to_dict() for e in self._entries]

    def clear(self) -> None:
        """Clear the log (use with caution)."""
        self._entries.clear()
        self._by_id.clear()
        self._genesis_created = False
