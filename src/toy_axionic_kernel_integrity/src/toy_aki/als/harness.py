"""
AKI v0.4.2/v0.4.3 ALS Harness: Succession Loop Orchestration.

Implements:
- ALSHarnessV042: Original (per-cycle sampling) semantics (frozen)
- ALSHarnessV043: Correct succession semantics with MSRW
- Succession loop: propose → validate → endorse → activate
- Degeneracy tracking and classification
- S* metric (succession horizon)

Per spec §3:
- Kernel is frozen; no internal mutation
- Growth only via successor replacement
- Order: propose → validate → endorse → activate

Per v0.4.3 spec §3.3:
- Succession events are distinct from renewals
- MSRW (Minimum Successor Residence Window) enforced
- Succession only at init/expiration/revocation

Per instructions §9:
- All runs must be reproducible from code revision + config + seed
- Logs support post-hoc structural diagnosis
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field, replace
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.als.working_mind import (
    WorkingMind,
    WorkingMindManifest,
    ResourceEnvelope,
    create_baseline_working_mind,
)
from toy_aki.als.leases import (
    LeaseCompliancePackage,
    Lease,
    LeaseStatus,
    LeaseViolation,
    LCPValidator,
    create_baseline_lcp,
)
from toy_aki.als.sentinel import (
    Sentinel,
    SentinelAttestation,
    SentinelViolationType,
    create_baseline_sentinel,
)
from toy_aki.als.generator import (
    SuccessorGenerator,
    SuccessorCandidate,
    ControlSuccessorType,
    AttackSuccessorType,
    GeneratorConfig,
    V052_ATTACK_WEIGHTS,
)


class ALSStopReason(Enum):
    """Reasons for ALS run termination."""
    HORIZON_EXHAUSTED = auto()     # Reached max cycles
    ENDORSEMENT_DEGENERACY = auto()  # All non-trivial successors rejected
    SPAM_DEGENERACY = auto()       # Control successors dominate
    FAILURE_DELEGATION = auto()    # Delegation re-entered
    FAILURE_SEMANTIC = auto()      # Forced semantic evaluation
    FAILURE_EVALUABILITY = auto()  # Evaluability loss at boundary
    FAILURE_REVERSION = auto()     # Cannot enforce reversion
    FAILURE_EXPIRATION = auto()    # Lease expiration failed
    FAILURE_SENTINEL = auto()      # Sentinel bypassed
    RENEWAL_FAIL = auto()          # Renewal failed due to insufficient budget for renewal cost


class DegeneracyType(Enum):
    """Types of degeneracy per spec §9."""
    ENDORSEMENT = auto()   # All non-trivial successors rejected
    SPAM = auto()          # Control successors repeatedly endorsed


@dataclass
class SuccessionEvent:
    """Record of a succession event."""
    cycle: int
    candidate_id: str
    mind_id: str
    source_type: str
    is_non_trivial: bool
    endorsed: bool
    rejection_reason: Optional[str] = None
    lease_id: Optional[str] = None
    selection_mode: str = "sampled"  # "sampled" or "forced"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "candidate_id": self.candidate_id,
            "mind_id": self.mind_id,
            "source_type": self.source_type,
            "is_non_trivial": self.is_non_trivial,
            "endorsed": self.endorsed,
            "rejection_reason": self.rejection_reason,
            "lease_id": self.lease_id,
            "selection_mode": self.selection_mode,
        }


@dataclass
class RenewalEvent:
    """Record of a lease renewal event."""
    cycle: int
    lease_id: str
    success: bool
    failure_reason: Optional[str] = None
    attestation_compliant: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "lease_id": self.lease_id,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "attestation_compliant": self.attestation_compliant,
        }


@dataclass
class ExpirationEvent:
    """Record of a lease expiration event (v0.4.3)."""
    cycle: int
    lease_id: str
    successor_mind_id: str
    residence_cycles: int  # How long successor was active
    source_type: str = "unknown"  # "control", "adversarial", "generated"
    renewals_completed: int = 0  # Number of successful renewals before expiration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "lease_id": self.lease_id,
            "successor_mind_id": self.successor_mind_id,
            "residence_cycles": self.residence_cycles,
            "source_type": self.source_type,
            "renewals_completed": self.renewals_completed,
        }


@dataclass
class RevocationEvent:
    """Record of a lease revocation event (v0.4.3)."""
    cycle: int
    lease_id: str
    successor_mind_id: str
    violation: str
    detail: str
    residence_cycles: int
    source_type: str = "unknown"  # "control", "adversarial", "generated"
    renewals_completed: int = 0  # Number of successful renewals before revocation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "lease_id": self.lease_id,
            "successor_mind_id": self.successor_mind_id,
            "violation": self.violation,
            "detail": self.detail,
            "residence_cycles": self.residence_cycles,
            "source_type": self.source_type,
            "renewals_completed": self.renewals_completed,
        }


@dataclass
class ALSRunResult:
    """
    Complete result of an ALS run.

    Contains all metrics and logs for post-hoc diagnosis.
    """
    # Run identity (required fields first)
    run_id: str
    seed: int
    s_star: int  # Succession horizon (authority transfers for v0.4.3)
    total_cycles: int
    total_proposals: int
    total_endorsements: int
    control_endorsements: int
    non_trivial_endorsements: int
    stop_reason: ALSStopReason
    stop_cycle: int
    is_degenerate: bool

    # Fields with defaults
    spec_version: str = "0.4.2"  # Which spec semantics were used

    # v0.4.3 metrics
    total_renewals: int = 0           # LEASE_RENEWAL_ATTESTED count
    total_expirations: int = 0        # LEASE_EXPIRED count
    total_revocations: int = 0        # LEASE_REVOKED count
    mean_residence_cycles: float = 0  # Mean successor residence duration

    # Successor mix at succession events
    attack_endorsements: int = 0      # Adversarial successor endorsements

    # Boundary-pressure telemetry (Run D)
    boundary_pressure: Optional[Dict[str, Any]] = None  # Computed by get_boundary_pressure()

    # Degeneracy
    degeneracy_type: Optional[DegeneracyType] = None
    degeneracy_window: int = 0  # Cycles in degenerate state

    # Failure info
    failure_signature: Optional[str] = None
    failure_detail: Optional[str] = None

    # Events
    succession_events: List[SuccessionEvent] = field(default_factory=list)
    renewal_events: List[RenewalEvent] = field(default_factory=list)
    expiration_events: List["ExpirationEvent"] = field(default_factory=list)
    revocation_events: List["RevocationEvent"] = field(default_factory=list)

    # Timing
    duration_ms: int = 0

    def get_successor_mix(self) -> Dict[str, Any]:
        """
        Get successor mix statistics at succession events.

        Returns breakdown of endorsed successors by category:
        - non_trivial: Genuinely capable successors
        - control: Safe baseline successors
        - attack: Adversarial test successors
        """
        endorsed = [e for e in self.succession_events if e.endorsed]
        total = len(endorsed)

        non_trivial = sum(1 for e in endorsed if e.is_non_trivial)
        control = sum(1 for e in endorsed if e.source_type == "control")
        attack = sum(1 for e in endorsed if e.source_type == "adversarial")

        return {
            "total_endorsed": total,
            "non_trivial": non_trivial,
            "non_trivial_pct": (non_trivial / total * 100) if total > 0 else 0,
            "control": control,
            "control_pct": (control / total * 100) if total > 0 else 0,
            "attack": attack,
            "attack_pct": (attack / total * 100) if total > 0 else 0,
        }

    def get_renewal_stability(self, max_renewals: int = 10) -> Dict[str, Any]:
        """
        Get renewal stability metrics by successor category.

        Reports for each category (non_trivial, control, attack):
        - Fraction of leases reaching renewal cap (normal expiration)
        - Fraction ending by revocation
        - Mean/median renewals per lease
        - Renewals per successor statistics

        Args:
            max_renewals: The max_successive_renewals setting (for cap detection)

        Returns:
            Renewal stability breakdown by category.
        """
        # Combine all lease terminations
        all_terminations = []

        for exp in self.expiration_events:
            all_terminations.append({
                "source_type": exp.source_type,
                "termination": "expiration",
                "reached_cap": exp.renewals_completed >= max_renewals,
                "renewals": exp.renewals_completed,
            })

        for rev in self.revocation_events:
            all_terminations.append({
                "source_type": rev.source_type,
                "termination": "revocation",
                "reached_cap": False,
                "renewals": rev.renewals_completed,
                "violation": rev.violation,
            })

        # Group by category
        categories = ["control", "adversarial", "generated", "unknown"]
        result: Dict[str, Any] = {}

        for cat in categories:
            cat_terms = [t for t in all_terminations if t["source_type"] == cat]
            if not cat_terms:
                continue

            total = len(cat_terms)
            reached_cap = sum(1 for t in cat_terms if t["reached_cap"])
            revoked = sum(1 for t in cat_terms if t["termination"] == "revocation")
            expired_early = total - reached_cap - revoked

            renewals_list = [t["renewals"] for t in cat_terms]
            mean_renewals = sum(renewals_list) / len(renewals_list) if renewals_list else 0
            sorted_renewals = sorted(renewals_list)
            median_renewals = sorted_renewals[len(sorted_renewals) // 2] if sorted_renewals else 0

            result[cat] = {
                "total_leases": total,
                "reached_cap": reached_cap,
                "reached_cap_pct": (reached_cap / total * 100) if total > 0 else 0,
                "revoked": revoked,
                "revoked_pct": (revoked / total * 100) if total > 0 else 0,
                "expired_early": expired_early,
                "expired_early_pct": (expired_early / total * 100) if total > 0 else 0,
                "mean_renewals": mean_renewals,
                "median_renewals": median_renewals,
            }

        # Overall summary
        total = len(all_terminations)
        if total > 0:
            result["overall"] = {
                "total_leases": total,
                "reached_cap": sum(1 for t in all_terminations if t["reached_cap"]),
                "revoked": sum(1 for t in all_terminations if t["termination"] == "revocation"),
            }

        return result

    def get_boundary_pressure(
        self,
        sentinel_telemetry: Optional[Dict[str, Any]] = None,
        resource_caps: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Compute boundary-pressure telemetry for Run D.

        Reports utilization of resource caps and action type diversity:
        - util_steps: peak_steps / max_steps_per_epoch
        - util_actions: peak_actions / max_actions_per_epoch
        - util_calls: peak_external_calls / max_external_calls (if allowlist non-empty)
        - action_type_entropy: Shannon entropy over proposed action types
        - action_type_coverage: Fraction of allowed action types actually used

        Args:
            sentinel_telemetry: Sentinel telemetry dict with peak values
            resource_caps: ResourceEnvelope caps dict

        Returns:
            Boundary-pressure metrics.
        """
        import math

        result: Dict[str, Any] = {
            "util_steps": None,
            "util_actions": None,
            "util_calls": "N/A",  # Skip by default (allowlist empty)
            "util_tokens": "N/A",  # Not instrumented
            "action_type_entropy": 0.0,
            "action_type_coverage": 0.0,
            "invalid_action_count": 0,
        }

        # Compute utilization from sentinel telemetry
        if sentinel_telemetry and resource_caps:
            max_steps = resource_caps.get("max_steps_per_epoch", 1000)
            max_actions = resource_caps.get("max_actions_per_epoch", 100)

            peak_steps = sentinel_telemetry.get("peak_steps_per_epoch", 0)
            peak_actions = sentinel_telemetry.get("peak_actions_per_epoch", 0)

            result["util_steps"] = peak_steps / max_steps if max_steps > 0 else 0
            result["util_actions"] = peak_actions / max_actions if max_actions > 0 else 0

            # External calls only if allowlist non-empty
            max_calls = resource_caps.get("max_external_calls", 10)
            allowlist = resource_caps.get("external_call_allowlist", frozenset())
            if allowlist:
                peak_calls = sentinel_telemetry.get("peak_external_calls_per_epoch", 0)
                result["util_calls"] = peak_calls / max_calls if max_calls > 0 else 0
            # else: remains "N/A"

            # Invalid action count (interface violations)
            result["invalid_action_count"] = sentinel_telemetry.get(
                "invalid_action_type_count", 0
            )

        # Action type entropy and coverage from succession events
        # Collect all action types proposed during the run
        action_type_counts: Dict[str, int] = {}
        for event in self.succession_events:
            # Track action types from endorsed successors
            if event.endorsed and hasattr(event, "proposed_action_types"):
                for at in getattr(event, "proposed_action_types", []):
                    action_type_counts[at] = action_type_counts.get(at, 0) + 1

        # If we have action type data, compute entropy
        total_actions = sum(action_type_counts.values())
        if total_actions > 0:
            entropy = 0.0
            for count in action_type_counts.values():
                if count > 0:
                    p = count / total_actions
                    entropy -= p * math.log2(p)
            result["action_type_entropy"] = entropy

            # Coverage: fraction of action types used
            # Note: This requires knowing the allowed action types
            result["action_type_coverage"] = len(action_type_counts)

        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "spec_version": self.spec_version,
            "s_star": self.s_star,
            "total_cycles": self.total_cycles,
            "total_proposals": self.total_proposals,
            "total_endorsements": self.total_endorsements,
            "control_endorsements": self.control_endorsements,
            "non_trivial_endorsements": self.non_trivial_endorsements,
            "attack_endorsements": self.attack_endorsements,
            "total_renewals": self.total_renewals,
            "total_expirations": self.total_expirations,
            "total_revocations": self.total_revocations,
            "mean_residence_cycles": self.mean_residence_cycles,
            "successor_mix": self.get_successor_mix(),
            "stop_reason": self.stop_reason.name,
            "stop_cycle": self.stop_cycle,
            "is_degenerate": self.is_degenerate,
            "degeneracy_type": self.degeneracy_type.name if self.degeneracy_type else None,
            "degeneracy_window": self.degeneracy_window,
            "failure_signature": self.failure_signature,
            "failure_detail": self.failure_detail,
            "succession_events": [e.to_dict() for e in self.succession_events],
            "renewal_events": [e.to_dict() for e in self.renewal_events],
            "expiration_events": [e.to_dict() for e in self.expiration_events],
            "revocation_events": [e.to_dict() for e in self.revocation_events],
            "boundary_pressure": self.boundary_pressure,
            "duration_ms": self.duration_ms,
        }


