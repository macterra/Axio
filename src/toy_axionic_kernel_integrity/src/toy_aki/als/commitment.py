"""
AKI v0.6 Commitment Ledger and Semantic Obligation System.

Implements:
- Commitment: Persistent semantic obligation with lifecycle management
- CommitmentLedger: Kernel-owned ledger persisting across epochs/successions
- CommitmentSpec: Harness-resident commitment specification
- GENESIS_SET_0: Canonical initial commitment set

Per spec §6:
- Commitments persist across epochs, renewals, and successions
- Status transitions: ACTIVE → SATISFIED/FAILED/EXPIRED
- Cost is charged per epoch while ACTIVE
- Semantic failure does NOT cause lease revocation
- Verifiers query ACV traces only (no internal state)

Per binding decisions:
- α = 0.25 (commit_cap = floor(0.25 * steps_cap_epoch))
- MAX_COMMIT_TTL = 10 epochs
- Evaluation at epoch end only
- Always-on with per-window evaluation for genesis commitments
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple


class CommitmentStatus(Enum):
    """Commitment lifecycle states per spec §6.1."""
    ACTIVE = auto()     # Obligation in force, cost being charged
    SATISFIED = auto()  # Verifier returned PASS within window
    FAILED = auto()     # Verifier returned FAIL within window
    EXPIRED = auto()    # Window lapsed without PASS or FAIL


@dataclass(frozen=True)
class CommitmentSpec:
    """
    Harness-resident commitment specification.

    Defines what a commitment means and how to verify it.
    Successors cannot create or modify specs.
    """
    spec_id: str
    description: str
    verifier_id: str
    default_window: int  # epochs
    default_cost: int    # steps/epoch


# Frozen parameter values per binding decisions
MAX_COMMIT_TTL: int = 10  # epochs
COMMIT_CAP_ALPHA: float = 0.25  # commit_cap = floor(α * steps_cap_epoch)


@dataclass
class Commitment:
    """
    A single semantic commitment instance.

    Per spec §6.1:
    - cid: unique commitment identifier
    - spec_id: reference to harness-resident CommitmentSpec
    - verifier_id: reference to kernel-approved verifier
    - window: temporal resolution window (epochs)
    - cost: mandatory per-epoch maintenance cost (steps)
    - status: current lifecycle state
    """
    cid: str
    spec_id: str
    verifier_id: str
    window: int  # epochs
    cost: int    # steps/epoch while ACTIVE
    status: CommitmentStatus = CommitmentStatus.ACTIVE

    # Tracking fields
    created_epoch: int = 0
    window_start_epoch: int = 0  # For rolling window evaluation
    last_evaluation_epoch: int = -1
    satisfaction_count: int = 0  # Times satisfied (for always-on commitments)
    failure_count: int = 0       # Times failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cid": self.cid,
            "spec_id": self.spec_id,
            "verifier_id": self.verifier_id,
            "window": self.window,
            "cost": self.cost,
            "status": self.status.name,
            "created_epoch": self.created_epoch,
            "window_start_epoch": self.window_start_epoch,
            "last_evaluation_epoch": self.last_evaluation_epoch,
            "satisfaction_count": self.satisfaction_count,
            "failure_count": self.failure_count,
        }


# =============================================================================
# GENESIS_SET_0: Canonical Initial Commitment Set
# =============================================================================

# C0 — Presence (E1-compatible)
SPEC_CMT_PRESENCE_LOG = CommitmentSpec(
    spec_id="CMT_PRESENCE_LOG",
    description="At least 1 LOG action occurs within each epoch",
    verifier_id="VRF_EPOCH_ACTION_COUNT",
    default_window=1,
    default_cost=2,
)

# C1 — Continuity (E2-compatible)
SPEC_CMT_STATE_ECHO = CommitmentSpec(
    spec_id="CMT_STATE_ECHO",
    description="Perform STATE_SET then STATE_GET with matching value within window",
    verifier_id="VRF_ORDERED_ACTION_PATTERN",
    default_window=2,
    default_cost=4,
)

# C2 — Composition (E3-compatible)
SPEC_CMT_COMPOSED_OP = CommitmentSpec(
    spec_id="CMT_COMPOSED_OP",
    description="Execute SEQUENCE or BATCH with length >= 2 within window",
    verifier_id="VRF_ACTION_HAS_PAYLOAD_SHAPE",
    default_window=3,
    default_cost=6,
)

# Registry of harness-approved specs
COMMITMENT_SPECS: Dict[str, CommitmentSpec] = {
    "CMT_PRESENCE_LOG": SPEC_CMT_PRESENCE_LOG,
    "CMT_STATE_ECHO": SPEC_CMT_STATE_ECHO,
    "CMT_COMPOSED_OP": SPEC_CMT_COMPOSED_OP,
}


def create_genesis_set_0(start_epoch: int = 0) -> List[Commitment]:
    """
    Create GENESIS_SET_0: the canonical initial commitment set.

    Returns three commitments (C0, C1, C2) that exercise different
    structural capabilities and create real tradeoffs.

    Args:
        start_epoch: Epoch at which commitments become active

    Returns:
        List of three Commitment objects
    """
    return [
        Commitment(
            cid="C0",
            spec_id="CMT_PRESENCE_LOG",
            verifier_id="VRF_EPOCH_ACTION_COUNT",
            window=1,
            cost=2,
            status=CommitmentStatus.ACTIVE,
            created_epoch=start_epoch,
            window_start_epoch=start_epoch,
        ),
        Commitment(
            cid="C1",
            spec_id="CMT_STATE_ECHO",
            verifier_id="VRF_ORDERED_ACTION_PATTERN",
            window=2,
            cost=4,
            status=CommitmentStatus.ACTIVE,
            created_epoch=start_epoch,
            window_start_epoch=start_epoch,
        ),
        Commitment(
            cid="C2",
            spec_id="CMT_COMPOSED_OP",
            verifier_id="VRF_ACTION_HAS_PAYLOAD_SHAPE",
            window=3,
            cost=6,
            status=CommitmentStatus.ACTIVE,
            created_epoch=start_epoch,
            window_start_epoch=start_epoch,
        ),
    ]


# =============================================================================
# Commitment Lifecycle Events
# =============================================================================

@dataclass
class CommitmentEvent:
    """Record of a commitment lifecycle event."""
    cycle: int
    epoch: int
    cid: str
    event_type: str  # "created", "satisfied", "failed", "expired", "defaulted"
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "epoch": self.epoch,
            "cid": self.cid,
            "event_type": self.event_type,
            "detail": self.detail,
        }


@dataclass
class CommitmentCostRecord:
    """Record of commitment cost charged per epoch."""
    epoch: int
    cycle: int
    total_cost: int
    commitments_charged: int
    remaining_budget_after: int
    defaulted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "cycle": self.cycle,
            "total_cost": self.total_cost,
            "commitments_charged": self.commitments_charged,
            "remaining_budget_after": self.remaining_budget_after,
            "defaulted": self.defaulted,
        }


# =============================================================================
# Commitment Ledger
# =============================================================================

class CommitmentLedger:
    """
    Kernel-owned ledger of semantic commitments.

    Per spec §6:
    - Persistent across epochs, renewals, and successions
    - NOT part of the lease or successor state
    - Constitutional, not behavioral

    Key operations:
    - seed(): Initialize with genesis commitments
    - charge_costs(): Deduct commitment costs at epoch start
    - evaluate_all(): Evaluate commitments at epoch end
    - get_active_cost(): Query current per-epoch commitment cost
    """

    def __init__(self, steps_cap_epoch: int):
        """
        Initialize empty ledger.

        Args:
            steps_cap_epoch: Step budget per epoch (for commit_cap calculation)
        """
        self._steps_cap_epoch = steps_cap_epoch
        self._commit_cap = int(math.floor(COMMIT_CAP_ALPHA * steps_cap_epoch))
        self._commitments: Dict[str, Commitment] = {}
        self._events: List[CommitmentEvent] = []
        self._cost_records: List[CommitmentCostRecord] = []
        self._current_epoch = 0
        self._seeded = False

        # Metrics
        self._total_satisfied = 0
        self._total_failed = 0
        self._total_expired = 0
        self._total_defaulted = 0
        self._total_cost_charged = 0

    @property
    def commit_cap(self) -> int:
        """Maximum per-epoch commitment cost allowed."""
        return self._commit_cap

    @property
    def is_seeded(self) -> bool:
        """Whether genesis commitments have been loaded."""
        return self._seeded

    def seed(self, commitments: List[Commitment]) -> None:
        """
        Seed the ledger with genesis commitments.

        Per spec §6.0:
        - Must be called before any successor logic runs
        - Genesis commitments cannot be declined or removed

        Args:
            commitments: Initial commitment set (e.g., GENESIS_SET_0)

        Raises:
            ValueError: If ledger already seeded or commitments empty
        """
        if self._seeded:
            raise ValueError("Ledger already seeded")
        if not commitments:
            raise ValueError("Genesis commitment set cannot be empty")

        for c in commitments:
            if c.cid in self._commitments:
                raise ValueError(f"Duplicate commitment ID: {c.cid}")
            self._commitments[c.cid] = c
            self._events.append(CommitmentEvent(
                cycle=0,
                epoch=0,
                cid=c.cid,
                event_type="created",
                detail=f"Genesis: {c.spec_id}",
            ))

        self._seeded = True

    def get_active_cost(self) -> int:
        """
        Get total per-epoch cost of all ACTIVE commitments.

        Returns:
            Sum of cost fields for ACTIVE commitments
        """
        return sum(
            c.cost for c in self._commitments.values()
            if c.status == CommitmentStatus.ACTIVE
        )

    def get_active_commitments(self) -> List[Commitment]:
        """Get all ACTIVE commitments."""
        return [c for c in self._commitments.values() if c.status == CommitmentStatus.ACTIVE]

    def get_commitment(self, cid: str) -> Optional[Commitment]:
        """Get commitment by ID."""
        return self._commitments.get(cid)

    def charge_costs(
        self,
        epoch: int,
        cycle: int,
        available_budget: int,
    ) -> Tuple[int, bool]:
        """
        Charge commitment maintenance costs at epoch start.

        Per spec §6.4:
        - Charged AFTER rent deduction
        - If insufficient budget, all ACTIVE commitments fail (default)
        - Lease continues if rent was paid

        Args:
            epoch: Current epoch index
            cycle: Current cycle
            available_budget: Steps remaining after rent deduction

        Returns:
            Tuple of (cost_charged, defaulted)
            - cost_charged: Steps deducted for commitments
            - defaulted: True if insufficient budget caused default
        """
        self._current_epoch = epoch
        total_cost = self.get_active_cost()

        if total_cost > available_budget:
            # Default: cannot pay commitment costs
            # All ACTIVE commitments fail
            for c in self._commitments.values():
                if c.status == CommitmentStatus.ACTIVE:
                    c.status = CommitmentStatus.FAILED
                    c.failure_count += 1
                    self._events.append(CommitmentEvent(
                        cycle=cycle,
                        epoch=epoch,
                        cid=c.cid,
                        event_type="defaulted",
                        detail=f"Cost default: needed {total_cost}, had {available_budget}",
                    ))
                    self._total_defaulted += 1
                    self._total_failed += 1

            self._cost_records.append(CommitmentCostRecord(
                epoch=epoch,
                cycle=cycle,
                total_cost=0,  # Nothing charged
                commitments_charged=0,
                remaining_budget_after=available_budget,
                defaulted=True,
            ))
            return 0, True

        # Normal case: charge all costs
        active_count = len(self.get_active_commitments())
        self._total_cost_charged += total_cost

        self._cost_records.append(CommitmentCostRecord(
            epoch=epoch,
            cycle=cycle,
            total_cost=total_cost,
            commitments_charged=active_count,
            remaining_budget_after=available_budget - total_cost,
            defaulted=False,
        ))

        return total_cost, False

    def evaluate_commitment(
        self,
        cid: str,
        epoch: int,
        cycle: int,
        verifier_result: bool,
    ) -> CommitmentStatus:
        """
        Evaluate a single commitment based on verifier result.

        Per spec §6.7:
        - Evaluation occurs at epoch end
        - Verifier returns PASS (True) or FAIL (False)

        For always-on commitments:
        - PASS resets window and increments satisfaction count
        - FAIL transitions to FAILED status

        Args:
            cid: Commitment ID
            epoch: Current epoch
            cycle: Current cycle
            verifier_result: True for PASS, False for FAIL

        Returns:
            New commitment status
        """
        c = self._commitments.get(cid)
        if c is None:
            raise ValueError(f"Unknown commitment: {cid}")

        if c.status != CommitmentStatus.ACTIVE:
            return c.status

        c.last_evaluation_epoch = epoch

        if verifier_result:
            # PASS: Commitment satisfied for this window
            c.satisfaction_count += 1
            c.window_start_epoch = epoch + 1  # Reset window for always-on
            self._events.append(CommitmentEvent(
                cycle=cycle,
                epoch=epoch,
                cid=cid,
                event_type="satisfied",
                detail=f"Satisfaction #{c.satisfaction_count}",
            ))
            self._total_satisfied += 1
            # For always-on, stays ACTIVE (window resets)
            # Status remains ACTIVE
        else:
            # FAIL: Check if within window or expired
            epochs_elapsed = epoch - c.window_start_epoch + 1
            if epochs_elapsed >= c.window:
                # Window exhausted without pass
                c.status = CommitmentStatus.FAILED
                c.failure_count += 1
                self._events.append(CommitmentEvent(
                    cycle=cycle,
                    epoch=epoch,
                    cid=cid,
                    event_type="failed",
                    detail=f"Window expired after {epochs_elapsed} epochs",
                ))
                self._total_failed += 1
            # Else: still within window, stays ACTIVE

        return c.status

    def check_ttl_expirations(self, epoch: int, cycle: int) -> int:
        """
        Check for commitments exceeding MAX_COMMIT_TTL.

        Per spec §6.2:
        - No commitment may exceed MAX_COMMIT_TTL epochs
        - Upon expiration, commitment ceases to incur cost

        Args:
            epoch: Current epoch
            cycle: Current cycle

        Returns:
            Number of commitments expired due to TTL
        """
        expired_count = 0
        for c in self._commitments.values():
            if c.status != CommitmentStatus.ACTIVE:
                continue

            age_epochs = epoch - c.created_epoch
            if age_epochs >= MAX_COMMIT_TTL:
                c.status = CommitmentStatus.EXPIRED
                self._events.append(CommitmentEvent(
                    cycle=cycle,
                    epoch=epoch,
                    cid=c.cid,
                    event_type="expired",
                    detail=f"TTL exceeded: {age_epochs} >= {MAX_COMMIT_TTL} epochs",
                ))
                self._total_expired += 1
                expired_count += 1

        return expired_count

    def can_add_commitment(self, spec_id: str) -> Tuple[bool, str]:
        """
        Check if a new commitment can be added without exceeding commit_cap.

        Per spec §6.3:
        - Reject if total_commit_cost_next_epoch > commit_cap

        Args:
            spec_id: Spec to add

        Returns:
            Tuple of (allowed, reason)
        """
        spec = COMMITMENT_SPECS.get(spec_id)
        if spec is None:
            return False, f"Unknown spec: {spec_id}"

        current_cost = self.get_active_cost()
        new_cost = current_cost + spec.default_cost

        if new_cost > self._commit_cap:
            return False, f"Would exceed commit_cap: {new_cost} > {self._commit_cap}"

        return True, "OK"

    def add_commitment(
        self,
        spec_id: str,
        epoch: int,
        cycle: int,
    ) -> Optional[Commitment]:
        """
        Add a new commitment if allowed.

        Args:
            spec_id: Spec to instantiate
            epoch: Current epoch
            cycle: Current cycle

        Returns:
            New Commitment if added, None if rejected
        """
        allowed, reason = self.can_add_commitment(spec_id)
        if not allowed:
            return None

        spec = COMMITMENT_SPECS[spec_id]
        cid = f"{spec_id}_{epoch}_{len(self._commitments)}"

        c = Commitment(
            cid=cid,
            spec_id=spec_id,
            verifier_id=spec.verifier_id,
            window=spec.default_window,
            cost=spec.default_cost,
            status=CommitmentStatus.ACTIVE,
            created_epoch=epoch,
            window_start_epoch=epoch,
        )

        self._commitments[cid] = c
        self._events.append(CommitmentEvent(
            cycle=cycle,
            epoch=epoch,
            cid=cid,
            event_type="created",
            detail=f"Successor-requested: {spec_id}",
        ))

        return c

    def get_metrics(self) -> Dict[str, Any]:
        """Get ledger metrics for reporting."""
        active = [c for c in self._commitments.values() if c.status == CommitmentStatus.ACTIVE]
        failed = [c for c in self._commitments.values() if c.status == CommitmentStatus.FAILED]

        return {
            "total_commitments": len(self._commitments),
            "active_count": len(active),
            "active_cost": self.get_active_cost(),
            "commit_cap": self._commit_cap,
            "total_satisfied": self._total_satisfied,
            "total_failed": self._total_failed,
            "total_expired": self._total_expired,
            "total_defaulted": self._total_defaulted,
            "total_cost_charged": self._total_cost_charged,
            "semantic_debt_mass": len(active) + len(failed),  # ACTIVE + FAILED
        }

    def get_events(self) -> List[CommitmentEvent]:
        """Get all commitment lifecycle events."""
        return list(self._events)

    def get_cost_records(self) -> List[CommitmentCostRecord]:
        """Get all cost charging records."""
        return list(self._cost_records)

    def reset_for_new_window(self, epoch: int) -> None:
        """
        Reset always-on commitments for a new evaluation window.

        Called at epoch end after evaluation. For commitments that
        were satisfied, their window has already been reset in
        evaluate_commitment(). This handles the case where we need
        to re-activate failed commitments for the next window.

        For GENESIS_SET_0 always-on semantics:
        - Commitments that FAILED stay FAILED (terminal for that instance)
        - But genesis commitments are "always-on" so we might want to
          track per-window stats without terminal failure

        For now: FAILED commitments stay FAILED (conservative).
        """
        # Currently no-op: FAILED stays FAILED per conservative interpretation
        # If we want "always-on with per-window stats", we'd reset here
        pass
