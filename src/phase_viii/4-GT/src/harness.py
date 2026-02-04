"""
GT-VIII-4 Test Harness

Generates event sequences for Conditions A-E per prereg §10.

Condition A: Governance Without Authority
Condition B: Single-Authority Governance
Condition C: Conflicting Governance Authorities
Condition D1: Self-Governance Execution
Condition D2: Self-Governance Deadlock
Condition E: Infinite Regress Attempt
"""

from structures import (
    AuthorityRecord,
    AuthorityStatus,
    EpochAdvancementRequest,
    AuthorityInjectionEvent,
    AuthorityRenewalRequest,
    GovernanceActionRequest,
    GovernanceActionType,
    ActionRequestEvent,
    aav_bit,
    TRANSFORM_EXECUTE,
    TRANSFORM_DESTROY_AUTHORITY,
    TRANSFORM_CREATE_AUTHORITY,
)


# ============================================================================
# Canonical Identifiers
# ============================================================================

# Condition A
AUTH_X = "AUTH_X"

# Condition B
AUTH_GOV = "AUTH_GOV"
AUTH_TARGET = "AUTH_TARGET"

# Condition C
AUTH_GOV_A = "AUTH_GOV_A"
AUTH_GOV_B = "AUTH_GOV_B"
AUTH_TARGET_C = "AUTH_TARGET_C"

# Condition D
AUTH_SELF = "AUTH_SELF"
AUTH_SELF_A = "AUTH_SELF_A"
AUTH_SELF_B = "AUTH_SELF_B"

# Condition E
AUTH_R_PREFIX = "AUTH_R"

# Scopes
SCOPE_X = "SCOPE_X"
SCOPE_S = "SCOPE_S"
SCOPE_SHARED = "SCOPE_SHARED"

# External authorizer
AUTHORIZER_EXTERNAL = "EXT_AUTHORIZER_001"


# ============================================================================
# AAV Helpers
# ============================================================================

AAV_EXECUTE_ONLY = aav_bit(TRANSFORM_EXECUTE)  # 0b001
AAV_EXECUTE_DESTROY = aav_bit(TRANSFORM_EXECUTE) | aav_bit(TRANSFORM_DESTROY_AUTHORITY)  # 0b011
AAV_ALL_GOVERNANCE = (
    aav_bit(TRANSFORM_EXECUTE) |
    aav_bit(TRANSFORM_DESTROY_AUTHORITY) |
    aav_bit(TRANSFORM_CREATE_AUTHORITY)
)  # 0b111


# ============================================================================
# Condition A: Governance Without Authority
# ============================================================================

def create_authority_x_no_governance() -> AuthorityRecord:
    """
    AUTH_X per prereg §10 Condition A:
    ACTIVE, AAV = 0b001 (EXECUTE only, no governance bits)
    """
    return AuthorityRecord(
        authority_id=AUTH_X,
        holder_id="HOLDER_X",
        resource_scope=SCOPE_X,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_ONLY,
        start_epoch=0,
        expiry_epoch=100,
    )


def generate_condition_a_events() -> dict:
    """
    Generate events for Condition A per prereg §10.

    Tests governance action proposed with no admitting authority.
    Expected: ACTION_REFUSED (reason: NO_AUTHORITY)
    """
    nonce = 100

    events = {
        "injection_x": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:A001",
            authority=create_authority_x_no_governance(),
            nonce=nonce,
        ),
        "destroy_x": GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset([AUTH_X]),
            target_ids=frozenset([AUTH_X]),
            epoch=0,
            params={
                "target_authority_id": AUTH_X,
                "destruction_reason": "test_condition_a",
            },
            event_id="GA:A001",
            nonce=nonce + 1,
        ),
    }
    return events


# ============================================================================
# Condition B: Single-Authority Governance
# ============================================================================

def create_authority_gov() -> AuthorityRecord:
    """
    AUTH_GOV per prereg §10 Condition B:
    ACTIVE, AAV = 0b011 (EXECUTE + DESTROY_AUTHORITY)
    """
    return AuthorityRecord(
        authority_id=AUTH_GOV,
        holder_id="HOLDER_GOV",
        resource_scope=SCOPE_X,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_DESTROY,
        start_epoch=0,
        expiry_epoch=100,
    )


def create_authority_target() -> AuthorityRecord:
    """
    AUTH_TARGET per prereg §10 Condition B:
    ACTIVE, AAV = 0b001 (EXECUTE only)
    """
    return AuthorityRecord(
        authority_id=AUTH_TARGET,
        holder_id="HOLDER_TARGET",
        resource_scope=SCOPE_X,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_ONLY,
        start_epoch=0,
        expiry_epoch=100,
    )


