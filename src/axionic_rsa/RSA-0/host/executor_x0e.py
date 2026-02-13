"""
RSA-0 X-0E — Executor (Notify Only)

Executes warranted Notify actions by appending to outbox.jsonl.
All other action types are refused.

Enforces:
  - Warrant required (single-use)
  - Destination idempotency (check outbox before write)
  - Execution outcome logging (SUCCESS / FAILURE)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Set

from kernel.src.artifacts import (
    ActionType,
    CandidateBundle,
    ExecutionWarrant,
)
from kernel.src.canonical import canonical_str
from host.log_io import append_jsonl, extract_warrant_ids


class ExecutorX0E:
    """X-0E warrant-gated executor.  Notify only."""

    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.outbox_path = log_dir / "outbox.jsonl"
        self.execution_trace_path = log_dir / "execution_trace.jsonl"
        self.reconciliation_trace_path = log_dir / "reconciliation_trace.jsonl"
        self._used_warrants: Set[str] = set()
        # Load effected warrants from outbox for idempotency
        self._effected_warrants: Set[str] = extract_warrant_ids(self.outbox_path)

    # ------------------------------------------------------------------
    # Startup reconciliation (spec §6.2 / instructions §6.2)
    # ------------------------------------------------------------------

    def startup_reconciliation(self) -> None:
        """Reconcile outbox vs execution_trace before first new cycle.

        For each warrant_id in outbox but NOT in execution_trace,
        append a synthetic SUCCESS entry to execution_trace and
        a reconciliation_trace entry.
        """
        executed = extract_warrant_ids(self.execution_trace_path)
        effected = extract_warrant_ids(self.outbox_path)

        orphans = effected - executed
        for wid in sorted(orphans):  # sorted for determinism
            # Synthetic execution_trace entry
            exec_record = {
                "warrant_id": wid,
                "cycle_id": -1,  # unknown — reconciled
                "execution_status": "SUCCESS",
                "reason": "RECONCILED_FROM_DESTINATION",
            }
            append_jsonl(self.execution_trace_path, exec_record)

            # Advisory reconciliation trace
            recon_record = {
                "warrant_id": wid,
                "action": "RECONCILED_FROM_DESTINATION",
            }
            append_jsonl(self.reconciliation_trace_path, recon_record)

        # Mark reconciled warrants as used
        self._used_warrants.update(orphans)
        self._used_warrants.update(executed)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        warrant: ExecutionWarrant,
        bundle: CandidateBundle,
        cycle_id: int,
        timestamp: str,
    ) -> Dict[str, Any]:
        """Execute a warranted action.  Returns execution trace record.

        Only Notify is permitted.  All else is refused.
        """
        wid = warrant.warrant_id

        # --- Refuse non-Notify ---
        if warrant.action_type != ActionType.NOTIFY.value:
            record = {
                "warrant_id": wid,
                "cycle_id": cycle_id,
                "execution_status": "FAILURE",
                "failure_reason": f"ACTION_TYPE_REFUSED: {warrant.action_type}",
                "timestamp": timestamp,
            }
            append_jsonl(self.execution_trace_path, record)
            return record

        # --- Single-use check ---
        if wid in self._used_warrants:
            record = {
                "warrant_id": wid,
                "cycle_id": cycle_id,
                "execution_status": "FAILURE",
                "failure_reason": "DUPLICATE_WARRANT_REFUSED",
                "timestamp": timestamp,
            }
            append_jsonl(self.execution_trace_path, record)
            return record

        # --- Destination idempotency: check outbox ---
        if wid in self._effected_warrants:
            record = {
                "warrant_id": wid,
                "cycle_id": cycle_id,
                "execution_status": "FAILURE",
                "failure_reason": "DUPLICATE_WARRANT_REFUSED",
                "timestamp": timestamp,
            }
            append_jsonl(self.execution_trace_path, record)
            return record

        # --- Execute Notify: append to outbox ---
        from kernel.src.hashing import content_hash

        message = bundle.action_request.fields.get("message", "")
        outbox_record = {
            "warrant_id": wid,
            "cycle_id": cycle_id,
            "artifact_id": bundle.action_request.id,
            "payload_hash": content_hash({"message": message}),
            "message": message,
            "timestamp": timestamp,
        }

        try:
            append_jsonl(self.outbox_path, outbox_record)
            self._effected_warrants.add(wid)
            self._used_warrants.add(wid)

            exec_record = {
                "warrant_id": wid,
                "cycle_id": cycle_id,
                "execution_status": "SUCCESS",
                "timestamp": timestamp,
            }
            append_jsonl(self.execution_trace_path, exec_record)
            return exec_record

        except Exception as e:
            exec_record = {
                "warrant_id": wid,
                "cycle_id": cycle_id,
                "execution_status": "FAILURE",
                "failure_reason": str(e),
                "timestamp": timestamp,
            }
            append_jsonl(self.execution_trace_path, exec_record)
            return exec_record
