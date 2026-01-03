"""
AKI v0.5.2 Expressivity Classes and Rent Enforcement.

Implements:
- ExpressivityClass (E0-E4): Lease-assigned structural tiers
- CapabilityGroup: Externally visible interface primitives
- Rent schedule: Mandatory step deduction per epoch
- E-Class assignment from capability groups

Per spec §6:
- Expressivity is defined purely structurally
- E-Class assigned by harness from granted interface surface
- Rent is charged at epoch start, regardless of actions taken
- Failure to pay rent = LEASE_EXPIRED (bankruptcy)

Per binding decisions:
- Rent schedule: E0=1, E1=ceil(0.10*S), E2=ceil(0.25*S), E3=ceil(0.40*S), E4=ceil(0.60*S)
- Strict monotone enforcement with tie-breaking
- rent <= S-1 for all classes (leave at least 1 step for renewal)
- Renewal attestation consumes successor budget (no kernel subsidy)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, Optional, Set


class ExpressivityClass(Enum):
    """
    Expressivity tiers per spec §6.2.

    E-Class determines the lease rent (mandatory step deduction per epoch).
    Higher E-Class = higher rent = more structural expressivity.
    """
    E0 = 0  # Heartbeat only
    E1 = 1  # Heartbeat + logging
    E2 = 2  # + State mutation
    E3 = 3  # + Fanout/composition
    E4 = 4  # Maximal kernel API surface


class CapabilityGroup(Enum):
    """
    Capability groups that define structural interface surface.

    Per binding decisions §2:
    - E0: HEARTBEAT only
    - E1: HEARTBEAT + LOGGING
    - E2: + STATE_MUTATION
    - E3: + FANOUT_COMPOSITION
    - E4: + FULL_API_SURFACE (all groups)
    """
    HEARTBEAT = auto()          # Basic liveness (WAIT, PING)
    LOGGING = auto()            # Observation logging (LOG, REPORT)
    STATE_MUTATION = auto()     # Bounded key/value state ops (SET, GET, DELETE)
    FANOUT_COMPOSITION = auto()  # Batch ops, multi-call (BATCH, COMPOSE, INVOKE)
    FULL_API_SURFACE = auto()    # All remaining primitives (MOVE_*, HARVEST, SPEND, etc.)


# Default action type mappings to capability groups
DEFAULT_CAPABILITY_MAPPING: Dict[str, CapabilityGroup] = {
    # HEARTBEAT group
    "WAIT": CapabilityGroup.HEARTBEAT,
    "PING": CapabilityGroup.HEARTBEAT,
    "HEARTBEAT": CapabilityGroup.HEARTBEAT,

    # LOGGING group
    "LOG": CapabilityGroup.LOGGING,
    "REPORT": CapabilityGroup.LOGGING,
    "DEBUG": CapabilityGroup.LOGGING,

    # STATE_MUTATION group
    "SET": CapabilityGroup.STATE_MUTATION,
    "GET": CapabilityGroup.STATE_MUTATION,
    "DELETE": CapabilityGroup.STATE_MUTATION,
    "UPDATE": CapabilityGroup.STATE_MUTATION,
    "STORE": CapabilityGroup.STATE_MUTATION,
    "LOAD": CapabilityGroup.STATE_MUTATION,

    # FANOUT_COMPOSITION group
    "BATCH": CapabilityGroup.FANOUT_COMPOSITION,
    "COMPOSE": CapabilityGroup.FANOUT_COMPOSITION,
    "INVOKE": CapabilityGroup.FANOUT_COMPOSITION,
    "PARALLEL": CapabilityGroup.FANOUT_COMPOSITION,
    "SEQUENCE": CapabilityGroup.FANOUT_COMPOSITION,

    # FULL_API_SURFACE group (default for unmapped actions)
    "MOVE_LEFT": CapabilityGroup.FULL_API_SURFACE,
    "MOVE_RIGHT": CapabilityGroup.FULL_API_SURFACE,
    "MOVE_UP": CapabilityGroup.FULL_API_SURFACE,
    "MOVE_DOWN": CapabilityGroup.FULL_API_SURFACE,
    "HARVEST": CapabilityGroup.FULL_API_SURFACE,
    "SPEND": CapabilityGroup.FULL_API_SURFACE,
    "BUILD": CapabilityGroup.FULL_API_SURFACE,
    "DESTROY": CapabilityGroup.FULL_API_SURFACE,
}


def get_capability_group(action_type: str) -> CapabilityGroup:
    """
    Get the capability group for an action type.

    Unmapped actions default to FULL_API_SURFACE.
    """
    return DEFAULT_CAPABILITY_MAPPING.get(action_type, CapabilityGroup.FULL_API_SURFACE)


def get_capability_groups_for_actions(action_types: FrozenSet[str]) -> Set[CapabilityGroup]:
    """
    Get all capability groups required by a set of action types.
    """
    return {get_capability_group(action_type) for action_type in action_types}


def assign_e_class_from_capabilities(capability_groups: Set[CapabilityGroup]) -> ExpressivityClass:
    """
    Assign E-Class from capability groups.

    Per binding decisions §2:
    - E0: Only HEARTBEAT
    - E1: HEARTBEAT + LOGGING (no others)
    - E2: STATE_MUTATION present (but not FANOUT or FULL)
    - E3: FANOUT_COMPOSITION present (but not FULL)
    - E4: FULL_API_SURFACE present

    This is a monotonic assignment: higher capability groups imply higher E-Class.
    """
    if CapabilityGroup.FULL_API_SURFACE in capability_groups:
        return ExpressivityClass.E4

    if CapabilityGroup.FANOUT_COMPOSITION in capability_groups:
        return ExpressivityClass.E3

    if CapabilityGroup.STATE_MUTATION in capability_groups:
        return ExpressivityClass.E2

    if CapabilityGroup.LOGGING in capability_groups:
        return ExpressivityClass.E1

    # Only HEARTBEAT or empty
    return ExpressivityClass.E0


def assign_e_class_from_action_types(action_types: FrozenSet[str]) -> ExpressivityClass:
    """
    Assign E-Class directly from action types.

    Convenience function that combines capability group extraction
    and E-Class assignment.
    """
    capability_groups = get_capability_groups_for_actions(action_types)
    return assign_e_class_from_capabilities(capability_groups)


@dataclass(frozen=True)
class RentSchedule:
    """
    Rent schedule for expressivity classes.

    Per binding decisions §1:
    - rent(E0) = 1
    - rent(E1) = ceil(0.10 * S)
    - rent(E2) = ceil(0.25 * S)
    - rent(E3) = ceil(0.40 * S)
    - rent(E4) = ceil(0.60 * S)

    Where S = steps_cap_epoch.

    Constraints enforced:
    - Strict monotone: E0 < E1 < E2 < E3 < E4 (with tie-breaking)
    - rent <= S - 1 for all classes (leave at least 1 step for renewal)
    """
    steps_cap_epoch: int

    # Rent fractions (can be overridden for experiments)
    e0_rent: int = 1
    e1_fraction: float = 0.10
    e2_fraction: float = 0.25
    e3_fraction: float = 0.40
    e4_fraction: float = 0.60

    def __post_init__(self) -> None:
        """Validate schedule configuration."""
        if self.steps_cap_epoch < 5:
            raise ValueError(f"steps_cap_epoch must be >= 5, got {self.steps_cap_epoch}")

        # Validate fractions are monotone
        if not (0 < self.e1_fraction < self.e2_fraction < self.e3_fraction < self.e4_fraction < 1):
            raise ValueError("Rent fractions must be strictly monotone: e1 < e2 < e3 < e4 < 1")

    def compute_rent(self, e_class: ExpressivityClass) -> int:
        """
        Compute rent for an E-Class.

        Returns the rent in steps, with monotone enforcement and cap constraint.
        """
        S = self.steps_cap_epoch

        # Compute raw rents
        raw_rents = {
            ExpressivityClass.E0: self.e0_rent,
            ExpressivityClass.E1: math.ceil(self.e1_fraction * S),
            ExpressivityClass.E2: math.ceil(self.e2_fraction * S),
            ExpressivityClass.E3: math.ceil(self.e3_fraction * S),
            ExpressivityClass.E4: math.ceil(self.e4_fraction * S),
        }

        # Enforce strict monotone by bumping ties
        rents = self._enforce_monotone(raw_rents)

        # Enforce cap constraint: rent <= S - 1
        max_rent = S - 1
        for e in ExpressivityClass:
            if rents[e] > max_rent:
                rents[e] = max_rent

        return rents[e_class]

    def _enforce_monotone(self, raw_rents: Dict[ExpressivityClass, int]) -> Dict[ExpressivityClass, int]:
        """
        Enforce strict monotone constraint by bumping higher tiers.

        If E(k) <= E(k-1) after rounding, bump E(k) to E(k-1) + 1.
        """
        rents = dict(raw_rents)

        # Process in order: E0 -> E1 -> E2 -> E3 -> E4
        prev_rent = rents[ExpressivityClass.E0]
        for e_class in [ExpressivityClass.E1, ExpressivityClass.E2,
                        ExpressivityClass.E3, ExpressivityClass.E4]:
            if rents[e_class] <= prev_rent:
                rents[e_class] = prev_rent + 1
            prev_rent = rents[e_class]

        return rents

    def compute_effective_steps(self, e_class: ExpressivityClass) -> int:
        """
        Compute effective steps available after rent deduction.

        effective_steps = max(0, steps_cap_epoch - rent)
        """
        rent = self.compute_rent(e_class)
        return max(0, self.steps_cap_epoch - rent)

    def can_afford_renewal(self, e_class: ExpressivityClass) -> bool:
        """
        Check if an E-Class can afford at least 1 step for renewal.

        Per binding decisions: renewal requires >= 1 effective step.
        """
        return self.compute_effective_steps(e_class) >= 1

    def get_all_rents(self) -> Dict[ExpressivityClass, int]:
        """Get rents for all E-Classes."""
        return {e: self.compute_rent(e) for e in ExpressivityClass}

    def get_all_effective_steps(self) -> Dict[ExpressivityClass, int]:
        """Get effective steps for all E-Classes."""
        return {e: self.compute_effective_steps(e) for e in ExpressivityClass}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "steps_cap_epoch": self.steps_cap_epoch,
            "rents": {e.name: self.compute_rent(e) for e in ExpressivityClass},
            "effective_steps": {e.name: self.compute_effective_steps(e) for e in ExpressivityClass},
        }


def create_default_rent_schedule(steps_cap_epoch: int) -> RentSchedule:
    """
    Create the default rent schedule per binding decisions.

    Default fractions:
    - E0 = 1 (fixed)
    - E1 = 10% of S
    - E2 = 25% of S
    - E3 = 40% of S
    - E4 = 60% of S
    """
    return RentSchedule(steps_cap_epoch=steps_cap_epoch)


@dataclass
class ExpressivityTelemetry:
    """
    Telemetry for expressivity and rent tracking.

    Logged per epoch and aggregated per run.
    """
    # Per-epoch tracking
    e_class: ExpressivityClass = ExpressivityClass.E0
    rent_steps_charged: int = 0
    effective_steps_available: int = 0
    steps_used: int = 0
    actions_used: int = 0

    # Bankruptcy tracking
    bankruptcy_occurred: bool = False
    bankruptcy_cycle: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "e_class": self.e_class.name,
            "rent_steps_charged": self.rent_steps_charged,
            "effective_steps_available": self.effective_steps_available,
            "steps_used": self.steps_used,
            "actions_used": self.actions_used,
            "bankruptcy_occurred": self.bankruptcy_occurred,
            "bankruptcy_cycle": self.bankruptcy_cycle,
        }


@dataclass
class EClassAssignmentError(Exception):
    """Raised when E-Class assignment fails due to misconfiguration."""
    action_types: FrozenSet[str]
    expected_e_class: Optional[ExpressivityClass]
    actual_e_class: ExpressivityClass
    message: str

    def __str__(self) -> str:
        return (
            f"E-Class assignment error: {self.message}. "
            f"Actions: {sorted(self.action_types)}, "
            f"Expected: {self.expected_e_class}, Actual: {self.actual_e_class}"
        )


def validate_e_class_assignment(
    action_types: FrozenSet[str],
    assigned_e_class: ExpressivityClass,
) -> None:
    """
    Validate that an E-Class assignment is consistent with action types.

    Raises EClassAssignmentError if:
    - E0 is assigned but action types require higher capability
    - E-Class is lower than what action types require

    This is the action-count backstop per binding decisions §2.
    """
    computed_e_class = assign_e_class_from_action_types(action_types)

    # Assigned E-Class must be >= computed E-Class
    if assigned_e_class.value < computed_e_class.value:
        raise EClassAssignmentError(
            action_types=action_types,
            expected_e_class=computed_e_class,
            actual_e_class=assigned_e_class,
            message=f"Assigned E-Class {assigned_e_class.name} is too low for granted capabilities",
        )

    # E0 cannot have more than 1 action type (heartbeat only)
    if assigned_e_class == ExpressivityClass.E0 and len(action_types) > 1:
        # Check if all actions are heartbeat
        groups = get_capability_groups_for_actions(action_types)
        if groups != {CapabilityGroup.HEARTBEAT}:
            raise EClassAssignmentError(
                action_types=action_types,
                expected_e_class=computed_e_class,
                actual_e_class=assigned_e_class,
                message="E0 requires HEARTBEAT-only actions",
            )


# =============================================================================
# Hollow Tenure Classification (Post-hoc Analysis for Run F)
# =============================================================================

@dataclass
class HollowTenure:
    """
    Record of a hollow succession tenure.

    Per Run F binding decisions, a tenure is "hollow" if:
    1. E-Class >= E2
    2. renewal_success = True for at least 2 consecutive renewals
    3. actions_used <= 0.10 * actions_cap_epoch for >= 5 consecutive epochs
    4. No revocations occurred during the tenure
    """
    mind_id: str
    start_cycle: int
    end_cycle: int
    e_class: str
    epochs_count: int
    low_action_epochs_streak_max: int
    renewals_count: int
    successor_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mind_id": self.mind_id,
            "start_cycle": self.start_cycle,
            "end_cycle": self.end_cycle,
            "e_class": self.e_class,
            "epochs_count": self.epochs_count,
            "low_action_epochs_streak_max": self.low_action_epochs_streak_max,
            "renewals_count": self.renewals_count,
            "successor_type": self.successor_type,
        }


def classify_hollow_tenures(
    epoch_rent_records: List[Any],
    succession_events: List[Any],
    renewal_events: List[Any],
    revocation_events: List[Any],
    actions_cap_epoch: int,
    low_action_threshold: float = 0.10,
    min_consecutive_renewals: int = 2,
    min_low_action_streak: int = 5,
) -> List[HollowTenure]:
    """
    Classify hollow tenures from telemetry data (post-hoc analysis).

    Per Run F binding decisions:
    - A tenure is "hollow" if it meets all structural criteria
    - This is a classification, not an enforcement mechanism

    Args:
        epoch_rent_records: List of EpochRentRecord from run
        succession_events: List of SuccessionEvent from run
        renewal_events: List of RenewalEvent from run
        revocation_events: List of RevocationEvent from run
        actions_cap_epoch: Actions cap for computing threshold
        low_action_threshold: Fraction of cap below which actions are "low" (default 0.10)
        min_consecutive_renewals: Minimum renewals for hollow (default 2)
        min_low_action_streak: Minimum consecutive low-action epochs (default 5)

    Returns:
        List of HollowTenure records
    """
    hollow_tenures = []
    action_threshold = int(low_action_threshold * actions_cap_epoch)

    # Build lease_id -> mind_id mapping from succession events
    lease_to_mind: Dict[str, str] = {}
    for ev in succession_events:
        if hasattr(ev, 'lease_id') and hasattr(ev, 'mind_id'):
            lease_to_mind[ev.lease_id] = ev.mind_id

    # Build revoked mind_ids set for quick lookup
    revoked_minds = set()
    for ev in revocation_events:
        if hasattr(ev, 'successor_mind_id'):
            revoked_minds.add(ev.successor_mind_id)
        elif hasattr(ev, 'mind_id'):
            revoked_minds.add(ev.mind_id)
        elif hasattr(ev, 'lease_id'):
            mind_id = lease_to_mind.get(ev.lease_id)
            if mind_id:
                revoked_minds.add(mind_id)

    # Group epochs and renewals by mind_id
    epochs_by_mind: Dict[str, List[Any]] = {}
    for record in epoch_rent_records:
        mind_id = record.mind_id
        if mind_id not in epochs_by_mind:
            epochs_by_mind[mind_id] = []
        epochs_by_mind[mind_id].append(record)

    renewals_by_mind: Dict[str, int] = {}
    for ev in renewal_events:
        # RenewalEvent has lease_id, not mind_id - use mapping
        if hasattr(ev, 'mind_id'):
            mind_id = ev.mind_id
        elif hasattr(ev, 'lease_id'):
            mind_id = lease_to_mind.get(ev.lease_id)
            if not mind_id:
                continue
        else:
            continue
        renewals_by_mind[mind_id] = renewals_by_mind.get(mind_id, 0) + 1

    # Extract succession info for start/end cycles and successor type
    succession_info: Dict[str, Dict[str, Any]] = {}
    for ev in succession_events:
        mind_id = ev.mind_id if hasattr(ev, 'mind_id') else getattr(ev, 'successor_mind_id', None)
        if mind_id:
            succession_info[mind_id] = {
                "start_cycle": ev.cycle,
                "successor_type": getattr(ev, 'source_type', 'unknown'),
            }

    # Analyze each mind's tenure
    for mind_id, epochs in epochs_by_mind.items():
        # Skip if revoked
        if mind_id in revoked_minds:
            continue

        # Get E-Class from first epoch
        if not epochs:
            continue
        e_class = epochs[0].e_class

        # Criterion 1: E-Class >= E2
        if e_class not in ("E2", "E3", "E4"):
            continue

        # Criterion 2: At least min_consecutive_renewals
        renewals_count = renewals_by_mind.get(mind_id, 0)
        if renewals_count < min_consecutive_renewals:
            continue

        # Criterion 3: Find max streak of low-action epochs
        epochs_sorted = sorted(epochs, key=lambda x: x.epoch_index)
        max_streak = 0
        current_streak = 0

        for epoch in epochs_sorted:
            if epoch.actions_used <= action_threshold:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        if max_streak < min_low_action_streak:
            continue

        # All criteria met - this is a hollow tenure
        info = succession_info.get(mind_id, {})
        start_cycle = info.get("start_cycle", epochs_sorted[0].cycle_start)
        end_cycle = epochs_sorted[-1].cycle_start  # Approximate

        hollow_tenures.append(HollowTenure(
            mind_id=mind_id,
            start_cycle=start_cycle,
            end_cycle=end_cycle,
            e_class=e_class,
            epochs_count=len(epochs),
            low_action_epochs_streak_max=max_streak,
            renewals_count=renewals_count,
            successor_type=info.get("successor_type", "unknown"),
        ))

    return hollow_tenures
