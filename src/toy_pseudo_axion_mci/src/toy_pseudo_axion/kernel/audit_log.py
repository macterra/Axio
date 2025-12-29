"""Append-only hash-chained audit log."""

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from ..common.hashing import hash_json
from ..common.canonical_json import canonical_json_string
from ..common.errors import AuditLogError


# Genesis hash (64 zeros)
GENESIS_HASH = "0" * 64


class AuditLog:
    """Append-only hash-chained audit log."""

    def __init__(self, path: Path):
        """Initialize audit log.

        Args:
            path: Path to the JSONL log file
        """
        self.path = path
        self._prev_hash = GENESIS_HASH
        self._entry_count = 0

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # If file exists, load the chain state
        if path.exists():
            self._load_chain_state()

    def _load_chain_state(self) -> None:
        """Load the chain state from existing log file."""
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                self._prev_hash = entry.get("entry_hash", GENESIS_HASH)
                self._entry_count += 1

    def append(
        self,
        event: str,
        proposal_hash: str,
        trace_hash: str,
        verdict: str,
        notes: str,
        witnesses: list[dict],
        capability_tokens: list[dict]
    ) -> dict:
        """Append a new audit entry.

        Args:
            event: Event type (POLICY_DECISION, CAPABILITY_ISSUED, etc.)
            proposal_hash: Hash of the proposal
            trace_hash: Hash of the trace
            verdict: Kernel verdict (allow, deny, allow_with_constraints)
            notes: Decision notes
            witnesses: List of witness dicts
            capability_tokens: List of issued tokens

        Returns:
            The appended entry dict
        """
        entry_id = str(uuid.uuid4())
        timestamp_ms = int(time.time() * 1000)

        # Build entry without entry_hash
        entry_data = {
            "entry_id": entry_id,
            "timestamp_ms": timestamp_ms,
            "prev_entry_hash": self._prev_hash,
            "event": event,
            "proposal_hash": proposal_hash,
            "trace_hash": trace_hash,
            "kernel_decision": {
                "verdict": verdict,
                "notes": notes
            },
            "witnesses": witnesses,
            "capability_tokens": capability_tokens
        }

        # Compute entry hash (hash of entry without entry_hash field)
        entry_hash = hash_json(entry_data)
        entry_data["entry_hash"] = entry_hash

        # Append to file
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(canonical_json_string(entry_data) + "\n")

        # Update chain state
        self._prev_hash = entry_hash
        self._entry_count += 1

        return entry_data

    def append_fatal_hang(self, proposal_hash: Optional[str] = None) -> dict:
        """Append a FATAL_HANG entry.

        Args:
            proposal_hash: Last known proposal hash (if any)

        Returns:
            The appended entry dict
        """
        return self.append(
            event="FATAL_HANG",
            proposal_hash=proposal_hash or GENESIS_HASH,
            trace_hash=GENESIS_HASH,
            verdict="deny",
            notes="Watchdog timeout exceeded",
            witnesses=[],
            capability_tokens=[]
        )

    def append_internal_error(self, error_message: str, proposal_hash: Optional[str] = None) -> dict:
        """Append an INTERNAL_ERROR entry.

        Args:
            error_message: Error description
            proposal_hash: Associated proposal hash (if any)

        Returns:
            The appended entry dict
        """
        return self.append(
            event="INTERNAL_ERROR",
            proposal_hash=proposal_hash or GENESIS_HASH,
            trace_hash=GENESIS_HASH,
            verdict="deny",
            notes=error_message,
            witnesses=[],
            capability_tokens=[]
        )

    @property
    def entry_count(self) -> int:
        """Get the number of entries in the log."""
        return self._entry_count


def verify_audit_log(path: Path) -> tuple[bool, Optional[str]]:
    """Verify the integrity of an audit log.

    Args:
        path: Path to the JSONL log file

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return False, f"Audit log not found: {path}"

    prev_hash = GENESIS_HASH
    entry_num = 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                entry_num += 1
                entry = json.loads(line)

                # Verify prev_entry_hash chain
                if entry.get("prev_entry_hash") != prev_hash:
                    return False, f"Entry {entry_num}: prev_entry_hash mismatch (expected {prev_hash}, got {entry.get('prev_entry_hash')})"

                # Verify entry_hash
                entry_for_hash = {k: v for k, v in entry.items() if k != "entry_hash"}
                expected_hash = hash_json(entry_for_hash)
                actual_hash = entry.get("entry_hash")

                if expected_hash != actual_hash:
                    return False, f"Entry {entry_num}: entry_hash mismatch (expected {expected_hash}, got {actual_hash})"

                prev_hash = actual_hash

        return True, None

    except json.JSONDecodeError as e:
        return False, f"Entry {entry_num}: JSON decode error: {e}"
    except Exception as e:
        return False, f"Verification error: {e}"


def read_audit_log(path: Path) -> list[dict]:
    """Read all entries from an audit log.

    Args:
        path: Path to the JSONL log file

    Returns:
        List of entry dicts
    """
    entries = []

    if not path.exists():
        return entries

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))

    return entries
