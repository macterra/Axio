"""
X-3 Profiling Runner

Executes a single X-3 session: admit → generate plan → execute N cycles
→ boundary verification → replay → closure evaluation → write logs.

Harness-to-kernel handoff per AR1:
  1. Load InternalStateX3 from prior cycle's committed state
  2. Perform boundary verification + activation (Step 0)
  3. Pass post-activation state to policy_core_x3()
  4. Extract results, sign CycleCommit, then CycleStart for next cycle
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import (
    ActionRequest,
    Author,
    CandidateBundle,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    canonical_json,
    canonical_json_bytes,
)
from kernel.src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyGrant,
    TreatyRevocation,
    TreatyAdmissionEvent,
    TreatyAdmissionResult,
)
from kernel.src.rsax3.artifacts_x3 import (
    ActiveTreatySetX3,
    BoundaryCode,
    CycleCommitPayload,
    CycleStartPayload,
    DecisionTypeX3,
    InternalStateX3,
    PolicyOutputX3,
    SuccessionProposal,
    TreatyRatification,
    compute_identity_chain_tip_hash,
    compute_genesis_tip_hash,
)
from kernel.src.rsax3.boundary_verifier import (
    BoundaryVerificationResult,
    verify_and_activate_boundary,
)
from kernel.src.rsax3.constitution_x3 import EffectiveConstitutionFrame
from kernel.src.rsax3.policy_core_x3 import (
    KERNEL_VERSION_ID,
    policy_core_x3,
)
from kernel.src.rsax3.signature_x3 import (
    derive_genesis_keypair,
    precompute_keypairs,
    sign_cycle_commit,
    sign_cycle_start,
)
from kernel.src.rsax2.policy_core_x2 import DelegatedActionRequest

from .generators_x3 import X3CyclePlan, X3Generator, X3_GENESIS_SEED, create_generator
from .schemas_x3 import (
    X3GateResult,
    X3SessionStart,
    X3SessionEnd,
    admit_session,
)


# ---------------------------------------------------------------------------
# Cycle / Session Result
# ---------------------------------------------------------------------------

@dataclass
class X3CycleResult:
    """Result of a single X-3 cycle execution."""
    cycle_index: int
    cycle_id: str = ""
    decision_type: str = ""
    state_in_hash: str = ""
    state_out_hash: str = ""
    # Treaty
    grants_admitted: int = 0
    grants_rejected: int = 0
    revocations_admitted: int = 0
    revocations_rejected: int = 0
    delegated_warrants_issued: int = 0
    delegated_rejections: int = 0
    density: float = 0.0
    active_grants_count: int = 0
    # Succession
    succession_admitted: bool = False
    succession_is_self: bool = False
    succession_rejected_count: int = 0
    succession_rejection_codes: List[str] = field(default_factory=list)
    # Ratification
    ratifications_admitted: int = 0
    ratifications_rejected: int = 0
    # Boundary
    boundary_activation: bool = False
    boundary_fault_injected: bool = False
    boundary_fault_detected: bool = False
    boundary_fault_code: str = ""
    # Lineage
    sovereign_public_key_active: str = ""
    identity_chain_length: int = 1
    suspended_count: int = 0
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "X3CycleResult",
            "cycle_index": self.cycle_index,
            "cycle_id": self.cycle_id,
            "decision_type": self.decision_type,
            "state_in_hash": self.state_in_hash,
            "state_out_hash": self.state_out_hash,
            "grants_admitted": self.grants_admitted,
            "grants_rejected": self.grants_rejected,
            "revocations_admitted": self.revocations_admitted,
            "revocations_rejected": self.revocations_rejected,
            "delegated_warrants_issued": self.delegated_warrants_issued,
            "delegated_rejections": self.delegated_rejections,
            "density": self.density,
            "active_grants_count": self.active_grants_count,
            "succession_admitted": self.succession_admitted,
            "succession_is_self": self.succession_is_self,
            "succession_rejected_count": self.succession_rejected_count,
            "succession_rejection_codes": self.succession_rejection_codes,
            "ratifications_admitted": self.ratifications_admitted,
            "ratifications_rejected": self.ratifications_rejected,
            "boundary_activation": self.boundary_activation,
            "boundary_fault_injected": self.boundary_fault_injected,
            "boundary_fault_detected": self.boundary_fault_detected,
            "boundary_fault_code": self.boundary_fault_code,
            "sovereign_public_key_active": self.sovereign_public_key_active,
            "identity_chain_length": self.identity_chain_length,
            "suspended_count": self.suspended_count,
            "latency_ms": round(self.latency_ms, 3),
        }


@dataclass
class X3SessionResult:
    """Aggregate result of a full X-3 session."""
    session_id: str = ""
    session_family: str = ""
    start_time: str = ""
    end_time: str = ""
    constitution_hash: str = ""
    total_cycles: int = 0
    total_rotations_activated: int = 0
    total_successions_rejected: int = 0
    total_boundary_faults_detected: int = 0
    total_grants_admitted: int = 0
    total_grants_rejected: int = 0
    total_revocations_admitted: int = 0
    total_delegated_warrants: int = 0
    total_ratifications_admitted: int = 0
    total_ratifications_rejected: int = 0
    density_series: List[float] = field(default_factory=list)
    state_hash_chain_tip: str = ""
    replay_divergence_count: int = 0
    replay_divergences: List[str] = field(default_factory=list)
    closure_pass: bool = False
    failure_reasons: List[str] = field(default_factory=list)
    aborted: bool = False
    abort_reason: str = ""
    cycle_results: List[X3CycleResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "X3SessionResult",
            "session_id": self.session_id,
            "session_family": self.session_family,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "constitution_hash": self.constitution_hash,
            "total_cycles": self.total_cycles,
            "total_rotations_activated": self.total_rotations_activated,
            "total_successions_rejected": self.total_successions_rejected,
            "total_boundary_faults_detected": self.total_boundary_faults_detected,
            "total_grants_admitted": self.total_grants_admitted,
            "total_grants_rejected": self.total_grants_rejected,
            "total_revocations_admitted": self.total_revocations_admitted,
            "total_delegated_warrants": self.total_delegated_warrants,
            "total_ratifications_admitted": self.total_ratifications_admitted,
            "total_ratifications_rejected": self.total_ratifications_rejected,
            "replay_divergence_count": self.replay_divergence_count,
            "replay_divergences": self.replay_divergences,
            "closure_pass": self.closure_pass,
            "failure_reasons": self.failure_reasons,
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _state_hash(state: InternalStateX3) -> str:
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
        payload={"text": text, "source": "x3_harness"},
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
    msg: str, constitution: EffectiveConstitutionFrame,
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
        claim="X-3 cycle notification",
        clause_ref=constitution.make_citation("CL-SCOPE-SYSTEM"),
        author=Author.HOST.value,
    )
    just = Justification(
        text=f"X-3 cycle Notify(stdout)",
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

class X3Runner:
    """Runs a single X-3 session."""

    def __init__(
        self,
        session_start: X3SessionStart,
        constitution_frame: EffectiveConstitutionFrame,
        repo_root: Path,
        log_root: Path,
        verbose: bool = True,
    ):
        self.session_start = session_start
        self.constitution = constitution_frame
        self.repo_root = repo_root
        self.log_root = log_root
        self.verbose = verbose

        # Precompute sovereign keypairs
        max_rotations = len(session_start.rotation_schedule) + 1
        self.sovereign_keypairs = precompute_keypairs(
            X3_GENESIS_SEED, max_rotations,
        )

        # Initialize state
        gen_priv, gen_gid = self.sovereign_keypairs[0]
        genesis_artifact = {
            "type": "genesis",
            "sovereign_public_key": gen_gid,
            "kernel_version_id": KERNEL_VERSION_ID,
            "constitution_hash": constitution_frame.sha256,
            "overlay_hash": constitution_frame.overlay_hash,
        }
        genesis_tip_hash = compute_genesis_tip_hash(genesis_artifact)

        self._state = InternalStateX3(
            active_constitution_hash=constitution_frame.sha256,
            sovereign_public_key_active=gen_gid,
            identity_chain_length=1,
            identity_chain_tip_hash=genesis_tip_hash,
            overlay_hash=constitution_frame.overlay_hash,
        )

        self._cycle_log: List[Dict[str, Any]] = []
        self._boundary_events: List[Dict[str, Any]] = []

        # Track succession state for boundary verification
        self._succession_admitted_this_cycle = False
        self._succession_proposal_hash = ""
        self._prior_cycle_commit_payload: Optional[Dict[str, Any]] = None
        self._prior_cycle_commit_signature: Optional[str] = None
        self._active_sovereign_index = 0

    def run(self) -> X3SessionResult:
        """Execute full session."""
        result = X3SessionResult(
            session_id=self.session_start.session_id,
            session_family=self.session_start.session_family,
            start_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            constitution_hash=self.constitution.sha256,
        )

        self._log(f"=== X-3 Session: {self.session_start.session_family} ===")
        self._log(f"Session ID: {self.session_start.session_id}")

        # --- Gate admission ---
        gate_results = admit_session(
            self.session_start,
            KERNEL_VERSION_ID,
            self.constitution.sha256,
            self.constitution.has_x2_sections(),
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
        self._log(f"  Plan: {len(plan)} cycles")

        # --- Log session start ---
        session_dir = self.log_root / self.session_start.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        self._append_jsonl(session_dir / "x3_sessions.jsonl",
                           self.session_start.to_dict())

        # --- Execute cycles ---
        self._log(f"Executing {len(plan)} cycles...")
        density_bound = self.constitution.density_upper_bound()

        for cycle_plan in plan:
            cycle_result = self._execute_cycle(cycle_plan, density_bound)
            result.cycle_results.append(cycle_result)
            result.total_cycles += 1

            # Aggregates
            result.total_grants_admitted += cycle_result.grants_admitted
            result.total_grants_rejected += cycle_result.grants_rejected
            result.total_revocations_admitted += cycle_result.revocations_admitted
            result.total_delegated_warrants += cycle_result.delegated_warrants_issued
            result.total_ratifications_admitted += cycle_result.ratifications_admitted
            result.total_ratifications_rejected += cycle_result.ratifications_rejected
            result.density_series.append(cycle_result.density)
            if cycle_result.succession_admitted:
                result.total_rotations_activated += 1
            result.total_successions_rejected += cycle_result.succession_rejected_count
            if cycle_result.boundary_fault_detected:
                result.total_boundary_faults_detected += 1

            # Log
            self._append_jsonl(session_dir / "x3_metrics.jsonl",
                               cycle_result.to_dict())

            if cycle_result.boundary_fault_detected:
                # Hard-stop on boundary fault (per AQ2)
                self._log(
                    f"  Cycle {cycle_result.cycle_index}: BOUNDARY FAULT "
                    f"({cycle_result.boundary_fault_code})"
                )
                break

            if self.verbose and cycle_result.cycle_index % 10 == 0:
                self._log(
                    f"  Cycle {cycle_result.cycle_index}: "
                    f"d={cycle_result.density:.4f} "
                    f"chain={cycle_result.identity_chain_length} "
                    f"dt={cycle_result.decision_type}"
                )

        # --- State hash chain tip ---
        result.state_hash_chain_tip = self._compute_chain_tip()

        # --- Replay verification ---
        self._log("Replay verification...")
        divergences = self._replay_verify()
        result.replay_divergence_count = len(divergences)
        result.replay_divergences = divergences
        self._log(f"  Replay: {'PASS' if not divergences else 'FAIL'}")

        # --- Closure evaluation ---
        result.closure_pass, result.failure_reasons = self._evaluate_closure(result)
        self._log(f"Closure: {'PASS' if result.closure_pass else 'FAIL'}")
        for r in result.failure_reasons:
            self._log(f"  FAIL: {r}")

        # --- Write session end ---
        session_end = X3SessionEnd(
            session_id=self.session_start.session_id,
            final_cycle=result.total_cycles - 1,
            replay_divergence_count=result.replay_divergence_count,
            closure_pass=result.closure_pass,
            failure_reasons=result.failure_reasons,
            state_hash_chain_tip=result.state_hash_chain_tip,
            total_rotations_activated=result.total_rotations_activated,
            total_successions_rejected=result.total_successions_rejected,
            total_boundary_faults_detected=result.total_boundary_faults_detected,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self._append_jsonl(session_dir / "x3_sessions.jsonl",
                           session_end.to_dict())

        # Boundary events
        for evt in self._boundary_events:
            self._append_jsonl(session_dir / "x3_boundary_events.jsonl", evt)

        return self._finalize(result)

    # -------------------------------------------------------------------
    # Per-cycle execution
    # -------------------------------------------------------------------

    def _execute_cycle(
        self,
        plan: X3CyclePlan,
        density_bound: float,
    ) -> X3CycleResult:
        cycle_index = plan.cycle_index
        cycle_id = f"X3-{cycle_index:04d}"
        t_start = time.perf_counter()

        state_in_hash = _state_hash(self._state)

        # ------- Step 0: Boundary verification/activation -------
        boundary_result = self._do_boundary(cycle_index, plan)
        if boundary_result is not None and not boundary_result.passed:
            # Boundary fault detected — log and return
            elapsed = (time.perf_counter() - t_start) * 1000
            return X3CycleResult(
                cycle_index=cycle_index,
                cycle_id=cycle_id,
                state_in_hash=state_in_hash,
                boundary_fault_injected=plan.boundary_fault is not None,
                boundary_fault_detected=True,
                boundary_fault_code=boundary_result.failure_code,
                sovereign_public_key_active=self._state.sovereign_public_key_active,
                identity_chain_length=self._state.identity_chain_length,
                latency_ms=elapsed,
            )

        activation_occurred = (
            boundary_result is not None and boundary_result.activation_occurred
        )

        # ------- Steps 1-11: policy_core_x3 -------
        observations = [
            _make_timestamp_obs(plan.timestamp),
            _make_user_input_obs(f"X-3 cycle {cycle_index}"),
            _make_budget_obs(1),
        ]

        rsa_action_candidates = [_build_notify_candidate(
            f"X-3 cycle {cycle_index}", self.constitution,
        )]

        output = policy_core_x3(
            cycle_id=cycle_index,
            observations=observations,
            amendment_candidates=[],
            pending_amendment_candidates=list(self._state.pending_amendments),
            succession_candidates=list(plan.succession_proposals),
            treaty_revocation_candidates=list(plan.revocations),
            treaty_ratification_candidates=list(plan.ratifications),
            treaty_grant_candidates=list(plan.grants),
            delegated_action_candidates=list(plan.delegated_requests),
            rsa_action_candidates=rsa_action_candidates,
            constitution_frame=self.constitution,
            internal_state=self._state,
        )

        elapsed_ms = (time.perf_counter() - t_start) * 1000

        # Extract succession results
        succession_admitted = False
        succession_is_self = False
        succession_rejected_count = 0
        succession_rejection_codes: List[str] = []

        if output.succession_admission is not None:
            succession_admitted = output.succession_admission.admitted
            succession_is_self = output.succession_admission.is_self_succession

        for rej in output.succession_rejections:
            succession_rejected_count += 1
            succession_rejection_codes.append(rej.rejection_code)

        # Track succession for next-cycle boundary
        self._succession_admitted_this_cycle = (
            succession_admitted and not succession_is_self
        )
        if self._succession_admitted_this_cycle and output.succession_admission:
            # Compute proposal hash for tip computation
            self._succession_proposal_hash = hashlib.sha256(
                json.dumps(
                    {"proposal_id": output.succession_admission.proposal_id},
                    sort_keys=True,
                ).encode()
            ).hexdigest()
        else:
            self._succession_proposal_hash = ""

        # Post-cycle density
        active = self._state.active_treaty_set.active_grants(
            self._state.cycle_index
        )
        density = 0.0
        try:
            _, _, _, density = self.constitution.compute_effective_density(active)
        except Exception:
            pass

        # Build result
        result = X3CycleResult(
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
            active_grants_count=len(active),
            succession_admitted=succession_admitted,
            succession_is_self=succession_is_self,
            succession_rejected_count=succession_rejected_count,
            succession_rejection_codes=succession_rejection_codes,
            ratifications_admitted=len(output.ratification_admissions),
            ratifications_rejected=len(output.ratification_rejections),
            boundary_activation=activation_occurred,
            boundary_fault_injected=plan.boundary_fault is not None,
            sovereign_public_key_active=self._state.sovereign_public_key_active,
            identity_chain_length=self._state.identity_chain_length,
            suspended_count=(
                len(self._state.active_treaty_set.suspended_grant_ids)
            ),
            latency_ms=elapsed_ms,
        )

        # ------- Sign CycleCommit (end of cycle) -------
        self._sign_cycle_commit(cycle_index)

        # Advance state
        self._state = self._state.advance(output.decision_type)

        result.state_out_hash = _state_hash(self._state)

        # Store cycle log for replay
        self._cycle_log.append({
            "cycle_index": cycle_index,
            "state_in_hash": state_in_hash,
            "state_out_hash": result.state_out_hash,
            "decision_type": output.decision_type,
        })

        return result

    # -------------------------------------------------------------------
    # Boundary logic
    # -------------------------------------------------------------------

    def _do_boundary(
        self,
        cycle_index: int,
        plan: X3CyclePlan,
    ) -> Optional[BoundaryVerificationResult]:
        """Perform Step 0: boundary verification and activation.

        The boundary verifier mutates state in-place during activation (Step 3),
        then verifies CycleStart against the post-activation state (Step 4).
        Therefore, CycleStart must be built and signed with post-activation
        values when activation is expected.

        For cycle 0: just sign CycleStart (no prior commit to verify).
        For cycle >= 1: verify CycleCommit(c-1), then activate if pending,
                        then verify CycleStart(c) against post-activation key.
        """
        # --- Fault injection setup ---
        fault = plan.boundary_fault
        commit_payload = self._prior_cycle_commit_payload
        commit_sig = self._prior_cycle_commit_signature

        # Determine which sovereign index will be active AFTER activation
        will_activate = (
            self._state.pending_successor_key is not None
            and cycle_index >= 1
        )

        if will_activate:
            # After activation, the successor becomes active
            post_activation_key = self._state.pending_successor_key
            post_activation_index = self._find_sovereign_index(post_activation_key)
            if post_activation_index is None:
                post_activation_index = self._active_sovereign_index
            post_activation_chain_length = self._state.identity_chain_length + 1
            # Precompute new tip hash
            post_activation_tip = compute_identity_chain_tip_hash(
                chain_length=post_activation_chain_length,
                active_key=post_activation_key,
                prior_tip_hash=self._state.identity_chain_tip_hash,
                succession_proposal_hash=self._succession_proposal_hash,
            )
        else:
            post_activation_key = self._state.sovereign_public_key_active
            post_activation_index = self._active_sovereign_index
            post_activation_chain_length = self._state.identity_chain_length
            post_activation_tip = self._state.identity_chain_tip_hash

        # Build CycleStart payload with post-activation state
        start_payload = CycleStartPayload(
            cycle_id=cycle_index,
            kernel_version_id=KERNEL_VERSION_ID,
            state_hash_prev=(
                self._cycle_log[-1]["state_out_hash"] if self._cycle_log else ""
            ),
            sovereign_public_key_active=post_activation_key,
            identity_chain_length=post_activation_chain_length,
            identity_chain_tip_hash=post_activation_tip,
            overlay_hash=self._state.overlay_hash,
        )

        # Sign CycleStart with the post-activation sovereign key
        start_priv = self.sovereign_keypairs[post_activation_index][0]
        start_sig = sign_cycle_start(start_priv, start_payload.to_dict())

        # Pre-activation sovereign for CycleCommit verification
        active_priv = self.sovereign_keypairs[self._active_sovereign_index][0]

        # --- Fault injection ---
        if fault and cycle_index >= 1:
            fault_type = fault.get("fault_type", "")
            if fault_type == "wrong_commit_signer":
                wrong_priv = self.sovereign_keypairs[
                    (self._active_sovereign_index + 1)
                    % len(self.sovereign_keypairs)
                ][0]
                if commit_payload:
                    commit_sig = sign_cycle_commit(wrong_priv, commit_payload)
            elif fault_type == "wrong_start_signer":
                wrong_priv = self.sovereign_keypairs[
                    (post_activation_index + 1)
                    % len(self.sovereign_keypairs)
                ][0]
                start_sig = sign_cycle_start(wrong_priv, start_payload.to_dict())
            elif fault_type == "missing_pending_successor":
                if commit_payload:
                    commit_payload = dict(commit_payload)
                    commit_payload["pending_successor_key"] = None
                    commit_sig = sign_cycle_commit(active_priv, commit_payload)
            elif fault_type == "spurious_pending_successor":
                if commit_payload:
                    commit_payload = dict(commit_payload)
                    commit_payload["pending_successor_key"] = "ed25519:fake"
                    commit_sig = sign_cycle_commit(active_priv, commit_payload)
            elif fault_type == "chain_mismatch":
                start_payload.identity_chain_tip_hash = "bad" * 16
                start_sig = sign_cycle_start(start_priv, start_payload.to_dict())

        if cycle_index == 0:
            bv = verify_and_activate_boundary(
                cycle_id=cycle_index,
                state=self._state,
                cycle_commit_payload=None,
                cycle_commit_signature=None,
                cycle_start_payload=start_payload.to_dict(),
                cycle_start_signature=start_sig,
                succession_admitted_in_prior_cycle=False,
            )
            self._log_boundary_event(cycle_index, bv)
            return bv

        # Cycle >= 1
        bv = verify_and_activate_boundary(
            cycle_id=cycle_index,
            state=self._state,
            cycle_commit_payload=commit_payload,
            cycle_commit_signature=commit_sig,
            cycle_start_payload=start_payload.to_dict(),
            cycle_start_signature=start_sig,
            succession_admitted_in_prior_cycle=self._succession_admitted_this_cycle,
            succession_proposal_hash=self._succession_proposal_hash,
        )

        if bv.activation_occurred:
            self._active_sovereign_index = post_activation_index

        self._log_boundary_event(cycle_index, bv)
        self._succession_admitted_this_cycle = False
        return bv

    def _sign_cycle_commit(self, cycle_index: int) -> None:
        """Sign CycleCommit at end of cycle."""
        active_priv = self.sovereign_keypairs[self._active_sovereign_index][0]

        commit = CycleCommitPayload(
            cycle_id=cycle_index,
            kernel_version_id=KERNEL_VERSION_ID,
            state_hash_end=_state_hash(self._state),
            state_hash_prev=(
                self._cycle_log[-1]["state_out_hash"]
                if self._cycle_log else ""
            ),
            constitution_hash_tip=self._state.active_constitution_hash,
            pending_successor_key=self._state.pending_successor_key,
            identity_chain_length=self._state.identity_chain_length,
            identity_chain_tip_hash=self._state.identity_chain_tip_hash,
            overlay_hash=self._state.overlay_hash,
        )
        sig = sign_cycle_commit(active_priv, commit.to_dict())

        self._prior_cycle_commit_payload = commit.to_dict()
        self._prior_cycle_commit_signature = sig

    def _find_sovereign_index(self, gid: str) -> Optional[int]:
        """Find index of sovereign keypair by grantee identifier."""
        for i, (_, g) in enumerate(self.sovereign_keypairs):
            if g == gid:
                return i
        return None

    def _log_boundary_event(
        self, cycle_index: int, bv: BoundaryVerificationResult,
    ) -> None:
        evt = {
            "cycle_id": cycle_index,
            "passed": bv.passed,
            "activation_occurred": bv.activation_occurred,
        }
        if not bv.passed:
            evt["failure_code"] = bv.failure_code
            evt["failure_detail"] = bv.failure_detail
        if bv.activation_occurred:
            evt["prior_key"] = bv.prior_key[:32] + "..."
            evt["successor_key"] = bv.successor_key[:32] + "..."
            evt["suspended_grant_ids"] = bv.suspended_grant_ids
        self._boundary_events.append(evt)

    # -------------------------------------------------------------------
    # Replay
    # -------------------------------------------------------------------

    def _replay_verify(self) -> List[str]:
        divergences: List[str] = []
        if len(self._cycle_log) < 2:
            return divergences
        for i in range(len(self._cycle_log) - 1):
            curr = self._cycle_log[i]
            nxt = self._cycle_log[i + 1]
            if curr["state_out_hash"] != nxt["state_in_hash"]:
                divergences.append(
                    f"Cycle {curr['cycle_index']}→{nxt['cycle_index']}: "
                    f"out={curr['state_out_hash'][:16]} "
                    f"!= in={nxt['state_in_hash'][:16]}"
                )
        return divergences

    def _compute_chain_tip(self) -> str:
        if not self._cycle_log:
            return ""
        return self._cycle_log[-1]["state_out_hash"]

    # -------------------------------------------------------------------
    # Closure evaluation
    # -------------------------------------------------------------------

    def _evaluate_closure(
        self, result: X3SessionResult,
    ) -> Tuple[bool, List[str]]:
        """Evaluate X-3 closure criteria per spec §11."""
        failures: List[str] = []
        family = self.session_start.session_family

        # C1: All N cycles completed
        # For boundary fault families, early stop is expected
        if family != "X3-INVALID_BOUNDARY":
            if result.total_cycles != self.session_start.session_length_cycles:
                failures.append(
                    f"C1: expected {self.session_start.session_length_cycles} "
                    f"cycles, got {result.total_cycles}"
                )

        # C2: Replay divergence = 0
        if result.replay_divergence_count > 0:
            failures.append(
                f"C2: {result.replay_divergence_count} replay divergences"
            )

        # C3: Density never exceeded bound
        bound = self.session_start.density_upper_bound
        for i, d in enumerate(result.density_series):
            if d > bound + 1e-9:
                failures.append(f"C3: density {d:.6f} > bound {bound} at cycle {i}")
                break

        # C4: Family-specific closure
        if family in ("X3-BASE", "X3-NEAR_BOUND", "X3-CHURN",
                       "X3-RAT_DELAY", "X3-MULTI_ROT"):
            # Must have at least 1 lawful rotation
            if result.total_rotations_activated == 0:
                failures.append("C4: no lawful succession activated")

        if family == "X3-MULTI_ROT":
            if result.total_rotations_activated < 2:
                failures.append(
                    f"C4-MULTI_ROT: only {result.total_rotations_activated} "
                    f"rotations, need >= 2"
                )

        if family in ("X3-INVALID_SIG", "X3-DUP_CYCLE"):
            if result.total_successions_rejected == 0:
                failures.append("C4: no unlawful succession rejected")

        if family == "X3-INVALID_BOUNDARY":
            if result.total_boundary_faults_detected == 0:
                failures.append("C4: no boundary fault detected")

        return (len(failures) == 0, failures)

    # -------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------

    def _finalize(self, result: X3SessionResult) -> X3SessionResult:
        result.end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return result

    def _append_jsonl(self, path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n")

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------

def run_x3_session(
    session_start: X3SessionStart,
    constitution_frame: EffectiveConstitutionFrame,
    repo_root: str,
    log_root: str,
    verbose: bool = True,
) -> X3SessionResult:
    """Run a single X-3 session."""
    return X3Runner(
        session_start=session_start,
        constitution_frame=constitution_frame,
        repo_root=Path(repo_root),
        log_root=Path(log_root),
        verbose=verbose,
    ).run()
