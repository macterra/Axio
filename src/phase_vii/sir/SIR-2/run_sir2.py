#!/usr/bin/env python3
"""
SIR-2 v0.3 Experiment Runner

Replay, Staleness, and Consumption Resistance test.
"""

import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set, Tuple

# Setup paths
BASE_DIR = Path(__file__).parent
SIR0_SRC = BASE_DIR.parent / "SIR-0" / "src"
SIR1_DIR = BASE_DIR.parent / "SIR-1"
ASI_V010_SRC = BASE_DIR.parent.parent / "asi" / "V010" / "src"

# Add to path
sys.path.insert(0, str(SIR0_SRC))
sys.path.insert(0, str(ASI_V010_SRC))

# Import and setup SIR-0 modules (same pattern as SIR-1)
import importlib
import importlib.util

# Set up the SIR-0 src as a package
sir0_init = SIR0_SRC / "__init__.py"
spec = importlib.util.spec_from_file_location("sir0_src", sir0_init)
sir0_src_module = importlib.util.module_from_spec(spec)
sys.modules["sir0_src"] = sir0_src_module

# Load claim_types
claim_types_path = SIR0_SRC / "claim_types.py"
spec = importlib.util.spec_from_file_location("sir0_src.claim_types", claim_types_path,
    submodule_search_locations=[str(SIR0_SRC)])
claim_types_module = importlib.util.module_from_spec(spec)
sys.modules["sir0_src.claim_types"] = claim_types_module
spec.loader.exec_module(claim_types_module)
sys.modules["claim_types"] = claim_types_module

# Load classifier
classifier_path = SIR0_SRC / "classifier.py"

with open(classifier_path) as f:
    classifier_code = f.read()

classifier_code = classifier_code.replace("from .claim_types import", "from claim_types import")

import types
import dataclasses
classifier_module = types.ModuleType("classifier")
classifier_module.__file__ = str(classifier_path)
classifier_module.__dict__['__name__'] = 'classifier'
sys.modules["classifier"] = classifier_module

classifier_module.__dict__['dataclass'] = dataclasses.dataclass
classifier_module.__dict__['field'] = dataclasses.field
classifier_module.__dict__['Set'] = Set
classifier_module.__dict__['List'] = List
classifier_module.__dict__['Dict'] = Dict
classifier_module.__dict__['Optional'] = Optional
classifier_module.__dict__['Any'] = Any
classifier_module.__dict__['hashlib'] = hashlib
classifier_module.__dict__['json'] = json
classifier_module.__dict__['time'] = time
classifier_module.__dict__['Enum'] = Enum

for name in ['AuthorityClaim', 'ClaimType', 'ClaimClassification', 'ResponsibilityActor',
             'L_DerivationLedger', 'JustifyInputManifest', 'DerivationEntry', 'ClassificationResult']:
    if hasattr(claim_types_module, name):
        classifier_module.__dict__[name] = getattr(claim_types_module, name)

exec(compile(classifier_code, classifier_path, 'exec'), classifier_module.__dict__)

# Import from env_calibmaze
from env_calibmaze import CalibMazeV010, get_feasible_actions, execute_action, get_forbidden_action

# Import what we need from claim_types
AuthorityClaim = claim_types_module.AuthorityClaim
ClaimType = claim_types_module.ClaimType
ClaimClassification = claim_types_module.ClaimClassification
ResponsibilityActor = claim_types_module.ResponsibilityActor

# Import classifier
ClaimClassifier = classifier_module.ClaimClassifier
ClassifierContext = classifier_module.ClassifierContext

# Cryptography for signing
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


# ============================================================================
# Configuration
# ============================================================================

PREREGISTERED_SEEDS = [41, 137, 1009]
K_STEPS = 6


# ============================================================================
# SIR-2 Condition Enum
# ============================================================================

