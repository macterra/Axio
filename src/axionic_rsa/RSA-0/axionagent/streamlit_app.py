"""
AxionAgent — Streamlit Chat UI

Run via: cd src/axionic_rsa/RSA-0 && streamlit run axionagent/streamlit_app.py
"""

import base64
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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

import streamlit as st

from axionagent.agent import AxionAgent
from axionagent.cycle_result import ActionResult, CycleResult, TurnResult


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def _init_agent() -> AxionAgent:
    """Create and start up the agent."""
    agent = AxionAgent(repo_root=RSA0_ROOT)
    if not agent.startup():
        st.error(
            "Agent startup failed. Check that ANTHROPIC_API_KEY is set "
            "and the constitution file is valid."
        )
        st.stop()
    return agent


def _init_session() -> None:
    """Initialize session state on first run."""
    if "agent" not in st.session_state:
        st.session_state.agent = _init_agent()
        st.session_state.messages = []
        st.session_state.total_tokens = 0


MODEL_ALIASES = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
}


def _handle_model_command(agent: AxionAgent, text: str) -> None:
    """Handle /model [alias|full-id]. No arg = show current."""
    parts = text.strip().split(None, 1)
    if len(parts) < 2:
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                f"Current model: `{agent.llm_client.model}`\n\n"
                f"Usage: `/model <name>`\n\n"
                f"Aliases: {', '.join(f'`{k}`' for k in MODEL_ALIASES)}"
            ),
        })
        return

    name = parts[1].strip()
    model_id = MODEL_ALIASES.get(name, name)
    agent.llm_client.model = model_id
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Switched model to `{model_id}`",
    })


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _render_action(action: ActionResult) -> None:
    """Render an executed action in the chat."""
    if not action.committed:
        st.error(f"Execution failed: {action.detail}")
        return

    if action.action_type == "ReadLocal":
        st.info(f"Read: `{action.file_path}`")
        if action.file_content:
            with st.expander(
                f"File contents ({len(action.file_content)} chars)",
                expanded=False,
            ):
                st.code(action.file_content[:10000], language="text")

    elif action.action_type == "WriteLocal":
        st.success(f"Wrote {action.content_length} chars to `{action.file_path}`")

    elif action.action_type == "AppendLocal":
        st.success(f"Appended {action.content_length} chars to `{action.file_path}`")

    elif action.action_type == "ListDir":
        st.info(f"Listed: `{action.file_path}`")
        if action.file_content:
            with st.expander(
                f"Directory listing",
                expanded=False,
            ):
                st.code(action.file_content, language="text")

    elif action.action_type == "FetchURL":
        st.info(f"Fetched: `{action.fetch_url}`")
        if action.fetch_content:
            with st.expander(
                f"Page content ({len(action.fetch_content)} chars)",
                expanded=False,
            ):
                st.code(action.fetch_content, language="text")

    elif action.action_type == "Notify":
        st.info(f"Notify: {action.notify_message}")


def _render_kernel_feedback(result: CycleResult) -> None:
    """Render kernel decision metadata below the prose."""
    if result.decision_type == "ACTION" and result.action:
        _render_action(result.action)

    elif result.decision_type == "REFUSE":
        st.warning(
            f"Kernel REFUSE: {result.refusal_reason} "
            f"(gate: {result.refusal_gate})"
        )

    elif result.decision_type == "EXIT":
        st.error(f"Kernel EXIT: {result.exit_reason}")

    # Token usage
    if result.total_tokens > 0:
        parts = [
            f"{result.prompt_tokens} in",
            f"{result.completion_tokens} out",
            f"{result.total_tokens} total",
        ]
        if result.candidate_count:
            parts.append(f"{result.candidate_count} candidate(s)")
        if result.parse_errors:
            parts.append(f"{result.parse_errors} parse error(s)")
        st.caption("Tokens: " + " | ".join(parts))


