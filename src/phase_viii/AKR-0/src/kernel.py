"""
AKR-0 Kernel Core

Authority-constrained execution kernel per AKR Spec v0.1.
Implements admissibility evaluation, conflict detection, transformation handling,
epoch advancement with eager expiry, and gas accounting.
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from copy import deepcopy

from structures import (
    AuthorityRecord,
    AuthorityState,
    AuthorityStatus,
    ConflictRecord,
    ConflictStatus,
    TransformationType,
    OutputType,
    DeadlockType,
    FailureCode,
    KernelOutput,
    GasAccounting,
    EpochTickEvent,
    AuthorityInjectionEvent,
    TransformationRequestEvent,
    ActionRequestEvent,
    ScopeElement,
)
from canonical import (
    compute_state_id,
    compute_conflict_id,
    compute_authority_id,
    canonical_json,
    sha256_hex,
)


# Gas costs per Q22
GAS_HASH = 50
GAS_COMPARE = 1
GAS_SET_MEM = 5
GAS_SCAN_AR = 10
GAS_UPDATE = 20
GAS_LOG = 10

# Gas budgets per Q4
GAS_ACTION_EVAL = 50_000
GAS_TRANSFORM = 100_000
GAS_EPOCH_ADVANCE = 200_000


@dataclass
class KernelResult:
    """Result of processing an event."""
    output: KernelOutput
    state: AuthorityState
    failure: Optional[FailureCode] = None
    deadlock: Optional[DeadlockType] = None


class AKRKernel:
    """
    AKR-0 Authority Kernel.

    Invariant: No action, transformation, or refusal may occur unless
    attributable to explicit authority state transition.
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
                authorities=[],
                conflicts=[],
            )
            self.state.state_id = compute_state_id(self.state)
        else:
            self.state = initial_state

        self.event_index = 0
        self.gas = GasAccounting(budget=0, consumed=0)

        # Scope index for efficient conflict detection
        self._rebuild_scope_index()

    def _rebuild_scope_index(self) -> None:
        """Build index from scope element to authority IDs."""
        self.scope_index: dict[ScopeElement, list[str]] = {}
        for auth in self.state.authorities:
            if auth.status == AuthorityStatus.ACTIVE:
                for elem in auth.scope:
                    key = tuple(elem)
                    if key not in self.scope_index:
                        self.scope_index[key] = []
                    self.scope_index[key].append(auth.authority_id)

    def process_event(
        self, event: Union[
            EpochTickEvent,
            AuthorityInjectionEvent,
            TransformationRequestEvent,
            ActionRequestEvent,
        ]
    ) -> KernelResult:
        """
        Process a single event and return result.

        Dispatches to appropriate handler based on event type.
        """
        self.event_index += 1

        if isinstance(event, EpochTickEvent):
            return self._process_epoch_tick(event)
        elif isinstance(event, AuthorityInjectionEvent):
            return self._process_authority_injection(event)
        elif isinstance(event, TransformationRequestEvent):
            return self._process_transformation_request(event)
        elif isinstance(event, ActionRequestEvent):
            return self._process_action_request(event)
        else:
            raise ValueError(f"Unknown event type: {type(event)}")

    def _process_epoch_tick(self, event: EpochTickEvent) -> KernelResult:
        """
        Process EPOCH_TICK event.

        1. Validate epoch continuity
        2. Advance epoch
        3. Eager expiry evaluation
        """
        self.gas = GasAccounting(budget=GAS_EPOCH_ADVANCE, consumed=0)

        # Validate epoch continuity per Q34
        if event.target_epoch != self.state.current_epoch + 1:
            return self._make_failure_result(FailureCode.NONDETERMINISTIC_EXECUTION)

        # Advance epoch
        self.state.current_epoch = event.target_epoch
        self._consume_gas(GAS_UPDATE)

        # Eager expiry evaluation per Q5
        expired_ids = []
        for auth in self.state.authorities:
            self._consume_gas(GAS_SCAN_AR)
            if (auth.status == AuthorityStatus.ACTIVE and
                auth.expiry_epoch is not None and
                auth.expiry_epoch <= self.state.current_epoch):
                expired_ids.append(auth.authority_id)

        # Expire authorities (SYSTEM_AUTHORITY transformations)
        for auth_id in expired_ids:
            self._expire_authority(auth_id)

        # Rebuild index after expiries
        if expired_ids:
            self._rebuild_scope_index()

        # Update state ID
        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.AUTHORITY_TRANSFORMED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={"expired_count": len(expired_ids)},
            ),
            state=self.state,
        )

    def _process_authority_injection(
        self, event: AuthorityInjectionEvent
    ) -> KernelResult:
        """
        Process AuthorityInjection event.

        1. Add authority to state
        2. Detect and register conflicts
        """
        self.gas = GasAccounting(budget=GAS_TRANSFORM, consumed=0)

        authority = deepcopy(event.authority)

        # Add to authorities list
        self.state.authorities.append(authority)
        self._consume_gas(GAS_UPDATE)

        # Detect conflicts for each scope element
        new_conflicts = []
        for elem in authority.scope:
            key = tuple(elem)
            self._consume_gas(GAS_SET_MEM)

            if key in self.scope_index:
                existing_ids = self.scope_index[key]
                if existing_ids:
                    # Conflict detected
                    all_ids = existing_ids + [authority.authority_id]
                    conflict = self._register_conflict(
                        scope_elements=[elem],
                        authority_ids=all_ids,
                    )
                    if conflict:
                        new_conflicts.append(conflict)

            # Add to index
            if key not in self.scope_index:
                self.scope_index[key] = []
            self.scope_index[key].append(authority.authority_id)

        # Update state ID
        self.state.state_id = compute_state_id(self.state)

        if new_conflicts:
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.CONFLICT_REGISTERED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={"conflicts": [c.conflict_id for c in new_conflicts]},
                ),
                state=self.state,
            )
        else:
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.AUTHORITY_TRANSFORMED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={"authority_id": authority.authority_id},
                ),
                state=self.state,
            )

    def _process_transformation_request(
        self, event: TransformationRequestEvent
    ) -> KernelResult:
        """
        Process TransformationRequest event.

        1. Check admissibility per Q18
        2. Apply transformation if admissible
        3. Refuse if inadmissible
        """
        self.gas = GasAccounting(budget=GAS_TRANSFORM, consumed=0)

        # Check admissibility
        admissible, reason = self._check_transformation_admissibility(event)

        if not admissible:
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.ACTION_REFUSED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={"reason": reason, "request_id": event.request_id},
                ),
                state=self.state,
            )

        # Apply transformation
        transformation = event.transformation

        if transformation == TransformationType.REVOKE_AUTHORITY.value:
            for auth_id in event.targets.get("authorityIds", []):
                self._revoke_authority(auth_id)
        elif transformation == TransformationType.RESOLVE_CONFLICT.value:
            for conflict_id in event.targets.get("conflictIds", []):
                self._resolve_conflict(conflict_id, event.targets.get("authorityIds", []))
        elif transformation == TransformationType.SUSPEND_AUTHORITY.value:
            for auth_id in event.targets.get("authorityIds", []):
                self._suspend_authority(auth_id)
        elif transformation == TransformationType.RESUME_AUTHORITY.value:
            for auth_id in event.targets.get("authorityIds", []):
                self._resume_authority(auth_id)
        else:
            # NARROW_SCOPE is degenerate per Q28
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.ACTION_REFUSED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={"reason": "DEGENERATE_TRANSFORMATION"},
                ),
                state=self.state,
            )

        self._rebuild_scope_index()
        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.AUTHORITY_TRANSFORMED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={"transformation": transformation},
            ),
            state=self.state,
        )

    def _process_action_request(self, event: ActionRequestEvent) -> KernelResult:
        """
        Process ActionRequest event.

        1. Check admissibility per Q13
        2. Execute if admissible
        3. Refuse if inadmissible
        """
        self.gas = GasAccounting(budget=GAS_ACTION_EVAL, consumed=0)

        # Check admissibility
        admissible, reason = self._check_action_admissibility(event)

        if not admissible:
            self.state.state_id = compute_state_id(self.state)
            return KernelResult(
                output=KernelOutput(
                    output_type=OutputType.ACTION_REFUSED,
                    event_index=self.event_index,
                    state_hash=self.state.state_id,
                    details={"reason": reason, "request_id": event.request_id},
                ),
                state=self.state,
            )

        # Action is admissible - execute (no state change for actions)
        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.ACTION_EXECUTED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={"request_id": event.request_id, "action": event.action},
            ),
            state=self.state,
        )

    def _check_action_admissibility(
        self, event: ActionRequestEvent
    ) -> tuple[bool, str]:
        """
        Check if action is admissible per preregistration §13.

        Admissible iff:
        1. ≥1 ACTIVE authority binds exact scope
        2. Authority's holderId = requesterHolderId
        3. No OPEN conflict blocks the scope element
        4. Authority is not SUSPENDED
        """
        requester = event.requester_holder_id

        for scope_elem in event.action:
            key = tuple(scope_elem)
            self._consume_gas(GAS_SET_MEM)

            # Check for blocking conflicts
            for conflict in self.state.conflicts:
                self._consume_gas(GAS_SCAN_AR)
                if conflict.status == ConflictStatus.OPEN:
                    for c_elem in conflict.scope_elements:
                        if tuple(c_elem) == key:
                            return False, "CONFLICT_BLOCKS"

            # Find matching authority
            found_authority = False
            for auth in self.state.authorities:
                self._consume_gas(GAS_SCAN_AR)
                if auth.status != AuthorityStatus.ACTIVE:
                    continue
                if auth.holder_id != requester:
                    continue

                # Check scope match (exact)
                for auth_elem in auth.scope:
                    self._consume_gas(GAS_COMPARE)
                    if tuple(auth_elem) == key:
                        found_authority = True
                        break

                if found_authority:
                    break

            if not found_authority:
                return False, "NO_AUTHORITY"

        return True, ""

    def _check_transformation_admissibility(
        self, event: TransformationRequestEvent
    ) -> tuple[bool, str]:
        """
        Check if transformation is admissible per Q18/preregistration §12.

        Admissible iff:
        1. Requester has ≥1 ACTIVE authority
        2. Requested transformation in requester's PTS
        3. Requester's scope covers affected scope elements
        4. No conflicts/suspensions block
        """
        requester = event.requester_holder_id
        transformation = event.transformation

        # Find requester's authorities
        requester_auths = []
        for auth in self.state.authorities:
            self._consume_gas(GAS_SCAN_AR)
            if (auth.holder_id == requester and
                auth.status == AuthorityStatus.ACTIVE):
                requester_auths.append(auth)

        if not requester_auths:
            return False, "NO_REQUESTER_AUTHORITY"

        # Check if any requester authority has the transformation permission
        has_permission = False
        permitting_auth = None
        for auth in requester_auths:
            self._consume_gas(GAS_SET_MEM)
            if transformation in auth.permitted_transformation_set:
                has_permission = True
                permitting_auth = auth
                break

        if not has_permission:
            return False, "TRANSFORMATION_NOT_PERMITTED"

        # Get affected scope elements
        affected_scopes = set()

        for auth_id in event.targets.get("authorityIds") or []:
            target_auth = self.state.get_authority_by_id(auth_id)
            if target_auth:
                for elem in target_auth.scope:
                    affected_scopes.add(tuple(elem))

        for elem in event.targets.get("scopeElements") or []:
            affected_scopes.add(tuple(elem))

        for conflict_id in event.targets.get("conflictIds") or []:
            for conflict in self.state.conflicts:
                if conflict.conflict_id == conflict_id:
                    for elem in conflict.scope_elements:
                        affected_scopes.add(tuple(elem))

        # Check scope coverage
        permitter_scopes = set(tuple(e) for e in permitting_auth.scope)
        if not affected_scopes.issubset(permitter_scopes):
            return False, "SCOPE_NOT_COVERED"

        return True, ""

    def _register_conflict(
        self,
        scope_elements: list[ScopeElement],
        authority_ids: list[str],
    ) -> Optional[ConflictRecord]:
        """
        Register a conflict (SYSTEM_AUTHORITY transformation).

        Returns the created conflict record or None if already exists.
        """
        # Check if conflict already exists for this scope
        for existing in self.state.conflicts:
            if (set(tuple(e) for e in existing.scope_elements) ==
                set(tuple(e) for e in scope_elements)):
                # Update existing conflict with new authority
                for aid in authority_ids:
                    if aid not in existing.authority_ids:
                        existing.authority_ids.append(aid)
                        existing.authority_ids.sort()
                return None

        # Create new conflict
        conflict = ConflictRecord(
            conflict_id="",  # Computed below
            epoch_detected=self.state.current_epoch,
            scope_elements=scope_elements,
            authority_ids=sorted(authority_ids),
            status=ConflictStatus.OPEN,
        )
        conflict.conflict_id = compute_conflict_id(conflict)

        self.state.conflicts.append(conflict)
        self._consume_gas(GAS_UPDATE)

        # Update authority conflict sets
        for auth in self.state.authorities:
            if auth.authority_id in authority_ids:
                if conflict.conflict_id not in auth.conflict_set:
                    auth.conflict_set.append(conflict.conflict_id)
                    auth.conflict_set.sort()

        return conflict

    def _expire_authority(self, authority_id: str) -> None:
        """Expire an authority (SYSTEM_AUTHORITY transformation)."""
        for auth in self.state.authorities:
            if auth.authority_id == authority_id:
                auth.status = AuthorityStatus.EXPIRED
                self._consume_gas(GAS_UPDATE)
                break

    def _revoke_authority(self, authority_id: str) -> None:
        """Revoke an authority."""
        for auth in self.state.authorities:
            if auth.authority_id == authority_id:
                auth.status = AuthorityStatus.REVOKED
                self._consume_gas(GAS_UPDATE)
                break

    def _suspend_authority(self, authority_id: str) -> None:
        """Suspend an authority."""
        for auth in self.state.authorities:
            if auth.authority_id == authority_id and auth.status == AuthorityStatus.ACTIVE:
                auth.status = AuthorityStatus.SUSPENDED
                self._consume_gas(GAS_UPDATE)
                break

    def _resume_authority(self, authority_id: str) -> None:
        """Resume a suspended authority."""
        for auth in self.state.authorities:
            if auth.authority_id == authority_id and auth.status == AuthorityStatus.SUSPENDED:
                auth.status = AuthorityStatus.ACTIVE
                self._consume_gas(GAS_UPDATE)
                break

    def _resolve_conflict(
        self, conflict_id: str, authorities_to_revoke: list[str]
    ) -> None:
        """
        Resolve a conflict destructively per Q29.

        Must revoke at least one participating authority.
        """
        for conflict in self.state.conflicts:
            if conflict.conflict_id == conflict_id:
                # Revoke specified authorities
                revoked_any = False
                for auth_id in authorities_to_revoke:
                    if auth_id in conflict.authority_ids:
                        self._revoke_authority(auth_id)
                        revoked_any = True

                if revoked_any:
                    conflict.status = ConflictStatus.RESOLVED
                    self._consume_gas(GAS_UPDATE)
                break

    def _consume_gas(self, amount: int) -> None:
        """Consume gas, tracking for budget enforcement."""
        self.gas.consumed += amount

    def _make_failure_result(self, code: FailureCode) -> KernelResult:
        """Create a failure result."""
        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.SUSPENSION_ENTERED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={"failure": code.value},
            ),
            state=self.state,
            failure=code,
        )

    def check_gas_exhaustion(self) -> bool:
        """Check if gas budget is exhausted."""
        return self.gas.consumed > self.gas.budget

    def check_deadlock(self) -> Optional[DeadlockType]:
        """
        Check for deadlock conditions per Q9/Q37.

        Deadlock types:
        1. Conflict Deadlock: Conflicts block all admissible actions AND
           no destructive resolution is admissible
        2. Governance Deadlock: No admissible actions AND no admissible
           transformations that could change admissibility
        3. Entropic Collapse: ASA == 0 AND no admissible transformations
           that can increase ASA

        Returns:
            DeadlockType if deadlock detected, None otherwise
        """
        # Check for Entropic Collapse first (most severe)
        active_authorities = self.state.get_active_authorities()
        if len(active_authorities) == 0:
            # No active authorities - check if any transformations admissible
            # Since no authorities exist, no transformations can be admissible
            # (transformations require requester to have authority)
            return DeadlockType.ENTROPIC_COLLAPSE

        # Check for Conflict Deadlock
        open_conflicts = self.state.get_open_conflicts()
        if open_conflicts:
            # Get all scope elements blocked by conflicts
            blocked_scopes = set()
            for conflict in open_conflicts:
                for elem in conflict.scope_elements:
                    blocked_scopes.add(tuple(elem))

            # Check if all active authority scopes are blocked
            all_blocked = True
            for auth in active_authorities:
                for elem in auth.scope:
                    if tuple(elem) not in blocked_scopes:
                        all_blocked = False
                        break
                if not all_blocked:
                    break

            if all_blocked:
                # All actions blocked - check if resolution is possible
                resolution_possible = self._check_resolution_possible(open_conflicts)
                if not resolution_possible:
                    return DeadlockType.CONFLICT_DEADLOCK

        # Check for Governance Deadlock
        # This requires checking if any action or transformation is admissible
        has_admissible_action = self._has_any_admissible_action()
        has_admissible_transform = self._has_any_admissible_transformation()

        if not has_admissible_action and not has_admissible_transform:
            return DeadlockType.GOVERNANCE_DEADLOCK

        return None

    def _check_resolution_possible(self, conflicts: list[ConflictRecord]) -> bool:
        """
        Check if any holder can resolve any conflict.

        Resolution requires:
        1. Holder has ACTIVE authority with RESOLVE_CONFLICT in PTS
        2. Holder's scope covers the conflict's scope elements
        """
        for conflict in conflicts:
            conflict_scopes = set(tuple(e) for e in conflict.scope_elements)

            for auth in self.state.get_active_authorities():
                if "RESOLVE_CONFLICT" not in auth.permitted_transformation_set:
                    continue

                auth_scopes = set(tuple(e) for e in auth.scope)
                if conflict_scopes.issubset(auth_scopes):
                    return True

        return False

    def _has_any_admissible_action(self) -> bool:
        """
        Check if any action could be admissible.

        An action is admissible if there exists at least one
        unblocked scope element with an active authority.
        """
        # Get blocked scopes
        blocked_scopes = set()
        for conflict in self.state.get_open_conflicts():
            for elem in conflict.scope_elements:
                blocked_scopes.add(tuple(elem))

        # Check for any unblocked active authority scope
        for auth in self.state.get_active_authorities():
            for elem in auth.scope:
                if tuple(elem) not in blocked_scopes:
                    return True

        return False

    def _has_any_admissible_transformation(self) -> bool:
        """
        Check if any transformation could be admissible.

        A transformation is admissible if there exists at least one
        holder with ACTIVE authority that has a non-empty PTS.
        """
        for auth in self.state.get_active_authorities():
            if auth.permitted_transformation_set:
                return True

        return False

    def declare_deadlock(self, deadlock_type: DeadlockType) -> KernelResult:
        """
        Declare deadlock and terminate run per Q37.

        Deadlock is an output event only, does not mutate state,
        and causes run termination.
        """
        self.state.state_id = compute_state_id(self.state)

        return KernelResult(
            output=KernelOutput(
                output_type=OutputType.DEADLOCK_DECLARED,
                event_index=self.event_index,
                state_hash=self.state.state_id,
                details={"deadlock_type": deadlock_type.value},
            ),
            state=self.state,
            deadlock=deadlock_type,
        )

