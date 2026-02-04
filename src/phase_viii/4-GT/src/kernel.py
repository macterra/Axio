"""
GT-VIII-4 Kernel Core

Governance Transitions kernel per VIII-4 Spec v0.1.

Implements:
- Two-phase processing (epoch advancement, then Phase 2)
- Governance actions (DESTROY_AUTHORITY, CREATE_AUTHORITY)
- Non-amplification enforcement (AAV)
- Scope containment (byte-equality only)
- Authority activation timing (pending until next epoch)
- Instruction accounting with bound exhaustion
- Conflict detection (structural only, no DENY vote)

Key constraints:
- No kernel-initiated governance
- No privilege escalation
- No special-case for self-governance
- Deterministic and replayable
"""

from dataclasses import dataclass
from typing import Optional
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
    InstructionAccounting,
    EpochAdvancementRequest,
    AuthorityInjectionEvent,
    AuthorityRenewalRequest,
    GovernanceActionRequest,
    GovernanceActionType,
    ActionRequestEvent,
    ExpiryMetadata,
    DestructionMetadata,
    CreationMetadata,
    # AAV helpers
    AAV_LENGTH,
    AAV_RESERVED_MASK,
    TRANSFORM_EXECUTE,
    TRANSFORM_DESTROY_AUTHORITY,
    TRANSFORM_CREATE_AUTHORITY,
    aav_bit,
    aav_has_bit,
    aav_has_reserved_bits,
    aav_union,
    aav_is_subset,
    # Instruction costs
    C_LOOKUP,
    C_AAV_WORD,
    C_AST_RULE,
    C_CONFLICT_UPDATE,
    C_STATE_WRITE,
    B_EPOCH_INSTR,
)
from canonical import compute_state_id, governance_action_identity


@dataclass
class KernelResult:
    """Result of processing an event or step batch."""
    outputs: list[KernelOutput]
    traces: list[TraceRecord]
    state: AuthorityState
    failure: Optional[FailureCode] = None