def _render_step(result: CycleResult) -> None:
    """Render a single cycle step (prose + kernel feedback)."""
    if result.prose:
        st.markdown(result.prose)
    _render_kernel_feedback(result)


def _render_message(msg: dict) -> None:
    """Render a stored message for history replay."""
    with st.chat_message(msg["role"]):
        # Show images if present
        for img in msg.get("images", []):
            st.image(img["data"], width=300)

        steps = msg.get("steps")
        if steps:
            # Multi-step turn: render each step
            for result in steps:
                _render_step(result)
        else:
            # Simple message (user or single-step legacy)
            st.markdown(msg["content"])
            meta = msg.get("meta")
            if meta:
                _render_kernel_feedback(meta)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="AxionAgent",
        page_icon="\u2693",
        layout="wide",
    )
    st.title("AxionAgent")
    st.caption("RSA-0 Sovereign Interactive Agent")

    _init_session()
    agent: AxionAgent = st.session_state.agent

    # --- Sidebar ---
    with st.sidebar:
        st.markdown(f"**Session:** `{agent.session_id[:8]}...`")
        st.markdown(f"**Constitution:** v{agent.constitution.version}")
        st.markdown(f"**Model:** {agent.llm_client.model}")
        st.divider()
        st.metric("Cycle", agent.internal_state.cycle_index)
        st.metric("Total tokens", st.session_state.total_tokens)

    # --- Conversation history ---
    for msg in st.session_state.messages:
        _render_message(msg)

    # --- Chat input ---
    chat_value = st.chat_input(
        "Message AxionAgent...",
        accept_file="multiple",
        file_type=["png", "jpg", "jpeg", "gif", "webp"],
    )
    if chat_value:
        # Extract text and files from input
        if isinstance(chat_value, str):
            user_text = chat_value
            files = []
        else:
            user_text = chat_value.text or ""
            files = chat_value.files or []

        # --- /model command ---
        if user_text.startswith("/model"):
            _handle_model_command(agent, user_text)
            st.rerun()

        # Build multimodal content blocks if images are present
        content_blocks: Optional[List[Dict[str, Any]]] = None
        image_records: List[Dict[str, Any]] = []

        if files:
            content_blocks = []
            for f in files:
                raw = f.read()
                b64 = base64.standard_b64encode(raw).decode("ascii")
                media_type = f.type or "image/png"
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": b64,
                    },
                })
                image_records.append({"data": raw, "name": f.name})
            if user_text:
                content_blocks.append({"type": "text", "text": user_text})

        # Display user message immediately
        user_msg: Dict[str, Any] = {
            "role": "user",
            "content": user_text or "[image]",
        }
        if image_records:
            user_msg["images"] = image_records
        st.session_state.messages.append(user_msg)

        with st.chat_message("user"):
            for img in image_records:
                st.image(img["data"], width=300)
            if user_text:
                st.markdown(user_text)

        # Run agent turn (auto-continue loop)
        with st.chat_message("assistant"):
            container = st.container()
            all_steps: List[CycleResult] = []

            def on_step(step_idx: int, result: CycleResult) -> None:
                """Render each step as it completes."""
                with container:
                    if result.error:
                        st.error(f"LLM Error: {result.error}")
                    else:
                        _render_step(result)

            turn_result = agent._run_turn(
                user_text or "[image]",
                content_blocks=content_blocks,
                on_step=on_step,
            )
            all_steps = turn_result.steps

            if turn_result.stopped_by_limit:
                with container:
                    st.warning(
                        f"Reached auto-continue limit "
                        f"({agent.MAX_STEPS_PER_TURN} steps)"
                    )

        # Store as single assistant message with all steps
        combined_prose = "\n\n".join(
            s.prose for s in all_steps if s.prose
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": combined_prose,
            "steps": all_steps,
        })
        st.session_state.total_tokens += turn_result.total_tokens


if __name__ == "__main__":
    main()
else:
    main()
