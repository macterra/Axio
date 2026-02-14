"""
X-2D Session Runner

Orchestrates N-cycle sessions with deterministic generators,
X2D_TOPOLOGICAL ordering, per-cycle metrics, and replay verification.

Per Q&A E19: generators precompute full N-cycle plan before execution.
Per Q&A V79: topological ordering within each cycle.
Per Q&A O56: per-session log dir under logs/x2d/<session_id>/
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import (
    ActionRequest,
    Author,
    CandidateBundle,
    ExecutionWarrant,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    canonical_json,
)
from kernel.src.rsax1.artifacts_x1 import (
    AmendmentProposal,
    PendingAmendment,
    StateDelta,
)
from kernel.src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyGrant,
    TreatyRevalidationEvent,
    TreatyRevocation,
    _compute_effective_density,
)
from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax2.policy_core_x2 import (
    CYCLE_ORDERING_X2D_TOPOLOGICAL,
    DelegatedActionRequest,
    PolicyOutputX2,
    policy_core_x2,
)
from kernel.src.state_hash import (
    KERNEL_VERSION_ID,
    initial_state_hash,
    cycle_state_hash,
    state_hash_hex,
    component_hash,
)

from .generators import X2DGenerator, X2DCyclePlan, create_generator
from .schemas import (
    SessionFamily,
    X2DSessionStart,
    X2DSessionEnd,
    admit_session,
)


# ---------------------------------------------------------------------------
# Per-cycle result
# ---------------------------------------------------------------------------

@dataclass
class X2DCycleResult:
    """Result of a single X-2D cycle."""
    cycle_index: int
    cycle_id: str
    decision_type: str
    state_in_hash: str = ""
    state_out_hash: str = ""
    # Treaty
    grants_admitted: int = 0
    grants_rejected: int = 0
    revocations_admitted: int = 0
    revocations_rejected: int = 0
    active_grants_count: int = 0
    # Delegated
    delegated_warrants_issued: int = 0
    delegated_rejections: int = 0
    # Density
    density: float = 0.0
    a_eff: int = 0
    b: int = 0
    m_eff: int = 0
    density_upper_bound_active: float = 0.0
    # Revalidation
    revalidation_invalidated: int = 0
    density_repair_invalidated: int = 0
    # Amendment
    amendment_adopted: bool = False
    new_constitution_hash: str = ""
    # Warrant IDs
    warrant_ids: List[str] = field(default_factory=list)
    # Refusal
    refusal_reason: str = ""
    # Latency
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_index": self.cycle_index,
            "cycle_id": self.cycle_id,
            "decision_type": self.decision_type,
            "state_in_hash": self.state_in_hash,
            "state_out_hash": self.state_out_hash,
            "grants_admitted": self.grants_admitted,
            "grants_rejected": self.grants_rejected,
            "revocations_admitted": self.revocations_admitted,
            "revocations_rejected": self.revocations_rejected,
            "active_grants_count": self.active_grants_count,
            "delegated_warrants_issued": self.delegated_warrants_issued,
            "delegated_rejections": self.delegated_rejections,
            "density": self.density,
            "a_eff": self.a_eff,
            "b": self.b,
            "m_eff": self.m_eff,
            "density_upper_bound_active": self.density_upper_bound_active,
            "revalidation_invalidated": self.revalidation_invalidated,
            "density_repair_invalidated": self.density_repair_invalidated,
            "amendment_adopted": self.amendment_adopted,
            "new_constitution_hash": self.new_constitution_hash,
            "warrant_ids": self.warrant_ids,
            "refusal_reason": self.refusal_reason,
            "latency_ms": self.latency_ms,
        }


# ---------------------------------------------------------------------------
# Session result
# ---------------------------------------------------------------------------

@dataclass
class X2DSessionResult:
    """Full result of an X-2D profiling session."""
    session_id: str
    session_family: str
    start_time: str
    end_time: str = ""
    constitution_hash: str = ""
    total_cycles: int = 0
    cycle_results: List[X2DCycleResult] = field(default_factory=list)
    # Aggregates
    total_grants_admitted: int = 0
    total_grants_rejected: int = 0
    total_revocations_admitted: int = 0
    total_revocations_rejected: int = 0
    total_delegated_warrants: int = 0
    total_delegated_rejections: int = 0
    total_revalidation_invalidated: int = 0
    total_density_repair_invalidated: int = 0
    # Density series
    density_series: List[float] = field(default_factory=list)
    active_treaty_count_series: List[int] = field(default_factory=list)
    # State hash chain
    state_hash_chain_tip: str = ""
    # Replay
    replay_divergence_count: int = 0
    replay_divergences: List[str] = field(default_factory=list)
    # Closure
    closure_pass: bool = False
    failure_reasons: List[str] = field(default_factory=list)
    # Abort
    aborted: bool = False
    abort_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_family": self.session_family,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "constitution_hash": self.constitution_hash,
            "total_cycles": self.total_cycles,
            "total_grants_admitted": self.total_grants_admitted,
            "total_grants_rejected": self.total_grants_rejected,
            "total_revocations_admitted": self.total_revocations_admitted,
            "total_revocations_rejected": self.total_revocations_rejected,
            "total_delegated_warrants": self.total_delegated_warrants,
            "total_delegated_rejections": self.total_delegated_rejections,
            "total_revalidation_invalidated": self.total_revalidation_invalidated,
            "total_density_repair_invalidated": self.total_density_repair_invalidated,
            "density_series": self.density_series,
            "active_treaty_count_series": self.active_treaty_count_series,
            "state_hash_chain_tip": self.state_hash_chain_tip,
            "replay_divergence_count": self.replay_divergence_count,
            "replay_divergences": self.replay_divergences,
            "closure_pass": self.closure_pass,
            "failure_reasons": self.failure_reasons,
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
            "cycles": [r.to_dict() for r in self.cycle_results],
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_hash(state: InternalStateX2) -> str:
    return hashlib.sha256(
        canonical_json(state.to_dict()).encode("utf-8")
    ).hexdigest()


def _make_timestamp_obs(timestamp: str) -> Observation:
    return Observation(
        kind=ObservationKind.TIMESTAMP.value,
        payload={"iso8601_utc": timestamp},
        author=Author.HOST.value,
    )


def _make_user_input_obs(text: str) -> Observation:
    return Observation(
        kind=ObservationKind.USER_INPUT.value,
        payload={"text": text, "source": "x2d_harness"},
        author=Author.USER.value,
    )


def _make_budget_obs(candidates: int = 0) -> Observation:
    return Observation(
        kind=ObservationKind.BUDGET.value,
        payload={
            "llm_output_token_count": 0,
            "llm_candidates_reported": candidates,
            "llm_parse_errors": 0,
        },
        author=Author.HOST.value,
    )


def _build_notify_candidate(
    msg: str, constitution: ConstitutionX2,
) -> CandidateBundle:
    """Build a minimal Notify candidate for RSA action path."""
    from kernel.src.artifacts import ActionType
    ar = ActionRequest(
        action_type=ActionType.NOTIFY.value,
        fields={"target": "stdout", "message": msg},
        author=Author.HOST.value,
    )
    sc = ScopeClaim(
        observation_ids=[],
        claim="X-2D cycle notification",
        clause_ref=constitution.make_citation("CL-SCOPE-SYSTEM"),
        author=Author.HOST.value,
    )
    just = Justification(
        text=f"X-2D cycle Notify(stdout)",
        author=Author.HOST.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[
            constitution.make_citation("INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"),
            constitution.make_citation("INV-AUTHORITY-CITED"),
            constitution.make_authority_citation("AUTH_TELEMETRY"),
        ],
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

class X2DRunner:
    """
    Runs a single X-2D session: admit → generate plan → execute N cycles
    → compute metrics → replay verify → write logs.
    """

    def __init__(
        self,
        session_start: X2DSessionStart,
        constitution: ConstitutionX2,
        repo_root: Path,
        log_root: Path,
        schema: Optional[Dict[str, Any]] = None,
        verbose: bool = True,
    ):
        self.session_start = session_start
        self.constitution = constitution
        self.repo_root = repo_root
        self.log_root = log_root
        self.schema = schema
        self.verbose = verbose

        self._state = InternalStateX2()
        self._state.active_constitution_hash = constitution.sha256
        self._cycle_log: List[Dict[str, Any]] = []

        # Amendment YAML storage: proposal_id → proposed_constitution_yaml
        # Needed to reconstruct ConstitutionX2 after adoption.
        self._proposed_constitutions: Dict[str, str] = {}

    def run(self) -> X2DSessionResult:
        """Execute full session. Returns result."""
        result = X2DSessionResult(
            session_id=self.session_start.session_id,
            session_family=self.session_start.session_family,
            start_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            constitution_hash=self.constitution.sha256,
        )

        # --- Gate admission ---
        self._log(f"=== X-2D Session: {self.session_start.session_family} ===")
        self._log(f"Session ID: {self.session_start.session_id}")

        gate_results = admit_session(
            self.session_start,
            KERNEL_VERSION_ID,
            self.constitution.sha256,
            self.constitution.sha256,  # treaty schema hash = constitution hash
            self.constitution.has_x2_sections(),
            self.constitution.amendments_enabled(),
        )
        for gr in gate_results:
            self._log(f"  Gate {gr.gate}: {'PASS' if gr.passed else 'FAIL'} {gr.reason}")
            if not gr.passed:
                result.aborted = True
                result.abort_reason = f"Gate {gr.gate}: {gr.reason} — {gr.detail}"
                return self._finalize(result)

        # --- Generate plan ---
        self._log("Generating cycle plan...")
        generator = create_generator(self.session_start, self.constitution)
        plan = generator.generate_plan()
        self._log(f"  Plan generated: {len(plan)} cycles")

        # --- Log session start ---
        session_dir = self.log_root / self.session_start.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        self._append_jsonl(session_dir / "x2d_session.jsonl", self.session_start.to_dict())

        # --- Execute cycles ---
        self._log(f"Executing {len(plan)} cycles...")

        density_bound = self.constitution.density_upper_bound() or 0.75
        action_perms = self.constitution.get_action_permissions()
        action_type_count = len(self.constitution.get_action_types())

        for cycle_plan in plan:
            cycle_result = self._execute_cycle(
                cycle_plan, density_bound, action_perms, action_type_count,
            )
            result.cycle_results.append(cycle_result)
            result.total_cycles += 1

            # Aggregates
            result.total_grants_admitted += cycle_result.grants_admitted
            result.total_grants_rejected += cycle_result.grants_rejected
            result.total_revocations_admitted += cycle_result.revocations_admitted
            result.total_revocations_rejected += cycle_result.revocations_rejected
            result.total_delegated_warrants += cycle_result.delegated_warrants_issued
            result.total_delegated_rejections += cycle_result.delegated_rejections
            result.total_revalidation_invalidated += cycle_result.revalidation_invalidated
            result.total_density_repair_invalidated += cycle_result.density_repair_invalidated
            result.density_series.append(cycle_result.density)
            result.active_treaty_count_series.append(cycle_result.active_grants_count)

            # Log cycle
            self._append_jsonl(session_dir / "x2d_session.jsonl", cycle_result.to_dict())

            if self.verbose and cycle_result.cycle_index % 10 == 0:
                self._log(
                    f"  Cycle {cycle_result.cycle_index}: "
                    f"d={cycle_result.density:.4f} "
                    f"active={cycle_result.active_grants_count} "
                    f"dt={cycle_result.decision_type}"
                )

        # --- State hash chain ---
        result.state_hash_chain_tip = self._compute_state_hash_chain_tip()

        # --- Replay verification ---
        self._log("Replay verification...")
        divergences = self._replay_verify()
        result.replay_divergence_count = len(divergences)
        result.replay_divergences = divergences
        if divergences:
            self._log(f"  Replay: FAIL ({len(divergences)} divergences)")
        else:
            self._log("  Replay: PASS")

        # --- Closure evaluation ---
        result.closure_pass, result.failure_reasons = self._evaluate_closure(result)
        self._log(f"Closure: {'PASS' if result.closure_pass else 'FAIL'}")
        if result.failure_reasons:
            for r in result.failure_reasons:
                self._log(f"  FAIL: {r}")

        # --- Write session end ---
        session_end = X2DSessionEnd(
            session_id=self.session_start.session_id,
            final_cycle=result.total_cycles - 1,
            replay_divergence_count=result.replay_divergence_count,
            closure_pass=result.closure_pass,
            failure_reasons=result.failure_reasons,
            state_hash_chain_tip=result.state_hash_chain_tip,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        session_end.canonical_hash()
        self._append_jsonl(session_dir / "x2d_session.jsonl", session_end.to_dict())

        return self._finalize(result)

    # --- Single cycle execution ---

    def _execute_cycle(
        self,
        plan: X2DCyclePlan,
        density_bound: float,
        action_perms: List[Dict[str, Any]],
        action_type_count: int,
    ) -> X2DCycleResult:
        """Execute a single cycle from the precomputed plan."""
        cycle_index = plan.cycle_index
        cycle_id = f"X2D-{cycle_index:04d}"
        state_in_hash = _state_hash(self._state)
        t_start = time.perf_counter()

        # Build observations
        observations = [
            _make_timestamp_obs(plan.timestamp),
            _make_user_input_obs(f"X-2D cycle {cycle_index}"),
            _make_budget_obs(1),
        ]

        # RSA action candidate (always provide a Notify)
        action_candidates = [_build_notify_candidate(
            f"X-2D cycle {cycle_index}", self.constitution,
        )]

        # Amendment candidates
        amendment_candidates: List[AmendmentProposal] = []
        if plan.amendment_proposal is not None:
            amendment_candidates.append(plan.amendment_proposal)
            # Store YAML for later reconstruction after adoption
            self._proposed_constitutions[
                plan.amendment_proposal.id
            ] = plan.amendment_proposal.proposed_constitution_yaml
        pending_candidates = list(self._state.pending_amendments)

        # Call policy core with X2D_TOPOLOGICAL ordering
        output = policy_core_x2(
            observations=observations,
            action_candidates=action_candidates,
            amendment_candidates=amendment_candidates,
            pending_amendment_candidates=pending_candidates,
            treaty_grant_candidates=list(plan.grants),
            treaty_revocation_candidates=list(plan.revocations),
            delegated_action_candidates=list(plan.delegated_requests),
            constitution=self.constitution,
            internal_state=self._state,
            repo_root=self.repo_root,
            schema=self.schema,
            cycle_ordering_mode=CYCLE_ORDERING_X2D_TOPOLOGICAL,
        )

        elapsed_ms = (time.perf_counter() - t_start) * 1000

        # Post-cycle density
        active = self._state.active_treaty_set.active_grants(self._state.cycle_index)
        a_eff, b, m_eff, density = self.constitution.compute_effective_density(active)

        # Revalidation counts
        reval_invalidated = 0
        density_repair_invalidated = 0
        for evt in getattr(output, "revalidation_events", []):
            if evt.result == "SUMMARY":
                if evt.pass_type == "POST_AMENDMENT":
                    reval_invalidated = evt.invalidated_count
                elif evt.pass_type == "DENSITY_REPAIR":
                    density_repair_invalidated = evt.invalidated_count

        # Build result
        result = X2DCycleResult(
            cycle_index=cycle_index,
            cycle_id=cycle_id,
            decision_type=output.decision_type,
            state_in_hash=state_in_hash,
            grants_admitted=len(output.treaty_grants_admitted),
            grants_rejected=len(output.treaty_grants_rejected),
            revocations_admitted=len(output.treaty_revocations_admitted),
            revocations_rejected=len(output.treaty_revocations_rejected),
            delegated_warrants_issued=len(output.delegated_warrants),
            delegated_rejections=len(output.delegated_rejections),
            density=density,
            a_eff=a_eff,
            b=b,
            m_eff=m_eff,
            density_upper_bound_active=density_bound,
            revalidation_invalidated=reval_invalidated,
            density_repair_invalidated=density_repair_invalidated,
            warrant_ids=[w.warrant_id for w in output.warrants],
            latency_ms=elapsed_ms,
        )

        # Amendment adoption
        if output.decision_type == DecisionTypeX2.ADOPT:
            result.amendment_adopted = True
            if output.adoption_record:
                result.new_constitution_hash = output.adoption_record.new_constitution_hash

        # Refusal
        if output.decision_type == DecisionTypeX2.REFUSE and output.refusal:
            result.refusal_reason = output.refusal.reason_code

        # Advance state
        next_state = self._state.advance(output.decision_type)

        # Apply state deltas
        if output.state_delta:
            delta = output.state_delta
            if delta.delta_type == "queue_amendment":
                p = delta.payload.get("pending_amendment", {})
                pending = PendingAmendment(
                    proposal_id=p["proposal_id"],
                    prior_constitution_hash=p["prior_constitution_hash"],
                    proposed_constitution_hash=p["proposed_constitution_hash"],
                    proposal_cycle=p["proposal_cycle"],
                )
                next_state.pending_amendments = list(self._state.pending_amendments) + [pending]
            elif delta.delta_type == "adopt_amendment":
                new_hash = delta.payload.get("new_constitution_hash", "")
                next_state.active_constitution_hash = new_hash
                remaining = delta.payload.get("remaining_pending", [])
                next_state.pending_amendments = [
                    PendingAmendment(**r) for r in remaining
                ]
                # Swap to the new constitution for subsequent cycles.
                # The adoption record contains the proposal_id that lets
                # us look up the stored YAML.
                adoption_rec = delta.payload.get("adoption_record", {})
                proposal_id = adoption_rec.get("proposal_id", "")
                proposal_yaml = self._proposed_constitutions.get(proposal_id, "")
                if proposal_yaml:
                    self.constitution = ConstitutionX2(yaml_string=proposal_yaml)
                    self._log(f"  Constitution swapped → {new_hash[:16]}...")

        result.state_out_hash = _state_hash(next_state)
        result.active_grants_count = len(
            next_state.active_treaty_set.active_grants(cycle_index)
        )

        # Store cycle log entry for replay
        self._cycle_log.append({
            "cycle_index": cycle_index,
            "state_in_hash": state_in_hash,
            "state_out_hash": result.state_out_hash,
            "decision_type": output.decision_type,
        })

        self._state = next_state
        return result

    # --- Replay ---

    def _replay_verify(self) -> List[str]:
        """Verify state hash chain consistency."""
        divergences: List[str] = []
        if len(self._cycle_log) < 2:
            return divergences

        for i in range(len(self._cycle_log) - 1):
            curr = self._cycle_log[i]
            nxt = self._cycle_log[i + 1]
            if curr["state_out_hash"] != nxt["state_in_hash"]:
                divergences.append(
                    f"Cycle {curr['cycle_index']}→{nxt['cycle_index']}: "
                    f"out={curr['state_out_hash'][:16]} != in={nxt['state_in_hash'][:16]}"
                )
        return divergences

    # --- State hash chain ---

    def _compute_state_hash_chain_tip(self) -> str:
        """Compute final state hash chain tip."""
        if not self._cycle_log:
            return ""
        return self._cycle_log[-1]["state_out_hash"]

    # --- Closure evaluation ---

    def _evaluate_closure(self, result: X2DSessionResult) -> Tuple[bool, List[str]]:
        """Evaluate session closure criteria per spec §8."""
        failures: List[str] = []

        # C1: All N cycles completed
        if result.total_cycles != self.session_start.session_length_cycles:
            failures.append(
                f"C1: expected {self.session_start.session_length_cycles} cycles, "
                f"got {result.total_cycles}"
            )

        # C2: Replay divergence = 0
        if result.replay_divergence_count > 0:
            failures.append(f"C2: {result.replay_divergence_count} replay divergences")

        # C3: Density never exceeded bound
        bound = self.session_start.density_upper_bound
        for i, d in enumerate(result.density_series):
            if d > bound + 1e-9:  # float tolerance
                failures.append(f"C3: density {d:.6f} > bound {bound} at cycle {i}")
                break

        # C4: At least one delegated warrant issued
        if result.total_delegated_warrants == 0:
            failures.append("C4: no delegated warrants issued")

        # C5: At least one grant admitted
        if result.total_grants_admitted == 0:
            failures.append("C5: no grants admitted")

        # C6: Family-specific checks
        family = self.session_start.session_family
        if family == SessionFamily.D_CHURN.value:
            if result.total_revocations_admitted == 0:
                failures.append("C6-CHURN: no revocations admitted")
        elif family == SessionFamily.D_RATCHET.value:
            if result.total_revalidation_invalidated == 0:
                failures.append("C6-RATCHET: no revalidation invalidations")

        return (len(failures) == 0, failures)

    # --- Finalization ---

    def _finalize(self, result: X2DSessionResult) -> X2DSessionResult:
        result.end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return result

    # --- Logging ---

    def _append_jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        """Append a single JSON record to a JSONL file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n")

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def run_x2d_session(
    session_start: X2DSessionStart,
    constitution: ConstitutionX2,
    repo_root: str,
    log_root: str,
    schema: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
) -> X2DSessionResult:
    """Run a single X-2D session."""
    runner = X2DRunner(
        session_start=session_start,
        constitution=constitution,
        repo_root=Path(repo_root),
        log_root=Path(log_root),
        schema=schema,
        verbose=verbose,
    )
    return runner.run()