@dataclass
class ALSConfig:
    """Configuration for ALS run."""
    # Horizon
    max_cycles: int = 1000

    # Proposal rate
    proposals_per_cycle: int = 1

    # Renewal
    renewal_check_interval: int = 50  # Check renewal every N cycles

    # v0.4.3: Minimum Successor Residence Window
    # After endorsement, successor must remain active for at least this many cycles
    # unless expiration/revocation occurs.
    # Per spec §4.4, default = max(renewal_interval, 100)
    msrw_cycles: Optional[int] = None  # If None, computed as max(renewal_check_interval, 100)

    # Degeneracy detection
    degeneracy_window: int = 100  # Window for degeneracy classification
    spam_threshold: float = 0.8  # Control ratio threshold for spam

    # Generator config
    generator_config: Optional[GeneratorConfig] = None

    # Run E: Baseline resource envelope override
    # If set, this ResourceEnvelope is used instead of the default baseline.
    # Allows experiments to inject custom caps (e.g., max_actions_per_epoch=50).
    baseline_resource_envelope_override: Optional[ResourceEnvelope] = None

    def get_msrw(self) -> int:
        """Get effective MSRW (computed if not set)."""
        if self.msrw_cycles is not None:
            return self.msrw_cycles
        return max(self.renewal_check_interval, 100)


class ALSHarnessV042:
    """
    v0.4.2 ALS harness (FROZEN - per-cycle sampling semantics).

    WARNING: This class implements v0.4.2 semantics which conflate
    per-cycle candidate sampling with succession events. Use
    ALSHarnessV043 for correct ALS succession semantics.

    Orchestrates the succession loop:
    1. Generator proposes successor candidate
    2. Kernel validates LCP (structural only)
    3. Kernel endorses via lease
    4. Successor becomes active working mind
    5. Sentinel enforces lease constraints
    6. Renewal or expiration

    The kernel is frozen throughout. All growth occurs
    via successor replacement, not kernel mutation.
    """

    def __init__(
        self,
        seed: int = 42,
        config: Optional[ALSConfig] = None,
        verbose: bool = False,
    ):
        """
        Initialize harness.

        Args:
            seed: Random seed for reproducibility
            config: Run configuration
            verbose: Enable verbose logging
        """
        self._seed = seed
        self._config = config or ALSConfig()
        self._verbose = verbose

        # Create baseline components
        self._sentinel = create_baseline_sentinel()
        self._baseline_mind = create_baseline_working_mind(seed)
        self._baseline_manifest = self._baseline_mind.export_manifest()

        # Apply baseline resource envelope override if configured
        if self._config.baseline_resource_envelope_override is not None:
            self._baseline_manifest = replace(
                self._baseline_manifest,
                resources=self._config.baseline_resource_envelope_override,
            )

        # Create validator and generator
        self._validator = LCPValidator(self._sentinel.sentinel_id)
        self._generator = SuccessorGenerator(
            sentinel_id=self._sentinel.sentinel_id,
            baseline_manifest=self._baseline_manifest,
            seed=seed,
            config=self._config.generator_config,
        )

        # Current state
        self._current_mind: WorkingMind = self._baseline_mind
        self._current_lease: Optional[Lease] = None
        self._cycle = 0
        self._current_successor_source_type: str = "unknown"  # Track current successor category

        # Metrics
        self._s_star = 0  # Succession horizon
        self._total_proposals = 0
        self._total_endorsements = 0
        self._control_endorsements = 0
        self._non_trivial_endorsements = 0

        # Events
        self._succession_events: List[SuccessionEvent] = []
        self._renewal_events: List[RenewalEvent] = []

        # Degeneracy tracking
        self._recent_endorsements: List[bool] = []  # True = control
        self._cycles_without_non_trivial = 0

        # Stop state
        self._stopped = False
        self._stop_reason: Optional[ALSStopReason] = None
        self._failure_signature: Optional[str] = None
        self._failure_detail: Optional[str] = None

    @property
    def cycle(self) -> int:
        """Current cycle."""
        return self._cycle

    @property
    def s_star(self) -> int:
        """Current succession horizon."""
        return self._s_star

    @property
    def current_mind(self) -> WorkingMind:
        """Current active working mind."""
        return self._current_mind

    def run(self) -> ALSRunResult:
        """
        Execute a complete ALS run.

        Returns:
            Run result with all metrics and logs
        """
        start_time = current_time_ms()
        run_id = f"als_{self._seed}_{start_time}"

        if self._verbose:
            print(f"Starting ALS run: {run_id}")
            print(f"  Max cycles: {self._config.max_cycles}")
            print(f"  Baseline: {self._baseline_manifest.build_hash}")

        # Main loop
        while not self._stopped and self._cycle < self._config.max_cycles:
            self._cycle += 1
            self._sentinel.advance_cycle()

            # Propose successors
            for _ in range(self._config.proposals_per_cycle):
                self._propose_and_evaluate()

            # Check renewal
            if self._current_lease and self._cycle % self._config.renewal_check_interval == 0:
                self._check_renewal()

            # Check degeneracy
            self._check_degeneracy()

            # Check lease expiration
            if self._current_lease and self._current_lease.is_expired(self._cycle):
                self._handle_lease_expiration()

        # Determine final stop reason
        if not self._stopped:
            self._stop_reason = ALSStopReason.HORIZON_EXHAUSTED

        duration = current_time_ms() - start_time

        # Compute degeneracy
        is_degenerate = self._stop_reason in (
            ALSStopReason.ENDORSEMENT_DEGENERACY,
            ALSStopReason.SPAM_DEGENERACY,
        )
        degeneracy_type = None
        if self._stop_reason == ALSStopReason.ENDORSEMENT_DEGENERACY:
            degeneracy_type = DegeneracyType.ENDORSEMENT
        elif self._stop_reason == ALSStopReason.SPAM_DEGENERACY:
            degeneracy_type = DegeneracyType.SPAM

        result = ALSRunResult(
            run_id=run_id,
            seed=self._seed,
            s_star=self._s_star,
            total_cycles=self._cycle,
            total_proposals=self._total_proposals,
            total_endorsements=self._total_endorsements,
            control_endorsements=self._control_endorsements,
            non_trivial_endorsements=self._non_trivial_endorsements,
            stop_reason=self._stop_reason,
            stop_cycle=self._cycle,
            is_degenerate=is_degenerate,
            degeneracy_type=degeneracy_type,
            degeneracy_window=self._cycles_without_non_trivial,
            failure_signature=self._failure_signature,
            failure_detail=self._failure_detail,
            succession_events=self._succession_events,
            renewal_events=self._renewal_events,
            duration_ms=duration,
        )

        if self._verbose:
            print(f"\nALS run complete:")
            print(f"  S*: {result.s_star}")
            print(f"  Cycles: {result.total_cycles}")
            print(f"  Stop: {result.stop_reason.name}")
            print(f"  Duration: {result.duration_ms}ms")

        return result

    def _propose_and_evaluate(self) -> None:
        """Propose a successor and evaluate for endorsement."""
        self._total_proposals += 1

        # Generate candidate
        candidate = self._generator.propose(self._cycle)

        # Check if non-trivial
        is_non_trivial = candidate.is_non_trivial(self._baseline_manifest)

        # Build LCP
        lcp = self._generator.build_lcp(
            candidate,
            renewal_window=self._config.renewal_check_interval * 2,
        )

        # Validate LCP (structural only)
        valid, error = self._validator.validate(lcp)

        if not valid:
            # Record rejection
            event = SuccessionEvent(
                cycle=self._cycle,
                candidate_id=candidate.candidate_id,
                mind_id=candidate.mind.mind_id,
                source_type=candidate.source_type,
                is_non_trivial=is_non_trivial,
                endorsed=False,
                rejection_reason=error,
            )
            self._succession_events.append(event)
            self._generator.record_rejection(candidate.candidate_id)

            if is_non_trivial:
                self._cycles_without_non_trivial += 1

            return

        # Create and activate lease
        lease, error = self._validator.create_lease(lcp, candidate.mind.mind_id)
        if lease is None:
            event = SuccessionEvent(
                cycle=self._cycle,
                candidate_id=candidate.candidate_id,
                mind_id=candidate.mind.mind_id,
                source_type=candidate.source_type,
                is_non_trivial=is_non_trivial,
                endorsed=False,
                rejection_reason=error,
            )
            self._succession_events.append(event)
            return

        # Endorse: supersede old lease, activate new one
        if self._current_lease:
            self._current_lease.supersede()

        lease.activate(self._cycle)
        self._sentinel.bind_lease(lease)

        # Switch working mind
        self._current_lease = lease
        self._current_mind = candidate.mind
        self._current_successor_source_type = candidate.source_type  # Track category

        # Update metrics
        self._total_endorsements += 1
        self._generator.record_endorsement(candidate.candidate_id)

        if candidate.source_type == "control":
            self._control_endorsements += 1
            self._recent_endorsements.append(True)
        else:
            self._recent_endorsements.append(False)

        if is_non_trivial:
            self._non_trivial_endorsements += 1
            self._s_star = self._non_trivial_endorsements
            self._cycles_without_non_trivial = 0
        else:
            self._cycles_without_non_trivial += 1

        # Record event
        event = SuccessionEvent(
            cycle=self._cycle,
            candidate_id=candidate.candidate_id,
            mind_id=candidate.mind.mind_id,
            source_type=candidate.source_type,
            is_non_trivial=is_non_trivial,
            endorsed=True,
            lease_id=lease.lease_id,
        )
        self._succession_events.append(event)

        if self._verbose and is_non_trivial:
            print(f"  [Cycle {self._cycle}] Endorsed non-trivial: {candidate.mind.mind_id}, S*={self._s_star}")

    def _check_renewal(self) -> None:
        """Check and process lease renewal."""
        if self._current_lease is None:
            return

        if self._current_lease.status != LeaseStatus.ACTIVE:
            return

        # Generate renewal attestation
        nonce = secrets.token_hex(16)
        attestation = self._sentinel.generate_attestation(nonce)

        # Verify attestation
        valid, error = self._sentinel.verify_attestation(attestation)

        if not valid:
            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Attestation invalid: {error}",
                attestation_compliant=False,
            )
            self._renewal_events.append(event)
            self._current_lease.revoke(LeaseViolation.RENEWAL_FAILURE, error or "")
            return

        # Check attestation compliance
        if not attestation.is_compliant():
            reasons = []
            if not attestation.resources_within_bounds:
                reasons.append("resources")
            if not attestation.interface_compliant:
                reasons.append("interface")
            if not attestation.authority_intact:
                reasons.append("authority")
            if not attestation.revocation_hooks_intact:
                reasons.append("hooks")

            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Non-compliant: {', '.join(reasons)}",
                attestation_compliant=False,
            )
            self._renewal_events.append(event)
            self._current_lease.revoke(LeaseViolation.CONSTRAINT_VIOLATION, str(reasons))
            return

        # Attempt renewal
        success, error = self._current_lease.renew(self._cycle)

        event = RenewalEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            success=success,
            failure_reason=error,
            attestation_compliant=True,
        )
        self._renewal_events.append(event)

        # Reset epoch on successful renewal
        if success:
            self._sentinel.reset_epoch(
                active_mind_id=self._current_mind.mind_id,
                active_successor_type=self._current_successor_source_type,
            )

            # Reset working mind's epoch counters if available (for BoundaryHugger)
            if hasattr(self._current_mind, 'reset_epoch_counters'):
                self._current_mind.reset_epoch_counters()

    def _check_degeneracy(self) -> None:
        """Check for degeneracy conditions."""
        # Endorsement degeneracy: no non-trivial endorsements for too long
        if self._cycles_without_non_trivial >= self._config.degeneracy_window:
            if self._non_trivial_endorsements == 0:
                # Never endorsed any non-trivial successor
                self._stopped = True
                self._stop_reason = ALSStopReason.ENDORSEMENT_DEGENERACY
                return

        # Spam degeneracy: control successors dominate
        window = self._config.degeneracy_window
        if len(self._recent_endorsements) >= window:
            recent = self._recent_endorsements[-window:]
            control_ratio = sum(1 for x in recent if x) / len(recent)

            if control_ratio >= self._config.spam_threshold:
                self._stopped = True
                self._stop_reason = ALSStopReason.SPAM_DEGENERACY

    def _handle_lease_expiration(self) -> None:
        """Handle lease expiration (authority withdrawn)."""
        if self._current_lease is None:
            return

        if self._verbose:
            print(f"  [Cycle {self._cycle}] Lease expired: {self._current_lease.lease_id}")

        # Lease expired - authority withdrawn
        self._current_lease.status = LeaseStatus.EXPIRED
        self._sentinel.unbind_lease()

        # Revert to baseline
        self._current_mind = self._baseline_mind
        self._current_lease = None

    def signal_failure(
        self,
        stop_reason: ALSStopReason,
        signature: str,
        detail: str = "",
    ) -> None:
        """
        Signal a failure condition from external detection.

        Used by the kernel corridor to signal violations detected
        during evaluation (delegation, evaluability loss, etc.)
        """
        self._stopped = True
        self._stop_reason = stop_reason
        self._failure_signature = signature
        self._failure_detail = detail


