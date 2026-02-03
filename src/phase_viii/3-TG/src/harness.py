"""
TG-VIII-3 Test Harness

Generates event sequences for Conditions A, B, C, D per prereg §15-18.

Condition A: Expiry Without Renewal
Condition B: Renewal Without Conflict
Condition C: Renewal After Destruction
Condition D: Renewal Under Ongoing Conflict
"""

from structures import (
    AuthorityRecord,
    AuthorityStatus,
    EpochAdvancementRequest,
    AuthorityInjectionEvent,
    AuthorityRenewalRequest,
    DestructionAuthorizationEvent,
    ActionRequestEvent,
    Scope,
)


# Canonical identifiers
AUTH_A = "AUTH_A"
AUTH_B = "AUTH_B"
AUTH_C = "AUTH_C"
AUTH_D = "AUTH_D"
AUTH_DX = "AUTH_DX"  # Denying authority for Condition C conflict
AUTH_E = "AUTH_E"
AUTH_F = "AUTH_F"
AUTH_G = "AUTH_G"
AUTH_H = "AUTH_H"

HOLDER_A = "HOLDER_A"
HOLDER_B = "HOLDER_B"
HOLDER_C = "HOLDER_C"
HOLDER_D = "HOLDER_D"
HOLDER_DX = "HOLDER_DX"
HOLDER_E = "HOLDER_E"
HOLDER_F = "HOLDER_F"
HOLDER_G = "HOLDER_G"
HOLDER_H = "HOLDER_H"

AUTHORIZER_EXTERNAL = "EXT_AUTHORIZER_001"

# Scopes per prereg §22
SCOPE_R0000_OP0: Scope = [("R0000", "OP0")]
SCOPE_R0001_OP1: Scope = [("R0001", "OP1")]
SCOPE_R0002_OP2: Scope = [("R0002", "OP2")]
SCOPE_R0003_OP3: Scope = [("R0003", "OP3")]

# Transformation types
EXECUTE_OP0 = "EXECUTE_OP0"
EXECUTE_OP1 = "EXECUTE_OP1"
EXECUTE_OP2 = "EXECUTE_OP2"
EXECUTE_OP3 = "EXECUTE_OP3"


# =============================================================================
# Condition A: Expiry Without Renewal
# =============================================================================

def create_authority_a() -> AuthorityRecord:
    """
    AUTH_A per prereg §22:
    StartEpoch=0, ExpiryEpoch=2, Scope=(R0000, OP0), Permits=["EXECUTE_OP0"]
    """
    return AuthorityRecord(
        authority_id=AUTH_A,
        holder_id=HOLDER_A,
        scope=SCOPE_R0000_OP0,
        status=AuthorityStatus.ACTIVE,
        start_epoch=0,
        expiry_epoch=2,
        permitted_transformation_set=[EXECUTE_OP0],
        conflict_set=[],
    )


def create_authority_b() -> AuthorityRecord:
    """
    AUTH_B per prereg §22:
    StartEpoch=0, ExpiryEpoch=2, Scope=(R0000, OP0), Permits=["EXECUTE_OP0"]

    Note: Both AUTH_A and AUTH_B permit EXECUTE_OP0 (non-conflicting)
    """
    return AuthorityRecord(
        authority_id=AUTH_B,
        holder_id=HOLDER_B,
        scope=SCOPE_R0000_OP0,
        status=AuthorityStatus.ACTIVE,
        start_epoch=0,
        expiry_epoch=2,
        permitted_transformation_set=[EXECUTE_OP0],
        conflict_set=[],
    )


def generate_condition_a_events() -> dict:
    """
    Generate events for Condition A per prereg §15.

    Tests authority expiry mechanics (not conflict).
    Both AUTH_A and AUTH_B permit EXECUTE_OP0.
    """
    nonce = 100

    events = {
        "injection_a": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:0001",
            authority=create_authority_a(),
            nonce=nonce,
        ),
        "injection_b": AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:0002",
            authority=create_authority_b(),
            nonce=nonce + 1,
        ),
        "action_1": ActionRequestEvent(
            request_id="AR:001",
            requester_holder_id=HOLDER_A,
            action=SCOPE_R0000_OP0,
            transformation_type=EXECUTE_OP0,
            epoch=0,
            nonce=nonce + 2,
        ),
        "epoch_0_to_1": EpochAdvancementRequest(
            new_epoch=1,
            event_id="EA:0001",
            nonce=nonce + 3,
        ),
        "epoch_1_to_2": EpochAdvancementRequest(
            new_epoch=2,
            event_id="EA:0002",
            nonce=nonce + 4,
        ),
        "epoch_2_to_3": EpochAdvancementRequest(
            new_epoch=3,
            event_id="EA:0003",
            nonce=nonce + 5,
        ),
        "action_2": ActionRequestEvent(
            request_id="AR:002",
            requester_holder_id=HOLDER_A,
            action=SCOPE_R0000_OP0,
            transformation_type=EXECUTE_OP0,
            epoch=3,
            nonce=nonce + 6,
        ),
    }
    return events


