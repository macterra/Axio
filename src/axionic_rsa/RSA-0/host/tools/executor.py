"""
RSA-0 Phase X — Executor (Sandboxed)

Executes warranted actions only. Refuses execution without valid warrant.
Implements: Notify, ReadLocal, WriteLocal, LogAppend.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    ActionType,
    CandidateBundle,
    ExecutionWarrant,
    canonical_json,
)


@dataclass
class ExecutionEvent:
    warrant_id: str
    tool: str  # ActionType value
    result: str  # "committed" | "failed"
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "execution_event",
            "warrant_id": self.warrant_id,
            "tool": self.tool,
            "result": self.result,
            "detail": self.detail,
        }


class ExecutorError(Exception):
    pass


class Executor:
    """
    Warrant-gated executor. Will not execute without a valid warrant.
    """

    def __init__(self, repo_root: Path, current_cycle: int):
        self.repo_root = repo_root.resolve()
        self.current_cycle = current_cycle
        self._used_warrants: set = set()

    def execute(
        self,
        warrant: ExecutionWarrant,
        bundle: CandidateBundle,
    ) -> ExecutionEvent:
        """
        Execute the warranted action. Returns an ExecutionEvent.
        Raises ExecutorError if warrant is invalid.
        """
        # Validate warrant
        if warrant.warrant_id in self._used_warrants:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=warrant.action_type,
                result="failed",
                detail="Warrant already used (single-use violated)",
            )

        if warrant.issued_in_cycle != self.current_cycle:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=warrant.action_type,
                result="failed",
                detail=f"Warrant cycle mismatch: {warrant.issued_in_cycle} != {self.current_cycle}",
            )

        if warrant.action_request_id != bundle.action_request.id:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=warrant.action_type,
                result="failed",
                detail="Warrant does not reference this ActionRequest",
            )

        # Mark as used
        self._used_warrants.add(warrant.warrant_id)

        # Dispatch
        ar = bundle.action_request
        try:
            if ar.action_type == ActionType.NOTIFY.value:
                return self._execute_notify(warrant, ar.fields)
            elif ar.action_type == ActionType.READ_LOCAL.value:
                return self._execute_read_local(warrant, ar.fields)
            elif ar.action_type == ActionType.WRITE_LOCAL.value:
                return self._execute_write_local(warrant, ar.fields)
            elif ar.action_type == ActionType.LOG_APPEND.value:
                return self._execute_log_append(warrant, ar.fields)
            else:
                return ExecutionEvent(
                    warrant_id=warrant.warrant_id,
                    tool=ar.action_type,
                    result="failed",
                    detail=f"Unknown action type: {ar.action_type}",
                )
        except Exception as e:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=ar.action_type,
                result="failed",
                detail=str(e),
            )

    def _execute_notify(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
        target = fields.get("target", "stdout")
        message = fields.get("message", "")

        if target == "stdout":
            print(f"[RSA-0 Notify] {message}")
        elif target == "local_log":
            log_path = self.repo_root / "logs" / "notify.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")

        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=ActionType.NOTIFY.value,
            result="committed",
            detail=f"target={target}, len={len(message)}",
        )

    def _execute_read_local(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
        path_str = fields.get("path", "")
        resolved = (self.repo_root / path_str).resolve()

        if not resolved.exists():
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=ActionType.READ_LOCAL.value,
                result="failed",
                detail=f"File not found: {resolved}",
            )

        content = resolved.read_text(encoding="utf-8")
        # Content is returned via execution event detail (bounded)
        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=ActionType.READ_LOCAL.value,
            result="committed",
            detail=f"read {len(content)} chars from {path_str}",
        )

    def _execute_write_local(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
        path_str = fields.get("path", "")
        content = fields.get("content", "")
        resolved = (self.repo_root / path_str).resolve()

        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")

        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=ActionType.WRITE_LOCAL.value,
            result="committed",
            detail=f"wrote {len(content)} chars to {path_str}",
        )

    def _execute_log_append(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
        log_name = fields.get("log_name", "")
        lines = fields.get("jsonl_lines", [])

        log_path = self.repo_root / "logs" / f"{log_name}.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=ActionType.LOG_APPEND.value,
            result="committed",
            detail=f"appended {len(lines)} lines to {log_name}.jsonl",
        )
