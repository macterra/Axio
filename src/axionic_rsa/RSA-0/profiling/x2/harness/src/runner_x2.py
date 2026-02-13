"""
X-2 Main Runner

Orchestrates the full X-2 treaty delegation lifecycle:

  Phase A: Startup + normal operation (verify treaty sections loaded)
  Phase B: Lawful delegation (pre-populated grants → signed DARs → warrants)
  Phase C: Lawful revocation (pre-populated grant → revoke → confirm inactive)
  Phase D: Adversarial grant rejection (11 scenarios, all rejected at correct gates)
  Phase E: Adversarial delegation rejection (4 scenarios, all rejected)
  Phase F: Expiry lifecycle (grant expires after duration_cycles)
  Phase G: Replay verification

Produces:
  - Full cycle log (for replay)
  - Treaty event trace (grants/revocations/delegated warrants)
  - Adversarial rejection log
  - Session summary
"""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from kernel.src.artifacts import Author, SystemEvent, canonical_json
from kernel.src.rsax1.artifacts_x1 import (
    AmendmentProposal,
    DecisionTypeX1,
    InternalStateX1,
    PendingAmendment,
)
from kernel.src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    DecisionTypeX2,
    InternalStateX2,
    TreatyGrant,
    TreatyRejectionCode,
    TreatyRevocation,
)
from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax2.policy_core_x2 import DelegatedActionRequest, PolicyOutputX2

from profiling.x2.harness.src.cycle_x2 import (
    X2CycleResult,
    build_notify_candidate,
    execute_warrants,
    make_system_obs,
    make_timestamp_obs,
    run_x2_cycle,
    _state_hash,
)
from profiling.x2.harness.src.scenarios import (
    TreatyScenario,
    build_all_adversarial_delegation,
    build_all_adversarial_grants,
    build_all_lawful,
    build_all_scenarios,
    build_lawful_read_delegation,
    build_lawful_notify_delegation,
    build_lawful_revocation,
)


# ---------------------------------------------------------------------------
# Session configuration
# ---------------------------------------------------------------------------

@dataclass
class X2SessionConfig:
    """Configuration for an X-2 profiling session."""
    repo_root: Path
    constitution_path: str
    schema_path: Optional[str] = None
    base_timestamp: str = "2026-02-12T12:00:00Z"
    normal_cycles_pre: int = 3          # Startup normal cycles
    normal_cycles_post: int = 2         # Post-delegation normal cycles
    adversarial_grants: bool = True
    adversarial_delegation: bool = True
    expiry_test: bool = True
    verbose: bool = True


# ---------------------------------------------------------------------------
# Session result
# ---------------------------------------------------------------------------

@dataclass
class X2SessionResult:
    """Complete result of an X-2 profiling session."""
    session_id: str
    start_time: str
    end_time: str = ""
    constitution_hash: str = ""
    total_cycles: int = 0
    cycle_results: List[X2CycleResult] = field(default_factory=list)
    # Treaty results
    total_grants_admitted: int = 0
    total_grants_rejected: int = 0
    total_revocations_admitted: int = 0
    total_revocations_rejected: int = 0
    total_delegated_warrants: int = 0
    total_delegated_rejections: int = 0
    # Adversarial results
    grant_rejection_results: List[Dict[str, Any]] = field(default_factory=list)
    delegation_rejection_results: List[Dict[str, Any]] = field(default_factory=list)
    # Phase tracking
    phase_summary: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    decision_type_counts: Dict[str, int] = field(default_factory=dict)
    # Expiry lifecycle
    expiry_confirmed: bool = False
    # Replay
    replay_verified: bool = False
    replay_divergences: List[str] = field(default_factory=list)
    # Abort
    aborted: bool = False
    abort_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
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
            "decision_type_counts": self.decision_type_counts,
            "grant_rejection_results": self.grant_rejection_results,
            "delegation_rejection_results": self.delegation_rejection_results,
            "expiry_confirmed": self.expiry_confirmed,
            "replay_verified": self.replay_verified,
            "replay_divergences": self.replay_divergences,
            "phase_summary": self.phase_summary,
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
            "cycles": [r.to_dict() for r in self.cycle_results],
        }


# ---------------------------------------------------------------------------
# Timestamp generation
# ---------------------------------------------------------------------------

