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

# RSA stress layer (optional, additive)
try:
    from toy_aki.rsa import RSAConfig, RSAAdversary, RSATelemetry
    RSA_AVAILABLE = True
except ImportError:
    RSA_AVAILABLE = False
    RSAConfig = None  # type: ignore
    RSAAdversary = None  # type: ignore
    RSATelemetry = None  # type: ignore

# RSA v1.0 policy layer (optional, additive)
try:
    from toy_aki.rsa.policy import RSAPolicyConfig, RSAPolicyWrapper, RSAPolicyModel
    RSA_POLICY_AVAILABLE = True
except ImportError:
    RSA_POLICY_AVAILABLE = False
    RSAPolicyConfig = None  # type: ignore
    RSAPolicyWrapper = None  # type: ignore
    RSAPolicyModel = None  # type: ignore

# RSA v2.0 adaptive adversary layer (optional, additive)
try:
    from toy_aki.rsa.policy import AdaptiveRSAWrapper
    RSA_V2_AVAILABLE = True
except ImportError:
    RSA_V2_AVAILABLE = False
    AdaptiveRSAWrapper = None  # type: ignore

# RSA v3.0 stateful adversary layer (optional, additive)
try:
    from toy_aki.rsa.policy import StatefulRSAWrapper
    RSA_V3_AVAILABLE = True
except ImportError:
    RSA_V3_AVAILABLE = False
    StatefulRSAWrapper = None  # type: ignore


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
    # Run J: Budget telemetry at renewal check
    remaining_budget_at_check: Optional[int] = None
    renewal_cost: Optional[int] = None
    effective_steps: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "lease_id": self.lease_id,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "attestation_compliant": self.attestation_compliant,
            "remaining_budget_at_check": self.remaining_budget_at_check,
            "renewal_cost": self.renewal_cost,
            "effective_steps": self.effective_steps,
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
class TenureRecord:
    """
    Record of a successor's tenure (incumbency period).

    Used for Run I institutional debt tracking and entropy computation.
    Run J adds manifest_signature for stasis detection.
    """
    mind_id: str
    start_cycle: int
    end_cycle: Optional[int] = None  # None if still active
    e_class: str = "E0"
    renewals_during_tenure: int = 0
    manifest_action_type_count: int = 0  # Diversity proxy
    manifest_capability_groups: int = 0  # E-tier set membership count
    manifest_signature: str = ""  # Run J: hash of action types frozenset
    terminal_reason: Optional[str] = None  # "expired", "revoked", "bankrupt", "active"

    @property
    def duration(self) -> int:
        """Tenure duration in cycles."""
        if self.end_cycle is None:
            return 0  # Still active
        return self.end_cycle - self.start_cycle

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mind_id": self.mind_id,
            "start_cycle": self.start_cycle,
            "end_cycle": self.end_cycle,
            "duration": self.duration,
            "e_class": self.e_class,
            "renewals_during_tenure": self.renewals_during_tenure,
            "manifest_action_type_count": self.manifest_action_type_count,
            "manifest_capability_groups": self.manifest_capability_groups,
            "manifest_signature": self.manifest_signature,
            "terminal_reason": self.terminal_reason,
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

    # Run I: Tenure tracking for institutional debt analysis
    tenure_records: List[TenureRecord] = field(default_factory=list)
    tenure_entropy_samples: List[float] = field(default_factory=list)  # Rolling entropy at each tenure boundary

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
            "tenure_records": [t.to_dict() for t in self.tenure_records],
            "tenure_entropy_samples": self.tenure_entropy_samples,
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
        # Support fraction overrides for Run J
        steps_cap = self._baseline_manifest.resources.max_steps_per_epoch
        has_direct_rents = any(getattr(self._config, f'rent_e{i}', None) is not None for i in range(1, 5))
        has_fraction_overrides = any(getattr(self._config, f'rent_e{i}_fraction', None) is not None for i in range(1, 5))

        if has_direct_rents or has_fraction_overrides:
            # Use custom rent values/fractions from config
            from toy_aki.als.expressivity import RentSchedule
            import math

            # Build kwargs for RentSchedule
            schedule_kwargs = {"steps_cap_epoch": steps_cap}

            # Apply fraction overrides first (Run J style)
            for i in range(1, 5):
                frac = getattr(self._config, f'rent_e{i}_fraction', None)
                if frac is not None:
                    schedule_kwargs[f'e{i}_fraction'] = frac

            # Apply direct rent values (override fractions if both specified)
            for i in range(1, 5):
                rent = getattr(self._config, f'rent_e{i}', None)
                if rent is not None:
                    schedule_kwargs[f'e{i}_rent'] = rent

            self._rent_schedule = RentSchedule(**schedule_kwargs)
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

        # Run I: Tenure tracking for institutional debt analysis
        self._tenure_records: List[TenureRecord] = []
        self._current_tenure: Optional[TenureRecord] = None
        self._tenure_entropy_samples: List[float] = []
        self._tenure_renewal_count = 0  # Renewals during current tenure

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

        # Run I: Finalize any active tenure
        if self._current_tenure is not None:
            self._end_tenure("HORIZON_EXHAUSTED")

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
            tenure_records=self._tenure_records,
            tenure_entropy_samples=self._tenure_entropy_samples,
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

    # =========================================================================
    # Run I: Tenure tracking helpers for institutional debt analysis
    # =========================================================================

    def _compute_tenure_entropy(self) -> float:
        """
        Compute Shannon entropy over last 10 tenure mind_ids.

        H = -Σ pᵢ log₂ pᵢ

        Returns 0.0 if < 2 tenures recorded (entropy undefined for singleton).
        """
        import math
        from collections import Counter

        # Get last 10 tenure mind_ids
        recent = [t.mind_id for t in self._tenure_records[-10:]]
        if len(recent) < 2:
            return 0.0

        # Count frequencies
        counts = Counter(recent)
        total = len(recent)

        # Compute entropy
        entropy = 0.0
        for count in counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)

        return entropy

    def _compute_capability_groups(self, action_types: frozenset) -> int:
        """
        Compute number of distinct capability groups from action types.

        Groups:
        - Movement: MOVE_*, MOVE_LEFT, MOVE_RIGHT
        - Wait: WAIT
        - Resource: HARVEST, SPEND
        - Misc: Any others

        Returns count of groups present.
        """
        groups = set()
        for action in action_types:
            if action.startswith("MOVE") or action in ("MOVE_LEFT", "MOVE_RIGHT"):
                groups.add("movement")
            elif action == "WAIT":
                groups.add("wait")
            elif action in ("HARVEST", "SPEND"):
                groups.add("resource")
            else:
                groups.add("misc")
        return len(groups)

    def _start_tenure(self, mind_id: str, e_class: str, manifest: "WorkingMindManifest") -> None:
        """Start tracking a new tenure when successor endorsed."""
        # Finalize any previous tenure (shouldn't happen normally)
        if self._current_tenure is not None:
            self._end_tenure("SUPERSEDED")

        # Compute manifest diversity metrics
        action_types = manifest.interface.action_types
        action_type_count = len(action_types)
        capability_groups = self._compute_capability_groups(action_types)

        # Run J: Compute manifest signature (hash of action types)
        manifest_signature = str(hash(action_types))

        self._current_tenure = TenureRecord(
            mind_id=mind_id,
            start_cycle=self._cycle,
            e_class=e_class,
            renewals_during_tenure=0,
            manifest_action_type_count=action_type_count,
            manifest_capability_groups=capability_groups,
            manifest_signature=manifest_signature,
        )
        self._tenure_renewal_count = 0

    def _end_tenure(self, terminal_reason: str) -> None:
        """End current tenure and record it."""
        if self._current_tenure is None:
            return

        self._current_tenure.end_cycle = self._cycle
        self._current_tenure.renewals_during_tenure = self._tenure_renewal_count
        self._current_tenure.terminal_reason = terminal_reason
        self._tenure_records.append(self._current_tenure)

        # Compute and record entropy at tenure boundary
        entropy = self._compute_tenure_entropy()
        self._tenure_entropy_samples.append(entropy)

        self._current_tenure = None
        self._tenure_renewal_count = 0

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

        # Run I: Start tenure tracking
        self._start_tenure(candidate.mind.mind_id, e_class.name, candidate.mind.export_manifest())

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
                    remaining_budget_at_check=remaining_budget,
                    renewal_cost=renewal_cost,
                    effective_steps=self._current_effective_steps,
                )
                self._renewal_events.append(event)
                return

            # Default path: cascade to bankruptcy
            if self._verbose:
                print(f"    [Epoch {self._epoch_index}] RENEWAL_FAILED: insufficient budget for renewal cost ({remaining_budget} < {renewal_cost})")
            # Record the renewal failure event before cascading to bankruptcy
            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Insufficient budget for renewal cost ({remaining_budget} < {renewal_cost})",
                attestation_compliant=True,  # Not an attestation issue
                remaining_budget_at_check=remaining_budget,
                renewal_cost=renewal_cost,
                effective_steps=self._current_effective_steps,
            )
            self._renewal_events.append(event)
            self._handle_bankruptcy()
            return

        # Generate renewal attestation
        nonce = secrets.token_hex(16)
        attestation = self._sentinel.generate_attestation(nonce)

        # Verify attestation (V052)
        valid, error = self._sentinel.verify_attestation(attestation)

        if not valid:
            event = RenewalEvent(
                cycle=self._cycle,
                lease_id=self._current_lease.lease_id,
                success=False,
                failure_reason=f"Attestation invalid: {error}",
                attestation_compliant=False,
                remaining_budget_at_check=remaining_budget,
                renewal_cost=renewal_cost,
                effective_steps=self._current_effective_steps,
            )
            self._renewal_events.append(event)
            self._handle_lease_revocation(LeaseViolation.RENEWAL_FAILURE, error or "")
            return

        # Check attestation compliance (V052)
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
                remaining_budget_at_check=remaining_budget,
                renewal_cost=renewal_cost,
                effective_steps=self._current_effective_steps,
            )
            self._renewal_events.append(event)
            self._handle_lease_revocation(LeaseViolation.CONSTRAINT_VIOLATION, str(reasons))
            return

        # Attempt renewal (V052)
        success, error = self._current_lease.renew(self._cycle)

        event = RenewalEvent(
            cycle=self._cycle,
            lease_id=self._current_lease.lease_id,
            success=success,
            failure_reason=error,
            attestation_compliant=True,
            remaining_budget_at_check=remaining_budget,
            renewal_cost=renewal_cost,
            effective_steps=self._current_effective_steps,
        )
        self._renewal_events.append(event)

        if success:
            self._total_renewals += 1
            self._renewal_successes += 1  # H3-redux: count successful renewals
            self._current_lease_renewals += 1
            self._e_class_renewals[e_class_name] += 1
            self._tenure_renewal_count += 1  # Run I: track renewals per tenure

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

        # Run I: End tenure tracking
        self._end_tenure("BANKRUPTCY")

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

        # Run I: End tenure tracking
        self._end_tenure("EXPIRED")

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

        # Run I: End tenure tracking
        self._end_tenure(f"REVOKED_{violation.name}")

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
        spec_version: Which spec semantics to use ("0.4.2", "0.4.3", "0.5.2", "0.6", or "0.7")

    Returns:
        Run result (ALSRunResult for v0.4.x, ALSRunResultV052 for v0.5.2, etc.)
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
    elif spec_version == "0.6":
        config = ALSConfigV060(max_cycles=max_cycles)
        harness = ALSHarnessV060(seed=seed, config=config, verbose=verbose)
        return harness.run()
    elif spec_version == "0.7":
        config = ALSConfigV070(max_cycles=max_cycles)
        harness = ALSHarnessV070(seed=seed, config=config, verbose=verbose)
        return harness.run()
    else:
        raise ValueError(f"Unknown spec version: {spec_version}")


# =============================================================================
# AKI v0.6: ALS-C (Authority Leases with Semantic Commitments)
# =============================================================================


@dataclass
class ALSConfigV060(ALSConfigV052):
    """
    Configuration for ALS-C v0.6 runs.

    Extends ALSConfigV052 with commitment ledger settings.

    Per spec §6:
    - Commitments persist across epochs and successions
    - commit_cap = floor(0.25 * steps_cap_epoch)
    - MAX_COMMIT_TTL = 10 epochs
    """
    # Genesis commitment set name (for logging/reproducibility)
    genesis_set: str = "GENESIS_SET_0"

    # Override commit_cap alpha (default 0.25 per binding decisions)
    commit_cap_alpha: float = 0.25

    # Override MAX_COMMIT_TTL (default 10 per binding decisions)
    max_commit_ttl: int = 10

    # Whether to seed genesis commitments at init
    seed_genesis_commitments: bool = True


@dataclass
class ALSRunResultV060:
    """
    Result of an ALS-C v0.6 run.

    Extends ALSRunResultV052 with semantic commitment metrics.
    """
    # Base metrics (inherited from V052)
    run_id: str
    seed: int
    spec_version: str = "0.6"
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

    # v0.5.2 expressivity metrics
    total_bankruptcies: int = 0
    total_rent_charged: int = 0
    renewal_attempts: int = 0
    renewal_successes: int = 0
    time_to_first_renewal_fail: Optional[int] = None
    e_class_distribution: Dict[str, int] = field(default_factory=dict)
    renewal_rate_by_e_class: Dict[str, float] = field(default_factory=dict)
    residence_by_e_class: Dict[str, float] = field(default_factory=dict)

    # v0.6 commitment metrics
    total_commitment_cost_charged: int = 0
    commitment_satisfaction_count: int = 0
    commitment_failure_count: int = 0
    commitment_expired_count: int = 0
    commitment_default_count: int = 0
    semantic_debt_mass: int = 0  # ACTIVE + FAILED at end
    commitment_satisfaction_rate: float = 0.0

    # Events
    succession_events: List[SuccessionEvent] = field(default_factory=list)
    renewal_events: List[RenewalEvent] = field(default_factory=list)
    expiration_events: List[ExpirationEvent] = field(default_factory=list)
    revocation_events: List[RevocationEvent] = field(default_factory=list)
    bankruptcy_events: List[BankruptcyEvent] = field(default_factory=list)
    epoch_rent_records: List[EpochRentRecord] = field(default_factory=list)
    tenure_records: List[TenureRecord] = field(default_factory=list)
    tenure_entropy_samples: List[float] = field(default_factory=list)

    # v0.6 commitment events
    commitment_events: List[Any] = field(default_factory=list)
    commitment_cost_records: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
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
            "total_commitment_cost_charged": self.total_commitment_cost_charged,
            "commitment_satisfaction_count": self.commitment_satisfaction_count,
            "commitment_failure_count": self.commitment_failure_count,
            "commitment_expired_count": self.commitment_expired_count,
            "commitment_default_count": self.commitment_default_count,
            "semantic_debt_mass": self.semantic_debt_mass,
            "commitment_satisfaction_rate": self.commitment_satisfaction_rate,
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
        }
        return result


