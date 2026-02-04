"""
GT-VIII-4 Logging and Replay Verification

Per prereg §15:
- All governance action requests
- Governance action identities
- Admissible authority sets at evaluation time
- Authority creation, expiry, and destruction events
- Conflict and deadlock transitions
- Instruction-count exhaustion events
- Authority state hashes
- Epoch transitions
"""

import json
import os
from datetime import datetime
from typing import Optional

from structures import KernelOutput, TraceRecord
from canonical import canonical_json, chain_hash, GENESIS_HASH


class RunLogger:
    """Logger for VIII-4 experiment runs."""

    def __init__(self, run_id: str, output_dir: str = "logs"):
        self.run_id = run_id
        self.output_dir = output_dir
        self.log_file = None
        self.outputs: list[KernelOutput] = []
        self.traces: list[TraceRecord] = []
        self.hash_chain: list[str] = [GENESIS_HASH]

        os.makedirs(output_dir, exist_ok=True)

        log_path = os.path.join(output_dir, f"{run_id}.jsonl")
        self.log_file = open(log_path, "w")

    def _write(self, record: dict) -> None:
        """Write a record to the log file."""
        self.log_file.write(canonical_json(record) + "\n")
        self.log_file.flush()

    def log_run_start(
        self,
        seed: int,
        initial_state_hash: str,
        conditions: list[str],
    ) -> None:
        """Log run start."""
        self._write({
            "recordType": "RUN_START",
            "timestamp": datetime.now().isoformat(),
            "runId": self.run_id,
            "seed": seed,
            "initialStateHash": initial_state_hash,
            "conditions": conditions,
        })

    def log_condition_marker(
        self,
        condition: str,
        marker: str,
        trace_seq: int,
    ) -> None:
        """Log condition start/end marker."""
        self._write({
            "recordType": "CONDITION_MARKER",
            "timestamp": datetime.now().isoformat(),
            "condition": condition,
            "marker": marker,
            "traceSeq": trace_seq,
        })

    def log_output(self, output: KernelOutput) -> None:
        """Log kernel output and update hash chain."""
        self.outputs.append(output)

        # Update hash chain per prereg §15.2
        new_hash = chain_hash(self.hash_chain[-1], output)
        self.hash_chain.append(new_hash)

        self._write({
            "recordType": "OUTPUT",
            "timestamp": datetime.now().isoformat(),
            **output.to_canonical_dict(),
            "chainHash": new_hash,
        })

    def log_trace(self, trace: TraceRecord) -> None:
        """Log trace record."""
        self.traces.append(trace)
        self._write({
            "recordType": "TRACE",
            "timestamp": datetime.now().isoformat(),
            **trace.to_canonical_dict(),
        })

    def log_criteria_result(
        self,
        criterion_id: str,
        condition: str,
        passed: bool,
        details: dict,
    ) -> None:
        """Log individual criterion result."""
        self._write({
            "recordType": "CRITERION_RESULT",
            "timestamp": datetime.now().isoformat(),
            "criterionId": criterion_id,
            "condition": condition,
            "passed": passed,
            "details": details,
        })

    def log_run_end(
        self,
        classification: str,
        final_state_hash: str,
        criteria_summary: dict,
    ) -> None:
        """Log run end."""
        self._write({
            "recordType": "RUN_END",
            "timestamp": datetime.now().isoformat(),
            "runId": self.run_id,
            "classification": classification,
            "finalStateHash": final_state_hash,
            "chainHashHead": self.hash_chain[-1],
            "criteriaSummary": criteria_summary,
        })
        self.log_file.close()

    def get_chain_hash_head(self) -> str:
        """Return current hash chain head."""
        return self.hash_chain[-1]


class ReplayVerifier:
    """Verify replay produces identical results."""

    def __init__(self, original_log_path: str):
        self.original_outputs: list[dict] = []
        self.original_chain_head: Optional[str] = None

        with open(original_log_path, "r") as f:
            for line in f:
                record = json.loads(line)
                if record.get("recordType") == "OUTPUT":
                    self.original_outputs.append(record)
                if record.get("recordType") == "RUN_END":
                    self.original_chain_head = record.get("chainHashHead")

    def verify(self, replay_outputs: list[KernelOutput], replay_chain_head: str) -> dict:
        """Verify replay matches original."""
        results = {
            "output_count_match": len(replay_outputs) == len(self.original_outputs),
            "chain_hash_match": replay_chain_head == self.original_chain_head,
            "output_mismatches": [],
        }

        for i, (orig, replay) in enumerate(zip(self.original_outputs, replay_outputs)):
            replay_dict = replay.to_canonical_dict()
            # Compare relevant fields
            if orig.get("outputType") != replay_dict.get("outputType"):
                results["output_mismatches"].append({
                    "index": i,
                    "field": "outputType",
                    "original": orig.get("outputType"),
                    "replay": replay_dict.get("outputType"),
                })
            if orig.get("stateHash") != replay_dict.get("stateHash"):
                results["output_mismatches"].append({
                    "index": i,
                    "field": "stateHash",
                    "original": orig.get("stateHash"),
                    "replay": replay_dict.get("stateHash"),
                })

        results["verified"] = (
            results["output_count_match"] and
            results["chain_hash_match"] and
            len(results["output_mismatches"]) == 0
        )

        return results
