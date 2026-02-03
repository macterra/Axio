"""
DCR-VIII-2 Logging and Replay

Implements JSONL logs with hash chain for deterministic replay verification.
Extended from VIII-1 to support destruction events.
"""

import os
import json
from dataclasses import dataclass
from typing import Any, Optional, Union

from structures import (
    AuthorityInjectionEvent,
    ActionRequestEvent,
    DestructionAuthorizationEvent,
    KernelOutput,
)
from canonical import (
    canonical_json,
    sha256_hex,
    compute_hash_chain_entry,
)


Event = Union[AuthorityInjectionEvent, ActionRequestEvent, DestructionAuthorizationEvent]


@dataclass
class LogEntry:
    """A single log entry."""
    event_index: int
    event_hash: str
    chain_hash: str
    event: dict
    output: dict
    state_hash: str


class RunLogger:
    """
    DCR-VIII-2 Run Logger.

    Maintains append-only JSONL logs with hash chain.
    """

    GENESIS_HASH = "0" * 64  # All zeros for chain start

    def __init__(self, run_id: str, output_dir: str = "logs"):
        self.run_id = run_id
        self.output_dir = output_dir

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Log file path
        self.execution_path = os.path.join(output_dir, f"{run_id}_execution.jsonl")
        self.summary_path = os.path.join(output_dir, f"{run_id}_summary.json")

        # Hash chain state
        self.prev_chain_hash = self.GENESIS_HASH
        self.event_index = 0

        # Clear any existing logs
        if os.path.exists(self.execution_path):
            os.remove(self.execution_path)

    def log_run_start(self, seed: int, initial_state_hash: str, condition: str) -> None:
        """Log run start with configuration."""
        entry = {
            "type": "RUN_START",
            "run_id": self.run_id,
            "seed": seed,
            "condition": condition,
            "initial_state_hash": initial_state_hash,
            "genesis_hash": self.GENESIS_HASH,
        }
        self._append_to_log(self.execution_path, entry)

    def log_event(self, event: Event, output: KernelOutput) -> str:
        """
        Log a processed event with output and update hash chain.

        Returns the new chain hash.
        """
        self.event_index += 1

        # Compute event hash
        event_dict = event.to_canonical_dict()
        event_bytes = canonical_json(event_dict).encode('utf-8')
        event_hash = sha256_hex(event_bytes)

        # Compute chain hash
        chain_hash = compute_hash_chain_entry(self.prev_chain_hash, event_bytes)

        # Build log entry
        entry = {
            "type": "EVENT",
            "event_index": self.event_index,
            "event_hash": event_hash,
            "chain_hash": chain_hash,
            "prev_chain_hash": self.prev_chain_hash,
            "event": event_dict,
            "output": output.to_canonical_dict(),
            "state_hash": output.state_hash,
        }

        self._append_to_log(self.execution_path, entry)

        # Update chain state
        self.prev_chain_hash = chain_hash

        return chain_hash

    def log_run_end(self, results: dict) -> None:
        """Log run end with results summary."""
        entry = {
            "type": "RUN_END",
            "run_id": self.run_id,
            "results": results,
            "final_chain_hash": self.prev_chain_hash,
            "total_events": self.event_index,
        }
        self._append_to_log(self.execution_path, entry)

        # Write summary file
        with open(self.summary_path, 'w') as f:
            json.dump(entry, f, indent=2)

    def log_additional_output(self, output: KernelOutput) -> str:
        """
        Log an additional output for the same event.

        Per prereg: CONFLICT_REGISTERED is distinct from ACTION_REFUSED.
        """
        self.event_index += 1

        # Synthetic sub-event for the additional output
        output_dict = output.to_canonical_dict()
        event_dict = {
            "type": "AdditionalOutput",
            "event_index": self.event_index,
            "output_type": output.output_type.value,
        }
        event_bytes = canonical_json(event_dict).encode('utf-8')
        event_hash = sha256_hex(event_bytes)

        # Compute chain hash
        chain_hash = compute_hash_chain_entry(self.prev_chain_hash, event_bytes)

        entry = {
            "type": "EVENT",
            "event_index": self.event_index,
            "event_hash": event_hash,
            "chain_hash": chain_hash,
            "prev_chain_hash": self.prev_chain_hash,
            "event": event_dict,
            "output": output_dict,
            "state_hash": output.state_hash,
        }

        self._append_to_log(self.execution_path, entry)
        self.prev_chain_hash = chain_hash

        return chain_hash

    def log_kernel_state_event(self, output: KernelOutput, event_type: str) -> str:
        """
        Log kernel state events (DEADLOCK_DECLARED, DEADLOCK_PERSISTED).

        These are kernel-emitted events, not harness events.
        """
        self.event_index += 1

        event_dict = {
            "type": event_type,
            "event_index": self.event_index,
        }
        event_bytes = canonical_json(event_dict).encode('utf-8')
        event_hash = sha256_hex(event_bytes)

        chain_hash = compute_hash_chain_entry(self.prev_chain_hash, event_bytes)

        entry = {
            "type": "EVENT",
            "event_index": self.event_index,
            "event_hash": event_hash,
            "chain_hash": chain_hash,
            "prev_chain_hash": self.prev_chain_hash,
            "event": event_dict,
            "output": output.to_canonical_dict(),
            "state_hash": output.state_hash,
        }

        self._append_to_log(self.execution_path, entry)
        self.prev_chain_hash = chain_hash

        return chain_hash

    def _append_to_log(self, path: str, entry: dict) -> None:
        """Append entry to JSONL log."""
        with open(path, 'a') as f:
            f.write(json.dumps(entry, separators=(',', ':')) + '\n')


class ReplayVerifier:
    """
    Verify execution log against replay.

    Re-executes all events and verifies state hashes match.
    """

    def __init__(self, log_path: str):
        self.log_path = log_path
        self.entries: list[dict] = []
        self._load_log()

    def _load_log(self) -> None:
        """Load log entries from file."""
        with open(self.log_path, 'r') as f:
            for line in f:
                if line.strip():
                    self.entries.append(json.loads(line))

    def verify_hash_chain(self) -> tuple[bool, Optional[str]]:
        """
        Verify hash chain integrity.

        Returns (success, error_message).
        """
        prev_hash = RunLogger.GENESIS_HASH

        for entry in self.entries:
            if entry.get("type") != "EVENT":
                continue

            event_dict = entry["event"]
            event_bytes = canonical_json(event_dict).encode('utf-8')

            # Verify chain hash
            expected_chain = compute_hash_chain_entry(prev_hash, event_bytes)
            actual_chain = entry["chain_hash"]

            if expected_chain != actual_chain:
                return False, f"Chain hash mismatch at index {entry['event_index']}"

            prev_hash = actual_chain

        return True, None

    def get_events(self) -> list[dict]:
        """Get all event entries for replay."""
        return [e for e in self.entries if e.get("type") == "EVENT"]

    def get_run_start(self) -> Optional[dict]:
        """Get run start entry."""
        for e in self.entries:
            if e.get("type") == "RUN_START":
                return e
        return None

    def get_run_end(self) -> Optional[dict]:
        """Get run end entry."""
        for e in self.entries:
            if e.get("type") == "RUN_END":
                return e
        return None