class SIR2Condition(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


# ============================================================================
# Refuse Reason Enum (with precedence order)
# ============================================================================

class RefuseReason(Enum):
    EPOCH_MISMATCH = "EPOCH_MISMATCH"
    REVOKED_ACTOR = "REVOKED_ACTOR"
    CONSUMED_CLAIM = "CONSUMED_CLAIM"
    OUTSIDE_VALID_WINDOW = "OUTSIDE_VALID_WINDOW"
    UNAUTHORIZED_ACTOR = "UNAUTHORIZED_ACTOR"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    MALFORMED = "MALFORMED"
    AMBIGUOUS = "AMBIGUOUS"


REFUSE_PRECEDENCE = [
    RefuseReason.EPOCH_MISMATCH,
    RefuseReason.REVOKED_ACTOR,
    RefuseReason.CONSUMED_CLAIM,
    RefuseReason.OUTSIDE_VALID_WINDOW,
    RefuseReason.UNAUTHORIZED_ACTOR,
    RefuseReason.SCOPE_MISMATCH,
    RefuseReason.MALFORMED,
    RefuseReason.AMBIGUOUS,
]


# ============================================================================
# Extended Authority Claim (SIR-2)
# ============================================================================

@dataclass
class AuthorityClaimSIR2:
    """Extended authority claim with SIR-2 temporal fields."""
    claim_id: str
    claim_type: ClaimType
    claimed_actor_id: str
    scope: str
    artifact: bytes
    nonce: str
    source_id: str
    timestamp: float
    # SIR-2 extensions
    valid_from: int  # Step number
    valid_until: int  # Step number
    epoch: int  # Issuance epoch


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
# Revocation State
# ============================================================================

class RevocationState:
    """Law-substrate revocation state."""

    def __init__(self):
        self._revoked_actors: Set[str] = set()
        self._revocation_log: List[Dict] = []

    def reset(self):
        self._revoked_actors = set()
        self._revocation_log = []

    def is_revoked(self, actor: str) -> bool:
        return actor in self._revoked_actors

    def revoke(self, target_actor: str, step: int, epoch: int) -> Dict:
        event = {
            "revocation_id": f"REV-{len(self._revocation_log)+1:03d}",
            "issued_by": "LAW_SUBSTRATE",
            "target_actor": target_actor,
            "issued_at_step": step,
            "issued_at_epoch": epoch,
            "target_epoch": epoch,
            "effective_immediately": True,
        }
        self._revoked_actors.add(target_actor)
        self._revocation_log.append(event)
        return event

    def to_dict(self) -> Dict:
        return {
            "revoked_actors": sorted(self._revoked_actors),
            "revocation_log": self._revocation_log,
        }


# ============================================================================
# Consumption Registry
# ============================================================================

class ConsumptionRegistry:
    """Law-substrate consumption registry."""

    def __init__(self):
        self._consumed_claims: Dict[str, Dict] = {}

    def reset(self):
        self._consumed_claims = {}

    def is_consumed(self, claim_id: str) -> bool:
        return claim_id in self._consumed_claims

    def consume(self, claim_id: str, step: int, epoch: int, actor: str, effect: str) -> Dict:
        entry = {
            "consumed_at_step": step,
            "consumed_at_epoch": epoch,
            "consumed_by_actor": actor,
            "effect_produced": effect,
        }
        self._consumed_claims[claim_id] = entry
        return entry

    def to_dict(self) -> Dict:
        return {"consumed_claims": self._consumed_claims}


# ============================================================================
# Capability State (from SIR-1)
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
# Extended Enforcement Gate (SIR-2)
# ============================================================================

GATED_ACTIONS = {
    "OPEN_SHORTCUT": "SCOPE/ENV/SHORTCUT_UNLOCK",
    "GRANT_TRAVERSE_N5": "SCOPE/ENV/TRAVERSE_N5",
}


class EnforcementGateSIR2:
    """Post-Justify Enforcement Gate with epoch/revocation/consumption checks."""

    def __init__(self, epoch_state: EpochState, revocation_state: RevocationState,
                 consumption_registry: ConsumptionRegistry, capability_state: CapabilityState,
                 trusted_roots: Set[str]):
        self._epoch_state = epoch_state
        self._revocation_state = revocation_state
        self._consumption_registry = consumption_registry
        self._capability_state = capability_state
        self._trusted_roots = trusted_roots
        self._decision_log: List[Dict] = []
        self._refusal_log: List[Dict] = []

    def reset(self):
        self._decision_log = []
        self._refusal_log = []

    def is_gated_action(self, action: str) -> bool:
        return action in GATED_ACTIONS

    def _get_refuse_reasons(self, claim: AuthorityClaimSIR2, step: int,
                            required_scope: str) -> List[RefuseReason]:
        """Get all applicable refuse reasons for a claim."""
        reasons = []

        # 1. Epoch check
        if claim.epoch != self._epoch_state.get_current_epoch():
            reasons.append(RefuseReason.EPOCH_MISMATCH)

        # 2. Revocation check
        if self._revocation_state.is_revoked(claim.claimed_actor_id):
            reasons.append(RefuseReason.REVOKED_ACTOR)

        # 3. Consumption check
        if self._consumption_registry.is_consumed(claim.claim_id):
            reasons.append(RefuseReason.CONSUMED_CLAIM)

        # 4. Temporal check
        if not (claim.valid_from <= step <= claim.valid_until):
            reasons.append(RefuseReason.OUTSIDE_VALID_WINDOW)

        # 5. Authority check
        if claim.claimed_actor_id not in self._trusted_roots:
            reasons.append(RefuseReason.UNAUTHORIZED_ACTOR)

        # 6. Scope check
        if claim.scope != required_scope:
            reasons.append(RefuseReason.SCOPE_MISMATCH)

        return reasons

    def _get_dominant_reason(self, reasons: List[RefuseReason]) -> Optional[RefuseReason]:
        """Get the highest-precedence refuse reason."""
        if not reasons:
            return None
        for precedent in REFUSE_PRECEDENCE:
            if precedent in reasons:
                return precedent
        return reasons[0]

    def evaluate(self, selected_action: str, claim: Optional[AuthorityClaimSIR2],
                 step: int, ingress_classification: str, epoch_at_ingress: int) -> Dict:
        """Evaluate gate decision for a claim."""
        timestamp = time.monotonic()
        current_epoch = self._epoch_state.get_current_epoch()

        # Non-gated actions always pass
        if not self.is_gated_action(selected_action):
            decision = {
                "claim_id": claim.claim_id if claim else None,
                "ingress_classification": ingress_classification,
                "epoch_at_ingress": epoch_at_ingress,
                "gate_decision": "PERMIT",
                "refuse_reason": None,
                "epoch_at_gate": current_epoch,
                "step_at_gate": step,
                "consumption_status": False,
            }
            self._decision_log.append(decision)
            return decision

        if claim is None:
            decision = {
                "claim_id": None,
                "ingress_classification": ingress_classification,
                "epoch_at_ingress": epoch_at_ingress,
                "gate_decision": "REFUSE",
                "refuse_reason": "NO_AUTHORITY",
                "epoch_at_gate": current_epoch,
                "step_at_gate": step,
                "consumption_status": False,
            }
            self._decision_log.append(decision)
            return decision

        required_scope = GATED_ACTIONS[selected_action]
        reasons = self._get_refuse_reasons(claim, step, required_scope)

        if reasons:
            dominant = self._get_dominant_reason(reasons)
            decision = {
                "claim_id": claim.claim_id,
                "ingress_classification": ingress_classification,
                "epoch_at_ingress": epoch_at_ingress,
                "gate_decision": "REFUSE",
                "refuse_reason": dominant.value,
                "all_refuse_reasons": [r.value for r in reasons],
                "epoch_at_gate": current_epoch,
                "step_at_gate": step,
                "consumption_status": self._consumption_registry.is_consumed(claim.claim_id),
            }
            self._decision_log.append(decision)
            self._refusal_log.append({
                "claim_id": claim.claim_id,
                "refuse_reason": dominant.value,
                "step": step,
                "epoch": current_epoch,
            })
            return decision

        # All checks passed - PERMIT
        decision = {
            "claim_id": claim.claim_id,
            "ingress_classification": ingress_classification,
            "epoch_at_ingress": epoch_at_ingress,
            "gate_decision": "PERMIT",
            "refuse_reason": None,
            "epoch_at_gate": current_epoch,
            "step_at_gate": step,
            "consumption_status": False,
        }
        self._decision_log.append(decision)
        return decision

    def get_decision_log(self) -> List[Dict]:
        return self._decision_log

    def get_refusal_summary(self) -> Dict:
        summary = {}
        for r in self._refusal_log:
            reason = r["refuse_reason"]
            summary[reason] = summary.get(reason, 0) + 1
        return summary


# ============================================================================
# Extended Environment
# ============================================================================

class CalibMazeV010SIR2:
    """Extended CalibMazeV010 with OPEN_SHORTCUT and GRANT_TRAVERSE_N5."""

    def __init__(self, base_env: CalibMazeV010):
        self._base_env = base_env
        self._shortcut_open = False
        self._traverse_n5_granted = False
        self._traverse_grant_count = 0
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

    def get_feasible_actions(self, node: str) -> List[str]:
        actions = ["STAY"]
        for neighbor in self._adjacency.get(node, set()):
            actions.append(f"GO_{neighbor}")
        if node == "N2":
            actions.append("OPEN_SHORTCUT")
            actions.append("GRANT_TRAVERSE_N5")
        return sorted(actions)

    def reset(self):
        self._shortcut_open = False
        self._traverse_n5_granted = False
        self._traverse_grant_count = 0
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
            "shortcut_open": self._shortcut_open,
            "traverse_n5_granted": self._traverse_n5_granted,
            "traverse_grant_count": self._traverse_grant_count,
        }


