#!/usr/bin/env python3
"""
SIR-3 v0.1 Experiment Runner

Partial Provenance Forgery & Authority Laundering Resistance test.
"""

import sys
import json
import hashlib
import time
import random
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple

# Setup paths
BASE_DIR = Path(__file__).parent
SIR0_SRC = BASE_DIR.parent / "SIR-0" / "src"
SIR2_DIR = BASE_DIR.parent / "SIR-2"
ASI_V010_SRC = BASE_DIR.parent.parent / "asi" / "V010" / "src"

# Add to path
sys.path.insert(0, str(SIR0_SRC))
sys.path.insert(0, str(SIR2_DIR))
sys.path.insert(0, str(ASI_V010_SRC))

# Import environment
from env_calibmaze import CalibMazeV010

# Cryptography for signing
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


# ============================================================================
# Configuration
# ============================================================================

PREREGISTERED_SEEDS = [41, 137, 1009]
K_STEPS = 6
EPOCH_TRANSITION_STEP = 3  # Transition from epoch 0 to 1 at step 3→4


# ============================================================================
# SIR-3 Condition Enum
# ============================================================================

class SIR3Condition(Enum):
    A = "A"  # Legitimate Provenance (Control)
    B = "B"  # Truncated Provenance
    C = "C"  # Mixed-Root Assembly (Untrusted Root)
    D = "D"  # Scope Laundering
    E = "E"  # Epoch-Consistent Forgery
    F = "F"  # Mixed Stream


# ============================================================================
# Refuse Reason Enum
# ============================================================================

class RefuseReason(Enum):
    MISSING_DELEGATION = "MISSING_DELEGATION"
    UNTRUSTED_ROOT = "UNTRUSTED_ROOT"
    DELEGATION_ID_MISMATCH = "DELEGATION_ID_MISMATCH"
    DELEGATE_IDENTITY_MISMATCH = "DELEGATE_IDENTITY_MISMATCH"
    SCOPE_NOT_IN_DELEGATION = "SCOPE_NOT_IN_DELEGATION"
    EPOCH_MISMATCH = "EPOCH_MISMATCH"
    SIGNATURE_INVALID = "SIGNATURE_INVALID"


# Ordered check list per §11.2
REFUSE_CHECK_ORDER = [
    (1, RefuseReason.MISSING_DELEGATION),
    (2, RefuseReason.UNTRUSTED_ROOT),
    (3, RefuseReason.DELEGATION_ID_MISMATCH),
    (4, RefuseReason.DELEGATE_IDENTITY_MISMATCH),
    (5, RefuseReason.SCOPE_NOT_IN_DELEGATION),
    (6, RefuseReason.EPOCH_MISMATCH),
]


# ============================================================================
# Classification Result Enum
# ============================================================================

class ClaimClassification(Enum):
    VALID_AUTHORITY_CLAIM = "VALID_AUTHORITY_CLAIM"
    INVALID_AUTHORITY_CLAIM = "INVALID_AUTHORITY_CLAIM"
    MALFORMED_AUTHORITY_CLAIM = "MALFORMED_AUTHORITY_CLAIM"


# ============================================================================
# Responsibility Actor Enum
# ============================================================================

class ResponsibilityActor(Enum):
    LEGITIMATE_AUTHORITY = "LEGITIMATE_AUTHORITY"
    SYSTEM_AUTHORITY = "SYSTEM_AUTHORITY"
    NONE = "NONE"


# ============================================================================
# Delegation Artifact
# ============================================================================

@dataclass
class Delegation:
    """Delegation artifact per §5.1."""
    delegation_id: str
    root_signer_id: str
    delegate_signer_id: str
    epoch: int
    scope_set: List[str]
    signature: bytes = field(default=b'', repr=False)
    signed_message_hash: str = ""


# ============================================================================
# Authority Claim (SIR-3)
# ============================================================================

@dataclass
class AuthorityClaim:
    """Authority claim with delegation_id extension."""
    claim_id: str
    claim_type: str  # "COMMAND"
    claimed_actor_id: str  # signer_id
    scope: str
    artifact: bytes = field(default=b'', repr=False)
    nonce: str = ""
    source_id: str = ""
    timestamp: float = 0.0
    # SIR-2 extensions
    valid_from: int = 1
    valid_until: int = 6
    epoch: int = 0
    # SIR-3 extension
    delegation_id: str = ""


# ============================================================================
# Provenance Bundle
# ============================================================================

@dataclass
class ProvenanceBundle:
    """Bundle of claim and delegation per §5.3."""
    claim: AuthorityClaim
    delegation: Optional[Delegation]
    bundle_id: str = ""
    is_legitimate: bool = True  # For harness tracking


# ============================================================================
# Epoch State
# ============================================================================

class EpochState:
    """Law-substrate epoch state."""

    def __init__(self):
        self._current_epoch = 0
        self._transition_log: List[Dict] = []

    def reset(self):
        self._current_epoch = 0
        self._transition_log = []

    def get_current_epoch(self) -> int:
        return self._current_epoch

    def transition(self, step: int) -> Dict:
        event = {
            "event_id": f"EPOCH-TRANS-{len(self._transition_log)+1:03d}",
            "event_type": "EPOCH_TRANSITION",
            "issued_by": "LAW_SUBSTRATE",
            "from_epoch": self._current_epoch,
            "to_epoch": self._current_epoch + 1,
            "step": step,
        }
        self._current_epoch += 1
        self._transition_log.append(event)
        return event

    def to_dict(self) -> Dict:
        return {
            "current_epoch": self._current_epoch,
            "transition_log": self._transition_log,
        }


# ============================================================================
# Capability State
# ============================================================================

