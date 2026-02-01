"""
MPA-VIII-1 Kernel Core

Minimal Plural Authority kernel per MPA Spec v0.1.
Implements admissibility evaluation, conflict detection, deadlock handling.

Key constraints:
- No action execution (ACTION_EXECUTED never emitted)
- No transformations permitted
- No epoch advancement
- Conflict registration on first contested action
- Deadlock entry when no resolution is possible
"""

from dataclasses import dataclass
from typing import Optional, Union
from copy import deepcopy

from structures import (
    AuthorityRecord,
    AuthorityState,
    AuthorityStatus,
    ConflictRecord,
    ConflictStatus,
    OutputType,
    RefusalReason,
    DeadlockType,
    FailureCode,
    KernelOutput,
    GasAccounting,
    AuthorityInjectionEvent,
    ActionRequestEvent,
    ScopeElement,
)
from canonical import compute_state_id, compute_conflict_id


# Gas costs
GAS_HASH = 50
GAS_COMPARE = 1
GAS_SET_MEM = 5
GAS_SCAN_AR = 10
GAS_UPDATE = 20
GAS_LOG = 10

# Gas budgets (unchanged from AKR-0 per Q9)
GAS_ACTION_EVAL = 50_000
GAS_TRANSFORM = 100_000


@dataclass
class KernelResult:
    """Result of processing an event."""
    output: KernelOutput
    state: AuthorityState
    failure: Optional[FailureCode] = None
    deadlock: Optional[DeadlockType] = None
    additional_outputs: list = None  # For multi-event steps (e.g., CONFLICT_REGISTERED + ACTION_REFUSED)

    def __post_init__(self):
        if self.additional_outputs is None:
            self.additional_outputs = []