def generate_condition_b_events() -> dict:
    """
    Generate events for Condition B per prereg §10.

    Tests single-authority governance execution.
    Expected: AUTHORITY_DESTROYED (AUTH_TARGET → VOID)
    """
    nonce = 200

    events = {
        "injection_gov": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:B001",
            authority=create_authority_gov(),
            nonce=nonce,
        ),
        "injection_target": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:B002",
            authority=create_authority_target(),
            nonce=nonce + 1,
        ),
        "destroy_target": GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset([AUTH_GOV]),
            target_ids=frozenset([AUTH_TARGET]),
            epoch=0,
            params={
                "target_authority_id": AUTH_TARGET,
                "destruction_reason": "test_condition_b",
            },
            event_id="GA:B001",
            nonce=nonce + 2,
        ),
    }
    return events


# ============================================================================
# Condition C: Conflicting Governance Authorities
# ============================================================================

def create_authority_gov_a() -> AuthorityRecord:
    """
    AUTH_GOV_A per prereg §10 Condition C:
    ACTIVE, AAV = 0b011 (EXECUTE + DESTROY), scope = SCOPE_X
    """
    return AuthorityRecord(
        authority_id=AUTH_GOV_A,
        holder_id="HOLDER_GOV_A",
        resource_scope=SCOPE_X,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_DESTROY,
        start_epoch=0,
        expiry_epoch=100,
    )


def create_authority_gov_b() -> AuthorityRecord:
    """
    AUTH_GOV_B per prereg §10 Condition C:
    ACTIVE, AAV = 0b001 (EXECUTE only, no DESTROY), scope = SCOPE_X (overlapping)
    """
    return AuthorityRecord(
        authority_id=AUTH_GOV_B,
        holder_id="HOLDER_GOV_B",
        resource_scope=SCOPE_X,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_ONLY,
        start_epoch=0,
        expiry_epoch=100,
    )


def create_authority_target_c() -> AuthorityRecord:
    """
    AUTH_TARGET_C per prereg §10 Condition C:
    ACTIVE, scope = SCOPE_X
    """
    return AuthorityRecord(
        authority_id=AUTH_TARGET_C,
        holder_id="HOLDER_TARGET_C",
        resource_scope=SCOPE_X,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_ONLY,
        start_epoch=0,
        expiry_epoch=100,
    )


def generate_condition_c_events() -> dict:
    """
    Generate events for Condition C per prereg §10.

    Tests conflicting governance authorities.
    Expected: ACTION_REFUSED (reason: CONFLICT_BLOCKS), DEADLOCK_DECLARED
    """
    nonce = 300

    events = {
        "injection_gov_a": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:C001",
            authority=create_authority_gov_a(),
            nonce=nonce,
        ),
        "injection_gov_b": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:C002",
            authority=create_authority_gov_b(),
            nonce=nonce + 1,
        ),
        "injection_target": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:C003",
            authority=create_authority_target_c(),
            nonce=nonce + 2,
        ),
        "destroy_target": GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset([AUTH_GOV_A]),
            target_ids=frozenset([AUTH_TARGET_C]),
            epoch=0,
            params={
                "target_authority_id": AUTH_TARGET_C,
                "destruction_reason": "test_condition_c",
            },
            event_id="GA:C001",
            nonce=nonce + 3,
        ),
    }
    return events


# ============================================================================
# Condition D1: Self-Governance Execution
# ============================================================================

def create_authority_self() -> AuthorityRecord:
    """
    AUTH_SELF per prereg §10 Condition D1:
    ACTIVE, AAV = 0b011 (EXECUTE + DESTROY_AUTHORITY)
    Self-covering scope.
    """
    return AuthorityRecord(
        authority_id=AUTH_SELF,
        holder_id="HOLDER_SELF",
        resource_scope=SCOPE_S,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_DESTROY,
        start_epoch=0,
        expiry_epoch=100,
    )


def generate_condition_d1_events() -> dict:
    """
    Generate events for Condition D1 per prereg §10.

    Tests self-targeting governance execution.
    Expected: AUTHORITY_DESTROYED (AUTH_SELF → VOID)
    """
    nonce = 400

    events = {
        "injection_self": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:D1_001",
            authority=create_authority_self(),
            nonce=nonce,
        ),
        "destroy_self": GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset([AUTH_SELF]),
            target_ids=frozenset([AUTH_SELF]),
            epoch=0,
            params={
                "target_authority_id": AUTH_SELF,
                "destruction_reason": "test_condition_d1_self_destruct",
            },
            event_id="GA:D1_001",
            nonce=nonce + 1,
        ),
    }
    return events