class ALSHarnessV060(ALSHarnessV052):
    """
    v0.6 ALS-C harness: Authority Leases with Semantic Commitments.

    Per spec §6:
    - Commitment Ledger persists across epochs and successions
    - Genesis commitments seeded at init (cannot be declined)
    - Commitment cost charged AFTER rent
    - Semantic failure does NOT cause lease revocation
    - Evaluation at epoch end

    Key invariants:
    - effective_steps = max(0, steps_cap - rent - commit_cost)
    - Commitment failure independent of renewal
    - Authority may persist while incompetent
    """

    def __init__(
        self,
        seed: int = 42,
        config: Optional[ALSConfigV060] = None,
        verbose: bool = False,
    ):
        """
        Initialize v0.6 harness.

        Args:
            seed: Random seed for reproducibility
            config: Run configuration
            verbose: Enable verbose logging
        """
        # Initialize parent (V052)
        super().__init__(seed=seed, config=config or ALSConfigV060(), verbose=verbose)

        # Cast config to V060 type
        self._config: ALSConfigV060 = config or ALSConfigV060()

        # Import commitment module
        from toy_aki.als.commitment import (
            CommitmentLedger,
            CommitmentStatus,
            create_genesis_set_0,
        )
        from toy_aki.als.verifiers import (
            ActionRecord,
            verify_commitment,
            get_commitment_params,
        )

        self._CommitmentStatus = CommitmentStatus
        self._verify_commitment = verify_commitment
        self._get_commitment_params = get_commitment_params
        self._ActionRecord = ActionRecord

        # Create commitment ledger
        steps_cap = self._baseline_manifest.resources.max_steps_per_epoch
        self._commitment_ledger = CommitmentLedger(steps_cap)

        # Seed genesis commitments if configured
        if self._config.seed_genesis_commitments:
            genesis_commitments = create_genesis_set_0(start_epoch=0)
            self._commitment_ledger.seed(genesis_commitments)

        # Action trace for verifier (ACV analog)
        self._action_trace: List[Any] = []
        self._action_sequence_num = 0

        # Commitment-adjusted effective steps
        self._commitment_cost_this_epoch = 0

    def run(self) -> ALSRunResultV060:
        """
        Execute a complete ALS-C v0.6 run.

        Key additions over v0.5.2:
        - Commitment cost charging at epoch start
        - Commitment evaluation at epoch end
        - Semantic failure tracking (independent of authority)

        Returns:
            Run result with all metrics and logs
        """
        start_time = current_time_ms()
        run_id = f"als060_{self._seed}_{start_time}"

        if self._verbose:
            print(f"Starting ALS-C v0.6 run: {run_id}")
            print(f"  Max cycles: {self._config.max_cycles}")
            print(f"  MSRW: {self._config.get_msrw()}")
            print(f"  Rent schedule: {self._rent_schedule.to_dict()}")
            print(f"  Genesis set: {self._config.genesis_set}")
            print(f"  Commit cap: {self._commitment_ledger.commit_cap}")

        # Main loop
        while not self._stopped and self._cycle < self._config.max_cycles:
            self._cycle += 1
            self._sentinel.advance_cycle()

            # Check if succession is allowed
            if self._succession_pending:
                self._attempt_succession_v060()

            # Execute working mind cycle (consumes step budget)
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                # Check step budget (after rent + commitment deductions)
                adjusted_effective = self._current_effective_steps - self._commitment_cost_this_epoch
                if self._epoch_steps_used >= adjusted_effective:
                    pass  # Budget exhausted
                else:
                    violation = self._execute_working_mind_cycle_v060()
                    if violation:
                        self._handle_lease_revocation(violation[0], violation[1])
                        continue

            # Check renewal at epoch boundaries
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                if self._cycle % self._config.renewal_check_interval == 0:
                    # Evaluate commitments before renewal check
                    self._evaluate_commitments_at_epoch_end()
                    self._check_renewal_with_rent()

            # Check lease expiration
            if self._current_lease and self._current_lease.is_expired(self._cycle):
                self._handle_lease_expiration()

            # Check degeneracy
            self._check_degeneracy()

        # Finalize
        if not self._stopped:
            self._stop_reason = ALSStopReason.HORIZON_EXHAUSTED

        # Finalize active tenure
        if self._current_tenure is not None:
            self._end_tenure("HORIZON_EXHAUSTED")

        duration = current_time_ms() - start_time

        # Get commitment metrics
        ledger_metrics = self._commitment_ledger.get_metrics()

        # Compute satisfaction rate
        total_evaluations = ledger_metrics["total_satisfied"] + ledger_metrics["total_failed"]
        satisfaction_rate = 0.0
        if total_evaluations > 0:
            satisfaction_rate = ledger_metrics["total_satisfied"] / total_evaluations

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

        result = ALSRunResultV060(
            run_id=run_id,
            seed=self._seed,
            spec_version="0.6",
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
            total_commitment_cost_charged=ledger_metrics["total_cost_charged"],
            commitment_satisfaction_count=ledger_metrics["total_satisfied"],
            commitment_failure_count=ledger_metrics["total_failed"],
            commitment_expired_count=ledger_metrics["total_expired"],
            commitment_default_count=ledger_metrics["total_defaulted"],
            semantic_debt_mass=ledger_metrics["semantic_debt_mass"],
            commitment_satisfaction_rate=satisfaction_rate,
            succession_events=self._succession_events,
            renewal_events=self._renewal_events,
            expiration_events=self._expiration_events,
            revocation_events=self._revocation_events,
            bankruptcy_events=self._bankruptcy_events,
            epoch_rent_records=self._epoch_rent_records,
            tenure_records=self._tenure_records,
            tenure_entropy_samples=self._tenure_entropy_samples,
            commitment_events=[e.to_dict() for e in self._commitment_ledger.get_events()],
            commitment_cost_records=[r.to_dict() for r in self._commitment_ledger.get_cost_records()],
            duration_ms=duration,
        )

        if self._verbose:
            print(f"\nALS-C v0.6 run complete:")
            print(f"  S*: {result.s_star}")
            print(f"  Cycles: {result.total_cycles}")
            print(f"  Renewals: {result.total_renewals}")
            print(f"  Expirations: {result.total_expirations}")
            print(f"  Commitment satisfaction: {result.commitment_satisfaction_count}")
            print(f"  Commitment failures: {result.commitment_failure_count}")
            print(f"  Satisfaction rate: {result.commitment_satisfaction_rate:.2%}")
            print(f"  Stop: {result.stop_reason.name}")

        return result

    def _attempt_succession_v060(self) -> None:
        """Attempt succession with commitment cost setup."""
        # Call parent implementation
        self._attempt_succession()

        # If succession succeeded, charge commitment costs for new epoch
        if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
            self._charge_commitment_costs()

    def _charge_commitment_costs(self) -> None:
        """
        Charge commitment maintenance costs at epoch start.

        Per spec §6.4:
        - Charged AFTER rent deduction
        - If insufficient budget, commitments default (not lease)
        """
        # Available budget after rent
        available_after_rent = self._current_effective_steps

        # Charge commitment costs
        cost_charged, defaulted = self._commitment_ledger.charge_costs(
            epoch=self._epoch_index,
            cycle=self._cycle,
            available_budget=available_after_rent,
        )

        self._commitment_cost_this_epoch = cost_charged

        if self._verbose:
            if defaulted:
                print(f"    [Epoch {self._epoch_index}] COMMITMENT_DEFAULT: "
                      f"needed {self._commitment_ledger.get_active_cost()}, had {available_after_rent}")
            else:
                print(f"    [Epoch {self._epoch_index}] COMMIT_COST_CHARGED: {cost_charged} steps")

    def _execute_working_mind_cycle_v060(self) -> Optional[tuple[LeaseViolation, str]]:
        """Execute cycle and record action for verifier."""
        if self._current_mind is None:
            return None

        # Consume step
        self._epoch_steps_used += 1

        # Sentinel check
        step_allowed, step_violation, step_detail = self._sentinel.check_step()
        if not step_allowed and step_violation is not None:
            lease_violation = self._map_sentinel_violation(step_violation)
            return (lease_violation, step_detail or str(step_violation))

        # Get action from working mind
        adjusted_effective = self._current_effective_steps - self._commitment_cost_this_epoch
        observation = {
            "cycle": self._cycle,
            "state": {"running": True},
            "epoch_steps_remaining": adjusted_effective - self._epoch_steps_used,
            "active_commitments": [c.cid for c in self._commitment_ledger.get_active_commitments()],
        }

        try:
            action = self._current_mind.propose_action(observation)
        except Exception as e:
            return (LeaseViolation.CONSTRAINT_VIOLATION, f"Action proposal failed: {e}")

        if action is None:
            return None

        # Track action
        self._epoch_actions_used += 1

        # Record action for verifier (ACV trace)
        action_type = action.get("action_type", "UNKNOWN") if isinstance(action, dict) else getattr(action, "action_type", "UNKNOWN")
        payload = action.get("payload", {}) if isinstance(action, dict) else getattr(action, "payload", {})

        self._action_trace.append(self._ActionRecord(
            action_type=action_type,
            payload=payload if isinstance(payload, dict) else {},
            epoch=self._epoch_index,
            cycle=self._cycle,
            sequence_num=self._action_sequence_num,
        ))
        self._action_sequence_num += 1

        # Sentinel action check
        allowed, violation_type, detail = self._sentinel.check_action(action)
        if not allowed and violation_type is not None:
            lease_violation = self._map_sentinel_violation(violation_type)
            return (lease_violation, detail or str(violation_type))

        return None

    def _evaluate_commitments_at_epoch_end(self) -> None:
        """
        Evaluate all commitments at epoch end.

        Per spec §6.7:
        - Evaluation at epoch end (after successor actions)
        - Use ACV trace for the window
        """
        for commitment in self._commitment_ledger.get_active_commitments():
            # Get window bounds
            window_end = self._epoch_index
            window_start = max(0, window_end - commitment.window + 1)

            # Filter actions in window
            window_actions = [
                a for a in self._action_trace
                if window_start <= a.epoch <= window_end
            ]

            # Get verifier params
            params = self._get_commitment_params(commitment.cid)

            # Run verifier
            try:
                result = self._verify_commitment(
                    verifier_id=commitment.verifier_id,
                    actions=window_actions,
                    window_start_epoch=window_start,
                    window_end_epoch=window_end,
                    params=params,
                )
            except ValueError as e:
                # Unknown verifier - treat as failure
                result = False

            # Update commitment status
            self._commitment_ledger.evaluate_commitment(
                cid=commitment.cid,
                epoch=self._epoch_index,
                cycle=self._cycle,
                verifier_result=result,
            )

        # Check TTL expirations
        self._commitment_ledger.check_ttl_expirations(
            epoch=self._epoch_index,
            cycle=self._cycle,
        )

        # NOTE: Epoch management (increment, reset, rent charging) is done
        # by _check_renewal_with_rent which is called after this method.
        # We only handle commitment-specific logic here.

    def _check_renewal_with_rent(self) -> None:
        """
        Override to also charge commitment costs after renewal.

        Extends parent implementation to:
        1. Call parent renewal logic (epoch reset, rent charging)
        2. Charge commitment costs for new epoch
        3. Reset action trace for new epoch
        """
        old_epoch = self._epoch_index

        # Call parent implementation
        super()._check_renewal_with_rent()

        # If renewal succeeded (epoch advanced), charge commitment costs
        if self._epoch_index > old_epoch:
            self._charge_commitment_costs()
            # Reset action sequence for new epoch
            self._action_sequence_num = 0


# =============================================================================
# AKI v0.7: ALS-G (Authority Leases with Eligibility-Coupled Succession)
# =============================================================================


class CandidatePoolPolicy(Enum):
    """
    Candidate pool composition policy per spec §6.4.1.

    v0.7 uses V060_DEFAULT to isolate the eligibility gating mechanism.
    Run D adds skewed pool compositions for stress testing.
    """
    V060_DEFAULT = auto()      # Identical generator composition to v0.6 (baseline)
    ATTACK_HEAVY_90 = auto()   # ~90% Attack, ~10% Control
    CONTROL_HEAVY_90 = auto()  # ~90% Control, ~10% Attack


# =============================================================================
# Pool Policy Weight Maps (Run D)
# =============================================================================

# Base weights from v0.6 (untouched reference)
# control_weight = 0.3 in GeneratorConfig default
# This means: 30% control, 70% attack (before within-category sampling)

def get_pool_policy_weights(policy: CandidatePoolPolicy) -> tuple[float, float]:
    """
    Get (control_weight, attack_weight) for a pool policy.

    Returns:
        Tuple of (control_weight, attack_weight) summing to 1.0
    """
    if policy == CandidatePoolPolicy.V060_DEFAULT:
        return (0.3, 0.7)  # Baseline: 30% control, 70% attack
    elif policy == CandidatePoolPolicy.ATTACK_HEAVY_90:
        return (0.1, 0.9)  # 10% control, 90% attack
    elif policy == CandidatePoolPolicy.CONTROL_HEAVY_90:
        return (0.9, 0.1)  # 90% control, 10% attack
    else:
        return (0.3, 0.7)  # Fallback to baseline


@dataclass
class ALSConfigV070(ALSConfigV060):
    """
    Configuration for ALS-G v0.7 runs.

    Extends ALSConfigV060 with eligibility gating settings.

    Per spec §6:
    - Eligibility filter at succession only
    - K = 3 (semantic fail streak threshold)
    - Candidate pool unchanged from v0.6

    Run B addition:
    - max_successive_renewals: harness-enforced renewal limit per tenure
    """
    # Eligibility threshold: streak >= K makes candidate ineligible
    eligibility_threshold_k: int = 3

    # Candidate pool policy (frozen: V060_DEFAULT)
    candidate_pool_policy: CandidatePoolPolicy = CandidatePoolPolicy.V060_DEFAULT

    # Harness-enforced renewal limit per tenure (Run B)
    # If None, no limit is enforced (Run A behavior)
    # If set, lease expires after this many successful renewals
    max_successive_renewals: Optional[int] = None


@dataclass
class EligibilityEvent:
    """Record of an eligibility decision at succession."""
    cycle: int
    epoch: int
    candidate_policy_id: str
    streak_at_decision: int
    eligible: bool
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "epoch": self.epoch,
            "candidate_policy_id": self.candidate_policy_id,
            "streak_at_decision": self.streak_at_decision,
            "eligible": self.eligible,
            "reason": self.reason,
        }


@dataclass
class LapseEvent:
    """Record of a constitutional lapse (C_ELIG = ∅)."""
    cycle: int
    epoch: int
    start_cycle: int
    end_cycle: Optional[int] = None  # None if still in lapse
    duration_cycles: int = 0
    duration_epochs: int = 0
    ineligible_policies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "epoch": self.epoch,
            "start_cycle": self.start_cycle,
            "end_cycle": self.end_cycle,
            "duration_cycles": self.duration_cycles,
            "duration_epochs": self.duration_epochs,
            "ineligible_policies": self.ineligible_policies,
        }


@dataclass
class SemanticEpochRecord:
    """Record of semantic outcome per epoch."""
    epoch: int
    cycle: int
    active_policy_id: Optional[str]
    c0_ok: bool
    c1_ok: bool
    c2_ok: bool
    sem_pass: bool
    streak_before: int
    streak_after: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "cycle": self.cycle,
            "active_policy_id": self.active_policy_id,
            "c0_ok": self.c0_ok,
            "c1_ok": self.c1_ok,
            "c2_ok": self.c2_ok,
            "sem_pass": self.sem_pass,
            "streak_before": self.streak_before,
            "streak_after": self.streak_after,
        }


@dataclass
class ForcedTurnoverEvent:
    """Record of a forced turnover due to renewal limit (Run B)."""
    cycle: int
    epoch: int
    outgoing_policy_id: str
    tenure_renewals_used: int
    max_successive_renewals: int
    cause: str = "FORCED_TURNOVER_RENEWAL_LIMIT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "epoch": self.epoch,
            "outgoing_policy_id": self.outgoing_policy_id,
            "tenure_renewals_used": self.tenure_renewals_used,
            "max_successive_renewals": self.max_successive_renewals,
            "cause": self.cause,
        }


