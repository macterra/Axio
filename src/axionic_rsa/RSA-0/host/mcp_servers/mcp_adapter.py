"""
MCP Adapter — wraps any ToolServer as a real FastMCP server.

Usage:
    from host.mcp_servers import FilesystemServer
    from host.mcp_servers.mcp_adapter import to_fastmcp

    fs = FilesystemServer(root=Path("./workspace"))
    mcp_server = to_fastmcp(fs)
    mcp_server.run()  # starts stdio MCP server
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .base import ToolServer


def to_fastmcp(server: ToolServer) -> FastMCP:
    """Wrap a sync ToolServer as an async FastMCP server."""
    mcp = FastMCP(server.name)

    def _make_handler(tool_name: str):
        async def handler(**kwargs: Any) -> str:
            result = server.call_tool(tool_name, kwargs)
            if result.is_error:
                raise Exception(result.content)
            return result.content
        handler.__name__ = tool_name
        return handler

    for tool_def in server.list_tools():
        mcp.add_tool(
            _make_handler(tool_def.name),
            name=tool_def.name,
            description=tool_def.description,
        )

    return mcp