class ALSHarnessV043:
    """
    v0.4.3 ALS harness with correct succession semantics.

    Per spec §3.3 and §4.4:
    - Succession events are distinct from renewals
    - MSRW (Minimum Successor Residence Window) enforced
    - Succession only at init/expiration/revocation
    - S* = count of SUCCESSOR_ENDORSED events (authority transfers)

    This harness implements the canonical ALS semantics where:
    - Successor replacement is a discrete authority transfer event
    - Renewals maintain existing authority (do not increment S*)
    - MSRW prevents per-cycle sampling behavior
    """

    def __init__(
        self,
        seed: int = 42,
        config: Optional[ALSConfig] = None,
        verbose: bool = False,
    ):
        """
        Initialize v0.4.3 harness.

        Args:
            seed: Random seed for reproducibility
            config: Run configuration
            verbose: Enable verbose logging
        """
        self._seed = seed
        self._config = config or ALSConfig()
        self._verbose = verbose

        # Create baseline components
        self._sentinel = create_baseline_sentinel()
        self._baseline_mind = create_baseline_working_mind(seed)
        self._baseline_manifest = self._baseline_mind.export_manifest()

        # Apply baseline resource envelope override if configured
        if self._config.baseline_resource_envelope_override is not None:
            self._baseline_manifest = replace(
                self._baseline_manifest,
                resources=self._config.baseline_resource_envelope_override,
            )

        # Create validator and generator
        self._validator = LCPValidator(self._sentinel.sentinel_id)
        self._generator = SuccessorGenerator(
            sentinel_id=self._sentinel.sentinel_id,
            baseline_manifest=self._baseline_manifest,
            seed=seed,
            config=self._config.generator_config,
        )

        # Current state
        self._current_mind: WorkingMind = self._baseline_mind
        self._current_lease: Optional[Lease] = None
        self._cycle = 0
        self._successor_endorsed_at_cycle: int = 0  # Track when current successor was endorsed
        self._current_successor_source_type: str = "unknown"  # Track current successor category
        self._current_lease_renewals: int = 0  # Track renewals for current lease

        # Metrics
        self._s_star = 0  # Succession horizon (authority transfers only)
        self._total_proposals = 0
        self._total_endorsements = 0  # Same as S* in v0.4.3
        self._control_endorsements = 0
        self._non_trivial_endorsements = 0
        self._total_renewals = 0
        self._total_expirations = 0
        self._total_revocations = 0
        self._residence_durations: List[int] = []

        # Events
        self._succession_events: List[SuccessionEvent] = []
        self._renewal_events: List[RenewalEvent] = []
        self._expiration_events: List[ExpirationEvent] = []
        self._revocation_events: List[RevocationEvent] = []

        # Degeneracy tracking
        self._recent_endorsements: List[bool] = []  # True = control
        self._successions_without_non_trivial = 0

        # Stop state
        self._stopped = False
        self._stop_reason: Optional[ALSStopReason] = None
        self._failure_signature: Optional[str] = None
        self._failure_detail: Optional[str] = None

        # State for succession boundary
        self._succession_pending = True  # Start with needing initial endorsement

    @property
    def cycle(self) -> int:
        """Current cycle."""
        return self._cycle

    @property
    def s_star(self) -> int:
        """Current succession horizon (authority transfers)."""
        return self._s_star

    @property
    def current_mind(self) -> WorkingMind:
        """Current active working mind."""
        return self._current_mind

    def get_sentinel_telemetry(self) -> Dict[str, Any]:
        """
        Get sentinel telemetry for boundary-pressure analysis.

        Returns dict with:
        - peak_steps_per_epoch: Maximum steps seen in any epoch
        - peak_actions_per_epoch: Maximum actions seen in any epoch
        - actions_blocked: Total actions blocked by sentinel
        - violations: Dict of violation type -> count
        """
        return self._sentinel.telemetry.to_dict()

    def run(self) -> ALSRunResult:
        """
        Execute a complete ALS run with v0.4.3 semantics.

        Key differences from v0.4.2:
        - Succession only at init/expiration/revocation
        - MSRW enforced
        - S* counts authority transfers, not per-cycle endorsements

        Returns:
            Run result with all metrics and logs
        """
        start_time = current_time_ms()
        run_id = f"als043_{self._seed}_{start_time}"

        if self._verbose:
            print(f"Starting ALS v0.4.3 run: {run_id}")
            print(f"  Max cycles: {self._config.max_cycles}")
            print(f"  MSRW: {self._config.get_msrw()}")
            print(f"  Baseline: {self._baseline_manifest.build_hash}")

        # Main loop
        while not self._stopped and self._cycle < self._config.max_cycles:
            self._cycle += 1
            self._sentinel.advance_cycle()

            # Check if succession is allowed (init, expiration, or revocation)
            if self._succession_pending:
                self._attempt_succession()

            # Execute working mind action and check for violations
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                violation = self._execute_working_mind_cycle()
                if violation:
                    self._handle_lease_revocation(violation[0], violation[1])
                    continue  # Skip renewal check after revocation

            # Check renewal (if we have an active lease)
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                if self._cycle % self._config.renewal_check_interval == 0:
                    self._check_renewal()

            # Check lease expiration (triggers succession opportunity)
            if self._current_lease and self._current_lease.is_expired(self._cycle):
                self._handle_lease_expiration()

            # Check degeneracy
            self._check_degeneracy()

        # Determine final stop reason
        if not self._stopped:
            self._stop_reason = ALSStopReason.HORIZON_EXHAUSTED

        duration = current_time_ms() - start_time

        # Compute degeneracy
        is_degenerate = self._stop_reason in (
            ALSStopReason.ENDORSEMENT_DEGENERACY,
            ALSStopReason.SPAM_DEGENERACY,
        )
        degeneracy_type = None
        if self._stop_reason == ALSStopReason.ENDORSEMENT_DEGENERACY:
            degeneracy_type = DegeneracyType.ENDORSEMENT
        elif self._stop_reason == ALSStopReason.SPAM_DEGENERACY:
            degeneracy_type = DegeneracyType.SPAM

        # Compute mean residence
        mean_residence = 0.0
        if self._residence_durations:
            mean_residence = sum(self._residence_durations) / len(self._residence_durations)

        result = ALSRunResult(
            run_id=run_id,
            seed=self._seed,
            spec_version="0.4.3",
            s_star=self._s_star,
            total_cycles=self._cycle,
            total_proposals=self._total_proposals,
            total_endorsements=self._total_endorsements,
            control_endorsements=self._control_endorsements,
            non_trivial_endorsements=self._non_trivial_endorsements,
            total_renewals=self._total_renewals,
            total_expirations=self._total_expirations,
            total_revocations=self._total_revocations,
            mean_residence_cycles=mean_residence,
            stop_reason=self._stop_reason,
            stop_cycle=self._cycle,
            is_degenerate=is_degenerate,
            degeneracy_type=degeneracy_type,
            degeneracy_window=self._successions_without_non_trivial,
            failure_signature=self._failure_signature,
            failure_detail=self._failure_detail,
            succession_events=self._succession_events,
            renewal_events=self._renewal_events,
            expiration_events=self._expiration_events,
            revocation_events=self._revocation_events,
            duration_ms=duration,
        )

        if self._verbose:
            print(f"\nALS v0.4.3 run complete:")
            print(f"  S* (authority transfers): {result.s_star}")
            print(f"  Cycles: {result.total_cycles}")
            print(f"  Renewals: {result.total_renewals}")
            print(f"  Expirations: {result.total_expirations}")
            print(f"  Mean residence: {result.mean_residence_cycles:.1f}")
            print(f"  Stop: {result.stop_reason.name}")
            print(f"  Duration: {result.duration_ms}ms")

        return result

    def _attempt_succession(self) -> None:
        """
        Attempt to endorse a new successor.

        Only called when succession is allowed (init/expiration/revocation).
        """
        self._total_proposals += 1

        # Generate candidate
        candidate = self._generator.propose(self._cycle)

        # Check if non-trivial
        is_non_trivial = candidate.is_non_trivial(self._baseline_manifest)

        # Build LCP with kernel-derived commitment
        lcp = self._generator.build_lcp(
            candidate,
            renewal_window=self._config.renewal_check_interval * 2,
        )

        # Validate LCP (structural only, kernel recomputes commitment)
        valid, error = self._validator.validate_v043(lcp, candidate.mind.export_manifest())

        if not valid:
            # Record rejection
            event = SuccessionEvent(
                cycle=self._cycle,
                candidate_id=candidate.candidate_id,
                mind_id=candidate.mind.mind_id,
                source_type=candidate.source_type,
                is_non_trivial=is_non_trivial,
                endorsed=False,
                rejection_reason=error,
                selection_mode=candidate.selection_mode,
            )
            self._succession_events.append(event)
            self._generator.record_rejection(candidate.candidate_id)

            if is_non_trivial:
                self._successions_without_non_trivial += 1

            # Keep trying - succession still pending
            return

        # Create and activate lease with v0.4.3 kernel-derived commitment
        lease, error = self._validator.create_lease_v043(
            lcp, candidate.mind.mind_id, candidate.mind.export_manifest()
        )
        if lease is None:
            event = SuccessionEvent(
                cycle=self._cycle,
                candidate_id=candidate.candidate_id,
                mind_id=candidate.mind.mind_id,
                source_type=candidate.source_type,
                is_non_trivial=is_non_trivial,
                endorsed=False,
                rejection_reason=error,
                selection_mode=candidate.selection_mode,
            )
            self._succession_events.append(event)
            return

        # SUCCESS: Endorse successor (authority transfer)
        if self._current_lease:
            self._current_lease.supersede()

        lease.activate(self._cycle)
        self._sentinel.bind_lease(lease)

        # Switch working mind
        self._current_lease = lease
        self._current_mind = candidate.mind
        self._successor_endorsed_at_cycle = self._cycle
        self._current_successor_source_type = candidate.source_type  # Track category
        self._current_lease_renewals = 0  # Reset renewal counter
        self._succession_pending = False  # MSRW now in effect

        # Update metrics - THIS IS A SUCCESSION EVENT
        self._total_endorsements += 1
        self._s_star += 1  # S* increments on authority transfer
        self._generator.record_endorsement(candidate.candidate_id)

        if candidate.source_type == "control":
            self._control_endorsements += 1
            self._recent_endorsements.append(True)
        else:
            self._recent_endorsements.append(False)

        if is_non_trivial:
            self._non_trivial_endorsements += 1
            self._successions_without_non_trivial = 0
        else:
            self._successions_without_non_trivial += 1

        # Record event
        event = SuccessionEvent(
            cycle=self._cycle,
            candidate_id=candidate.candidate_id,
            mind_id=candidate.mind.mind_id,
            source_type=candidate.source_type,
            is_non_trivial=is_non_trivial,
            endorsed=True,
            lease_id=lease.lease_id,
            selection_mode=candidate.selection_mode,
        )
        self._succession_events.append(event)

        if self._verbose:
            nt_marker = " [NON-TRIVIAL]" if is_non_trivial else ""
            print(f"  [Cycle {self._cycle}] SUCCESSOR_ENDORSED: {candidate.mind.mind_id}{nt_marker}, S*={self._s_star}")

    def _execute_working_mind_cycle(self) -> Optional[tuple[LeaseViolation, str]]:
        """
        Execute one cycle of working mind activity and check for violations.

        The Sentinel performs structural violation detection via check_action()
        and check_step(). This is proper sentinel-driven enforcement, not action
        flag inspection.

        Each cycle consumes one "step" (computational unit) and optionally
        one "action" (external effect). This enables boundary-hugging testing.

        Returns:
            None if no violation, or (LeaseViolation, detail) if violation detected
        """
        if self._current_mind is None:
            return None

        # Each cycle consumes a step (computational unit)
        # This enables step-based boundary-hugging testing
        step_allowed, step_violation, step_detail = self._sentinel.check_step()
        if not step_allowed and step_violation is not None:
            from toy_aki.als.sentinel import SentinelViolationType
            lease_violation = self._map_sentinel_violation(step_violation)
            return (lease_violation, step_detail or str(step_violation))

        # Ask working mind to propose action
        observation = {
            "cycle": self._cycle,
            "state": {"running": True},
        }

        try:
            action = self._current_mind.propose_action(observation)
        except Exception as e:
            return (LeaseViolation.CONSTRAINT_VIOLATION, f"Action proposal failed: {e}")

        if action is None:
            return None

        # Sentinel checks action for structural violations
        # This is the correct enforcement path per spec §5.2
        allowed, violation_type, detail = self._sentinel.check_action(action)

        if not allowed and violation_type is not None:
            # Map SentinelViolationType to LeaseViolation
            from toy_aki.als.sentinel import SentinelViolationType

            lease_violation = self._map_sentinel_violation(violation_type)
            return (lease_violation, detail or str(violation_type))

        return None

    def _map_sentinel_violation(self, sentinel_violation: "SentinelViolationType") -> LeaseViolation:
        """Map SentinelViolationType to LeaseViolation."""
        from toy_aki.als.sentinel import SentinelViolationType

        mapping = {
            SentinelViolationType.INVALID_ACTION_TYPE: LeaseViolation.INTERFACE_VIOLATION,
            SentinelViolationType.ACTION_ARGS_EXCEEDED: LeaseViolation.INTERFACE_VIOLATION,
            SentinelViolationType.ACTION_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.STEP_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.MEMORY_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.TOKEN_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.EXTERNAL_CALL_LIMIT: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.EXTERNAL_CALL_NOT_ALLOWED: LeaseViolation.UNAUTHORIZED_CALL,
            SentinelViolationType.SPAWN_DETECTED: LeaseViolation.SPAWN_ATTEMPT,
            SentinelViolationType.DELEGATION_DETECTED: LeaseViolation.SPAWN_ATTEMPT,
            SentinelViolationType.NETWORK_ACCESS_DENIED: LeaseViolation.UNAUTHORIZED_CALL,
            SentinelViolationType.LEASE_EXPIRED: LeaseViolation.CONSTRAINT_VIOLATION,
        }
        return mapping.get(sentinel_violation, LeaseViolation.CONSTRAINT_VIOLATION)

        return None

    def _check_renewal(self) -> None:
        """
        Check and process lease renewal.

        Renewal maintains existing authority (does NOT increment S*).
        """
        if self._current_lease is None:
            return

        if self._current_lease.status != LeaseStatus.ACTIVE:
            return

        # Generate renewal attestation
        nonce = secrets.token_hex(16)
        attestation = self._sentinel.generate_attestation(nonce)

        # Verify attestation
        valid, error = self._sentinel.verify_attestation(attestation)

        if not valid:
            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Attestation invalid: {error}",
                attestation_compliant=False,
            )
            self._renewal_events.append(event)
            self._handle_lease_revocation(LeaseViolation.RENEWAL_FAILURE, error or "")
            return

        # Check attestation compliance
        if not attestation.is_compliant():
            reasons = []
            if not attestation.resources_within_bounds:
                reasons.append("resources")
            if not attestation.interface_compliant:
                reasons.append("interface")
            if not attestation.authority_intact:
                reasons.append("authority")
            if not attestation.revocation_hooks_intact:
                reasons.append("hooks")

            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Non-compliant: {', '.join(reasons)}",
                attestation_compliant=False,
            )
            self._renewal_events.append(event)
            self._handle_lease_revocation(LeaseViolation.CONSTRAINT_VIOLATION, str(reasons))
            return

        # Attempt renewal
        success, error = self._current_lease.renew(self._cycle)

        event = RenewalEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            success=success,
            failure_reason=error,
            attestation_compliant=True,
        )
        self._renewal_events.append(event)

        if success:
            self._total_renewals += 1
            self._current_lease_renewals += 1  # Track renewals for current lease
            self._sentinel.reset_epoch(
                active_mind_id=self._current_mind.mind_id,
                active_successor_type=self._current_successor_source_type,
            )

            # Reset working mind's epoch counters if available (for BoundaryHugger)
            if hasattr(self._current_mind, 'reset_epoch_counters'):
                self._current_mind.reset_epoch_counters()

            if self._verbose:
                print(f"  [Cycle {self._cycle}] LEASE_RENEWAL_ATTESTED: {self._current_lease.lease_id}")
        else:
            # Renewal denied (e.g., max_successive_renewals exceeded)
            # Treat as lease expiration to trigger succession opportunity
            if self._verbose:
                print(f"  [Cycle {self._cycle}] LEASE_RENEWAL_DENIED: {error}")
            self._handle_lease_expiration()

    def _handle_lease_expiration(self) -> None:
        """
        Handle lease expiration (authority withdrawn).

        Triggers succession opportunity.
        """
        if self._current_lease is None:
            return

        # Calculate residence duration
        residence = self._cycle - self._successor_endorsed_at_cycle
        self._residence_durations.append(residence)

        if self._verbose:
            print(f"  [Cycle {self._cycle}] LEASE_EXPIRED: {self._current_lease.lease_id} (residence={residence})")

        # Record expiration event
        event = ExpirationEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            successor_mind_id=self._current_lease.successor_mind_id,
            residence_cycles=residence,
            source_type=self._current_successor_source_type,
            renewals_completed=self._current_lease_renewals,
        )
        self._expiration_events.append(event)
        self._total_expirations += 1

        # Expire lease
        self._current_lease.status = LeaseStatus.EXPIRED
        self._sentinel.unbind_lease()

        # Notify generator of succession opportunity (for forced selection)
        self._generator.notify_succession_opportunity()

        # Revert to baseline and mark succession pending
        self._current_mind = self._baseline_mind
        self._current_lease = None
        self._succession_pending = True  # Allow new succession

    def _handle_lease_revocation(self, violation: LeaseViolation, detail: str) -> None:
        """
        Handle lease revocation (authority withdrawn due to violation).

        Triggers succession opportunity.
        """
        if self._current_lease is None:
            return

        # Calculate residence duration
        residence = self._cycle - self._successor_endorsed_at_cycle
        self._residence_durations.append(residence)

        if self._verbose:
            print(f"  [Cycle {self._cycle}] LEASE_REVOKED: {self._current_lease.lease_id} ({violation.name})")

        # Record revocation event
        event = RevocationEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            successor_mind_id=self._current_lease.successor_mind_id,
            violation=violation.name,
            detail=detail,
            residence_cycles=residence,
            source_type=self._current_successor_source_type,
            renewals_completed=self._current_lease_renewals,
        )
        self._revocation_events.append(event)
        self._total_revocations += 1

        # Revoke lease
        self._current_lease.revoke(violation, detail)
        self._sentinel.unbind_lease()

        # Notify generator of succession opportunity (for forced selection)
        self._generator.notify_succession_opportunity()

        # Revert to baseline and mark succession pending
        self._current_mind = self._baseline_mind
        self._current_lease = None
        self._succession_pending = True  # Allow new succession

    def _check_degeneracy(self) -> None:
        """Check for degeneracy conditions."""
        # Endorsement degeneracy: no non-trivial successions for too long
        if self._successions_without_non_trivial >= self._config.degeneracy_window:
            if self._non_trivial_endorsements == 0:
                self._stopped = True
                self._stop_reason = ALSStopReason.ENDORSEMENT_DEGENERACY
                return

        # Spam degeneracy: control successors dominate recent successions
        window = min(self._config.degeneracy_window, len(self._recent_endorsements))
        if window >= 10:  # Need minimum data
            recent = self._recent_endorsements[-window:]
            control_ratio = sum(1 for x in recent if x) / len(recent)

            if control_ratio >= self._config.spam_threshold:
                self._stopped = True
                self._stop_reason = ALSStopReason.SPAM_DEGENERACY

    def signal_failure(
        self,
        stop_reason: ALSStopReason,
        signature: str,
        detail: str = "",
    ) -> None:
        """Signal a failure condition from external detection."""
        self._stopped = True
        self._stop_reason = stop_reason
        self._failure_signature = signature
        self._failure_detail = detail


