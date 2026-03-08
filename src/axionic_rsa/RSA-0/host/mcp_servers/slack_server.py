"""
Slack ToolServer — post_message, reply_thread, add_reaction.

Wraps Slack WebClient calls as MCP-compatible tools.
Can also run as a standalone MCP server.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import ToolDef, ToolResult, ToolServer


class SlackServer(ToolServer):
    name = "slack"

    def __init__(self, client: Optional[Any] = None) -> None:
        super().__init__()
        self.client = client  # slack_sdk.WebClient or None

        self._register(ToolDef(
            name="post_message",
            description="Post a message to a Slack channel.",
            parameters={
                "channel": {"type": "string"},
                "message": {"type": "string"},
            },
        ), self._post_message)

        self._register(ToolDef(
            name="reply_thread",
            description="Reply to a message in a Slack thread.",
            parameters={
                "channel": {"type": "string"},
                "thread_ts": {"type": "string"},
                "message": {"type": "string"},
            },
        ), self._reply_thread)

        self._register(ToolDef(
            name="add_reaction",
            description="Add an emoji reaction to a Slack message.",
            parameters={
                "channel": {"type": "string"},
                "timestamp": {"type": "string"},
                "emoji": {"type": "string"},
            },
        ), self._add_reaction)

    def _check_client(self) -> Optional[ToolResult]:
        if not self.client:
            return ToolResult(content="Slack client not configured", is_error=True)
        return None

    # -- Tool handlers -------------------------------------------------------

    def _post_message(self, args: Dict[str, Any]) -> ToolResult:
        err = self._check_client()
        if err:
            return err
        channel = args.get("channel", "")
        message = args.get("message", "")
        response = self.client.chat_postMessage(channel=channel, text=message)
        ts = response.get("ts", "")
        return ToolResult(content=ts)

    def _reply_thread(self, args: Dict[str, Any]) -> ToolResult:
        err = self._check_client()
        if err:
            return err
        channel = args.get("channel", "")
        thread_ts = args.get("thread_ts", "")
        message = args.get("message", "")
        response = self.client.chat_postMessage(
            channel=channel, text=message, thread_ts=thread_ts,
        )
        ts = response.get("ts", "")
        return ToolResult(content=ts)

    def _add_reaction(self, args: Dict[str, Any]) -> ToolResult:
        err = self._check_client()
        if err:
            return err
        channel = args.get("channel", "")
        timestamp = args.get("timestamp", "")
        emoji = args.get("emoji", "")
        self.client.reactions_add(channel=channel, timestamp=timestamp, name=emoji)
        return ToolResult(content=f":{emoji}:")
