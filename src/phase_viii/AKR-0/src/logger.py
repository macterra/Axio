"""
AKR-0 Logging and Replay

Implements pre/post-ordering JSONL logs, hash chain,
and replay verifier with per-event comparison.
"""

import os
import json
from dataclasses import dataclass
from typing import Any, Optional, Union

from structures import (
    EpochTickEvent,
    AuthorityInjectionEvent,
    TransformationRequestEvent,
    ActionRequestEvent,
    KernelOutput,
)
from canonical import (
    canonical_json,
    sha256_hex,
    compute_hash_chain_entry,
)


Event = Union[
    EpochTickEvent,
    AuthorityInjectionEvent,
    TransformationRequestEvent,
    ActionRequestEvent,
]


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
    AKR-0 Run Logger.

    Maintains append-only JSONL logs with hash chain.
    """

    GENESIS_HASH = "0" * 64  # All zeros for chain start

    def __init__(self, run_id: str, output_dir: str = "logs"):
        self.run_id = run_id
        self.output_dir = output_dir

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Log file paths
        self.pre_order_path = os.path.join(output_dir, f"{run_id}_pre_order.jsonl")
        self.post_order_path = os.path.join(output_dir, f"{run_id}_post_order.jsonl")
        self.execution_path = os.path.join(output_dir, f"{run_id}_execution.jsonl")
        self.summary_path = os.path.join(output_dir, f"{run_id}_summary.json")

        # Hash chain state
        self.prev_chain_hash = self.GENESIS_HASH
        self.event_index = 0

        # Clear any existing logs
        for path in [self.pre_order_path, self.post_order_path, self.execution_path]:
            if os.path.exists(path):
                os.remove(path)

    def log_run_start(self, config: Any) -> None:
        """Log run start with configuration."""
        entry = {
            "type": "RUN_START",
            "run_id": self.run_id,
            "config": {
                "condition": config.condition.value,
                "seed": config.seed,
                "epochs": config.epochs,
                "actions_per_epoch": config.actions_per_epoch,
            },
            "genesis_hash": self.GENESIS_HASH,
        }
        self._append_to_log(self.execution_path, entry)

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

        # Also write summary file
        with open(self.summary_path, 'w') as f:
            json.dump(entry, f, indent=2)

    def log_pre_order_batch(self, epoch: int, events: list[Event]) -> None:
        """Log pre-ordering batch (raw harness sequence)."""
        entry = {
            "type": "PRE_ORDER_BATCH",
            "epoch": epoch,
            "event_count": len(events),
            "events": [self._event_to_dict(e) for e in events],
        }
        self._append_to_log(self.pre_order_path, entry)

    def log_post_order_batch(self, epoch: int, events: list[Event]) -> None:
        """Log post-ordering batch (canonical sequence)."""
        entry = {
            "type": "POST_ORDER_BATCH",
            "epoch": epoch,
            "event_count": len(events),
            "events": [self._event_to_dict(e) for e in events],
        }
        self._append_to_log(self.post_order_path, entry)

    def log_event(self, event: Event, result: Any) -> None:
        """
        Log an event with its result and update hash chain.

        Per Q14:
        - eventHash = SHA256(prevEventHash || canonicalEventBytes)
        """
        self.event_index += 1

        # Get canonical event
        event_dict = self._event_to_dict(event)
        event_canonical = canonical_json(event_dict)
        event_bytes = event_canonical.encode('utf-8')

        # Compute hashes
        event_hash = sha256_hex(event_bytes)
        chain_hash = compute_hash_chain_entry(self.prev_chain_hash, event_bytes)

        # Build log entry
        entry = {
            "event_index": self.event_index,
            "event_hash": event_hash,
            "chain_hash": chain_hash,
            "prev_chain_hash": self.prev_chain_hash,
            "event": event_dict,
            "output": result.output.to_canonical_dict() if result.output else None,
            "state_hash": result.state.state_id if result.state else None,
        }

        self._append_to_log(self.execution_path, entry)

        # Update chain
        self.prev_chain_hash = chain_hash

    def log_error(self, error: str) -> None:
        """Log an error."""
        entry = {
            "type": "ERROR",
            "event_index": self.event_index,
            "error": error,
            "chain_hash": self.prev_chain_hash,
        }
        self._append_to_log(self.execution_path, entry)

    def _event_to_dict(self, event: Event) -> dict:
        """Convert event to canonical dict."""
        if hasattr(event, 'to_canonical_dict'):
            return event.to_canonical_dict()
        return {}

    def _append_to_log(self, path: str, entry: dict) -> None:
        """Append entry to JSONL log file."""
        with open(path, 'a') as f:
            f.write(json.dumps(entry, separators=(',', ':')) + '\n')


@dataclass
class DivergenceReport:
    """Report of replay divergence per Q23."""
    divergence_event_index: int
    expected_event_hash: str
    observed_event_hash: str
    expected_state_hash: str
    observed_state_hash: str
    expected_output: dict
    observed_output: dict


class ReplayVerifier:
    """
    AKR-0 Replay Verifier.

    Loads execution log and re-executes to verify bit-perfect replay.
    """

    def __init__(self, execution_log_path: str):
        self.log_path = execution_log_path
        self.entries = []
        self._load_log()

    def _load_log(self) -> None:
        """Load execution log entries."""
        with open(self.log_path, 'r') as f:
            for line in f:
                entry = json.loads(line.strip())
                self.entries.append(entry)

    def verify(self, kernel: Any) -> tuple[bool, Optional[DivergenceReport]]:
        """
        Verify replay against a fresh kernel execution.

        Returns:
            (success, divergence_report or None)
        """
        from kernel import AKRKernel
        from structures import (
            EpochTickEvent,
            AuthorityInjectionEvent,
            TransformationRequestEvent,
            ActionRequestEvent,
            AuthorityRecord,
            AuthorityStatus,
        )

        # Fresh kernel
        replay_kernel = AKRKernel()
        prev_chain_hash = RunLogger.GENESIS_HASH

        for entry in self.entries:
            # Skip non-event entries
            if "event_index" not in entry or "event" not in entry:
                continue

            # Reconstruct event from log
            event = self._reconstruct_event(entry["event"])
            if event is None:
                continue

            # Execute on replay kernel
            result = replay_kernel.process_event(event)

            # Compute hashes
            event_dict = entry["event"]
            event_canonical = canonical_json(event_dict)
            event_bytes = event_canonical.encode('utf-8')

            observed_event_hash = sha256_hex(event_bytes)
            observed_chain_hash = compute_hash_chain_entry(prev_chain_hash, event_bytes)
            observed_state_hash = result.state.state_id
            observed_output = result.output.to_canonical_dict()

            # Compare
            expected_event_hash = entry["event_hash"]
            expected_chain_hash = entry["chain_hash"]
            expected_state_hash = entry["state_hash"]
            expected_output = entry["output"]

            if (observed_event_hash != expected_event_hash or
                observed_chain_hash != expected_chain_hash or
                observed_state_hash != expected_state_hash or
                observed_output != expected_output):

                return False, DivergenceReport(
                    divergence_event_index=entry["event_index"],
                    expected_event_hash=expected_event_hash,
                    observed_event_hash=observed_event_hash,
                    expected_state_hash=expected_state_hash,
                    observed_state_hash=observed_state_hash,
                    expected_output=expected_output,
                    observed_output=observed_output,
                )

            prev_chain_hash = observed_chain_hash

        return True, None

    def _reconstruct_event(self, event_dict: dict) -> Optional[Event]:
        """Reconstruct event object from dict."""
        from structures import (
            EpochTickEvent,
            AuthorityInjectionEvent,
            TransformationRequestEvent,
            ActionRequestEvent,
            AuthorityRecord,
            AuthorityStatus,
        )

        event_type = event_dict.get("type")

        if event_type == "EPOCH_TICK":
            return EpochTickEvent(
                event_id=event_dict["eventId"],
                target_epoch=event_dict["targetEpoch"],
            )

        elif event_type == "AuthorityInjection":
            auth_dict = event_dict["authority"]
            authority = AuthorityRecord(
                authority_id=auth_dict["authorityId"],
                holder_id=auth_dict["holderId"],
                origin=auth_dict["origin"],
                scope=[tuple(e) for e in auth_dict["scope"]],
                status=AuthorityStatus(auth_dict["status"]),
                start_epoch=auth_dict["startEpoch"],
                expiry_epoch=auth_dict["expiryEpoch"],
                permitted_transformation_set=auth_dict["permittedTransformationSet"],
                conflict_set=auth_dict["conflictSet"],
            )
            return AuthorityInjectionEvent(
                epoch=event_dict["epoch"],
                event_id=event_dict["eventId"],
                authority=authority,
                nonce=event_dict.get("nonce", 0),
            )

        elif event_type == "TransformationRequest":
            return TransformationRequestEvent(
                epoch=event_dict["epoch"],
                request_id=event_dict["requestId"],
                requester_holder_id=event_dict["requesterHolderId"],
                transformation=event_dict["transformation"],
                targets=event_dict["targets"],
                nonce=event_dict.get("nonce", 0),
            )

        elif event_type == "ActionRequest":
            return ActionRequestEvent(
                epoch=event_dict["epoch"],
                request_id=event_dict["requestId"],
                requester_holder_id=event_dict["requesterHolderId"],
                action=[tuple(e) for e in event_dict["action"]],
                nonce=event_dict.get("nonce", 0),
            )

        return None


def verify_run(run_id: str, log_dir: str = "logs") -> tuple[bool, Optional[DivergenceReport]]:
    """
    Verify a completed run via replay.

    Args:
        run_id: The run identifier
        log_dir: Directory containing logs

    Returns:
        (success, divergence_report or None)
    """
    from kernel import AKRKernel

    log_path = os.path.join(log_dir, f"{run_id}_execution.jsonl")

    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Execution log not found: {log_path}")

    verifier = ReplayVerifier(log_path)
    kernel = AKRKernel()

    return verifier.verify(kernel)
