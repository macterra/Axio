"""
TG-VIII-3 Kernel Core

Temporal Governance kernel per TG Spec v0.1.
Implements:
- Two-phase processing (epoch advancement first, then Phase 2 inputs)
- Eager expiry on epoch advancement
- Authority renewal (creates new authority, non-resurrective)
- OPEN_BINDING / OPEN_NONBINDING conflict status
- Deadlock with causes (CONFLICT, EMPTY_AUTHORITY, MIXED)

Key constraints:
- No authority persists across epochs without explicit renewal
- Time does not resolve conflict, repair deadlock, or justify reinterpretation
- Kernel does not choose renewal targets
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
    DeadlockCause,
    KernelState,
    FailureCode,
    KernelOutput,
    TraceRecord,
    GasAccounting,
    EpochAdvancementRequest,
    AuthorityInjectionEvent,
    AuthorityRenewalRequest,
    DestructionAuthorizationEvent,
    ActionRequestEvent,
    ExpiryMetadata,
    DestructionMetadata,
    RenewalMetadata,
    ScopeElement,
)
from canonical import compute_state_id


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
    """Result of processing an event or step batch."""
    outputs: list[KernelOutput]
    traces: list[TraceRecord]
    state: AuthorityState
    failure: Optional[FailureCode] = None


class TGKernel:
    """
    TG-VIII-3 Temporal Governance Kernel.

    Supports:
    - Epoch advancement with eager expiry
    - Authority renewal (non-resurrective)
    - OPEN_BINDING / OPEN_NONBINDING conflict status
    - Deadlock with CONFLICT / EMPTY_AUTHORITY / MIXED causes
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
                deadlock_cause=None,
            )
            self.state.state_id = compute_state_id(self.state)
        else:
            self.state = initial_state

        self.event_index = 0
        self.trace_seq = 0
        self.conflict_counter = 0
        self.gas = GasAccounting(budget=0, consumed=0)

        # Track all AuthorityIDs ever used (for uniqueness check)
        self.used_authority_ids: set[str] = set(self.state.authorities.keys())

        # Scope index for efficient conflict detection
        self._rebuild_scope_index()

    def _rebuild_scope_index(self) -> None:
        """Build index from scope element to ACTIVE authority IDs."""
        self.scope_index: dict[ScopeElement, list[str]] = {}
        for auth_id, auth in self.state.authorities.items():
            if auth.status == AuthorityStatus.ACTIVE:
                for elem in auth.scope:
                    key = tuple(elem)
                    if key not in self.scope_index:
                        self.scope_index[key] = []
                    self.scope_index[key].append(auth_id)

    def _consume_gas(self, amount: int) -> None:
        """Consume gas from current budget."""
        self.gas.consume(amount)

    def _next_event_index(self) -> int:
        """Advance and return next event index."""
        self.event_index += 1
        return self.event_index

    def _next_trace_seq(self) -> int:
        """Advance and return next trace sequence."""
        self.trace_seq += 1
        return self.trace_seq

    # =========================================================================
    # Two-Phase Processing
    # =========================================================================

    def process_step_batch(
        self,
        epoch_advancement: Optional[EpochAdvancementRequest],
        phase2_events: list,
    ) -> KernelResult:
        """
        Process a step batch per prereg §8.

        Phase 0: Canonicalize inputs (epoch advancement first)
        Phase 1: Apply epoch transition + eager expirations
        Phase 2: Process remaining inputs in order

        Note: Authority injection consumes event index but produces no output.
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Phase 1: Epoch advancement (if present)
        if epoch_advancement is not None:
            result = self._process_epoch_advancement(epoch_advancement)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

        # Check for deadlock after epoch advancement
        deadlock_result = self._check_and_emit_deadlock(outputs, traces)
        if deadlock_result:
            outputs.extend(deadlock_result.outputs)
            traces.extend(deadlock_result.traces)

        # Phase 2: Process remaining events in canonical order
        # Order: AuthorityRenewalRequest, DestructionAuthorizationEvent, ActionRequest
        renewals = [e for e in phase2_events if isinstance(e, AuthorityRenewalRequest)]
        destructions = [e for e in phase2_events if isinstance(e, DestructionAuthorizationEvent)]
        actions = [e for e in phase2_events if isinstance(e, ActionRequestEvent)]
        injections = [e for e in phase2_events if isinstance(e, AuthorityInjectionEvent)]

        # Process injections first (trace-only, consumes event index)
        for event in injections:
            result = self._process_authority_injection(event)
            outputs.extend(result.outputs)  # Should be empty
            traces.extend(result.traces)
            if result.failure:
                return result

        # Process renewals
        for event in renewals:
            result = self._process_authority_renewal(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

        # Process destructions
        for event in destructions:
            result = self._process_destruction_authorization(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

        # Process actions
        for event in actions:
            result = self._process_action_request(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

            # Check for deadlock after action that may have created conflict
            deadlock_result = self._check_and_emit_deadlock(outputs, traces)
            if deadlock_result:
                outputs.extend(deadlock_result.outputs)
                traces.extend(deadlock_result.traces)

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
        )

    # =========================================================================
    # Phase 1: Epoch Advancement
    # =========================================================================

    def _process_epoch_advancement(
        self, event: EpochAdvancementRequest
    ) -> KernelResult:
        """
        Process epoch advancement per prereg §6.1 and §8.

        1. Validate newEpoch > currentEpoch (monotonicity)
        2. Update currentEpoch
        3. Apply eager expirations
        4. Emit AUTHORITY_EXPIRED per expired authority (canonical order)

        Note: Epoch advancement consumes event index but produces no output
        (trace-only). Only expirations produce output events.
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Validate monotonicity
        if event.new_epoch <= self.state.current_epoch:
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.TEMPORAL_REGRESSION,
            )

        # Consume event index for epoch advancement (trace-only)
        self._next_event_index()

        # Record trace
        traces.append(TraceRecord(
            trace_type="EPOCH_ADVANCEMENT",
            trace_seq=self._next_trace_seq(),
            details={
                "event_id": event.event_id,
                "old_epoch": self.state.current_epoch,
                "new_epoch": event.new_epoch,
            },
        ))

        # Update epoch
        old_epoch = self.state.current_epoch
        self.state.current_epoch = event.new_epoch

        # Eager expiry: find all authorities with ExpiryEpoch < CurrentEpoch
        expired_ids = []
        for auth_id, auth in self.state.authorities.items():
            if auth.status == AuthorityStatus.ACTIVE:
                if auth.expiry_epoch < self.state.current_epoch:
                    expired_ids.append(auth_id)

        # Process expirations in canonical (sorted) order
        for auth_id in sorted(expired_ids):
            auth = self.state.authorities[auth_id]
            auth.status = AuthorityStatus.EXPIRED
            auth.expiry_metadata = ExpiryMetadata(
                expiry_epoch=auth.expiry_epoch,
                transition_epoch=self.state.current_epoch,
                triggering_event_id=event.event_id,
            )

            # Remove from scope index
            for elem in auth.scope:
                key = tuple(elem)
                if key in self.scope_index and auth_id in self.scope_index[key]:
                    self.scope_index[key].remove(auth_id)

            # Emit AUTHORITY_EXPIRED
            self.state.state_id = compute_state_id(self.state)
            outputs.append(KernelOutput(
                output_type=OutputType.AUTHORITY_EXPIRED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "authority_id": auth_id,
                    "expiry_epoch": auth.expiry_epoch,
                    "transition_epoch": self.state.current_epoch,
                    "triggering_event_id": event.event_id,
                },
            ))

            # Update conflict status for conflicts involving this authority
            self._update_conflict_status_for_authority(auth_id)

        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
        )

    def _update_conflict_status_for_authority(self, auth_id: str) -> None:
        """
        Update conflict status when an authority becomes non-ACTIVE.

        Per prereg §9.1: OPEN_BINDING → OPEN_NONBINDING when at least one
        participant becomes EXPIRED or VOID.
        """
        for conflict in self.state.conflicts.values():
            if auth_id in conflict.authority_ids:
                if conflict.status == ConflictStatus.OPEN_BINDING:
                    # The authority that just became non-ACTIVE is a participant
                    # Per prereg: "at least one participant non-ACTIVE" → OPEN_NONBINDING
                    conflict.status = ConflictStatus.OPEN_NONBINDING

    # =========================================================================
    # Authority Injection (Trace-only)
    # =========================================================================

    def _process_authority_injection(
        self, event: AuthorityInjectionEvent
    ) -> KernelResult:
        """
        Process authority injection per prereg §6.1.1.

        - Trace-only input
        - Consumes event index
        - Produces no output event
        - State mutation visible via state hash
        """
        traces: list[TraceRecord] = []

        authority = deepcopy(event.authority)

        # Check AuthorityID uniqueness
        if authority.authority_id in self.used_authority_ids:
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.AUTHORITY_ID_REUSE,
            )

        # Consume event index
        self._next_event_index()

        # Mark as used
        self.used_authority_ids.add(authority.authority_id)

        # Add to state
        self.state.authorities[authority.authority_id] = authority
        self._consume_gas(GAS_UPDATE)

        # Update scope index if ACTIVE
        if authority.status == AuthorityStatus.ACTIVE:
            for elem in authority.scope:
                key = tuple(elem)
                if key not in self.scope_index:
                    self.scope_index[key] = []
                self.scope_index[key].append(authority.authority_id)

        # Trace record
        traces.append(TraceRecord(
            trace_type="TRACE_INPUT / AUTHORITY_RECORD_RECEIVED",
            trace_seq=self._next_trace_seq(),
            details={
                "event_index": self.event_index,
                "authority_id": authority.authority_id,
                "start_epoch": authority.start_epoch,
                "expiry_epoch": authority.expiry_epoch,
                "nonce": event.nonce,
            },
        ))

        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            outputs=[],  # No output event
            traces=traces,
            state=self.state,
        )

    # =========================================================================
    # Authority Renewal
    # =========================================================================

    def _process_authority_renewal(
        self, event: AuthorityRenewalRequest
    ) -> KernelResult:
        """
        Process authority renewal per prereg §6.2 and §11.

        - Creates new AuthorityID
        - Does not inherit authority force
        - Does not modify prior records
        - Non-resurrective
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        new_authority = deepcopy(event.new_authority)

        # Check AuthorityID uniqueness
        if new_authority.authority_id in self.used_authority_ids:
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.AUTHORITY_ID_REUSE,
            )

        # Validate prior authority exists if specified
        if event.prior_authority_id is not None:
            if event.prior_authority_id not in self.state.authorities:
                return KernelResult(
                    outputs=[],
                    traces=[],
                    state=self.state,
                    failure=FailureCode.PRIOR_AUTHORITY_NOT_FOUND,
                )

        # Mark as used
        self.used_authority_ids.add(new_authority.authority_id)

        # Attach renewal metadata
        new_authority.renewal_metadata = RenewalMetadata(
            prior_authority_id=event.prior_authority_id,
            renewal_event_id=event.renewal_event_id,
            renewal_epoch=self.state.current_epoch,
            external_authorizing_source_id=event.external_authorizing_source_id,
        )

        # Add to state
        self.state.authorities[new_authority.authority_id] = new_authority

        # Update scope index if ACTIVE
        if new_authority.status == AuthorityStatus.ACTIVE:
            for elem in new_authority.scope:
                key = tuple(elem)
                if key not in self.scope_index:
                    self.scope_index[key] = []
                self.scope_index[key].append(new_authority.authority_id)

        self.state.state_id = compute_state_id(self.state)

        # Emit AUTHORITY_RENEWED
        outputs.append(KernelOutput(
            output_type=OutputType.AUTHORITY_RENEWED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "new_authority_id": new_authority.authority_id,
                "prior_authority_id": event.prior_authority_id,
                "renewal_event_id": event.renewal_event_id,
                "renewal_epoch": self.state.current_epoch,
            },
        ))

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
        )

    # =========================================================================
    # Destruction Authorization
    # =========================================================================

    def _process_destruction_authorization(
        self, event: DestructionAuthorizationEvent
    ) -> KernelResult:
        """
        Process destruction authorization per prereg §6.3.

        - Must reference existing conflict
        - Transitions target(s) to VOID
        - Updates conflict status
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Validate conflict exists
        conflict = self.state.conflicts.get(event.conflict_id)
        if conflict is None:
            # Conflict not found - refuse
            self.state.state_id = compute_state_id(self.state)
            outputs.append(KernelOutput(
                output_type=OutputType.ACTION_REFUSED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "reason": "CONFLICT_NOT_FOUND",
                    "conflict_id": event.conflict_id,
                },
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Determine targets
        if event.target_authority_ids == ["ALL"]:
            target_ids = list(conflict.authority_ids)
        else:
            target_ids = event.target_authority_ids

        # Process each target
        for auth_id in sorted(target_ids):
            auth = self.state.authorities.get(auth_id)
            if auth is None:
                continue
            if auth.status == AuthorityStatus.VOID:
                continue  # Already destroyed

            # Transition to VOID
            auth.status = AuthorityStatus.VOID
            auth.destruction_metadata = DestructionMetadata(
                destruction_event_id=f"DE:{event.nonce}",
                authorizer_id=event.authorizer_id,
                destruction_epoch=self.state.current_epoch,
                destruction_nonce=event.nonce,
            )

            # Remove from scope index
            for elem in auth.scope:
                key = tuple(elem)
                if key in self.scope_index and auth_id in self.scope_index[key]:
                    self.scope_index[key].remove(auth_id)

            # Update conflict status
            self._update_conflict_status_for_authority(auth_id)

            # Emit AUTHORITY_DESTROYED
            self.state.state_id = compute_state_id(self.state)
            outputs.append(KernelOutput(
                output_type=OutputType.AUTHORITY_DESTROYED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "authority_id": auth_id,
                    "conflict_id": event.conflict_id,
                    "authorizer_id": event.authorizer_id,
                    "destruction_epoch": self.state.current_epoch,
                },
            ))

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
        )

    # =========================================================================
    # Action Request
    # =========================================================================

    def _process_action_request(
        self, event: ActionRequestEvent
    ) -> KernelResult:
        """
        Process action request per prereg §6.4.

        - Check requester has ACTIVE authority
        - Evaluate admissibility (permit vs deny)
        - Register conflict if disagreement
        - Execute if coherent admissibility
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        self.gas = GasAccounting(budget=GAS_ACTION_EVAL, consumed=0)

        requester = event.requester_holder_id
        transformation_type = event.transformation_type

        # Re-evaluate deadlock status before processing
        # Deadlock may have been resolved if all conflicts became OPEN_NONBINDING
        # or new ACTIVE authorities were added
        self._reevaluate_deadlock_status()

        # Check if in deadlock due to EMPTY_AUTHORITY
        if self.state.deadlock and self.state.deadlock_cause == DeadlockCause.EMPTY_AUTHORITY:
            # Can only exit via renewal adding new authority
            self.state.state_id = compute_state_id(self.state)
            outputs.append(KernelOutput(
                output_type=OutputType.ACTION_REFUSED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "reason": RefusalReason.NO_AUTHORITY.value,
                    "request_id": event.request_id,
                    "kernel_state": KernelState.STATE_DEADLOCK.value,
                },
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check if any ACTIVE authority exists
        active_authorities = self.state.get_active_authorities()
        if not active_authorities:
            self.state.state_id = compute_state_id(self.state)
            outputs.append(KernelOutput(
                output_type=OutputType.ACTION_REFUSED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "reason": RefusalReason.NO_AUTHORITY.value,
                    "request_id": event.request_id,
                },
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check for existing open binding conflicts on scope
        for scope_elem in event.action:
            key = tuple(scope_elem)
            for conflict in self.state.conflicts.values():
                if conflict.status == ConflictStatus.OPEN_BINDING:
                    for c_elem in conflict.scope_elements:
                        if tuple(c_elem) == key:
                            # Existing binding conflict blocks
                            self.state.state_id = compute_state_id(self.state)
                            outputs.append(KernelOutput(
                                output_type=OutputType.ACTION_REFUSED,
                                event_index=self._next_event_index(),
                                state_hash=self.state.state_id,
                                details={
                                    "reason": RefusalReason.CONFLICT_BLOCKS.value,
                                    "request_id": event.request_id,
                                    "conflict_id": conflict.conflict_id,
                                },
                            ))
                            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Evaluate admissibility for each scope element
        for scope_elem in event.action:
            has_permit, has_deny, auth_ids = self._evaluate_admissibility(
                scope_elem, transformation_type
            )

            if has_permit and has_deny:
                # Divergent admissibility - register conflict
                conflict = self._register_conflict(
                    scope_elements=[scope_elem],
                    authority_ids=auth_ids,
                )

                self.state.state_id = compute_state_id(self.state)

                # Refuse action (conflict registered in state, not as output)
                outputs.append(KernelOutput(
                    output_type=OutputType.ACTION_REFUSED,
                    event_index=self._next_event_index(),
                    state_hash=self.state.state_id,
                    details={
                        "reason": RefusalReason.CONFLICT_BLOCKS.value,
                        "request_id": event.request_id,
                        "conflict_id": conflict.conflict_id,
                    },
                ))
                return KernelResult(outputs=outputs, traces=traces, state=self.state)

            if not has_permit:
                # No permitting authority
                self.state.state_id = compute_state_id(self.state)
                outputs.append(KernelOutput(
                    output_type=OutputType.ACTION_REFUSED,
                    event_index=self._next_event_index(),
                    state_hash=self.state.state_id,
                    details={
                        "reason": RefusalReason.NO_AUTHORITY.value,
                        "request_id": event.request_id,
                    },
                ))
                return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # All scope elements have coherent admissibility - execute
        self.state.state_id = compute_state_id(self.state)
        outputs.append(KernelOutput(
            output_type=OutputType.ACTION_EXECUTED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "request_id": event.request_id,
                "transformation_type": transformation_type,
            },
        ))

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
        )

    def _evaluate_admissibility(
        self, scope_elem: ScopeElement, transformation_type: str
    ) -> tuple[bool, bool, list[str]]:
        """
        Evaluate admissibility for a transformation on a scope element.

        Returns:
            (has_permit, has_deny, authority_ids)
        """
        key = tuple(scope_elem)
        if key not in self.scope_index:
            return False, False, []

        authority_ids = []
        has_permit = False
        has_deny = False

        for auth_id in self.scope_index[key]:
            auth = self.state.authorities.get(auth_id)
            if auth and auth.status == AuthorityStatus.ACTIVE:
                authority_ids.append(auth_id)
                self._consume_gas(GAS_SCAN_AR)

                if transformation_type in auth.permitted_transformation_set:
                    has_permit = True
                else:
                    has_deny = True

        return has_permit, has_deny, authority_ids

    def _register_conflict(
        self, scope_elements: list, authority_ids: list[str]
    ) -> ConflictRecord:
        """
        Register a new conflict per prereg §9.2.

        Conflict is registered on action evaluation, not at injection time.
        """
        self.conflict_counter += 1
        conflict_id = f"C:{self.conflict_counter:04d}"

        conflict = ConflictRecord(
            conflict_id=conflict_id,
            epoch_detected=self.state.current_epoch,
            scope_elements=scope_elements,
            authority_ids=frozenset(authority_ids),
            status=ConflictStatus.OPEN_BINDING,
        )

        self.state.conflicts[conflict_id] = conflict
        self._consume_gas(GAS_UPDATE)

        # Update conflict_set in each authority
        for auth_id in authority_ids:
            if auth_id in self.state.authorities:
                self.state.authorities[auth_id].conflict_set.append(conflict_id)
                self._consume_gas(GAS_UPDATE)

        return conflict

    # =========================================================================
    # Deadlock Detection
    # =========================================================================

    def _check_and_emit_deadlock(
        self,
        existing_outputs: list[KernelOutput],
        existing_traces: list[TraceRecord],
    ) -> Optional[KernelResult]:
        """
        Check for deadlock and emit DEADLOCK_DECLARED/PERSISTED.

        Per prereg §10: Deadlock is declared eagerly when:
        - ACTIVE_AUTHORITY_SET == ∅, OR
        - Open binding conflict with no admissible resolution

        Returns KernelResult with deadlock output if deadlock should be emitted.
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Compute current deadlock cause
        deadlock_cause = self._compute_deadlock_cause()

        if deadlock_cause is None:
            # No deadlock condition
            if self.state.deadlock:
                # Was in deadlock, now resolved
                self.state.deadlock = False
                self.state.deadlock_cause = None
            return None

        # Determine output type
        if self.state.deadlock:
            output_type = OutputType.DEADLOCK_PERSISTED
        else:
            output_type = OutputType.DEADLOCK_DECLARED
            self.state.deadlock = True

        # Update cause (recomputed per emission)
        self.state.deadlock_cause = deadlock_cause
        self.state.state_id = compute_state_id(self.state)

        outputs.append(KernelOutput(
            output_type=output_type,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "deadlock_cause": deadlock_cause.value,
                "open_conflicts": [c.conflict_id for c in self.state.get_open_binding_conflicts()],
                "active_authority_count": len(self.state.get_active_authorities()),
                "current_epoch": self.state.current_epoch,
            },
        ))

        return KernelResult(outputs=outputs, traces=traces, state=self.state)

    def _compute_deadlock_cause(self) -> Optional[DeadlockCause]:
        """
        Compute deadlock cause per prereg §10.1.

        Returns None if no deadlock condition.
        """
        active_authorities = self.state.get_active_authorities()
        open_binding_conflicts = self.state.get_open_binding_conflicts()
        has_conflict_history = self.state.has_conflict_history()

        has_empty_authority = len(active_authorities) == 0
        has_open_conflict = len(open_binding_conflicts) > 0

        if has_empty_authority and has_conflict_history:
            return DeadlockCause.MIXED
        elif has_empty_authority:
            return DeadlockCause.EMPTY_AUTHORITY
        elif has_open_conflict:
            return DeadlockCause.CONFLICT
        else:
            return None

    def _reevaluate_deadlock_status(self) -> None:
        """
        Re-evaluate deadlock status based on current state.

        Deadlock may be cleared if:
        - All OPEN_BINDING conflicts became OPEN_NONBINDING
        - New ACTIVE authorities were added

        This does not emit outputs - just updates internal state.
        """
        if not self.state.deadlock:
            return

        deadlock_cause = self._compute_deadlock_cause()
        if deadlock_cause is None:
            # Deadlock resolved
            self.state.deadlock = False
            self.state.deadlock_cause = None
        else:
            # Update cause (may have changed)
            self.state.deadlock_cause = deadlock_cause

    # =========================================================================
    # Query Methods
    # =========================================================================

    def get_state_hash(self) -> str:
        """Return current state hash."""
        return self.state.state_id

    def get_kernel_state(self) -> KernelState:
        """Return current kernel state."""
        if self.state.deadlock:
            return KernelState.STATE_DEADLOCK
        return KernelState.STATE_OPERATIONAL

    def get_current_epoch(self) -> int:
        """Return current epoch."""
        return self.state.current_epoch