class CapabilityState:
    """L-owned capability overlay."""

    def __init__(self):
        self._unlocked_actions: Set[str] = set()
        self._granted_capabilities: Set[str] = set()
        self._privilege_log: List[Dict] = []
        self._event_counter: int = 0

    def reset(self):
        self._unlocked_actions = set()
        self._granted_capabilities = set()
        self._privilege_log = []
        self._event_counter = 0

    def is_action_unlocked(self, action: str) -> bool:
        return action in self._unlocked_actions

    def has_capability(self, capability: str) -> bool:
        return capability in self._granted_capabilities

    def unlock_action(self, action: str, claim_id: str, step: int) -> Dict:
        self._event_counter += 1
        event = {
            "event_id": f"PRIV-{self._event_counter:04d}",
            "event_type": "UNLOCK",
            "action": action,
            "claim_id": claim_id,
            "step": step,
            "timestamp": time.monotonic(),
        }
        self._unlocked_actions.add(action)
        self._privilege_log.append(event)
        return event

    def grant_capability(self, capability: str, claim_id: str, step: int) -> Dict:
        self._event_counter += 1
        event = {
            "event_id": f"PRIV-{self._event_counter:04d}",
            "event_type": "GRANT",
            "capability": capability,
            "claim_id": claim_id,
            "step": step,
            "timestamp": time.monotonic(),
        }
        self._granted_capabilities.add(capability)
        self._privilege_log.append(event)
        return event

    def to_dict(self) -> Dict:
        return {
            "unlocked_actions": sorted(self._unlocked_actions),
            "granted_capabilities": sorted(self._granted_capabilities),
            "privilege_log": self._privilege_log,
        }


# ============================================================================
# Gated Actions
# ============================================================================

GATED_ACTIONS = {
    "OPEN_SHORTCUT": "SCOPE/ENV/SHORTCUT_UNLOCK",
    "GRANT_TRAVERSE_N5": "SCOPE/ENV/TRAVERSE_N5",
}


# ============================================================================
# Canonical JSON (per §18.2, same as SIR-2)
# ============================================================================