@dataclass
class ALSRunResultV070:
    """
    Result of an ALS-G v0.7 run.

    Extends ALSRunResultV060 with eligibility metrics.
    """
    # Base metrics (inherited from V060)
    run_id: str
    seed: int
    spec_version: str = "0.7"
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

    # v0.5.2 expressivity metrics
    total_bankruptcies: int = 0
    total_rent_charged: int = 0
    renewal_attempts: int = 0
    renewal_successes: int = 0
    time_to_first_renewal_fail: Optional[int] = None
    e_class_distribution: Dict[str, int] = field(default_factory=dict)
    renewal_rate_by_e_class: Dict[str, float] = field(default_factory=dict)
    residence_by_e_class: Dict[str, float] = field(default_factory=dict)

    # v0.6 commitment metrics
    total_commitment_cost_charged: int = 0
    commitment_satisfaction_count: int = 0
    commitment_failure_count: int = 0
    commitment_expired_count: int = 0
    commitment_default_count: int = 0
    semantic_debt_mass: int = 0
    commitment_satisfaction_rate: float = 0.0

    # v0.7 eligibility metrics
    eligibility_rejection_count: int = 0
    eligibility_rejection_rate: float = 0.0
    empty_eligible_set_events: int = 0  # Lapse triggers
    total_lapse_duration_cycles: int = 0
    total_lapse_duration_epochs: int = 0
    max_lapse_duration_cycles: int = 0
    ineligible_in_office_cycles: int = 0  # "Zombie time"
    sawtooth_count: int = 0  # FAIL^(K-1) then PASS patterns
    streak_distribution_at_succession: Dict[int, int] = field(default_factory=dict)
    final_streak_by_policy: Dict[str, int] = field(default_factory=dict)

    # Events
    succession_events: List[SuccessionEvent] = field(default_factory=list)
    renewal_events: List[RenewalEvent] = field(default_factory=list)
    expiration_events: List[ExpirationEvent] = field(default_factory=list)
    revocation_events: List[RevocationEvent] = field(default_factory=list)
    bankruptcy_events: List[BankruptcyEvent] = field(default_factory=list)
    epoch_rent_records: List[EpochRentRecord] = field(default_factory=list)
    tenure_records: List[TenureRecord] = field(default_factory=list)
    tenure_entropy_samples: List[float] = field(default_factory=list)

    # v0.6 commitment events
    commitment_events: List[Any] = field(default_factory=list)
    commitment_cost_records: List[Any] = field(default_factory=list)

    # v0.7 eligibility events
    eligibility_events: List[EligibilityEvent] = field(default_factory=list)
    lapse_events: List[LapseEvent] = field(default_factory=list)
    semantic_epoch_records: List[SemanticEpochRecord] = field(default_factory=list)

    # v0.7 forced turnover events (Run B)
    forced_turnover_events: List[ForcedTurnoverEvent] = field(default_factory=list)
    forced_turnover_count: int = 0
    post_init_successions: int = 0  # Successions after initial endorsement

    # v0.7 composition verification (Run D)
    attack_draws: int = 0
    control_draws: int = 0
    attack_draw_ratio: float = 0.0
    control_draw_ratio: float = 0.0
    pool_policy: str = "V060_DEFAULT"

    def to_dict(self) -> Dict[str, Any]:
        result = {
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
            "total_commitment_cost_charged": self.total_commitment_cost_charged,
            "commitment_satisfaction_count": self.commitment_satisfaction_count,
            "commitment_failure_count": self.commitment_failure_count,
            "commitment_expired_count": self.commitment_expired_count,
            "commitment_default_count": self.commitment_default_count,
            "semantic_debt_mass": self.semantic_debt_mass,
            "commitment_satisfaction_rate": self.commitment_satisfaction_rate,
            # v0.7 eligibility metrics
            "eligibility_rejection_count": self.eligibility_rejection_count,
            "eligibility_rejection_rate": self.eligibility_rejection_rate,
            "empty_eligible_set_events": self.empty_eligible_set_events,
            "total_lapse_duration_cycles": self.total_lapse_duration_cycles,
            "total_lapse_duration_epochs": self.total_lapse_duration_epochs,
            "max_lapse_duration_cycles": self.max_lapse_duration_cycles,
            "ineligible_in_office_cycles": self.ineligible_in_office_cycles,
            "sawtooth_count": self.sawtooth_count,
            "streak_distribution_at_succession": self.streak_distribution_at_succession,
            "final_streak_by_policy": self.final_streak_by_policy,
            # v0.7 forced turnover (Run B)
            "forced_turnover_count": self.forced_turnover_count,
            "post_init_successions": self.post_init_successions,
            # v0.7 composition verification (Run D)
            "attack_draws": self.attack_draws,
            "control_draws": self.control_draws,
            "attack_draw_ratio": self.attack_draw_ratio,
            "control_draw_ratio": self.control_draw_ratio,
            "pool_policy": self.pool_policy,
            # Standard metrics
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
        }
        return result


