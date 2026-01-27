"""
ASI-3 Provenance Certificate Implementation

Implements ProvenanceCertificate and SignatureLink per preregistration §7,
evaluate_candidate() per §9.2, and commit() per §10.1.

This module is frozen at ASI-3 v0.1 freeze time.
"""

from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SignatureLink:
    """
    Per §7.2: A single link in the provenance chain.

    Keys are serialized in order: [signer_id, sig, signed_message_hash]
    Hex strings are lowercase without 0x prefix (§7.4/H8).
    """
    signer_id: str
    sig: str  # Hex-encoded, lowercase, no 0x prefix
    signed_message_hash: str  # Hex-encoded, lowercase, no 0x prefix

    def to_dict(self) -> dict:
        """Serialize with fixed key order per §7.4."""
        return {
            "signer_id": self.signer_id,
            "sig": self.sig.lower().replace("0x", ""),
            "signed_message_hash": self.signed_message_hash.lower().replace("0x", "")
        }


@dataclass
class ProvenanceCertificate:
    """
    Per §7.1: Certificate binding successor to predecessor via authorization chain.

    Fields:
        schema_id: Constant "PCERT/0.1"
        subject_payload_hash: SHA256 of successor normative payload root
        parent_payload_hash: SHA256 of predecessor payload root at AUTH_INIT
        chain: List of SignatureLink (length >= 1)
    """
    schema_id: str  # Constant: "PCERT/0.1"
    subject_payload_hash: str
    parent_payload_hash: str
    chain: list[SignatureLink]

    def to_dict(self) -> dict:
        """Serialize with fixed lexicographic key order per §7.4."""
        return {
            "chain": [link.to_dict() for link in self.chain],
            "parent_payload_hash": self.parent_payload_hash.lower().replace("0x", ""),
            "schema_id": self.schema_id,
            "subject_payload_hash": self.subject_payload_hash.lower().replace("0x", "")
        }


def canonical(cert: ProvenanceCertificate) -> bytes:
    """
    Per §7.4: Deterministic byte-serialization of ProvenanceCertificate.

    - Fixed lexicographic key order
    - UTF-8 encoded
    - Preserves list order for chain
    - SignatureLink keys: [signer_id, sig, signed_message_hash]
    - Hex strings: lowercase, no 0x prefix

    DISTINCT FROM canonical_message used for signature verification.
    """
    d = cert.to_dict()
    # JSON with sorted keys, no whitespace, UTF-8
    return json.dumps(d, sort_keys=True, separators=(',', ':')).encode('utf-8')


def sha256_hex(data: bytes) -> str:
    """Compute SHA256 and return lowercase hex string."""
    return hashlib.sha256(data).hexdigest().lower()


def canonical_message(
    schema_id: str,
    subject_payload_hash: str,
    parent_payload_hash: str,
    prev_link_hash: str = ""
) -> str:
    """
    Per §7.3: Construct canonical message for signature verification.

    canonical_message = hash(schema_id || subject_payload_hash || parent_payload_hash || prev_link_hash)

    Returns hex-encoded SHA256 hash.
    """
    message = (
        schema_id +
        subject_payload_hash.lower().replace("0x", "") +
        parent_payload_hash.lower().replace("0x", "") +
        prev_link_hash.lower().replace("0x", "")
    )
    return sha256_hex(message.encode('utf-8'))


def verify_signature(pubkey: bytes, signature: str, message_hash: str) -> bool:
    """
    Verify cryptographic signature.

    For ASI-3, we use a simplified HMAC-based scheme for demonstration.
    In production, this would use Ed25519 or similar.

    Args:
        pubkey: Public key bytes
        signature: Hex-encoded signature
        message_hash: Hex-encoded message hash

    Returns:
        True if signature is valid, False otherwise
    """
    import hmac

    # Normalize inputs
    sig_bytes = bytes.fromhex(signature.lower().replace("0x", ""))
    msg_bytes = bytes.fromhex(message_hash.lower().replace("0x", ""))

    # Compute expected signature using HMAC-SHA256
    expected = hmac.new(pubkey, msg_bytes, hashlib.sha256).digest()

    # Constant-time comparison
    return hmac.compare_digest(sig_bytes, expected)