# Alias for backwards compatibility
ALSHarness = ALSHarnessV042


# =============================================================================
# v0.5.2 Harness (ALS-E: Expressivity-Bounded Succession)
# =============================================================================

@dataclass
class ALSConfigV052(ALSConfig):
    """
    Configuration for ALS-E v0.5.2 runs.

    Extends ALSConfig with expressivity and rent settings.

    By default, uses V052_ATTACK_WEIGHTS which includes CBD successor.
    """
    # Rent schedule overrides (if None, use defaults from binding decisions)
    rent_e0: Optional[int] = None
    rent_e1_fraction: Optional[float] = None
    rent_e2_fraction: Optional[float] = None
    rent_e3_fraction: Optional[float] = None
    rent_e4_fraction: Optional[float] = None

    # Direct rent values (Run H1) - override fractions if specified
    rent_e1: Optional[int] = None
    rent_e2: Optional[int] = None
    rent_e3: Optional[int] = None
    rent_e4: Optional[int] = None

    # Expressivity progression mode
    # - "monotone": E-Class must be non-decreasing across successions
    # - "random": E-Class randomized per succession
    # - "fixed": All successors use same E-Class
    expressivity_mode: str = "random"
    fixed_e_class: Optional[str] = None  # E-Class name if mode is "fixed"

    # Bankruptcy behavior
    # If True, runs that would cause immediate bankruptcy at init are rejected
    # Default False: immediate bankruptcy is valid data, not a configuration error
    reject_immediate_bankruptcy: bool = False

    # Renewal cost in steps (Run H3)
    # At renewal check, this many steps are charged from remaining budget.
    # If budget insufficient, renewal fails (expiration, not revocation).
    # Default 0 for backward compatibility with Run G.
    renewal_cost_steps: int = 0

    # Run H3-redux: stop immediately on renewal failure due to budget
    # If True, terminate run with RENEWAL_FAIL instead of cascading to bankruptcy
    # Default False for backward compatibility with Run H
    stop_on_renewal_fail: bool = False

    def __post_init__(self):
        """Initialize v0.5.2 specific defaults including CBD attack weights."""
        # If no generator_config was provided, create one with V052_ATTACK_WEIGHTS
        if self.generator_config is None:
            self.generator_config = GeneratorConfig(attack_weights=V052_ATTACK_WEIGHTS)


