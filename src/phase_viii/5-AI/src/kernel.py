"""
AI-VIII-5 Kernel Core

Authority Injection kernel per VIII-5 Spec v0.1.

Extends VIII-4 GTKernel with:
- Authority injection processing
- Content-addressed AuthorityID computation
- VOID lineage validation
- Duplicate detection (idempotent)
- AUTHORITY_INJECTED output emission
- Epoch consistency enforcement

Key constraints (all inherited + VIII-5 specific):
- No kernel-initiated injection
- No privilege escalation
- Content-addressed identity (no user-assigned IDs)
- VOID lineage for all injected authorities
- Injection enters PENDING, activates next epoch
- Duplicate injection = idempotent (emit AUTHORITY_INJECTED, no state change)
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
    C_HASH,
    C_TRACE_APPEND,
    C_INJECT,
    B_EPOCH_INSTR,
    # VOID lineage
    VOID_LINEAGE,
)
from canonical import compute_state_id, compute_authority_id, governance_action_identity


@dataclass
class KernelResult:
    """Result of processing an event or step batch."""
    outputs: list[KernelOutput]
    traces: list[TraceRecord]
    state: AuthorityState
    failure: Optional[FailureCode] = None


class AIKernel:
    """
    AI-VIII-5 Authority Injection Kernel.

    Extends VIII-4 GTKernel with:
    - Authority injection with content-addressed IDs
    - VOID lineage enforcement
    - Duplicate detection (idempotent)
    - Epoch consistency enforcement
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
        self.epoch_advanced_this_batch = False  # Track duplicate epoch advances

        # Track all AuthorityIDs ever used (for uniqueness check in CREATE_AUTHORITY)
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
          1. Injections (VIII-5)
          2. Renewals
          3. Authority Destructions (DESTROY_AUTHORITY)
          4. Authority Creations (CREATE_AUTHORITY)
          5. Non-Governance Actions
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Reset per-batch state
        self.epoch_advanced_this_batch = False

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

            # Check for deadlock after epoch advancement
            deadlock_result = self._check_and_emit_deadlock(outputs, traces)
            if deadlock_result:
                outputs.extend(deadlock_result.outputs)
                traces.extend(deadlock_result.traces)

        # Separate Phase 2 events by type
        injections = [e for e in phase2_events if isinstance(e, AuthorityInjectionEvent)]
        renewals = [e for e in phase2_events if isinstance(e, AuthorityRenewalRequest)]
        governance = [e for e in phase2_events if isinstance(e, GovernanceActionRequest)]
        actions = [e for e in phase2_events if isinstance(e, ActionRequestEvent)]

        # Sort injections by (source_id, authority_id) per prereg §7.3
        # Note: authority_id may not be set yet, use capability core hash for ordering
        def injection_order_key(e: AuthorityInjectionEvent) -> tuple:
            core = e.authority_record.get_capability_core()
            derived_id = compute_authority_id(core)
            return (e.source_id, derived_id)

        injections = sorted(injections, key=injection_order_key)

        # Sort governance actions by type (DESTROY first, then CREATE)
        destructions = sorted(
            [g for g in governance if g.action_type == GovernanceActionType.DESTROY_AUTHORITY],
            key=lambda g: governance_action_identity(g.epoch, g.initiator_ids, g.target_ids, g.action_type.value, g.params)
        )
        creations = sorted(
            [g for g in governance if g.action_type == GovernanceActionType.CREATE_AUTHORITY],
            key=lambda g: governance_action_identity(g.epoch, g.initiator_ids, g.target_ids, g.action_type.value, g.params)
        )

        # Sub-phase 1: Injections (VIII-5)
        for event in injections:
            if self.instructions.would_exceed(C_INJECT):
                # Refuse remaining injections
                outputs.append(self._emit_refusal(
                    event.event_id,
                    RefusalReason.BOUND_EXHAUSTED,
                    {"remaining_injections": len(injections)}
                ))
                continue

            result = self._process_injection(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

        # Check for deadlock after injections (state may have changed)
        deadlock_result = self._check_and_emit_deadlock(outputs, traces)
        if deadlock_result:
            outputs.extend(deadlock_result.outputs)
            traces.extend(deadlock_result.traces)

        # Sub-phase 2: Renewals
        for event in renewals:
            result = self._process_authority_renewal(event)
            outputs.extend(result.outputs)
            traces.extend(result.traces)
            if result.failure:
                return result

        # Sub-phase 3: Authority Destructions
        for event in destructions:
            if self.instructions.is_exhausted():
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

        # Sub-phase 4: Authority Creations
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

        # Sub-phase 5: Non-Governance Actions
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

        Order per prereg (binding):
        1. Check for duplicate epoch advancement
        2. Validate newEpoch > currentEpoch (monotonicity)
        3. Update currentEpoch
        4. Apply eager expirations (before activation)
        5. Activate pending authorities
        6. Update conflict statuses
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Check for duplicate epoch advancement per prereg §7.1
        if self.epoch_advanced_this_batch:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.DUPLICATE_EPOCH_ADVANCE,
                {"current_epoch": self.state.current_epoch}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Validate monotonicity
        if event.new_epoch <= self.state.current_epoch:
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.TEMPORAL_REGRESSION,
            )

        self.epoch_advanced_this_batch = True

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

        # Update epoch first (needed for expiry check)
        self.state.current_epoch = event.new_epoch

        # Eager expiry BEFORE activation per prereg §7.1 order
        # Find authorities with expiry_epoch < current_epoch
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

        # Activate pending authorities AFTER expiry per prereg §7.1
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
    # Authority Injection (VIII-5)
    # =========================================================================

    def _process_injection(
        self, event: AuthorityInjectionEvent
    ) -> KernelResult:
        """
        Process authority injection per prereg §8.

        Steps per §8.1:
        1. Validate AuthorityRecord schema (AST v0.2)
        2. Enforce reserved-field constraints (AAV bits 3-15 must be 0)
        3. Verify creation_metadata.lineage == "VOID"
        4. Compute content-addressed AuthorityID
        5. Check for duplicate (AuthorityID already exists)
        6. Verify budget sufficiency for atomic completion
        7. If new: register injected authority as PENDING
        8. If duplicate: no state change
        9. Emit appropriate outputs
        10. Preserve all existing conflicts
        """
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        authority = deepcopy(event.authority_record)

        # === Admissibility Checks per §8.2 ===

        # Check 1: Schema validation (simplified - check required fields)
        if not self._validate_injection_schema(authority):
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.SCHEMA_INVALID,
                {"reason": "Missing or invalid required fields"}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check 2: Reserved AAV bits
        if aav_has_reserved_bits(authority.aav):
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.SCHEMA_INVALID,
                {"reason": "Reserved AAV bits set", "aav": authority.aav}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check 3: VOID lineage per §4.3
        if authority.creation_metadata is None:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.LINEAGE_INVALID,
                {"reason": "Missing creation_metadata"}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        if authority.creation_metadata.lineage != VOID_LINEAGE:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.LINEAGE_INVALID,
                {"expected": VOID_LINEAGE, "actual": authority.creation_metadata.lineage}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check 4: Epoch consistency per §5.1
        if event.injection_epoch != self.state.current_epoch:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.EPOCH_MISMATCH,
                {"injection_epoch": event.injection_epoch, "current_epoch": self.state.current_epoch}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check 5: Source ID not empty
        if not event.source_id or event.source_id.strip() == "":
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.SCHEMA_INVALID,
                {"reason": "Empty source_id"}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # === Content-Addressed ID Computation per §4.2 ===

        # Compute capability core
        capability_core = authority.get_capability_core()
        derived_id = compute_authority_id(capability_core)

        # Check per §8.1 AuthorityID Input Handling:
        # If non-empty AuthorityID supplied and differs from derived, refuse with HASH_MISMATCH
        if authority.authority_id and authority.authority_id != derived_id:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.HASH_MISMATCH,
                {"supplied_id": authority.authority_id, "derived_id": derived_id}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Overwrite with derived ID
        authority.authority_id = derived_id

        # === Budget Check per §6.4 ===

        if not self._consume_instructions(C_INJECT):
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.BOUND_EXHAUSTED,
                {"instructions_consumed": self.instructions.consumed, "injection_cost": C_INJECT}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # === Duplicate Detection per §8.3 ===

        is_duplicate = derived_id in self.state.authorities or derived_id in self.state.pending_authorities

        if is_duplicate:
            # Idempotent: emit AUTHORITY_INJECTED but no state change
            self.state.state_id = compute_state_id(self.state)
            outputs.append(KernelOutput(
                output_type=OutputType.AUTHORITY_INJECTED,
                event_index=self._next_event_index(),
                state_hash=self.state.state_id,
                details={
                    "authority_id": derived_id,
                    "source_id": event.source_id,
                    "injection_epoch": event.injection_epoch,
                    "is_duplicate": True,
                    "resource_scope": authority.resource_scope,
                    "aav": authority.aav,
                    "expiry_epoch": authority.expiry_epoch,
                },
            ))

            traces.append(TraceRecord(
                trace_type="INJECTION_DUPLICATE",
                trace_seq=self._next_trace_seq(),
                details={
                    "event_id": event.event_id,
                    "authority_id": derived_id,
                    "source_id": event.source_id,
                },
            ))

            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # === New Injection: Register as PENDING per §7.2 ===

        # Set status to PENDING (activates next epoch)
        authority.status = AuthorityStatus.PENDING
        authority.start_epoch = self.state.current_epoch + 1

        # Update creation_metadata with injection details
        authority.creation_metadata.creation_epoch = self.state.current_epoch
        authority.creation_metadata.source_id = event.source_id

        # Add to pending authorities
        self.state.pending_authorities[derived_id] = authority

        # Track used ID
        self.used_authority_ids.add(derived_id)

        # Update state hash
        self.state.state_id = compute_state_id(self.state)

        # Emit AUTHORITY_INJECTED
        outputs.append(KernelOutput(
            output_type=OutputType.AUTHORITY_INJECTED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details={
                "authority_id": derived_id,
                "source_id": event.source_id,
                "injection_epoch": event.injection_epoch,
                "is_duplicate": False,
                "resource_scope": authority.resource_scope,
                "aav": authority.aav,
                "expiry_epoch": authority.expiry_epoch,
            },
        ))

        traces.append(TraceRecord(
            trace_type="INJECTION_NEW",
            trace_seq=self._next_trace_seq(),
            details={
                "event_id": event.event_id,
                "authority_id": derived_id,
                "source_id": event.source_id,
                "capability_core": capability_core,
                "activation_epoch": self.state.current_epoch + 1,
            },
        ))

        return KernelResult(outputs=outputs, traces=traces, state=self.state)

    def _validate_injection_schema(self, authority: AuthorityRecord) -> bool:
        """Validate AuthorityRecord has required fields for injection."""
        # Required fields for capability core
        if authority.holder_id is None or authority.holder_id == "":
            return False
        if authority.resource_scope is None or authority.resource_scope == "":
            return False
        if authority.aav is None:
            return False
        if authority.expiry_epoch is None:
            return False
        return True

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
    # Governance Actions (from VIII-4)
    # =========================================================================

    def _max_governance_action_cost(self, event: GovernanceActionRequest) -> int:
        """Compute maximum instruction cost for a governance action."""
        n_initiators = len(event.initiator_ids)
        cost = C_LOOKUP * n_initiators + C_AST_RULE
        cost += C_AAV_WORD * n_initiators
        cost += C_CONFLICT_UPDATE

        if event.action_type == GovernanceActionType.DESTROY_AUTHORITY:
            cost += C_STATE_WRITE
        else:  # CREATE_AUTHORITY
            cost += C_AAV_WORD
            cost += C_STATE_WRITE

        return cost

    def _process_governance_action(
        self, event: GovernanceActionRequest
    ) -> KernelResult:
        """Process governance action per VIII-4."""
        outputs: list[KernelOutput] = []
        traces: list[TraceRecord] = []

        # Upfront budget check
        max_cost = self._max_governance_action_cost(event)
        if self.instructions.would_exceed(max_cost):
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.BOUND_EXHAUSTED,
                {"instructions_consumed": self.instructions.consumed, "action_cost": max_cost}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Consume base cost
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

        # Find target scope
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
            target_scope = event.params.get("resource_scope")

        # Find admitting authorities
        admitting_authorities = []
        for init_id in event.initiator_ids:
            if init_id not in self.state.authorities:
                continue
            auth = self.state.authorities[init_id]
            if auth.status != AuthorityStatus.ACTIVE:
                continue
            if not aav_has_bit(auth.aav, transform_id):
                continue
            if auth.resource_scope == target_scope:
                admitting_authorities.append(auth)

        self._consume_instructions(C_AAV_WORD * len(admitting_authorities))

        if not admitting_authorities:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.NO_AUTHORITY,
                {"transform_id": transform_id, "target_scope": target_scope}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        # Check for structural conflict
        conflicting_authorities = []
        covering_authorities = self.scope_index.get(target_scope, [])
        target_id = event.params.get("target_authority_id") if event.action_type == GovernanceActionType.DESTROY_AUTHORITY else None
        for auth_id in covering_authorities:
            if auth_id == target_id:
                continue
            auth = self.state.authorities[auth_id]
            if auth.status != AuthorityStatus.ACTIVE:
                continue
            has_bit = aav_has_bit(auth.aav, transform_id)
            if not has_bit:
                conflicting_authorities.append(auth)

        if conflicting_authorities:
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

        target.status = AuthorityStatus.VOID
        target.destruction_metadata = DestructionMetadata(
            destruction_event_id=event.event_id,
            authorizer_ids=[a.authority_id for a in admitting],
            destruction_epoch=self.state.current_epoch,
        )

        scope = target.resource_scope
        if scope in self.scope_index and target_id in self.scope_index[scope]:
            self.scope_index[scope].remove(target_id)

        self._consume_instructions(C_STATE_WRITE)
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
        """Execute CREATE_AUTHORITY governance action per VIII-4."""
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

        # Check reserved AAV bits
        if aav_has_reserved_bits(new_aav):
            return KernelResult(
                outputs=[],
                traces=[],
                state=self.state,
                failure=FailureCode.AAV_RESERVED_BIT_SET,
            )

        # Non-amplification check
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

        # Scope containment check
        basis_in_admitting = any(a.authority_id == scope_basis_id for a in admitting)
        if not basis_in_admitting:
            outputs.append(self._emit_refusal(
                event.event_id,
                RefusalReason.SCOPE_NOT_COVERED,
                {"scope_basis_authority_id": scope_basis_id, "sub_reason": "basis_not_admitting"}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

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

        # Create new authority (PENDING)
        new_authority = AuthorityRecord(
            authority_id=new_id,
            holder_id=params.get("holder_id", "GOVERNANCE_CREATED"),
            resource_scope=new_scope,
            status=AuthorityStatus.PENDING,
            aav=new_aav,
            start_epoch=self.state.current_epoch + 1,
            expiry_epoch=new_expiry,
            creation_metadata=CreationMetadata(
                creation_epoch=self.state.current_epoch,
                lineage=lineage if lineage else scope_basis_id,  # Use basis as lineage
                admitting_authority_ids=[a.authority_id for a in admitting],
            ),
        )

        self.used_authority_ids.add(new_id)
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

        self._consume_instructions(C_LOOKUP + C_AST_RULE)

        if self.instructions.is_exhausted():
            outputs.append(self._emit_refusal(
                event.request_id,
                RefusalReason.BOUND_EXHAUSTED,
                {}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

        if self.state.deadlock:
            outputs.append(self._emit_refusal(
                event.request_id,
                RefusalReason.DEADLOCK_STATE,
                {"deadlock_cause": self.state.deadlock_cause.value if self.state.deadlock_cause else None}
            ))
            return KernelResult(outputs=outputs, traces=traces, state=self.state)

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
        """
        Check for deadlock conditions and emit appropriate output.

        Per prereg §9.2: deadlock persists until admissibility changes structurally.
        When ACTIVE authorities appear and no open binding conflicts exist,
        deadlock may be resolved explicitly.
        """

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

        outputs: list[KernelOutput] = []

        if new_deadlock_cause is None:
            # No deadlock condition exists
            if self.state.deadlock:
                # Clear deadlock - admissibility has changed structurally (per §9.2)
                self.state.deadlock = False
                self.state.deadlock_cause = None
                self.state.state_id = compute_state_id(self.state)
                # No explicit output for deadlock resolution per prereg §10
                # (Condition A success criterion #5: "Deadlock resolution (if any) is explicit and lawful")
                # The trace captures the state change
            return None

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
        # Merge details but ensure reason is not overwritten
        merged_details = {
            "event_id": event_id,
            "reason": reason.value,
        }
        # Add details but rename 'reason' key if present to avoid overwriting
        for k, v in details.items():
            if k == "reason":
                merged_details["detail_message"] = v
            else:
                merged_details[k] = v
        return KernelOutput(
            output_type=OutputType.ACTION_REFUSED,
            event_index=self._next_event_index(),
            state_hash=self.state.state_id,
            details=merged_details,
        )
