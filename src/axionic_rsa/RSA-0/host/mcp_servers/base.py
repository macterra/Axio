"""
Base ToolServer interface — MCP-compatible tool semantics, synchronous Python.

Each ToolServer exposes a set of named tools with typed arguments.
The executor routes warranted actions to the appropriate server+tool.

Servers can also be wrapped as real MCP servers via the FastMCP adapter
for external clients (see mcp_adapter.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ToolResult:
    """Result from a tool invocation. Matches MCP CallToolResult semantics."""
    content: str = ""
    is_error: bool = False


@dataclass
class ToolDef:
    """Tool definition. Matches MCP Tool schema."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class ToolServer:
    """Base class for MCP-compatible tool servers.

    Subclasses register tools in __init__ and implement handler methods.
    The executor calls ``call_tool(name, arguments)`` to invoke them.
    """

    name: str = "unnamed"

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDef] = {}
        self._handlers: Dict[str, Any] = {}  # name -> callable(arguments) -> ToolResult

    def _register(self, tool_def: ToolDef, handler: Any) -> None:
        self._tools[tool_def.name] = tool_def
        self._handlers[tool_def.name] = handler

    def list_tools(self) -> List[ToolDef]:
        return list(self._tools.values())

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        handler = self._handlers.get(name)
        if handler is None:
            return ToolResult(content=f"Unknown tool: {name}", is_error=True)
        try:
            return handler(arguments)
        except Exception as e:
            return ToolResult(content=str(e), is_error=True)