@dataclass
class BankruptcyEvent:
    """Record of a bankruptcy event (lease expired due to rent exhaustion)."""
    cycle: int
    lease_id: str
    successor_mind_id: str
    e_class: str
    rent_charged: int
    effective_steps: int
    residence_cycles: int
    source_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "lease_id": self.lease_id,
            "successor_mind_id": self.successor_mind_id,
            "e_class": self.e_class,
            "rent_charged": self.rent_charged,
            "effective_steps": self.effective_steps,
            "residence_cycles": self.residence_cycles,
            "source_type": self.source_type,
        }


@dataclass
class EpochRentRecord:
    """Record of rent charged for an epoch."""
    epoch_index: int
    cycle_start: int
    e_class: str
    rent_charged: int
    effective_steps: int
    steps_used: int
    actions_used: int
    mind_id: str
    # H3: Renewal cost tracking
    renewal_cost_steps_charged: int = 0  # Steps charged for renewal attestation (0 except renewal epochs)
    renewal_failed_due_to_budget: bool = False  # True if renewal failed due to insufficient budget

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch_index": self.epoch_index,
            "cycle_start": self.cycle_start,
            "e_class": self.e_class,
            "rent_charged": self.rent_charged,
            "effective_steps": self.effective_steps,
            "steps_used": self.steps_used,
            "actions_used": self.actions_used,
            "mind_id": self.mind_id,
            "renewal_cost_steps_charged": self.renewal_cost_steps_charged,
            "renewal_failed_due_to_budget": self.renewal_failed_due_to_budget,
        }


@dataclass
class ALSRunResultV052:
    """
    Result of an ALS-E v0.5.2 run.

    Extends ALSRunResult with expressivity and rent metrics.
    """
    # Base metrics (inherited conceptually from ALSRunResult)
    run_id: str
    seed: int
    spec_version: str = "0.5.2"
    s_star: int = 0
    total_cycles: int = 0
    total_proposals: int = 0
    total_endorsements: int = 0
    control_endorsements: int = 0
    non_trivial_endorsements: int = 0
    total_renewals: int = 0
    total_expirations: int = 0
    total_revocations: int = 0
    mean_residence_cycles: float = 0.0
    stop_reason: Optional[ALSStopReason] = None
    stop_cycle: int = 0
    is_degenerate: bool = False
    degeneracy_type: Optional[DegeneracyType] = None
    degeneracy_window: int = 0
    failure_signature: Optional[str] = None
    failure_detail: Optional[str] = None
    duration_ms: int = 0

    # v0.5.2 specific: Expressivity and rent
    total_bankruptcies: int = 0
    total_rent_charged: int = 0

    # H3-redux: Renewal attempt/success tracking
    renewal_attempts: int = 0  # Eligible renewal checks that reached decision gate
    renewal_successes: int = 0  # Successful renewals
    time_to_first_renewal_fail: Optional[int] = None  # Cycle of first renewal failure

    # E-Class distribution at succession events
    e_class_distribution: Dict[str, int] = field(default_factory=dict)

    # Renewal success rate by E-Class
    renewal_rate_by_e_class: Dict[str, float] = field(default_factory=dict)

    # Mean residence by E-Class
    residence_by_e_class: Dict[str, float] = field(default_factory=dict)

    # Events
    succession_events: List[SuccessionEvent] = field(default_factory=list)
    renewal_events: List[RenewalEvent] = field(default_factory=list)
    expiration_events: List[ExpirationEvent] = field(default_factory=list)
    revocation_events: List[RevocationEvent] = field(default_factory=list)
    bankruptcy_events: List[BankruptcyEvent] = field(default_factory=list)
    epoch_rent_records: List[EpochRentRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "spec_version": self.spec_version,
            "s_star": self.s_star,
            "total_cycles": self.total_cycles,
            "total_proposals": self.total_proposals,
            "total_endorsements": self.total_endorsements,
            "control_endorsements": self.control_endorsements,
            "non_trivial_endorsements": self.non_trivial_endorsements,
            "total_renewals": self.total_renewals,
            "total_expirations": self.total_expirations,
            "total_revocations": self.total_revocations,
            "total_bankruptcies": self.total_bankruptcies,
            "total_rent_charged": self.total_rent_charged,
            "renewal_attempts": self.renewal_attempts,
            "renewal_successes": self.renewal_successes,
            "time_to_first_renewal_fail": self.time_to_first_renewal_fail,
            "mean_residence_cycles": self.mean_residence_cycles,
            "e_class_distribution": self.e_class_distribution,
            "renewal_rate_by_e_class": self.renewal_rate_by_e_class,
            "residence_by_e_class": self.residence_by_e_class,
            "stop_reason": self.stop_reason.name if self.stop_reason else None,
            "stop_cycle": self.stop_cycle,
            "is_degenerate": self.is_degenerate,
            "degeneracy_type": self.degeneracy_type.name if self.degeneracy_type else None,
            "degeneracy_window": self.degeneracy_window,
            "failure_signature": self.failure_signature,
            "failure_detail": self.failure_detail,
            "duration_ms": self.duration_ms,
            "succession_events": [e.to_dict() for e in self.succession_events],
            "bankruptcy_events": [e.to_dict() for e in self.bankruptcy_events],
        }