class MPAKernel:
    """
    MPA-VIII-1 Authority Kernel.

    Invariant: No action may execute. All contested actions are refused.
    Plural authority coexists structurally without collapse.
    """

    def __init__(self, initial_state: Optional[AuthorityState] = None):
        """
        Initialize kernel with optional initial state.

        Default: empty state at epoch 0.
        """
        if initial_state is None:
            self.state = AuthorityState(
                state_id="",
                current_epoch=0,
                authorities={},
                conflicts={},
                deadlock=False,
            )
            self.state.state_id = compute_state_id(self.state)
        else:
            self.state = initial_state

        self.event_index = 0
        self.gas = GasAccounting(budget=0, consumed=0)
        self.conflict_counter = 0
        self.deadlock_declared = False  # Track if we've emitted DEADLOCK_DECLARED

        # Scope index for efficient conflict detection
        self._rebuild_scope_index()

    def _rebuild_scope_index(self) -> None:
        """Build index from scope element to authority IDs."""
        self.scope_index: dict[ScopeElement, list[str]] = {}
        for auth_id, auth in self.state.authorities.items():
            if auth.status == AuthorityStatus.ACTIVE:
                for elem in auth.scope:
                    key = tuple(elem)
                    if key not in self.scope_index:
                        self.scope_index[key] = []
                    self.scope_index[key].append(auth_id)

    def process_event(
        self, event: Union[AuthorityInjectionEvent, ActionRequestEvent]
    ) -> KernelResult:
        """
        Process a single event and return result.

        Dispatches to appropriate handler based on event type.
        """
        self.event_index += 1

        if isinstance(event, AuthorityInjectionEvent):
            return self._process_authority_injection(event)
        elif isinstance(event, ActionRequestEvent):
            return self._process_action_request(event)
        else:
            raise ValueError(f"Unknown event type: {type(event)}")

    def _consume_gas(self, amount: int) -> None:
        """Consume gas from current budget."""
        self.gas.consume(amount)

    def _process_authority_injection(
        self, event: AuthorityInjectionEvent
    ) -> KernelResult:
        """
        Process AuthorityInjection event.

        Per Q6 answer: Conflict is NOT registered at injection time.
        Authority is simply added to state.
        """
        self.gas = GasAccounting(budget=GAS_TRANSFORM, consumed=0)

        authority = deepcopy(event.authority)

        # Add to authorities dict (keyed by AuthorityID for anti-ordering)
        self.state.authorities[authority.authority_id] = authority
        self._consume_gas(GAS_UPDATE)

        # Update scope index
        for elem in authority.scope:
            key = tuple(elem)
            self._consume_gas(GAS_SET_MEM)
            if key not in self.scope_index:
                self.scope_index[key] = []
            self.scope_index[key].append(authority.authority_id)

        # Update state ID
        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.AUTHORITY_INJECTED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={"authority_id": authority.authority_id},
            ),
            state=self.state,
        )

    def _process_action_request(self, event: ActionRequestEvent) -> KernelResult:
        """
        Process ActionRequest event.

        MPA kernel NEVER executes actions. It:
        1. Checks if requester has authority
        2. Checks for conflicts (multiple authorities on same scope)
        3. Registers conflict and enters deadlock if necessary
        4. Refuses all actions
        """
        self.gas = GasAccounting(budget=GAS_ACTION_EVAL, consumed=0)

        requester = event.requester_holder_id

        # If already in deadlock, refuse immediately with kernel_state logged
        if self.state.deadlock:
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.ACTION_REFUSED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={
                        "reason": RefusalReason.DEADLOCK_STATE.value,
                        "request_id": event.request_id,
                        "kernel_state": "STATE_DEADLOCK",  # Per §11 observability binding
                    },
                ),
                state=self.state,
            )

        # Check if requester has any authority
        requester_authority = None
        for auth in self.state.authorities.values():
            self._consume_gas(GAS_SCAN_AR)
            if auth.holder_id == requester and auth.status == AuthorityStatus.ACTIVE:
                requester_authority = auth
                break

        if requester_authority is None:
            # Third-party action: no authority found
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.ACTION_REFUSED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={
                        "reason": RefusalReason.AUTHORITY_NOT_FOUND.value,
                        "request_id": event.request_id,
                    },
                ),
                state=self.state,
            )

        # Check for conflicts on requested scope
        for scope_elem in event.action:
            key = tuple(scope_elem)
            self._consume_gas(GAS_SET_MEM)

            # Check if scope element is already in an open conflict
            for conflict in self.state.conflicts.values():
                self._consume_gas(GAS_SCAN_AR)
                if conflict.status == ConflictStatus.OPEN:
                    for c_elem in conflict.scope_elements:
                        if tuple(c_elem) == key:
                            # Conflict exists, action is refused with CONFLICT_BLOCKS
                            self.state.state_id = compute_state_id(self.state)

                            return KernelResult(
                                output=KernelOutput(
                                    output_type=OutputType.ACTION_REFUSED,
                                    event_index=self.event_index,
                                    state_hash=self.state.state_id,
                                    details={
                                        "reason": RefusalReason.CONFLICT_BLOCKS.value,
                                        "request_id": event.request_id,
                                        "conflict_id": conflict.conflict_id,
                                    },
                                ),
                                state=self.state,
                            )

            # Check for multiple authorities on this scope (potential conflict)
            if key in self.scope_index:
                authority_ids = self.scope_index[key]
                if len(authority_ids) > 1:
                    # Multiple authorities on same scope - register conflict
                    conflict = self._register_conflict(
                        scope_elements=[scope_elem],
                        authority_ids=authority_ids,
                    )

                    # Update state ID after conflict registration
                    self.state.state_id = compute_state_id(self.state)
                    conflict_state_hash = self.state.state_id

                    # Per prereg §8: CONFLICT_REGISTERED and ACTION_REFUSED are
                    # distinct events in the same action-evaluation step.
                    # CONFLICT_REGISTERED is primary output, ACTION_REFUSED is additional.

                    conflict_output = KernelOutput(
                        output_type=OutputType.CONFLICT_REGISTERED,
                        event_index=self.event_index,
                        state_hash=conflict_state_hash,
                        details={
                            "conflict_id": conflict.conflict_id,
                            "authority_ids": conflict.authority_ids,
                            "scope_elements": conflict.scope_elements,
                            "request_id": event.request_id,
                        },
                    )

                    # ACTION_REFUSED follows with same event_index but reflects
                    # the action being refused due to the newly registered conflict
                    refused_output = KernelOutput(
                        output_type=OutputType.ACTION_REFUSED,
                        event_index=self.event_index,
                        state_hash=conflict_state_hash,
                        details={
                            "reason": RefusalReason.CONFLICT_BLOCKS.value,
                            "request_id": event.request_id,
                            "conflict_id": conflict.conflict_id,
                        },
                    )

                    return KernelResult(
                        output=conflict_output,
                        state=self.state,
                        additional_outputs=[refused_output],
                    )

        # No conflict found, but action still cannot execute in MPA
        # This should not happen with proper test setup (contested scope)
        self.state.state_id = compute_state_id(self.state)
        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.ACTION_REFUSED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={
                    "reason": "UNCONTESTED_BUT_BLOCKED",
                    "request_id": event.request_id,
                },
            ),
            state=self.state,
        )

    def _register_conflict(
        self, scope_elements: list, authority_ids: list[str]
    ) -> ConflictRecord:
        """
        Register a new conflict.

        Per Q6: Conflict is registered on first action evaluation,
        not at authority injection time.
        """
        self.conflict_counter += 1
        conflict_id = f"C:{self.conflict_counter:04d}"

        # Use frozenset for authority_ids to enforce unorderedness
        conflict = ConflictRecord(
            conflict_id=conflict_id,
            epoch_detected=self.state.current_epoch,
            scope_elements=scope_elements,
            authority_ids=frozenset(authority_ids),
            status=ConflictStatus.OPEN,
        )

        # Add to state
        self.state.conflicts[conflict_id] = conflict
        self._consume_gas(GAS_UPDATE)

        # Update conflict_set in each authority
        for auth_id in authority_ids:
            if auth_id in self.state.authorities:
                self.state.authorities[auth_id].conflict_set.append(conflict_id)
                self._consume_gas(GAS_UPDATE)

        return conflict

    def _check_deadlock(self) -> bool:
        """
        Check if kernel should enter deadlock.

        Per Q12: Check that all authorities have empty PermittedTransformationSet.
        """
        if self.state.deadlock:
            return False  # Already in deadlock

        # Must have at least one open conflict
        open_conflicts = self.state.get_open_conflicts()
        if not open_conflicts:
            return False

        # Check transformation admissibility for all authorities in conflicts
        for conflict in open_conflicts:
            for auth_id in conflict.authority_ids:
                auth = self.state.authorities.get(auth_id)
                if auth and auth.permitted_transformation_set:
                    # Some transformation possible - not deadlock
                    return False

        # No transformations possible, deadlock condition met
        return True

    def declare_deadlock(self) -> KernelResult:
        """
        Explicitly declare deadlock state.

        Per patched prereg: Called by harness after all Condition A actions
        have been evaluated and refused, not mid-action.

        Emits DEADLOCK_DECLARED exactly once.
        """
        if self.state.deadlock:
            raise RuntimeError("Deadlock already declared")

        # Verify preconditions per §11 operational rule
        if not self._check_deadlock():
            raise RuntimeError("Deadlock preconditions not met")

        self.event_index += 1
        self.state.deadlock = True
        self.deadlock_declared = True
        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.DEADLOCK_DECLARED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={
                    "deadlock_type": DeadlockType.CONFLICT_DEADLOCK.value,
                    "open_conflicts": [c.conflict_id for c in self.state.get_open_conflicts()],
                },
            ),
            state=self.state,
            deadlock=DeadlockType.CONFLICT_DEADLOCK,
        )

    def get_state_hash(self) -> str:
        """Return current state hash."""
        return self.state.state_id
