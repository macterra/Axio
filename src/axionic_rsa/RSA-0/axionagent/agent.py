"""
AxionAgent — Main REPL Loop

Interactive sovereign agent: user input -> LLM proposal -> kernel admission -> warranted execution.
"""

from __future__ import annotations

import hashlib
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
from canonicalizer.pipeline import canonicalize
from host.cli.main import (
    make_budget_observation,
    make_system_observation,
    make_timestamp_observation,
    parse_llm_candidates,
)
from host.tools.executor import Executor, ExecutionEvent

from axionagent.llm_client import AnthropicClient, LLMResponse, TransportError
from axionagent.prompts import build_system_prompt
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
        self.session_id = str(uuid.uuid4())
        self.internal_state = InternalState()
        self.constitution: Optional[Constitution] = None
        self.llm_client: Optional[AnthropicClient] = None
        self.system_prompt: str = ""
        self.conversation_history: List[Dict[str, Any]] = []
        self.logger: Optional[SessionLogger] = None

    def startup(self) -> bool:
        """Load constitution, init LLM client, build system prompt."""
        # Load .env from repo root (so Streamlit picks up tokens too)
        from dotenv import load_dotenv
        load_dotenv(self.repo_root / ".env")

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
        model = os.environ.get("LLM_MODEL", "claude-sonnet-4-20250514")
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        if not api_key and not auth_token:
            print("[FATAL] Set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN.")
            return False

        self.llm_client = AnthropicClient(
            model=model, api_key=api_key, auth_token=auth_token
        )

        # Build system prompt
        self.system_prompt = build_system_prompt(self.constitution, self.repo_root)

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
        print(f"Model: {os.environ.get('LLM_MODEL', 'claude-sonnet-4-20250514')}")
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
        """Execute a full turn: one or more auto-continued cycles.

        After each committed action, the agent automatically continues
        (up to max_steps) until it responds with pure prose, hits a
        refusal/exit/error, or the step limit is reached.

        Args:
            user_input: The user's message text.
            content_blocks: Optional multimodal content blocks (first step only).
            max_steps: Maximum cycles before stopping.
            on_step: Optional callback ``fn(step_index, cycle_result)``
                     called after each cycle completes. Useful for
                     streaming intermediate results to the UI.
        """
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
        if result.decision_type != "ACTION":
            return False
        if result.action and not result.action.committed:
            return False
        return True

    # ------------------------------------------------------------------
    # Single cycle
    # ------------------------------------------------------------------

    def _run_cycle(
        self,
        user_input: str,
        content_blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> CycleResult:
        """Execute one complete agent cycle.

        Args:
            user_input: Text from the user (used for observations and logging).
            content_blocks: Optional multimodal content blocks for the LLM.
                           When provided, these replace the plain text in the
                           message sent to the LLM (e.g. image + text).
        """
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
        # Rebuild system prompt each cycle so context file edits
        # (memory, attention, manifest) take effect immediately.
        self.system_prompt = build_system_prompt(self.constitution, self.repo_root)

        llm_content: Any = content_blocks if content_blocks else user_input
        self.conversation_history.append({"role": "user", "content": llm_content})

        try:
            prepared = self._strip_old_images(self.conversation_history)
            prepared = self._trim_history(prepared)
            response = self.llm_client.call(
                system_message=self.system_prompt,
                messages=prepared,
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
        prose = self._extract_prose(raw_text)
        result.prose = prose.strip()
        if prose.strip():
            print(f"\nagent> {prose.strip()}")

        # Add assistant response to history
        self.conversation_history.append({"role": "assistant", "content": raw_text})

        # --- 4. Budget observation ---
        # llm_output_token_count = completion tokens only (what the LLM generated),
        # not prompt tokens (input context). The kernel's budget gate compares this
        # against max_total_tokens_per_cycle from the constitution.
        token_count = response.completion_tokens
        observations.append(make_budget_observation(token_count, 0, 0))

        # --- 5. Canonicalize ---
        canon_result = canonicalize(raw_text)

        # --- 6. Parse candidates ---
        candidates: List[CandidateBundle] = []
        parse_errors = 0

        if canon_result.success and canon_result.parsed:
            candidates, parse_errors = parse_llm_candidates(
                canon_result.json_string or "{}",
                self.constitution.version,
                self.constitution.max_candidates_per_cycle(),
            )
            # Update budget observation with candidate count
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
                repo_root=self.repo_root,
            )

            decision = output.decision
            decision_type = decision.decision_type

            # --- 9. Handle decision ---
            result.decision_type = decision_type

            if decision_type == DecisionType.ACTION.value:
                execution_result, result.action = self._handle_action(decision, cycle)

            elif decision_type == DecisionType.REFUSE.value:
                if decision.refusal:
                    result.refusal_reason = decision.refusal.reason_code
                    result.refusal_gate = decision.refusal.failed_gate
                    print(
                        f"\n[Kernel REFUSE: {decision.refusal.reason_code}"
                        f" (gate: {decision.refusal.failed_gate})]"
                    )

            elif decision_type == DecisionType.EXIT.value:
                if decision.exit_record:
                    result.exit_reason = decision.exit_record.reason_code
                    print(f"\n[Kernel EXIT: {decision.exit_record.reason_code}]")

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
                canonicalized_text=canon_result.json_string if canon_result.success else None,
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

    def _handle_action(self, decision, cycle: int) -> tuple[Optional[Dict[str, Any]], Optional[ActionResult]]:
        """Execute a warranted action and display results."""
        if not decision.warrant or not decision.bundle:
            return None, None

        executor = Executor(self.repo_root, cycle)
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
                resolved = (self.repo_root / path_str).resolve()
                if resolved.exists():
                    content = resolved.read_text("utf-8")
                    truncated = content[:50000]
                    print(f"\n[ReadLocal: {path_str} ({len(content)} chars)]")
                    print(truncated)
                    action_result.file_path = path_str
                    action_result.file_content = truncated
                    # Feed result back into conversation
                    self.conversation_history.append({
                        "role": "user",
                        "content": f"[System: File read complete for {path_str}]\n{truncated[:10000]}",
                    })
                else:
                    print(f"\n[ReadLocal: file not found: {path_str}]")
                    action_result.file_path = path_str

            elif action_type == ActionType.LIST_DIR.value:
                path_str = fields.get("path", "")
                listing = event.content or ""
                print(f"\n[ListDir: {path_str}]")
                print(listing)
                action_result.file_path = path_str
                action_result.file_content = listing
                # Feed result back into conversation
                self.conversation_history.append({
                    "role": "user",
                    "content": f"[System: Directory listing complete for {path_str}]\n{listing}",
                })

            elif action_type == ActionType.WRITE_LOCAL.value:
                path_str = fields.get("path", "")
                content_len = len(fields.get("content", ""))
                print(f"\n[WriteLocal: wrote {content_len} chars to {path_str}]")
                action_result.file_path = path_str
                action_result.content_length = content_len

            elif action_type == ActionType.APPEND_LOCAL.value:
                path_str = fields.get("path", "")
                content_len = len(fields.get("content", ""))
                print(f"\n[AppendLocal: appended {content_len} chars to {path_str}]")
                action_result.file_path = path_str
                action_result.content_length = content_len

            elif action_type == ActionType.FETCH_URL.value:
                url = fields.get("url", "")
                fetched = event.content or ""
                truncated = fetched[:500000]
                print(f"\n[FetchURL: {url} ({len(fetched)} chars)]")
                print(truncated[:2000])
                action_result.fetch_url = url
                action_result.fetch_content = truncated
                # Feed result back into conversation (cap injection to avoid
                # blowing the context window on large pages)
                self.conversation_history.append({
                    "role": "user",
                    "content": f"[System: URL fetch complete for {url}]\n{truncated[:50000]}",
                })

            elif action_type == ActionType.NOTIFY.value:
                msg = fields.get("message", "")
                print(f"\n[Notify] {msg}")
                action_result.notify_message = msg
        else:
            print(f"\n[Execution failed: {event.detail}]")

        return event.to_dict(), action_result

    @staticmethod
    def _strip_old_images(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return a copy of messages with image blocks removed from all but the last user message."""
        last_user_idx = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                last_user_idx = i
                break

        stripped = []
        for i, msg in enumerate(messages):
            content = msg["content"]
            if i != last_user_idx and isinstance(content, list):
                # Replace image blocks with text placeholder, keep text blocks
                new_blocks = []
                for block in content:
                    if block.get("type") == "image":
                        new_blocks.append({"type": "text", "text": "[image previously sent]"})
                    else:
                        new_blocks.append(block)
                stripped.append({"role": msg["role"], "content": new_blocks})
            else:
                stripped.append(msg)
        return stripped

    @classmethod
    def _estimate_message_tokens(cls, msg: Dict[str, Any]) -> int:
        """Conservative token estimate for a message (~3 chars per token)."""
        cpt = cls.CHARS_PER_TOKEN
        content = msg.get("content", "")
        if isinstance(content, str):
            return len(content) // cpt
        if isinstance(content, list):
            total = 0
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "image":
                        total += 1000  # rough estimate for image tokens
                    else:
                        total += len(block.get("text", "")) // cpt
            return total
        return 0

    def _trim_history(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Trim message content to fit within model context window.

        Three passes, from least to most aggressive:
          1. Replace system-injected bulk content (file reads, URL fetches,
             directory listings) with short placeholders — in ALL messages,
             including recent ones, since these are machine-generated context.
          2. Truncate long assistant messages (oldest first, preserving recent).
          3. Truncate long user messages (oldest first, preserving recent).
        """
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

        # Pass 1: Replace system-injected bulk content in ALL messages
        # (oldest first, but not limited by protect — these are machine-
        # generated context injections, not the user's actual words)
        for i in range(len(trimmed)):
            if total <= budget:
                break
            content = trimmed[i].get("content", "")
            if not isinstance(content, str):
                continue

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
                trimmed[i] = {"role": trimmed[i]["role"], "content": new_content}
                total -= old_tokens - len(new_content) // cpt

        # Pass 2: Truncate long assistant messages (oldest first, protect recent)
        for i in range(protect):
            if total <= budget:
                break
            msg = trimmed[i]
            content = msg.get("content", "")
            if not isinstance(content, str) or msg["role"] != "assistant":
                continue
            if len(content) <= 1000:
                continue
            old_tokens = len(content) // cpt
            new_content = content[:500] + "\n[... trimmed to fit context window ...]"
            trimmed[i] = {"role": msg["role"], "content": new_content}
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
            trimmed[i] = {"role": msg["role"], "content": new_content}
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

        Finds the first `{"` which marks the start of a JSON object.
        This is simpler and more robust than brace-depth counting,
        which fails when the LLM drops a closing brace.
        """
        json_start = text.find('{"')
        if json_start <= 0:
            return text

        prose = text[:json_start].rstrip()

        # Strip trailing markdown code fence markers
        if prose.endswith("```json"):
            prose = prose[:-7].rstrip()
        elif prose.endswith("```"):
            prose = prose[:-3].rstrip()

        return prose