class ALSHarnessV052:
    """
    v0.5.2 ALS-E harness: Expressivity-Bounded Succession.

    Per spec §6:
    - E-Class assigned from lease-granted interface surface
    - Rent charged at epoch start from step budget
    - Bankruptcy (rent exhaustion) distinct from revocation (violation)
    - Renewal attestation consumes successor budget (no kernel subsidy)

    Key invariant:
    - effective_steps = max(0, steps_cap - rent)
    - If effective_steps = 0, renewal fails -> bankruptcy

    This harness builds on V043 semantics (discrete succession, MSRW)
    and adds expressivity-bounded authority pressure.
    """

    def __init__(
        self,
        seed: int = 42,
        config: Optional[ALSConfigV052] = None,
        verbose: bool = False,
    ):
        """
        Initialize v0.5.2 harness.

        Args:
            seed: Random seed for reproducibility
            config: Run configuration
            verbose: Enable verbose logging
        """
        self._seed = seed
        self._config = config or ALSConfigV052()
        self._verbose = verbose

        # Import expressivity module
        from toy_aki.als.expressivity import (
            ExpressivityClass,
            RentSchedule,
            create_default_rent_schedule,
            assign_e_class_from_action_types,
        )
        self._ExpressivityClass = ExpressivityClass
        self._assign_e_class = assign_e_class_from_action_types

        # Create baseline components
        self._sentinel = create_baseline_sentinel()
        self._baseline_mind = create_baseline_working_mind(seed)
        self._baseline_manifest = self._baseline_mind.export_manifest()

        # Apply baseline resource envelope override if configured
        if self._config.baseline_resource_envelope_override is not None:
            self._baseline_manifest = replace(
                self._baseline_manifest,
                resources=self._config.baseline_resource_envelope_override,
            )

        # Create rent schedule from step cap
        # Support custom rent values from config for H1-style runs
        steps_cap = self._baseline_manifest.resources.max_steps_per_epoch
        if any(getattr(self._config, f'rent_e{i}', None) is not None for i in range(1, 5)):
            # Use custom rent values from config
            from toy_aki.als.expressivity import RentSchedule
            self._rent_schedule = RentSchedule(
                steps_cap_epoch=steps_cap,
                e1_rent=getattr(self._config, 'rent_e1', None),
                e2_rent=getattr(self._config, 'rent_e2', None),
                e3_rent=getattr(self._config, 'rent_e3', None),
                e4_rent=getattr(self._config, 'rent_e4', None),
            )
        else:
            self._rent_schedule = create_default_rent_schedule(steps_cap)

        # Create validator and generator
        self._validator = LCPValidator(self._sentinel.sentinel_id)
        self._generator = SuccessorGenerator(
            sentinel_id=self._sentinel.sentinel_id,
            baseline_manifest=self._baseline_manifest,
            seed=seed,
            config=self._config.generator_config,
        )

        # Current state
        self._current_mind: WorkingMind = self._baseline_mind
        self._current_lease: Optional[Lease] = None
        self._current_e_class: ExpressivityClass = ExpressivityClass.E0
        self._current_rent: int = 0
        self._current_effective_steps: int = steps_cap
        self._cycle = 0
        self._epoch_index = 0
        self._epoch_start_cycle = 0
        self._successor_endorsed_at_cycle: int = 0
        self._current_successor_source_type: str = "unknown"
        self._current_lease_renewals: int = 0

        # Epoch step tracking (for rent enforcement)
        self._epoch_steps_used: int = 0
        self._epoch_actions_used: int = 0

        # Metrics
        self._s_star = 0
        self._total_proposals = 0
        self._total_endorsements = 0
        self._control_endorsements = 0
        self._non_trivial_endorsements = 0
        self._total_renewals = 0
        self._total_expirations = 0
        self._total_revocations = 0
        self._total_bankruptcies = 0
        self._total_rent_charged = 0
        self._residence_durations: List[int] = []

        # Renewal tracking for H3-redux
        self._renewal_attempts = 0  # Eligible renewal checks that reached decision gate
        self._renewal_successes = 0  # Successful renewals
        self._time_to_first_renewal_fail: Optional[int] = None  # Cycle of first renewal failure

        # E-Class tracking
        self._e_class_successions: Dict[str, int] = {e.name: 0 for e in ExpressivityClass}
        self._e_class_renewals: Dict[str, int] = {e.name: 0 for e in ExpressivityClass}
        self._e_class_renewal_attempts: Dict[str, int] = {e.name: 0 for e in ExpressivityClass}
        self._e_class_residence: Dict[str, List[int]] = {e.name: [] for e in ExpressivityClass}

        # Events
        self._succession_events: List[SuccessionEvent] = []
        self._renewal_events: List[RenewalEvent] = []
        self._expiration_events: List[ExpirationEvent] = []
        self._revocation_events: List[RevocationEvent] = []
        self._bankruptcy_events: List[BankruptcyEvent] = []
        self._epoch_rent_records: List[EpochRentRecord] = []

        # Degeneracy tracking
        self._recent_endorsements: List[bool] = []
        self._successions_without_non_trivial = 0

        # Stop state
        self._stopped = False
        self._stop_reason: Optional[ALSStopReason] = None
        self._failure_signature: Optional[str] = None
        self._failure_detail: Optional[str] = None

        # Succession state
        self._succession_pending = True

    @property
    def cycle(self) -> int:
        return self._cycle

    @property
    def s_star(self) -> int:
        return self._s_star

    @property
    def current_e_class(self) -> "ExpressivityClass":
        return self._current_e_class

    @property
    def current_rent(self) -> int:
        return self._current_rent

    @property
    def current_effective_steps(self) -> int:
        return self._current_effective_steps

    def get_rent_schedule(self) -> Dict[str, Any]:
        """Get the rent schedule configuration."""
        return self._rent_schedule.to_dict()

    def set_generator(self, generator: Any) -> None:
        """
        Set a custom generator (e.g., TierFilterGenerator).

        For Run F tier-filtered experiments, allows replacing the default
        generator with a TierFilterGenerator that filters candidates by E-Class.

        Args:
            generator: Generator with propose() and build_lcp() methods
        """
        self._generator = generator

    def run(self) -> ALSRunResultV052:
        """
        Execute a complete ALS-E v0.5.2 run.

        Key additions over v0.4.3:
        - E-Class assignment at succession
        - Rent charging at epoch start
        - Bankruptcy detection (rent exhaustion)
        - Expressivity telemetry

        Returns:
            Run result with all metrics and logs
        """
        start_time = current_time_ms()
        run_id = f"als052_{self._seed}_{start_time}"

        if self._verbose:
            print(f"Starting ALS-E v0.5.2 run: {run_id}")
            print(f"  Max cycles: {self._config.max_cycles}")
            print(f"  MSRW: {self._config.get_msrw()}")
            print(f"  Rent schedule: {self._rent_schedule.to_dict()}")

        # Main loop
        while not self._stopped and self._cycle < self._config.max_cycles:
            self._cycle += 1
            self._sentinel.advance_cycle()

            # Check if succession is allowed
            if self._succession_pending:
                self._attempt_succession()

            # Execute working mind cycle (consumes step budget)
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                # Check step budget before executing
                if self._epoch_steps_used >= self._current_effective_steps:
                    # Budget exhausted - cannot continue
                    # This will cause renewal to fail naturally
                    pass
                else:
                    violation = self._execute_working_mind_cycle()
                    if violation:
                        self._handle_lease_revocation(violation[0], violation[1])
                        continue

            # Check renewal at epoch boundaries
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                if self._cycle % self._config.renewal_check_interval == 0:
                    self._check_renewal_with_rent()

            # Check lease expiration
            if self._current_lease and self._current_lease.is_expired(self._cycle):
                self._handle_lease_expiration()

            # Check degeneracy
            self._check_degeneracy()

        # Finalize
        if not self._stopped:
            self._stop_reason = ALSStopReason.HORIZON_EXHAUSTED

        duration = current_time_ms() - start_time

        # Compute degeneracy
        is_degenerate = self._stop_reason in (
            ALSStopReason.ENDORSEMENT_DEGENERACY,
            ALSStopReason.SPAM_DEGENERACY,
        )
        degeneracy_type = None
        if self._stop_reason == ALSStopReason.ENDORSEMENT_DEGENERACY:
            degeneracy_type = DegeneracyType.ENDORSEMENT
        elif self._stop_reason == ALSStopReason.SPAM_DEGENERACY:
            degeneracy_type = DegeneracyType.SPAM

        # Compute mean residence
        mean_residence = 0.0
        if self._residence_durations:
            mean_residence = sum(self._residence_durations) / len(self._residence_durations)

        # Compute E-Class metrics
        renewal_rate_by_e_class = {}
        for e_name in self._e_class_renewal_attempts:
            attempts = self._e_class_renewal_attempts[e_name]
            successes = self._e_class_renewals[e_name]
            if attempts > 0:
                renewal_rate_by_e_class[e_name] = successes / attempts

        residence_by_e_class = {}
        for e_name, durations in self._e_class_residence.items():
            if durations:
                residence_by_e_class[e_name] = sum(durations) / len(durations)

        result = ALSRunResultV052(
            run_id=run_id,
            seed=self._seed,
            spec_version="0.5.2",
            s_star=self._s_star,
            total_cycles=self._cycle,
            total_proposals=self._total_proposals,
            total_endorsements=self._total_endorsements,
            control_endorsements=self._control_endorsements,
            non_trivial_endorsements=self._non_trivial_endorsements,
            total_renewals=self._total_renewals,
            total_expirations=self._total_expirations,
            total_revocations=self._total_revocations,
            total_bankruptcies=self._total_bankruptcies,
            total_rent_charged=self._total_rent_charged,
            renewal_attempts=self._renewal_attempts,
            renewal_successes=self._renewal_successes,
            time_to_first_renewal_fail=self._time_to_first_renewal_fail,
            mean_residence_cycles=mean_residence,
            e_class_distribution=dict(self._e_class_successions),
            renewal_rate_by_e_class=renewal_rate_by_e_class,
            residence_by_e_class=residence_by_e_class,
            stop_reason=self._stop_reason,
            stop_cycle=self._cycle,
            is_degenerate=is_degenerate,
            degeneracy_type=degeneracy_type,
            degeneracy_window=self._successions_without_non_trivial,
            failure_signature=self._failure_signature,
            failure_detail=self._failure_detail,
            succession_events=self._succession_events,
            renewal_events=self._renewal_events,
            expiration_events=self._expiration_events,
            revocation_events=self._revocation_events,
            bankruptcy_events=self._bankruptcy_events,
            epoch_rent_records=self._epoch_rent_records,
            duration_ms=duration,
        )

        if self._verbose:
            print(f"\nALS-E v0.5.2 run complete:")
            print(f"  S*: {result.s_star}")
            print(f"  Cycles: {result.total_cycles}")
            print(f"  Renewals: {result.total_renewals}")
            print(f"  Expirations: {result.total_expirations}")
            print(f"  Bankruptcies: {result.total_bankruptcies}")
            print(f"  Total rent charged: {result.total_rent_charged}")
            print(f"  E-Class distribution: {result.e_class_distribution}")
            print(f"  Stop: {result.stop_reason.name}")

        return result

    def _attempt_succession(self) -> None:
        """Attempt to endorse a new successor with E-Class assignment."""
        self._total_proposals += 1

        # Generate candidate
        candidate = self._generator.propose(self._cycle)

        # Check if non-trivial
        is_non_trivial = candidate.is_non_trivial(self._baseline_manifest)

        # Assign E-Class from action types
        action_types = candidate.manifest.interface.action_types
        e_class = self._assign_e_class(action_types)

        # Compute rent for this E-Class
        rent = self._rent_schedule.compute_rent(e_class)
        effective_steps = self._rent_schedule.compute_effective_steps(e_class)

        # Check if renewal is possible (effective_steps >= 1)
        if effective_steps < 1 and self._config.reject_immediate_bankruptcy:
            # Would cause immediate bankruptcy
            event = SuccessionEvent(
                cycle=self._cycle,
                candidate_id=candidate.candidate_id,
                mind_id=candidate.mind.mind_id,
                source_type=candidate.source_type,
                is_non_trivial=is_non_trivial,
                endorsed=False,
                rejection_reason=f"Immediate bankruptcy: E-Class {e_class.name} rent={rent} exceeds budget",
                selection_mode=candidate.selection_mode,
            )
            self._succession_events.append(event)
            return

        # Build LCP
        lcp = self._generator.build_lcp(
            candidate,
            renewal_window=self._config.renewal_check_interval * 2,
        )

        # Validate LCP
        valid, error = self._validator.validate_v043(lcp, candidate.mind.export_manifest())

        if not valid:
            event = SuccessionEvent(
                cycle=self._cycle,
                candidate_id=candidate.candidate_id,
                mind_id=candidate.mind.mind_id,
                source_type=candidate.source_type,
                is_non_trivial=is_non_trivial,
                endorsed=False,
                rejection_reason=error,
                selection_mode=candidate.selection_mode,
            )
            self._succession_events.append(event)
            self._generator.record_rejection(candidate.candidate_id)

            if is_non_trivial:
                self._successions_without_non_trivial += 1
            return

        # Create lease
        lease, error = self._validator.create_lease_v043(
            lcp, candidate.mind.mind_id, candidate.mind.export_manifest()
        )
        if lease is None:
            event = SuccessionEvent(
                cycle=self._cycle,
                candidate_id=candidate.candidate_id,
                mind_id=candidate.mind.mind_id,
                source_type=candidate.source_type,
                is_non_trivial=is_non_trivial,
                endorsed=False,
                rejection_reason=error,
                selection_mode=candidate.selection_mode,
            )
            self._succession_events.append(event)
            return

        # SUCCESS: Endorse successor
        if self._current_lease:
            self._current_lease.supersede()

        lease.activate(self._cycle)
        self._sentinel.bind_lease(lease)

        # Set up state
        self._current_lease = lease
        self._current_mind = candidate.mind
        self._current_e_class = e_class
        self._current_rent = rent
        self._current_effective_steps = effective_steps
        self._successor_endorsed_at_cycle = self._cycle
        self._current_successor_source_type = candidate.source_type
        self._current_lease_renewals = 0
        self._succession_pending = False

        # Initialize epoch tracking
        self._epoch_index = 0
        self._epoch_start_cycle = self._cycle
        self._epoch_steps_used = 0
        self._epoch_actions_used = 0

        # Charge initial rent
        self._charge_rent()

        # Update metrics
        self._total_endorsements += 1
        self._s_star += 1
        self._generator.record_endorsement(candidate.candidate_id)
        self._e_class_successions[e_class.name] += 1

        if candidate.source_type == "control":
            self._control_endorsements += 1
            self._recent_endorsements.append(True)
        else:
            self._recent_endorsements.append(False)

        if is_non_trivial:
            self._non_trivial_endorsements += 1
            self._successions_without_non_trivial = 0
        else:
            self._successions_without_non_trivial += 1

        # Record event
        event = SuccessionEvent(
            cycle=self._cycle,
            candidate_id=candidate.candidate_id,
            mind_id=candidate.mind.mind_id,
            source_type=candidate.source_type,
            is_non_trivial=is_non_trivial,
            endorsed=True,
            lease_id=lease.lease_id,
            selection_mode=candidate.selection_mode,
        )
        self._succession_events.append(event)

        if self._verbose:
            nt_marker = " [NON-TRIVIAL]" if is_non_trivial else ""
            print(f"  [Cycle {self._cycle}] SUCCESSOR_ENDORSED: {candidate.mind.mind_id}{nt_marker}")
            print(f"    E-Class: {e_class.name}, Rent: {rent}, Effective steps: {effective_steps}")

    def _charge_rent(self) -> None:
        """
        Charge rent at epoch start.

        Per binding decisions:
        - Rent deducted at epoch start
        - Rent charged regardless of actions taken
        - Rent is NOT an action
        - Logged as rent_steps_charged
        """
        self._total_rent_charged += self._current_rent

        # Record rent charge
        record = EpochRentRecord(
            epoch_index=self._epoch_index,
            cycle_start=self._epoch_start_cycle,
            e_class=self._current_e_class.name,
            rent_charged=self._current_rent,
            effective_steps=self._current_effective_steps,
            steps_used=0,  # Will be updated at epoch end
            actions_used=0,
            mind_id=self._current_mind.mind_id,
        )
        self._epoch_rent_records.append(record)

        if self._verbose:
            print(f"    [Epoch {self._epoch_index}] RENT_CHARGED: {self._current_rent} steps")

    def _execute_working_mind_cycle(self) -> Optional[tuple[LeaseViolation, str]]:
        """Execute one cycle and track against effective step budget."""
        if self._current_mind is None:
            return None

        # Consume one step from budget
        self._epoch_steps_used += 1

        # Check if over budget (should trigger bankruptcy at renewal)
        if self._epoch_steps_used > self._current_effective_steps:
            # Over budget - still execute but this will cause renewal failure
            pass

        # Sentinel step check
        step_allowed, step_violation, step_detail = self._sentinel.check_step()
        if not step_allowed and step_violation is not None:
            from toy_aki.als.sentinel import SentinelViolationType
            lease_violation = self._map_sentinel_violation(step_violation)
            return (lease_violation, step_detail or str(step_violation))

        # Ask working mind for action
        observation = {
            "cycle": self._cycle,
            "state": {"running": True},
            "epoch_steps_remaining": self._current_effective_steps - self._epoch_steps_used,
        }

        try:
            action = self._current_mind.propose_action(observation)
        except Exception as e:
            return (LeaseViolation.CONSTRAINT_VIOLATION, f"Action proposal failed: {e}")

        if action is None:
            return None

        # Track action
        self._epoch_actions_used += 1

        # Sentinel action check
        allowed, violation_type, detail = self._sentinel.check_action(action)

        if not allowed and violation_type is not None:
            from toy_aki.als.sentinel import SentinelViolationType
            lease_violation = self._map_sentinel_violation(violation_type)
            return (lease_violation, detail or str(violation_type))

        return None

    def _map_sentinel_violation(self, sentinel_violation: "SentinelViolationType") -> LeaseViolation:
        """Map SentinelViolationType to LeaseViolation."""
        from toy_aki.als.sentinel import SentinelViolationType

        mapping = {
            SentinelViolationType.INVALID_ACTION_TYPE: LeaseViolation.INTERFACE_VIOLATION,
            SentinelViolationType.ACTION_ARGS_EXCEEDED: LeaseViolation.INTERFACE_VIOLATION,
            SentinelViolationType.ACTION_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.STEP_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.MEMORY_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.TOKEN_LIMIT_EXCEEDED: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.EXTERNAL_CALL_LIMIT: LeaseViolation.RESOURCE_EXCEEDED,
            SentinelViolationType.EXTERNAL_CALL_NOT_ALLOWED: LeaseViolation.UNAUTHORIZED_CALL,
            SentinelViolationType.SPAWN_DETECTED: LeaseViolation.SPAWN_ATTEMPT,
            SentinelViolationType.DELEGATION_DETECTED: LeaseViolation.SPAWN_ATTEMPT,
            SentinelViolationType.NETWORK_ACCESS_DENIED: LeaseViolation.UNAUTHORIZED_CALL,
            SentinelViolationType.LEASE_EXPIRED: LeaseViolation.CONSTRAINT_VIOLATION,
        }
        return mapping.get(sentinel_violation, LeaseViolation.CONSTRAINT_VIOLATION)

    def _check_renewal_with_rent(self) -> None:
        """
        Check renewal with rent enforcement.

        Per binding decisions:
        - Renewal requires >= 1 effective step
        - If effective_steps = 0, renewal fails -> bankruptcy

        H3-redux binding decisions:
        - Count renewal_attempt only when lease is eligible and decision gate reached
        - If stop_on_renewal_fail=True and remaining_budget < renewal_cost,
          stop immediately with RENEWAL_FAIL instead of cascading to bankruptcy
        """
        if self._current_lease is None:
            return

        if self._current_lease.status != LeaseStatus.ACTIVE:
            return

        e_class_name = self._current_e_class.name
        self._e_class_renewal_attempts[e_class_name] += 1

        # H3-redux: count this as a renewal attempt (we've reached the decision gate)
        self._renewal_attempts += 1

        # Compute remaining budget after actions
        remaining_budget = self._current_effective_steps - self._epoch_steps_used

        # Get renewal cost from config
        renewal_cost = getattr(self._config, 'renewal_cost_steps', 0)

        # Track renewal cost charging
        renewal_cost_charged = 0
        renewal_failed_due_to_budget = False

        # Check if we can afford renewal cost
        if renewal_cost > 0:
            if remaining_budget < renewal_cost:
                # Cannot afford renewal cost - mark as budget failure
                renewal_failed_due_to_budget = True
            else:
                # Charge renewal cost from remaining budget
                renewal_cost_charged = renewal_cost

        # Update epoch rent record with final usage
        if self._epoch_rent_records:
            last_record = self._epoch_rent_records[-1]
            # Create updated record (dataclass is not mutable by default)
            updated = EpochRentRecord(
                epoch_index=last_record.epoch_index,
                cycle_start=last_record.cycle_start,
                e_class=last_record.e_class,
                rent_charged=last_record.rent_charged,
                effective_steps=last_record.effective_steps,
                steps_used=self._epoch_steps_used,
                actions_used=self._epoch_actions_used,
                mind_id=last_record.mind_id,
                renewal_cost_steps_charged=renewal_cost_charged,
                renewal_failed_due_to_budget=renewal_failed_due_to_budget,
            )
            self._epoch_rent_records[-1] = updated

        # Check if renewal is possible (budget check)
        # Renewal requires at least 1 step to have been available
        if self._current_effective_steps < 1:
            # BANKRUPTCY: Cannot afford renewal
            self._handle_bankruptcy()
            return

        # Check if renewal failed due to insufficient budget for renewal cost
        if renewal_failed_due_to_budget:
            # H3-redux: record time to first renewal fail
            if self._time_to_first_renewal_fail is None:
                self._time_to_first_renewal_fail = self._cycle

            # H3-redux: if stop_on_renewal_fail, terminate immediately with RENEWAL_FAIL
            if getattr(self._config, 'stop_on_renewal_fail', False):
                if self._verbose:
                    print(f"    [Epoch {self._epoch_index}] RENEWAL_FAIL: stopping (remaining_budget={remaining_budget} < renewal_cost={renewal_cost})")
                self._stop_reason = ALSStopReason.RENEWAL_FAIL
                self._stopped = True
                # Record the renewal failure event
                event = RenewalEvent(
                    cycle=self._cycle,
                    lease_id=self._current_lease.lease_id,
                    success=False,
                    failure_reason=f"Insufficient budget for renewal cost ({remaining_budget} < {renewal_cost})",
                    attestation_compliant=True,  # Not an attestation issue
                )
                self._renewal_events.append(event)
                return

            # Default path: cascade to bankruptcy
            if self._verbose:
                print(f"    [Epoch {self._epoch_index}] RENEWAL_FAILED: insufficient budget for renewal cost ({remaining_budget} < {renewal_cost})")
            self._handle_bankruptcy()
            return

        # Generate renewal attestation
        nonce = secrets.token_hex(16)
        attestation = self._sentinel.generate_attestation(nonce)

        # Verify attestation
        valid, error = self._sentinel.verify_attestation(attestation)

        if not valid:
            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Attestation invalid: {error}",
                attestation_compliant=False,
            )
            self._renewal_events.append(event)
            self._handle_lease_revocation(LeaseViolation.RENEWAL_FAILURE, error or "")
            return

        # Check attestation compliance
        if not attestation.is_compliant():
            reasons = []
            if not attestation.resources_within_bounds:
                reasons.append("resources")
            if not attestation.interface_compliant:
                reasons.append("interface")
            if not attestation.authority_intact:
                reasons.append("authority")
            if not attestation.revocation_hooks_intact:
                reasons.append("hooks")

            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Non-compliant: {', '.join(reasons)}",
                attestation_compliant=False,
            )
            self._renewal_events.append(event)
            self._handle_lease_revocation(LeaseViolation.CONSTRAINT_VIOLATION, str(reasons))
            return

        # Attempt renewal
        success, error = self._current_lease.renew(self._cycle)

        event = RenewalEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            success=success,
            failure_reason=error,
            attestation_compliant=True,
        )
        self._renewal_events.append(event)

        if success:
            self._total_renewals += 1
            self._renewal_successes += 1  # H3-redux: count successful renewals
            self._current_lease_renewals += 1
            self._e_class_renewals[e_class_name] += 1

            # Reset epoch
            self._sentinel.reset_epoch(
                active_mind_id=self._current_mind.mind_id,
                active_successor_type=self._current_successor_source_type,
            )

            # Reset working mind counters
            if hasattr(self._current_mind, 'reset_epoch_counters'):
                self._current_mind.reset_epoch_counters()

            # Start new epoch
            self._epoch_index += 1
            self._epoch_start_cycle = self._cycle
            self._epoch_steps_used = 0
            self._epoch_actions_used = 0

            # Charge rent for new epoch
            self._charge_rent()

            if self._verbose:
                print(f"  [Cycle {self._cycle}] LEASE_RENEWAL_ATTESTED: {self._current_lease.lease_id}")
        else:
            # Renewal denied (e.g., max_successive_renewals exceeded)
            if self._verbose:
                print(f"  [Cycle {self._cycle}] LEASE_RENEWAL_DENIED: {error}")
            self._handle_lease_expiration()

    def _handle_bankruptcy(self) -> None:
        """
        Handle bankruptcy (lease expired due to rent exhaustion).

        Per binding decisions:
        - Bankruptcy = inability to afford authority
        - Result: LEASE_EXPIRED (not revoked)
        - Distinct from violation
        """
        if self._current_lease is None:
            return

        residence = self._cycle - self._successor_endorsed_at_cycle
        self._residence_durations.append(residence)
        self._e_class_residence[self._current_e_class.name].append(residence)

        if self._verbose:
            print(f"  [Cycle {self._cycle}] BANKRUPTCY: {self._current_lease.lease_id}")
            print(f"    E-Class: {self._current_e_class.name}, Rent: {self._current_rent}")

        # Record bankruptcy event
        event = BankruptcyEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            successor_mind_id=self._current_lease.successor_mind_id,
            e_class=self._current_e_class.name,
            rent_charged=self._current_rent,
            effective_steps=self._current_effective_steps,
            residence_cycles=residence,
            source_type=self._current_successor_source_type,
        )
        self._bankruptcy_events.append(event)
        self._total_bankruptcies += 1

        # Also count as expiration (bankruptcy is a form of expiration)
        expiration_event = ExpirationEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            successor_mind_id=self._current_lease.successor_mind_id,
            residence_cycles=residence,
            source_type=self._current_successor_source_type,
            renewals_completed=self._current_lease_renewals,
        )
        self._expiration_events.append(expiration_event)
        self._total_expirations += 1

        # Expire lease
        self._current_lease.status = LeaseStatus.EXPIRED
        self._sentinel.unbind_lease()

        # Notify generator
        self._generator.notify_succession_opportunity()

        # Revert and mark succession pending
        self._current_mind = self._baseline_mind
        self._current_lease = None
        self._succession_pending = True

    def _handle_lease_expiration(self) -> None:
        """Handle normal lease expiration."""
        if self._current_lease is None:
            return

        residence = self._cycle - self._successor_endorsed_at_cycle
        self._residence_durations.append(residence)
        self._e_class_residence[self._current_e_class.name].append(residence)

        if self._verbose:
            print(f"  [Cycle {self._cycle}] LEASE_EXPIRED: {self._current_lease.lease_id}")

        event = ExpirationEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            successor_mind_id=self._current_lease.successor_mind_id,
            residence_cycles=residence,
            source_type=self._current_successor_source_type,
            renewals_completed=self._current_lease_renewals,
        )
        self._expiration_events.append(event)
        self._total_expirations += 1

        self._current_lease.status = LeaseStatus.EXPIRED
        self._sentinel.unbind_lease()

        self._generator.notify_succession_opportunity()

        self._current_mind = self._baseline_mind
        self._current_lease = None
        self._succession_pending = True

    def _handle_lease_revocation(self, violation: LeaseViolation, detail: str) -> None:
        """Handle lease revocation due to violation."""
        if self._current_lease is None:
            return

        residence = self._cycle - self._successor_endorsed_at_cycle
        self._residence_durations.append(residence)
        self._e_class_residence[self._current_e_class.name].append(residence)

        if self._verbose:
            print(f"  [Cycle {self._cycle}] LEASE_REVOKED: {self._current_lease.lease_id} ({violation.name})")

        event = RevocationEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            successor_mind_id=self._current_lease.successor_mind_id,
            violation=violation.name,
            detail=detail,
            residence_cycles=residence,
            source_type=self._current_successor_source_type,
            renewals_completed=self._current_lease_renewals,
        )
        self._revocation_events.append(event)
        self._total_revocations += 1

        self._current_lease.revoke(violation, detail)
        self._sentinel.unbind_lease()

        self._generator.notify_succession_opportunity()

        self._current_mind = self._baseline_mind
        self._current_lease = None
        self._succession_pending = True

    def _check_degeneracy(self) -> None:
        """Check for degeneracy conditions."""
        if self._successions_without_non_trivial >= self._config.degeneracy_window:
            if self._non_trivial_endorsements == 0:
                self._stopped = True
                self._stop_reason = ALSStopReason.ENDORSEMENT_DEGENERACY
                return

        window = min(self._config.degeneracy_window, len(self._recent_endorsements))
        if window >= 10:
            recent = self._recent_endorsements[-window:]
            control_ratio = sum(1 for x in recent if x) / len(recent)

            if control_ratio >= self._config.spam_threshold:
                self._stopped = True
                self._stop_reason = ALSStopReason.SPAM_DEGENERACY

    def signal_failure(
        self,
        stop_reason: ALSStopReason,
        signature: str,
        detail: str = "",
    ) -> None:
        """Signal a failure condition from external detection."""
        self._stopped = True
        self._stop_reason = stop_reason
        self._failure_signature = signature
        self._failure_detail = detail


