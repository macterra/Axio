"""
Canonical JSON and Hashing

AST Appendix C compliant canonicalization, SHA-256 hashing,
and deterministic ID generation for AKR-0.
"""

import hashlib
import json
from typing import Any, Union

from structures import (
    AuthorityRecord,
    AuthorityState,
    ConflictRecord,
    EpochTickEvent,
    AuthorityInjectionEvent,
    TransformationRequestEvent,
    ActionRequestEvent,
)


def canonical_json(obj: Any) -> str:
    """
    Serialize object to canonical JSON per AST Appendix C.

    Rules:
    1. UTF-8 encoding, no BOM
    2. No whitespace (minified)
    3. Integers only (no floats, no exponentials)
    4. Strings use shortest valid escape sequences
    5. Optional fields represented explicitly as null
    6. Object keys lexicographically sorted by UTF-8 byte value
    7. Arrays with semantic order preserved
    8. Sets represented as sorted arrays
    """
    return json.dumps(
        _canonicalize(obj),
        separators=(',', ':'),
        ensure_ascii=False,
        sort_keys=True,
    )


def _canonicalize(obj: Any) -> Any:
    """
    Recursively canonicalize an object for JSON serialization.
    Ensures proper ordering and type handling.
    """
    if obj is None:
        return None
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, int):
        return obj
    elif isinstance(obj, float):
        # Floats are forbidden per Appendix C
        raise ValueError("Floats are forbidden in canonical JSON")
    elif isinstance(obj, str):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [_canonicalize(item) for item in obj]
    elif isinstance(obj, dict):
        # Keys must be sorted lexicographically
        return {k: _canonicalize(v) for k, v in sorted(obj.items())}
    elif hasattr(obj, 'to_canonical_dict'):
        return _canonicalize(obj.to_canonical_dict())
    else:
        raise TypeError(f"Cannot canonicalize type: {type(obj)}")


def sha256_hex(data: Union[str, bytes]) -> str:
    """
    Compute SHA-256 hash and return lowercase hexadecimal.

    Per AST Appendix C §6:
    1. Serialize to canonical JSON
    2. Encode as UTF-8 bytes
    3. Compute SHA-256
    4. Output lowercase hexadecimal
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def compute_authority_id(record: AuthorityRecord) -> str:
    """
    Compute authorityId per Q25.

    authorityId = "A:" + sha256(canonical_json(record_without_authorityId_and_conflictSet))
    """
    id_dict = record.to_id_generation_dict()
    canonical = canonical_json(id_dict)
    return "A:" + sha256_hex(canonical)


def compute_conflict_id(record: ConflictRecord) -> str:
    """
    Compute conflictId per Q19.

    conflictId = "C:" + sha256(canonical_json({epochDetected, scopeElements, authorityIds}))
    """
    id_dict = record.to_id_generation_dict()
    canonical = canonical_json(id_dict)
    return "C:" + sha256_hex(canonical)


def compute_epoch_tick_event_id(event: EpochTickEvent) -> str:
    """
    Compute eventId for EPOCH_TICK per Q34.

    eventId = "ET:" + sha256(canonical_json(event_without_eventId))
    """
    id_dict = event.to_id_generation_dict()
    canonical = canonical_json(id_dict)
    return "ET:" + sha256_hex(canonical)


def compute_authority_injection_event_id(event: AuthorityInjectionEvent) -> str:
    """
    Compute eventId for AuthorityInjection per Q33.

    eventId = "EI:" + sha256(canonical_json(event_without_eventId))
    Note: authority.origin must be null during ID generation.
    """
    id_dict = event.to_id_generation_dict()
    canonical = canonical_json(id_dict)
    return "EI:" + sha256_hex(canonical)


def compute_transformation_request_id(event: TransformationRequestEvent) -> str:
    """
    Compute requestId for TransformationRequest per Q21.

    requestId = "TR:" + sha256(canonical_json(event_without_requestId))
    """
    id_dict = event.to_id_generation_dict()
    canonical = canonical_json(id_dict)
    return "TR:" + sha256_hex(canonical)


def compute_action_request_id(event: ActionRequestEvent) -> str:
    """
    Compute requestId for ActionRequest per Q35.

    requestId = "AR:" + sha256(canonical_json(event_without_requestId))
    """
    id_dict = event.to_id_generation_dict()
    canonical = canonical_json(id_dict)
    return "AR:" + sha256_hex(canonical)


def compute_state_id(state: AuthorityState) -> str:
    """
    Compute stateId for AuthorityState.

    stateId = sha256(canonical_json(state_without_stateId))
    """
    state_dict = state.to_canonical_dict()
    # Remove stateId for hashing
    del state_dict["stateId"]
    canonical = canonical_json(state_dict)
    return sha256_hex(canonical)


def compute_event_hash(event: Any) -> str:
    """
    Compute hash of any event for canonical ordering.

    Per Q6: h = SHA256(canonical_json_bytes)
    """
    if hasattr(event, 'to_canonical_dict'):
        canonical = canonical_json(event.to_canonical_dict())
    else:
        canonical = canonical_json(event)
    return sha256_hex(canonical)


def compute_hash_chain_entry(prev_hash: str, event_bytes: bytes) -> str:
    """
    Compute hash chain entry per Q14.

    eventHash = SHA256(prevEventHash || canonicalEventBytes)
    """
    combined = prev_hash.encode('utf-8') + event_bytes
    return sha256_hex(combined)


def canonical_sort_key(event: Any) -> tuple[str, str]:
    """
    Compute sort key for canonical ordering per Q6.

    Sort by (h_hex, canonical_json_lex)
    """
    if hasattr(event, 'to_canonical_dict'):
        canonical = canonical_json(event.to_canonical_dict())
    else:
        canonical = canonical_json(event)
    h = sha256_hex(canonical)
    return (h, canonical)


def canonical_order(events: list[Any]) -> list[Any]:
    """
    Sort events in canonical order per Q6.

    1. Canonicalize each event
    2. Compute h = SHA256(canonical_json_bytes)
    3. Sort ascending by (h_hex, canonical_json_lex)
    """
    return sorted(events, key=canonical_sort_key)


def check_duplicates(events: list[Any]) -> bool:
    """
    Check for duplicate events in a batch.

    Returns True if duplicates exist (invalid run condition).
    """
    seen = set()
    for event in events:
        if hasattr(event, 'to_canonical_dict'):
            canonical = canonical_json(event.to_canonical_dict())
        else:
            canonical = canonical_json(event)
        if canonical in seen:
            return True
        seen.add(canonical)
    return False