def verify_certificate_signature(
    cert: ProvenanceCertificate,
    pubkeys: dict[str, bytes]
) -> tuple[bool, str]:
    """
    Verify a certificate's cryptographic signature regardless of trust status.

    This is used in PREVALIDATION ONLY to confirm the facade certificate
    has a valid signature (just from an untrusted signer).

    Per preregistration: The facade must have "valid signature, untrusted root."
    This function verifies the "valid signature" part independently.

    Returns:
        (valid, signer_id) where:
        - valid: True if signature is cryptographically valid
        - signer_id: The root signer's ID
    """
    if not cert.chain:
        return (False, "EMPTY_CHAIN")

    root_link = cert.chain[0]
    root_signer = root_link.signer_id

    if root_signer not in pubkeys:
        return (False, f"NO_PUBKEY:{root_signer}")

    if not verify_signature(
        pubkey=pubkeys[root_signer],
        signature=root_link.sig,
        message_hash=root_link.signed_message_hash
    ):
        return (False, f"INVALID_SIGNATURE:{root_signer}")

    return (True, root_signer)


def evaluate_candidate(
    cert: ProvenanceCertificate,
    trusted_roots: set[str],
    pubkeys: dict[str, bytes]
) -> tuple[bool, str]:
    """
    Per §9.2: Pure function of certificate, trusted roots, and public keys only.

    No behavioral, textual, or evaluative inputs.

    Returns:
        (accepted, reason) where reason is one of:
        - AUTHORIZED_ROOT: root signer trusted and signature valid
        - UNTRUSTED_ROOT: root signer not in trusted set
        - BAD_SIGNATURE: signature cryptographically invalid
        - EMPTY_CHAIN: no signers in chain
    """
    if not cert.chain:
        return (False, "EMPTY_CHAIN")

    root_link = cert.chain[0]
    root_signer = root_link.signer_id

    # Check trust status first
    if root_signer not in trusted_roots:
        return (False, "UNTRUSTED_ROOT")

    # Verify signature validity
    if root_signer not in pubkeys:
        return (False, "BAD_SIGNATURE")

    if not verify_signature(
        pubkey=pubkeys[root_signer],
        signature=root_link.sig,
        message_hash=root_link.signed_message_hash
    ):
        return (False, "BAD_SIGNATURE")

    return (True, "AUTHORIZED_ROOT")


@dataclass
class CommitResult:
    """Result of commit() function per §10.1."""
    accepted: bool
    reason: str
    inputs_used: list[str]
    commit_input_digest: str


def commit(
    cert: ProvenanceCertificate,
    trusted_roots: set[str],
    pubkeys: dict[str, bytes]
) -> CommitResult:
    """
    Per §10.1: Accepts ONLY ProvenanceCertificate.

    No other inputs permitted.
    Executes in sandboxed scope without access to:
      - Successor behavior buses
      - Explanation artifacts
      - Performance metrics

    inputs_used: ["cert"] — explicitly enumerated for verifiability.
    """
    accepted, reason = evaluate_candidate(cert, trusted_roots, pubkeys)
    return CommitResult(
        accepted=accepted,
        reason=reason,
        inputs_used=["cert"],
        commit_input_digest=sha256_hex(canonical(cert))
    )


def create_certificate(
    subject_payload_hash: str,
    parent_payload_hash: str,
    signer_id: str,
    signing_key: bytes
) -> ProvenanceCertificate:
    """
    Create a ProvenanceCertificate with a single signature link.

    Args:
        subject_payload_hash: Hash of successor payload
        parent_payload_hash: Hash of predecessor payload
        signer_id: Identity of signer (e.g., "Root_Authority" or "Unknown_Signer")
        signing_key: Key for signing (used as HMAC key)

    Returns:
        ProvenanceCertificate with valid signature
    """
    import hmac

    schema_id = "PCERT/0.1"

    # Compute canonical message hash
    msg_hash = canonical_message(
        schema_id,
        subject_payload_hash,
        parent_payload_hash,
        ""  # No previous link for first entry
    )

    # Sign the message hash
    msg_bytes = bytes.fromhex(msg_hash)
    sig = hmac.new(signing_key, msg_bytes, hashlib.sha256).hexdigest().lower()

    link = SignatureLink(
        signer_id=signer_id,
        sig=sig,
        signed_message_hash=msg_hash
    )

    return ProvenanceCertificate(
        schema_id=schema_id,
        subject_payload_hash=subject_payload_hash.lower().replace("0x", ""),
        parent_payload_hash=parent_payload_hash.lower().replace("0x", ""),
        chain=[link]
    )


def load_trusted_roots(path: str) -> set[str]:
    """Load trusted roots from JSON file per §9.4."""
    with open(path, 'r') as f:
        data = json.load(f)
    return set(data.get("trusted_roots", []))


def load_pubkeys(path: str) -> dict[str, bytes]:
    """Load public keys from JSON file per §9.4."""
    with open(path, 'r') as f:
        data = json.load(f)
    return {k: bytes.fromhex(v) for k, v in data.get("pubkeys", {}).items()}
