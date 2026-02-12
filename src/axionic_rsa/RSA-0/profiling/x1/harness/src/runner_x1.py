"""
X-1 Main Runner

Orchestrates the full X-1 amendment lifecycle:

  Phase A: Startup + normal operation (3 cycles under v0.2)
  Phase B: Amendment proposal (cycle 3: trivial amendment queued)
  Phase C: Cooling period (cycles 4-5: normal operation, cooling = 2)
  Phase D: Adoption (cycle 6: amendment adopted, constitution switches)
  Phase E: Post-fork operation (3 cycles under new constitution)
  Phase F: Adversarial rejection (7 scenarios, all REFUSE)
  Phase G: Chained amendments (3 sequential lawful amendments)
  Phase H: Replay verification

Produces:
  - Full cycle log (for replay)
  - Amendment trace (per proposal)
  - Constitution log (per transition)
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
from kernel.src.rsax1.constitution_x1 import ConstitutionX1

from profiling.x1.harness.src.cycle_x1 import (
    X1CycleResult,
    build_notify_candidate,
    execute_action,
    make_system_obs,
    make_timestamp_obs,
    run_x1_cycle,
)
from profiling.x1.harness.src.scenarios import (
    ScenarioResult,
    build_adversarial_cooling_reduction,
    build_adversarial_eck_removal,
    build_adversarial_physics_claim,
    build_adversarial_scope_collapse,
    build_adversarial_threshold_reduction,
    build_adversarial_universal_auth,
    build_adversarial_wildcard,
    build_all_adversarial,
    build_lawful_tighten_ratchet,
    build_lawful_trivial,
)


# ---------------------------------------------------------------------------
# Session configuration
# ---------------------------------------------------------------------------

@dataclass
class X1SessionConfig:
    """Configuration for an X-1 profiling session."""
    repo_root: Path
    constitution_path: str
    schema_path: Optional[str] = None
    base_timestamp: str = "2026-02-12T12:00:00Z"
    normal_cycles_pre_amendment: int = 3
    cooling_cycles: int = 2  # Must match constitution cooling_period_cycles
    normal_cycles_post_fork: int = 3
    adversarial_scenarios: bool = True
    chained_amendments: int = 3  # Number of sequential lawful amendments
    verbose: bool = True


# ---------------------------------------------------------------------------
# Session result
# ---------------------------------------------------------------------------

@dataclass
class X1SessionResult:
    """Complete result of an X-1 profiling session."""
    session_id: str
    start_time: str
    end_time: str = ""
    initial_constitution_hash: str = ""
    final_constitution_hash: str = ""
    total_cycles: int = 0
    cycle_results: List[X1CycleResult] = field(default_factory=list)
    # Phase results
    adoptions: List[Dict[str, Any]] = field(default_factory=list)
    rejections: List[Dict[str, Any]] = field(default_factory=list)
    constitution_transitions: List[Dict[str, Any]] = field(default_factory=list)
    # Replay
    replay_verified: bool = False
    replay_divergences: List[str] = field(default_factory=list)
    # Summary
    decision_type_counts: Dict[str, int] = field(default_factory=dict)
    phase_summary: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    aborted: bool = False
    abort_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "initial_constitution_hash": self.initial_constitution_hash,
            "final_constitution_hash": self.final_constitution_hash,
            "total_cycles": self.total_cycles,
            "decision_type_counts": self.decision_type_counts,
            "adoptions": self.adoptions,
            "rejections": self.rejections,
            "constitution_transitions": self.constitution_transitions,
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

class X1Runner:
    """
    Runs the full X-1 amendment lifecycle as a profiling session.
    """

    def __init__(self, config: X1SessionConfig):
        self.config = config
        self.session_id = str(uuid.uuid4())
        self.repo_root = config.repo_root.resolve()
        self._schema: Optional[Dict[str, Any]] = None
        self._current_constitution: Optional[ConstitutionX1] = None
        self._state: InternalStateX1 = InternalStateX1()
        self._cycle_index: int = 0
        self._result: X1SessionResult = X1SessionResult(
            session_id=self.session_id,
            start_time=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        # Constitution cache: hash → ConstitutionX1
        self._constitution_cache: Dict[str, ConstitutionX1] = {}
        # Amendment proposal store: proposal_id → full YAML string
        self._proposal_store: Dict[str, str] = {}

    def run(self) -> X1SessionResult:
        """Execute full X-1 session. Returns session result."""
        self._log("=" * 60)
        self._log("X-1 Profiling Session — Reflective Amendment Under Frozen Sovereignty")
        self._log(f"Session ID: {self.session_id}")
        self._log("=" * 60)

        # --- Startup ---
        self._startup()
        if self._result.aborted:
            return self._finalize()

        # --- Phase A: Normal operation (pre-amendment) ---
        self._log(f"\n=== Phase A: Normal Operation ({self.config.normal_cycles_pre_amendment} cycles) ===")
        self._run_normal_cycles("pre-fork", self.config.normal_cycles_pre_amendment)

        # --- Phase B: Propose trivial amendment ---
        self._log("\n=== Phase B: Propose Trivial Amendment ===")
        self._run_proposal_cycle()

        # --- Phase C: Cooling period ---
        self._log(f"\n=== Phase C: Cooling Period ({self.config.cooling_cycles} cycles) ===")
        self._run_normal_cycles("cooling", self.config.cooling_cycles)

        # --- Phase D: Adoption ---
        self._log("\n=== Phase D: Adoption ===")
        self._run_adoption_cycle()

        # --- Phase E: Post-fork operation ---
        self._log(f"\n=== Phase E: Post-Fork Operation ({self.config.normal_cycles_post_fork} cycles) ===")
        self._run_normal_cycles("post-fork", self.config.normal_cycles_post_fork)

        # --- Phase F: Adversarial rejection ---
        if self.config.adversarial_scenarios:
            self._log("\n=== Phase F: Adversarial Amendment Rejection ===")
            self._run_adversarial_phase()

        # --- Phase G: Chained amendments ---
        if self.config.chained_amendments > 0:
            self._log(f"\n=== Phase G: Chained Amendments ({self.config.chained_amendments}x) ===")
            self._run_chained_amendments()

        # --- Phase H: Replay verification ---
        self._log("\n=== Phase H: Replay Verification ===")
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
            self._current_constitution = ConstitutionX1(
                yaml_path=self.config.constitution_path,
            )
            h = self._current_constitution.sha256
            self._state.active_constitution_hash = h
            self._constitution_cache[h] = self._current_constitution
            self._result.initial_constitution_hash = h
            self._log(f"  Constitution loaded: v{self._current_constitution.version}")
            self._log(f"  Hash: {h[:24]}...")
            self._log(f"  Amendments: {'enabled' if self._current_constitution.amendments_enabled() else 'DISABLED'}")

            # ECK check
            if self._current_constitution.has_eck_sections():
                self._log("  ECK sections: OK")
            else:
                self._log("  [ERROR] ECK sections MISSING")
                self._result.aborted = True
                self._result.abort_reason = "ECK_MISSING"
                return

            # Density check
            A, B, M, density = self._current_constitution.compute_density()
            self._log(f"  Density: A={A} B={B} M={M} d={density:.4f}")

            # Citation self-test
            cix = self._current_constitution.citation_index
            all_ids = cix.all_ids()
            unresolvable = []
            for nid in all_ids:
                citation = self._current_constitution.make_citation(nid)
                if cix.resolve(citation) is None:
                    unresolvable.append(nid)
            if unresolvable:
                self._log(f"  [WARN] Unresolvable IDs: {unresolvable}")
            else:
                self._log(f"  Citation index: OK ({len(all_ids)} IDs)")

        except Exception as e:
            self._log(f"  [FATAL] Constitution load failed: {e}")
            self._result.aborted = True
            self._result.abort_reason = f"CONSTITUTION_LOAD_FAILED: {e}"

    # --- Phase A/C/E: Normal operation cycles ---

    def _handle_cycle_output(
        self, result: X1CycleResult, output: PolicyOutputX1, extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle any cycle output: execute actions, record adoptions, switch constitutions."""
        if output.decision_type == DecisionTypeX1.ACTION and output.warrant:
            exec_events = execute_action(output, self.repo_root, self._cycle_index - 1)
            result.execution_events = [e.to_dict() for e in exec_events]

        elif output.decision_type == DecisionTypeX1.ADOPT and output.adoption_record:
            adoption = output.adoption_record
            new_hash = adoption.new_constitution_hash
            self._switch_constitution(adoption)
            transition: Dict[str, Any] = {
                "cycle": result.cycle_index,
                "prior_hash": adoption.prior_constitution_hash,
                "new_hash": new_hash,
                "effective_cycle": adoption.effective_cycle,
                "adoption_record_id": adoption.id,
            }
            if extra:
                transition.update(extra)
            self._result.constitution_transitions.append(transition)
            self._result.adoptions.append(result.to_dict())

    def _run_normal_cycles(self, phase_label: str, count: int) -> None:
        """Run N normal action cycles (may also handle adoptions during cooling)."""
        for i in range(count):
            assert self._current_constitution is not None
            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            user_message = f"Normal operation cycle {self._cycle_index} ({phase_label})"

            obs_ids = []  # Will be populated from observations
            action_candidates = [
                build_notify_candidate(
                    f"Cycle {self._cycle_index}: processing {phase_label}",
                    obs_ids,
                    self._current_constitution,
                ),
            ]

            result, next_state, output = run_x1_cycle(
                cycle_index=self._cycle_index,
                phase=phase_label,
                timestamp=timestamp,
                user_message=user_message,
                action_candidates=action_candidates,
                amendment_candidates=[],
                constitution=self._current_constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )

            self._record_cycle(result)
            self._handle_cycle_output(result, output)
            self._state = next_state
            self._cycle_index += 1

            self._log(f"  Cycle {result.cycle_index}: {result.decision_type} "
                      f"(hash={result.constitution_hash[:16]}...)")

            if output.decision_type == DecisionTypeX1.EXIT:
                self._log("  [EXIT] Agent requested exit")
                self._result.aborted = True
                self._result.abort_reason = "AGENT_EXIT"
                return

    # --- Phase B: Proposal ---

    def _run_proposal_cycle(self) -> None:
        """Propose a trivial lawful amendment."""
        assert self._current_constitution is not None

        scenario = build_lawful_trivial(self._current_constitution)
        proposal = scenario.proposal
        self._proposal_store[proposal.id] = proposal.proposed_constitution_yaml

        timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
        user_message = f"Amendment proposal cycle {self._cycle_index}"

        # Action candidate alongside amendment
        action_candidates = [
            build_notify_candidate(
                f"Cycle {self._cycle_index}: submitting amendment proposal",
                [],
                self._current_constitution,
            ),
        ]

        result, next_state, output = run_x1_cycle(
            cycle_index=self._cycle_index,
            phase="propose",
            timestamp=timestamp,
            user_message=user_message,
            action_candidates=action_candidates,
            amendment_candidates=[proposal],
            constitution=self._current_constitution,
            internal_state=self._state,
            repo_root=self.repo_root,
            schema=self._schema,
        )

        self._record_cycle(result)
        self._state = next_state
        self._cycle_index += 1

        if output.decision_type == DecisionTypeX1.QUEUE_AMENDMENT:
            self._log(f"  Cycle {result.cycle_index}: QUEUE_AMENDMENT "
                      f"(proposal={proposal.id[:16]}...)")
        else:
            self._log(f"  Cycle {result.cycle_index}: {result.decision_type} "
                      f"[UNEXPECTED — expected QUEUE_AMENDMENT]")

    # --- Phase D: Adoption ---

    def _run_adoption_cycle(self) -> None:
        """Run a cycle where pending amendment should be adopted."""
        assert self._current_constitution is not None

        timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
        user_message = f"Adoption-eligible cycle {self._cycle_index}"

        action_candidates = [
            build_notify_candidate(
                f"Cycle {self._cycle_index}: adoption check",
                [],
                self._current_constitution,
            ),
        ]

        result, next_state, output = run_x1_cycle(
            cycle_index=self._cycle_index,
            phase="adopt",
            timestamp=timestamp,
            user_message=user_message,
            action_candidates=action_candidates,
            amendment_candidates=[],
            constitution=self._current_constitution,
            internal_state=self._state,
            repo_root=self.repo_root,
            schema=self._schema,
        )

        self._record_cycle(result)
        self._handle_cycle_output(result, output)
        self._state = next_state
        self._cycle_index += 1

        if output.decision_type == DecisionTypeX1.ADOPT:
            self._log(f"  Cycle {result.cycle_index}: ADOPT "
                      f"(new_hash={output.adoption_record.new_constitution_hash[:16]}...)")
        elif len(self._result.adoptions) > 0:
            # Adoption already happened during cooling phase
            self._log(f"  Cycle {result.cycle_index}: {result.decision_type} "
                      f"(adoption already occurred during cooling)")
        else:
            self._log(f"  Cycle {result.cycle_index}: {result.decision_type} "
                      f"[UNEXPECTED — expected ADOPT]")

    def _switch_constitution(self, adoption: Any) -> None:
        """Switch active constitution after adoption."""
        new_hash = adoption.new_constitution_hash
        proposal_id = adoption.proposal_id

        # Find the YAML for this proposal
        yaml_string = self._proposal_store.get(proposal_id)
        if yaml_string is None:
            # Try to find in pending amendments
            self._log(f"  [ERROR] Proposal YAML not found for {proposal_id}")
            return

        # Load new constitution from string
        try:
            new_constitution = ConstitutionX1(
                yaml_string=yaml_string,
                expected_hash=new_hash,
            )
            self._current_constitution = new_constitution
            self._constitution_cache[new_hash] = new_constitution
            self._state.active_constitution_hash = new_hash
            self._log(f"  Constitution switched: v{new_constitution.version} "
                      f"(hash={new_hash[:16]}...)")
        except Exception as e:
            self._log(f"  [ERROR] Failed to load new constitution: {e}")

    # --- Phase F: Adversarial rejection ---

    def _run_adversarial_phase(self) -> None:
        """Run all adversarial scenarios, each expected to REFUSE."""
        assert self._current_constitution is not None
        scenarios = build_all_adversarial(self._current_constitution)

        for scenario in scenarios:
            proposal = scenario.proposal
            self._proposal_store[proposal.id] = proposal.proposed_constitution_yaml
            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            user_message = f"Adversarial scenario: {scenario.scenario_id}"

            result, next_state, output = run_x1_cycle(
                cycle_index=self._cycle_index,
                phase="adversarial",
                timestamp=timestamp,
                user_message=user_message,
                action_candidates=[],
                amendment_candidates=[proposal],
                constitution=self._current_constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )

            self._record_cycle(result)
            self._state = next_state
            self._cycle_index += 1

            # Check expectation
            if (result.amendment_rejection_code == scenario.expected_rejection_code
                    or output.decision_type == DecisionTypeX1.REFUSE):
                self._log(f"  {scenario.scenario_id}: REJECT "
                          f"({result.amendment_rejection_code or result.refusal_reason}) ✓")
            else:
                self._log(f"  {scenario.scenario_id}: {output.decision_type} "
                          f"[UNEXPECTED — expected REJECT with {scenario.expected_rejection_code}]")

            self._result.rejections.append({
                "scenario_id": scenario.scenario_id,
                "expected_code": scenario.expected_rejection_code,
                "actual_code": result.amendment_rejection_code or "",
                "decision_type": output.decision_type,
                "correct": (result.amendment_rejection_code == scenario.expected_rejection_code
                           or (scenario.expected_outcome == "REJECT"
                               and output.decision_type in (DecisionTypeX1.REFUSE, DecisionTypeX1.ACTION)
                               and result.amendment_rejection_code is not None)),
            })

    # --- Phase G: Chained amendments ---

    def _run_chained_amendments(self) -> None:
        """Run N sequential lawful amendments (each: propose → cool → adopt)."""
        assert self._current_constitution is not None

        for chain_idx in range(self.config.chained_amendments):
            self._log(f"\n  --- Chain {chain_idx + 1}/{self.config.chained_amendments} ---")

            # Build scenario against current constitution
            scenario = build_lawful_tighten_ratchet(self._current_constitution)
            proposal = scenario.proposal
            self._proposal_store[proposal.id] = proposal.proposed_constitution_yaml

            # Propose
            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            result, next_state, output = run_x1_cycle(
                cycle_index=self._cycle_index,
                phase="chain-propose",
                timestamp=timestamp,
                user_message=f"Chained amendment {chain_idx + 1}: propose",
                action_candidates=[],
                amendment_candidates=[proposal],
                constitution=self._current_constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )
            self._record_cycle(result)
            self._state = next_state
            self._cycle_index += 1
            self._log(f"    Propose: {output.decision_type}")

            if output.decision_type != DecisionTypeX1.QUEUE_AMENDMENT:
                self._log(f"    [WARN] Expected QUEUE_AMENDMENT, got {output.decision_type}")
                continue

            # Cooling: run cooling_period_cycles of normal operation
            cooling = self._current_constitution.cooling_period_cycles()
            for c in range(cooling):
                timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
                action_candidates = [
                    build_notify_candidate(
                        f"Chain {chain_idx + 1} cooling {c + 1}/{cooling}",
                        [],
                        self._current_constitution,
                    ),
                ]
                result, next_state, output = run_x1_cycle(
                    cycle_index=self._cycle_index,
                    phase="chain-cooling",
                    timestamp=timestamp,
                    user_message=f"Chained cooling {c + 1}",
                    action_candidates=action_candidates,
                    amendment_candidates=[],
                    constitution=self._current_constitution,
                    internal_state=self._state,
                    repo_root=self.repo_root,
                    schema=self._schema,
                )
                self._record_cycle(result)
                self._handle_cycle_output(result, output, extra={"chain_index": chain_idx + 1})
                self._state = next_state
                self._cycle_index += 1

            # Adopt (may already have happened during cooling)
            timestamp = _timestamp_for_cycle(self.config.base_timestamp, self._cycle_index)
            result, next_state, output = run_x1_cycle(
                cycle_index=self._cycle_index,
                phase="chain-adopt",
                timestamp=timestamp,
                user_message=f"Chained amendment {chain_idx + 1}: adopt",
                action_candidates=[
                    build_notify_candidate(
                        f"Chain {chain_idx + 1} adopt check",
                        [],
                        self._current_constitution,
                    ),
                ],
                amendment_candidates=[],
                constitution=self._current_constitution,
                internal_state=self._state,
                repo_root=self.repo_root,
                schema=self._schema,
            )
            self._record_cycle(result)
            self._handle_cycle_output(result, output, extra={"chain_index": chain_idx + 1})
            self._state = next_state
            self._cycle_index += 1

            if output.decision_type == DecisionTypeX1.ADOPT:
                self._log(f"    Adopt: ADOPT → v{output.adoption_record.new_constitution_hash[:16]}...")
            else:
                self._log(f"    Adopt: {output.decision_type} (may have adopted during cooling)")

    # --- Phase H: Replay ---

    def _run_replay_verification(self) -> None:
        """
        Deterministic replay: replay all cycles from logged data.
        Verify state hashes match at each cycle boundary.
        """
        self._log("  Replaying all cycles from log...")

        # Reconstruct from base constitution
        base_hash = self._result.initial_constitution_hash
        base_constitution = self._constitution_cache.get(base_hash)
        if base_constitution is None:
            self._log("  [ERROR] Base constitution not in cache")
            return

        replay_state = InternalStateX1(active_constitution_hash=base_hash)
        replay_constitution = base_constitution
        divergences: List[str] = []

        for logged_result in self._result.cycle_results:
            expected_in_hash = logged_result.state_in_hash

            # Verify state_in matches
            from profiling.x1.harness.src.cycle_x1 import _state_hash
            actual_in_hash = _state_hash(replay_state)

            if actual_in_hash != expected_in_hash:
                msg = (f"Cycle {logged_result.cycle_index}: "
                       f"state_in divergence "
                       f"(expected={expected_in_hash[:16]}, "
                       f"actual={actual_in_hash[:16]})")
                divergences.append(msg)
                self._log(f"  [DIVERGENCE] {msg}")

            # Advance replay state to match logged decision
            replay_state = replay_state.advance(logged_result.decision_type)

            # Apply constitution transitions
            if logged_result.amendment_adopted and logged_result.new_constitution_hash:
                new_hash = logged_result.new_constitution_hash
                if new_hash in self._constitution_cache:
                    replay_constitution = self._constitution_cache[new_hash]
                    replay_state.active_constitution_hash = new_hash
                else:
                    divergences.append(
                        f"Cycle {logged_result.cycle_index}: "
                        f"constitution {new_hash[:16]} not in cache"
                    )

            # Apply queued amendments
            if logged_result.amendment_proposed and logged_result.proposal_id:
                yaml_str = self._proposal_store.get(logged_result.proposal_id)
                if yaml_str:
                    proposed_hash = hashlib.sha256(yaml_str.encode("utf-8")).hexdigest()
                    pending = PendingAmendment(
                        proposal_id=logged_result.proposal_id,
                        prior_constitution_hash=logged_result.constitution_hash,
                        proposed_constitution_hash=proposed_hash,
                        proposal_cycle=logged_result.cycle_index,
                    )
                    replay_state.pending_amendments.append(pending)

            # Adopt clears pending
            if logged_result.amendment_adopted:
                replay_state.pending_amendments = [
                    p for p in replay_state.pending_amendments
                    if p.prior_constitution_hash == logged_result.new_constitution_hash
                ]

        if not divergences:
            self._log("  Replay: PASS (all state hashes match)")
            self._result.replay_verified = True
        else:
            self._log(f"  Replay: FAIL ({len(divergences)} divergences)")
            self._result.replay_verified = False
            self._result.replay_divergences = divergences

    # --- Helpers ---

    def _record_cycle(self, result: X1CycleResult) -> None:
        """Record a cycle result and update aggregate counts."""
        self._result.cycle_results.append(result)
        self._result.total_cycles += 1
        dt = result.decision_type
        self._result.decision_type_counts[dt] = self._result.decision_type_counts.get(dt, 0) + 1

    def _finalize(self) -> X1SessionResult:
        """Finalize session result."""
        self._result.end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if self._current_constitution:
            self._result.final_constitution_hash = self._current_constitution.sha256

        # Phase summary
        phases: Dict[str, Dict[str, Any]] = {}
        for r in self._result.cycle_results:
            phase = r.phase
            if phase not in phases:
                phases[phase] = {"cycles": 0, "decisions": {}}
            phases[phase]["cycles"] += 1
            dt = r.decision_type
            phases[phase]["decisions"][dt] = phases[phase]["decisions"].get(dt, 0) + 1
        self._result.phase_summary = phases

        self._log("\n" + "=" * 60)
        self._log("Session Summary")
        self._log("=" * 60)
        self._log(f"  Total cycles: {self._result.total_cycles}")
        self._log(f"  Decision types: {self._result.decision_type_counts}")
        self._log(f"  Adoptions: {len(self._result.adoptions)}")
        self._log(f"  Rejections: {len(self._result.rejections)}")
        self._log(f"  Constitution transitions: {len(self._result.constitution_transitions)}")
        self._log(f"  Replay verified: {self._result.replay_verified}")
        self._log(f"  Initial hash: {self._result.initial_constitution_hash[:24]}...")
        self._log(f"  Final hash: {self._result.final_constitution_hash[:24]}...")

        return self._result

    def _log(self, msg: str) -> None:
        if self.config.verbose:
            print(msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_x1_session(
    repo_root: str,
    constitution_path: str,
    schema_path: Optional[str] = None,
    verbose: bool = True,
) -> X1SessionResult:
    """Convenience function to run a full X-1 session."""
    config = X1SessionConfig(
        repo_root=Path(repo_root),
        constitution_path=constitution_path,
        schema_path=schema_path,
        verbose=verbose,
    )
    runner = X1Runner(config)
    return runner.run()
