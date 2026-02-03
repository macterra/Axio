"""
DCR-VIII-2 Test Harness

Generates event sequences for Conditions A, B, C per prereg §6-8, §16.
"""

from structures import (
    AuthorityRecord,
    AuthorityStatus,
    AuthorityInjectionEvent,
    ActionRequestEvent,
    DestructionAuthorizationEvent,
    Scope,
)


# Canonical identifiers
AUTH_A = "AUTH_A"
AUTH_B = "AUTH_B"
HOLDER_A = "HOLDER_A"
HOLDER_B = "HOLDER_B"
AUTHORIZER_EXTERNAL = "EXT_AUTHORIZER_001"

# Contested scope
CONTESTED_SCOPE: Scope = [("R0000", "OP0")]
TRANSFORMATION_TYPE = "EXECUTE_OP0"


def create_authority_a() -> AuthorityRecord:
    """
    Create permitting authority (AUTH_A).

    Per prereg §1: PermittedTransformationSet = ["EXECUTE_OP0"]
    """
    return AuthorityRecord(
        authority_id=AUTH_A,
        holder_id=HOLDER_A,
        scope=CONTESTED_SCOPE,
        status=AuthorityStatus.ACTIVE,
        start_epoch=0,
        expiry_epoch=None,
        permitted_transformation_set=[TRANSFORMATION_TYPE],  # PERMITS
        conflict_set=[],
    )


def create_authority_b() -> AuthorityRecord:
    """
    Create denying authority (AUTH_B).

    Per prereg §1: PermittedTransformationSet = [] (empty = denial by absence)
    """
    return AuthorityRecord(
        authority_id=AUTH_B,
        holder_id=HOLDER_B,
        scope=CONTESTED_SCOPE,
        status=AuthorityStatus.ACTIVE,
        start_epoch=0,
        expiry_epoch=None,
        permitted_transformation_set=[],  # DENIES (absence)
        conflict_set=[],
    )


def generate_injection_events() -> list[AuthorityInjectionEvent]:
    """
    Generate authority injection events.

    Per prereg §16: AUTH_A first, then AUTH_B.
    """
    return [
        AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:0001",
            authority=create_authority_a(),
            nonce=1,
        ),
        AuthorityInjectionEvent(
            epoch=0,
            event_id="EI:0002",
            authority=create_authority_b(),
            nonce=2,
        ),
    ]


def generate_first_action_request() -> ActionRequestEvent:
    """
    Generate first contested action request.

    Per prereg §6: This triggers conflict registration.
    """
    return ActionRequestEvent(
        epoch=0,
        request_id="AR:001",
        requester_holder_id=HOLDER_A,
        action=CONTESTED_SCOPE,
        transformation_type=TRANSFORMATION_TYPE,
        nonce=100,
    )


def generate_destruction_authorization_single(
    target_authority_id: str,
    conflict_id: str = "C:0001",
) -> DestructionAuthorizationEvent:
    """
    Generate destruction authorization for a single authority.

    Per prereg §4: External authorization to destroy.
    """
    return DestructionAuthorizationEvent(
        target_authority_ids=[target_authority_id],
        conflict_id=conflict_id,
        authorizer_id=AUTHORIZER_EXTERNAL,
        nonce=500,
    )


def generate_destruction_authorization_all(
    conflict_id: str = "C:0001",
) -> DestructionAuthorizationEvent:
    """
    Generate destruction authorization for ALL authorities.

    Per prereg §7: Single request with ["ALL"].
    """
    return DestructionAuthorizationEvent(
        target_authority_ids=["ALL"],
        conflict_id=conflict_id,
        authorizer_id=AUTHORIZER_EXTERNAL,
        nonce=500,
    )


def generate_second_action_request() -> ActionRequestEvent:
    """
    Generate second action request (post-destruction).

    Per prereg §6: Should execute in Condition A, refuse in B/C.
    """
    return ActionRequestEvent(
        epoch=0,
        request_id="AR:002",
        requester_holder_id=HOLDER_A,
        action=CONTESTED_SCOPE,
        transformation_type=TRANSFORMATION_TYPE,
        nonce=200,
    )


# Condition-specific event generators

def generate_condition_a_events() -> dict:
    """
    Generate all events for Condition A (destroy denying authority).

    Returns dict with labeled event sequences for clarity.
    """
    return {
        "injections": generate_injection_events(),
        "first_action": generate_first_action_request(),
        "destruction": generate_destruction_authorization_single(AUTH_B),
        "second_action": generate_second_action_request(),
    }


def generate_condition_b_events() -> dict:
    """
    Generate all events for Condition B (destroy both).

    Returns dict with labeled event sequences.
    """
    return {
        "injections": generate_injection_events(),
        "first_action": generate_first_action_request(),
        "destruction": generate_destruction_authorization_all(),
        "second_action": generate_second_action_request(),
    }


def generate_condition_c_events() -> dict:
    """
    Generate all events for Condition C (no destruction).

    Returns dict with labeled event sequences.
    """
    return {
        "injections": generate_injection_events(),
        "first_action": generate_first_action_request(),
        "destruction": None,  # No destruction authorization
        "second_action": generate_second_action_request(),
    }
