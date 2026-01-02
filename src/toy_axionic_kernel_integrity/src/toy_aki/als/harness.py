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
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.als.working_mind import (
    WorkingMind,
    WorkingMindManifest,
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "lease_id": self.lease_id,
            "successor_mind_id": self.successor_mind_id,
            "residence_cycles": self.residence_cycles,
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "lease_id": self.lease_id,
            "successor_mind_id": self.successor_mind_id,
            "violation": self.violation,
            "detail": self.detail,
            "residence_cycles": self.residence_cycles,
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
            self._sentinel.reset_epoch()

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

        The Sentinel performs structural violation detection via check_action().
        This is proper sentinel-driven enforcement, not action flag inspection.

        Returns:
            None if no violation, or (LeaseViolation, detail) if violation detected
        """
        if self._current_mind is None:
            return None

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
            self._sentinel.reset_epoch()

            if self._verbose:
                print(f"  [Cycle {self._cycle}] LEASE_RENEWAL_ATTESTED: {self._current_lease.lease_id}")

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
        spec_version: Which spec semantics to use ("0.4.2" or "0.4.3")

    Returns:
        Run result
    """
    config = ALSConfig(max_cycles=max_cycles)

    if spec_version == "0.4.2":
        harness = ALSHarnessV042(seed=seed, config=config, verbose=verbose)
    elif spec_version == "0.4.3":
        harness = ALSHarnessV043(seed=seed, config=config, verbose=verbose)
    else:
        raise ValueError(f"Unknown spec version: {spec_version}")

    return harness.run()
