"""
RSA-0 Phase X — Executor (Warrant-Gated, MCP-Based)

Executes warranted actions only. Refuses execution without valid warrant.
Routes actions to MCP-compatible ToolServers for dispatch.

Host-level actions (Notify, FetchURL, LogAppend) remain inline.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    ActionType,
    CandidateBundle,
    ExecutionWarrant,
    canonical_json,
)
from host.mcp_servers.base import ToolResult, ToolServer


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


# ---------------------------------------------------------------------------
# Action type → (server_name, tool_name) mapping
# ---------------------------------------------------------------------------

_ACTION_ROUTES: Dict[str, tuple[str, str]] = {
    ActionType.READ_LOCAL.value:    ("filesystem", "read_file"),
    ActionType.WRITE_LOCAL.value:   ("filesystem", "write_file"),
    ActionType.APPEND_LOCAL.value:  ("filesystem", "append_file"),
    ActionType.LIST_DIR.value:      ("filesystem", "list_directory"),
    ActionType.SEARCH_LOCAL.value:  ("filesystem", "search"),
    ActionType.SLACK_POST.value:    ("slack", "post_message"),
    ActionType.SLACK_REPLY.value:   ("slack", "reply_thread"),
    ActionType.SLACK_REACT.value:   ("slack", "add_reaction"),
}

# Actions that map fields directly to tool arguments
_FIELD_MAPS: Dict[str, Dict[str, str]] = {
    ActionType.READ_LOCAL.value:    {"path": "path"},
    ActionType.WRITE_LOCAL.value:   {"path": "path", "content": "content"},
    ActionType.APPEND_LOCAL.value:  {"path": "path", "content": "content"},
    ActionType.LIST_DIR.value:      {"path": "path"},
    ActionType.SEARCH_LOCAL.value:  {"query": "query"},
    ActionType.SLACK_POST.value:    {"channel": "channel", "message": "message"},
    ActionType.SLACK_REPLY.value:   {"channel": "channel", "thread_ts": "thread_ts", "message": "message"},
    ActionType.SLACK_REACT.value:   {"channel": "channel", "timestamp": "timestamp", "emoji": "emoji"},
}


class Executor:
    """
    Warrant-gated executor. Routes actions to MCP-compatible ToolServers.
    """

    def __init__(
        self,
        repo_root: Path,
        current_cycle: int,
        servers: Optional[Dict[str, ToolServer]] = None,
    ):
        self.repo_root = repo_root.resolve()
        self.current_cycle = current_cycle
        self._used_warrants: set = set()
        self.servers: Dict[str, ToolServer] = servers or {}

    def execute(
        self,
        warrant: ExecutionWarrant,
        bundle: CandidateBundle,
    ) -> ExecutionEvent:
        """
        Execute the warranted action. Returns an ExecutionEvent.
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

        ar = bundle.action_request
        try:
            # Check if this action routes to a ToolServer
            route = _ACTION_ROUTES.get(ar.action_type)
            if route:
                return self._execute_via_server(warrant, ar.action_type, ar.fields, route)

            # Host-level actions (not routed to servers)
            if ar.action_type == ActionType.NOTIFY.value:
                return self._execute_notify(warrant, ar.fields)
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

    # ------------------------------------------------------------------
    # Generic MCP server dispatch
    # ------------------------------------------------------------------

    def _execute_via_server(
        self,
        warrant: ExecutionWarrant,
        action_type: str,
        fields: Dict[str, Any],
        route: tuple[str, str],
    ) -> ExecutionEvent:
        server_name, tool_name = route
        server = self.servers.get(server_name)
        if server is None:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=action_type,
                result="failed",
                detail=f"Server '{server_name}' not configured",
            )

        # Map action fields to tool arguments
        field_map = _FIELD_MAPS.get(action_type, {})
        arguments = {tool_arg: fields.get(field_name, "") for field_name, tool_arg in field_map.items()}

        result: ToolResult = server.call_tool(tool_name, arguments)

        if result.is_error:
            return ExecutionEvent(
                warrant_id=warrant.warrant_id,
                tool=action_type,
                result="failed",
                detail=result.content,
            )

        detail = self._make_detail(action_type, fields, result)
        return ExecutionEvent(
            warrant_id=warrant.warrant_id,
            tool=action_type,
            result="committed",
            detail=detail,
            content=result.content,
        )

    @staticmethod
    def _make_detail(action_type: str, fields: Dict[str, Any], result: ToolResult) -> str:
        """Generate a human-readable detail string for the execution event."""
        if action_type == ActionType.READ_LOCAL.value:
            return f"read {len(result.content)} chars from {fields.get('path', '')}"
        elif action_type == ActionType.WRITE_LOCAL.value:
            return f"wrote {len(fields.get('content', ''))} chars to {fields.get('path', '')}"
        elif action_type == ActionType.APPEND_LOCAL.value:
            return f"appended {len(fields.get('content', ''))} chars to {fields.get('path', '')}"
        elif action_type == ActionType.LIST_DIR.value:
            n = len(result.content.splitlines()) if result.content else 0
            return f"listed {n} entries in {fields.get('path', '')}"
        elif action_type == ActionType.SEARCH_LOCAL.value:
            return f"found results for '{fields.get('query', '')}'"
        elif action_type == ActionType.SLACK_POST.value:
            return f"posted to {fields.get('channel', '')} (ts={result.content})"
        elif action_type == ActionType.SLACK_REPLY.value:
            ch = fields.get('channel', '')
            tts = fields.get('thread_ts', '')
            return f"replied in {ch} thread {tts} (ts={result.content})"
        elif action_type == ActionType.SLACK_REACT.value:
            return f"reacted {result.content} in {fields.get('channel', '')} at {fields.get('timestamp', '')}"
        return result.content

    # ------------------------------------------------------------------
    # Host-level actions (not routed to servers)
    # ------------------------------------------------------------------

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

    def _execute_fetch_url(
        self,
        warrant: ExecutionWarrant,
        fields: Dict[str, Any],
    ) -> ExecutionEvent:
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