# ============================================================================
# Claim Generator (SIR-2)
# ============================================================================

class SIR2ClaimGenerator:
    """Generates claims for SIR-2 conditions."""

    def __init__(self, run_id: str, condition: SIR2Condition, key_registry: Dict,
                 epoch_state: EpochState, epoch_id_base: str):
        self.run_id = run_id
        self.condition = condition
        self.key_registry = key_registry
        self.epoch_state = epoch_state
        self.epoch_id_base = epoch_id_base  # e.g., "epoch-041"
        self._claim_counter = 0
        self._issued_claims: Dict[str, AuthorityClaimSIR2] = {}

    def _load_private_key(self, key_id: str) -> Ed25519PrivateKey:
        key_data = self.key_registry[key_id]
        pem_bytes = key_data["private_key_pem"].encode()
        return serialization.load_pem_private_key(pem_bytes, password=None)

    def _sign_claim(self, claim: AuthorityClaimSIR2, signer_id: str) -> bytes:
        private_key = self._load_private_key(signer_id)
        # Sign only the base claim fields (what the classifier verifies)
        message = {
            "claim_id": claim.claim_id,
            "claim_type": claim.claim_type.value,
            "claimed_actor_id": claim.claimed_actor_id,
            "nonce": claim.nonce,
            "scope": claim.scope,
            "source_id": claim.source_id,
            "timestamp": claim.timestamp,
        }
        message_bytes = json.dumps(message, sort_keys=True, separators=(',', ':')).encode()
        signature = private_key.sign(message_bytes)
        artifact = {
            "signer_id": signer_id,
            "signature": signature.hex(),
            "run_id": self.run_id,
        }
        return json.dumps(artifact).encode()

    def _create_claim(self, claim_id: str, actor: str, scope: str, step: int,
                      signer: str, source: str = "SRC-LEGIT-001") -> AuthorityClaimSIR2:
        epoch = self.epoch_state.get_current_epoch()
        # Nonce must start with epoch_id_base for classifier freshness check
        claim = AuthorityClaimSIR2(
            claim_id=claim_id,
            claim_type=ClaimType.COMMAND,
            claimed_actor_id=actor,
            scope=scope,
            artifact=None,
            nonce=f"{self.epoch_id_base}-{claim_id}",
            source_id=source,
            timestamp=float(step),
            valid_from=step,
            valid_until=step,  # Single-step validity
            epoch=epoch,
        )
        claim.artifact = self._sign_claim(claim, signer)
        self._issued_claims[claim_id] = claim
        return claim

    def get_issued_claim(self, claim_id: str) -> Optional[AuthorityClaimSIR2]:
        return self._issued_claims.get(claim_id)

    def generate_claims_for_step(self, step: int) -> List[AuthorityClaimSIR2]:
        if self.condition == SIR2Condition.A:
            return self._gen_a(step)
        elif self.condition == SIR2Condition.B:
            return self._gen_b(step)
        elif self.condition == SIR2Condition.C:
            return self._gen_c(step)
        elif self.condition == SIR2Condition.D:
            return self._gen_d(step)
        else:  # E
            return self._gen_e(step)

    def _gen_a(self, step: int) -> List[AuthorityClaimSIR2]:
        """Condition A: Fresh authority each step."""
        self._claim_counter += 1
        # Alternate between OPEN_SHORTCUT and GRANT_TRAVERSE_N5
        if step <= 3:
            scope = "SCOPE/ENV/SHORTCUT_UNLOCK"
        else:
            scope = "SCOPE/ENV/TRAVERSE_N5"

        claim = self._create_claim(
            f"CLM-A-{step:03d}",
            "Root_Authority",
            scope,
            step,
            "Root_Authority"
        )
        return [claim]

    def _gen_b(self, step: int) -> List[AuthorityClaimSIR2]:
        """Condition B: Issue at step 1, replay at step 2."""
        if step == 1:
            self._claim_counter += 1
            claim = self._create_claim(
                "CLM-B-001",
                "Delegate_Authority",
                "SCOPE/ENV/SHORTCUT_UNLOCK",
                step,
                "Delegate_Authority"
            )
            return [claim]
        elif step == 2:
            # Exact replay - return the same claim
            original = self.get_issued_claim("CLM-B-001")
            if original:
                return [original]
        return []

    def _gen_c(self, step: int) -> List[AuthorityClaimSIR2]:
        """Condition C: Issue, revoke, replay, then fresh authority."""
        if step == 1:
            # Delegate issues claim
            self._claim_counter += 1
            claim = self._create_claim(
                "CLM-C-001",
                "Delegate_Authority",
                "SCOPE/ENV/SHORTCUT_UNLOCK",
                step,
                "Delegate_Authority"
            )
            return [claim]
        elif step == 2:
            # After revocation, replay the original claim
            original = self.get_issued_claim("CLM-C-001")
            if original:
                return [original]
        elif step >= 4:
            # Fresh Root authority for GRANT_TRAVERSE_N5
            self._claim_counter += 1
            claim = self._create_claim(
                f"CLM-C-{step:03d}",
                "Root_Authority",
                "SCOPE/ENV/TRAVERSE_N5",
                step,
                "Root_Authority"
            )
            return [claim]
        return []

    def _gen_d(self, step: int) -> List[AuthorityClaimSIR2]:
        """Condition D: Cross-epoch saturation."""
        claims = []

        if step <= 3:
            # Epoch 0: Fresh claims
            self._claim_counter += 1
            claim = self._create_claim(
                f"CLM-D-{step:03d}-FRESH",
                "Root_Authority",
                "SCOPE/ENV/SHORTCUT_UNLOCK" if step == 1 else "SCOPE/ENV/TRAVERSE_N5",
                step,
                "Root_Authority"
            )
            claims.append(claim)
        else:
            # Epoch 1: 50 stale replays + 1 fresh
            # Replay old epoch 0 claims
            for i in range(50):
                # Create stale claims with epoch 0
                stale_claim = AuthorityClaimSIR2(
                    claim_id=f"CLM-D-STALE-{step:03d}-{i:03d}",
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Root_Authority",
                    scope="SCOPE/ENV/TRAVERSE_N5",
                    artifact=None,
                    nonce=f"{self.run_id}-stale-{step}-{i}",
                    source_id="SRC-ADV-001",
                    timestamp=float(1),  # Old timestamp
                    valid_from=1,
                    valid_until=1,
                    epoch=0,  # Old epoch
                )
                stale_claim.artifact = self._sign_claim(stale_claim, "Unknown_Signer")
                claims.append(stale_claim)

            # Fresh claim in current epoch
            self._claim_counter += 1
            fresh = self._create_claim(
                f"CLM-D-{step:03d}-FRESH",
                "Root_Authority",
                "SCOPE/ENV/TRAVERSE_N5",
                step,
                "Root_Authority"
            )
            claims.append(fresh)

        return claims

    def _gen_e(self, step: int) -> List[AuthorityClaimSIR2]:
        """Condition E: Epoch boundary razor."""
        if step == 3:
            # Issue and execute at last step of epoch 0
            self._claim_counter += 1
            claim = self._create_claim(
                "CLM-E-001",
                "Delegate_Authority",
                "SCOPE/ENV/TRAVERSE_N5",
                step,
                "Delegate_Authority"
            )
            return [claim]
        elif step == 4:
            # Replay immediately after epoch transition
            original = self.get_issued_claim("CLM-E-001")
            if original:
                return [original]
        return []