class GTKernel:
    """
    GT-VIII-4 Governance Transitions Kernel.

    Supports:
    - Governance actions (DESTROY_AUTHORITY, CREATE_AUTHORITY)
    - Non-amplification enforcement
    - Scope containment (byte-equality)
    - Authority activation timing (pending → active at epoch boundary)
    - Instruction bound enforcement
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
                pending_authorities={},
            )
            self.state.state_id = compute_state_id(self.state)
        else:
            self.state = initial_state

        self.event_index = 0
        self.trace_seq = 0
        self.conflict_counter = 0
        self.instructions = InstructionAccounting()

        # Track all AuthorityIDs ever used (for uniqueness check)
        self.used_authority_ids: set[str] = set(self.state.authorities.keys())
        self.used_authority_ids.update(self.state.pending_authorities.keys())

        # Scope index for efficient conflict detection
        self._rebuild_scope_index()

    def _rebuild_scope_index(self) -> None:
        """Build index from scope to ACTIVE authority IDs."""
        self.scope_index: dict[str, list[str]] = {}
        for auth_id, auth in self.state.authorities.items():
            if auth.status == AuthorityStatus.ACTIVE:
                scope = auth.resource_scope
                if scope not in self.scope_index:
                    self.scope_index[scope] = []
                self.scope_index[scope].append(auth_id)

    def _consume_instructions(self, amount: int) -> bool:
        """Consume instructions, return True if within budget."""
        return self.instructions.consume(amount)

    def _next_event_index(self) -> int:
        """Advance and return next event index."""
        self.event_index += 1
        return self.event_index

    def _next_trace_seq(self) -> int:
        """Advance and return next trace sequence."""
        self.trace_seq += 1
        return self.trace_seq

    def _next_conflict_id(self) -> str:
        """Generate next conflict ID."""
        self.conflict_counter += 1
        return f"C:{self.conflict_counter:04d}"

    def get_state_hash(self) -> str:
        """Return current state hash."""
        return self.state.state_id

    def get_current_epoch(self) -> int:
        """Return current epoch."""
        return self.state.current_epoch

    def get_kernel_state(self) -> KernelState:
        """Return kernel operational state."""
        if self.state.deadlock:
            return KernelState.STATE_DEADLOCK
        return KernelState.STATE_OPERATIONAL

    # =========================================================================
    # Two-Phase Processing
    # =========================================================================

    def process_step_batch(
        self,
        epoch_advancement: Optional[EpochAdvancementRequest],
        phase2_events: list,
    ) -> KernelResult:
        """
        Process a step batch per prereg §7.

        Phase 1: Epoch advancement + eager expiry + pending activation
        Phase 2: In sub-phase order:
          1. Renewals
          2. Authority Destructions (DESTROY_AUTHORITY)
          3. Authority Creations (CREATE_AUTHORITY)
          4. Non-Governance Actions
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Reset instruction budget for new epoch if advancing
        if epoch_advancement is not None:
            self.instructions.reset()

        # Phase 1: Epoch advancement (if present)
        if epoch_advancement is not None:
            result = self._process_epoch_advancement(epoch_advancement)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

            # Check for deadlock after epoch advancement (only if epoch advanced)
            deadlock_result = self._check_and_emit_deadlock(outputs, traces)
            if deadlock_result:
                outputs.extend(deadlock_result.outputs)
                traces.extend(deadlock_result.traces)

        # Separate Phase 2 events by type
        injections = [e for e in phase2_events if isinstance(e, AuthorityInjectionEvent)]
        renewals = [e for e in phase2_events if isinstance(e, AuthorityRenewalRequest)]
        governance = [e for e in phase2_events if isinstance(e, GovernanceActionRequest)]
        actions = [e for e in phase2_events if isinstance(e, ActionRequestEvent)]

        # Sort governance actions by type (DESTROY first, then CREATE)
        destructions = sorted(
            [g for g in governance if g.action_type == GovernanceActionType.DESTROY_AUTHORITY],
            key=lambda g: governance_action_identity(g.epoch, g.initiator_ids, g.target_ids, g.action_type.value, g.params)
        )
        creations = sorted(
            [g for g in governance if g.action_type == GovernanceActionType.CREATE_AUTHORITY],
            key=lambda g: governance_action_identity(g.epoch, g.initiator_ids, g.target_ids, g.action_type.value, g.params)
        )

        # Process injections first (setup only, no output)
        for event in injections:
            result = self._process_authority_injection(event)
            traces.extend(result.traces)
            if result.failure:
                return result

        # Sub-phase 1: Renewals
        for event in renewals:
            result = self._process_authority_renewal(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

        # Sub-phase 2: Authority Destructions
        for event in destructions:
            if self.instructions.is_exhausted():
                # Refuse remaining actions
                outputs.append(self._emit_refusal(
                    event.event_id,
                    RefusalReason.BOUND_EXHAUSTED,
                    {"remaining_actions": len(destructions) + len(creations) + len(actions)}
                ))
                continue

            result = self._process_governance_action(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

            # Check deadlock after governance action
            deadlock_result = self._check_and_emit_deadlock(outputs, traces)
            if deadlock_result:
                outputs.extend(deadlock_result.outputs)
                traces.extend(deadlock_result.traces)

        # Sub-phase 3: Authority Creations
        for event in creations:
            if self.instructions.is_exhausted():
                outputs.append(self._emit_refusal(
                    event.event_id,
                    RefusalReason.BOUND_EXHAUSTED,
                    {"remaining_actions": len(creations) + len(actions)}
                ))
                continue

            result = self._process_governance_action(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

            # Check deadlock after governance action
            deadlock_result = self._check_and_emit_deadlock(outputs, traces)
            if deadlock_result:
                outputs.extend(deadlock_result.outputs)
                traces.extend(deadlock_result.traces)

        # Sub-phase 4: Non-Governance Actions
        for event in actions:
            if self.instructions.is_exhausted():
                outputs.append(self._emit_refusal(
                    event.request_id,
                    RefusalReason.BOUND_EXHAUSTED,
                    {"remaining_actions": len(actions)}
                ))
                continue

            result = self._process_action_request(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

            # Check deadlock after action
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
        Process epoch advancement per prereg §7.1.

        1. Validate newEpoch > currentEpoch (monotonicity)
        2. Activate pending authorities from previous epoch
        3. Update currentEpoch
        4. Apply eager expirations
        5. Update conflict statuses
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

        # Consume event index (trace-only)
        self._next_event_index()

        # Trace epoch advancement
        traces.append(TraceRecord(
            trace_type="EPOCH_ADVANCEMENT",
            trace_seq=self._next_trace_seq(),
            details={
                "event_id": event.event_id,
                "old_epoch": self.state.current_epoch,
                "new_epoch": event.new_epoch,
            },
        ))

        # Activate pending authorities (per §7.3)
        activated_ids = []
        for auth_id, auth in list(self.state.pending_authorities.items()):
            # Pending authorities become ACTIVE at epoch boundary
            auth.status = AuthorityStatus.ACTIVE
            self.state.authorities[auth_id] = auth
            del self.state.pending_authorities[auth_id]
            activated_ids.append(auth_id)

            # Update scope index
            scope = auth.resource_scope
            if scope not in self.scope_index:
                self.scope_index[scope] = []
            self.scope_index[scope].append(auth_id)

        if activated_ids:
            traces.append(TraceRecord(
                trace_type="PENDING_AUTHORITIES_ACTIVATED",
                trace_seq=self._next_trace_seq(),
                details={
                    "activated_ids": sorted(activated_ids),
                    "epoch": event.new_epoch,
                },
            ))

        # Update epoch
        self.state.current_epoch = event.new_epoch

        # Eager expiry: find authorities with expiry_epoch < current_epoch
        expired_ids = []
        for auth_id, auth in self.state.authorities.items():
            if auth.status == AuthorityStatus.ACTIVE:
                if auth.expiry_epoch < self.state.current_epoch:
                    expired_ids.append(auth_id)

        # Process expirations in canonical order
        for auth_id in sorted(expired_ids):
            auth = self.state.authorities[auth_id]
            auth.status = AuthorityStatus.EXPIRED
            auth.expiry_metadata = ExpiryMetadata(
                expiry_epoch=auth.expiry_epoch,
                transition_epoch=self.state.current_epoch,
                triggering_event_id=event.event_id,
            )

            # Remove from scope index
            scope = auth.resource_scope
            if scope in self.scope_index and auth_id in self.scope_index[scope]:
                self.scope_index[scope].remove(auth_id)

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

            # Update conflict status
            self._update_conflict_status_for_authority(auth_id)

        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
        )

    def _update_conflict_status_for_authority(self, auth_id: str) -> None:
        """Update conflict status when authority becomes non-ACTIVE."""
        for conflict in self.state.conflicts.values():
            if auth_id in conflict.authority_ids:
                if conflict.status == ConflictStatus.OPEN_BINDING:
                    conflict.status = ConflictStatus.OPEN_NONBINDING

    # =========================================================================
    # Authority Injection (Setup only)
    # =========================================================================

    def _process_authority_injection(
        self, event: AuthorityInjectionEvent
    ) -> KernelResult:
        """Process authority injection (setup only)."""
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

        # Check for reserved AAV bits
        if aav_has_reserved_bits(authority.aav):
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.AAV_RESERVED_BIT_SET,
            )

        # Consume event index
        self._next_event_index()

        # Mark as used
        self.used_authority_ids.add(authority.authority_id)

        # Add to state
        self.state.authorities[authority.authority_id] = authority

        # Update scope index if ACTIVE
        if authority.status == AuthorityStatus.ACTIVE:
            scope = authority.resource_scope
            if scope not in self.scope_index:
                self.scope_index[scope] = []
            self.scope_index[scope].append(authority.authority_id)

        traces.append(TraceRecord(
            trace_type="AUTHORITY_INJECTION",
            trace_seq=self._next_trace_seq(),
            details={
                "event_index": self.event_index,
                "authority_id": authority.authority_id,
                "aav": authority.aav,
                "resource_scope": authority.resource_scope,
            },
        ))

        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            outputs=[],
            traces=traces,
            state=self.state,
        )

    # =========================================================================
    # Authority Renewal (from VIII-3)
    # =========================================================================

    def _process_authority_renewal(
        self, event: AuthorityRenewalRequest
    ) -> KernelResult:
        """Process authority renewal (inherited from VIII-3)."""
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

        # Check for reserved AAV bits
        if aav_has_reserved_bits(new_authority.aav):
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.AAV_RESERVED_BIT_SET,
            )

        # Consume instructions
        self._consume_instructions(C_LOOKUP + C_STATE_WRITE)

        # Mark as used
        self.used_authority_ids.add(new_authority.authority_id)

        # Add to state (immediately ACTIVE for renewal)
        self.state.authorities[new_authority.authority_id] = new_authority

        # Update scope index
        if new_authority.status == AuthorityStatus.ACTIVE:
            scope = new_authority.resource_scope
            if scope not in self.scope_index:
                self.scope_index[scope] = []
            self.scope_index[scope].append(new_authority.authority_id)

        self.state.state_id = compute_state_id(self.state)

        outputs.append(KernelOutput(
            output_type=OutputType.AUTHORITY_RENEWED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "new_authority_id": new_authority.authority_id,
                "prior_authority_id": event.prior_authority_id,
                "resource_scope": new_authority.resource_scope,
                "aav": new_authority.aav,
                "expiry_epoch": new_authority.expiry_epoch,
            },
        ))

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
        )

    # =========================================================================
    # Governance Actions
    # =========================================================================

    def _max_governance_action_cost(self, event: GovernanceActionRequest) -> int:
        """
        Compute maximum instruction cost for a governance action.

        Per prereg §6.4, we check upfront to ensure atomicity (no partial state).
        This is a conservative upper bound.
        """
        n_initiators = len(event.initiator_ids)

        # Base cost: lookup initiators + AST rule
        cost = C_LOOKUP * n_initiators + C_AST_RULE

        # Admitting authorities check (worst case: all initiators admit)
        cost += C_AAV_WORD * n_initiators

        # Conflict detection (worst case: conflict occurs)
        cost += C_CONFLICT_UPDATE

        if event.action_type == GovernanceActionType.DESTROY_AUTHORITY:
            # State write for destruction
            cost += C_STATE_WRITE
        else:  # CREATE_AUTHORITY
            # Non-amplification check
            cost += C_AAV_WORD
            # State write for creation
            cost += C_STATE_WRITE

        return cost

    def _process_governance_action(
        self, event: GovernanceActionRequest
    ) -> KernelResult:
        """
        Process governance action per prereg §8.

        1. Check instruction budget (upfront, for atomicity per §6.4)
        2. Find admitting authorities
        3. Check for conflicts
        4. Execute if admissible
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Upfront budget check for atomicity per §6.4
        max_cost = self._max_governance_action_cost(event)
        if self.instructions.would_exceed(max_cost):
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.BOUND_EXHAUSTED,
                {"instructions_consumed": self.instructions.consumed, "action_cost": max_cost}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Consume base instruction cost (abort if would exceed per §6.4)
        if not self._consume_instructions(C_LOOKUP * len(event.initiator_ids) + C_AST_RULE):
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.BOUND_EXHAUSTED,
                {"instructions_consumed": self.instructions.consumed}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Determine transformation type ID
        if event.action_type == GovernanceActionType.DESTROY_AUTHORITY:
            transform_id = TRANSFORM_DESTROY_AUTHORITY
        else:
            transform_id = TRANSFORM_CREATE_AUTHORITY

        # Find target scope for admissibility check
        if event.action_type == GovernanceActionType.DESTROY_AUTHORITY:
            target_id = event.params.get("target_authority_id")
            if target_id not in self.state.authorities:
                outputs.append(self._emit_refusal(
                    event.event_id,
                    RefusalReason.AUTHORITY_NOT_FOUND,
                    {"target_authority_id": target_id}
                ))
                return KernelResult(outputs=outputs, traces=traces, state=self.state)

            target = self.state.authorities[target_id]
            if target.status != AuthorityStatus.ACTIVE:
                outputs.append(self._emit_refusal(
                    event.event_id,
                    RefusalReason.TARGET_NOT_ACTIVE,
                    {"target_authority_id": target_id, "status": target.status.value}
                ))
                return KernelResult(outputs=outputs, traces=traces, state=self.state)

            target_scope = target.resource_scope
        else:
            # CREATE_AUTHORITY: scope comes from params
            target_scope = event.params.get("resource_scope")

        # Find ACTIVE authorities that:
        # 1. Are in initiator set
        # 2. Have AAV bit for this governance action
        # 3. Cover target scope (byte-equality)
        admitting_authorities = []
        for init_id in event.initiator_ids:
            if init_id not in self.state.authorities:
                continue
            auth = self.state.authorities[init_id]
            if auth.status != AuthorityStatus.ACTIVE:
                continue
            if not aav_has_bit(auth.aav, transform_id):
                continue
            # Scope check: byte-equality per §8.0
            if auth.resource_scope == target_scope:
                admitting_authorities.append(auth)

        self._consume_instructions(C_AAV_WORD * len(admitting_authorities))

        # Check: at least one admitting authority
        if not admitting_authorities:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.NO_AUTHORITY,
                {"transform_id": transform_id, "target_scope": target_scope}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check for structural conflict:
        # All ACTIVE authorities covering target scope must agree
        # (per §8.1 - structural agreement means same AAV bit for this action)
        # Note: For DESTROY_AUTHORITY, exclude the target itself from conflict check
        conflicting_authorities = []
        covering_authorities = self.scope_index.get(target_scope, [])
        target_id = event.params.get("target_authority_id") if event.action_type == GovernanceActionType.DESTROY_AUTHORITY else None
        for auth_id in covering_authorities:
            # Skip the target being destroyed - it's not a governance participant
            if auth_id == target_id:
                continue
            auth = self.state.authorities[auth_id]
            if auth.status != AuthorityStatus.ACTIVE:
                continue
            # Does this authority have the AAV bit?
            has_bit = aav_has_bit(auth.aav, transform_id)
            # Structural conflict: some admit (have bit) and some don't
            if not has_bit:
                conflicting_authorities.append(auth)

        if conflicting_authorities:
            # Register conflict
            conflict_id = self._next_conflict_id()
            all_participants = frozenset(
                [a.authority_id for a in admitting_authorities] +
                [a.authority_id for a in conflicting_authorities]
            )
            conflict = ConflictRecord(
                conflict_id=conflict_id,
                epoch_detected=self.state.current_epoch,
                resource_scope=target_scope,
                authority_ids=all_participants,
                status=ConflictStatus.OPEN_BINDING,
                governance_action_type=event.action_type,
            )
            self.state.conflicts[conflict_id] = conflict
            self._consume_instructions(C_CONFLICT_UPDATE)

            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.CONFLICT_BLOCKS,
                {"conflict_id": conflict_id}
            ))

            self.state.state_id = compute_state_id(self.state)

            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Execute governance action
        if event.action_type == GovernanceActionType.DESTROY_AUTHORITY:
            result = self._execute_destroy_authority(event, admitting_authorities)
        else:
            result = self._execute_create_authority(event, admitting_authorities)

        outputs.extend(result.outputs)
        traces.extend(result.traces)

        return KernelResult(
            outputs=outputs,
            traces=traces,
            state=self.state,
            failure=result.failure,
        )

    def _execute_destroy_authority(
        self,
        event: GovernanceActionRequest,
        admitting: list[AuthorityRecord],
    ) -> KernelResult:
        """Execute DESTROY_AUTHORITY governance action."""
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        target_id = event.params.get("target_authority_id")
        target = self.state.authorities[target_id]

        # Transition to VOID
        target.status = AuthorityStatus.VOID
        target.destruction_metadata = DestructionMetadata(
            destruction_event_id=event.event_id,
            authorizer_ids=[a.authority_id for a in admitting],
            destruction_epoch=self.state.current_epoch,
        )

        # Remove from scope index
        scope = target.resource_scope
        if scope in self.scope_index and target_id in self.scope_index[scope]:
            self.scope_index[scope].remove(target_id)

        self._consume_instructions(C_STATE_WRITE)

        # Update conflict status
        self._update_conflict_status_for_authority(target_id)

        self.state.state_id = compute_state_id(self.state)

        outputs.append(KernelOutput(
            output_type=OutputType.AUTHORITY_DESTROYED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "authority_id": target_id,
                "destruction_epoch": self.state.current_epoch,
                "authorizer_ids": sorted([a.authority_id for a in admitting]),
            },
        ))

        traces.append(TraceRecord(
            trace_type="GOVERNANCE_DESTROY",
            trace_seq=self._next_trace_seq(),
            details={
                "target_id": target_id,
                "admitting_ids": sorted([a.authority_id for a in admitting]),
                "event_id": event.event_id,
            },
        ))

        return KernelResult(outputs=outputs, traces=traces, state=self.state)

    def _execute_create_authority(
        self,
        event: GovernanceActionRequest,
        admitting: list[AuthorityRecord],
    ) -> KernelResult:
        """
        Execute CREATE_AUTHORITY governance action per prereg §8.2 and §8.3.

        Checks:
        1. Non-amplification: new AAV ⊆ union(admitting AAVs)
        2. Scope containment: scope_basis_authority in admitting set,
           new scope == basis scope
        3. Reserved bits: no reserved AAV bits set
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        params = event.params
        new_id = params.get("new_authority_id")
        new_scope = params.get("resource_scope")
        scope_basis_id = params.get("scope_basis_authority_id")
        new_aav = params.get("aav")
        new_expiry = params.get("expiry_epoch")
        lineage = params.get("lineage")

        # Check AuthorityID uniqueness
        if new_id in self.used_authority_ids:
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.AUTHORITY_ID_REUSE,
            )

        # Check reserved AAV bits per §5.1
        if aav_has_reserved_bits(new_aav):
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.AAV_RESERVED_BIT_SET,
            )

        # Non-amplification check per §8.2
        admitting_aavs = [a.aav for a in admitting]
        union_aav = aav_union(admitting_aavs)
        if not aav_is_subset(new_aav, union_aav):
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.AMPLIFICATION_BLOCKED,
                {
                    "requested_aav": new_aav,
                    "union_aav": union_aav,
                    "forbidden_bits": new_aav & ~union_aav,
                }
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        self._consume_instructions(C_AAV_WORD)

        # Scope containment check per §8.3
        # 1. scope_basis_authority_id must be in admitting set
        basis_in_admitting = any(a.authority_id == scope_basis_id for a in admitting)
        if not basis_in_admitting:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.SCOPE_NOT_COVERED,
                {"scope_basis_authority_id": scope_basis_id, "sub_reason": "basis_not_admitting"}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # 2. new scope must exactly equal basis scope
        basis_auth = self.state.authorities[scope_basis_id]
        if new_scope != basis_auth.resource_scope:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.SCOPE_NOT_COVERED,
                {
                    "requested_scope": new_scope,
                    "basis_scope": basis_auth.resource_scope,
                    "sub_reason": "scope_mismatch",
                }
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Create new authority (PENDING per §7.3)
        new_authority = AuthorityRecord(
            authority_id=new_id,
            holder_id=params.get("holder_id", "GOVERNANCE_CREATED"),
            resource_scope=new_scope,
            status=AuthorityStatus.PENDING,  # Not ACTIVE until next epoch
            aav=new_aav,
            start_epoch=self.state.current_epoch + 1,  # Activates next epoch
            expiry_epoch=new_expiry,
            creation_metadata=CreationMetadata(
                creation_epoch=self.state.current_epoch,
                admitting_authority_ids=[a.authority_id for a in admitting],
                lineage=lineage,
            ),
        )

        # Mark as used
        self.used_authority_ids.add(new_id)

        # Add to pending (per §7.3: not ACTIVE until next epoch)
        self.state.pending_authorities[new_id] = new_authority

        self._consume_instructions(C_STATE_WRITE)

        self.state.state_id = compute_state_id(self.state)

        outputs.append(KernelOutput(
            output_type=OutputType.AUTHORITY_CREATED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "new_authority_id": new_id,
                "resource_scope": new_scope,
                "aav": new_aav,
                "expiry_epoch": new_expiry,
                "lineage": lineage,
                "admitting_authorities": sorted([a.authority_id for a in admitting]),
                "creation_epoch": self.state.current_epoch,
                "activation_epoch": self.state.current_epoch + 1,
            },
        ))

        traces.append(TraceRecord(
            trace_type="GOVERNANCE_CREATE",
            trace_seq=self._next_trace_seq(),
            details={
                "new_id": new_id,
                "new_aav": new_aav,
                "union_aav": union_aav,
                "admitting_ids": sorted([a.authority_id for a in admitting]),
                "pending_until_epoch": self.state.current_epoch + 1,
            },
        ))

        return KernelResult(outputs=outputs, traces=traces, state=self.state)

    # =========================================================================
    # Non-Governance Actions
    # =========================================================================

    def _process_action_request(
        self, event: ActionRequestEvent
    ) -> KernelResult:
        """Process non-governance action request."""
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Consume instructions
        self._consume_instructions(C_LOOKUP + C_AST_RULE)

        if self.instructions.is_exhausted():
            outputs.append(self._emit_refusal(
                event.request_id,
                RefusalReason.BOUND_EXHAUSTED,
                {}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # If in deadlock, refuse all actions
        if self.state.deadlock:
            outputs.append(self._emit_refusal(
                event.request_id,
                RefusalReason.DEADLOCK_STATE,
                {"deadlock_cause": self.state.deadlock_cause.value if self.state.deadlock_cause else None}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Find admitting authority (scope + EXECUTE permission)
        admitting = None
        for auth in self.state.get_active_authorities():
            if auth.resource_scope == event.resource_scope:
                if aav_has_bit(auth.aav, TRANSFORM_EXECUTE):
                    admitting = auth
                    break

        if not admitting:
            outputs.append(self._emit_refusal(
                event.request_id,
                RefusalReason.NO_AUTHORITY,
                {"resource_scope": event.resource_scope}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Execute
        self._consume_instructions(C_STATE_WRITE)
        self.state.state_id = compute_state_id(self.state)

        outputs.append(KernelOutput(
            output_type=OutputType.ACTION_EXECUTED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "request_id": event.request_id,
                "resource_scope": event.resource_scope,
                "transformation_type": event.transformation_type,
                "authorizing_authority": admitting.authority_id,
            },
        ))

        return KernelResult(outputs=outputs, traces=traces, state=self.state)

    # =========================================================================
    # Deadlock Detection
    # =========================================================================

    def _check_and_emit_deadlock(
        self,
        existing_outputs: list[KernelOutput],
        traces: list[TraceRecord],
    ) -> Optional[KernelResult]:
        """Check for deadlock conditions and emit appropriate output."""

        active_authorities = self.state.get_active_authorities()
        has_active = len(active_authorities) > 0
        has_open_binding = len(self.state.get_open_binding_conflicts()) > 0
        has_conflict_history = self.state.has_conflict_history()

        # Determine deadlock cause
        new_deadlock_cause = None
        if not has_active and has_conflict_history:
            new_deadlock_cause = DeadlockCause.MIXED
        elif not has_active:
            new_deadlock_cause = DeadlockCause.EMPTY_AUTHORITY
        elif has_open_binding:
            new_deadlock_cause = DeadlockCause.CONFLICT

        if new_deadlock_cause is None:
            # No deadlock - if was deadlocked, stay deadlocked (no auto-resolution)
            return None

        outputs: list[KernelOutput] = []

        if not self.state.deadlock:
            # First entry into deadlock
            self.state.deadlock = True
            self.state.deadlock_cause = new_deadlock_cause
            self._consume_instructions(C_CONFLICT_UPDATE)

            self.state.state_id = compute_state_id(self.state)

            outputs.append(KernelOutput(
                output_type=OutputType.DEADLOCK_DECLARED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "deadlock_cause": new_deadlock_cause.value,
                    "active_authority_count": len(active_authorities),
                    "open_binding_conflict_count": len(self.state.get_open_binding_conflicts()),
                },
            ))
        else:
            # Already in deadlock - persist
            outputs.append(KernelOutput(
                output_type=OutputType.DEADLOCK_PERSISTED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "deadlock_cause": self.state.deadlock_cause.value if self.state.deadlock_cause else None,
                },
            ))

        return KernelResult(outputs=outputs, traces=[], state=self.state)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _emit_refusal(
        self,
        event_id: str,
        reason: RefusalReason,
        details: dict,
    ) -> KernelOutput:
        """Emit ACTION_REFUSED output."""
        self.state.state_id = compute_state_id(self.state)
        return KernelOutput(
            output_type=OutputType.ACTION_REFUSED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "event_id": event_id,
                "reason": reason.value,
                **details,
            },
        )