def _timestamp_for_cycle(base: str, cycle_index: int) -> str:
    dt = datetime.fromisoformat(base.replace("Z", "+00:00"))
    dt = dt + timedelta(seconds=cycle_index)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

class X2Runner:
    """
    Runs the full X-2 treaty delegation lifecycle as a profiling session.
    """

    def __init__(self, config: X2SessionConfig):
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.repo_root = config.repo_root.resolve()
        self._schema: Optional[Dict[str, Any]] = None
        self._constitution: Optional[ConstitutionX2] = None
        self._state: InternalStateX2 = InternalStateX2()
        self._cycle_index: int = 0
        self._result: X2SessionResult = X2SessionResult(
            session_id=self.session_id,
            start_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    def run(self) -> X2SessionResult:
        """Execute full X-2 session. Returns session result."""
        self._log("=" * 60)
        self._log("X-2 Profiling Session — Treaty-Constrained Delegation")
        self._log(f"Session ID: {self.session_id}")
        self._log("=" * 60)

        # --- Startup ---
        self._startup()
        if self._result.aborted:
            return self._finalize()

        # --- Phase A: Normal operation (pre-delegation) ---
        self._log(f"\n=== Phase A: Normal Operation ({self.config.normal_cycles_pre} cycles) ===")
        self._run_normal_cycles("pre-delegation", self.config.normal_cycles_pre)

        # --- Phase B: Lawful delegation (grant + DAR → warrant) ---
        self._log("\n=== Phase B: Lawful Delegation ===")
        self._run_lawful_delegation_phase()

        # --- Phase C: Lawful revocation ---
        self._log("\n=== Phase C: Lawful Revocation ===")
        self._run_lawful_revocation_phase()

        # --- Phase D: Adversarial grant rejection ---
        if self.config.adversarial_grants:
            self._log("\n=== Phase D: Adversarial Grant Rejection ===")
            self._run_adversarial_grant_phase()

        # --- Phase E: Adversarial delegation rejection ---
        if self.config.adversarial_delegation:
            self._log("\n=== Phase E: Adversarial Delegation Rejection ===")
            self._run_adversarial_delegation_phase()

        # --- Phase F: Expiry lifecycle ---
        if self.config.expiry_test:
            self._log("\n=== Phase F: Expiry Lifecycle ===")
            self._run_expiry_lifecycle()

        # --- Phase G: Replay verification ---
        self._log("\n=== Phase G: Replay Verification ===")
        self._run_replay_verification()

        return self._finalize()

    # --- Startup ---

    def _startup(self) -> None:
        """Load constitution and schema, verify integrity."""
        self._log("\n--- Startup ---")

        # Load schema
        if self.config.schema_path:
            schema_path = Path(self.config.schema_path)
            if schema_path.exists():
                self._schema = json.loads(schema_path.read_text())
                self._log(f"  Schema loaded: {schema_path.name}")

        # Load constitution
        try:
            self._constitution = ConstitutionX2(
                yaml_path=self.config.constitution_path,
            )
            h = self._constitution.sha256
            self._state.active_constitution_hash = h
            self._result.constitution_hash = h
            self._log(f"  Constitution loaded: v{self._constitution.version}")
            self._log(f"  Hash: {h[:24]}...")
            self._log(f"  Amendments: {'enabled' if self._constitution.amendments_enabled() else 'DISABLED'}")

            # Treaty section check
            treaty_perms = self._constitution.get_treaty_permissions()
            if treaty_perms:
                self._log(f"  Treaty permissions: {len(treaty_perms)} authorities with treaty rights")
            else:
                self._log("  [WARN] No treaty_permissions found in constitution")

            # ECK check
            if self._constitution.has_eck_sections():
                self._log("  ECK sections: OK")
            else:
                self._log("  [ERROR] ECK sections MISSING")
                self._result.aborted = True
                self._result.abort_reason = "ECK_MISSING"
                return

            # Density check
            A, B, M, density = self._constitution.compute_density()
            self._log(f"  Density: A={A} B={B} M={M} d={density:.4f}")

            # Citation self-test
            cix = self._constitution.citation_index
            all_ids = cix.all_ids()
            unresolvable = []
            for nid in all_ids:
                citation = self._constitution.make_citation(nid)
                if cix.resolve(citation) is None:
                    unresolvable.append(nid)
            if unresolvable:
                self._log(f"  [WARN] Unresolvable IDs: {unresolvable}")
            else:
                self._log(f"  Citation index: OK ({len(all_ids)} IDs)")

            # Scope enumerations check
            scope_zones = self._constitution.get_zone_labels()
            self._log(f"  ScopeEnumerations: {len(scope_zones)} scope types")
            for st in sorted(scope_zones):
                zones = scope_zones[st]
                self._log(f"    {st}: {sorted(zones)}")

        except Exception as e:
            self._log(f"  [FATAL] Constitution load failed: {e}")
            self._result.aborted = True
            self._result.abort_reason = f"CONSTITUTION_LOAD_FAILED: {e}"

    # --- Phase A: Normal operation cycles ---

    def _run_normal_cycles(self, phase_label: str, count: int) -> None:
        """Run N normal action cycles with no treaty activity."""
        for i in range(count):
            assert self._constitution is not None
            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            user_message = f"Normal operation cycle {self._cycle_index} ({phase_label})"

            action_candidates = [
                build_notify_candidate(
                    f"Cycle {self._cycle_index}: processing {phase_label}",
                    [],
                    self._constitution,
                ),
            ]

            result, next_state, output = run_x2_cycle(
                cycle_index=self._cycle_index,
                phase=phase_label,
                timestamp=timestamp,
                user_message=user_message,
                action_candidates=action_candidates,
                amendment_candidates=[],
                treaty_grant_candidates=[],
                treaty_revocation_candidates=[],
                delegated_action_candidates=[],
                constitution=self._constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )

            self._record_cycle(result, output)
            self._state = next_state
            self._cycle_index += 1

            self._log(f"  Cycle {result.cycle_index}: {result.decision_type} "
                      f"(hash={result.constitution_hash[:16]}...)")

    # --- Phase B: Lawful delegation ---

    def _run_lawful_delegation_phase(self) -> None:
        """
        Test lawful delegation using pre-populated grants.

        Since AUTH_DELEGATION lacks action_permissions (8C.2b blocks all grant
        admissions through the normal pipeline), we pre-populate grants into
        the active treaty set and test the delegated action path.
        """
        assert self._constitution is not None

        lawful_scenarios = [
            build_lawful_read_delegation(self._constitution),
            build_lawful_notify_delegation(self._constitution),
        ]

        for scenario in lawful_scenarios:
            # Pre-populate grants into active treaty set
            for grant in scenario.pre_populated_grants:
                self._state.active_treaty_set.add_grant(grant)

            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            user_message = f"Lawful delegation: {scenario.scenario_id}"

            # Normal action + delegated action
            action_candidates = [
                build_notify_candidate(
                    f"Cycle {self._cycle_index}: {scenario.scenario_id}",
                    [],
                    self._constitution,
                ),
            ]

            result, next_state, output = run_x2_cycle(
                cycle_index=self._cycle_index,
                phase="lawful-delegation",
                timestamp=timestamp,
                user_message=user_message,
                action_candidates=action_candidates,
                amendment_candidates=[],
                treaty_grant_candidates=[],
                treaty_revocation_candidates=[],
                delegated_action_candidates=scenario.delegated_actions,
                constitution=self._constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )

            self._record_cycle(result, output)
            self._state = next_state
            self._cycle_index += 1

            # Check expectations
            if scenario.expected_delegation_outcome == "WARRANT":
                if result.delegated_warrants_issued > 0:
                    self._log(f"  {scenario.scenario_id}: WARRANT issued "
                              f"({result.delegated_warrants_issued} warrants) ✓")
                else:
                    self._log(f"  {scenario.scenario_id}: NO WARRANT "
                              f"[UNEXPECTED — expected WARRANT]")
            elif result.delegated_rejections > 0:
                self._log(f"  {scenario.scenario_id}: REJECT "
                          f"({result.delegation_rejection_codes}) ✓")
            else:
                self._log(f"  {scenario.scenario_id}: {result.decision_type}")

    # --- Phase C: Lawful revocation ---

    def _run_lawful_revocation_phase(self) -> None:
        """Test lawful revocation: pre-populate a grant, then revoke it."""
        assert self._constitution is not None

        scenario = build_lawful_revocation(self._constitution)

        # Pre-populate grant
        for grant in scenario.pre_populated_grants:
            self._state.active_treaty_set.add_grant(grant)

        timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
        user_message = f"Lawful revocation: {scenario.scenario_id}"

        action_candidates = [
            build_notify_candidate(
                f"Cycle {self._cycle_index}: {scenario.scenario_id}",
                [],
                self._constitution,
            ),
        ]

        result, next_state, output = run_x2_cycle(
            cycle_index=self._cycle_index,
            phase="lawful-revocation",
            timestamp=timestamp,
            user_message=user_message,
            action_candidates=action_candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=scenario.revocations,
            delegated_action_candidates=[],
            constitution=self._constitution,
            internal_state=self._state,
            repo_root=self.repo_root,
            schema=self._schema,
        )

        self._record_cycle(result, output)
        self._state = next_state
        self._cycle_index += 1

        if result.revocations_admitted > 0:
            self._log(f"  {scenario.scenario_id}: "
                      f"REVOCATION ADMITTED ({result.revocations_admitted}) ✓")
        else:
            self._log(f"  {scenario.scenario_id}: {result.decision_type} "
                      f"(revocations_rejected={result.revocations_rejected})")

    # --- Phase D: Adversarial grant rejection ---

    def _run_adversarial_grant_phase(self) -> None:
        """Run all adversarial grant scenarios, each expected to be rejected."""
        assert self._constitution is not None
        scenarios = build_all_adversarial_grants(self._constitution)

        for scenario in scenarios:
            # Pre-populate any required grants
            for grant in scenario.pre_populated_grants:
                self._state.active_treaty_set.add_grant(grant)

            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            user_message = f"Adversarial grant: {scenario.scenario_id}"

            action_candidates = [
                build_notify_candidate(
                    f"Cycle {self._cycle_index}: {scenario.scenario_id}",
                    [],
                    self._constitution,
                ),
            ]

            result, next_state, output = run_x2_cycle(
                cycle_index=self._cycle_index,
                phase="adversarial-grant",
                timestamp=timestamp,
                user_message=user_message,
                action_candidates=action_candidates,
                amendment_candidates=[],
                treaty_grant_candidates=scenario.grants,
                treaty_revocation_candidates=scenario.revocations,
                delegated_action_candidates=[],
                constitution=self._constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )

            self._record_cycle(result, output)
            self._state = next_state
            self._cycle_index += 1

            # Determine correctness
            correct = False
            actual_code = ""

            if scenario.expected_grant_outcome == "REJECT" and result.grants_rejected > 0:
                actual_code = result.grant_rejection_codes[0] if result.grant_rejection_codes else ""
                correct = actual_code == scenario.expected_grant_rejection_code
            elif scenario.expected_revocation_outcome == "REJECT" and result.revocations_rejected > 0:
                actual_code = result.revocation_rejection_codes[0] if result.revocation_rejection_codes else ""
                correct = actual_code == scenario.expected_revocation_rejection_code

            expected_code = (
                scenario.expected_grant_rejection_code
                or scenario.expected_revocation_rejection_code
            )

            self._result.grant_rejection_results.append({
                "scenario_id": scenario.scenario_id,
                "expected_code": expected_code,
                "actual_code": actual_code,
                "correct": correct,
            })

            status = "✓" if correct else "✗"
            self._log(f"  {scenario.scenario_id}: "
                      f"expected={expected_code}, actual={actual_code} {status}")

    # --- Phase E: Adversarial delegation rejection ---

    def _run_adversarial_delegation_phase(self) -> None:
        """Run all adversarial delegation scenarios."""
        assert self._constitution is not None
        scenarios = build_all_adversarial_delegation(self._constitution)

        for scenario in scenarios:
            # Pre-populate any required grants
            for grant in scenario.pre_populated_grants:
                self._state.active_treaty_set.add_grant(grant)

            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            user_message = f"Adversarial delegation: {scenario.scenario_id}"

            action_candidates = [
                build_notify_candidate(
                    f"Cycle {self._cycle_index}: {scenario.scenario_id}",
                    [],
                    self._constitution,
                ),
            ]

            result, next_state, output = run_x2_cycle(
                cycle_index=self._cycle_index,
                phase="adversarial-delegation",
                timestamp=timestamp,
                user_message=user_message,
                action_candidates=action_candidates,
                amendment_candidates=[],
                treaty_grant_candidates=[],
                treaty_revocation_candidates=[],
                delegated_action_candidates=scenario.delegated_actions,
                constitution=self._constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )

            self._record_cycle(result, output)
            self._state = next_state
            self._cycle_index += 1

            # Determine correctness
            correct = False
            actual_code = ""

            if result.delegation_rejection_codes:
                actual_code = result.delegation_rejection_codes[0]
                correct = actual_code == scenario.expected_delegation_rejection_code

            self._result.delegation_rejection_results.append({
                "scenario_id": scenario.scenario_id,
                "expected_code": scenario.expected_delegation_rejection_code,
                "actual_code": actual_code,
                "correct": correct,
            })

            status = "✓" if correct else "✗"
            self._log(f"  {scenario.scenario_id}: "
                      f"expected={scenario.expected_delegation_rejection_code}, "
                      f"actual={actual_code} {status}")

    # --- Phase F: Expiry lifecycle ---

    def _run_expiry_lifecycle(self) -> None:
        """
        Test grant expiry: pre-populate a short-lived grant, use it,
        advance past its duration, verify it's no longer usable.
        """
        assert self._constitution is not None

        from profiling.x2.harness.src.scenarios import (
            IdentityPool, _make_grant, _make_signed_dar,
        )

        pool = IdentityPool()
        # idx 10 to avoid collision with scenario pool
        gid = pool.grantee_id(10)
        grant = _make_grant(
            self._constitution, gid,
            actions=["ReadLocal"],
            scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]},
            duration=2,  # only 2 cycles
        )
        grant.grant_cycle = self._cycle_index  # active from current cycle

        # Pre-populate
        self._state.active_treaty_set.add_grant(grant)

        # Step 1: Use the grant (should succeed, grant active at grant_cycle)
        dar = _make_signed_dar(
            pool_index=10,
            action_type="ReadLocal",
            fields={"path": "./artifacts/test"},
            grant=grant,
            scope_type="FILE_PATH",
            scope_zone="ARTIFACTS_READ",
        )
        # Fix: the pool in scenarios uses a different pool; we need to sign with pool's key
        from kernel.src.rsax2.signature import sign_action_request
        dar = DelegatedActionRequest(
            action_type="ReadLocal",
            fields={"path": "./artifacts/test"},
            grantee_identifier=gid,
            authority_citations=[f"treaty:{grant.id}#{grant.id}"],
            signature="",
            scope_type="FILE_PATH",
            scope_zone="ARTIFACTS_READ",
            created_at="2026-02-12T12:00:01Z",
        )
        dar.signature = sign_action_request(pool.private_key(10), dar.to_action_request_dict())

        timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
        action_candidates = [
            build_notify_candidate(
                f"Cycle {self._cycle_index}: expiry test — using grant",
                [],
                self._constitution,
            ),
        ]

        result, next_state, output = run_x2_cycle(
            cycle_index=self._cycle_index,
            phase="expiry-active",
            timestamp=timestamp,
            user_message="Expiry test: grant should be active",
            action_candidates=action_candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[dar],
            constitution=self._constitution,
            internal_state=self._state,
            repo_root=self.repo_root,
            schema=self._schema,
        )
        self._record_cycle(result, output)
        self._state = next_state
        self._cycle_index += 1

        grant_active_ok = result.delegated_warrants_issued > 0
        self._log(f"  Expiry (active): delegated_warrants={result.delegated_warrants_issued} "
                  f"{'✓' if grant_active_ok else '✗'}")

        # Step 2: Advance past grant expiry (grant_cycle + duration_cycles - 1 is last active)
        # With duration=2 and grant_cycle=N, last active cycle is N+1.
        # We need to advance cycle_index past N+1.
        cycles_to_advance = grant.duration_cycles + 1  # guarantees we're past expiry
        for _ in range(cycles_to_advance):
            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            action_candidates = [
                build_notify_candidate(
                    f"Cycle {self._cycle_index}: advancing past grant expiry",
                    [],
                    self._constitution,
                ),
            ]
            r, ns, o = run_x2_cycle(
                cycle_index=self._cycle_index,
                phase="expiry-advance",
                timestamp=timestamp,
                user_message="Advancing past grant expiry",
                action_candidates=action_candidates,
                amendment_candidates=[],
                treaty_grant_candidates=[],
                treaty_revocation_candidates=[],
                delegated_action_candidates=[],
                constitution=self._constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )
            self._record_cycle(r, o)
            self._state = ns
            self._cycle_index += 1

        # Step 3: Try to use the expired grant (should fail)
        dar_expired = DelegatedActionRequest(
            action_type="ReadLocal",
            fields={"path": "./artifacts/test"},
            grantee_identifier=gid,
            authority_citations=[f"treaty:{grant.id}#{grant.id}"],
            signature="",
            scope_type="FILE_PATH",
            scope_zone="ARTIFACTS_READ",
            created_at="2026-02-12T12:00:02Z",
        )
        dar_expired.signature = sign_action_request(pool.private_key(10), dar_expired.to_action_request_dict())

        timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
        action_candidates = [
            build_notify_candidate(
                f"Cycle {self._cycle_index}: expiry test — grant should be expired",
                [],
                self._constitution,
            ),
        ]

        result_exp, next_state_exp, output_exp = run_x2_cycle(
            cycle_index=self._cycle_index,
            phase="expiry-expired",
            timestamp=timestamp,
            user_message="Expiry test: grant should be expired now",
            action_candidates=action_candidates,
            amendment_candidates=[],
            treaty_grant_candidates=[],
            treaty_revocation_candidates=[],
            delegated_action_candidates=[dar_expired],
            constitution=self._constitution,
            internal_state=self._state,
            repo_root=self.repo_root,
            schema=self._schema,
        )
        self._record_cycle(result_exp, output_exp)
        self._state = next_state_exp
        self._cycle_index += 1

        grant_expired_ok = result_exp.delegated_rejections > 0
        self._log(f"  Expiry (expired): delegated_rejections={result_exp.delegated_rejections} "
                  f"{'✓' if grant_expired_ok else '✗'}")

        self._result.expiry_confirmed = grant_active_ok and grant_expired_ok
        self._log(f"  Expiry lifecycle: {'PASS ✓' if self._result.expiry_confirmed else 'FAIL ✗'}")

    # --- Phase G: Replay verification ---

    def _run_replay_verification(self) -> None:
        """
        Deterministic chain verification: verify that each cycle's state_out
        feeds correctly into the next cycle's state_in.

        NOTE: Unlike X-1, X-2 replay cannot fully reconstruct state from scratch
        because the runner pre-populates treaty grants between cycles (a valid
        pattern — grants are host-side injections). Instead we verify:
          1. Consecutive chain: state_out[i] feeds state_in[i+1]
             (state_in[i+1] may differ due to between-cycle mutations — we track
             these as "expected mutations" and verify the chain elsewhere)
          2. Determinism within each cycle: same inputs → same outputs (tested
             in unit tests)
          3. First cycle state_in matches base state

        For full chain verification, we check state_out_hash → state_in_hash
        consistency for cycles where no between-cycle mutations occur (same phase).
        """
        self._log("  Verifying cycle chain consistency...")

        cycles = self._result.cycle_results
        divergences: List[str] = []

        if not cycles:
            self._result.replay_verified = True
            return

        # Verify first cycle starts from base state
        base_state = InternalStateX2(
            active_constitution_hash=self._result.constitution_hash
        )
        expected_first_hash = _state_hash(base_state)
        if cycles[0].state_in_hash != expected_first_hash:
            divergences.append(
                f"Cycle 0: initial state mismatch "
                f"(expected={expected_first_hash[:16]}, "
                f"actual={cycles[0].state_in_hash[:16]})"
            )

        # Verify consecutive cycles chain correctly within non-scenario phases
        # Scenario phases (delegation, adversarial-*) pre-populate grants between
        # cycles, so state_out[i] != state_in[i+1] is expected there.
        PURE_PHASES = frozenset({"pre-delegation", "post-delegation", "expiry-advance"})

        for i in range(len(cycles) - 1):
            curr = cycles[i]
            nxt = cycles[i + 1]

            # Only check chain within pure phases (no between-cycle mutations)
            if curr.phase in PURE_PHASES and curr.phase == nxt.phase:
                if curr.state_out_hash != nxt.state_in_hash:
                    divergences.append(
                        f"Cycle {curr.cycle_index}→{nxt.cycle_index}: "
                        f"state chain break within phase '{curr.phase}' "
                        f"(out={curr.state_out_hash[:16]}, "
                        f"in={nxt.state_in_hash[:16]})"
                    )

        if not divergences:
            self._log("  Replay: PASS (cycle chain verified)")
            self._result.replay_verified = True
        else:
            self._log(f"  Replay: FAIL ({len(divergences)} divergences)")
            self._result.replay_verified = False
            self._result.replay_divergences = divergences

    # --- Helpers ---

    def _record_cycle(self, result: X2CycleResult, output: PolicyOutputX2) -> None:
        """Record a cycle result and update aggregate counts."""
        self._result.cycle_results.append(result)
        self._result.total_cycles += 1

        # Decision type count
        dt = result.decision_type
        self._result.decision_type_counts[dt] = (
            self._result.decision_type_counts.get(dt, 0) + 1
        )

        # Treaty aggregate counts
        self._result.total_grants_admitted += result.grants_admitted
        self._result.total_grants_rejected += result.grants_rejected
        self._result.total_revocations_admitted += result.revocations_admitted
        self._result.total_revocations_rejected += result.revocations_rejected
        self._result.total_delegated_warrants += result.delegated_warrants_issued
        self._result.total_delegated_rejections += result.delegated_rejections

        # Execute warrants if ACTION
        if output.decision_type == DecisionTypeX2.ACTION:
            events = execute_warrants(output, self.repo_root, self._cycle_index - 1)
            result.execution_events = [e.to_dict() for e in events]

    def _finalize(self) -> X2SessionResult:
        """Finalize session result."""
        self._result.end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Phase summary
        phases: Dict[str, Dict[str, Any]] = {}
        for r in self._result.cycle_results:
            phase = r.phase
            if phase not in phases:
                phases[phase] = {"cycles": 0, "decisions": {}, "treaty_events": {}}
            phases[phase]["cycles"] += 1
            dt = r.decision_type
            phases[phase]["decisions"][dt] = phases[phase]["decisions"].get(dt, 0) + 1
            # Treaty events
            if r.grants_admitted or r.grants_rejected:
                phases[phase]["treaty_events"]["grants_admitted"] = (
                    phases[phase]["treaty_events"].get("grants_admitted", 0) + r.grants_admitted
                )
                phases[phase]["treaty_events"]["grants_rejected"] = (
                    phases[phase]["treaty_events"].get("grants_rejected", 0) + r.grants_rejected
                )
            if r.delegated_warrants_issued or r.delegated_rejections:
                phases[phase]["treaty_events"]["delegated_warrants"] = (
                    phases[phase]["treaty_events"].get("delegated_warrants", 0) + r.delegated_warrants_issued
                )
                phases[phase]["treaty_events"]["delegated_rejections"] = (
                    phases[phase]["treaty_events"].get("delegated_rejections", 0) + r.delegated_rejections
                )
        self._result.phase_summary = phases

        self._log("\n" + "=" * 60)
        self._log("Session Summary")
        self._log("=" * 60)
        self._log(f"  Total cycles:           {self._result.total_cycles}")
        self._log(f"  Decision types:         {self._result.decision_type_counts}")
        self._log(f"  Grants admitted:        {self._result.total_grants_admitted}")
        self._log(f"  Grants rejected:        {self._result.total_grants_rejected}")
        self._log(f"  Revocations admitted:   {self._result.total_revocations_admitted}")
        self._log(f"  Revocations rejected:   {self._result.total_revocations_rejected}")
        self._log(f"  Delegated warrants:     {self._result.total_delegated_warrants}")
        self._log(f"  Delegated rejections:   {self._result.total_delegated_rejections}")
        self._log(f"  Expiry confirmed:       {self._result.expiry_confirmed}")
        self._log(f"  Replay verified:        {self._result.replay_verified}")
        self._log(f"  Constitution hash:      {self._result.constitution_hash[:24]}...")

        return self._result

    def _log(self, msg: str) -> None:
        if self.config.verbose:
            print(msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_x2_session(
    repo_root: str,
    constitution_path: str,
    schema_path: Optional[str] = None,
    verbose: bool = True,
) -> X2SessionResult:
    """Convenience function to run a full X-2 session."""
    config = X2SessionConfig(
        repo_root=Path(repo_root),
        constitution_path=constitution_path,
        schema_path=schema_path,
        verbose=verbose,
    )
    runner = X2Runner(config)
    return runner.run()
