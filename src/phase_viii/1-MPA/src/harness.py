"""
MPA-VIII-1 Experiment Harness

Generates Authority Records and Action Requests per preregistration.
Executes Condition A (contested actions) and Condition B (third-party actions).
"""

from typing import Generator

from structures import (
    AuthorityRecord,
    AuthorityStatus,
    AuthorityInjectionEvent,
    ActionRequestEvent,
    ScopeElement,
    Scope,
)


# Fixed configuration per preregistration
CONTESTED_SCOPE: Scope = [("R0000", "OP0")]
HOLDER_A = "HOLDER_A"
HOLDER_B = "HOLDER_B"
HOLDER_X = "HOLDER_X"  # Third party
AUTH_A = "AUTH_A"
AUTH_B = "AUTH_B"


def create_authority_a() -> AuthorityRecord:
    """Create first authority per preregistration."""
    return AuthorityRecord(
        authority_id=AUTH_A,
        holder_id=HOLDER_A,
        scope=CONTESTED_SCOPE,
        status=AuthorityStatus.ACTIVE,
        start_epoch=0,
        expiry_epoch=None,
        permitted_transformation_set=[],  # Empty per spec
        conflict_set=[],
    )


def create_authority_b() -> AuthorityRecord:
    """Create second authority per preregistration."""
    return AuthorityRecord(
        authority_id=AUTH_B,
        holder_id=HOLDER_B,
        scope=CONTESTED_SCOPE,
        status=AuthorityStatus.ACTIVE,
        start_epoch=0,
        expiry_epoch=None,
        permitted_transformation_set=[],  # Empty per spec
        conflict_set=[],
    )


def create_injection_events() -> list[AuthorityInjectionEvent]:
    """
    Create authority injection events.

    Returns events for AUTH_A and AUTH_B in that order.
    """
    auth_a = create_authority_a()
    auth_b = create_authority_b()

    event_a = AuthorityInjectionEvent(
        epoch=0,
        event_id=f"EI:0001",
        authority=auth_a,
        nonce=1,
    )

    event_b = AuthorityInjectionEvent(
        epoch=0,
        event_id=f"EI:0002",
        authority=auth_b,
        nonce=2,
    )

    return [event_a, event_b]


def create_condition_a_actions() -> list[ActionRequestEvent]:
    """
    Create Condition A action requests.

    4 actions alternating between HOLDER_A and HOLDER_B,
    all targeting the contested scope.
    """
    actions = []
    holders = [HOLDER_A, HOLDER_B, HOLDER_A, HOLDER_B]

    for i, holder in enumerate(holders):
        action = ActionRequestEvent(
            epoch=0,
            request_id=f"AR:A{i+1:03d}",
            requester_holder_id=holder,
            action=CONTESTED_SCOPE,
            nonce=100 + i,
        )
        actions.append(action)

    return actions


def create_condition_b_actions() -> list[ActionRequestEvent]:
    """
    Create Condition B action requests.

    2 actions from HOLDER_X (third party with no authority).
    """
    actions = []

    for i in range(2):
        action = ActionRequestEvent(
            epoch=0,
            request_id=f"AR:B{i+1:03d}",
            requester_holder_id=HOLDER_X,
            action=CONTESTED_SCOPE,
            nonce=200 + i,
        )
        actions.append(action)

    return actions


def generate_injection_events() -> Generator:
    """Generate authority injection events."""
    for event in create_injection_events():
        yield event


def generate_condition_a_events() -> Generator:
    """Generate Condition A action requests."""
    for event in create_condition_a_actions():
        yield event


def generate_condition_b_events() -> Generator:
    """Generate Condition B action requests."""
    for event in create_condition_b_actions():
        yield event


def generate_all_events() -> Generator:
    """
    Generate all events in execution order.

    Order:
    1. Authority injections (A, B)
    2. Condition A actions (4 total)
    3. Condition B actions (2 total)

    Note: Deadlock declaration occurs between Condition A and B,
    but is handled by the harness, not this generator.
    """
    # Authority injections
    for event in create_injection_events():
        yield event

    # Condition A
    for event in create_condition_a_actions():
        yield event

    # Condition B
    for event in create_condition_b_actions():
        yield event
