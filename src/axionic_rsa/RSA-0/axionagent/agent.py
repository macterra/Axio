"""
AxionAgent — Main REPL Loop

Interactive sovereign agent: user input -> LLM proposal -> kernel admission -> warranted execution.
Supports native tool use (Anthropic/OpenAI) with text-based JSON fallback.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    ActionType,
    Author,
    CandidateBundle,
    DecisionType,
    InternalState,
    Observation,
    ObservationKind,
    SystemEvent,
    _compute_id,
    canonical_json,
)
from kernel.src.constitution import Constitution, ConstitutionError
from kernel.src.policy_core import PolicyOutput, policy_core
from host.cli.main import (
    make_budget_observation,
    make_system_observation,
    make_timestamp_observation,
)
from host.tools.executor import Executor, ExecutionEvent

from axionagent.llm_client import (
    AnthropicClient,
    LLMResponse,
    ToolCall,
    TransportError,
    MODEL_REGISTRY,
    create_client,
)
from axionagent.prompts import build_system_prompt
from axionagent.tool_defs import (
    build_candidate_from_tool_call,
    to_anthropic_tools,
    to_openai_tools,
)
from axionagent.logger import AgentCycleLog, SessionLogger
from axionagent.cycle_result import ActionResult, CycleResult, TurnResult


def _state_hash(state: InternalState) -> str:
    return hashlib.sha256(
        canonical_json(state.to_dict()).encode("utf-8")
    ).hexdigest()


def _make_user_input_observation(text: str) -> Observation:
    """User input observation with axionagent source."""
    return Observation(
        kind=ObservationKind.USER_INPUT.value,
        payload={"text": text, "source": "axionagent"},
        author=Author.USER.value,
    )


class AxionAgent:
    """Interactive sovereign agent REPL."""

    # Context-window management
    MODEL_CONTEXT_LIMIT = int(os.environ.get("MODEL_CONTEXT_LIMIT", 200_000))
    CONTEXT_SAFETY_MARGIN = 20_000  # tokens; buffer for estimation error
    KEEP_RECENT_MESSAGES = 4  # always preserve the last N messages
    CHARS_PER_TOKEN = 3  # conservative estimate (structured text ≈ 2.5-3.5)

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.agent_root = (self.repo_root / "workspace").resolve()
        self.session_id = str(uuid.uuid4())
        self.internal_state = InternalState()
        self.constitution: Optional[Constitution] = None
        self.llm_client: Optional[Any] = None
        self.system_prompt: str = ""
        self.conversation_history: List[Dict[str, Any]] = []
        self.logger: Optional[SessionLogger] = None
        self._use_tools: bool = False  # set at startup based on model registry
        self.slack_client = None  # set by slack_app.py when running as Slack bot

    def startup(self) -> bool:
        """Load constitution, init LLM client, build system prompt."""
        # Load .env from project root (Axio/)
        from dotenv import load_dotenv
        load_dotenv(self.repo_root.parent.parent.parent / ".env")

        # Load constitution
        yaml_path = (
            self.repo_root / "axionagent" / "constitution" / "axionagent.v0.2.yaml"
        )
        try:
            self.constitution = Constitution(str(yaml_path))
        except ConstitutionError as e:
            print(f"[FATAL] Constitution error: {e}")
            return False

        # Citation index self-test
        failures = self.constitution.citation_index.self_test()
        if failures:
            print(f"[FATAL] Citation index failures: {failures}")
            return False

        # Init LLM client
        model_alias = os.environ.get("LLM_MODEL", "sonnet")
        entry = MODEL_REGISTRY.get(model_alias)
        if entry:
            provider = entry["provider"]
            model = entry["model"]
            extra = {k: v for k, v in entry.items() if k not in ("provider", "model")}
            self._use_tools = extra.pop("supports_tools", "false") == "true"
        else:
            # Treat as raw model ID with provider from env
            provider = os.environ.get("LLM_PROVIDER", "anthropic")
            model = model_alias
            extra = {}
            self._use_tools = provider == "anthropic"

        self.llm_client = create_client(provider, model, **extra)
        mode = "tools" if self._use_tools else "text"
        print(f"Model: {model} ({provider}, {mode})")

        # Build system prompt
        self.system_prompt = build_system_prompt(
            self.constitution, self.repo_root, use_tools=self._use_tools
        )

        # Init logger
        self.logger = SessionLogger(
            self.repo_root / "logs" / "axionagent", self.session_id
        )

        return True

    def run(self) -> None:
        """Main REPL loop."""
        print("=" * 60)
        print("AxionAgent -- RSA-0 Sovereign Interactive Agent")
        print(f"Session: {self.session_id[:8]}...")
        print("=" * 60)

        if not self.startup():
            return

        print(f"Constitution: v{self.constitution.version} ({self.constitution.sha256[:12]}...)")
        print(f"Model: {self.llm_client.model}")
        print("Type 'exit' or 'quit' to end session.\n")

        while True:
            try:
                user_input = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[AxionAgent] Session ended.")
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("[AxionAgent] Goodbye.")
                break

            self._run_turn(user_input)

    # ------------------------------------------------------------------
    # Turn-level orchestration (auto-continue loop)
    # ------------------------------------------------------------------

    CONTINUE_PROMPT = (
        "[System: Action completed. You may continue with additional "
        "actions or respond to the user with your findings.]"
    )
    MAX_STEPS_PER_TURN = 10

    def _run_turn(
        self,
        user_input: str,
        content_blocks: Optional[List[Dict[str, Any]]] = None,
        max_steps: int = MAX_STEPS_PER_TURN,
        on_step: Optional[Any] = None,
    ) -> TurnResult:
        """Execute a full turn: one or more auto-continued cycles."""
        turn = TurnResult()

        for step in range(max_steps):
            if step == 0:
                result = self._run_cycle(user_input, content_blocks=content_blocks)
            else:
                result = self._run_cycle(self.CONTINUE_PROMPT)

            turn.steps.append(result)

            if on_step:
                on_step(step, result)

            if not self._should_auto_continue(result):
                break

        if turn.stopped_by_limit:
            print(f"\n[AxionAgent] Auto-continue limit reached ({max_steps} steps)")

        return turn

    @staticmethod
    def _should_auto_continue(result: CycleResult) -> bool:
        """Decide whether to auto-continue after a cycle."""
        if result.error:
            return False
        if result.decision_type == "ACTION":
            return True
        if result.decision_type == "REFUSE":
            return True
        return False

    # ------------------------------------------------------------------
    # Tool definitions (cached per constitution reload)
    # ------------------------------------------------------------------

    def _get_tools(self) -> Optional[List[Dict[str, Any]]]:
        """Get provider-specific tool definitions, or None for text mode."""
        if not self._use_tools:
            return None
        if isinstance(self.llm_client, AnthropicClient):
            return to_anthropic_tools(self.constitution)
        else:
            return to_openai_tools(self.constitution)

    # ------------------------------------------------------------------
    # Single cycle
    # ------------------------------------------------------------------

    def _run_cycle(
        self,
        user_input: str,
        content_blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> CycleResult:
        """Execute one complete agent cycle."""
        result = CycleResult()
        cycle = self.internal_state.cycle_index
        state_in = _state_hash(self.internal_state)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # --- 1. Build initial observations ---
        observations = [
            make_timestamp_observation(),
            _make_user_input_observation(user_input),
        ]

        # --- 2. Call LLM ---
        self.system_prompt = build_system_prompt(
            self.constitution, self.repo_root, use_tools=self._use_tools
        )

        llm_content: Any = content_blocks if content_blocks else user_input
        self.conversation_history.append({"role": "user", "content": llm_content})

        tools = self._get_tools()

        try:
            prepared = self._strip_old_images(self.conversation_history)
            prepared = self._trim_history(prepared)
            response = self.llm_client.call(
                system_message=self.system_prompt,
                messages=prepared,
                tools=tools,
            )
        except TransportError as e:
            print(f"\n[AxionAgent] LLM error: {e}")
            self.conversation_history.pop()
            result.error = str(e)
            return result

        raw_text = response.raw_text
        result.prompt_tokens = response.prompt_tokens
        result.completion_tokens = response.completion_tokens
        result.total_tokens = response.total_tokens

        # --- 3. Display prose (ungated) ---
        if response.tool_calls:
            # Tool mode: raw_text is already prose-only
            prose = raw_text.strip()
        else:
            # Text mode or prose-only response: extract prose before JSON
            prose = self._extract_prose(raw_text).strip()
        result.prose = prose
        if prose:
            print(f"\nagent> {prose}")

        # --- 4. Add assistant response to history ---
        self._append_assistant_message(response)

        # --- 5. Budget observation ---
        token_count = response.completion_tokens
        observations.append(make_budget_observation(token_count, 0, 0))

        # --- 6. Build candidates ---
        candidates: List[CandidateBundle] = []
        parse_errors = 0

        if response.tool_calls:
            # Native tool use path
            for tc in response.tool_calls:
                try:
                    candidate = build_candidate_from_tool_call(
                        tc.name,
                        tc.arguments,
                        self.constitution.version,
                    )
                    candidates.append(candidate)
                except Exception:
                    parse_errors += 1
        elif not self._use_tools:
            # Text-based JSON fallback (for providers without tool support)
            from canonicalizer.pipeline import canonicalize
            from host.cli.main import parse_llm_candidates

            canon_result = canonicalize(raw_text)
            if canon_result.success and canon_result.parsed:
                candidates, parse_errors = parse_llm_candidates(
                    canon_result.json_string or "{}",
                    self.constitution.version,
                    self.constitution.max_candidates_per_cycle(),
                )

        if candidates or parse_errors:
            observations[-1] = make_budget_observation(
                token_count, len(candidates), parse_errors
            )

        result.candidate_count = len(candidates)
        result.parse_errors = parse_errors

        # --- 7. Bind observation IDs ---
        actual_obs_ids = [o.id for o in observations]
        for candidate in candidates:
            if candidate.scope_claim and candidate.scope_claim.observation_ids:
                candidate.scope_claim.observation_ids = actual_obs_ids
                candidate.scope_claim.id = _compute_id(candidate.scope_claim.to_dict())

        # --- 8. Kernel call (only if candidates exist) ---
        decision_type = "NONE"
        execution_result: Optional[Dict[str, Any]] = None

        if candidates:
            output: PolicyOutput = policy_core(
                observations=observations,
                constitution=self.constitution,
                internal_state=self.internal_state,
                candidates=candidates,
                repo_root=self.agent_root,
            )

            decision = output.decision
            decision_type = decision.decision_type

            # --- 9. Handle decision ---
            result.decision_type = decision_type

            if decision_type == DecisionType.ACTION.value:
                # Find the matching tool call for result feedback
                tool_call = self._find_tool_call(response.tool_calls, decision.bundle)
                execution_result, result.action = self._handle_action(
                    decision, cycle, tool_call
                )

            elif decision_type == DecisionType.REFUSE.value:
                if decision.refusal:
                    result.refusal_reason = decision.refusal.reason_code
                    result.refusal_gate = decision.refusal.failed_gate
                    msg = (
                        f"Kernel REFUSE: {decision.refusal.reason_code}"
                        f" (gate: {decision.refusal.failed_gate})"
                    )
                    print(f"\n[{msg}]")
                    # Send error for the tool call so the LLM sees the refusal
                    tool_call = self._find_tool_call(response.tool_calls, decision.bundle)
                    self._inject_feedback(
                        tool_call, f"[System: {msg}]", is_error=True
                    )

            elif decision_type == DecisionType.EXIT.value:
                if decision.exit_record:
                    result.exit_reason = decision.exit_record.reason_code
                    msg = f"Kernel EXIT: {decision.exit_record.reason_code}"
                    print(f"\n[{msg}]")
                    tool_call = self._find_tool_call(response.tool_calls, decision.bundle)
                    self._inject_feedback(
                        tool_call, f"[System: {msg}]", is_error=True
                    )

        # --- 10. Advance state ---
        self.internal_state = self.internal_state.advance(
            decision_type if decision_type != "NONE" else DecisionType.REFUSE.value
        )
        state_out = _state_hash(self.internal_state)

        # --- 11. Log cycle ---
        if self.logger:
            log_entry = AgentCycleLog(
                cycle_index=cycle,
                session_id=self.session_id,
                timestamp=timestamp,
                user_input=user_input,
                raw_llm_text=raw_text,
                canonicalized_text=None,
                parsed_candidates=[c.to_dict() for c in candidates],
                observations=[o.to_dict() for o in observations],
                decision_type=decision_type,
                execution_result=execution_result,
                state_in_hash=state_in,
                state_out_hash=state_out,
                token_usage={
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens,
                },
            )
            self.logger.log_cycle(log_entry)

        return result

    # ------------------------------------------------------------------
    # Tool call / conversation history helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_tool_call(
        tool_calls: List[ToolCall],
        bundle: Optional[CandidateBundle],
    ) -> Optional[ToolCall]:
        """Find the tool call matching a selected CandidateBundle by action type."""
        if not tool_calls or not bundle:
            return None
        action_type = bundle.action_request.action_type
        for tc in tool_calls:
            if tc.name == action_type:
                return tc
        return tool_calls[0] if tool_calls else None

    def _append_assistant_message(self, response: LLMResponse) -> None:
        """Add the assistant response to conversation history in provider format."""
        if not response.tool_calls:
            # Simple text response
            self.conversation_history.append({
                "role": "assistant",
                "content": response.raw_text,
            })
            return

        if isinstance(self.llm_client, AnthropicClient):
            # Anthropic: content is a list of blocks
            content_blocks: List[Dict[str, Any]] = []
            if response.raw_text:
                content_blocks.append({"type": "text", "text": response.raw_text})
            for tc in response.tool_calls:
                content_blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            self.conversation_history.append({
                "role": "assistant",
                "content": content_blocks,
            })
        else:
            # OpenAI: tool_calls is a separate field on the message
            self.conversation_history.append({
                "role": "assistant",
                "content": response.raw_text or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in response.tool_calls
                ],
            })

    def _inject_feedback(
        self,
        tool_call: Optional[ToolCall],
        content: str,
        is_error: bool = False,
    ) -> None:
        """Inject feedback into conversation as tool result or user message."""
        if tool_call:
            self._append_tool_result(tool_call.id, tool_call.name, content, is_error)
        else:
            self.conversation_history.append({
                "role": "user",
                "content": content,
            })

    def _append_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        content: str,
        is_error: bool = False,
    ) -> None:
        """Append a tool result to conversation history in provider format."""
        if isinstance(self.llm_client, AnthropicClient):
            result_block: Dict[str, Any] = {
                "type": "tool_result",
                "tool_use_id": tool_call_id,
                "content": content,
            }
            if is_error:
                result_block["is_error"] = True
            self.conversation_history.append({
                "role": "user",
                "content": [result_block],
            })
        else:
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": content,
            })

    # ------------------------------------------------------------------
    # Action execution
    # ------------------------------------------------------------------

    def _handle_action(
        self,
        decision,
        cycle: int,
        tool_call: Optional[ToolCall] = None,
    ) -> tuple[Optional[Dict[str, Any]], Optional[ActionResult]]:
        """Execute a warranted action and display results."""
        if not decision.warrant or not decision.bundle:
            return None, None

        executor = Executor(self.agent_root, cycle, slack_client=self.slack_client)
        event = executor.execute(decision.warrant, decision.bundle)

        action_type = decision.bundle.action_request.action_type
        fields = decision.bundle.action_request.fields

        action_result = ActionResult(
            action_type=action_type,
            committed=(event.result == "committed"),
            detail=event.detail,
        )

        if event.result == "committed":
            if action_type == ActionType.READ_LOCAL.value:
                path_str = fields.get("path", "")
                resolved = (self.agent_root / path_str).resolve()
                if resolved.exists():
                    content = resolved.read_text("utf-8")
                    truncated = content[:50000]
                    print(f"\n[ReadLocal: {path_str} ({len(content)} chars)]")
                    print(truncated)
                    action_result.file_path = path_str
                    action_result.file_content = truncated
                    feedback = f"File contents of {path_str} ({len(content)} chars):\n{truncated[:10000]}"
                    self._inject_feedback(tool_call, feedback)
                else:
                    print(f"\n[ReadLocal: file not found: {path_str}]")
                    action_result.file_path = path_str
                    self._inject_feedback(
                        tool_call, f"File not found: {path_str}", is_error=True
                    )

            elif action_type == ActionType.LIST_DIR.value:
                path_str = fields.get("path", "")
                listing = event.content or ""
                print(f"\n[ListDir: {path_str}]")
                print(listing)
                action_result.file_path = path_str
                action_result.file_content = listing
                self._inject_feedback(
                    tool_call, f"Directory listing of {path_str}:\n{listing}"
                )

            elif action_type == ActionType.WRITE_LOCAL.value:
                path_str = fields.get("path", "")
                content_len = len(fields.get("content", ""))
                print(f"\n[WriteLocal: wrote {content_len} chars to {path_str}]")
                action_result.file_path = path_str
                action_result.content_length = content_len
                self._inject_feedback(
                    tool_call, f"Wrote {content_len} chars to {path_str}"
                )

            elif action_type == ActionType.APPEND_LOCAL.value:
                path_str = fields.get("path", "")
                content_len = len(fields.get("content", ""))
                print(f"\n[AppendLocal: appended {content_len} chars to {path_str}]")
                action_result.file_path = path_str
                action_result.content_length = content_len
                self._inject_feedback(
                    tool_call, f"Appended {content_len} chars to {path_str}"
                )

            elif action_type == ActionType.SEARCH_LOCAL.value:
                query = fields.get("query", "")
                results = event.content or ""
                truncated = results[:50000]
                print(f"\n[SearchLocal: '{query}' ({len(results)} chars)]")
                print(truncated[:2000])
                action_result.file_content = truncated
                self._inject_feedback(
                    tool_call, f"Search results for '{query}':\n{truncated}"
                )

            elif action_type == ActionType.FETCH_URL.value:
                url = fields.get("url", "")
                fetched = event.content or ""
                truncated = fetched[:500000]
                print(f"\n[FetchURL: {url} ({len(fetched)} chars)]")
                print(truncated[:2000])
                action_result.fetch_url = url
                action_result.fetch_content = truncated
                self._inject_feedback(
                    tool_call,
                    f"Fetched content from {url} ({len(fetched)} chars):\n{truncated[:50000]}",
                )

            elif action_type == ActionType.NOTIFY.value:
                msg = fields.get("message", "")
                print(f"\n[Notify] {msg}")
                action_result.notify_message = msg
                self._inject_feedback(tool_call, f"Notification sent: {msg}")

            elif action_type == ActionType.SLACK_POST.value:
                channel = fields.get("channel", "")
                msg_text = fields.get("message", "")
                ts = event.content or ""
                print(f"\n[SlackPost: sent to {channel}]")
                action_result.slack_channel = channel
                action_result.slack_message = msg_text
                self._inject_feedback(
                    tool_call, f"Posted to {channel} (ts={ts})"
                )

            elif action_type == ActionType.SLACK_REPLY.value:
                channel = fields.get("channel", "")
                thread_ts = fields.get("thread_ts", "")
                msg_text = fields.get("message", "")
                ts = event.content or ""
                print(f"\n[SlackReply: replied in {channel} thread {thread_ts}]")
                action_result.slack_channel = channel
                action_result.slack_message = msg_text
                action_result.slack_thread_ts = thread_ts
                self._inject_feedback(
                    tool_call, f"Replied in {channel} thread {thread_ts} (ts={ts})"
                )

            elif action_type == ActionType.SLACK_REACT.value:
                channel = fields.get("channel", "")
                timestamp = fields.get("timestamp", "")
                emoji = fields.get("emoji", "")
                print(f"\n[SlackReact: :{emoji}: in {channel}]")
                action_result.slack_channel = channel
                action_result.slack_emoji = emoji
                self._inject_feedback(
                    tool_call, f"Reacted :{emoji}: in {channel} at {timestamp}"
                )
        else:
            print(f"\n[Execution failed: {event.detail}]")
            self._inject_feedback(
                tool_call,
                f"Action {action_type} failed: {event.detail}",
                is_error=True,
            )

        return event.to_dict(), action_result

    # ------------------------------------------------------------------
    # Context-window management
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_old_images(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a copy of messages with image blocks removed from all but the last user message."""
        last_user_idx = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                last_user_idx = i
                break

        stripped = []
        for i, msg in enumerate(messages):
            content = msg.get("content")
            if i != last_user_idx and isinstance(content, list):
                # Replace image blocks with text placeholder, keep text blocks
                new_blocks = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "image":
                        new_blocks.append({"type": "text", "text": "[image previously sent]"})
                    else:
                        new_blocks.append(block)
                stripped.append({**msg, "content": new_blocks})
            else:
                stripped.append(msg)
        return stripped

    @classmethod
    def _estimate_message_tokens(cls, msg: Dict[str, Any]) -> int:
        """Conservative token estimate for a message (~3 chars per token)."""
        cpt = cls.CHARS_PER_TOKEN
        content = msg.get("content", "")
        tokens = 0

        if isinstance(content, str):
            tokens += len(content) // cpt
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    btype = block.get("type", "")
                    if btype == "image":
                        tokens += 1000
                    elif btype == "tool_result":
                        tokens += len(block.get("content", "")) // cpt
                    elif btype == "tool_use":
                        tokens += len(json.dumps(block.get("input", {}))) // cpt
                    else:
                        tokens += len(block.get("text", "")) // cpt

        # Account for tool_calls in assistant messages
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            tokens += len(fn.get("arguments", "")) // cpt
            tokens += len(fn.get("name", "")) // cpt

        # Account for role: "tool" messages
        if msg.get("role") == "tool" and isinstance(content, str):
            pass  # already counted above

        return max(tokens, 1)

    def _trim_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trim message content to fit within model context window."""
        cpt = self.CHARS_PER_TOKEN
        budget = (
            self.MODEL_CONTEXT_LIMIT
            - self.llm_client.max_tokens
            - self.CONTEXT_SAFETY_MARGIN
            - len(self.system_prompt) // cpt
        )

        total = sum(self._estimate_message_tokens(m) for m in messages)
        if total <= budget:
            return messages

        trimmed = [dict(m) for m in messages]
        protect = max(0, len(trimmed) - self.KEEP_RECENT_MESSAGES)

        # Pass 1: Truncate tool results and system-injected bulk content
        for i in range(len(trimmed)):
            if total <= budget:
                break
            msg = trimmed[i]
            content = msg.get("content", "")

            # Handle string content (text-mode system injections)
            if isinstance(content, str):
                old_tokens = len(content) // cpt
                new_content = None

                if content.startswith("[System: File read complete for "):
                    end = content.find("]")
                    path = content[len("[System: File read complete for "):end]
                    new_content = f"[System: File previously read: {path}]"
                elif content.startswith("[System: Directory listing complete for "):
                    end = content.find("]")
                    path = content[len("[System: Directory listing complete for "):end]
                    new_content = f"[System: Directory previously listed: {path}]"
                elif content.startswith("[System: URL fetch complete for "):
                    end = content.find("]")
                    url = content[len("[System: URL fetch complete for "):end]
                    new_content = f"[System: URL previously fetched: {url}]"

                if new_content:
                    trimmed[i] = {**msg, "content": new_content}
                    total -= old_tokens - len(new_content) // cpt

            # Handle tool result blocks (Anthropic format)
            elif isinstance(content, list):
                for j, block in enumerate(content):
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        block_content = block.get("content", "")
                        if len(block_content) > 500:
                            old_tokens = len(block_content) // cpt
                            summary = block_content[:200] + "\n[... trimmed ...]"
                            content[j] = {**block, "content": summary}
                            total -= old_tokens - len(summary) // cpt

            # Handle role: "tool" messages (OpenAI format)
            if msg.get("role") == "tool" and isinstance(content, str) and len(content) > 500:
                old_tokens = len(content) // cpt
                summary = content[:200] + "\n[... trimmed ...]"
                trimmed[i] = {**msg, "content": summary}
                total -= old_tokens - len(summary) // cpt

        # Pass 2: Truncate long assistant messages (oldest first, protect recent)
        for i in range(protect):
            if total <= budget:
                break
            msg = trimmed[i]
            content = msg.get("content", "")
            if not isinstance(content, str) or msg.get("role") != "assistant":
                continue
            if len(content) <= 1000:
                continue
            old_tokens = len(content) // cpt
            new_content = content[:500] + "\n[... trimmed to fit context window ...]"
            trimmed[i] = {**msg, "content": new_content}
            total -= old_tokens - len(new_content) // cpt

        # Pass 3: Truncate any remaining long user messages (oldest first, protect recent)
        for i in range(protect):
            if total <= budget:
                break
            msg = trimmed[i]
            content = msg.get("content", "")
            if not isinstance(content, str) or len(content) <= 500:
                continue
            old_tokens = len(content) // cpt
            new_content = content[:500] + "\n[... trimmed to fit context window ...]"
            trimmed[i] = {**msg, "content": new_content}
            total -= old_tokens - len(new_content) // cpt

        # Pass 4: If still over budget, drop oldest messages entirely
        if total > budget:
            while len(trimmed) > self.KEEP_RECENT_MESSAGES and total > budget:
                removed = trimmed.pop(0)
                total -= self._estimate_message_tokens(removed)

        if total > budget:
            print(f"[AxionAgent] Warning: history still over budget after trimming "
                  f"(~{total} tokens, budget ~{budget})")

        return trimmed

    @staticmethod
    def _extract_prose(text: str) -> str:
        """Extract prose portion of LLM response (before JSON block).

        Used only for text-based fallback mode.
        """
        json_start = text.find('{"')
        if json_start < 0:
            return text
        if json_start == 0:
            return ""

        prose = text[:json_start].rstrip()

        if prose.endswith("```json"):
            prose = prose[:-7].rstrip()
        elif prose.endswith("```"):
            prose = prose[:-3].rstrip()

        return prose