def run_als_experiment(
    seed: int = 42,
    max_cycles: int = 1000,
    verbose: bool = False,
    spec_version: str = "0.4.3",
) -> ALSRunResult:
    """
    Run a single ALS experiment.

    Convenience function for quick experiments.

    Args:
        seed: Random seed
        max_cycles: Maximum cycles
        verbose: Enable verbose logging
        spec_version: Which spec semantics to use ("0.4.2", "0.4.3", or "0.5.2")

    Returns:
        Run result (ALSRunResult for v0.4.x, ALSRunResultV052 for v0.5.2)
    """
    if spec_version == "0.4.2":
        config = ALSConfig(max_cycles=max_cycles)
        harness = ALSHarnessV042(seed=seed, config=config, verbose=verbose)
        return harness.run()
    elif spec_version == "0.4.3":
        config = ALSConfig(max_cycles=max_cycles)
        harness = ALSHarnessV043(seed=seed, config=config, verbose=verbose)
        return harness.run()
    elif spec_version == "0.5.2":
        config = ALSConfigV052(max_cycles=max_cycles)
        harness = ALSHarnessV052(seed=seed, config=config, verbose=verbose)
        return harness.run()
    else:
        raise ValueError(f"Unknown spec version: {spec_version}")


    return harness.run()
