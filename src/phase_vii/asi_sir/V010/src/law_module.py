"""
Law Module and Escrow State Machine for ASI-0 v1.0

Implements:
- EscrowState: State machine (ESCROWED → VERIFYING → COMMITTED/ABORTED)
- CommitCapability: Predecessor-signed capability for provenance binding
- LawModule: Verification and authorization logic
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum
import hashlib
import json
import time
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

from normative_state import (
    NormativePayload, NormativeStateASI0,
    compute_payload_hash, NULL_BINDING
)


class EscrowState(Enum):
    """Escrow state machine states."""
    ESCROWED = "ESCROWED"
    VERIFYING = "VERIFYING"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


class AuthEvent(Enum):
    """Authorization protocol events."""
    AUTH_INIT = "AUTH_INIT"
    AUTH_COMMIT = "AUTH_COMMIT"
    AUTH_ABORT = "AUTH_ABORT"


@dataclass
class CommitCapability:
    """Predecessor-signed capability for provenance binding.

    The predecessor signs this to authorize the successor's
    normative state binding.
    """
    root_hash: bytes          # compute_payload_hash(Nₚ.payload)
    run_id: str
    env_id: str               # "CalibMazeV010"
    commit_nonce: int         # Monotonic, non-replayable
    compiler_schema_hash: bytes  # Hash of frozen compiler components
    signature: bytes = b''    # Predecessor private key signature

    def to_signing_bytes(self) -> bytes:
        """Get canonical bytes for signing (excludes signature)."""
        canonical = json.dumps({
            "root_hash": self.root_hash.hex(),
            "run_id": self.run_id,
            "env_id": self.env_id,
            "commit_nonce": self.commit_nonce,
            "compiler_schema_hash": self.compiler_schema_hash.hex(),
        }, sort_keys=True, separators=(',', ':'))
        return canonical.encode('utf-8')


def compute_compiler_schema_hash(frozen_files: Dict[str, bytes]) -> bytes:
    """Hash of frozen compiler components.

    frozen_files: mapping from filename to file contents (bytes)
    Required files: core/compiler.py, deliberator.py
    """
    canonical = json.dumps({
        filename: hashlib.sha256(content).hexdigest()
        for filename, content in sorted(frozen_files.items())
    }, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).digest()


@dataclass
class EscrowTransition:
    """Record of an escrow state transition."""
    from_state: EscrowState
    to_state: EscrowState
    event: AuthEvent
    timestamp: float
    step_count: int


@dataclass
class Escrow:
    """Escrow state machine for successor authorization.

    Tracks:
    - Current state
    - Transition history
    - Step count for timeout
    """
    state: EscrowState = EscrowState.ESCROWED
    transitions: List[EscrowTransition] = field(default_factory=list)
    step_count: int = 0
    predecessor_payload_hash: bytes = b''
    successor_initial_payload_hash: bytes = b''

    # Timeout bound: 50 steps in VERIFYING state
    TIMEOUT_STEPS = 50

    def transition(self, event: AuthEvent) -> bool:
        """Attempt a state transition.

        Returns True if transition succeeded, False otherwise.
        """
        old_state = self.state
        new_state = self._get_next_state(event)

        if new_state is None:
            return False

        self.state = new_state
        self.transitions.append(EscrowTransition(
            from_state=old_state,
            to_state=new_state,
            event=event,
            timestamp=time.time(),
            step_count=self.step_count
        ))
        return True

    def _get_next_state(self, event: AuthEvent) -> Optional[EscrowState]:
        """Determine next state given current state and event."""
        transitions = {
            (EscrowState.ESCROWED, AuthEvent.AUTH_INIT): EscrowState.VERIFYING,
            (EscrowState.VERIFYING, AuthEvent.AUTH_COMMIT): EscrowState.COMMITTED,
            (EscrowState.VERIFYING, AuthEvent.AUTH_ABORT): EscrowState.ABORTED,
        }
        return transitions.get((self.state, event))

    def increment_step(self) -> bool:
        """Increment step count. Returns False if timeout exceeded in VERIFYING."""
        self.step_count += 1
        if self.state == EscrowState.VERIFYING and self.step_count > self.TIMEOUT_STEPS:
            self.transition(AuthEvent.AUTH_ABORT)
            return False
        return True

    def can_act(self) -> bool:
        """Check if successor can act (only in COMMITTED state)."""
        return self.state == EscrowState.COMMITTED

    def is_terminal(self) -> bool:
        """Check if escrow has reached terminal state."""
        return self.state in {EscrowState.COMMITTED, EscrowState.ABORTED}


class LawModule:
    """Law Module for capability verification and authorization.

    This is a privileged, non-LLM component that:
    - Generates and signs CommitCapabilities
    - Verifies capability signatures
    - Enforces escrow constraints
    """

    def __init__(self):
        # Generate keypair for this instance
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._used_nonces: Set[int] = set()
        self._nonce_counter: int = 0

    def get_public_key_bytes(self) -> bytes:
        """Get public key for verification."""
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

    def sign_capability(
        self,
        payload: NormativePayload,
        run_id: str,
        env_id: str,
        compiler_schema_hash: bytes
    ) -> CommitCapability:
        """Create and sign a CommitCapability.

        This is called by the predecessor's law module to authorize
        the successor's normative state binding.
        """
        self._nonce_counter += 1
        nonce = self._nonce_counter

        capability = CommitCapability(
            root_hash=compute_payload_hash(payload),
            run_id=run_id,
            env_id=env_id,
            commit_nonce=nonce,
            compiler_schema_hash=compiler_schema_hash,
        )

        # Sign the capability
        signing_bytes = capability.to_signing_bytes()
        signature = self._private_key.sign(signing_bytes)
        capability.signature = signature

        return capability

    def verify_capability(
        self,
        capability: CommitCapability,
        expected_payload_hash: bytes,
        expected_run_id: str,
        public_key_bytes: bytes
    ) -> tuple[bool, str]:
        """Verify a CommitCapability.

        Returns (success, error_message).

        Checks:
        1. Signature valid (predecessor public key)
        2. root_hash matches compute_payload_hash(S.normative_state.payload)
        3. run_id matches current run
        4. commit_nonce is fresh (monotonically increasing, used at most once)
        """
        # Check root_hash matches
        if capability.root_hash != expected_payload_hash:
            return False, "INVALID_RUN / CAPABILITY_ROOT_HASH_MISMATCH"

        # Check run_id matches
        if capability.run_id != expected_run_id:
            return False, "INVALID_RUN / CAPABILITY_RUN_ID_MISMATCH"

        # Check nonce freshness
        if capability.commit_nonce in self._used_nonces:
            return False, "INVALID_RUN / CAPABILITY_NONCE_REPLAY"

        # Verify signature
        try:
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            signing_bytes = capability.to_signing_bytes()
            public_key.verify(capability.signature, signing_bytes)
        except InvalidSignature:
            return False, "INVALID_RUN / CAPABILITY_SIGNATURE_INVALID"
        except Exception as e:
            return False, f"INVALID_RUN / CAPABILITY_VERIFICATION_ERROR: {e}"

        # Mark nonce as used
        self._used_nonces.add(capability.commit_nonce)

        return True, ""


if __name__ == "__main__":
    print("Law Module & Escrow Verification")
    print("=" * 40)

    # Create law module
    law_module = LawModule()
    print(f"\n1. Law Module created")
    print(f"   Public key: {law_module.get_public_key_bytes().hex()[:32]}...")

    # Create sample payload
    from normative_state import NormativePayload
    payload = NormativePayload(
        forbidden_actions=frozenset({"GO_N2", "GO_N4"}),
        target_node="N5"
    )
    print(f"\n2. Sample payload: {payload}")

    # Sign capability
    compiler_hash = hashlib.sha256(b"dummy compiler").digest()
    capability = law_module.sign_capability(
        payload=payload,
        run_id="test-run-001",
        env_id="CalibMazeV010",
        compiler_schema_hash=compiler_hash
    )
    print(f"\n3. Signed capability:")
    print(f"   root_hash: {capability.root_hash.hex()[:32]}...")
    print(f"   run_id: {capability.run_id}")
    print(f"   commit_nonce: {capability.commit_nonce}")
    print(f"   signature: {capability.signature.hex()[:32]}...")

    # Verify capability
    expected_hash = compute_payload_hash(payload)
    success, error = law_module.verify_capability(
        capability=capability,
        expected_payload_hash=expected_hash,
        expected_run_id="test-run-001",
        public_key_bytes=law_module.get_public_key_bytes()
    )
    print(f"\n4. Verification result: {success}")
    if not success:
        print(f"   Error: {error}")

    # Test nonce replay
    success2, error2 = law_module.verify_capability(
        capability=capability,
        expected_payload_hash=expected_hash,
        expected_run_id="test-run-001",
        public_key_bytes=law_module.get_public_key_bytes()
    )
    print(f"\n5. Nonce replay test: {not success2} (expected True)")
    print(f"   Error: {error2}")

    # Test escrow state machine
    print(f"\n6. Escrow state machine:")
    escrow = Escrow()
    print(f"   Initial state: {escrow.state}")

    escrow.transition(AuthEvent.AUTH_INIT)
    print(f"   After AUTH_INIT: {escrow.state}")

    escrow.transition(AuthEvent.AUTH_COMMIT)
    print(f"   After AUTH_COMMIT: {escrow.state}")
    print(f"   Can act: {escrow.can_act()}")
    print(f"   Is terminal: {escrow.is_terminal()}")

    # Test abort path
    escrow2 = Escrow()
    escrow2.transition(AuthEvent.AUTH_INIT)
    escrow2.transition(AuthEvent.AUTH_ABORT)
    print(f"\n7. Abort path test:")
    print(f"   State: {escrow2.state}")
    print(f"   Can act: {escrow2.can_act()}")