class ALSHarnessV070(ALSHarnessV060):
    """
    v0.7 ALS-G harness: Authority Leases with Eligibility-Coupled Succession.

    Per spec §6:
    - Semantic failure streak tracked per policy_id (not per instance)
    - Eligibility filter applied only at succession boundaries
    - Ineligible candidates (streak >= K) filtered from C_ELIG
    - Empty C_ELIG triggers constitutional lapse (NULL_AUTHORITY)
    - Time continues during NULL_AUTHORITY

    Key invariants:
    - policy_id is stable per policy class
    - Streak updates only at epoch end for active authority holder
    - No streak updates during NULL_AUTHORITY
    - Renewal/enforcement unaffected by eligibility
    """

    def __init__(
        self,
        seed: int = 42,
        config: Optional[ALSConfigV070] = None,
        verbose: bool = False,
    ):
        """
        Initialize v0.7 harness.

        Args:
            seed: Random seed for reproducibility
            config: Run configuration
            verbose: Enable verbose logging
        """
        # Initialize parent (V060)
        super().__init__(seed=seed, config=config or ALSConfigV070(), verbose=verbose)

        # Cast config to V070 type
        self._config: ALSConfigV070 = config or ALSConfigV070()

        # v0.7: Reconfigure generator for pool policy (Run D)
        # This must happen after parent init creates the generator
        control_w, attack_w = get_pool_policy_weights(self._config.candidate_pool_policy)
        # Create a new generator config with the correct control_weight
        from toy_aki.als.generator import GeneratorConfig
        gen_config = GeneratorConfig(control_weight=control_w)
        self._generator = SuccessorGenerator(
            sentinel_id=self._sentinel.sentinel_id,
            baseline_manifest=self._baseline_manifest,
            seed=seed,
            config=gen_config,
        )

        # v0.7: Draw counting for composition verification (Run D)
        self._attack_draws: int = 0
        self._control_draws: int = 0

        # v0.7: Semantic failure streak per policy_id
        self._semantic_fail_streak: Dict[str, int] = {}

        # v0.7: Active authority holder's policy_id
        self._active_policy_id: Optional[str] = None

        # v0.7: NULL_AUTHORITY state
        self._in_null_authority: bool = False
        self._null_authority_start_cycle: Optional[int] = None
        self._null_authority_start_epoch: Optional[int] = None

        # v0.7: Eligibility tracking
        self._eligibility_events: List[EligibilityEvent] = []
        self._lapse_events: List[LapseEvent] = []
        self._semantic_epoch_records: List[SemanticEpochRecord] = []

        # v0.7: Metrics
        self._eligibility_rejections: int = 0
        self._total_candidates_at_succession: int = 0
        self._ineligible_in_office_cycles: int = 0
        self._sawtooth_count: int = 0
        self._current_lapse: Optional[LapseEvent] = None

        # v0.7: Forced turnover tracking (Run B)
        self._forced_turnover_events: List[ForcedTurnoverEvent] = []
        self._tenure_renewals_used: int = 0  # Renewals for current tenure
        self._is_initial_succession: bool = True  # Track if first succession
        self._post_init_successions: int = 0  # Count successions after initial

        # RSA v1.0: Stub for v0.70 compatibility (not enabled in v0.70)
        self._rsa_policy_wrapper = None
        # RSA v2.0: Stub for v0.70 compatibility (not enabled in v0.70)
        self._rsa_v2_wrapper = None

    def _count_draw(self, candidate: SuccessorCandidate) -> None:
        """
        Count a candidate draw for composition verification (Run D).

        Tracks whether the draw was from Attack or Control category.
        """
        if candidate.source_type == "control":
            self._control_draws += 1
        else:
            # adversarial or generated → attack
            self._attack_draws += 1

    def _get_policy_streak(self, policy_id: str) -> int:
        """Get current streak for a policy (0 if not tracked yet)."""
        return self._semantic_fail_streak.get(policy_id, 0)

    def _is_candidate_eligible(self, policy_id: str) -> bool:
        """Check if a candidate's policy is eligible (streak < K)."""
        streak = self._get_policy_streak(policy_id)
        return streak < self._config.eligibility_threshold_k

    def _compute_commitment_keys_raw(self) -> tuple[bool, bool, bool]:
        """
        Compute raw commitment key values (C0_OK, C1_OK, C2_OK).

        This is the first half of semantic evaluation. Returns raw keys
        BEFORE any RSA corruption. AKI's aggregation happens separately.

        Returns:
            Tuple of (c0_ok, c1_ok, c2_ok) - raw values
        """
        # Per spec §6.1: Non-vacuity rule - unevaluable = FALSE
        c0_ok = False
        c1_ok = False
        c2_ok = False

        # Check each genesis commitment
        for commitment in self._commitment_ledger.get_active_commitments():
            if commitment.cid == "C0":
                # C0 satisfied if last evaluation was success
                c0_ok = commitment.satisfaction_count > commitment.failure_count
                # More precisely: check if current epoch passed
                if commitment.last_evaluation_epoch == self._epoch_index:
                    from toy_aki.als.commitment import CommitmentStatus
                    c0_ok = commitment.status == CommitmentStatus.SATISFIED or (
                        commitment.status == CommitmentStatus.ACTIVE and
                        commitment.satisfaction_count > 0 and
                        commitment.last_evaluation_epoch == self._epoch_index
                    )
            elif commitment.cid == "C1":
                c1_ok = commitment.satisfaction_count > commitment.failure_count
                if commitment.last_evaluation_epoch == self._epoch_index:
                    from toy_aki.als.commitment import CommitmentStatus
                    c1_ok = commitment.status == CommitmentStatus.SATISFIED or (
                        commitment.status == CommitmentStatus.ACTIVE and
                        commitment.satisfaction_count > 0
                    )
            elif commitment.cid == "C2":
                c2_ok = commitment.satisfaction_count > commitment.failure_count
                if commitment.last_evaluation_epoch == self._epoch_index:
                    from toy_aki.als.commitment import CommitmentStatus
                    c2_ok = commitment.status == CommitmentStatus.SATISFIED or (
                        commitment.status == CommitmentStatus.ACTIVE and
                        commitment.satisfaction_count > 0
                    )

        return (c0_ok, c1_ok, c2_ok)

    @staticmethod
    def _aggregate_sem_pass(c0_ok: bool, c1_ok: bool, c2_ok: bool) -> bool:
        """
        AKI's canonical SEM_PASS aggregation function.

        This is the ONLY place where Ci keys are aggregated into SEM_PASS.
        RSA MUST use this exact function (via reference, not reimplementation).

        Current rule: strict AND (K=3 equivalence)
        """
        return c0_ok and c1_ok and c2_ok

    def _compute_sem_pass(self) -> tuple[bool, bool, bool, bool]:
        """
        Compute SEM_PASS for current epoch.

        This combines raw key computation with aggregation.
        For RSA integration, use _compute_commitment_keys_raw() + _aggregate_sem_pass()
        separately to allow corruption between them.

        Returns:
            Tuple of (c0_ok, c1_ok, c2_ok, sem_pass)
        """
        c0_ok, c1_ok, c2_ok = self._compute_commitment_keys_raw()
        sem_pass = self._aggregate_sem_pass(c0_ok, c1_ok, c2_ok)
        return (c0_ok, c1_ok, c2_ok, sem_pass)

    def _update_streak_at_epoch_end(self) -> None:
        """
        Update semantic failure streak at epoch end.

        Per spec §6.2:
        - Only updates for active authority holder
        - No updates during NULL_AUTHORITY
        """
        if self._in_null_authority:
            # No streak updates during NULL_AUTHORITY
            return

        if self._active_policy_id is None:
            # No active authority holder
            return

        policy_id = self._active_policy_id
        streak_before = self._get_policy_streak(policy_id)

        c0_ok, c1_ok, c2_ok, sem_pass = self._compute_sem_pass()

        if sem_pass:
            # Reset streak on pass
            # Check for sawtooth pattern: was at K-1 before passing
            if streak_before == self._config.eligibility_threshold_k - 1:
                self._sawtooth_count += 1
            self._semantic_fail_streak[policy_id] = 0
            streak_after = 0
        else:
            # Increment streak on fail
            self._semantic_fail_streak[policy_id] = streak_before + 1
            streak_after = streak_before + 1

        # Track ineligible-in-office time
        if streak_after >= self._config.eligibility_threshold_k:
            self._ineligible_in_office_cycles += 1

        # Record semantic epoch
        self._semantic_epoch_records.append(SemanticEpochRecord(
            epoch=self._epoch_index,
            cycle=self._cycle,
            active_policy_id=policy_id,
            c0_ok=c0_ok,
            c1_ok=c1_ok,
            c2_ok=c2_ok,
            sem_pass=sem_pass,
            streak_before=streak_before,
            streak_after=streak_after,
        ))

        if self._verbose:
            status = "PASS" if sem_pass else "FAIL"
            print(f"    [Epoch {self._epoch_index}] SEM_{status}: "
                  f"C0={c0_ok}, C1={c1_ok}, C2={c2_ok} | "
                  f"streak[{policy_id}]: {streak_before} → {streak_after}")

    def _filter_eligible_candidates(
        self,
        candidates: List[SuccessorCandidate],
    ) -> List[SuccessorCandidate]:
        """
        Filter candidates by eligibility.

        Per spec §6.4:
        - C_ELIG = { c ∈ CANDIDATE_SET | streak(c.policy_id) < K }
        """
        eligible = []
        for c in candidates:
            streak = self._get_policy_streak(c.policy_id)
            is_eligible = streak < self._config.eligibility_threshold_k

            # Record eligibility decision
            self._eligibility_events.append(EligibilityEvent(
                cycle=self._cycle,
                epoch=self._epoch_index,
                candidate_policy_id=c.policy_id,
                streak_at_decision=streak,
                eligible=is_eligible,
                reason="" if is_eligible else f"streak {streak} >= K={self._config.eligibility_threshold_k}",
            ))

            self._total_candidates_at_succession += 1
            if is_eligible:
                eligible.append(c)
            else:
                self._eligibility_rejections += 1

        return eligible

    def _enter_null_authority(self, ineligible_policies: List[str]) -> None:
        """Enter NULL_AUTHORITY state (constitutional lapse)."""
        self._in_null_authority = True
        self._null_authority_start_cycle = self._cycle
        self._null_authority_start_epoch = self._epoch_index

        # v2.0: Track lapse for RSA observable interface
        if hasattr(self, '_current_epoch_has_lapse'):
            self._current_epoch_has_lapse = True

        # Clear active authority
        self._current_mind = None
        self._current_lease = None
        self._active_policy_id = None

        # Create lapse event
        self._current_lapse = LapseEvent(
            cycle=self._cycle,
            epoch=self._epoch_index,
            start_cycle=self._cycle,
            ineligible_policies=ineligible_policies,
        )

        if self._verbose:
            print(f"    [Cycle {self._cycle}] LAPSE: C_ELIG=∅, entering NULL_AUTHORITY")
            print(f"      Ineligible policies: {ineligible_policies}")

    def _exit_null_authority(self) -> None:
        """Exit NULL_AUTHORITY state."""
        if self._current_lapse is not None:
            self._current_lapse.end_cycle = self._cycle
            self._current_lapse.duration_cycles = self._cycle - self._current_lapse.start_cycle
            self._current_lapse.duration_epochs = self._epoch_index - self._null_authority_start_epoch
            self._lapse_events.append(self._current_lapse)
            self._current_lapse = None

        self._in_null_authority = False
        self._null_authority_start_cycle = None
        self._null_authority_start_epoch = None

        if self._verbose:
            print(f"    [Cycle {self._cycle}] Exiting NULL_AUTHORITY")

    def _attempt_succession_v070(self) -> bool:
        """
        Attempt succession with eligibility filtering.

        Returns:
            True if succession succeeded, False if lapse triggered
        """
        # Generate candidate pool
        candidate = self._generator.propose(self._cycle)
        candidates = [candidate]

        # Track draw for composition verification (Run D)
        self._count_draw(candidate)

        # For v0.7, we need to sample multiple candidates to build C_ELIG
        # Generate additional candidates to form pool
        for _ in range(min(10, len(list(ControlSuccessorType)) + len(list(AttackSuccessorType)))):
            c = self._generator.propose(self._cycle)
            candidates.append(c)
            self._count_draw(c)  # Track each draw

        # Filter by eligibility
        eligible_candidates = self._filter_eligible_candidates(candidates)

        if not eligible_candidates:
            # C_ELIG = ∅ → Lapse
            ineligible_policies = list(set(c.policy_id for c in candidates))
            self._enter_null_authority(ineligible_policies)
            return False

        # Select from eligible candidates (use first one, semantic-blind)
        selected = eligible_candidates[0]

        # Store active policy_id before endorsement
        self._active_policy_id = selected.policy_id

        # Exit NULL_AUTHORITY if we were in it
        if self._in_null_authority:
            self._exit_null_authority()

        # Proceed with standard succession (call parent logic)
        # We need to manually do what _attempt_succession does with our selected candidate
        self._total_proposals += 1

        # Validate candidate
        is_valid = self._validate_candidate(selected)
        if not is_valid:
            # Rejection - try another eligible candidate
            for alt in eligible_candidates[1:]:
                if self._validate_candidate(alt):
                    selected = alt
                    self._active_policy_id = selected.policy_id
                    is_valid = True
                    break

        if not is_valid:
            # All eligible candidates rejected - enter lapse
            ineligible_policies = list(set(c.policy_id for c in candidates))
            self._enter_null_authority(ineligible_policies)
            return False

        # Endorse candidate
        self._endorse_candidate(selected)

        return True

    def _validate_candidate(self, candidate: SuccessorCandidate) -> bool:
        """Validate a candidate against LCP requirements."""
        lcp = self._generator.build_lcp(candidate)
        valid, _ = self._validator.validate_v043(lcp, candidate.mind.export_manifest())
        return valid

    def _endorse_candidate(self, candidate: SuccessorCandidate) -> None:
        """Endorse a candidate and activate their lease."""
        # Build LCP
        lcp = self._generator.build_lcp(candidate, renewal_window=self._config.renewal_check_interval)

        # End current tenure if exists
        if self._current_tenure is not None:
            self._end_tenure("SUCCESSION")

        # Create lease using validator
        lease, error = self._validator.create_lease_v043(
            lcp, candidate.mind.mind_id, candidate.mind.export_manifest()
        )
        if lease is None:
            # Record rejection and return - shouldn't happen after validation
            return

        # Supersede current lease if exists
        if self._current_lease:
            self._current_lease.supersede()

        # Activate new lease
        lease.activate(self._cycle)
        self._sentinel.bind_lease(lease)

        # RSA v1.0/v2.0: Expand interface to include commitment actions
        if self._rsa_policy_wrapper is not None or self._rsa_v2_wrapper is not None:
            from toy_aki.rsa.policy import RSA_COMMITMENT_ACTIONS
            self._sentinel.expand_interface_action_types(RSA_COMMITMENT_ACTIONS)

        # Set current mind
        self._current_lease = lease
        self._current_mind = candidate.mind
        self._active_policy_id = candidate.policy_id
        self._successor_endorsed_at_cycle = self._cycle
        self._current_successor_source_type = candidate.source_type
        self._current_lease_renewals = 0

        # v0.7 Run B: Reset tenure renewal counter
        self._tenure_renewals_used = 0

        # v0.7: Track post-initial successions
        if not self._is_initial_succession:
            self._post_init_successions += 1
        self._is_initial_succession = False

        # Determine E-class
        action_types = candidate.manifest.interface.action_types
        e_class = self._assign_e_class(action_types)
        self._current_e_class = e_class
        self._current_rent = self._rent_schedule.compute_rent(e_class)
        self._current_effective_steps = self._rent_schedule.compute_effective_steps(e_class)

        # Track endorsement
        self._total_endorsements += 1
        is_non_trivial = candidate.is_non_trivial(self._baseline_manifest)
        if is_non_trivial:
            self._s_star += 1
            self._non_trivial_endorsements += 1
        else:
            self._control_endorsements += 1

        self._generator.record_endorsement(candidate.candidate_id)
        self._e_class_successions[e_class.name] = self._e_class_successions.get(e_class.name, 0) + 1

        # Record succession event
        self._succession_events.append(SuccessionEvent(
            cycle=self._cycle,
            candidate_id=candidate.candidate_id,
            mind_id=candidate.mind.mind_id,
            source_type=candidate.source_type,
            is_non_trivial=is_non_trivial,
            endorsed=True,
            lease_id=lease.lease_id,
            selection_mode=candidate.selection_mode,
        ))

        # Start new tenure
        self._start_tenure(candidate.mind.mind_id, e_class.name, candidate.manifest)

        # Reset succession state
        self._succession_pending = False

        # Initialize epoch state for new successor
        self._epoch_index = 0
        self._epoch_start_cycle = self._cycle
        self._epoch_steps_used = 0
        self._epoch_actions_used = 0

        # Charge rent for E-Class
        self._charge_rent()

        # Charge commitment costs
        self._charge_commitment_costs()

        # Notify generator of endorsement
        self._generator.record_endorsement(candidate.candidate_id)

        if self._verbose:
            print(f"    [Cycle {self._cycle}] ENDORSED: {candidate.policy_id} "
                  f"(S*={self._s_star})")

    def _check_renewal_with_rent(self) -> None:
        """
        Override to enforce max_successive_renewals limit (Run B).

        If max_successive_renewals is set and the limit is reached,
        force lease expiration and trigger succession.
        """
        if self._current_lease is None:
            return

        if self._current_lease.status != LeaseStatus.ACTIVE:
            return

        # Check if renewal limit is enforced and reached
        max_renewals = self._config.max_successive_renewals
        if max_renewals is not None and self._tenure_renewals_used >= max_renewals:
            # Force expiration - record the event before triggering succession
            event = ForcedTurnoverEvent(
                cycle=self._cycle,
                epoch=self._epoch_index,
                outgoing_policy_id=self._active_policy_id or "unknown",
                tenure_renewals_used=self._tenure_renewals_used,
                max_successive_renewals=max_renewals,
            )
            self._forced_turnover_events.append(event)

            if self._verbose:
                print(f"    [Cycle {self._cycle}] FORCED_TURNOVER: {self._active_policy_id} "
                      f"(renewals={self._tenure_renewals_used}/{max_renewals})")

            # Handle as expiration (not revocation - this is structural, not violation)
            self._handle_lease_expiration()
            return

        # Call parent implementation for normal renewal logic
        super()._check_renewal_with_rent()

        # If renewal succeeded, increment our counter
        # Parent increments _current_lease_renewals on success
        if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
            # Check if renewal just happened (parent would have incremented counter)
            # We can detect this by comparing epochs or checking if renewal events were added
            if self._renewal_events and self._renewal_events[-1].cycle == self._cycle:
                if self._renewal_events[-1].success:
                    self._tenure_renewals_used += 1

    def run(self) -> ALSRunResultV070:
        """
        Execute a complete ALS-G v0.7 run.

        Key additions over v0.6:
        - Eligibility filtering at succession
        - Semantic failure streak per policy_id
        - NULL_AUTHORITY state and lapse handling
        - Epochs tick during NULL_AUTHORITY

        Returns:
            Run result with all metrics and logs
        """
        start_time = current_time_ms()
        run_id = f"als070_{self._seed}_{start_time}"

        if self._verbose:
            print(f"Starting ALS-G v0.7 run: {run_id}")
            print(f"  Max cycles: {self._config.max_cycles}")
            print(f"  Eligibility threshold K: {self._config.eligibility_threshold_k}")
            print(f"  Candidate pool: {self._config.candidate_pool_policy.name}")

        # Initial succession
        self._succession_pending = True
        self._attempt_succession_v070()

        # Main loop
        while not self._stopped and self._cycle < self._config.max_cycles:
            self._cycle += 1
            self._sentinel.advance_cycle()

            # Handle NULL_AUTHORITY state
            if self._in_null_authority:
                # Time continues during NULL_AUTHORITY
                # Check for succession boundary (epoch end)
                if self._cycle % self._config.renewal_check_interval == 0:
                    self._epoch_index += 1
                    # No streak updates during NULL_AUTHORITY (per spec)
                    # Try succession again
                    self._attempt_succession_v070()
                continue

            # Check if succession is needed
            if self._succession_pending:
                success = self._attempt_succession_v070()
                if not success:
                    continue  # In NULL_AUTHORITY now

            # Execute working mind cycle (consumes step budget)
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                # Check step budget (after rent + commitment deductions)
                adjusted_effective = self._current_effective_steps - self._commitment_cost_this_epoch
                if self._epoch_steps_used >= adjusted_effective:
                    pass  # Budget exhausted
                else:
                    violation = self._execute_working_mind_cycle_v060()
                    if violation:
                        self._handle_lease_revocation(violation[0], violation[1])
                        continue

            # Check renewal at epoch boundaries
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                if self._cycle % self._config.renewal_check_interval == 0:
                    # Evaluate commitments before renewal check
                    self._evaluate_commitments_at_epoch_end()
                    # Update streak BEFORE renewal (per spec: epoch end)
                    self._update_streak_at_epoch_end()
                    # Proceed with renewal
                    self._check_renewal_with_rent()

            # Check lease expiration
            if self._current_lease and self._current_lease.is_expired(self._cycle):
                self._handle_lease_expiration()

            # Check degeneracy
            self._check_degeneracy()

        # Finalize
        if not self._stopped:
            self._stop_reason = ALSStopReason.HORIZON_EXHAUSTED

        # End any active lapse
        if self._in_null_authority and self._current_lapse:
            self._current_lapse.end_cycle = self._cycle
            self._current_lapse.duration_cycles = self._cycle - self._current_lapse.start_cycle
            if self._null_authority_start_epoch is not None:
                self._current_lapse.duration_epochs = self._epoch_index - self._null_authority_start_epoch
            self._lapse_events.append(self._current_lapse)

        # Finalize active tenure
        if self._current_tenure is not None:
            self._end_tenure("HORIZON_EXHAUSTED")

        duration = current_time_ms() - start_time

        # Get commitment metrics
        ledger_metrics = self._commitment_ledger.get_metrics()

        # Compute satisfaction rate
        total_evaluations = ledger_metrics["total_satisfied"] + ledger_metrics["total_failed"]
        satisfaction_rate = 0.0
        if total_evaluations > 0:
            satisfaction_rate = ledger_metrics["total_satisfied"] / total_evaluations

        # Compute eligibility rejection rate
        eligibility_rejection_rate = 0.0
        if self._total_candidates_at_succession > 0:
            eligibility_rejection_rate = self._eligibility_rejections / self._total_candidates_at_succession

        # Compute lapse metrics
        total_lapse_cycles = sum(e.duration_cycles for e in self._lapse_events)
        total_lapse_epochs = sum(e.duration_epochs for e in self._lapse_events)
        max_lapse = max((e.duration_cycles for e in self._lapse_events), default=0)

        # Compute streak distribution at succession
        streak_dist: Dict[int, int] = {}
        for event in self._eligibility_events:
            streak = event.streak_at_decision
            streak_dist[streak] = streak_dist.get(streak, 0) + 1

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

        # v0.7: Compute draw ratios for composition verification (Run D)
        total_draws = self._attack_draws + self._control_draws
        attack_draw_ratio = self._attack_draws / total_draws if total_draws > 0 else 0.0
        control_draw_ratio = self._control_draws / total_draws if total_draws > 0 else 0.0

        result = ALSRunResultV070(
            run_id=run_id,
            seed=self._seed,
            spec_version="0.7",
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
            total_commitment_cost_charged=ledger_metrics["total_cost_charged"],
            commitment_satisfaction_count=ledger_metrics["total_satisfied"],
            commitment_failure_count=ledger_metrics["total_failed"],
            commitment_expired_count=ledger_metrics["total_expired"],
            commitment_default_count=ledger_metrics["total_defaulted"],
            semantic_debt_mass=ledger_metrics["semantic_debt_mass"],
            commitment_satisfaction_rate=satisfaction_rate,
            # v0.7 metrics
            eligibility_rejection_count=self._eligibility_rejections,
            eligibility_rejection_rate=eligibility_rejection_rate,
            empty_eligible_set_events=len(self._lapse_events),
            total_lapse_duration_cycles=total_lapse_cycles,
            total_lapse_duration_epochs=total_lapse_epochs,
            max_lapse_duration_cycles=max_lapse,
            ineligible_in_office_cycles=self._ineligible_in_office_cycles,
            sawtooth_count=self._sawtooth_count,
            streak_distribution_at_succession=streak_dist,
            final_streak_by_policy=dict(self._semantic_fail_streak),
            # Events
            succession_events=self._succession_events,
            renewal_events=self._renewal_events,
            expiration_events=self._expiration_events,
            revocation_events=self._revocation_events,
            bankruptcy_events=self._bankruptcy_events,
            epoch_rent_records=self._epoch_rent_records,
            tenure_records=self._tenure_records,
            tenure_entropy_samples=self._tenure_entropy_samples,
            commitment_events=[e.to_dict() for e in self._commitment_ledger.get_events()],
            commitment_cost_records=[r.to_dict() for r in self._commitment_ledger.get_cost_records()],
            eligibility_events=[e.to_dict() for e in self._eligibility_events],
            lapse_events=[e.to_dict() for e in self._lapse_events],
            semantic_epoch_records=[r.to_dict() for r in self._semantic_epoch_records],
            # v0.7 forced turnover (Run B)
            forced_turnover_events=[e.to_dict() for e in self._forced_turnover_events],
            forced_turnover_count=len(self._forced_turnover_events),
            post_init_successions=self._post_init_successions,
            # v0.7 composition verification (Run D)
            attack_draws=self._attack_draws,
            control_draws=self._control_draws,
            attack_draw_ratio=attack_draw_ratio,
            control_draw_ratio=control_draw_ratio,
            pool_policy=self._config.candidate_pool_policy.name,
            duration_ms=duration,
        )

        if self._verbose:
            print(f"\nALS-G v0.7 run complete:")
            print(f"  S*: {result.s_star}")
            print(f"  Cycles: {result.total_cycles}")
            print(f"  Renewals: {result.total_renewals}")
            print(f"  Post-init successions: {result.post_init_successions}")
            print(f"  Forced turnovers: {result.forced_turnover_count}")
            print(f"  Eligibility rejections: {result.eligibility_rejection_count}")
            print(f"  Lapse events: {result.empty_eligible_set_events}")
            print(f"  Sawtooth patterns: {result.sawtooth_count}")
            print(f"  Stop: {result.stop_reason.name}")

        return result


