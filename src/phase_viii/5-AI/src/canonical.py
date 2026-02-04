"""
AI-VIII-5 Canonical JSON and Hashing

Per prereg §5.3 and Appendix B:
- UTF-8 encoding, no BOM
- No whitespace (minified)
- Object keys sorted lexicographically by UTF-8 byte value
- Integers only (no floats)
- Null fields included explicitly
- Arrays preserve semantic order
- Boolean values as true/false (lowercase)

Content-addressed AuthorityID:
- Computed from capability core only (holder, resource_scope, aav, expiry_epoch)
- Excludes: authority_id, status, lineage, creation_epoch, source_id, metadata
"""

import json
import hashlib
from typing import Any


GENESIS_HASH = "0" * 64


def canonical_json(obj: Any) -> str:
    """
    Convert object to canonical JSON string per prereg §5.3.

    - Minified (no whitespace)
    - Keys sorted lexicographically
    - UTF-8 encoding
    """
    return json.dumps(
        obj,
        separators=(',', ':'),
        sort_keys=True,
        ensure_ascii=False,
    )


def canonical_json_bytes(obj: Any) -> bytes:
    """Convert object to canonical JSON bytes (UTF-8)."""
    return canonical_json(obj).encode('utf-8')


def compute_authority_id(capability_core: dict) -> str:
    """
    Compute content-addressed AuthorityID per prereg §4.2.

    AuthorityID = SHA256(canonical_serialize(AuthorityCore))

    capability_core should contain:
    - holder: str
    - resourceScope: str
    - aav: int
    - expiryEpoch: int

    All other fields must be excluded by the caller.
    """
    return hashlib.sha256(canonical_json_bytes(capability_core)).hexdigest()


def params_hash(params: dict) -> str:
    """
    Compute SHA256 of canonical JSON params.

    Used for governance action identity.
    """
    return hashlib.sha256(canonical_json_bytes(params)).hexdigest()


def compute_state_id(state) -> str:
    """
    Compute state ID (hash) for an AuthorityState.

    Per prereg: deterministic hash of canonical state representation.
    """
    state_dict = state.to_canonical_dict()
    # Don't include stateId in the hash computation
    state_dict.pop("stateId", None)
    return hashlib.sha256(canonical_json_bytes(state_dict)).hexdigest()


def chain_hash(prev_hash: str, output) -> str:
    """
    Compute next hash in chain.

    H[i] = SHA256(ascii_hex(H[i-1]) || canonical_json_bytes(output[i]))

    prev_hash is already hex string, so we use it directly.
    """
    output_bytes = canonical_json_bytes(output.to_canonical_dict())
    combined = prev_hash.encode('ascii') + output_bytes
    return hashlib.sha256(combined).hexdigest()


def governance_action_identity(
    epoch: int,
    initiator_ids: frozenset[str],
    target_ids: frozenset[str],
    action_type: int,
    params: dict,
) -> str:
    """
    Compute governance action identity tuple as hash.

    Identity: (epoch, sorted(initiator_ids), sorted(target_ids), action_type, params_hash)
    """
    identity_obj = {
        "epoch": epoch,
        "initiatorIds": sorted(initiator_ids),
        "targetIds": sorted(target_ids),
        "actionType": action_type,
        "paramsHash": params_hash(params),
    }
    return hashlib.sha256(canonical_json_bytes(identity_obj)).hexdigest()
