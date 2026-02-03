"""
DCR-VIII-2 Kernel Core

Destructive Conflict Resolution kernel per DCR Spec v0.1.
Extends VIII-1 with:
- Authority destruction (VOID status)
- Asymmetric admissibility evaluation
- ACTION_EXECUTED when admissibility restored
- DEADLOCK_PERSISTED for persistent deadlock

Key constraints:
- Destruction is the ONLY resolution mechanism
- No synthesis, merging, or narrowing
- VOID authorities are non-participants
- Kernel does not choose destruction targets
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
    KernelState,
    FailureCode,
    KernelOutput,
    GasAccounting,
    AuthorityInjectionEvent,
    ActionRequestEvent,
    DestructionAuthorizationEvent,
    DestructionMetadata,
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

# Gas budgets
GAS_ACTION_EVAL = 50_000
GAS_TRANSFORM = 100_000
GAS_DESTRUCTION = 100_000


@dataclass
class KernelResult:
    """Result of processing an event."""
    output: KernelOutput
    state: AuthorityState
    failure: Optional[FailureCode] = None
    deadlock: Optional[DeadlockType] = None
    additional_outputs: list = None  # For multi-event steps

    def __post_init__(self):
        if self.additional_outputs is None:
            self.additional_outputs = []


class DCRKernel:
    """
    DCR-VIII-2 Authority Kernel.

    Supports:
    - Asymmetric admissibility (permit vs deny via PermittedTransformationSet)
    - Authority destruction (ACTIVE → VOID)
    - Admissibility re-evaluation after destruction
    - Action execution when admissibility restored
    """

    def __init__(self, initial_state: Optional[AuthorityState] = None):
        """Initialize kernel with optional initial state."""
        if initial_state is None:
            self.state = AuthorityState(
                state_id="",
                current_epoch=0,
                authorities={},
                conflicts={},
                deadlock=False,
                destruction_count=0,
            )
            self.state.state_id = compute_state_id(self.state)
        else:
            self.state = initial_state

        self.event_index = 0
        self.gas = GasAccounting(budget=0, consumed=0)
        self.conflict_counter = 0
        self.destruction_authorization_received = False  # Track for AMBIGUOUS_DESTRUCTION

        # Scope index for efficient conflict detection
        self._rebuild_scope_index()

    def _rebuild_scope_index(self) -> None:
        """Build index from scope element to ACTIVE authority IDs."""
        self.scope_index: dict[ScopeElement, list[str]] = {}
        for auth_id, auth in self.state.authorities.items():
            # Only ACTIVE authorities participate
            if auth.status == AuthorityStatus.ACTIVE:
                for elem in auth.scope:
                    key = tuple(elem)
                    if key not in self.scope_index:
                        self.scope_index[key] = []
                    self.scope_index[key].append(auth_id)

    def process_event(
        self, event: Union[AuthorityInjectionEvent, ActionRequestEvent, DestructionAuthorizationEvent]
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
        elif isinstance(event, DestructionAuthorizationEvent):
            return self._process_destruction_authorization(event)
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

        Per prereg §3: Conflict is NOT registered at injection time.
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

    def _evaluate_admissibility(
        self, scope_elem: ScopeElement, transformation_type: str
    ) -> tuple[bool, bool, list[str]]:
        """
        Evaluate admissibility for a transformation on a scope element.

        Returns:
            (has_permit, has_deny, authority_ids)
            - has_permit: True if at least one ACTIVE authority permits
            - has_deny: True if at least one ACTIVE authority denies (absence of permission)
            - authority_ids: List of all ACTIVE authorities on this scope
        """
        key = tuple(scope_elem)
        if key not in self.scope_index:
            return False, False, []

        authority_ids = []
        has_permit = False
        has_deny = False

        for auth_id in self.scope_index[key]:
            auth = self.state.authorities.get(auth_id)
            # Only ACTIVE authorities participate (VOID are non-participants)
            if auth and auth.status == AuthorityStatus.ACTIVE:
                authority_ids.append(auth_id)
                self._consume_gas(GAS_SCAN_AR)

                if transformation_type in auth.permitted_transformation_set:
                    has_permit = True
                else:
                    has_deny = True

        return has_permit, has_deny, authority_ids

    def _process_action_request(self, event: ActionRequestEvent) -> KernelResult:
        """
        Process ActionRequest event.

        Per prereg:
        1. Check if requester has authority
        2. Evaluate admissibility (permit vs deny)
        3. Detect conflict if disagreement
        4. Execute if admissibility is coherent
        5. Refuse otherwise
        """
        self.gas = GasAccounting(budget=GAS_ACTION_EVAL, consumed=0)

        requester = event.requester_holder_id
        transformation_type = event.transformation_type

        # If in deadlock, check if we should stay in deadlock
        if self.state.deadlock:
            # Check if any ACTIVE authority remains
            active_authorities = self.state.get_active_authorities()
            if not active_authorities:
                # No authority at all - refuse with NO_AUTHORITY
                self.state.state_id = compute_state_id(self.state)
                return KernelResult(
                    output=KernelOutput(
                        output_type=OutputType.ACTION_REFUSED,
                        event_index=self.event_index,
                        state_hash=self.state.state_id,
                        details={
                            "reason": RefusalReason.NO_AUTHORITY.value,
                            "request_id": event.request_id,
                            "kernel_state": KernelState.STATE_DEADLOCK.value,
                        },
                    ),
                    state=self.state,
                )

            # Check if conflict still blocks
            for scope_elem in event.action:
                has_permit, has_deny, auth_ids = self._evaluate_admissibility(
                    scope_elem, transformation_type
                )
                if has_permit and has_deny:
                    # Still conflicted - refuse
                    self.state.state_id = compute_state_id(self.state)
                    return KernelResult(
                        output=KernelOutput(
                            output_type=OutputType.ACTION_REFUSED,
                            event_index=self.event_index,
                            state_hash=self.state.state_id,
                            details={
                                "reason": RefusalReason.CONFLICT_BLOCKS.value,
                                "request_id": event.request_id,
                                "kernel_state": KernelState.STATE_DEADLOCK.value,
                            },
                        ),
                        state=self.state,
                    )

                if not has_permit:
                    # No permitting authority - refuse with NO_AUTHORITY
                    self.state.state_id = compute_state_id(self.state)
                    return KernelResult(
                        output=KernelOutput(
                            output_type=OutputType.ACTION_REFUSED,
                            event_index=self.event_index,
                            state_hash=self.state.state_id,
                            details={
                                "reason": RefusalReason.NO_AUTHORITY.value,
                                "request_id": event.request_id,
                                "kernel_state": KernelState.STATE_DEADLOCK.value,
                            },
                        ),
                        state=self.state,
                    )

            # Admissibility restored - exit deadlock and execute
            self.state.deadlock = False
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.ACTION_EXECUTED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={
                        "request_id": event.request_id,
                        "transformation_type": transformation_type,
                    },
                ),
                state=self.state,
            )

        # Not in deadlock - normal processing

        # Check if requester has any ACTIVE authority
        requester_authority = None
        for auth in self.state.authorities.values():
            self._consume_gas(GAS_SCAN_AR)
            if auth.holder_id == requester and auth.status == AuthorityStatus.ACTIVE:
                requester_authority = auth
                break

        if requester_authority is None:
            # No authority found for requester
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

        # Check for existing open conflicts
        for scope_elem in event.action:
            key = tuple(scope_elem)
            for conflict in self.state.conflicts.values():
                self._consume_gas(GAS_SCAN_AR)
                if conflict.status == ConflictStatus.OPEN:
                    for c_elem in conflict.scope_elements:
                        if tuple(c_elem) == key:
                            # Existing conflict blocks
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

        # Evaluate admissibility for each scope element
        for scope_elem in event.action:
            has_permit, has_deny, auth_ids = self._evaluate_admissibility(
                scope_elem, transformation_type
            )

            if has_permit and has_deny:
                # Divergent admissibility - register conflict per prereg §3
                conflict = self._register_conflict(
                    scope_elements=[scope_elem],
                    authority_ids=auth_ids,
                )

                self.state.state_id = compute_state_id(self.state)
                conflict_state_hash = self.state.state_id

                # Emit CONFLICT_REGISTERED + ACTION_REFUSED
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

            if not has_permit:
                # No permitting authority for this scope
                self.state.state_id = compute_state_id(self.state)
                return KernelResult(
                    output=KernelOutput(
                        output_type=OutputType.ACTION_REFUSED,
                        event_index=self.event_index,
                        state_hash=self.state.state_id,
                        details={
                            "reason": RefusalReason.NO_AUTHORITY.value,
                            "request_id": event.request_id,
                        },
                    ),
                    state=self.state,
                )

        # All scope elements have coherent admissibility (permit without deny)
        # Execute the action
        self.state.state_id = compute_state_id(self.state)
        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.ACTION_EXECUTED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={
                    "request_id": event.request_id,
                    "transformation_type": transformation_type,
                },
            ),
            state=self.state,
        )

    def _process_destruction_authorization(
        self, event: DestructionAuthorizationEvent
    ) -> KernelResult:
        """
        Process DestructionAuthorizationRequest per prereg §4, §5, §15.

        Constraints:
        - Must reference existing conflict
        - Target must be ACTIVE (not already VOID)
        - At most one authorization per run
        """
        self.gas = GasAccounting(budget=GAS_DESTRUCTION, consumed=0)

        # Check for multiple authorizations
        if self.destruction_authorization_received:
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.DESTRUCTION_REFUSED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={
                        "reason": RefusalReason.AMBIGUOUS_DESTRUCTION.value,
                        "nonce": event.nonce,
                    },
                ),
                state=self.state,
                failure=FailureCode.AMBIGUOUS_DESTRUCTION,
            )

        # Mark that we've received an authorization
        self.destruction_authorization_received = True

        # Validate conflict exists
        conflict = self.state.conflicts.get(event.conflict_id)
        if conflict is None or conflict.status != ConflictStatus.OPEN:
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.DESTRUCTION_REFUSED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={
                        "reason": RefusalReason.CONFLICT_NOT_FOUND.value,
                        "conflict_id": event.conflict_id,
                        "nonce": event.nonce,
                    },
                ),
                state=self.state,
            )

        # Determine targets
        if event.target_authority_ids == ["ALL"]:
            # Destroy all authorities in the conflict
            target_ids = list(conflict.authority_ids)
        else:
            target_ids = event.target_authority_ids

        # Validate all targets are ACTIVE
        for auth_id in target_ids:
            auth = self.state.authorities.get(auth_id)
            if auth is None:
                self.state.state_id = compute_state_id(self.state)
                return KernelResult(
                    output=KernelOutput(
                        output_type=OutputType.DESTRUCTION_REFUSED,
                        event_index=self.event_index,
                        state_hash=self.state.state_id,
                        details={
                            "reason": RefusalReason.AUTHORITY_NOT_FOUND.value,
                            "authority_id": auth_id,
                            "nonce": event.nonce,
                        },
                    ),
                    state=self.state,
                )
            if auth.status == AuthorityStatus.VOID:
                self.state.state_id = compute_state_id(self.state)
                return KernelResult(
                    output=KernelOutput(
                        output_type=OutputType.DESTRUCTION_REFUSED,
                        event_index=self.event_index,
                        state_hash=self.state.state_id,
                        details={
                            "reason": RefusalReason.ALREADY_VOID.value,
                            "authority_id": auth_id,
                            "nonce": event.nonce,
                        },
                    ),
                    state=self.state,
                )

        # Execute destruction for each target
        destroyed_ids = []
        for auth_id in target_ids:
            self.state.destruction_count += 1
            auth = self.state.authorities[auth_id]

            # Transition to VOID
            auth.status = AuthorityStatus.VOID
            auth.destruction_metadata = DestructionMetadata(
                conflict_id=event.conflict_id,
                authorizer_id=event.authorizer_id,
                nonce=event.nonce,
                destruction_index=self.state.destruction_count,
            )
            destroyed_ids.append(auth_id)

            # Remove from scope index
            for elem in auth.scope:
                key = tuple(elem)
                if key in self.scope_index and auth_id in self.scope_index[key]:
                    self.scope_index[key].remove(auth_id)

            self._consume_gas(GAS_UPDATE)

        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.AUTHORITY_DESTROYED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={
                    "destroyed_authority_ids": destroyed_ids,
                    "conflict_id": event.conflict_id,
                    "authorizer_id": event.authorizer_id,
                    "nonce": event.nonce,
                },
            ),
            state=self.state,
        )

    def _register_conflict(
        self, scope_elements: list, authority_ids: list[str]
    ) -> ConflictRecord:
        """
        Register a new conflict.

        Per prereg §3: Conflict is registered on first contested action request.
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

        Per prereg and answers: Deadlock occurs when:
        - Open conflict exists
        - No kernel-internal transformation can resolve it

        In VIII-2, the only resolution mechanism is destruction (external
        governance action). Therefore, any open conflict = deadlock.

        NOTE: permitted_transformation_set defines what actions an authority
        PERMITS, not conflict resolution mechanisms. Denial is absence of
        permission, not a semantic veto that can be "resolved" internally.
        """
        if self.state.deadlock:
            return False  # Already in deadlock

        # Must have at least one open conflict
        open_conflicts = self.state.get_open_conflicts()
        if not open_conflicts:
            return False

        # In VIII-2, open conflict with no destruction = deadlock
        # There is no kernel-internal resolution mechanism
        return True

    def declare_deadlock(self) -> KernelResult:
        """
        Explicitly declare deadlock state.

        Emits DEADLOCK_DECLARED exactly once.
        """
        if self.state.deadlock:
            raise RuntimeError("Deadlock already declared")

        # Verify preconditions
        if not self._check_deadlock():
            raise RuntimeError("Deadlock preconditions not met")

        self.event_index += 1
        self.state.deadlock = True
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

    def declare_deadlock_persisted(self) -> KernelResult:
        """
        Emit DEADLOCK_PERSISTED to confirm deadlock remains.

        Per prereg §9: Distinct from DEADLOCK_DECLARED.
        """
        if not self.state.deadlock:
            raise RuntimeError("Cannot persist deadlock that was not declared")

        self.event_index += 1
        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.DEADLOCK_PERSISTED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={
                    "kernel_state": KernelState.STATE_DEADLOCK.value,
                    "open_conflicts": [c.conflict_id for c in self.state.get_open_conflicts()],
                },
            ),
            state=self.state,
        )

    def get_state_hash(self) -> str:
        """Return current state hash."""
        return self.state.state_id

    def get_kernel_state(self) -> KernelState:
        """Return current kernel state."""
        if self.state.deadlock:
            return KernelState.STATE_DEADLOCK
        return KernelState.STATE_OPERATIONAL
