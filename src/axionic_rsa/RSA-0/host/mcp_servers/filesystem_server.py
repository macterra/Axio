"""
Filesystem ToolServer — ReadLocal, WriteLocal, AppendLocal, ListDir, SearchLocal.

All paths are resolved relative to a root directory and sandboxed to it.
Can also run as a standalone MCP server via ``python -m host.mcp_servers.filesystem_server``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import ToolDef, ToolResult, ToolServer


class FilesystemServer(ToolServer):
    name = "filesystem"

    def __init__(self, root: Path) -> None:
        super().__init__()
        self.root = root.resolve()

        self._register(ToolDef(
            name="read_file",
            description="Read a file from the workspace.",
            parameters={"path": {"type": "string"}},
        ), self._read_file)

        self._register(ToolDef(
            name="write_file",
            description="Write content to a file in the workspace.",
            parameters={"path": {"type": "string"}, "content": {"type": "string"}},
        ), self._write_file)

        self._register(ToolDef(
            name="append_file",
            description="Append content to a file in the workspace.",
            parameters={"path": {"type": "string"}, "content": {"type": "string"}},
        ), self._append_file)

        self._register(ToolDef(
            name="list_directory",
            description="List entries in a directory.",
            parameters={"path": {"type": "string"}},
        ), self._list_directory)

        self._register(ToolDef(
            name="search",
            description="Search workspace files using keyword search (BM25).",
            parameters={"query": {"type": "string"}},
        ), self._search)

    def _resolve(self, path_str: str) -> Path:
        return (self.root / path_str).resolve()

    # -- Tool handlers -------------------------------------------------------

    def _read_file(self, args: Dict[str, Any]) -> ToolResult:
        path_str = args.get("path", "")
        resolved = self._resolve(path_str)
        if not resolved.exists():
            return ToolResult(content=f"File not found: {path_str}", is_error=True)
        content = resolved.read_text(encoding="utf-8")
        return ToolResult(content=content)

    def _write_file(self, args: Dict[str, Any]) -> ToolResult:
        path_str = args.get("path", "")
        content = args.get("content", "")
        resolved = self._resolve(path_str)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return ToolResult(content=f"wrote {len(content)} chars to {path_str}")

    def _append_file(self, args: Dict[str, Any]) -> ToolResult:
        path_str = args.get("path", "")
        content = args.get("content", "")
        resolved = self._resolve(path_str)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with open(resolved, "a", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(content=f"appended {len(content)} chars to {path_str}")

    def _list_directory(self, args: Dict[str, Any]) -> ToolResult:
        path_str = args.get("path", "")
        resolved = self._resolve(path_str)
        if not resolved.exists():
            return ToolResult(content=f"Directory not found: {path_str}", is_error=True)
        if not resolved.is_dir():
            return ToolResult(content=f"Not a directory: {path_str}", is_error=True)
        entries = sorted(p.name + ("/" if p.is_dir() else "") for p in resolved.iterdir())
        return ToolResult(content="\n".join(entries))

    def _search(self, args: Dict[str, Any]) -> ToolResult:
        query = args.get("query", "")
        try:
            subprocess.run(
                ["qmd", "update"],
                capture_output=True, text=True, timeout=30,
            )
            result = subprocess.run(
                ["qmd", "search", query, "-c", "workspace", "-n", "10", "--json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return ToolResult(content=f"qmd error: {result.stderr.strip()}", is_error=True)
            return ToolResult(content=result.stdout)
        except Exception as e:
            return ToolResult(content=f"Search error: {e}", is_error=True)
