"""
AxionAgent — Slack Frontend (Socket Mode)

Connects AxionAgent to a Slack workspace. Two interaction modes:
  - DMs: Work like the web UI. Prose auto-posted, actions execute normally.
  - Channels: Agent observes all messages but can only interact via
    warrant-gated SlackPost/SlackReply/SlackReact actions.

Runs alongside Streamlit (both frontends share a single AxionAgent instance).

Required env vars:
  SLACK_BOT_TOKEN  — xoxb-... (Bot User OAuth Token)
  SLACK_APP_TOKEN  — xapp-... (App-Level Token for Socket Mode)

Usage:
  cd src/axionic_rsa/RSA-0
  python -m axionagent.slack_app
"""

from __future__ import annotations

import base64
import logging
import os
import re
import sys
import threading
import urllib.request
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

# RSA-0 root is the parent of the axionagent/ package
RSA0_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RSA0_ROOT))


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no external dependency)."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


# Load .env before any imports that need API keys
_axio_root = RSA0_ROOT.parent.parent.parent
_load_dotenv(_axio_root / ".env")

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from axionagent.agent import AxionAgent
from axionagent.cycle_result import TurnResult

logger = logging.getLogger("axionagent.slack")


class SlackFrontend:
    """Slack frontend for AxionAgent using Socket Mode."""

    CHANNEL_BUFFER_SIZE = 50
    TURN_TIMEOUT = 120  # seconds before giving up on a stuck turn

    def __init__(self, agent: AxionAgent):
        self.agent = agent

        bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
        if not bot_token:
            raise RuntimeError("SLACK_BOT_TOKEN not set")

        self.app = App(token=bot_token)
        self.client = WebClient(token=bot_token)

        # Get our own bot user ID and bot_id for filtering self-messages
        auth = self.client.auth_test()
        self.bot_user_id = auth["user_id"]
        self.bot_id = auth.get("bot_id", "")

        # Thread safety: serialize all agent turns
        self._lock = threading.Lock()

        # Per-channel message buffer for context injection on @mentions.
        # Each entry: {"user": str, "text": str, "files": [{"url","mimetype"}]}
        self._channel_buffers: Dict[str, Deque[Dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.CHANNEL_BUFFER_SIZE)
        )

        # Wire up event handlers
        self.app.event("message")(self._handle_message)
        self.app.event("app_mention")(self._handle_app_mention)

    # ------------------------------------------------------------------
    # Image helpers
    # ------------------------------------------------------------------

    _IMAGE_MIMETYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

    def _extract_images(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Download image attachments from a Slack event.

        Returns a list of Anthropic-style image content blocks ready for
        ``_run_turn(content_blocks=...)``.
        """
        files = event.get("files") or []
        blocks: List[Dict[str, Any]] = []
        for f in files:
            mimetype = f.get("mimetype", "")
            if mimetype not in self._IMAGE_MIMETYPES:
                continue
            url = f.get("url_private_download") or f.get("url_private")
            if not url:
                continue
            try:
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": f"Bearer {self.client.token}"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read(10_000_000)  # 10 MB cap
                b64 = base64.standard_b64encode(raw).decode("ascii")
                blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mimetype,
                        "data": b64,
                    },
                })
            except Exception as e:
                logger.warning("Failed to download Slack image %s: %s", url, e)
        return blocks

    def _build_content_blocks(
        self, text: str, image_blocks: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Build multimodal content blocks if images are present.

        Returns None if there are no images (caller should pass plain text).
        """
        if not image_blocks:
            return None
        blocks = list(image_blocks)
        if text:
            blocks.append({"type": "text", "text": text})
        return blocks

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _handle_message(self, event: Dict[str, Any], say: Any) -> None:
        """Handle all message events (DMs and channels)."""
        # Ignore our own messages only (allow other bots through)
        if event.get("user") == self.bot_user_id:
            return
        if event.get("bot_id") == self.bot_id:
            return

        # Ignore message subtypes except bot_message and file_share
        subtype = event.get("subtype")
        if subtype and subtype not in ("bot_message", "file_share"):
            return

        text = event.get("text", "").strip()
        has_files = bool(event.get("files"))
        if not text and not has_files:
            return

        channel = event.get("channel", "")
        channel_type = event.get("channel_type", "")

        if channel_type == "im":
            # DM: treat like web UI (only from humans, not other bots)
            if not event.get("bot_id"):
                self._handle_dm(text, channel, event)
        else:
            # Channel message: buffer for context (no agent interaction)
            user = event.get("user") or event.get("username") or "bot"
            file_meta = []
            for f in (event.get("files") or []):
                mt = f.get("mimetype", "")
                url = f.get("url_private_download") or f.get("url_private")
                if mt in self._IMAGE_MIMETYPES and url:
                    file_meta.append({"url": url, "mimetype": mt})
            self._channel_buffers[channel].append({
                "user": user,
                "text": text,
                "files": file_meta,
            })

    def _handle_dm(
        self, text: str, channel: str, event: Dict[str, Any]
    ) -> None:
        """Process a DM like the web UI, with optional image support."""
        image_blocks = self._extract_images(event)
        ts = event.get("ts", "")
        meta = f"[Slack DM channel={channel} ts={ts}]\n"
        enriched = meta + (text or "[image]")
        content_blocks = self._build_content_blocks(enriched, image_blocks)

        if not self._lock.acquire(timeout=self.TURN_TIMEOUT):
            logger.warning("Lock timeout on DM — skipping message")
            self.client.chat_postMessage(
                channel=channel, text="_Sorry, I'm still processing a previous message. Try again shortly._"
            )
            return
        try:
            turn_result = self.agent._run_turn(
                enriched,
                content_blocks=content_blocks,
            )
            self._post_turn_result(turn_result, channel)
        except Exception as e:
            logger.exception("Error in DM turn")
            self.client.chat_postMessage(
                channel=channel, text=f"_Error: {e}_"
            )
        finally:
            self._lock.release()

    def _handle_app_mention(self, event: Dict[str, Any], say: Any) -> None:
        """Handle @mentions in channels, with optional image support."""
        # Ignore bot's own messages
        if event.get("bot_id") or event.get("user") == self.bot_user_id:
            return

        text = event.get("text", "").strip()
        channel = event.get("channel", "")
        thread_ts = event.get("thread_ts") or event.get("ts", "")

        # Strip the bot mention from the text
        text = re.sub(rf"<@{self.bot_user_id}>\s*", "", text).strip()
        if not text and not event.get("files"):
            return

        mention_images = self._extract_images(event)

        if not self._lock.acquire(timeout=self.TURN_TIMEOUT):
            logger.warning("Lock timeout on @mention — skipping")
            self.client.chat_postMessage(
                channel=channel, text="_Still processing a previous request._",
                thread_ts=thread_ts,
            )
            return
        try:
            # Build context from channel buffer (may include images)
            context_input, context_images = self._build_channel_context(
                text, channel, thread_ts
            )
            all_images = context_images + mention_images
            content_blocks = self._build_content_blocks(context_input, all_images)
            turn_result = self.agent._run_turn(
                context_input or "[image]",
                content_blocks=content_blocks,
            )
            self._post_mention_result(turn_result, channel, thread_ts)
        except Exception as e:
            logger.exception("Error in @mention turn")
            self.client.chat_postMessage(
                channel=channel, text=f"_Error: {e}_",
                thread_ts=thread_ts,
            )
        finally:
            self._lock.release()

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    def _post_turn_result(self, turn: TurnResult, channel: str) -> None:
        """Post all prose from a turn result to a DM channel."""
        for step in turn.steps:
            if step.prose:
                self.client.chat_postMessage(channel=channel, text=step.prose)

            # Log refusals/errors so user sees kernel feedback
            if step.refusal_reason:
                self.client.chat_postMessage(
                    channel=channel,
                    text=f"_Kernel REFUSE: {step.refusal_reason} (gate: {step.refusal_gate})_",
                )
            if step.error:
                self.client.chat_postMessage(
                    channel=channel,
                    text=f"_Error: {step.error}_",
                )

    def _post_mention_result(
        self, turn: TurnResult, channel: str, thread_ts: str
    ) -> None:
        """Post results from a channel @mention as thread replies.

        Only posts prose-only responses. SlackPost/SlackReply/SlackReact
        actions are handled by the executor directly.
        """
        for step in turn.steps:
            # If the step had a Slack action, the executor already posted.
            # Only auto-post prose if there was no action (pure conversation).
            if step.prose and step.decision_type in ("NONE", ""):
                self.client.chat_postMessage(
                    channel=channel,
                    text=step.prose,
                    thread_ts=thread_ts,
                )

            if step.refusal_reason:
                self.client.chat_postMessage(
                    channel=channel,
                    text=f"_Kernel REFUSE: {step.refusal_reason} (gate: {step.refusal_gate})_",
                    thread_ts=thread_ts,
                )
            if step.error:
                self.client.chat_postMessage(
                    channel=channel,
                    text=f"_Error: {step.error}_",
                    thread_ts=thread_ts,
                )

    MAX_CONTEXT_IMAGES = 5  # cap images pulled from channel history

    def _build_channel_context(
        self, mention_text: str, channel: str, thread_ts: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Build input with channel context for @mention interactions.

        Returns (context_text, image_blocks) where image_blocks are
        Anthropic-style image content blocks from recent channel messages.
        Images are downloaded lazily here (not at buffer time).
        """
        parts = []
        context_images: List[Dict[str, Any]] = []

        buffer = self._channel_buffers.get(channel)
        if buffer:
            recent = list(buffer)[-20:]  # last 20 messages
            lines = []
            for entry in recent:
                user = entry["user"]
                text = entry["text"]
                has_img = bool(entry["files"])
                suffix = " [+image]" if has_img else ""
                lines.append(f"<@{user}>: {text}{suffix}")

                # Lazily download images from context messages
                if has_img and len(context_images) < self.MAX_CONTEXT_IMAGES:
                    for fm in entry["files"]:
                        if len(context_images) >= self.MAX_CONTEXT_IMAGES:
                            break
                        try:
                            req = urllib.request.Request(
                                fm["url"],
                                headers={"Authorization": f"Bearer {self.client.token}"},
                            )
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                raw = resp.read(10_000_000)
                            b64 = base64.standard_b64encode(raw).decode("ascii")
                            context_images.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": fm["mimetype"],
                                    "data": b64,
                                },
                            })
                        except Exception as e:
                            logger.warning("Failed to download context image: %s", e)

            if lines:
                parts.append(
                    f"[Channel context — recent messages]\n" + "\n".join(lines)
                )

        parts.append(
            f"[User @mention in channel {channel}, thread_ts={thread_ts}]\n{mention_text}"
        )

        return "\n\n".join(parts), context_images

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the Socket Mode handler (blocking)."""
        app_token = os.environ.get("SLACK_APP_TOKEN", "")
        if not app_token:
            raise RuntimeError("SLACK_APP_TOKEN not set")

        handler = SocketModeHandler(self.app, app_token)
        logger.info("Starting AxionAgent Slack bot (Socket Mode)...")
        print("[SlackFrontend] Connected. Listening for messages...")
        handler.start()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    agent = AxionAgent(repo_root=RSA0_ROOT)
    if not agent.startup():
        print("[FATAL] Agent startup failed.")
        sys.exit(1)

    # Set up slack_client on the agent so executor can use it
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
    if bot_token:
        agent.slack_client = WebClient(token=bot_token)

    frontend = SlackFrontend(agent)
    frontend.start()


if __name__ == "__main__":
    main()