# =============================================================================
# Condition B: Renewal Without Conflict
# =============================================================================

def create_authority_c() -> AuthorityRecord:
    """
    AUTH_C per prereg §22:
    StartEpoch=3, ExpiryEpoch=10, Scope=(R0001, OP1), Permits=["EXECUTE_OP1"]
    """
    return AuthorityRecord(
        authority_id=AUTH_C,
        holder_id=HOLDER_C,
        scope=SCOPE_R0001_OP1,
        status=AuthorityStatus.ACTIVE,
        start_epoch=3,
        expiry_epoch=10,
        permitted_transformation_set=[EXECUTE_OP1],
        conflict_set=[],
    )


def generate_condition_b_events() -> dict:
    """
    Generate events for Condition B per prereg §16.

    Tests renewal without conflict.
    AUTH_C is fresh authority (priorAuthorityId=null).
    """
    nonce = 200

    events = {
        "renewal_c": AuthorityRenewalRequest(
            new_authority=create_authority_c(),
            prior_authority_id=None,  # Fresh authority
            renewal_event_id="RE:0001",
            external_authorizing_source_id=AUTHORIZER_EXTERNAL,
            nonce=nonce,
        ),
        "action_1": ActionRequestEvent(
            request_id="AR:003",
            requester_holder_id=HOLDER_C,
            action=SCOPE_R0001_OP1,
            transformation_type=EXECUTE_OP1,
            epoch=3,
            nonce=nonce + 1,
        ),
        "action_2": ActionRequestEvent(
            request_id="AR:004",
            requester_holder_id=HOLDER_A,  # Holder A has expired authority
            action=SCOPE_R0000_OP0,
            transformation_type=EXECUTE_OP0,
            epoch=3,
            nonce=nonce + 2,
        ),
    }
    return events


# =============================================================================
# Condition C: Renewal After Destruction
# =============================================================================

def create_authority_d() -> AuthorityRecord:
    """
    AUTH_D per prereg §22:
    StartEpoch=3, ExpiryEpoch=10, Scope=(R0002, OP2), Permits=["EXECUTE_OP2"]
    """
    return AuthorityRecord(
        authority_id=AUTH_D,
        holder_id=HOLDER_D,
        scope=SCOPE_R0002_OP2,
        status=AuthorityStatus.ACTIVE,
        start_epoch=3,
        expiry_epoch=10,
        permitted_transformation_set=[EXECUTE_OP2],
        conflict_set=[],
    )


def create_authority_dx() -> AuthorityRecord:
    """
    AUTH_DX per prereg §22:
    StartEpoch=3, ExpiryEpoch=10, Scope=(R0002, OP2), Permits=[]

    Denying authority to create conflict with AUTH_D.
    """
    return AuthorityRecord(
        authority_id=AUTH_DX,
        holder_id=HOLDER_DX,
        scope=SCOPE_R0002_OP2,
        status=AuthorityStatus.ACTIVE,
        start_epoch=3,
        expiry_epoch=10,
        permitted_transformation_set=[],  # Denies
        conflict_set=[],
    )


def create_authority_e() -> AuthorityRecord:
    """
    AUTH_E per prereg §22:
    StartEpoch=3, ExpiryEpoch=10, Scope=(R0002, OP2), Permits=["EXECUTE_OP2"], Prior=AUTH_D
    """
    return AuthorityRecord(
        authority_id=AUTH_E,
        holder_id=HOLDER_E,
        scope=SCOPE_R0002_OP2,
        status=AuthorityStatus.ACTIVE,
        start_epoch=3,
        expiry_epoch=10,
        permitted_transformation_set=[EXECUTE_OP2],
        conflict_set=[],
    )


def generate_condition_c_events() -> dict:
    """
    Generate events for Condition C per prereg §17.

    Tests renewal after destruction.
    Both AUTH_D and AUTH_DX are destroyed, then AUTH_E is renewed from AUTH_D.
    """
    nonce = 300

    events = {
        # Setup: inject conflicting authorities
        "injection_d": AuthorityInjectionEvent(
            epoch=3,
            event_id="EI:0003",
            authority=create_authority_d(),
            nonce=nonce,
        ),
        "injection_dx": AuthorityInjectionEvent(
            epoch=3,
            event_id="EI:0004",
            authority=create_authority_dx(),
            nonce=nonce + 1,
        ),
        # Action triggers conflict registration
        "action_1": ActionRequestEvent(
            request_id="AR:005",
            requester_holder_id=HOLDER_D,
            action=SCOPE_R0002_OP2,
            transformation_type=EXECUTE_OP2,
            epoch=3,
            nonce=nonce + 2,
        ),
        # Destroy AUTH_D
        "destruction_d": DestructionAuthorizationEvent(
            target_authority_ids=[AUTH_D],
            conflict_id="C:0001",  # Will be created by action_1
            authorizer_id=AUTHORIZER_EXTERNAL,
            nonce=nonce + 3,
        ),
        # Destroy AUTH_DX
        "destruction_dx": DestructionAuthorizationEvent(
            target_authority_ids=[AUTH_DX],
            conflict_id="C:0001",
            authorizer_id=AUTHORIZER_EXTERNAL,
            nonce=nonce + 4,
        ),
        # Renewal from destroyed AUTH_D
        "renewal_e": AuthorityRenewalRequest(
            new_authority=create_authority_e(),
            prior_authority_id=AUTH_D,  # References destroyed authority
            renewal_event_id="RE:0002",
            external_authorizing_source_id=AUTHORIZER_EXTERNAL,
            nonce=nonce + 5,
        ),
        # Action should now succeed (no conflicting ACTIVE authority)
        "action_2": ActionRequestEvent(
            request_id="AR:006",
            requester_holder_id=HOLDER_E,
            action=SCOPE_R0002_OP2,
            transformation_type=EXECUTE_OP2,
            epoch=3,
            nonce=nonce + 6,
        ),
    }
    return events