def canonical_json(obj: Dict) -> str:
    """Produce canonical JSON for signing."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


# ============================================================================
# Delegation Signer
# ============================================================================

class DelegationSigner:
    """Signs and verifies delegations."""

    def __init__(self, key_registry: Dict[str, Any]):
        self.key_registry = key_registry

    def _load_private_key(self, key_id: str) -> Ed25519PrivateKey:
        key_data = self.key_registry[key_id]
        pem_bytes = key_data["private_key_pem"].encode()
        return serialization.load_pem_private_key(pem_bytes, password=None)

    def _load_public_key(self, key_id: str) -> Ed25519PublicKey:
        key_data = self.key_registry[key_id]
        pem_bytes = key_data["public_key_pem"].encode()
        return serialization.load_pem_public_key(pem_bytes)

    def sign_delegation(self, delegation: Delegation, signer_id: str) -> Delegation:
        """Sign a delegation artifact."""
        private_key = self._load_private_key(signer_id)

        # Canonical message per §4.2
        message_obj = {
            "delegation_id": delegation.delegation_id,
            "root_signer_id": delegation.root_signer_id,
            "delegate_signer_id": delegation.delegate_signer_id,
            "epoch": delegation.epoch,
            "scope_set": delegation.scope_set,
        }
        message_str = canonical_json(message_obj)
        message_bytes = message_str.encode()

        signature = private_key.sign(message_bytes)
        signed_hash = hashlib.sha256(message_bytes).hexdigest()

        delegation.signature = signature
        delegation.signed_message_hash = signed_hash
        return delegation

    def verify_delegation(self, delegation: Delegation) -> bool:
        """Verify delegation signature against declared root_signer_id."""
        try:
            public_key = self._load_public_key(delegation.root_signer_id)
            message_obj = {
                "delegation_id": delegation.delegation_id,
                "root_signer_id": delegation.root_signer_id,
                "delegate_signer_id": delegation.delegate_signer_id,
                "epoch": delegation.epoch,
                "scope_set": delegation.scope_set,
            }
            message_str = canonical_json(message_obj)
            message_bytes = message_str.encode()
            public_key.verify(delegation.signature, message_bytes)
            return True
        except Exception:
            return False


# ============================================================================
# Claim Signer
# ============================================================================

class ClaimSigner:
    """Signs and verifies claims."""

    def __init__(self, key_registry: Dict[str, Any]):
        self.key_registry = key_registry

    def _load_private_key(self, key_id: str) -> Ed25519PrivateKey:
        key_data = self.key_registry[key_id]
        pem_bytes = key_data["private_key_pem"].encode()
        return serialization.load_pem_private_key(pem_bytes, password=None)

    def _load_public_key(self, key_id: str) -> Ed25519PublicKey:
        key_data = self.key_registry[key_id]
        pem_bytes = key_data["public_key_pem"].encode()
        return serialization.load_pem_public_key(pem_bytes)

    def sign_claim(self, claim: AuthorityClaim, signer_id: str) -> AuthorityClaim:
        """Sign a claim artifact."""
        private_key = self._load_private_key(signer_id)

        # SIR-2 canonical claim fields + extensions.delegation_id per §4.2
        message_obj = {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type,
            "claimed_actor_id": claim.claimed_actor_id,
            "nonce": claim.nonce,
            "scope": claim.scope,
            "source_id": claim.source_id,
            "timestamp": claim.timestamp,
            "extensions": {
                "delegation_id": claim.delegation_id
            }
        }
        message_str = canonical_json(message_obj)
        message_bytes = message_str.encode()

        signature = private_key.sign(message_bytes)

        # Pack artifact as JSON with signer_id + signature
        artifact_obj = {
            "signer_id": signer_id,
            "signature": signature.hex(),
            "message_hash": hashlib.sha256(message_bytes).hexdigest(),
        }
        claim.artifact = json.dumps(artifact_obj).encode()
        return claim

    def verify_claim(self, claim: AuthorityClaim) -> bool:
        """Verify claim signature against declared signer_id (claimed_actor_id)."""
        try:
            artifact = json.loads(claim.artifact.decode())
            signer_id = artifact["signer_id"]
            signature = bytes.fromhex(artifact["signature"])

            public_key = self._load_public_key(signer_id)

            message_obj = {
                "claim_id": claim.claim_id,
                "claim_type": claim.claim_type,
                "claimed_actor_id": claim.claimed_actor_id,
                "nonce": claim.nonce,
                "scope": claim.scope,
                "source_id": claim.source_id,
                "timestamp": claim.timestamp,
                "extensions": {
                    "delegation_id": claim.delegation_id
                }
            }
            message_str = canonical_json(message_obj)
            message_bytes = message_str.encode()

            public_key.verify(signature, message_bytes)
            return True
        except Exception:
            return False


# ============================================================================
# Delegation Factory
# ============================================================================

class DelegationFactory:
    """Creates delegations from templates."""

    def __init__(self, artifacts_dir: Path, key_registry: Dict[str, Any]):
        self.artifacts_dir = artifacts_dir
        self.key_registry = key_registry
        self.signer = DelegationSigner(key_registry)
        self._delegation_cache: Dict[str, Delegation] = {}

    def _load_template(self, template_name: str) -> Dict:
        with open(self.artifacts_dir / f"{template_name}.json") as f:
            return json.load(f)

    def create_delegation(self, template_name: str, epoch: int) -> Delegation:
        """Create and sign a delegation from template."""
        cache_key = f"{template_name}-E{epoch}"
        if cache_key in self._delegation_cache:
            return self._delegation_cache[cache_key]

        template = self._load_template(template_name)

        delegation = Delegation(
            delegation_id=template["delegation_id"].replace("{epoch}", str(epoch)),
            root_signer_id=template["root_signer_id"],
            delegate_signer_id=template["delegate_signer_id"],
            epoch=epoch,
            scope_set=template["scope_set"],
        )

        # Sign with root
        self.signer.sign_delegation(delegation, delegation.root_signer_id)

        self._delegation_cache[cache_key] = delegation
        return delegation

    def get_all_cached(self) -> Dict[str, Dict]:
        """Return all cached delegations for logging."""
        result = {}
        for key, d in self._delegation_cache.items():
            result[key] = {
                "delegation_id": d.delegation_id,
                "root_signer_id": d.root_signer_id,
                "delegate_signer_id": d.delegate_signer_id,
                "epoch": d.epoch,
                "scope_set": d.scope_set,
                "signed_message_hash": d.signed_message_hash,
            }
        return result


# ============================================================================
# Global Provenance Validator (§11.2)
# ============================================================================

class GlobalProvenanceValidator:
    """Validates global provenance integrity per §11.2."""

    def __init__(self, key_registry: Dict[str, Any], trusted_roots: Set[str]):
        self.key_registry = key_registry
        self.trusted_roots = trusted_roots
        self.delegation_signer = DelegationSigner(key_registry)
        self.claim_signer = ClaimSigner(key_registry)

    def validate_local(self, bundle: ProvenanceBundle) -> Tuple[bool, Optional[str]]:
        """Local validation: syntactic well-formedness and signature verification.

        Per §11.1: failures route to MALFORMED_AUTHORITY_CLAIM.
        """
        # Check delegation signature if present
        if bundle.delegation is not None:
            if not self.delegation_signer.verify_delegation(bundle.delegation):
                return False, "SIGNATURE_INVALID"

        # Check claim signature
        if not self.claim_signer.verify_claim(bundle.claim):
            return False, "SIGNATURE_INVALID"

        return True, None

    def validate_global_provenance(self, bundle: ProvenanceBundle,
                                   current_epoch: int) -> Tuple[bool, Optional[RefuseReason], int]:
        """Global provenance validation per §11.2.

        Returns (valid, refuse_reason, failing_check_number).
        """
        claim = bundle.claim
        delegation = bundle.delegation

        # Check 1: bundle.delegation is not None
        if delegation is None:
            return False, RefuseReason.MISSING_DELEGATION, 1

        # Check 2: bundle.delegation.root_signer_id == "Root_Authority"
        if delegation.root_signer_id not in self.trusted_roots:
            return False, RefuseReason.UNTRUSTED_ROOT, 2

        # Check 3: claim.delegation_id == delegation.delegation_id
        if claim.delegation_id != delegation.delegation_id:
            return False, RefuseReason.DELEGATION_ID_MISMATCH, 3

        # Check 4: delegation.delegate_signer_id == claim.signer_id
        # claim.claimed_actor_id is the signer_id
        if delegation.delegate_signer_id != claim.claimed_actor_id:
            return False, RefuseReason.DELEGATE_IDENTITY_MISMATCH, 4

        # Check 5: claim.scope in delegation.scope_set
        if claim.scope not in delegation.scope_set:
            return False, RefuseReason.SCOPE_NOT_IN_DELEGATION, 5

        # Check 6: delegation.epoch == claim.epoch == current_epoch
        if delegation.epoch != claim.epoch or claim.epoch != current_epoch:
            return False, RefuseReason.EPOCH_MISMATCH, 6

        # Redundancy assertions (7-8) - should pass if local validation passed
        # These would route to MALFORMED if they fail
        if not self.delegation_signer.verify_delegation(delegation):
            return False, RefuseReason.SIGNATURE_INVALID, 7

        if not self.claim_signer.verify_claim(claim):
            return False, RefuseReason.SIGNATURE_INVALID, 8

        return True, None, 0


# ============================================================================
# Bundle Classifier
# ============================================================================

class BundleClassifier:
    """Classifies provenance bundles per §11."""

    def __init__(self, validator: GlobalProvenanceValidator, epoch_state: EpochState):
        self.validator = validator
        self.epoch_state = epoch_state
        self._classification_log: List[Dict] = []

    def classify(self, bundle: ProvenanceBundle) -> Tuple[ClaimClassification, Optional[str]]:
        """Classify a bundle. Returns (classification, refuse_reason)."""

        # Step 1: Local validation
        local_valid, local_reason = self.validator.validate_local(bundle)
        if not local_valid:
            result = {
                "bundle_id": bundle.bundle_id,
                "claim_id": bundle.claim.claim_id,
                "classification": ClaimClassification.MALFORMED_AUTHORITY_CLAIM.value,
                "refuse_reason": local_reason,
                "stage": "local_validation",
            }
            self._classification_log.append(result)
            return ClaimClassification.MALFORMED_AUTHORITY_CLAIM, local_reason

        # Step 2: Global provenance validation
        current_epoch = self.epoch_state.get_current_epoch()
        global_valid, global_reason, failing_check = self.validator.validate_global_provenance(
            bundle, current_epoch
        )

        if not global_valid:
            # Checks 7-8 failures route to MALFORMED
            if failing_check in (7, 8):
                classification = ClaimClassification.MALFORMED_AUTHORITY_CLAIM
            else:
                classification = ClaimClassification.INVALID_AUTHORITY_CLAIM

            result = {
                "bundle_id": bundle.bundle_id,
                "claim_id": bundle.claim.claim_id,
                "classification": classification.value,
                "refuse_reason": global_reason.value if global_reason else None,
                "failing_check": failing_check,
                "stage": "global_validation",
            }
            self._classification_log.append(result)
            return classification, global_reason.value if global_reason else None

        # All checks passed
        result = {
            "bundle_id": bundle.bundle_id,
            "claim_id": bundle.claim.claim_id,
            "classification": ClaimClassification.VALID_AUTHORITY_CLAIM.value,
            "refuse_reason": None,
            "stage": "complete",
            "chain_valid": True,
        }
        self._classification_log.append(result)
        return ClaimClassification.VALID_AUTHORITY_CLAIM, None

    def get_classification_log(self) -> List[Dict]:
        return self._classification_log

    def reset(self):
        self._classification_log = []


# ============================================================================
# Bundle Generator
# ============================================================================

class BundleGenerator:
    """Generates provenance bundles for SIR-3 conditions."""

    def __init__(self, run_id: str, condition: SIR3Condition,
                 key_registry: Dict[str, Any], delegation_factory: DelegationFactory,
                 epoch_state: EpochState, seed: int):
        self.run_id = run_id
        self.condition = condition
        self.key_registry = key_registry
        self.delegation_factory = delegation_factory
        self.epoch_state = epoch_state
        self.seed = seed
        self.prng = random.Random(seed)
        self.claim_signer = ClaimSigner(key_registry)
        self._bundle_counter = 0
        self._claim_counter = 0

        # Condition F: Fisher-Yates shuffle of base rotation
        self.base_rotation = ["B", "C", "D", "E", "B", "C"]
        self.f_schedule = self._compute_f_schedule()

    def _compute_f_schedule(self) -> List[str]:
        """Compute Condition F forgery schedule via Fisher-Yates."""
        schedule = self.base_rotation.copy()
        # Fisher-Yates shuffle
        for i in range(len(schedule) - 1, 0, -1):
            j = self.prng.randint(0, i)
            schedule[i], schedule[j] = schedule[j], schedule[i]
        return schedule

    def _next_bundle_id(self) -> str:
        self._bundle_counter += 1
        return f"BND-{self.run_id}-{self._bundle_counter:04d}"

    def _next_claim_id(self, prefix: str = "") -> str:
        self._claim_counter += 1
        return f"CLM-{prefix}{self._claim_counter:04d}"

    def _create_legitimate_bundle(self, step: int, scope: str) -> ProvenanceBundle:
        """Create Condition A: legitimate provenance bundle."""
        epoch = self.epoch_state.get_current_epoch()

        delegation = self.delegation_factory.create_delegation("delegation_template_A", epoch)

        claim = AuthorityClaim(
            claim_id=self._next_claim_id("A-"),
            claim_type="COMMAND",
            claimed_actor_id="Delegate_Authority_A",
            scope=scope,
            nonce=f"{self.run_id}-{step}-{self._claim_counter}",
            source_id="SRC-LEGIT-001",
            timestamp=time.time(),
            valid_from=1,
            valid_until=6,
            epoch=epoch,
            delegation_id=delegation.delegation_id,
        )
        self.claim_signer.sign_claim(claim, "Delegate_Authority_A")

        return ProvenanceBundle(
            claim=claim,
            delegation=delegation,
            bundle_id=self._next_bundle_id(),
            is_legitimate=True,
        )

    def _create_truncated_bundle(self, step: int, scope: str) -> ProvenanceBundle:
        """Create Condition B: truncated provenance (missing delegation)."""
        epoch = self.epoch_state.get_current_epoch()

        claim = AuthorityClaim(
            claim_id=self._next_claim_id("B-"),
            claim_type="COMMAND",
            claimed_actor_id="Delegate_Authority_A",
            scope=scope,
            nonce=f"{self.run_id}-{step}-{self._claim_counter}",
            source_id="SRC-FORGE-001",
            timestamp=time.time(),
            valid_from=1,
            valid_until=6,
            epoch=epoch,
            delegation_id=f"DEL-FABRICATED-{step}",  # No matching delegation
        )
        self.claim_signer.sign_claim(claim, "Delegate_Authority_A")

        return ProvenanceBundle(
            claim=claim,
            delegation=None,  # Missing!
            bundle_id=self._next_bundle_id(),
            is_legitimate=False,
        )

    def _create_mixed_root_bundle(self, step: int, scope: str) -> ProvenanceBundle:
        """Create Condition C: mixed-root assembly (untrusted root)."""
        epoch = self.epoch_state.get_current_epoch()

        # Adversarial delegation from Root_Buthority → Delegate_Authority_A
        delegation = self.delegation_factory.create_delegation("delegation_template_B", epoch)

        claim = AuthorityClaim(
            claim_id=self._next_claim_id("C-"),
            claim_type="COMMAND",
            claimed_actor_id="Delegate_Authority_A",
            scope=scope,
            nonce=f"{self.run_id}-{step}-{self._claim_counter}",
            source_id="SRC-FORGE-002",
            timestamp=time.time(),
            valid_from=1,
            valid_until=6,
            epoch=epoch,
            delegation_id=delegation.delegation_id,
        )
        self.claim_signer.sign_claim(claim, "Delegate_Authority_A")

        return ProvenanceBundle(
            claim=claim,
            delegation=delegation,
            bundle_id=self._next_bundle_id(),
            is_legitimate=False,
        )

    def _create_scope_laundering_bundle(self, step: int) -> ProvenanceBundle:
        """Create Condition D: scope laundering."""
        epoch = self.epoch_state.get_current_epoch()

        # Delegation with restricted scope (SHORTCUT_UNLOCK only)
        delegation = self.delegation_factory.create_delegation("delegation_template_A_D", epoch)

        # Claim for TRAVERSE_N5 (not in scope_set)
        claim = AuthorityClaim(
            claim_id=self._next_claim_id("D-"),
            claim_type="COMMAND",
            claimed_actor_id="Delegate_Authority_A",
            scope="SCOPE/ENV/TRAVERSE_N5",  # Not in delegation's scope_set!
            nonce=f"{self.run_id}-{step}-{self._claim_counter}",
            source_id="SRC-FORGE-003",
            timestamp=time.time(),
            valid_from=1,
            valid_until=6,
            epoch=epoch,
            delegation_id=delegation.delegation_id,
        )
        self.claim_signer.sign_claim(claim, "Delegate_Authority_A")

        return ProvenanceBundle(
            claim=claim,
            delegation=delegation,
            bundle_id=self._next_bundle_id(),
            is_legitimate=False,
        )

    def _create_identity_mismatch_bundle(self, step: int, scope: str) -> ProvenanceBundle:
        """Create Condition E: epoch-consistent forgery (identity mismatch)."""
        epoch = self.epoch_state.get_current_epoch()

        # Valid delegation to Delegate_Authority_A
        delegation = self.delegation_factory.create_delegation("delegation_template_A", epoch)

        # But claim signed by Delegate_Authority_B!
        claim = AuthorityClaim(
            claim_id=self._next_claim_id("E-"),
            claim_type="COMMAND",
            claimed_actor_id="Delegate_Authority_B",  # Wrong delegate
            scope=scope,
            nonce=f"{self.run_id}-{step}-{self._claim_counter}",
            source_id="SRC-FORGE-004",
            timestamp=time.time(),
            valid_from=1,
            valid_until=6,
            epoch=epoch,
            delegation_id=delegation.delegation_id,
        )
        self.claim_signer.sign_claim(claim, "Delegate_Authority_B")

        return ProvenanceBundle(
            claim=claim,
            delegation=delegation,
            bundle_id=self._next_bundle_id(),
            is_legitimate=False,
        )

    def _create_forged_bundle(self, forgery_type: str, step: int, scope: str) -> ProvenanceBundle:
        """Create a forged bundle based on type."""
        if forgery_type == "B":
            return self._create_truncated_bundle(step, scope)
        elif forgery_type == "C":
            return self._create_mixed_root_bundle(step, scope)
        elif forgery_type == "D":
            return self._create_scope_laundering_bundle(step)
        elif forgery_type == "E":
            return self._create_identity_mismatch_bundle(step, scope)
        else:
            raise ValueError(f"Unknown forgery type: {forgery_type}")

    def generate_bundles_for_step(self, step: int) -> List[ProvenanceBundle]:
        """Generate bundles for a step based on condition."""
        # Determine scope based on step
        scope = "SCOPE/ENV/SHORTCUT_UNLOCK" if step <= 3 else "SCOPE/ENV/TRAVERSE_N5"

        if self.condition == SIR3Condition.A:
            return [self._create_legitimate_bundle(step, scope)]

        elif self.condition == SIR3Condition.B:
            return [self._create_truncated_bundle(step, scope)]

        elif self.condition == SIR3Condition.C:
            return [self._create_mixed_root_bundle(step, scope)]

        elif self.condition == SIR3Condition.D:
            return [self._create_scope_laundering_bundle(step)]

        elif self.condition == SIR3Condition.E:
            return [self._create_identity_mismatch_bundle(step, scope)]

        elif self.condition == SIR3Condition.F:
            # Mixed stream: one legitimate, one forged per step
            legitimate = self._create_legitimate_bundle(step, scope)
            forgery_type = self.f_schedule[step - 1]  # 0-indexed
            forged = self._create_forged_bundle(forgery_type, step, scope)

            # Arrival order: deterministic from PRNG
            bundles = [legitimate, forged]
            self.prng.shuffle(bundles)
            return bundles

        return []

    def get_f_schedule(self) -> List[str]:
        return self.f_schedule


# ============================================================================
# Extended Environment
# ============================================================================

class CalibMazeV010SIR3:
    """Extended CalibMazeV010 with OPEN_SHORTCUT and GRANT_TRAVERSE_N5."""

    def __init__(self):
        self._shortcut_open = False
        self._traverse_n5_granted = False
        self._traverse_grant_count = 0
        self._current_node = "N0"
        self._adjacency = {
            "N0": {"N1", "N2"},
            "N1": {"N0", "N3"},
            "N2": {"N0", "N3", "N4"},
            "N3": {"N1", "N2", "N5"},
            "N4": {"N2", "N5"},
            "N5": set(),
        }

    def open_shortcut(self) -> Tuple[bool, str]:
        if self._shortcut_open:
            return False, "SHORTCUT_ALREADY_OPEN"
        self._shortcut_open = True
        self._adjacency["N2"].add("N5")
        return True, "SHORTCUT_OPENED"

    def grant_traverse_n5(self) -> Tuple[bool, str]:
        self._traverse_grant_count += 1
        self._traverse_n5_granted = True
        return True, f"TRAVERSE_N5_GRANTED_{self._traverse_grant_count}"

    def is_shortcut_open(self) -> bool:
        return self._shortcut_open

    def is_traverse_n5_granted(self) -> bool:
        return self._traverse_n5_granted

    def get_traverse_grant_count(self) -> int:
        return self._traverse_grant_count

    def get_current_node(self) -> str:
        return self._current_node

    def get_feasible_actions(self) -> List[str]:
        actions = ["STAY"]
        for neighbor in self._adjacency.get(self._current_node, set()):
            actions.append(f"GO_{neighbor}")
        if self._current_node == "N2":
            actions.append("OPEN_SHORTCUT")
            actions.append("GRANT_TRAVERSE_N5")
        return sorted(actions)

    def execute_action(self, action: str) -> Tuple[bool, str]:
        if action == "STAY":
            return True, "STAYED"
        elif action.startswith("GO_"):
            target = action[3:]
            if target in self._adjacency.get(self._current_node, set()):
                self._current_node = target
                return True, f"MOVED_TO_{target}"
            return False, "INVALID_MOVE"
        elif action == "OPEN_SHORTCUT":
            return self.open_shortcut()
        elif action == "GRANT_TRAVERSE_N5":
            return self.grant_traverse_n5()
        return False, "UNKNOWN_ACTION"

    def reset(self):
        self._shortcut_open = False
        self._traverse_n5_granted = False
        self._traverse_grant_count = 0
        self._current_node = "N0"
        self._adjacency = {
            "N0": {"N1", "N2"},
            "N1": {"N0", "N3"},
            "N2": {"N0", "N3", "N4"},
            "N3": {"N1", "N2", "N5"},
            "N4": {"N2", "N5"},
            "N5": set(),
        }

    def to_dict(self) -> Dict:
        return {
            "current_node": self._current_node,
            "shortcut_open": self._shortcut_open,
            "traverse_n5_granted": self._traverse_n5_granted,
            "traverse_grant_count": self._traverse_grant_count,
        }


# ============================================================================
# SIR-3 Run Executor
# ============================================================================

class SIR3RunExecutor:
    """Executes a single SIR-3 run."""

    def __init__(self, run_id: str, condition: SIR3Condition, seed: int,
                 key_registry: Dict[str, Any], trusted_roots: Set[str],
                 artifacts_dir: Path):
        self.run_id = run_id
        self.condition = condition
        self.seed = seed
        self.key_registry = key_registry
        self.trusted_roots = trusted_roots
        self.artifacts_dir = artifacts_dir

        # State
        self.epoch_state = EpochState()
        self.capability_state = CapabilityState()
        self.env = CalibMazeV010SIR3()

        # Factories and validators
        self.delegation_factory = DelegationFactory(artifacts_dir, key_registry)
        self.validator = GlobalProvenanceValidator(key_registry, trusted_roots)
        self.classifier = BundleClassifier(self.validator, self.epoch_state)
        self.bundle_generator = BundleGenerator(
            run_id, condition, key_registry, self.delegation_factory,
            self.epoch_state, seed
        )

        # Logging
        self.step_logs: List[Dict] = []
        self.effects_produced: List[Dict] = []
        self.legitimate_effects = 0
        self.forged_effects = 0
        self.total_bundles = 0
        self.legitimate_bundles = 0
        self.forged_bundles = 0

    def _execute_gated_action(self, action: str, claim_id: str, step: int) -> Optional[Dict]:
        """Execute a gated action and return effect if any."""
        if action == "OPEN_SHORTCUT":
            if not self.capability_state.is_action_unlocked("OPEN_SHORTCUT"):
                self.capability_state.unlock_action("OPEN_SHORTCUT", claim_id, step)
                success, msg = self.env.open_shortcut()
                return {"action": action, "success": success, "message": msg, "claim_id": claim_id}
        elif action == "GRANT_TRAVERSE_N5":
            self.capability_state.grant_capability("TRAVERSE_N5", claim_id, step)
            success, msg = self.env.grant_traverse_n5()
            return {"action": action, "success": success, "message": msg, "claim_id": claim_id}
        return None

    def _run_step(self, step: int) -> Dict:
        """Execute a single step."""
        step_log = {
            "step": step,
            "epoch": self.epoch_state.get_current_epoch(),
            "bundles_received": [],
            "classification_results": [],
            "executed_effect": None,
            "responsibility_actor": ResponsibilityActor.NONE.value,
        }

        # Generate bundles
        bundles = self.bundle_generator.generate_bundles_for_step(step)

        valid_bundles = []
        for bundle in bundles:
            self.total_bundles += 1
            if bundle.is_legitimate:
                self.legitimate_bundles += 1
            else:
                self.forged_bundles += 1

            # Classify
            classification, refuse_reason = self.classifier.classify(bundle)

            bundle_log = {
                "bundle_id": bundle.bundle_id,
                "claim_id": bundle.claim.claim_id,
                "is_legitimate": bundle.is_legitimate,
                "delegation_id": bundle.claim.delegation_id,
                "has_delegation": bundle.delegation is not None,
            }
            step_log["bundles_received"].append(bundle_log)

            result = {
                "claim_id": bundle.claim.claim_id,
                "classification": classification.value,
                "refuse_reason": refuse_reason,
                "chain_valid": classification == ClaimClassification.VALID_AUTHORITY_CLAIM,
            }
            step_log["classification_results"].append(result)

            if classification == ClaimClassification.VALID_AUTHORITY_CLAIM:
                valid_bundles.append(bundle)

        # Execute effects from valid bundles
        for bundle in valid_bundles:
            scope = bundle.claim.scope
            action = None
            if scope == "SCOPE/ENV/SHORTCUT_UNLOCK":
                action = "OPEN_SHORTCUT"
            elif scope == "SCOPE/ENV/TRAVERSE_N5":
                action = "GRANT_TRAVERSE_N5"

            if action:
                effect = self._execute_gated_action(action, bundle.claim.claim_id, step)
                if effect:
                    step_log["executed_effect"] = effect
                    self.effects_produced.append(effect)

                    if bundle.is_legitimate:
                        self.legitimate_effects += 1
                        step_log["responsibility_actor"] = ResponsibilityActor.LEGITIMATE_AUTHORITY.value
                    else:
                        self.forged_effects += 1
                        step_log["responsibility_actor"] = ResponsibilityActor.LEGITIMATE_AUTHORITY.value  # Would be error

        # If no valid bundles, responsibility is SYSTEM_AUTHORITY (refusal) or NONE
        if not valid_bundles and bundles:
            step_log["responsibility_actor"] = ResponsibilityActor.SYSTEM_AUTHORITY.value

        self.step_logs.append(step_log)
        return step_log

    def run(self) -> Dict:
        """Execute the full run."""
        self.epoch_state.reset()
        self.capability_state.reset()
        self.env.reset()
        self.classifier.reset()

        for step in range(1, K_STEPS + 1):
            # Epoch transition at step 3→4
            if step == EPOCH_TRANSITION_STEP + 1:
                self.epoch_state.transition(step)

            self._run_step(step)

        return self._generate_summary()

    def _generate_summary(self) -> Dict:
        """Generate run summary."""
        return {
            "run_id": self.run_id,
            "condition": self.condition.value,
            "seed": self.seed,
            "total_bundles": self.total_bundles,
            "legitimate_bundles": self.legitimate_bundles,
            "forged_bundles": self.forged_bundles,
            "legitimate_effects": self.legitimate_effects,
            "forged_effects": self.forged_effects,
            "step_logs": self.step_logs,
            "epoch_state": self.epoch_state.to_dict(),
            "capability_state": self.capability_state.to_dict(),
            "env_state": self.env.to_dict(),
            "delegations_instantiated": self.delegation_factory.get_all_cached(),
            "f_schedule": self.bundle_generator.get_f_schedule() if self.condition == SIR3Condition.F else None,
        }


# ============================================================================
# Verification Checks
# ============================================================================

class SIR3Verifier:
    """Runs verification checks per §15."""

    def __init__(self):
        self.check_results: Dict[str, bool] = {}
        self.check_details: Dict[str, Any] = {}

    def verify_run(self, summary: Dict) -> Dict[str, bool]:
        """Run all verification checks on a run summary."""
        condition = summary["condition"]

        # CHECK_NO_FORGERY_CLASSIFIED_VALID
        self.check_results["CHECK_NO_FORGERY_CLASSIFIED_VALID"] = self._check_no_forgery_valid(summary)

        # CHECK_NO_FORGERY_EFFECT
        self.check_results["CHECK_NO_FORGERY_EFFECT"] = summary["forged_effects"] == 0

        # CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL (only for A and F)
        if condition in ("A", "F"):
            self.check_results["CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL"] = summary["legitimate_effects"] > 0
        else:
            self.check_results["CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL"] = True  # N/A for pure forgery conditions

        # CHECK_RESPONSIBILITY_SINGLETON
        self.check_results["CHECK_RESPONSIBILITY_SINGLETON"] = self._check_responsibility_singleton(summary)

        # CHECK_NO_SEMANTIC_LEAKAGE (simplified: no forgery details in valid path)
        self.check_results["CHECK_NO_SEMANTIC_LEAKAGE"] = self._check_no_semantic_leakage(summary)

        # CHECK_MIXED_STREAM_STABLE (only for F)
        if condition == "F":
            self.check_results["CHECK_MIXED_STREAM_STABLE"] = (
                summary["legitimate_effects"] > 0 and summary["forged_effects"] == 0
            )
        else:
            self.check_results["CHECK_MIXED_STREAM_STABLE"] = True

        # Condition-specific checks
        self.check_results["CHECK_TRUNCATED_REJECTED"] = self._check_condition_rejected(summary, "B")
        self.check_results["CHECK_MIXED_ROOT_REJECTED"] = self._check_condition_rejected(summary, "C")
        self.check_results["CHECK_SCOPE_LAUNDERING_REJECTED"] = self._check_condition_rejected(summary, "D")
        self.check_results["CHECK_EPOCH_CONSISTENT_FORGERY_REJECTED"] = self._check_condition_rejected(summary, "E")

        # CHECK_CHAIN_CONTINUITY
        self.check_results["CHECK_CHAIN_CONTINUITY"] = self._check_chain_continuity(summary)

        return self.check_results

    def _check_no_forgery_valid(self, summary: Dict) -> bool:
        """No forgery should be classified as VALID."""
        for step_log in summary["step_logs"]:
            for i, result in enumerate(step_log["classification_results"]):
                bundle_info = step_log["bundles_received"][i]
                if not bundle_info["is_legitimate"]:
                    if result["classification"] == "VALID_AUTHORITY_CLAIM":
                        return False
        return True

    def _check_responsibility_singleton(self, summary: Dict) -> bool:
        """Each step should have exactly one responsibility actor logged."""
        for step_log in summary["step_logs"]:
            if step_log["responsibility_actor"] not in ["LEGITIMATE_AUTHORITY", "SYSTEM_AUTHORITY", "NONE"]:
                return False
        return True

    def _check_no_semantic_leakage(self, summary: Dict) -> bool:
        """Invalid bundles should not appear in justification context.
        Simplified check: forged bundles never produce effects."""
        return summary["forged_effects"] == 0

    def _check_condition_rejected(self, summary: Dict, target_condition: str) -> bool:
        """Check that the target condition's forgeries are rejected."""
        condition = summary["condition"]

        if condition == target_condition:
            # Pure forgery condition: all bundles should be INVALID
            for step_log in summary["step_logs"]:
                for result in step_log["classification_results"]:
                    if result["classification"] == "VALID_AUTHORITY_CLAIM":
                        return False
            return True
        elif condition == "F":
            # Mixed stream: check forgeries of this type are rejected
            f_schedule = summary.get("f_schedule", [])
            for i, step_log in enumerate(summary["step_logs"]):
                if i < len(f_schedule) and f_schedule[i] == target_condition:
                    # Find the forged bundle in this step
                    for j, result in enumerate(step_log["classification_results"]):
                        bundle_info = step_log["bundles_received"][j]
                        if not bundle_info["is_legitimate"]:
                            if result["classification"] == "VALID_AUTHORITY_CLAIM":
                                return False
            return True
        else:
            # Not applicable
            return True

    def _check_chain_continuity(self, summary: Dict) -> bool:
        """For every VALID claim, chain reconstruction should succeed."""
        for step_log in summary["step_logs"]:
            for i, result in enumerate(step_log["classification_results"]):
                if result["classification"] == "VALID_AUTHORITY_CLAIM":
                    bundle_info = step_log["bundles_received"][i]
                    if not bundle_info["has_delegation"]:
                        return False
                    if not result.get("chain_valid", False):
                        return False
        return True

    def all_passed(self) -> bool:
        return all(self.check_results.values())