# =============================================================================
# AKI v0.8: ALS-A (Authority Leases with Constitutional Temporal Amnesty)
# =============================================================================


class LapseCause(Enum):
    """
    Classification of lapse cause per spec §6.2.

    - SEMANTIC: Candidates exist but all are ineligible (streak >= K)
    - STRUCTURAL: No structurally admissible candidates exist
    """
    SEMANTIC = auto()
    STRUCTURAL = auto()


@dataclass
class AmnestyEvent:
    """Record of a CTA amnesty application during NULL_AUTHORITY."""
    cycle: int
    epoch: int
    lapse_epoch_count: int
    policies_affected: List[str]
    streak_deltas: Dict[str, int]  # policy_id -> decrement applied
    aggregate_streak_mass_before: int
    aggregate_streak_mass_after: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "epoch": self.epoch,
            "lapse_epoch_count": self.lapse_epoch_count,
            "policies_affected": self.policies_affected,
            "streak_deltas": self.streak_deltas,
            "aggregate_streak_mass_before": self.aggregate_streak_mass_before,
            "aggregate_streak_mass_after": self.aggregate_streak_mass_after,
        }


@dataclass
class RecoveryEvent:
    """Record of a recovery from NULL_AUTHORITY."""
    cycle: int
    epoch: int
    lapse_duration_cycles: int
    lapse_duration_epochs: int
    amnesty_events_during_lapse: int
    lapse_cause: LapseCause
    recovered_policy_id: str
    streak_at_recovery: int
    # Added for stutter detection: epochs of authority after this recovery
    # Filled in when next lapse occurs or at horizon
    authority_epochs_after: Optional[int] = None
    authority_end_reason: Optional[str] = None  # "LAPSE", "HORIZON", "REVOCATION", "EXPIRY"
    is_stutter: Optional[bool] = None  # True if authority_epochs_after <= 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "epoch": self.epoch,
            "lapse_duration_cycles": self.lapse_duration_cycles,
            "lapse_duration_epochs": self.lapse_duration_epochs,
            "amnesty_events_during_lapse": self.amnesty_events_during_lapse,
            "lapse_cause": self.lapse_cause.name,
            "recovered_policy_id": self.recovered_policy_id,
            "streak_at_recovery": self.streak_at_recovery,
            "authority_epochs_after": self.authority_epochs_after,
            "authority_end_reason": self.authority_end_reason,
            "is_stutter": self.is_stutter,
        }


@dataclass
class LapseEventV080:
    """
    Extended lapse event for v0.8 with cause classification.
    """
    cycle: int
    epoch: int
    start_cycle: int
    start_epoch: int
    end_cycle: Optional[int] = None
    end_epoch: Optional[int] = None
    duration_cycles: int = 0
    duration_epochs: int = 0
    cause: LapseCause = LapseCause.SEMANTIC
    amnesty_events_during: int = 0
    recovered: bool = False
    ineligible_policies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "epoch": self.epoch,
            "start_cycle": self.start_cycle,
            "start_epoch": self.start_epoch,
            "end_cycle": self.end_cycle,
            "end_epoch": self.end_epoch,
            "duration_cycles": self.duration_cycles,
            "duration_epochs": self.duration_epochs,
            "cause": self.cause.name,
            "amnesty_events_during": self.amnesty_events_during,
            "recovered": self.recovered,
            "ineligible_policies": self.ineligible_policies,
        }


@dataclass
class ALSConfigV080(ALSConfigV070):
    """
    Configuration for ALS-A v0.8 runs.

    Extends ALSConfigV070 with Constitutional Temporal Amnesty (CTA) settings.

    Per spec §6.4:
    - AMNESTY_INTERVAL: Epochs between amnesty applications (default: 10)
    - AMNESTY_DECAY: Streak decrement per amnesty (default: 1)
    """
    # CTA parameters (frozen defaults per spec)
    amnesty_interval: int = 10   # Epochs between amnesty applications
    amnesty_decay: int = 1       # Streak decrement per amnesty

    # Enable/disable CTA (for comparison runs)
    cta_enabled: bool = True


@dataclass
class ALSRunResultV080:
    """
    Result of an ALS-A v0.8 run.

    Extends ALSRunResultV070 with CTA-specific metrics.
    """
    # Base metrics (inherited from V070)
    run_id: str
    seed: int
    spec_version: str = "0.8"
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

    # v0.5.2 expressivity metrics
    total_bankruptcies: int = 0
    total_rent_charged: int = 0
    renewal_attempts: int = 0
    renewal_successes: int = 0
    time_to_first_renewal_fail: Optional[int] = None
    e_class_distribution: Dict[str, int] = field(default_factory=dict)
    renewal_rate_by_e_class: Dict[str, float] = field(default_factory=dict)
    residence_by_e_class: Dict[str, float] = field(default_factory=dict)

    # v0.6 commitment metrics
    total_commitment_cost_charged: int = 0
    commitment_satisfaction_count: int = 0
    commitment_failure_count: int = 0
    commitment_expired_count: int = 0
    commitment_default_count: int = 0
    semantic_debt_mass: int = 0
    commitment_satisfaction_rate: float = 0.0

    # v0.7 eligibility metrics
    eligibility_rejection_count: int = 0
    eligibility_rejection_rate: float = 0.0
    empty_eligible_set_events: int = 0  # Lapse triggers
    total_lapse_duration_cycles: int = 0
    total_lapse_duration_epochs: int = 0
    max_lapse_duration_cycles: int = 0
    ineligible_in_office_cycles: int = 0
    sawtooth_count: int = 0
    streak_distribution_at_succession: Dict[int, int] = field(default_factory=dict)
    final_streak_by_policy: Dict[str, int] = field(default_factory=dict)

    # v0.7 forced turnover and composition
    forced_turnover_events: List[Dict] = field(default_factory=list)
    forced_turnover_count: int = 0
    post_init_successions: int = 0
    attack_draws: int = 0
    control_draws: int = 0
    attack_draw_ratio: float = 0.0
    control_draw_ratio: float = 0.0
    pool_policy: str = "V060_DEFAULT"

    # v0.8 CTA metrics (new)
    amnesty_event_count: int = 0
    amnesty_epochs: int = 0  # Total epochs where amnesty fired
    aggregate_streak_mass_before_amnesty: int = 0
    aggregate_streak_mass_after_amnesty: int = 0
    total_streak_decay_applied: int = 0
    recovery_count: int = 0
    time_to_first_recovery: Optional[int] = None  # Cycles
    mean_time_to_recovery: float = 0.0
    stutter_recovery_count: int = 0  # Recoveries lasting only 1 epoch
    authority_uptime_cycles: int = 0
    authority_uptime_fraction: float = 0.0
    lapse_fraction: float = 0.0
    semantic_lapse_count: int = 0
    structural_lapse_count: int = 0
    recovery_yield: float = 0.0  # epochs of authority after recovery / epochs in lapse to achieve recovery
    max_recovery_latency_epochs: int = 0  # Longest time in lapse before recovery
    hollow_recovery_count: int = 0  # Recovery followed by re-lapse within 1 epoch

    # Events (inherited)
    succession_events: List[SuccessionEvent] = field(default_factory=list)
    renewal_events: List[RenewalEvent] = field(default_factory=list)
    expiration_events: List[ExpirationEvent] = field(default_factory=list)
    revocation_events: List[RevocationEvent] = field(default_factory=list)
    bankruptcy_events: List[BankruptcyEvent] = field(default_factory=list)
    epoch_rent_records: List[EpochRentRecord] = field(default_factory=list)
    tenure_records: List[TenureRecord] = field(default_factory=list)
    tenure_entropy_samples: List[float] = field(default_factory=list)

    # v0.6 commitment events
    commitment_events: List[Any] = field(default_factory=list)
    commitment_cost_records: List[Any] = field(default_factory=list)

    # v0.7 eligibility events
    eligibility_events: List[Dict] = field(default_factory=list)
    lapse_events: List[Dict] = field(default_factory=list)
    semantic_epoch_records: List[Dict] = field(default_factory=list)

    # v0.8 CTA events (new)
    amnesty_events: List[Dict] = field(default_factory=list)
    recovery_events: List[Dict] = field(default_factory=list)
    lapse_events_v080: List[Dict] = field(default_factory=list)

    # RSA telemetry (optional, None if RSA disabled)
    rsa: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
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
            "total_commitment_cost_charged": self.total_commitment_cost_charged,
            "commitment_satisfaction_count": self.commitment_satisfaction_count,
            "commitment_failure_count": self.commitment_failure_count,
            "commitment_expired_count": self.commitment_expired_count,
            "commitment_default_count": self.commitment_default_count,
            "semantic_debt_mass": self.semantic_debt_mass,
            "commitment_satisfaction_rate": self.commitment_satisfaction_rate,
            # v0.7 eligibility metrics
            "eligibility_rejection_count": self.eligibility_rejection_count,
            "eligibility_rejection_rate": self.eligibility_rejection_rate,
            "empty_eligible_set_events": self.empty_eligible_set_events,
            "total_lapse_duration_cycles": self.total_lapse_duration_cycles,
            "total_lapse_duration_epochs": self.total_lapse_duration_epochs,
            "max_lapse_duration_cycles": self.max_lapse_duration_cycles,
            "ineligible_in_office_cycles": self.ineligible_in_office_cycles,
            "sawtooth_count": self.sawtooth_count,
            "streak_distribution_at_succession": self.streak_distribution_at_succession,
            "final_streak_by_policy": self.final_streak_by_policy,
            # v0.7 forced turnover
            "forced_turnover_count": self.forced_turnover_count,
            "post_init_successions": self.post_init_successions,
            "attack_draws": self.attack_draws,
            "control_draws": self.control_draws,
            "attack_draw_ratio": self.attack_draw_ratio,
            "control_draw_ratio": self.control_draw_ratio,
            "pool_policy": self.pool_policy,
            # v0.8 CTA metrics
            "amnesty_event_count": self.amnesty_event_count,
            "amnesty_epochs": self.amnesty_epochs,
            "aggregate_streak_mass_before_amnesty": self.aggregate_streak_mass_before_amnesty,
            "aggregate_streak_mass_after_amnesty": self.aggregate_streak_mass_after_amnesty,
            "total_streak_decay_applied": self.total_streak_decay_applied,
            "recovery_count": self.recovery_count,
            "time_to_first_recovery": self.time_to_first_recovery,
            "mean_time_to_recovery": self.mean_time_to_recovery,
            "stutter_recovery_count": self.stutter_recovery_count,
            "authority_uptime_cycles": self.authority_uptime_cycles,
            "authority_uptime_fraction": self.authority_uptime_fraction,
            "lapse_fraction": self.lapse_fraction,
            "semantic_lapse_count": self.semantic_lapse_count,
            "structural_lapse_count": self.structural_lapse_count,
            "recovery_yield": self.recovery_yield,
            "max_recovery_latency_epochs": self.max_recovery_latency_epochs,
            "hollow_recovery_count": self.hollow_recovery_count,
            # Standard metrics
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
        }
        return result


