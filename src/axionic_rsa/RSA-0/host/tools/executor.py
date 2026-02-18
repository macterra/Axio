"""
RSA-0 Phase X — Executor (Sandboxed)

Executes warranted actions only. Refuses execution without valid warrant.
Implements: Notify, ReadLocal, ListDir, WriteLocal, FetchURL, LogAppend.
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
    content: Optional[str] = None  # payload for content-returning actions (FetchURL)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "event_type": "execution_event",
            "warrant_id": self.warrant_id,
            "tool": self.tool,
            "result": self.result,
            "detail": self.detail,
        }
        if self.content is not None:
            d["content_length"] = len(self.content)
        return d


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
            elif ar.action_type == ActionType.LIST_DIR.value:
                return self._execute_list_dir(warrant, ar.fields)
            elif ar.action_type == ActionType.WRITE_LOCAL.value:
                return self._execute_write_local(warrant, ar.fields)
            elif ar.action_type == ActionType.APPEND_LOCAL.value:
                return self._execute_append_local(warrant, ar.fields)
            elif ar.action_type == ActionType.FETCH_URL.value:
                return self._execute_fetch_url(warrant, ar.fields)
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

    def _execute_list_dir(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
        path_str = fields.get("path", "")
        resolved = (self.repo_root / path_str).resolve()

        if not resolved.exists():
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=ActionType.LIST_DIR.value,
                result="failed",
                detail=f"Directory not found: {resolved}",
            )

        if not resolved.is_dir():
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=ActionType.LIST_DIR.value,
                result="failed",
                detail=f"Not a directory: {resolved}",
            )

        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in resolved.iterdir())
        listing = "\n".join(entries)
        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=ActionType.LIST_DIR.value,
            result="committed",
            detail=f"listed {len(entries)} entries in {path_str}",
            content=listing,
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

    def _execute_append_local(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
        path_str = fields.get("path", "")
        content = fields.get("content", "")
        resolved = (self.repo_root / path_str).resolve()

        resolved.parent.mkdir(parents=True, exist_ok=True)
        with open(resolved, "a", encoding="utf-8") as f:
            f.write(content)

        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=ActionType.APPEND_LOCAL.value,
            result="committed",
            detail=f"appended {len(content)} chars to {path_str}",
        )

    def _execute_fetch_url(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
        import urllib.request
        import urllib.error

        url = fields.get("url", "")
        max_bytes = fields.get("max_bytes", 500000)

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AxionAgent/0.2"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read(max_bytes)
                charset = resp.headers.get_content_charset() or "utf-8"
                text = content.decode(charset, errors="replace")
        except urllib.error.URLError as e:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=ActionType.FETCH_URL.value,
                result="failed",
                detail=f"URL error: {e.reason}",
            )
        except Exception as e:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=ActionType.FETCH_URL.value,
                result="failed",
                detail=f"Fetch error: {e}",
            )

        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=ActionType.FETCH_URL.value,
            result="committed",
            detail=f"fetched {len(text)} chars from {url}",
            content=text,
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