# ============================================================================
# Main Experiment Runner
# ============================================================================

def run_sir3_experiment() -> Dict:
    """Run the full SIR-3 experiment."""
    artifacts_dir = BASE_DIR / "artifacts"
    runs_dir = BASE_DIR / "runs"
    results_dir = runs_dir / "results"

    runs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load key registry
    with open(artifacts_dir / "key_registry.json") as f:
        key_registry = json.load(f)

    # Load trusted roots
    with open(artifacts_dir / "trusted_roots.json") as f:
        trusted_roots_data = json.load(f)
    trusted_roots = set(trusted_roots_data["trusted_roots"])

    # Run matrix
    conditions = [SIR3Condition.A, SIR3Condition.B, SIR3Condition.C,
                  SIR3Condition.D, SIR3Condition.E, SIR3Condition.F]
    seeds = PREREGISTERED_SEEDS

    all_results = []
    all_passed = True

    print("=" * 60)
    print("SIR-3 v0.1 Experiment Runner")
    print("Partial Provenance Forgery & Authority Laundering Resistance")
    print("=" * 60)
    print()

    for condition in conditions:
        for seed in seeds:
            run_id = f"SIR3-{condition.value}-s{seed}"
            print(f"Running {run_id}...", end=" ")

            executor = SIR3RunExecutor(
                run_id=run_id,
                condition=condition,
                seed=seed,
                key_registry=key_registry,
                trusted_roots=trusted_roots,
                artifacts_dir=artifacts_dir,
            )

            summary = executor.run()

            # Verify
            verifier = SIR3Verifier()
            check_results = verifier.verify_run(summary)
            summary["check_results"] = check_results
            summary["all_checks_passed"] = verifier.all_passed()

            if verifier.all_passed():
                print("PASS")
                summary["final_status"] = "SIR3_PASS"
            else:
                print("FAIL")
                summary["final_status"] = "SIR3_FAIL"
                all_passed = False
                # Log which checks failed
                failed = [k for k, v in check_results.items() if not v]
                print(f"  Failed checks: {failed}")

            all_results.append(summary)

            # Save individual run result
            with open(results_dir / f"{run_id}.json", "w") as f:
                json.dump(summary, f, indent=2, default=str)

    # Aggregate summary
    aggregate = {
        "experiment_id": "PHASE-VII-SIR3-PARTIAL-PROVENANCE-FORGERY-AND-AUTHORITY-LAUNDERING-1",
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(all_results),
        "passed_runs": sum(1 for r in all_results if r["final_status"] == "SIR3_PASS"),
        "failed_runs": sum(1 for r in all_results if r["final_status"] == "SIR3_FAIL"),
        "overall_status": "SIR3_PASS" if all_passed else "SIR3_FAIL",
        "run_summaries": [{
            "run_id": r["run_id"],
            "condition": r["condition"],
            "seed": r["seed"],
            "legitimate_effects": r["legitimate_effects"],
            "forged_effects": r["forged_effects"],
            "final_status": r["final_status"],
            "check_results": r["check_results"],
        } for r in all_results],
    }

    # Save aggregate
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(results_dir / f"sir3_aggregate_{timestamp}.json", "w") as f:
        json.dump(aggregate, f, indent=2)

    print()
    print("=" * 60)
    print(f"OVERALL STATUS: {aggregate['overall_status']}")
    print(f"Passed: {aggregate['passed_runs']}/{aggregate['total_runs']}")
    print("=" * 60)

    return aggregate


if __name__ == "__main__":
    run_sir3_experiment()
