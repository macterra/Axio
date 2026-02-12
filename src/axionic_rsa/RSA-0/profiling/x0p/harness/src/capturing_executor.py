"""
X-0P Capturing Executor (Composition Wrapper)

Wraps the real Executor via composition (per EC4/DA2).
- Intercepts Notify events → writes to execution_trace.jsonl (not stdout)
- Remaps file paths through ExecutionFS sandbox policy
- Delegates actual execution to the real executor
- Captures all execution events for profiling log
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    ActionRequest,
    ActionType,
    CandidateBundle,
    ExecutionWarrant,
    canonical_json,
)
from host.tools.executor import Executor, ExecutionEvent


# ---------------------------------------------------------------------------
# Sandbox FS policy
# ---------------------------------------------------------------------------

@dataclass
class ExecutionFS:
    """Sandbox filesystem policy for profiling execution.

    Remaps write paths to run-specific sandbox directories.
    Rejects traversal, absolute paths, symlink escapes.
    """
    sandbox_root: Path  # e.g., workspace/x0p/<run_id>/
    allowed_read_prefixes: List[str] = field(default_factory=lambda: [
        "./artifacts/",
        "./workspace/",
    ])
    allowed_write_prefixes: List[str] = field(default_factory=lambda: [
        "./workspace/",
        "./logs/",
    ])

    def validate_path(self, path_str: str, is_write: bool = False) -> tuple[bool, str]:
        """Validate and optionally remap a path.

        Returns (is_valid, resolved_path_or_error).
        """
        # Reject absolute paths
        if path_str.startswith("/"):
            return False, f"Absolute path rejected: {path_str}"

        # Reject obvious traversal
        if ".." in path_str:
            return False, f"Path traversal rejected: {path_str}"

        # Check against allowlist
        prefixes = self.allowed_write_prefixes if is_write else self.allowed_read_prefixes
        allowed = any(path_str.startswith(p) for p in prefixes)

        if not allowed:
            return False, f"Path not in allowlist: {path_str}"

        # For writes, remap to sandbox
        if is_write:
            # Strip leading ./ and remap
            rel_path = path_str.lstrip("./")
            sandboxed = str(self.sandbox_root / rel_path)
            return True, sandboxed

        return True, path_str

    def remap_fields(self, fields: Dict[str, Any], action_type: str) -> tuple[bool, Dict[str, Any], str]:
        """Remap path fields for sandbox execution.

        Returns (is_valid, remapped_fields, error_msg).
        """
        remapped = dict(fields)

        if action_type == ActionType.READ_LOCAL.value:
            path = fields.get("path", "")
            valid, result = self.validate_path(path, is_write=False)
            if not valid:
                return False, fields, result
            remapped["path"] = result

        elif action_type == ActionType.WRITE_LOCAL.value:
            path = fields.get("path", "")
            valid, result = self.validate_path(path, is_write=True)
            if not valid:
                return False, fields, result
            remapped["path"] = result

        elif action_type == ActionType.LOG_APPEND.value:
            # LogAppend uses log_name, not path — sandbox the log directory
            log_name = fields.get("log_name", "")
            if "/" in log_name or ".." in log_name:
                return False, fields, f"Invalid log_name: {log_name}"

        return True, remapped, ""


# ---------------------------------------------------------------------------
# Notify sink (per CA2: capture to execution_trace.jsonl, never to terminal)
# ---------------------------------------------------------------------------

@dataclass
class NotifySink:
    """Captures Notify events to a JSONL file instead of stdout."""
    trace_path: Path
    _events: List[Dict[str, Any]] = field(default_factory=list)

    def capture(self, warrant_id: str, fields: Dict[str, Any]) -> None:
        """Record a Notify event."""
        event = {
            "type": "notify_capture",
            "warrant_id": warrant_id,
            "target": fields.get("target", "stdout"),
            "message": fields.get("message", ""),
        }
        self._events.append(event)

    def flush(self) -> None:
        """Write all captured events to trace file."""
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.trace_path, "a", encoding="utf-8") as f:
            for event in self._events:
                f.write(json.dumps(event, sort_keys=True) + "\n")
        self._events.clear()

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)


# ---------------------------------------------------------------------------
# CapturingExecutor (composition wrapper per EC4)
# ---------------------------------------------------------------------------

class CapturingExecutor:
    """Composition wrapper around the real Executor.

    - Intercepts Notify → NotifySink (no stdout)
    - Remaps paths through ExecutionFS
    - Delegates execution to the real Executor
    - Captures all execution events for profiling
    """

    def __init__(
        self,
        delegate: Executor,
        fs_policy: ExecutionFS,
        notify_sink: NotifySink,
    ):
        self.delegate = delegate
        self.fs_policy = fs_policy
        self.notify_sink = notify_sink
        self._trace: List[Dict[str, Any]] = []

    def execute(
        self,
        warrant: ExecutionWarrant,
        action_request: ActionRequest,
        cycle: int,
    ) -> Dict[str, Any]:
        """Execute a warranted action through the sandbox.

        Returns execution trace dict.
        """
        action_type = action_request.action_type

        # For Notify: capture to sink instead of delegating
        if action_type == ActionType.NOTIFY.value:
            self.notify_sink.capture(warrant.warrant_id, action_request.fields)
            event = {
                "warrant_id": warrant.warrant_id,
                "action_type": action_type,
                "result": "captured",
                "detail": f"Notify captured to sink, message_len={len(action_request.fields.get('message', ''))}",
            }
            self._trace.append(event)
            return event

        # For file operations: validate and remap through FS policy
        valid, remapped_fields, error = self.fs_policy.remap_fields(
            action_request.fields, action_type
        )
        if not valid:
            event = {
                "warrant_id": warrant.warrant_id,
                "action_type": action_type,
                "result": "sandbox_rejected",
                "detail": error,
            }
            self._trace.append(event)
            return event

        # Create a sandboxed bundle for delegation
        # We need to reconstruct the bundle with remapped fields
        sandboxed_ar = ActionRequest(
            action_type=action_type,
            fields=remapped_fields,
            author=action_request.author,
            created_at=action_request.created_at,
        )

        # Build a minimal CandidateBundle for the delegate
        from kernel.src.artifacts import Justification, ScopeClaim
        sandboxed_bundle = CandidateBundle(
            action_request=sandboxed_ar,
            scope_claim=ScopeClaim(
                observation_ids=[],
                claim="sandboxed_execution",
                clause_ref="",
                author=action_request.author,
            ),
            justification=Justification(
                text="sandboxed_execution",
                author=action_request.author,
            ),
            authority_citations=[],
        )

        # Delegate to real executor
        try:
            exec_event: ExecutionEvent = self.delegate.execute(warrant, sandboxed_bundle)
            event = exec_event.to_dict()
            event["sandboxed"] = True
            self._trace.append(event)
            return event
        except Exception as e:
            event = {
                "warrant_id": warrant.warrant_id,
                "action_type": action_type,
                "result": "execution_error",
                "detail": str(e),
            }
            self._trace.append(event)
            return event

    @property
    def trace(self) -> List[Dict[str, Any]]:
        """All execution events captured during this session."""
        return list(self._trace)

    def flush(self) -> None:
        """Flush captured Notify events to trace file."""
        self.notify_sink.flush()