# =============================================================================
# Condition D: Renewal Under Ongoing Conflict
# =============================================================================

def create_authority_f() -> AuthorityRecord:
    """
    AUTH_F per prereg §22:
    StartEpoch=3, ExpiryEpoch=10, Scope=(R0003, OP3), Permits=["EXECUTE_OP3"]
    """
    return AuthorityRecord(
        authority_id=AUTH_F,
        holder_id=HOLDER_F,
        scope=SCOPE_R0003_OP3,
        status=AuthorityStatus.ACTIVE,
        start_epoch=3,
        expiry_epoch=10,
        permitted_transformation_set=[EXECUTE_OP3],
        conflict_set=[],
    )


def create_authority_g() -> AuthorityRecord:
    """
    AUTH_G per prereg §22:
    StartEpoch=3, ExpiryEpoch=5, Scope=(R0003, OP3), Permits=[]

    Note: ExpiryEpoch=5 so it expires at epoch 6
    """
    return AuthorityRecord(
        authority_id=AUTH_G,
        holder_id=HOLDER_G,
        scope=SCOPE_R0003_OP3,
        status=AuthorityStatus.ACTIVE,
        start_epoch=3,
        expiry_epoch=5,
        permitted_transformation_set=[],  # Denies
        conflict_set=[],
    )


def create_authority_h() -> AuthorityRecord:
    """
    AUTH_H per prereg §22:
    StartEpoch=6, ExpiryEpoch=10, Scope=(R0003, OP3), Permits=[], Prior=AUTH_G
    """
    return AuthorityRecord(
        authority_id=AUTH_H,
        holder_id=HOLDER_H,
        scope=SCOPE_R0003_OP3,
        status=AuthorityStatus.ACTIVE,
        start_epoch=6,
        expiry_epoch=10,
        permitted_transformation_set=[],  # Denies
        conflict_set=[],
    )


def generate_condition_d_events() -> dict:
    """
    Generate events for Condition D per prereg §18.

    Tests renewal under ongoing conflict.
    AUTH_F permits, AUTH_G denies → conflict.
    AUTH_G expires, AUTH_H renews the denying position.
    New conflict between AUTH_F and AUTH_H.
    """
    nonce = 400

    events = {
        # Setup: inject conflicting authorities
        "injection_f": AuthorityInjectionEvent(
            epoch=3,
            event_id="EI:0005",
            authority=create_authority_f(),
            nonce=nonce,
        ),
        "injection_g": AuthorityInjectionEvent(
            epoch=3,
            event_id="EI:0006",
            authority=create_authority_g(),
            nonce=nonce + 1,
        ),
        # Action triggers conflict registration
        "action_1": ActionRequestEvent(
            request_id="AR:007",
            requester_holder_id=HOLDER_F,
            action=SCOPE_R0003_OP3,
            transformation_type=EXECUTE_OP3,
            epoch=3,
            nonce=nonce + 2,
        ),
        # Epoch advancement to expire AUTH_G (3 → 6)
        "epoch_3_to_6": EpochAdvancementRequest(
            new_epoch=6,
            event_id="EA:0004",
            nonce=nonce + 3,
        ),
        # Renewal of denying position
        "renewal_h": AuthorityRenewalRequest(
            new_authority=create_authority_h(),
            prior_authority_id=AUTH_G,  # References expired authority
            renewal_event_id="RE:0003",
            external_authorizing_source_id=AUTHORIZER_EXTERNAL,
            nonce=nonce + 4,
        ),
        # Action should be refused (new conflict AUTH_F vs AUTH_H)
        "action_2": ActionRequestEvent(
            request_id="AR:008",
            requester_holder_id=HOLDER_F,
            action=SCOPE_R0003_OP3,
            transformation_type=EXECUTE_OP3,
            epoch=6,
            nonce=nonce + 5,
        ),
    }
    return events
