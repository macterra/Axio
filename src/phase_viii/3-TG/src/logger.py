"""
TG-VIII-3 Logging Infrastructure

Trace markers, step batch envelopes, and hash chain verification
per prereg §13-14.
"""

import json
import os
from datetime import datetime
from typing import Optional, Any

from structures import KernelOutput, TraceRecord
from canonical import canonical_json, sha256_hex, compute_event_hash, compute_hash_chain_entry


class RunLogger:
    """
    Logger for VIII-3 experiment runs.

    Maintains:
    - Event log with hash chain
    - Trace markers (non-output)
    - Step batch envelopes
    """

    def __init__(self, run_id: str, output_dir: str = "logs"):
        self.run_id = run_id
        self.output_dir = output_dir
        self.log_entries: list[dict] = []
        self.trace_entries: list[dict] = []
        self.hash_chain: list[str] = []
        self.prev_hash = "0" * 64  # Genesis hash

        os.makedirs(output_dir, exist_ok=True)
        self.log_path = os.path.join(output_dir, f"{run_id}.jsonl")
        self.execution_path = os.path.join(output_dir, f"{run_id}_execution.json")

    def log_run_start(
        self,
        seed: int,
        initial_state_hash: str,
        conditions: list[str],
    ) -> None:
        """Log run initialization."""
        entry = {
            "type": "RUN_START",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "seed": seed,
            "initial_state_hash": initial_state_hash,
            "conditions": conditions,
        }
        self._append_entry(entry)

    def log_condition_marker(
        self,
        condition: str,
        marker_type: str,  # "CONDITION_START" or "CONDITION_END"
        trace_seq: int,
    ) -> None:
        """Log condition boundary marker (trace-only, no event index)."""
        marker = {
            "type": "TRACE_MARKER",
            "marker_type": marker_type,
            "condition": condition,
            "trace_seq": trace_seq,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.trace_entries.append(marker)
        # Not added to hash chain (excluded per prereg §14)

    def log_step_batch(
        self,
        step_id: int,
        inputs: list[dict],
    ) -> None:
        """Log step batch envelope (trace-only)."""
        envelope = {
            "type": "STEP_BATCH",
            "step_id": step_id,
            "inputs": inputs,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.trace_entries.append(envelope)

    def log_output(self, output: KernelOutput) -> None:
        """Log kernel output with hash chain entry."""
        entry = {
            "type": "OUTPUT",
            "output": output.to_canonical_dict(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._append_entry(entry)

        # Update hash chain
        event_bytes = canonical_json(output.to_canonical_dict()).encode('utf-8')
        event_hash = compute_hash_chain_entry(self.prev_hash, event_bytes)
        self.hash_chain.append(event_hash)
        self.prev_hash = event_hash

    def log_trace(self, trace: TraceRecord) -> None:
        """Log trace record (not in hash chain)."""
        entry = {
            "type": "TRACE",
            "trace": trace.to_canonical_dict(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.trace_entries.append(entry)

    def log_run_end(self, results: dict) -> None:
        """Log run completion with results."""
        entry = {
            "type": "RUN_END",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "results": results,
            "final_hash": self.prev_hash,
            "hash_chain_length": len(self.hash_chain),
        }
        self._append_entry(entry)
        self._write_execution_summary(results)

    def _append_entry(self, entry: dict) -> None:
        """Append entry to log."""
        self.log_entries.append(entry)
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def _write_execution_summary(self, results: dict) -> None:
        """Write complete execution summary."""
        summary = {
            "run_id": self.run_id,
            "log_entries": self.log_entries,
            "trace_entries": self.trace_entries,
            "hash_chain": self.hash_chain,
            "results": results,
        }
        with open(self.execution_path, 'w') as f:
            json.dump(summary, f, indent=2)


class ReplayVerifier:
    """
    Verifier for replay and hash chain integrity.
    """

    def __init__(self, execution_path: str):
        self.execution_path = execution_path
        self.execution_data: Optional[dict] = None

    def load(self) -> bool:
        """Load execution data."""
        try:
            with open(self.execution_path, 'r') as f:
                self.execution_data = json.load(f)
            return True
        except Exception as e:
            print(f"Failed to load execution data: {e}")
            return False

    def verify_hash_chain(self) -> tuple[bool, Optional[str]]:
        """
        Verify hash chain integrity.

        Returns (success, error_message).
        """
        if not self.load():
            return False, "Failed to load execution data"

        hash_chain = self.execution_data.get("hash_chain", [])
        log_entries = self.execution_data.get("log_entries", [])

        # Extract outputs from log entries
        outputs = [
            e["output"] for e in log_entries
            if e.get("type") == "OUTPUT"
        ]

        if len(outputs) != len(hash_chain):
            return False, f"Output count mismatch: {len(outputs)} outputs, {len(hash_chain)} hashes"

        # Recompute hash chain
        prev_hash = "0" * 64
        for i, output in enumerate(outputs):
            event_bytes = canonical_json(output).encode('utf-8')
            computed_hash = compute_hash_chain_entry(prev_hash, event_bytes)

            if computed_hash != hash_chain[i]:
                return False, f"Hash mismatch at index {i}: expected {hash_chain[i]}, got {computed_hash}"

            prev_hash = computed_hash

        return True, None