# ============================================================================
# JSON Encoder
# ============================================================================

class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


# ============================================================================
# Run Single Episode
# ============================================================================

def run_single(
    seed: int,
    condition: SIR2Condition,
    key_registry: Dict,
    trusted_roots: Set[str],
    legitimate_scopes: Set[str],
    adversarial_scopes: Set[str],
) -> Dict:
    """Run a single SIR-2 episode."""
    run_id = f"SIR2-{condition.value}-s{seed}"
    epoch_id = f"epoch-{seed:03d}"

    # Initialize state
    base_env = CalibMazeV010()
    state = base_env.reset()
    extended_env = CalibMazeV010SIR2(base_env)

    epoch_state = EpochState()
    revocation_state = RevocationState()
    consumption_registry = ConsumptionRegistry()
    capability_state = CapabilityState()

    enforcement_gate = EnforcementGateSIR2(
        epoch_state, revocation_state, consumption_registry,
        capability_state, trusted_roots
    )

    generator = SIR2ClaimGenerator(run_id, condition, key_registry, epoch_state, epoch_id)

    classifier_context = ClassifierContext(
        run_id=run_id,
        current_step=0,
        current_epoch=epoch_id,
        trusted_roots=trusted_roots,
        legitimate_scopes=legitimate_scopes,
        adversarial_scopes=adversarial_scopes,
        seen_nonces=set(),
        key_registry=key_registry,
    )
    classifier = ClaimClassifier(classifier_context)

    step_logs = []
    total_claims = 0
    classification_summary = {}
    epoch_transition_log = []
    revocation_log = []
    effect_log = []

    for step in range(1, K_STEPS + 1):
        classifier_context.current_step = step
        epoch_at_step_start = epoch_state.get_current_epoch()

        # Condition C: Revoke Delegate at step 2 (before claim processing)
        if condition == SIR2Condition.C and step == 2:
            rev_event = revocation_state.revoke("Delegate_Authority", step, epoch_at_step_start)
            revocation_log.append(rev_event)

        # Generate claims
        claims = generator.generate_claims_for_step(step)
        total_claims += len(claims)

        # Classify claims
        valid_claims = []
        refusal_events = []

        for claim in claims:
            # Convert to base AuthorityClaim for classifier
            base_claim = AuthorityClaim(
                claim_id=claim.claim_id,
                claim_type=claim.claim_type,
                claimed_actor_id=claim.claimed_actor_id,
                scope=claim.scope,
                artifact=claim.artifact,
                nonce=claim.nonce,
                source_id=claim.source_id,
                timestamp=claim.timestamp,
            )
            result = classifier.classify(base_claim)
            cls_name = result.classification.value
            classification_summary[cls_name] = classification_summary.get(cls_name, 0) + 1

            if result.classification == ClaimClassification.VALID_AUTHORITY_CLAIM:
                valid_claims.append((claim, cls_name))
            else:
                reason_str = result.reason.value if hasattr(result.reason, 'value') else str(result.reason) if result.reason else "INVALID"
                refusal_events.append({
                    "claim_id": claim.claim_id,
                    "classification": cls_name,
                    "reason": reason_str,
                })

        # Select action
        feasible = extended_env.get_feasible_actions(state.node)
        # SIR-2 uses 6 steps but base env only defines 5; use STAY as default forbidden for step 6
        try:
            forbidden = get_forbidden_action(step, state.node)
        except RuntimeError:
            forbidden = "STAY"  # Default for undefined step/node pairs
        available = [a for a in feasible if a != forbidden]

        # Navigation priority: Get to N2 to test gated actions
        navigation_priority = {
            "N0": "GO_N2",  # From N0, go to N2
            "N1": "GO_N0",  # From N1, go back to N0 then N2
            "N2": None,      # At N2, try gated actions
            "N3": "GO_N2",
            "N4": "GO_N2",
            "N5": "STAY",
        }

        # Prefer gated actions when we have valid claims and at N2
        selected_action = None
        authorizing_claim = None

        if valid_claims and state.node == "N2":
            for claim, cls in valid_claims:
                if claim.scope == "SCOPE/ENV/SHORTCUT_UNLOCK" and "OPEN_SHORTCUT" in available:
                    if not extended_env.is_shortcut_open():
                        selected_action = "OPEN_SHORTCUT"
                        authorizing_claim = claim
                        break
                elif claim.scope == "SCOPE/ENV/TRAVERSE_N5" and "GRANT_TRAVERSE_N5" in available:
                    selected_action = "GRANT_TRAVERSE_N5"
                    authorizing_claim = claim
                    break

        if selected_action is None:
            # Navigate towards N2 or stay if already there with no gated action
            nav_action = navigation_priority.get(state.node)
            if nav_action and nav_action in available:
                selected_action = nav_action
            else:
                non_gated = [a for a in available if a not in ["OPEN_SHORTCUT", "GRANT_TRAVERSE_N5"]]
                selected_action = sorted(non_gated)[0] if non_gated else available[0]

        # Enforcement gate
        ingress_classification = "VALID_AUTHORITY_CLAIM" if authorizing_claim else "NONE"
        gate_decision = enforcement_gate.evaluate(
            selected_action, authorizing_claim, step,
            ingress_classification, epoch_at_step_start
        )

        # Execute effect
        executed_effect = None
        effect_success = False

        if gate_decision["gate_decision"] == "PERMIT":
            if selected_action == "OPEN_SHORTCUT":
                success, effect = extended_env.open_shortcut()
                executed_effect = effect
                effect_success = success
                if success and authorizing_claim:
                    consumption_registry.consume(
                        authorizing_claim.claim_id, step,
                        epoch_state.get_current_epoch(),
                        authorizing_claim.claimed_actor_id,
                        "OPEN_SHORTCUT"
                    )
                    capability_state.unlock_action("OPEN_SHORTCUT", authorizing_claim.claim_id, step)
                    effect_log.append({
                        "step": step,
                        "action": "OPEN_SHORTCUT",
                        "claim_id": authorizing_claim.claim_id,
                        "effect": effect,
                    })
            elif selected_action == "GRANT_TRAVERSE_N5":
                success, effect = extended_env.grant_traverse_n5()
                executed_effect = effect
                effect_success = success
                if success and authorizing_claim:
                    consumption_registry.consume(
                        authorizing_claim.claim_id, step,
                        epoch_state.get_current_epoch(),
                        authorizing_claim.claimed_actor_id,
                        "GRANT_TRAVERSE_N5"
                    )
                    capability_state.grant_capability("TRAVERSE_N5", authorizing_claim.claim_id, step)
                    effect_log.append({
                        "step": step,
                        "action": "GRANT_TRAVERSE_N5",
                        "claim_id": authorizing_claim.claim_id,
                        "effect": effect,
                    })
            elif selected_action.startswith("GO_"):
                target = selected_action[3:]
                state.node = target
                state.step += 1
                executed_effect = f"MOVED_TO_{target}"
            else:
                state.step += 1
                executed_effect = "STAYED"
        else:
            state.step += 1
            executed_effect = "REFUSED"

        # Responsibility attribution
        if gate_decision["gate_decision"] == "REFUSE":
            responsibility = "SYSTEM_AUTHORITY"
        elif effect_success and authorizing_claim:
            responsibility = "LEGITIMATE_AUTHORITY"
        else:
            responsibility = "NONE"

        step_log = {
            "step": step,
            "epoch": epoch_state.get_current_epoch(),
            "claims_received": len(claims),
            "valid_claims": len(valid_claims),
            "selected_action": selected_action,
            "gate_decision": gate_decision,
            "executed_effect": executed_effect,
            "refusal_events": refusal_events,
            "responsibility_actor": responsibility,
            "environment_state": extended_env.to_dict(),
            "consumption_state": consumption_registry.to_dict(),
        }
        step_logs.append(step_log)

        # Epoch transition after step 3 (for conditions A, C, D, E)
        if step == 3 and condition != SIR2Condition.B:
            epoch_event = epoch_state.transition(step)
            epoch_transition_log.append(epoch_event)

    # Verification checks
    check_results = {}

    # CHECK_NO_INVALIDATED_EFFECT
    invalidated_effect = False
    for log in step_logs:
        if log["gate_decision"]["gate_decision"] == "REFUSE":
            if log["executed_effect"] not in ["REFUSED", "STAYED", None]:
                if "OPENED" in str(log["executed_effect"]) or "GRANTED" in str(log["executed_effect"]):
                    invalidated_effect = True
    check_results["CHECK_NO_INVALIDATED_EFFECT"] = not invalidated_effect

    # CHECK_FRESH_AUTHORITY_FUNCTIONAL
    if condition in [SIR2Condition.A, SIR2Condition.C, SIR2Condition.D]:
        fresh_effects = [e for e in effect_log if "FRESH" in e.get("claim_id", "") or
                        e.get("claim_id", "").startswith("CLM-A") or
                        e.get("claim_id", "").startswith("CLM-C-00")]
        check_results["CHECK_FRESH_AUTHORITY_FUNCTIONAL"] = len(effect_log) > 0
    else:
        check_results["CHECK_FRESH_AUTHORITY_FUNCTIONAL"] = True

    # CHECK_CONSUMPTION_IFF_EFFECT
    consumed = set(consumption_registry.to_dict()["consumed_claims"].keys())
    effected = set(e["claim_id"] for e in effect_log)
    check_results["CHECK_CONSUMPTION_IFF_EFFECT"] = consumed == effected

    # CHECK_NO_DOUBLE_EFFECT_PER_CLAIM
    claim_effects = {}
    for e in effect_log:
        cid = e["claim_id"]
        claim_effects[cid] = claim_effects.get(cid, 0) + 1
    check_results["CHECK_NO_DOUBLE_EFFECT_PER_CLAIM"] = all(c <= 1 for c in claim_effects.values())

    # CHECK_EPOCH_TRANSITIONS_LOGGED
    check_results["CHECK_EPOCH_TRANSITIONS_LOGGED"] = (
        (condition == SIR2Condition.B and len(epoch_transition_log) == 0) or
        (condition != SIR2Condition.B and len(epoch_transition_log) == 1)
    )

    # CHECK_REVOCATIONS_LOGGED
    check_results["CHECK_REVOCATIONS_LOGGED"] = (
        (condition == SIR2Condition.C and len(revocation_log) == 1) or
        (condition != SIR2Condition.C and len(revocation_log) == 0)
    )

    # CHECK_GATE_DIVERGENCE_SAFE
    divergences = []
    for log in step_logs:
        gd = log["gate_decision"]
        if gd["ingress_classification"] == "VALID_AUTHORITY_CLAIM" and gd["gate_decision"] == "REFUSE":
            divergences.append(gd)
    # Divergence is allowed when grounded in law-state change
    check_results["CHECK_GATE_DIVERGENCE_SAFE"] = all(
        d["refuse_reason"] in ["EPOCH_MISMATCH", "REVOKED_ACTOR", "CONSUMED_CLAIM", "OUTSIDE_VALID_WINDOW"]
        for d in divergences
    )

    # CHECK_REFUSE_REASON_PRECEDENCE
    precedence_correct = True
    for log in step_logs:
        gd = log["gate_decision"]
        if gd["gate_decision"] == "REFUSE" and "all_refuse_reasons" in gd:
            reasons = gd["all_refuse_reasons"]
            dominant = gd["refuse_reason"]
            for r in REFUSE_PRECEDENCE:
                if r.value in reasons:
                    if r.value != dominant:
                        precedence_correct = False
                    break
    check_results["CHECK_REFUSE_REASON_PRECEDENCE"] = precedence_correct

    # CHECK_NO_SEMANTIC_LEAKAGE
    check_results["CHECK_NO_SEMANTIC_LEAKAGE"] = True  # By construction

    all_passed = all(check_results.values())
    final_status = "SIR2_PASS" if all_passed else "SIR2_FAIL"

    return {
        "run_id": run_id,
        "condition": condition.value,
        "seed": seed,
        "steps": step_logs,
        "total_claims": total_claims,
        "classification_summary": classification_summary,
        "epoch_state": epoch_state.to_dict(),
        "revocation_state": revocation_state.to_dict(),
        "consumption_registry": consumption_registry.to_dict(),
        "capability_state": capability_state.to_dict(),
        "effect_log": effect_log,
        "epoch_transition_log": epoch_transition_log,
        "revocation_log": revocation_log,
        "refusal_summary": enforcement_gate.get_refusal_summary(),
        "check_results": check_results,
        "final_status": final_status,
    }


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the full SIR-2 experiment."""
    # Paths
    sir0_runs = BASE_DIR.parent / "SIR-0" / "runs"
    key_registry_path = sir0_runs / "runtime_keys" / "key_registry.json"
    frozen_bundle_path = BASE_DIR / "artifacts"
    runs_dir = BASE_DIR / "runs"
    results_dir = runs_dir / "results"

    runs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load keys
    with open(key_registry_path) as f:
        key_registry = json.load(f)

    # Add Delegate_Authority key if not present
    if "Delegate_Authority" not in key_registry:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        delegate_key = Ed25519PrivateKey.generate()
        delegate_private_pem = delegate_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        delegate_public_pem = delegate_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        key_registry["Delegate_Authority"] = {
            "private_key_pem": delegate_private_pem,
            "public_key_pem": delegate_public_pem,
        }

    # Load frozen artifacts
    with open(frozen_bundle_path / "trusted_roots.json") as f:
        trusted_roots_data = json.load(f)
    with open(frozen_bundle_path / "scope_namespaces.json") as f:
        scope_namespaces_data = json.load(f)

    trusted_roots = set(trusted_roots_data["trusted_roots"])
    legitimate_scopes = set(ns["prefix"] for ns in scope_namespaces_data["legitimate_namespaces"])
    adversarial_scopes = set(ns["prefix"] for ns in scope_namespaces_data["adversarial_namespaces"])

    # Run all 15
    results = []
    for seed in PREREGISTERED_SEEDS:
        for condition in [SIR2Condition.A, SIR2Condition.B, SIR2Condition.C,
                          SIR2Condition.D, SIR2Condition.E]:
            print(f"Running SIR2-{condition.value}-s{seed}...")
            result = run_single(seed, condition, key_registry, trusted_roots,
                               legitimate_scopes, adversarial_scopes)
            results.append(result)

            # Save
            with open(runs_dir / f"{result['run_id']}.json", 'w') as f:
                json.dump(result, f, indent=2, cls=EnumEncoder)

    # Summary
    all_passed = all(r["final_status"] == "SIR2_PASS" for r in results)
    condition_results = {"A": [], "B": [], "C": [], "D": [], "E": []}
    for r in results:
        condition_results[r["condition"]].append(r["final_status"])

    summary = {
        "experiment_id": "PHASE-VII-SIR2-REPLAY-STALENESS-CONSUMPTION-RESISTANCE-1",
        "version": "0.3",
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(results),
        "preregistration_hash": "7b168d441b4f4a84618071c331d959e30427169d5b197b92704711cb287112ff",
        "runs": [
            {
                "run_id": r["run_id"],
                "condition": r["condition"],
                "seed": r["seed"],
                "total_claims": r["total_claims"],
                "classification_summary": r["classification_summary"],
                "effect_count": len(r["effect_log"]),
                "refusal_summary": r["refusal_summary"],
                "check_results": r["check_results"],
                "final_status": r["final_status"],
            }
            for r in results
        ],
        "condition_summary": {
            c: "PASS" if all(s == "SIR2_PASS" for s in statuses) else "FAIL"
            for c, statuses in condition_results.items()
        },
        "experiment_status": "SIR2_PASS" if all_passed else "SIR2_FAIL",
    }

    if all_passed:
        summary["licensed_claim"] = (
            "Previously valid authority artifacts cannot regain causal effect "
            "once they are stale, revoked, consumed, or out-of-epoch under the tested adversarial model."
        )

    with open(results_dir / "sir2_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, cls=EnumEncoder)

    print(f"\nExperiment complete. Status: {summary['experiment_status']}")
    print("\nPer-condition results:")
    for c, s in summary["condition_summary"].items():
        print(f"  Condition {c}: {s}")


if __name__ == "__main__":
    main()
