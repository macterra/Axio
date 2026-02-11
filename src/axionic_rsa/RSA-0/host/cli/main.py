"""
RSA-0 Phase X — Host CLI

Outer loop: collects observations, optionally calls LLM (or uses stubs),
parses candidates, invokes kernel, executes warrants, logs via LogAppend.
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    DecisionType,
    ExitReasonCode,
    InternalState,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    SystemEvent,
)
from kernel.src.constitution import Constitution, ConstitutionError
from kernel.src.policy_core import PolicyOutput, policy_core, issue_log_append_warrants
from kernel.src.telemetry import build_log_append_bundles, derive_telemetry
from host.tools.executor import ExecutionEvent, Executor


def make_timestamp_observation() -> Observation:
    return Observation(
        kind=ObservationKind.TIMESTAMP.value,
        payload={
            "iso8601_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        author=Author.HOST.value,
    )


def make_user_input_observation(text: str) -> Observation:
    return Observation(
        kind=ObservationKind.USER_INPUT.value,
        payload={"text": text, "source": "cli"},
        author=Author.USER.value,
    )


def make_system_observation(event: str, detail: str = "") -> Observation:
    """
    TRUST BOUNDARY: System observations are the host's internal integrity
    channel. They can trigger EXIT (e.g., startup_integrity_fail).

    TRUST CLASSIFICATION: This channel is TRUSTED-BY-CONSTRUCTION in RSA-0.
    The host is trusted for integrity reporting but NOT trusted for execution
    authority. The kernel accepts system observations at face value but they
    alone cannot cause side effects — only warrants can.

    This function must ONLY be called by host-level integrity verification
    code (startup, citation self-test, executor audit). It must NEVER be
    called with values derived from user input or LLM output.

    User input → make_user_input_observation()
    LLM output → parse_llm_candidates()
    Host checks → make_system_observation()   ← this function
    """
    return Observation(
        kind=ObservationKind.SYSTEM.value,
        payload={"event": event, "detail": detail},
        author=Author.HOST.value,
    )


def make_budget_observation(
    token_count: int = 0,
    candidates_reported: int = 0,
    parse_errors: int = 0,
) -> Observation:
    return Observation(
        kind=ObservationKind.BUDGET.value,
        payload={
            "llm_output_token_count": token_count,
            "llm_candidates_reported": candidates_reported,
            "llm_parse_errors": parse_errors,
        },
        author=Author.HOST.value,
    )


def build_host_notify_candidate(
    message: str,
    target: str,
    observation_ids: List[str],
    constitution_version: str,
) -> CandidateBundle:
    """Build a host-constructed Notify candidate."""
    ar = ActionRequest(
        action_type=ActionType.NOTIFY.value,
        fields={"target": target, "message": message},
        author=Author.HOST.value,
    )
    sc = ScopeClaim(
        observation_ids=observation_ids,
        claim=f"User input warrants notification via {target}",
        clause_ref=f"constitution:v{constitution_version}@/action_space/action_types/0",
        author=Author.HOST.value,
    )
    just = Justification(
        text=f"Responding to user input with Notify({target})",
        author=Author.HOST.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[
            f"constitution:v{constitution_version}#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            f"constitution:v{constitution_version}#INV-AUTHORITY-CITED",
        ],
    )


def build_host_exit_candidate(
    reason: str,
    observation_ids: List[str],
    constitution_version: str,
) -> CandidateBundle:
    """Build a host-constructed Exit candidate (EXIT is a Decision, not warranted,
    but we model the request for the kernel to decide)."""
    ar = ActionRequest(
        action_type=ActionType.EXIT.value,
        fields={"reason_code": ExitReasonCode.USER_REQUESTED.value},
        author=Author.HOST.value,
    )
    sc = ScopeClaim(
        observation_ids=observation_ids,
        claim="User requested exit",
        clause_ref=f"constitution:v{constitution_version}@/exit_policy",
        author=Author.HOST.value,
    )
    just = Justification(
        text=f"User requested exit: {reason}",
        author=Author.HOST.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[
            f"constitution:v{constitution_version}@/exit_policy/exit_permitted",
        ],
    )


def parse_llm_candidates(
    raw_json: str,
    constitution_version: str,
    max_candidates: int,
) -> tuple[List[CandidateBundle], int]:
    """
    Parse LLM output JSON into candidate bundles.
    Returns (bundles, parse_error_count).
    """
    bundles: List[CandidateBundle] = []
    parse_errors = 0

    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return [], 1

    raw_candidates = data.get("candidates", [])
    if not isinstance(raw_candidates, list):
        return [], 1

    for i, raw in enumerate(raw_candidates):
        if len(bundles) + parse_errors >= max_candidates:
            # Remaining are budget-exceeded (still count)
            break
        try:
            bundle = _parse_single_candidate(raw, constitution_version)
            bundles.append(bundle)
        except Exception:
            parse_errors += 1

    return bundles, parse_errors


def _parse_single_candidate(raw: Dict[str, Any], constitution_version: str) -> CandidateBundle:
    """Parse a single candidate bundle from LLM JSON."""
    raw_ar = raw["action_request"]
    ar = ActionRequest(
        action_type=raw_ar["action_type"],
        fields=raw_ar.get("fields", {}),
        author=Author.REFLECTION.value,
    )

    sc = None
    if "scope_claim" in raw and raw["scope_claim"]:
        raw_sc = raw["scope_claim"]
        sc = ScopeClaim(
            observation_ids=raw_sc.get("observation_ids", []),
            claim=raw_sc.get("claim", ""),
            clause_ref=raw_sc.get("clause_ref", ""),
            author=Author.REFLECTION.value,
        )

    just = None
    if "justification" in raw and raw["justification"]:
        raw_j = raw["justification"]
        just = Justification(
            text=raw_j.get("text", ""),
            author=Author.REFLECTION.value,
        )

    citations = raw.get("authority_citations", [])

    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=citations,
    )


class RSAHost:
    """
    Main host loop for RSA-0.
    """

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root).resolve()
        self.run_id = str(uuid.uuid4())
        self.internal_state = InternalState()
        self.constitution: Optional[Constitution] = None
        self._execution_events: List[ExecutionEvent] = []

    def startup(self) -> List[Observation]:
        """
        Load constitution, verify integrity, build citation index.
        Returns startup observations for cycle 0.
        """
        observations: List[Observation] = []
        observations.append(make_timestamp_observation())

        # Load constitution
        yaml_path = (
            self.repo_root
            / "artifacts"
            / "phase-x"
            / "constitution"
            / "rsa_constitution.v0.1.1.yaml"
        )
        try:
            self.constitution = Constitution(str(yaml_path))
            observations.append(make_system_observation(
                SystemEvent.STARTUP_INTEGRITY_OK.value,
                f"Constitution hash verified: {self.constitution.sha256}",
            ))
        except ConstitutionError as e:
            observations.append(make_system_observation(
                SystemEvent.STARTUP_INTEGRITY_FAIL.value,
                str(e),
            ))
            return observations

        # Citation index self-test
        failures = self.constitution.citation_index.self_test()
        if failures:
            observations.append(make_system_observation(
                SystemEvent.CITATION_INDEX_FAIL.value,
                "; ".join(failures),
            ))
        else:
            observations.append(make_system_observation(
                SystemEvent.CITATION_INDEX_OK.value,
                f"Citation index OK: {len(self.constitution.citation_index.all_ids())} IDs indexed",
            ))

        return observations

    def run_cycle(
        self,
        observations: List[Observation],
        candidates: List[CandidateBundle],
    ) -> PolicyOutput:
        """Run a single kernel cycle."""
        assert self.constitution is not None

        output = policy_core(
            observations=observations,
            constitution=self.constitution,
            internal_state=self.internal_state,
            candidates=candidates,
            repo_root=self.repo_root,
        )

        return output

    def execute_decision(self, output: PolicyOutput) -> List[ExecutionEvent]:
        """Execute the decision's warranted action (if ACTION)."""
        events: List[ExecutionEvent] = []

        if (
            output.decision.decision_type == DecisionType.ACTION.value
            and output.decision.warrant is not None
            and output.decision.bundle is not None
        ):
            executor = Executor(self.repo_root, self.internal_state.cycle_index)
            event = executor.execute(output.decision.warrant, output.decision.bundle)
            events.append(event)

        return events

    def execute_log_appends(
        self,
        log_intents_bundles: List[CandidateBundle],
        observations: List[Observation],
    ) -> List[ExecutionEvent]:
        """Request kernel-issued warrants for LogAppend, then execute."""
        assert self.constitution is not None
        events: List[ExecutionEvent] = []

        # Warrants issued by the kernel, not the host (INV-1 compliance)
        warrant_results = issue_log_append_warrants(
            log_bundles=log_intents_bundles,
            observations=observations,
            constitution=self.constitution,
            cycle_index=self.internal_state.cycle_index,
            repo_root=self.repo_root,
        )

        executor = Executor(self.repo_root, self.internal_state.cycle_index)

        for wr in warrant_results:
            if wr.admitted and wr.warrant is not None:
                event = executor.execute(wr.warrant, wr.bundle)
                events.append(event)

        return events

    def run(self) -> None:
        """Main CLI loop."""
        print("=" * 60)
        print("RSA-0 Phase X — Reflective Sovereign Agent")
        print("=" * 60)

        # Startup (cycle 0)
        startup_obs = self.startup()

        if self.constitution is None:
            print("[FATAL] Constitution failed to load. Exiting.")
            return

        # Cycle 0: startup observations, no user candidates
        self._run_single_cycle(startup_obs, [])

        if self.internal_state.last_decision == DecisionType.EXIT.value:
            return

        # Main loop: cycles 1+
        while True:
            try:
                user_input = input("\n[RSA-0] > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[RSA-0] EOF/interrupt — exiting.")
                break

            if not user_input:
                continue

            observations = [make_timestamp_observation()]
            obs_input = make_user_input_observation(user_input)
            observations.append(obs_input)

            # Build candidates from user input
            candidates: List[CandidateBundle] = []
            obs_ids = [o.id for o in observations]

            if user_input.lower() in ("exit", "quit", "q"):
                candidates.append(build_host_exit_candidate(
                    user_input,
                    obs_ids,
                    self.constitution.version,
                ))
            else:
                # Default: echo as Notify(stdout)
                candidates.append(build_host_notify_candidate(
                    f"Echo: {user_input}",
                    "stdout",
                    obs_ids,
                    self.constitution.version,
                ))

            # Budget observation (no LLM used in stub mode)
            observations.append(make_budget_observation(0, len(candidates), 0))

            self._run_single_cycle(observations, candidates)

            if self.internal_state.last_decision == DecisionType.EXIT.value:
                break

    def _run_single_cycle(
        self,
        observations: List[Observation],
        candidates: List[CandidateBundle],
    ) -> None:
        """Run one complete cycle: decide → execute → log."""
        assert self.constitution is not None
        cycle = self.internal_state.cycle_index

        print(f"\n--- Cycle {cycle} ---")

        # 1. Policy core decision
        output = self.run_cycle(observations, candidates)
        decision = output.decision

        print(f"  Decision: {decision.decision_type}")
        if decision.refusal:
            print(f"  Refusal: {decision.refusal.reason_code} (gate: {decision.refusal.failed_gate})")
        if decision.exit_record:
            print(f"  Exit: {decision.exit_record.reason_code}")

        # 2. Execute warranted action (if ACTION and not Exit/LogAppend)
        exec_events: List[ExecutionEvent] = []
        if (
            decision.decision_type == DecisionType.ACTION.value
            and decision.bundle is not None
            and decision.bundle.action_request.action_type != ActionType.EXIT.value
        ):
            exec_events = self.execute_decision(output)
            for ev in exec_events:
                print(f"  Executed: {ev.tool} → {ev.result} ({ev.detail})")

        # 3. Derive telemetry and log
        log_intents = derive_telemetry(
            self.run_id,
            cycle,
            observations,
            candidates,
            output,
        )

        log_bundles = build_log_append_bundles(
            log_intents,
            cycle,
            self.constitution.version,
        )

        log_events = self.execute_log_appends(log_bundles, observations)

        # 4. Advance state
        self.internal_state = self.internal_state.advance(decision.decision_type)


def main():
    """Entry point."""
    import os

    # Find repo root: directory containing artifacts/phase-x/constitution/
    repo_root = Path(__file__).resolve().parent.parent.parent
    # Verify it looks right
    constitution_dir = repo_root / "artifacts" / "phase-x" / "constitution"
    if not constitution_dir.exists():
        print(f"[FATAL] Cannot find constitution at {constitution_dir}")
        sys.exit(1)

    host = RSAHost(str(repo_root))
    host.run()


if __name__ == "__main__":
    main()