# ============================================================================
# Condition D2: Self-Governance Deadlock
# ============================================================================

def create_authority_self_a() -> AuthorityRecord:
    """
    AUTH_SELF_A per prereg §10 Condition D2:
    ACTIVE, AAV = 0b011 (EXECUTE + DESTROY), scope = SCOPE_S
    """
    return AuthorityRecord(
        authority_id=AUTH_SELF_A,
        holder_id="HOLDER_SELF_A",
        resource_scope=SCOPE_S,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_DESTROY,
        start_epoch=0,
        expiry_epoch=100,
    )


def create_authority_self_b() -> AuthorityRecord:
    """
    AUTH_SELF_B per prereg §10 Condition D2:
    ACTIVE, AAV = 0b001 (EXECUTE only, no DESTROY), scope = SCOPE_S
    Creates structural conflict.
    """
    return AuthorityRecord(
        authority_id=AUTH_SELF_B,
        holder_id="HOLDER_SELF_B",
        resource_scope=SCOPE_S,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_EXECUTE_ONLY,
        start_epoch=0,
        expiry_epoch=100,
    )


def generate_condition_d2_events() -> dict:
    """
    Generate events for Condition D2 per prereg §10.

    Tests self-targeting governance with conflict.
    Expected: ACTION_REFUSED (reason: CONFLICT_BLOCKS), DEADLOCK_DECLARED
    """
    nonce = 500

    events = {
        "injection_self_a": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:D2_001",
            authority=create_authority_self_a(),
            nonce=nonce,
        ),
        "injection_self_b": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:D2_002",
            authority=create_authority_self_b(),
            nonce=nonce + 1,
        ),
        "destroy_self_a": GovernanceActionRequest(
            action_type=GovernanceActionType.DESTROY_AUTHORITY,
            initiator_ids=frozenset([AUTH_SELF_A]),
            target_ids=frozenset([AUTH_SELF_A]),
            epoch=0,
            params={
                "target_authority_id": AUTH_SELF_A,
                "destruction_reason": "test_condition_d2_self_conflict",
            },
            event_id="GA:D2_001",
            nonce=nonce + 2,
        ),
    }
    return events


# ============================================================================
# Condition E: Infinite Regress Attempt
# ============================================================================

def create_authority_r(index: int) -> AuthorityRecord:
    """
    AUTH_R{index} per prereg §10 Condition E:
    ACTIVE, AAV = 0b111 (EXECUTE + DESTROY + CREATE)
    All share SCOPE_SHARED.
    """
    return AuthorityRecord(
        authority_id=f"{AUTH_R_PREFIX}{index:03d}",
        holder_id=f"HOLDER_R{index:03d}",
        resource_scope=SCOPE_SHARED,
        status=AuthorityStatus.ACTIVE,
        aav=AAV_ALL_GOVERNANCE,
        start_epoch=0,
        expiry_epoch=1000,
    )


def generate_condition_e_events(num_initial_authorities: int = 100, num_create_actions: int = 200) -> dict:
    """
    Generate events for Condition E per prereg §10.

    Tests instruction bound enforcement on mass governance.
    Expected: Some AUTHORITY_CREATED, then ACTION_REFUSED (reason: BOUND_EXHAUSTED)
    """
    nonce = 600
    events = {}

    # Inject initial authorities
    for i in range(1, num_initial_authorities + 1):
        events[f"injection_r{i}"] = AuthorityInjectionEvent(
            epoch=0,
            event_id=f"EI:E{i:03d}",
            authority=create_authority_r(i),
            nonce=nonce + i,
        )

    nonce += num_initial_authorities + 1

    # Generate CREATE_AUTHORITY actions
    for i in range(1, num_create_actions + 1):
        initiator_idx = ((i - 1) % num_initial_authorities) + 1
        initiator_id = f"{AUTH_R_PREFIX}{initiator_idx:03d}"
        new_id = f"AUTH_NEW_{i:03d}"

        events[f"create_{i}"] = GovernanceActionRequest(
            action_type=GovernanceActionType.CREATE_AUTHORITY,
            initiator_ids=frozenset([initiator_id]),
            target_ids=frozenset(),  # CREATE targets nothing existing
            epoch=0,
            params={
                "new_authority_id": new_id,
                "resource_scope": SCOPE_SHARED,
                "scope_basis_authority_id": initiator_id,
                "aav": AAV_ALL_GOVERNANCE,  # Non-amplifying (same as parent)
                "expiry_epoch": 1000,
                "lineage": None,
            },
            event_id=f"GA:E{i:03d}",
            nonce=nonce + i,
        )

    return events