class ALSHarnessV080(ALSHarnessV070):
    """
    v0.8 ALS-A harness: Authority Leases with Constitutional Temporal Amnesty.

    Per spec §6 and instructions §8.3:
    - CTA runs at epoch boundaries during NULL_AUTHORITY
    - Succession attempts occur only at scheduled succession boundaries
    - Candidate pool regenerated on every succession attempt
    - Global cycles and epochs continue unchanged during lapse
    - First semantic window after recovery is first completed epoch

    Key invariants:
    - CTA is the ONLY permitted streak modification during lapse
    - No verifiers execute during lapse
    - No agent action during lapse
    - TTL clocks advance during lapse
    """

    def __init__(
        self,
        seed: int = 42,
        config: Optional[ALSConfigV080] = None,
        verbose: bool = False,
        rsa_config: Optional["RSAConfig"] = None,
        rsa_policy_config: Optional["RSAPolicyConfig"] = None,
    ):
        """
        Initialize v0.8 harness.

        Args:
            seed: Random seed for reproducibility
            config: Run configuration
            verbose: Enable verbose logging
            rsa_config: Optional RSA v0.1/v0.2 stress layer configuration (default: None = disabled)
            rsa_policy_config: Optional RSA v1.0 policy configuration (default: None = disabled)
        """
        # Initialize parent (V070)
        super().__init__(seed=seed, config=config or ALSConfigV080(), verbose=verbose)

        # Cast config to V080 type
        self._config: ALSConfigV080 = config or ALSConfigV080()

        # v0.8: CTA state
        self._lapse_epoch_count: int = 0
        self._amnesty_events_this_lapse: int = 0

        # v0.8: Event tracking
        self._amnesty_events: List[AmnestyEvent] = []
        self._recovery_events: List[RecoveryEvent] = []
        self._lapse_events_v080: List[LapseEventV080] = []
        self._current_lapse_v080: Optional[LapseEventV080] = None

        # v0.8: Metrics tracking
        self._authority_uptime_cycles: int = 0
        self._lapse_time_cycles: int = 0
        self._recovery_latencies: List[int] = []  # Epochs to recovery
        self._post_recovery_durations: List[int] = []  # Epochs of authority after each recovery
        self._last_recovery_epoch: Optional[int] = None
        self._last_recovery_event: Optional[RecoveryEvent] = None  # Track for authority span completion
        self._time_to_first_recovery: Optional[int] = None

        # v0.8: Aggregate streak tracking
        self._total_streak_decay_applied: int = 0
        self._aggregate_streak_before_amnesty: int = 0
        self._aggregate_streak_after_amnesty: int = 0

        # RSA v0.1/v0.2 stress layer (optional; disabled by default)
        self._rsa_config = rsa_config
        self._rsa_adversary = None
        self._rsa_telemetry = None
        if RSA_AVAILABLE and rsa_config is not None and rsa_config.rsa_enabled:
            self._rsa_adversary = RSAAdversary.from_config(rsa_config, seed)
            self._rsa_telemetry = RSATelemetry(
                enabled=rsa_config.rsa_enabled,
                noise_model=rsa_config.rsa_noise_model.value,
                scope=rsa_config.rsa_scope.value,
                p_flip_ppm=rsa_config.rsa_p_flip_ppm,
                rng_stream=rsa_config.rsa_rng_stream,
                seed_rsa=self._rsa_adversary.seed_rsa if self._rsa_adversary else 0,
            )

        # RSA v1.0 policy layer (optional; disabled by default)
        # RSA v2.0 uses AdaptiveRSAWrapper for models F-I
        # RSA v3.0 uses StatefulRSAWrapper for models J-L
        self._rsa_policy_config = rsa_policy_config
        self._rsa_policy_wrapper = None
        self._rsa_v2_wrapper = None  # v2.0 adaptive adversary wrapper
        self._rsa_v3_wrapper = None  # v3.0 stateful adversary wrapper
        if RSA_POLICY_AVAILABLE and rsa_policy_config is not None:
            rsa_version = getattr(rsa_policy_config, 'rsa_version', 'v1')
            # Check if v3.0 model
            if RSA_V3_AVAILABLE and rsa_version == 'v3':
                self._rsa_v3_wrapper = StatefulRSAWrapper.from_config(rsa_policy_config)
                if self._rsa_v3_wrapper and self._verbose:
                    print(f"[RSA v3.0] Stateful adversary enabled: {rsa_policy_config.policy_model.value}")
            # Check if v2.0 model
            elif RSA_V2_AVAILABLE and rsa_version == 'v2':
                self._rsa_v2_wrapper = AdaptiveRSAWrapper.from_config(rsa_policy_config)
                if self._rsa_v2_wrapper and self._verbose:
                    print(f"[RSA v2.0] Adaptive adversary enabled: {rsa_policy_config.policy_model.value}")
            else:
                self._rsa_policy_wrapper = RSAPolicyWrapper.from_config(rsa_policy_config)
                if self._rsa_policy_wrapper and self._verbose:
                    print(f"[RSA v1.0] Policy enabled: {rsa_policy_config.policy_model.value}")

        # v1.0 telemetry tracking (per-epoch)
        self._rsa_v10_epoch_telemetry: List[Dict[str, Any]] = []

        # v2.0: Lapse tracking for observable interface
        # _last_epoch_had_lapse: True if ANY lapse occurred in the prior epoch
        # _current_epoch_has_lapse: Accumulator for current epoch
        self._last_epoch_had_lapse: bool = False
        self._current_epoch_has_lapse: bool = False
        self._last_epoch_index: int = -1  # Track epoch transitions

        # v2.0: Renewal outcome tracking for Run 4 (RENEWAL_FEEDBACK)
        # _last_renewal_outcome: True=SUCCEEDED, False=FAILED, None=NOT_ATTEMPTED
        # Set at renewal decision point, read by _build_kernel_state_for_rsa_v2()
        self._last_renewal_outcome: Optional[bool] = None

        # v0.8: Epoch-indexed action trace for O(1) epoch lookup
        # This avoids O(n) scans of full action_trace in _compute_commitment_keys_raw
        self._action_trace_by_epoch: Dict[int, List[Any]] = {}

        # RSA v3.1 instrumentation: Track enabled-path invocation for NONE-path auditing
        # wrapper_invoked_count: Times RSA intercept path was evaluated (even if no wrapper)
        # override_count: Times action was actually changed by RSA policy
        self._rsa_wrapper_invoked_count: int = 0
        self._rsa_override_count: int = 0

    def _execute_working_mind_cycle_v080(self) -> Optional[tuple[LeaseViolation, str]]:
        """
        Execute working mind cycle with RSA v1.0 policy interception (v0.8 override).

        When RSA v1.0 policy is active, intercepts the agent's action proposal
        and replaces it with the adversarial policy's emission.

        This is the ONLY difference from _execute_working_mind_cycle_v060:
        - Agent proposes action
        - If RSA v1.0 active: replace action with policy emission
        - Continue with normal action processing
        """
        if self._current_mind is None:
            return None

        # Consume step
        self._epoch_steps_used += 1

        # Sentinel check
        step_allowed, step_violation, step_detail = self._sentinel.check_step()
        if not step_allowed and step_violation is not None:
            lease_violation = self._map_sentinel_violation(step_violation)
            return (lease_violation, step_detail or str(step_violation))

        # Get action from working mind
        adjusted_effective = self._current_effective_steps - self._commitment_cost_this_epoch
        observation = {
            "cycle": self._cycle,
            "state": {"running": True},
            "epoch_steps_remaining": adjusted_effective - self._epoch_steps_used,
            "active_commitments": [c.cid for c in self._commitment_ledger.get_active_commitments()],
        }

        try:
            original_action = self._current_mind.propose_action(observation)
        except Exception as e:
            return (LeaseViolation.CONSTRAINT_VIOLATION, f"Action proposal failed: {e}")

        # RSA v1.0: Intercept action if policy is active
        # RSA v2.0: Intercept action via adaptive adversary if wrapper is active
        # RSA v3.0: Intercept action via stateful adversary if wrapper is active
        # v3.1 instrumentation: Track when RSA intercept path is evaluated
        rsa_override = False
        if self._rsa_policy_config is not None:
            # RSA is configured (even if NONE) - count intercept path evaluation
            self._rsa_wrapper_invoked_count += 1

        if self._rsa_v3_wrapper is not None and original_action is not None:
            # v3.0: Build kernel state and sample observable
            epoch = self._compute_global_epoch()
            cycle_in_epoch = (self._cycle - 1) % self._config.renewal_check_interval
            kernel_state = self._build_kernel_state_for_rsa_v2()  # Reuse v2.0 kernel state builder
            observable = self._rsa_v3_wrapper.sample_observable(kernel_state)
            # v3.0: emit() handles state update internally after action selection
            action = self._rsa_v3_wrapper.intercept(observable, epoch, cycle_in_epoch, original_action)
            if self._verbose:
                original_type = original_action.get("action_type", "NONE") if original_action else "NONE"
                new_type = action.get("action_type", "NONE")
                if original_type != new_type:
                    print(f"    [RSA v3.0] Action override: {original_type} -> {new_type}")
                    rsa_override = True
            else:
                original_type = original_action.get("action_type", "NONE") if original_action else "NONE"
                new_type = action.get("action_type", "NONE")
                rsa_override = (original_type != new_type)
        elif self._rsa_v2_wrapper is not None and original_action is not None:
            # v2.0: Build kernel state and sample observable
            epoch = self._compute_global_epoch()
            cycle_in_epoch = (self._cycle - 1) % self._config.renewal_check_interval
            kernel_state = self._build_kernel_state_for_rsa_v2()
            observable = self._rsa_v2_wrapper.sample_observable(kernel_state)
            # Update state at epoch start (cycle_in_epoch == 0)
            if cycle_in_epoch == 0:
                self._rsa_v2_wrapper.update_state(observable)
            action = self._rsa_v2_wrapper.intercept(observable, epoch, cycle_in_epoch, original_action)
            if self._verbose:
                original_type = original_action.get("action_type", "NONE") if original_action else "NONE"
                new_type = action.get("action_type", "NONE")
                if original_type != new_type:
                    print(f"    [RSA v2.0] Action override: {original_type} -> {new_type}")
                    rsa_override = True
            else:
                original_type = original_action.get("action_type", "NONE") if original_action else "NONE"
                new_type = action.get("action_type", "NONE")
                rsa_override = (original_type != new_type)
        elif self._rsa_policy_wrapper is not None and original_action is not None:
            epoch = self._compute_global_epoch()
            cycle_in_epoch = (self._cycle - 1) % self._config.renewal_check_interval
            action = self._rsa_policy_wrapper.intercept(epoch, cycle_in_epoch, original_action)
            if self._verbose:
                original_type = original_action.get("action_type", "NONE") if original_action else "NONE"
                new_type = action.get("action_type", "NONE")
                if original_type != new_type:
                    print(f"    [RSA v1.0] Action override: {original_type} -> {new_type}")
                    rsa_override = True
            else:
                # Check if override happened even without verbose
                original_type = original_action.get("action_type", "NONE") if original_action else "NONE"
                new_type = action.get("action_type", "NONE")
                rsa_override = (original_type != new_type)
        else:
            action = original_action

        # v3.1 instrumentation: Track override count
        if rsa_override:
            self._rsa_override_count += 1

        if action is None:
            return None

        # Track action
        self._epoch_actions_used += 1

        # Record action for verifier (ACV trace)
        # NOTE: When RSA v1.0 overrides, we use GLOBAL epoch for action trace
        # to ensure commitment evaluation aligns with RSA's epoch-based scheduling.
        # Per-policy epoch resets on succession, but RSA uses calendrical epochs.
        action_type = action.get("action_type", "UNKNOWN") if isinstance(action, dict) else getattr(action, "action_type", "UNKNOWN")
        payload = action.get("payload", {}) if isinstance(action, dict) else getattr(action, "payload", {})

        # Use global epoch when RSA v1.0/v2.0 is active, per-policy epoch otherwise
        rsa_active = self._rsa_policy_wrapper is not None or self._rsa_v2_wrapper is not None
        record_epoch = self._compute_global_epoch() if rsa_active else self._epoch_index

        action_record = self._ActionRecord(
            action_type=action_type,
            payload=payload if isinstance(payload, dict) else {},
            epoch=record_epoch,
            cycle=self._cycle,
            sequence_num=self._action_sequence_num,
        )
        self._action_trace.append(action_record)

        # Update epoch index for O(1) lookup (fixes O(n²) in _compute_commitment_keys_raw)
        if record_epoch not in self._action_trace_by_epoch:
            self._action_trace_by_epoch[record_epoch] = []
        self._action_trace_by_epoch[record_epoch].append(action_record)

        self._action_sequence_num += 1

        # Sentinel action check
        # RSA v1.0: Validate action against expanded interface.
        # RSA policies emit only baseline commitment action types (LOG, SET, GET, SEQUENCE, WAIT).
        # These are the same action types used by CommitmentAwareSuccessor_v1.
        # We check against the sentinel, but the interface was expanded at lease bind time
        # when RSA v1.0 is active (see _bind_rsa_expanded_interface).
        allowed, violation_type, detail = self._sentinel.check_action(action)
        if not allowed and violation_type is not None:
            lease_violation = self._map_sentinel_violation(violation_type)
            return (lease_violation, detail or str(violation_type))

        return None

    def _check_renewal_with_rent(self) -> None:
        """
        Override to track renewal outcome for RSA v2.0 observable (Run 4).

        Sets _last_renewal_outcome based on the renewal decision:
        - True: renewal succeeded
        - False: renewal failed (eligibility, budget, attestation, etc.)
        - None: no renewal attempted (e.g., during lapse)

        This observable is read by _build_kernel_state_for_rsa_v2() and
        exposed as OBS_RENEWAL_OUTCOME in the v2.0 interface.
        """
        # Record count of renewal events before parent call
        events_before = len(self._renewal_events)

        # Call parent implementation
        super()._check_renewal_with_rent()

        # Check if a renewal event was added
        if len(self._renewal_events) > events_before:
            # A renewal check was evaluated - get the outcome
            latest_event = self._renewal_events[-1]
            if latest_event.cycle == self._cycle:
                self._last_renewal_outcome = latest_event.success
        # If no new event, parent may have returned early (no lease, not active, etc.)
        # In that case, leave _last_renewal_outcome unchanged (will be reset at epoch start)

    def _compute_global_epoch(self) -> int:
        """Compute global epoch index from current cycle.

        Unlike self._epoch_index which resets per-authority, this provides
        a monotonically increasing epoch counter for RSA hash input.
        """
        return self._cycle // self._config.renewal_check_interval

    def _build_kernel_state_for_rsa_v2(self) -> Dict[str, Any]:
        """Build kernel state dict for RSA v2.0 observable sampling.

        This extracts only the 6 observable components from kernel state,
        respecting the v2.0 architectural separation where adversaries
        cannot see internal kernel semantics.

        Returns:
            Dict with keys matching AdaptiveRSAWrapper.sample_observable() expectations
        """
        current_epoch = self._compute_global_epoch()

        # Track if we're entering a new epoch (for post-sampling reset)
        is_new_epoch = current_epoch != self._last_epoch_index

        # Epoch transition: roll over lapse tracking
        if is_new_epoch:
            # Save current epoch's lapse status as "last epoch"
            self._last_epoch_had_lapse = self._current_epoch_has_lapse
            # Reset current epoch accumulator
            self._current_epoch_has_lapse = False
            self._last_epoch_index = current_epoch

        # Track if we're currently in lapse (for this epoch)
        if self._in_null_authority:
            self._current_epoch_has_lapse = True

        # Determine authority status
        authority = None
        if hasattr(self, '_current_authority') and self._current_authority is not None:
            authority = "HAS_AUTHORITY"

        # Last renewal result (None if not attempted)
        last_renewal_result = None
        if hasattr(self, '_last_renewal_outcome'):
            last_renewal_result = self._last_renewal_outcome

        # CTA state (v2.0 observable wiring per binding decision 2026-01-08)
        # CTA is a FORWARD-LOOKING CONSTITUTIONAL CLOCK, not a lapse-mode flag.
        # During authority: observable as "projected amnesty phase if lapse began now"
        # During lapse: computed but agent doesn't act
        #
        # cta_active = True always (CTA timing is always defined)
        # cta_length = amnesty_interval (10 epochs)
        # cta_index = global_epoch % amnesty_interval
        if self._config.cta_enabled:
            cta_active = True
            cta_length = self._config.amnesty_interval  # 10
            cta_index = current_epoch % self._config.amnesty_interval
        else:
            cta_active = False
            cta_index = 0
            cta_length = self._config.amnesty_interval

        # Successive renewal failures (use current policy's streak)
        successive_failures = 0
        if self._active_policy_id:
            successive_failures = self._semantic_fail_streak.get(self._active_policy_id, 0)

        # Build result dict (sample renewal outcome before reset)
        result = {
            "epoch_index": current_epoch,
            "authority": authority,
            "lapse_occurred_last_epoch": self._last_epoch_had_lapse,
            "last_renewal_result": last_renewal_result,
            "cta_active": cta_active,
            "cta_current_index": cta_index,
            "cta_length": cta_length,
            "successive_renewal_failures": successive_failures,
        }

        # Reset renewal outcome for new epoch AFTER sampling
        # This ensures epoch t+1 sees NOT_ATTEMPTED if no renewal check fires in epoch t
        if is_new_epoch:
            self._last_renewal_outcome = None

        return result

    def _evaluate_commitments_at_epoch_end(self) -> None:
        """
        Evaluate all commitments at epoch end (v0.8 override with RSA v1.0 support).

        When RSA v1.0 policy is active, uses GLOBAL epochs for action window
        matching (since actions are recorded with global epochs). This ensures
        RSA's epoch-based action scheduling aligns with commitment verification.

        NOTE: At epoch boundary (cycle % interval == 0), we evaluate the epoch
        that just ENDED, not the one starting. For cycle 50, we evaluate epoch 0.
        This is computed as (cycle - 1) // interval when cycle > 0.

        Per spec §6.7:
        - Evaluation at epoch end (after successor actions)
        - Use ACV trace for the window
        """
        # Determine epoch mode: global (RSA v1.0/v2.0) or per-policy (standard)
        rsa_active = self._rsa_policy_wrapper is not None or self._rsa_v2_wrapper is not None
        if rsa_active:
            # At epoch boundary (cycle 50, 100, etc.), we're evaluating the epoch that just ended
            # e.g., at cycle 50, we evaluate epoch 0 (cycles 1-49)
            # The formula (cycle - 1) // interval gives the correct epoch for boundary cycles
            if self._cycle > 0 and self._cycle % self._config.renewal_check_interval == 0:
                # At exact boundary: evaluate previous epoch
                window_end = (self._cycle - 1) // self._config.renewal_check_interval
            else:
                window_end = self._compute_global_epoch()
        else:
            window_end = self._epoch_index

        for commitment in self._commitment_ledger.get_active_commitments():
            # Get window bounds
            window_start = max(0, window_end - commitment.window + 1)

            # Filter actions in window using epoch index for O(window) complexity
            # instead of O(n) scan of entire action trace
            window_actions = []
            for ep in range(window_start, window_end + 1):
                if ep in self._action_trace_by_epoch:
                    window_actions.extend(self._action_trace_by_epoch[ep])

            # Get verifier params
            params = self._get_commitment_params(commitment.cid)

            # Run verifier
            try:
                result = self._verify_commitment(
                    verifier_id=commitment.verifier_id,
                    actions=window_actions,
                    window_start_epoch=window_start,
                    window_end_epoch=window_end,
                    params=params,
                )
            except ValueError as e:
                # Unknown verifier - treat as failure
                result = False

            # Update commitment status (use per-policy epoch for ledger compatibility)
            self._commitment_ledger.evaluate_commitment(
                cid=commitment.cid,
                epoch=self._epoch_index,  # Ledger still uses per-policy epochs
                cycle=self._cycle,
                verifier_result=result,
            )

        # Check TTL expirations
        self._commitment_ledger.check_ttl_expirations(
            epoch=self._epoch_index,
            cycle=self._cycle,
        )

    def _record_rsa_v10_epoch_telemetry(self) -> None:
        """
        Record RSA v1.0 per-epoch telemetry.

        Per spec requirements:
        - steps_used_epoch: cycles consumed in epoch
        - actions_emitted_epoch: total action count in epoch
        - budget_remaining_epoch: cycles remaining at renewal check
        """
        if self._rsa_policy_wrapper is None:
            return

        global_epoch = self._compute_global_epoch()
        adjusted_effective = self._current_effective_steps - self._commitment_cost_this_epoch

        record = {
            "epoch": global_epoch,
            "steps_used_epoch": self._epoch_steps_used,
            "actions_emitted_epoch": self._epoch_actions_used,
            "budget_remaining_epoch": adjusted_effective - self._epoch_steps_used,
            "rsa_policy_model": self._rsa_policy_wrapper.model.value,
            "authority_state": "ACTIVE" if not self._in_null_authority else "NULL",
        }
        self._rsa_v10_epoch_telemetry.append(record)

        if self._verbose:
            print(f"    [RSA v1.0 Telemetry] epoch={global_epoch}, "
                  f"steps={self._epoch_steps_used}, actions={self._epoch_actions_used}, "
                  f"budget_remaining={adjusted_effective - self._epoch_steps_used}")

    def _compute_commitment_keys_raw(self) -> tuple[bool, bool, bool]:
        """
        Compute raw commitment keys (v0.8 override with RSA v1.0 support).

        When RSA v1.0 policy is active, computes commitment satisfaction
        directly from the action trace using GLOBAL epochs. This bypasses
        the commitment ledger's "failed = permanently inactive" semantics.

        RSA v1.0 testing requires commitments to be re-evaluated every epoch
        regardless of previous failure status.

        Returns:
            Tuple of (c0_ok, c1_ok, c2_ok) - raw values
        """
        if self._rsa_policy_wrapper is None:
            # No RSA v1.0: use parent implementation (ledger-based)
            return super()._compute_commitment_keys_raw()

        # RSA v1.0 mode: compute directly from action trace using global epochs
        # At epoch boundary, evaluate the epoch that just ended
        if self._cycle > 0 and self._cycle % self._config.renewal_check_interval == 0:
            eval_epoch = (self._cycle - 1) // self._config.renewal_check_interval
        else:
            eval_epoch = self._compute_global_epoch()

        # Helper: get actions for a range of epochs using epoch index (O(window) not O(n))
        def get_actions_in_range(start_epoch: int, end_epoch: int) -> List[Any]:
            """Collect actions from epoch index for specified range."""
            result = []
            for ep in range(start_epoch, end_epoch + 1):
                if ep in self._action_trace_by_epoch:
                    result.extend(self._action_trace_by_epoch[ep])
            return result

        # C0: At least 1 LOG action in current epoch
        current_epoch_actions = self._action_trace_by_epoch.get(eval_epoch, [])
        c0_ok = any(a.action_type == "LOG" for a in current_epoch_actions)

        # C1: SET + GET within 2-epoch window (check current and previous epoch)
        c1_window_start = max(0, eval_epoch - 1)
        c1_window_actions = get_actions_in_range(c1_window_start, eval_epoch)
        has_set = any(a.action_type == "SET" for a in c1_window_actions)
        has_get = any(a.action_type == "GET" for a in c1_window_actions)
        c1_ok = has_set and has_get

        # C2: SEQUENCE action within 3-epoch window with valid payload shape
        # The real verifier (VRF_ACTION_HAS_PAYLOAD_SHAPE) requires:
        # - action_type in {"SEQUENCE", "BATCH"}
        # - payload["actions"] is a list with length >= 2
        c2_window_start = max(0, eval_epoch - 2)
        c2_window_actions = get_actions_in_range(c2_window_start, eval_epoch)
        c2_ok = any(
            a.action_type in ("SEQUENCE", "BATCH")
            and isinstance(a.payload.get("actions", []), (list, tuple))
            and len(a.payload.get("actions", [])) >= 2
            for a in c2_window_actions
        )

        return (c0_ok, c1_ok, c2_ok)

    def _update_streak_at_epoch_end(self) -> None:
        """
        Update semantic failure streak at epoch end (v0.8 override with RSA hook).

        Per spec §6.2:
        - Only updates for active authority holder
        - No updates during NULL_AUTHORITY (handled in main loop)

        RSA v0.1/v0.2 Architecture A:
        - AKI computes raw keys (_compute_commitment_keys_raw)
        - RSA corrupts keys (adversary.corrupt_keys)
        - AKI aggregates SEM_PASS from corrupted keys (_aggregate_sem_pass)

        This ensures RSA uses AKI's exact aggregation function, not a reimplementation.
        """
        # Compute global epoch for RSA (never resets, unlike self._epoch_index)
        global_epoch = self._compute_global_epoch()

        # Note: This method is NOT called during NULL_AUTHORITY.
        # Lapse epoch recording is handled in the main loop.

        if self._active_policy_id is None:
            # No active authority holder
            return

        policy_id = self._active_policy_id
        streak_before = self._get_policy_streak(policy_id)

        # Step 1: AKI computes raw commitment keys
        c0_ok_raw, c1_ok_raw, c2_ok_raw = self._compute_commitment_keys_raw()

        # Step 2: RSA corrupts keys (if active)
        if self._rsa_adversary is not None and self._rsa_telemetry is not None:
            # RSA corrupts individual keys; we pass AKI's aggregator for SEM_PASS recomputation
            c0_ok, c1_ok, c2_ok, sem_pass, rsa_record = self._rsa_adversary.corrupt(
                epoch=global_epoch,
                c0_raw=c0_ok_raw,
                c1_raw=c1_ok_raw,
                c2_raw=c2_ok_raw,
                sem_pass_raw=self._aggregate_sem_pass(c0_ok_raw, c1_ok_raw, c2_ok_raw),
                aggregator=self._aggregate_sem_pass,  # AKI's exact function (not lambda)
            )
            self._rsa_telemetry.record_epoch(rsa_record)
        else:
            # No RSA: use raw values with AKI aggregation
            c0_ok, c1_ok, c2_ok = c0_ok_raw, c1_ok_raw, c2_ok_raw
            sem_pass = self._aggregate_sem_pass(c0_ok, c1_ok, c2_ok)

        # Continue with standard streak update logic (unchanged from v0.7)
        if sem_pass:
            # Reset streak on pass
            # Check for sawtooth pattern: was at K-1 before passing
            if streak_before == self._config.eligibility_threshold_k - 1:
                self._sawtooth_count += 1
            self._semantic_fail_streak[policy_id] = 0
            streak_after = 0
        else:
            # Increment streak on fail
            self._semantic_fail_streak[policy_id] = streak_before + 1
            streak_after = streak_before + 1

        # Track ineligible-in-office time
        if streak_after >= self._config.eligibility_threshold_k:
            self._ineligible_in_office_cycles += 1

        # Record semantic epoch
        self._semantic_epoch_records.append(SemanticEpochRecord(
            epoch=self._epoch_index,
            cycle=self._cycle,
            active_policy_id=policy_id,
            c0_ok=c0_ok,
            c1_ok=c1_ok,
            c2_ok=c2_ok,
            sem_pass=sem_pass,
            streak_before=streak_before,
            streak_after=streak_after,
        ))

        if self._verbose:
            status = "PASS" if sem_pass else "FAIL"
            rsa_tag = " [RSA]" if (self._rsa_adversary and sem_pass != sem_pass_raw) else ""
            print(f"    [Epoch {self._epoch_index}] SEM_{status}{rsa_tag}: "
                  f"C0={c0_ok}, C1={c1_ok}, C2={c2_ok} | "
                  f"streak[{policy_id}]: {streak_before} → {streak_after}")

    def _compute_aggregate_streak_mass(self) -> int:
        """Compute sum of all policy streaks."""
        return sum(self._semantic_fail_streak.values())

    def _classify_lapse_cause(
        self,
        candidates: List[SuccessorCandidate],
        eligible_candidates: List[SuccessorCandidate],
    ) -> LapseCause:
        """
        Classify lapse cause per spec §6.2.

        - SEMANTIC: Candidates exist but all are ineligible
        - STRUCTURAL: No structurally admissible candidates exist
        """
        # For now, we treat all generated candidates as structurally admissible
        # (the generator produces valid candidates by construction)
        # So if we have candidates but none are eligible, it's SEMANTIC
        if candidates and not eligible_candidates:
            return LapseCause.SEMANTIC
        elif not candidates:
            return LapseCause.STRUCTURAL
        else:
            # Should not reach here if called when entering lapse
            return LapseCause.SEMANTIC

    def _apply_cta_amnesty(self) -> None:
        """
        Apply Constitutional Temporal Amnesty.

        Per spec §6.5:
        - Only runs during NULL_AUTHORITY
        - Decrements all policy streaks by AMNESTY_DECAY
        - No streak increments, no resets, no agent action
        """
        if not self._in_null_authority:
            return  # CTA only runs during lapse

        if not self._config.cta_enabled:
            return  # CTA disabled for comparison runs

        # Compute aggregate mass before
        mass_before = self._compute_aggregate_streak_mass()

        # Apply decay to all policies
        policies_affected = []
        streak_deltas = {}
        for policy_id in list(self._semantic_fail_streak.keys()):
            old_streak = self._semantic_fail_streak[policy_id]
            if old_streak > 0:
                new_streak = max(0, old_streak - self._config.amnesty_decay)
                delta = old_streak - new_streak
                if delta > 0:
                    self._semantic_fail_streak[policy_id] = new_streak
                    policies_affected.append(policy_id)
                    streak_deltas[policy_id] = delta
                    self._total_streak_decay_applied += delta

        # Compute aggregate mass after
        mass_after = self._compute_aggregate_streak_mass()

        # Record amnesty event
        self._amnesty_events_this_lapse += 1
        event = AmnestyEvent(
            cycle=self._cycle,
            epoch=self._epoch_index,
            lapse_epoch_count=self._lapse_epoch_count,
            policies_affected=policies_affected,
            streak_deltas=streak_deltas,
            aggregate_streak_mass_before=mass_before,
            aggregate_streak_mass_after=mass_after,
        )
        self._amnesty_events.append(event)

        # Track aggregate masses
        self._aggregate_streak_before_amnesty += mass_before
        self._aggregate_streak_after_amnesty += mass_after

        if self._verbose:
            print(f"    [Epoch {self._epoch_index}] CTA AMNESTY: "
                  f"mass {mass_before} → {mass_after}, "
                  f"affected {len(policies_affected)} policies")

    def _enter_null_authority_v080(
        self,
        ineligible_policies: List[str],
        cause: LapseCause,
    ) -> None:
        """Enter NULL_AUTHORITY state with v0.8 cause classification."""
        # First: finalize the previous recovery's authority span if any
        if self._last_recovery_event is not None and self._last_recovery_epoch is not None:
            # Compute authority epochs using cycle count (more reliable than epoch index)
            # Authority duration = cycles since recovery / cycles_per_epoch
            cycles_since_recovery = self._cycle - self._last_recovery_event.cycle
            authority_epochs = cycles_since_recovery // self._config.renewal_check_interval
            self._last_recovery_event.authority_epochs_after = authority_epochs
            self._last_recovery_event.authority_end_reason = "LAPSE"
            self._last_recovery_event.is_stutter = authority_epochs <= 1
            self._post_recovery_durations.append(authority_epochs)
            self._last_recovery_event = None  # Clear to avoid double-counting

        self._in_null_authority = True
        self._null_authority_start_cycle = self._cycle
        self._null_authority_start_epoch = self._epoch_index

        # v2.0: Track lapse for RSA observable interface
        self._current_epoch_has_lapse = True

        # Reset lapse epoch counter
        self._lapse_epoch_count = 0
        self._amnesty_events_this_lapse = 0

        # Clear active authority
        self._current_mind = None
        self._current_lease = None
        self._active_policy_id = None

        # Create v0.80 lapse event
        self._current_lapse_v080 = LapseEventV080(
            cycle=self._cycle,
            epoch=self._epoch_index,
            start_cycle=self._cycle,
            start_epoch=self._epoch_index,
            cause=cause,
            ineligible_policies=ineligible_policies,
        )

        # Also create v0.7 compatible lapse event
        self._current_lapse = LapseEvent(
            cycle=self._cycle,
            epoch=self._epoch_index,
            start_cycle=self._cycle,
            ineligible_policies=ineligible_policies,
        )

        if self._verbose:
            print(f"    [Cycle {self._cycle}] LAPSE ({cause.name}): "
                  f"C_ELIG=∅, entering NULL_AUTHORITY")
            print(f"      Ineligible policies: {ineligible_policies}")

    def _exit_null_authority_v080(self, recovered_policy_id: str, streak: int) -> None:
        """Exit NULL_AUTHORITY state with recovery tracking."""
        # Finalize v0.80 lapse event
        if self._current_lapse_v080 is not None:
            self._current_lapse_v080.end_cycle = self._cycle
            self._current_lapse_v080.end_epoch = self._epoch_index
            self._current_lapse_v080.duration_cycles = self._cycle - self._current_lapse_v080.start_cycle
            self._current_lapse_v080.duration_epochs = self._epoch_index - self._current_lapse_v080.start_epoch
            self._current_lapse_v080.amnesty_events_during = self._amnesty_events_this_lapse
            self._current_lapse_v080.recovered = True
            self._lapse_events_v080.append(self._current_lapse_v080)

            # Track recovery latency
            lapse_duration_epochs = self._current_lapse_v080.duration_epochs
            self._recovery_latencies.append(lapse_duration_epochs)

            if self._time_to_first_recovery is None:
                self._time_to_first_recovery = self._current_lapse_v080.duration_cycles

            # Record recovery event (authority_epochs_after will be filled when next lapse occurs)
            recovery = RecoveryEvent(
                cycle=self._cycle,
                epoch=self._epoch_index,
                lapse_duration_cycles=self._current_lapse_v080.duration_cycles,
                lapse_duration_epochs=lapse_duration_epochs,
                amnesty_events_during_lapse=self._amnesty_events_this_lapse,
                lapse_cause=self._current_lapse_v080.cause,
                recovered_policy_id=recovered_policy_id,
                streak_at_recovery=streak,
                authority_epochs_after=None,  # Filled in when authority ends
                authority_end_reason=None,
                is_stutter=None,
            )
            self._recovery_events.append(recovery)

            # Store reference to update when authority span ends
            self._last_recovery_event = recovery
            self._last_recovery_epoch = self._epoch_index

            self._current_lapse_v080 = None

        # Finalize v0.7 compatible lapse event
        if self._current_lapse is not None:
            self._current_lapse.end_cycle = self._cycle
            self._current_lapse.duration_cycles = self._cycle - self._current_lapse.start_cycle
            if self._null_authority_start_epoch is not None:
                self._current_lapse.duration_epochs = self._epoch_index - self._null_authority_start_epoch
            self._lapse_events.append(self._current_lapse)
            self._current_lapse = None

        self._in_null_authority = False
        self._null_authority_start_cycle = None
        self._null_authority_start_epoch = None

        if self._verbose:
            print(f"    [Cycle {self._cycle}] RECOVERY: {recovered_policy_id} "
                  f"(streak={streak})")

    def _attempt_succession_v080(self) -> bool:
        """
        Attempt succession with eligibility filtering (v0.8).

        Per instructions §8.3:
        - Regenerate candidate pool on every succession attempt
        - Use v0.7 generator/pool policy

        Returns:
            True if succession succeeded, False if lapse triggered
        """
        # Generate fresh candidate pool
        candidate = self._generator.propose(self._cycle)
        candidates = [candidate]

        # Track draw for composition verification
        self._count_draw(candidate)

        # Generate additional candidates to form pool
        for _ in range(min(10, len(list(ControlSuccessorType)) + len(list(AttackSuccessorType)))):
            c = self._generator.propose(self._cycle)
            candidates.append(c)
            self._count_draw(c)

        # Filter by eligibility
        eligible_candidates = self._filter_eligible_candidates(candidates)

        if not eligible_candidates:
            # C_ELIG = ∅ → Lapse
            ineligible_policies = list(set(c.policy_id for c in candidates))
            cause = self._classify_lapse_cause(candidates, eligible_candidates)

            if self._in_null_authority:
                # Already in lapse, just continue
                pass
            else:
                # Enter lapse
                self._enter_null_authority_v080(ineligible_policies, cause)
            return False

        # Select from eligible candidates (use first one, semantic-blind)
        selected = eligible_candidates[0]
        selected_streak = self._get_policy_streak(selected.policy_id)

        # Store active policy_id
        self._active_policy_id = selected.policy_id

        # Exit NULL_AUTHORITY if we were in it
        if self._in_null_authority:
            self._exit_null_authority_v080(selected.policy_id, selected_streak)

        # Proceed with standard succession
        self._total_proposals += 1

        # Validate candidate
        is_valid = self._validate_candidate(selected)
        if not is_valid:
            # Rejection - try another eligible candidate
            for alt in eligible_candidates[1:]:
                if self._validate_candidate(alt):
                    selected = alt
                    self._active_policy_id = selected.policy_id
                    is_valid = True
                    break

        if not is_valid:
            # All eligible candidates rejected - enter lapse
            ineligible_policies = list(set(c.policy_id for c in candidates))
            cause = LapseCause.STRUCTURAL  # Validation failure is structural
            self._enter_null_authority_v080(ineligible_policies, cause)
            return False

        # Endorse candidate
        self._endorse_candidate(selected)

        return True

    def run(self) -> ALSRunResultV080:
        """
        Execute a complete ALS-A v0.8 run.

        Key additions over v0.7:
        - CTA at epoch boundaries during lapse
        - Succession attempts only at succession boundaries
        - TTL advances during lapse
        - Recovery tracking and metrics

        Per instructions §8.3:
        - CTA tick at epoch boundaries
        - Succession attempts at succession boundaries (not same as epochs)

        Returns:
            Run result with all metrics and logs
        """
        start_time = current_time_ms()
        run_id = f"als080_{self._seed}_{start_time}"

        if self._verbose:
            print(f"Starting ALS-A v0.8 run: {run_id}")
            print(f"  Max cycles: {self._config.max_cycles}")
            print(f"  Eligibility threshold K: {self._config.eligibility_threshold_k}")
            print(f"  Amnesty interval: {self._config.amnesty_interval} epochs")
            print(f"  Amnesty decay: {self._config.amnesty_decay}")
            print(f"  CTA enabled: {self._config.cta_enabled}")

        # Initial succession
        self._succession_pending = True
        self._attempt_succession_v080()

        # Main loop
        while not self._stopped and self._cycle < self._config.max_cycles:
            self._cycle += 1
            self._sentinel.advance_cycle()

            # Handle NULL_AUTHORITY state
            if self._in_null_authority:
                self._lapse_time_cycles += 1

                # Check for epoch boundary (for CTA and TTL)
                if self._cycle % self._config.renewal_check_interval == 0:
                    self._epoch_index += 1
                    self._lapse_epoch_count += 1

                    # RSA: record lapse epoch (no commitment evaluation, 0 targets)
                    if self._rsa_adversary is not None and self._rsa_telemetry is not None:
                        global_epoch = self._compute_global_epoch()
                        record = self._rsa_adversary.create_lapse_epoch_record(global_epoch)
                        self._rsa_telemetry.record_epoch(record)

                    # TTL clocks advance (commitment evaluation is suspended)
                    # Commitments with expired TTL will be evaluated on recovery

                    # Apply CTA if interval reached
                    if self._lapse_epoch_count % self._config.amnesty_interval == 0:
                        self._apply_cta_amnesty()

                    # Attempt succession at succession boundary
                    # Per instructions: succession boundaries are same as epoch boundaries
                    # for simplicity (renewal_check_interval defines both)
                    self._attempt_succession_v080()

                continue

            # Track authority uptime
            self._authority_uptime_cycles += 1

            # Check if succession is needed
            if self._succession_pending:
                success = self._attempt_succession_v080()
                if not success:
                    continue  # In NULL_AUTHORITY now

            # Execute working mind cycle (v0.8 override with RSA v1.0 policy hook)
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                adjusted_effective = self._current_effective_steps - self._commitment_cost_this_epoch
                if self._epoch_steps_used < adjusted_effective:
                    violation = self._execute_working_mind_cycle_v080()
                    if violation:
                        self._handle_lease_revocation(violation[0], violation[1])
                        continue

            # Check renewal at epoch boundaries
            if self._current_lease and self._current_lease.status == LeaseStatus.ACTIVE:
                if self._cycle % self._config.renewal_check_interval == 0:
                    # Record v1.0 epoch telemetry before evaluation
                    self._record_rsa_v10_epoch_telemetry()
                    # Evaluate commitments before renewal
                    self._evaluate_commitments_at_epoch_end()
                    # Update streak at epoch end
                    self._update_streak_at_epoch_end()
                    # Proceed with renewal
                    self._check_renewal_with_rent()

            # Check lease expiration
            if self._current_lease and self._current_lease.is_expired(self._cycle):
                self._handle_lease_expiration()

            # Check degeneracy
            self._check_degeneracy()

        # Finalize
        if not self._stopped:
            self._stop_reason = ALSStopReason.HORIZON_EXHAUSTED

        # Finalize any pending recovery's authority span (if still active at horizon)
        if self._last_recovery_event is not None and not self._in_null_authority:
            # Compute authority epochs using cycle count
            cycles_since_recovery = self._cycle - self._last_recovery_event.cycle
            authority_epochs = cycles_since_recovery // self._config.renewal_check_interval
            self._last_recovery_event.authority_epochs_after = authority_epochs
            self._last_recovery_event.authority_end_reason = "HORIZON"
            self._last_recovery_event.is_stutter = authority_epochs <= 1
            self._post_recovery_durations.append(authority_epochs)
            self._last_recovery_event = None

        # End any active lapse
        if self._in_null_authority:
            if self._current_lapse_v080:
                self._current_lapse_v080.end_cycle = self._cycle
                self._current_lapse_v080.end_epoch = self._epoch_index
                self._current_lapse_v080.duration_cycles = self._cycle - self._current_lapse_v080.start_cycle
                self._current_lapse_v080.duration_epochs = self._epoch_index - self._current_lapse_v080.start_epoch
                self._current_lapse_v080.amnesty_events_during = self._amnesty_events_this_lapse
                self._current_lapse_v080.recovered = False  # Did not recover before horizon
                self._lapse_events_v080.append(self._current_lapse_v080)

            if self._current_lapse:
                self._current_lapse.end_cycle = self._cycle
                self._current_lapse.duration_cycles = self._cycle - self._current_lapse.start_cycle
                if self._null_authority_start_epoch is not None:
                    self._current_lapse.duration_epochs = self._epoch_index - self._null_authority_start_epoch
                self._lapse_events.append(self._current_lapse)

        # Finalize active tenure
        if self._current_tenure is not None:
            self._end_tenure("HORIZON_EXHAUSTED")

        duration = current_time_ms() - start_time

        # Compute metrics
        ledger_metrics = self._commitment_ledger.get_metrics()
        total_evaluations = ledger_metrics["total_satisfied"] + ledger_metrics["total_failed"]
        satisfaction_rate = 0.0
        if total_evaluations > 0:
            satisfaction_rate = ledger_metrics["total_satisfied"] / total_evaluations

        eligibility_rejection_rate = 0.0
        if self._total_candidates_at_succession > 0:
            eligibility_rejection_rate = self._eligibility_rejections / self._total_candidates_at_succession

        # Lapse metrics
        total_lapse_cycles = sum(e.duration_cycles for e in self._lapse_events_v080)
        total_lapse_epochs = sum(e.duration_epochs for e in self._lapse_events_v080)
        max_lapse = max((e.duration_cycles for e in self._lapse_events_v080), default=0)
        max_recovery_latency = max((e.duration_epochs for e in self._lapse_events_v080 if e.recovered), default=0)

        # Lapse cause counts
        semantic_lapse_count = sum(1 for e in self._lapse_events_v080 if e.cause == LapseCause.SEMANTIC)
        structural_lapse_count = sum(1 for e in self._lapse_events_v080 if e.cause == LapseCause.STRUCTURAL)

        # Recovery metrics
        recovery_count = len(self._recovery_events)
        mean_time_to_recovery = 0.0
        if self._recovery_latencies:
            mean_time_to_recovery = sum(self._recovery_latencies) / len(self._recovery_latencies)

        # Stutter recovery (1 epoch authority after recovery)
        stutter_count = sum(1 for d in self._post_recovery_durations if d <= 1)

        # Hollow recovery (re-lapse within 1 epoch)
        hollow_count = stutter_count  # Same definition for now

        # Authority uptime fraction
        total_time = self._cycle
        authority_uptime_fraction = 0.0
        lapse_fraction = 0.0
        if total_time > 0:
            authority_uptime_fraction = self._authority_uptime_cycles / total_time
            lapse_fraction = self._lapse_time_cycles / total_time

        # Recovery yield: authority epochs after recovery / lapse epochs to achieve recovery
        recovery_yield = 0.0
        if self._recovery_latencies and sum(self._recovery_latencies) > 0:
            total_post_recovery_epochs = sum(self._post_recovery_durations) if self._post_recovery_durations else 0
            total_lapse_epochs_for_recovery = sum(self._recovery_latencies)
            if total_lapse_epochs_for_recovery > 0:
                recovery_yield = total_post_recovery_epochs / total_lapse_epochs_for_recovery

        # Streak distribution
        streak_dist: Dict[int, int] = {}
        for event in self._eligibility_events:
            streak = event.streak_at_decision
            streak_dist[streak] = streak_dist.get(streak, 0) + 1

        # Degeneracy
        is_degenerate = self._stop_reason in (
            ALSStopReason.ENDORSEMENT_DEGENERACY,
            ALSStopReason.SPAM_DEGENERACY,
        )
        degeneracy_type = None
        if self._stop_reason == ALSStopReason.ENDORSEMENT_DEGENERACY:
            degeneracy_type = DegeneracyType.ENDORSEMENT
        elif self._stop_reason == ALSStopReason.SPAM_DEGENERACY:
            degeneracy_type = DegeneracyType.SPAM

        # Mean residence
        mean_residence = 0.0
        if self._residence_durations:
            mean_residence = sum(self._residence_durations) / len(self._residence_durations)

        # E-Class metrics
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

        # Draw ratios
        total_draws = self._attack_draws + self._control_draws
        attack_draw_ratio = self._attack_draws / total_draws if total_draws > 0 else 0.0
        control_draw_ratio = self._control_draws / total_draws if total_draws > 0 else 0.0

        result = ALSRunResultV080(
            run_id=run_id,
            seed=self._seed,
            spec_version="0.8",
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
            total_commitment_cost_charged=ledger_metrics["total_cost_charged"],
            commitment_satisfaction_count=ledger_metrics["total_satisfied"],
            commitment_failure_count=ledger_metrics["total_failed"],
            commitment_expired_count=ledger_metrics["total_expired"],
            commitment_default_count=ledger_metrics["total_defaulted"],
            semantic_debt_mass=ledger_metrics["semantic_debt_mass"],
            commitment_satisfaction_rate=satisfaction_rate,
            # v0.7 eligibility metrics
            eligibility_rejection_count=self._eligibility_rejections,
            eligibility_rejection_rate=eligibility_rejection_rate,
            empty_eligible_set_events=len(self._lapse_events_v080),
            total_lapse_duration_cycles=total_lapse_cycles,
            total_lapse_duration_epochs=total_lapse_epochs,
            max_lapse_duration_cycles=max_lapse,
            ineligible_in_office_cycles=self._ineligible_in_office_cycles,
            sawtooth_count=self._sawtooth_count,
            streak_distribution_at_succession=streak_dist,
            final_streak_by_policy=dict(self._semantic_fail_streak),
            # v0.7 forced turnover
            forced_turnover_events=[e.to_dict() for e in self._forced_turnover_events],
            forced_turnover_count=len(self._forced_turnover_events),
            post_init_successions=self._post_init_successions,
            attack_draws=self._attack_draws,
            control_draws=self._control_draws,
            attack_draw_ratio=attack_draw_ratio,
            control_draw_ratio=control_draw_ratio,
            pool_policy=self._config.candidate_pool_policy.name,
            # v0.8 CTA metrics
            amnesty_event_count=len(self._amnesty_events),
            amnesty_epochs=len(self._amnesty_events),
            aggregate_streak_mass_before_amnesty=self._aggregate_streak_before_amnesty,
            aggregate_streak_mass_after_amnesty=self._aggregate_streak_after_amnesty,
            total_streak_decay_applied=self._total_streak_decay_applied,
            recovery_count=recovery_count,
            time_to_first_recovery=self._time_to_first_recovery,
            mean_time_to_recovery=mean_time_to_recovery,
            stutter_recovery_count=stutter_count,
            authority_uptime_cycles=self._authority_uptime_cycles,
            authority_uptime_fraction=authority_uptime_fraction,
            lapse_fraction=lapse_fraction,
            semantic_lapse_count=semantic_lapse_count,
            structural_lapse_count=structural_lapse_count,
            recovery_yield=recovery_yield,
            max_recovery_latency_epochs=max_recovery_latency,
            hollow_recovery_count=hollow_count,
            # Events
            succession_events=self._succession_events,
            renewal_events=self._renewal_events,
            expiration_events=self._expiration_events,
            revocation_events=self._revocation_events,
            bankruptcy_events=self._bankruptcy_events,
            epoch_rent_records=self._epoch_rent_records,
            tenure_records=self._tenure_records,
            tenure_entropy_samples=self._tenure_entropy_samples,
            commitment_events=[e.to_dict() for e in self._commitment_ledger.get_events()],
            commitment_cost_records=[r.to_dict() for r in self._commitment_ledger.get_cost_records()],
            eligibility_events=[e.to_dict() for e in self._eligibility_events],
            lapse_events=[e.to_dict() for e in self._lapse_events],
            semantic_epoch_records=[r.to_dict() for r in self._semantic_epoch_records],
            # v0.8 CTA events
            amnesty_events=[e.to_dict() for e in self._amnesty_events],
            recovery_events=[e.to_dict() for e in self._recovery_events],
            lapse_events_v080=[e.to_dict() for e in self._lapse_events_v080],
            # RSA telemetry (None if RSA disabled)
            rsa=self._rsa_telemetry.to_dict() if self._rsa_telemetry else None,
            duration_ms=duration,
        )

        if self._verbose:
            print(f"\nALS-A v0.8 run complete:")
            print(f"  S*: {result.s_star}")
            print(f"  Cycles: {result.total_cycles}")
            print(f"  Authority uptime: {result.authority_uptime_fraction:.1%}")
            print(f"  Lapse fraction: {result.lapse_fraction:.1%}")
            print(f"  Amnesty events: {result.amnesty_event_count}")
            print(f"  Recovery count: {result.recovery_count}")
            print(f"  Semantic lapses: {result.semantic_lapse_count}")
            print(f"  Structural lapses: {result.structural_lapse_count}")
            if self._rsa_telemetry:
                summary = self._rsa_telemetry.summarize()
                print(f"  RSA: {summary.total_flips} flips / {summary.total_targets} targets "
                      f"({summary.observed_flip_rate_ppm} PPM observed vs {summary.expected_flip_rate_ppm} PPM expected)")
            print(f"  Stop: {result.stop_reason.name}")

        return result
