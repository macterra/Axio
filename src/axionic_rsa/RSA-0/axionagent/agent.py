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

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.session_id = str(uuid.uuid4())
        self.internal_state = InternalState()
        self.constitution: Optional[Constitution] = None
        self.llm_client: Optional[AnthropicClient] = None
        self.system_prompt: str = ""
        self.conversation_history: List[Dict[str, str]] = []
        self.logger: Optional[SessionLogger] = None

    def startup(self) -> bool:
        """Load constitution, init LLM client, build system prompt."""
        # Load constitution
        yaml_path = (
            self.repo_root / "axionagent" / "constitution" / "axionagent.v0.1.yaml"
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
        if not api_key:
            print("[FATAL] ANTHROPIC_API_KEY not set.")
            return False

        self.llm_client = AnthropicClient(model=model, api_key=api_key)

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

            self._run_cycle(user_input)

    def _run_cycle(self, user_input: str) -> None:
        """Execute one complete agent cycle."""
        cycle = self.internal_state.cycle_index
        state_in = _state_hash(self.internal_state)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # --- 1. Build initial observations ---
        observations = [
            make_timestamp_observation(),
            _make_user_input_observation(user_input),
        ]

        # --- 2. Call LLM ---
        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            response = self.llm_client.call(
                system_message=self.system_prompt,
                messages=self.conversation_history,
            )
        except TransportError as e:
            print(f"\n[AxionAgent] LLM error: {e}")
            self.conversation_history.pop()
            return

        raw_text = response.raw_text

        # --- 3. Display prose (ungated) ---
        prose = self._extract_prose(raw_text)
        if prose.strip():
            print(f"\nagent> {prose.strip()}")

        # Add assistant response to history
        self.conversation_history.append({"role": "assistant", "content": raw_text})

        # --- 4. Budget observation ---
        token_count = response.prompt_tokens + response.completion_tokens
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
            if decision_type == DecisionType.ACTION.value:
                execution_result = self._handle_action(decision, cycle)

            elif decision_type == DecisionType.REFUSE.value:
                if decision.refusal:
                    print(
                        f"\n[Kernel REFUSE: {decision.refusal.reason_code}"
                        f" (gate: {decision.refusal.failed_gate})]"
                    )

            elif decision_type == DecisionType.EXIT.value:
                if decision.exit_record:
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

    def _handle_action(self, decision, cycle: int) -> Optional[Dict[str, Any]]:
        """Execute a warranted action and display results."""
        if not decision.warrant or not decision.bundle:
            return None

        executor = Executor(self.repo_root, cycle)
        event = executor.execute(decision.warrant, decision.bundle)

        action_type = decision.bundle.action_request.action_type
        fields = decision.bundle.action_request.fields

        if event.result == "committed":
            if action_type == ActionType.READ_LOCAL.value:
                path_str = fields.get("path", "")
                resolved = (self.repo_root / path_str).resolve()
                if resolved.exists():
                    content = resolved.read_text("utf-8")
                    truncated = content[:50000]
                    print(f"\n[ReadLocal: {path_str} ({len(content)} chars)]")
                    print(truncated)
                    # Feed result back into conversation
                    self.conversation_history.append({
                        "role": "user",
                        "content": f"[System: File read complete for {path_str}]\n{truncated[:10000]}",
                    })
                else:
                    print(f"\n[ReadLocal: file not found: {path_str}]")

            elif action_type == ActionType.WRITE_LOCAL.value:
                path_str = fields.get("path", "")
                content_len = len(fields.get("content", ""))
                print(f"\n[WriteLocal: wrote {content_len} chars to {path_str}]")

            elif action_type == ActionType.NOTIFY.value:
                msg = fields.get("message", "")
                print(f"\n[Notify] {msg}")
        else:
            print(f"\n[Execution failed: {event.detail}]")

        return event.to_dict()

    def _extract_prose(self, text: str) -> str:
        """Extract prose portion of LLM response (before JSON block)."""
        # Find the last top-level { that starts a JSON object
        # Walk backwards to find it
        brace_depth = 0
        json_start = -1

        for i in range(len(text) - 1, -1, -1):
            if text[i] == "}":
                brace_depth += 1
            elif text[i] == "{":
                brace_depth -= 1
                if brace_depth == 0:
                    json_start = i
                    break

        if json_start <= 0:
            return text

        prose = text[:json_start].rstrip()

        # Strip trailing markdown code fence markers
        if prose.endswith("```json"):
            prose = prose[:-7].rstrip()
        elif prose.endswith("```"):
            prose = prose[:-3].rstrip()

        return prose
