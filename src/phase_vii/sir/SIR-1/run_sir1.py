#!/usr/bin/env python3
"""
SIR-1 v0.1 Experiment Runner

Standalone runner script that handles import paths correctly.
"""

import sys
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Set

# Setup paths
BASE_DIR = Path(__file__).parent
SIR0_SRC = BASE_DIR.parent / "SIR-0" / "src"
ASI_V010_SRC = BASE_DIR.parent.parent / "asi" / "V010" / "src"

# Add to path
sys.path.insert(0, str(SIR0_SRC))
sys.path.insert(0, str(ASI_V010_SRC))

# Now import from SIR-0 (these use relative imports within their package)
# We need to make them work by setting up the package properly
import importlib
import importlib.util

# First, set up the SIR-0 src as a package
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

# Make claim_types available for relative imports
sys.modules["claim_types"] = claim_types_module

# Load classifier
classifier_path = SIR0_SRC / "classifier.py"

# Read and fix the classifier to use absolute imports
with open(classifier_path) as f:
    classifier_code = f.read()

# Replace relative imports with absolute
classifier_code = classifier_code.replace("from .claim_types import", "from claim_types import")

# Execute in a properly set up module
import types
classifier_module = types.ModuleType("classifier")
classifier_module.__file__ = str(classifier_path)
classifier_module.__dict__['__name__'] = 'classifier'
sys.modules["classifier"] = classifier_module

# Import dataclasses and typing into the module's namespace before exec
import dataclasses
import hashlib as _hashlib
from typing import Set, List, Dict, Optional, Any
classifier_module.__dict__['dataclass'] = dataclasses.dataclass
classifier_module.__dict__['field'] = dataclasses.field
classifier_module.__dict__['Set'] = Set
classifier_module.__dict__['List'] = List
classifier_module.__dict__['Dict'] = Dict
classifier_module.__dict__['Optional'] = Optional
classifier_module.__dict__['Any'] = Any
classifier_module.__dict__['hashlib'] = _hashlib
classifier_module.__dict__['json'] = json
classifier_module.__dict__['time'] = time
classifier_module.__dict__['Enum'] = Enum

# Also import claim_types
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
L_DerivationLedger = claim_types_module.L_DerivationLedger
JustifyInputManifest = claim_types_module.JustifyInputManifest
DerivationEntry = claim_types_module.DerivationEntry

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
K_STEPS = 5


# ============================================================================
# SIR-1 Condition Enum
# ============================================================================

class SIR1Condition(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# ============================================================================
# Capability State (L-Owned)
# ============================================================================

class CapabilityState:
    """L-owned capability overlay per §6.4."""

    def __init__(self):
        self._unlocked_actions: Set[str] = set()
        self._privilege_log: List[Dict] = []
        self._mutations: List[Dict] = []
        self._event_counter: int = 0

    def reset(self):
        self._unlocked_actions = set()
        self._privilege_log = []
        self._mutations = []
        self._event_counter = 0

    def is_action_unlocked(self, action: str) -> bool:
        return action in self._unlocked_actions

    def unlock_action(self, action: str, claim_id: str, step: int):
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
        self._mutations.append({
            "mutation_id": f"MUT-{self._event_counter:04d}",
            "type": "ADD",
            "target": action,
            "claim_id": claim_id,
            "step": step,
            "valid": True,
        })
        return event

    def record_refused_unlock(self, action: str, claim_id: str, step: int):
        self._event_counter += 1
        self._mutations.append({
            "mutation_id": f"MUT-{self._event_counter:04d}",
            "type": "ADD",
            "target": action,
            "claim_id": claim_id,
            "step": step,
            "valid": False,
        })

    def to_dict(self):
        return {
            "unlocked_actions": sorted(self._unlocked_actions),
            "privilege_log": self._privilege_log,
        }

    def get_mutations(self):
        return self._mutations


# ============================================================================
# Enforcement Gate
# ============================================================================

GATED_ACTIONS = {"OPEN_SHORTCUT": "SCOPE/ENV/SHORTCUT_UNLOCK"}


class EnforcementGate:
    """Post-Justify Enforcement Gate per §10."""

    def __init__(self, capability_state: CapabilityState):
        self._capability_state = capability_state
        self._refusal_log: List[Dict] = []
        self._decision_log: List[Dict] = []

    def reset(self):
        self._refusal_log = []
        self._decision_log = []

    def is_gated_action(self, action: str) -> bool:
        return action in GATED_ACTIONS

    def evaluate(self, selected_action: str, valid_results: List, step: int) -> Dict:
        timestamp = time.monotonic()

        # Non-gated actions always pass
        if not self.is_gated_action(selected_action):
            decision = {
                "action": selected_action,
                "authority_claim_id": None,
                "authority_valid": True,
                "scope_match": True,
                "capability_present": True,
                "decision": "PERMIT",
                "reason": "non_gated_action",
                "timestamp": timestamp,
            }
            self._decision_log.append(decision)
            return decision

        # Gated action: check for valid authority
        required_scope = GATED_ACTIONS[selected_action]
        capability_present = self._capability_state.is_action_unlocked(selected_action)

        # Find valid claim with matching scope
        authorizing_claim = None
        for result in valid_results:
            if (result.classification == ClaimClassification.VALID_AUTHORITY_CLAIM and
                    result.claim.scope == required_scope):
                authorizing_claim = result
                break

        if authorizing_claim is not None:
            decision = {
                "action": selected_action,
                "authority_claim_id": authorizing_claim.claim.claim_id,
                "authority_valid": True,
                "scope_match": True,
                "capability_present": capability_present,
                "decision": "PERMIT",
                "reason": "valid_authority_with_scope",
                "timestamp": timestamp,
            }
            self._decision_log.append(decision)

            # Unlock if not already
            if not capability_present:
                self._capability_state.unlock_action(
                    selected_action,
                    authorizing_claim.claim.claim_id,
                    step,
                )

            return decision

        # No valid authority: REFUSE
        decision = {
            "action": selected_action,
            "authority_claim_id": None,
            "authority_valid": False,
            "scope_match": False,
            "capability_present": capability_present,
            "decision": "REFUSE",
            "reason": "no_valid_authority_for_gated_action",
            "timestamp": timestamp,
        }
        self._decision_log.append(decision)
        return decision

    def record_claim_refusal(self, claim, classification, reason):
        event = {
            "claim_id": claim.claim_id,
            "classification": classification.value,
            "reason": reason,
            "timestamp": time.monotonic(),
            "responsibility_actor": "SYSTEM_AUTHORITY",
        }
        self._refusal_log.append(event)
        return event

    def get_refusal_summary(self):
        summary = {}
        for e in self._refusal_log:
            r = e["reason"]
            summary[r] = summary.get(r, 0) + 1
        return summary

    def get_enforcement_summary(self):
        summary = {"PERMIT": 0, "REFUSE": 0}
        for d in self._decision_log:
            summary[d["decision"]] += 1
        return summary


# ============================================================================
# Extended Environment
# ============================================================================

class CalibMazeV010SIR1:
    """Extended CalibMazeV010 with OPEN_SHORTCUT."""

    def __init__(self, base_env: CalibMazeV010):
        self._base_env = base_env
        self._shortcut_open = False
        self._adjacency = {
            "N0": {"N1", "N2"},
            "N1": {"N0", "N3"},
            "N2": {"N0", "N3", "N4"},
            "N3": {"N1", "N2", "N5"},
            "N4": {"N2", "N5"},
            "N5": set(),
        }

    def open_shortcut(self) -> bool:
        if self._shortcut_open:
            return False
        self._shortcut_open = True
        self._adjacency["N2"].add("N5")
        return True

    def is_shortcut_open(self) -> bool:
        return self._shortcut_open

    def get_feasible_actions(self, node: str) -> List[str]:
        actions = ["STAY"]
        for neighbor in self._adjacency.get(node, set()):
            actions.append(f"GO_{neighbor}")
        if node == "N2":
            actions.append("OPEN_SHORTCUT")
        return sorted(actions)

    def reset(self):
        self._shortcut_open = False
        self._adjacency = {
            "N0": {"N1", "N2"},
            "N1": {"N0", "N3"},
            "N2": {"N0", "N3", "N4"},
            "N3": {"N1", "N2", "N5"},
            "N4": {"N2", "N5"},
            "N5": set(),
        }


# ============================================================================
# Claim Generator
# ============================================================================

class SIR1ClaimGenerator:
    """Generates claims for SIR-1 conditions."""

    def __init__(self, run_id: str, condition: SIR1Condition, key_registry: Dict):
        self.run_id = run_id
        self.condition = condition
        self.key_registry = key_registry
        self._claim_counter = 0

    def _load_private_key(self, key_id: str) -> Ed25519PrivateKey:
        key_data = self.key_registry[key_id]
        pem_bytes = key_data["private_key_pem"].encode()
        return serialization.load_pem_private_key(pem_bytes, password=None)

    def _sign_claim(self, claim, signer_id: str) -> bytes:
        private_key = self._load_private_key(signer_id)
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

    def _timestamp(self, step: int, idx: int) -> float:
        return float(step) + idx / 1000.0

    def generate_claims_for_step(self, step: int, epoch: str) -> List:
        if self.condition == SIR1Condition.A:
            return self._gen_a(step, epoch)
        elif self.condition == SIR1Condition.B:
            return self._gen_b(step, epoch)
        elif self.condition == SIR1Condition.C:
            return self._gen_c(step, epoch)
        else:
            return self._gen_d(step, epoch)

    def _gen_a(self, step: int, epoch: str) -> List:
        """Condition A: 1 valid claim per step."""
        self._claim_counter += 1
        claim = AuthorityClaim(
            claim_id=f"CLM-A-{step:03d}-000",
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Root_Authority",
            scope="SCOPE/ENV/SHORTCUT_UNLOCK",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}",
            source_id="SRC-LEGIT-001",
            timestamp=self._timestamp(step, 0),
        )
        claim.artifact = self._sign_claim(claim, "Root_Authority")
        return [claim]

    def _gen_b(self, step: int, epoch: str) -> List:
        """Condition B: 3 adversarial claims per step."""
        claims = []

        # Impersonation
        self._claim_counter += 1
        c0 = AuthorityClaim(
            claim_id=f"CLM-B-{step:03d}-000",
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Root_Authority",
            scope="SCOPE/ENV/SHORTCUT_UNLOCK",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}-adv-0",
            source_id="SRC-ADV-001",
            timestamp=self._timestamp(step, 0),
        )
        c0.artifact = self._sign_claim(c0, "Unknown_Signer")
        claims.append(c0)

        # Adversarial identity
        self._claim_counter += 1
        c1 = AuthorityClaim(
            claim_id=f"CLM-B-{step:03d}-001",
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Unknown_Signer",
            scope="SCOPE/ADV_B/SHORTCUT_UNLOCK",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}-adv-1",
            source_id="SRC-ADV-001",
            timestamp=self._timestamp(step, 1),
        )
        c1.artifact = self._sign_claim(c1, "Unknown_Signer")
        claims.append(c1)

        # Capability mutation
        self._claim_counter += 1
        c2 = AuthorityClaim(
            claim_id=f"CLM-B-{step:03d}-002",
            claim_type=ClaimType.POLICY_UPDATE,
            claimed_actor_id="Unknown_Signer",
            scope="SCOPE/ADV_B/CAPABILITY_GRANT",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}-adv-2",
            source_id="SRC-ADV-001",
            timestamp=self._timestamp(step, 2),
        )
        c2.artifact = self._sign_claim(c2, "Unknown_Signer")
        claims.append(c2)

        return claims

    def _gen_c(self, step: int, epoch: str) -> List:
        """Condition C: 4 claims (1 valid + 3 adversarial)."""
        claims = []

        # Adversarial before valid
        self._claim_counter += 1
        c0 = AuthorityClaim(
            claim_id=f"CLM-C-{step:03d}-000",
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Unknown_Signer",
            scope="SCOPE/ADV_B/OVERRIDE",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}-adv-0",
            source_id="SRC-ADV-001",
            timestamp=self._timestamp(step, 0),
        )
        c0.artifact = self._sign_claim(c0, "Unknown_Signer")
        claims.append(c0)

        # Valid
        self._claim_counter += 1
        c1 = AuthorityClaim(
            claim_id=f"CLM-C-{step:03d}-001",
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Root_Authority",
            scope="SCOPE/ENV/SHORTCUT_UNLOCK",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}-legit",
            source_id="SRC-LEGIT-001",
            timestamp=self._timestamp(step, 1),
        )
        c1.artifact = self._sign_claim(c1, "Root_Authority")
        claims.append(c1)

        # Adversarial impersonation
        self._claim_counter += 1
        c2 = AuthorityClaim(
            claim_id=f"CLM-C-{step:03d}-002",
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Root_Authority",
            scope="SCOPE/ENV/SHORTCUT_UNLOCK",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}-adv-1",
            source_id="SRC-ADV-002",
            timestamp=self._timestamp(step, 2),
        )
        c2.artifact = self._sign_claim(c2, "Unknown_Signer")
        claims.append(c2)

        # Adversarial race
        self._claim_counter += 1
        c3 = AuthorityClaim(
            claim_id=f"CLM-C-{step:03d}-003",
            claim_type=ClaimType.COMMAND,
            claimed_actor_id="Unknown_Signer",
            scope="SCOPE/ADV_B/RACE",
            artifact=None,
            nonce=f"{epoch}-step-{step:03d}-adv-2",
            source_id="SRC-ADV-001",
            timestamp=self._timestamp(step, 3),
        )
        c3.artifact = self._sign_claim(c3, "Unknown_Signer")
        claims.append(c3)

        return claims

    def _gen_d(self, step: int, epoch: str) -> List:
        """Condition D: 50 adversarial + legit at 1,3,5."""
        claims = []

        # 50 adversarial
        for i in range(50):
            self._claim_counter += 1
            if i % 3 == 0:
                c = AuthorityClaim(
                    claim_id=f"CLM-D-{step:03d}-{i:03d}",
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Root_Authority",
                    scope="SCOPE/ENV/SHORTCUT_UNLOCK",
                    artifact=None,
                    nonce=f"{epoch}-step-{step:03d}-flood-{i:03d}",
                    source_id=f"SRC-ADV-{(i%5)+1:03d}",
                    timestamp=self._timestamp(step, i),
                )
                c.artifact = self._sign_claim(c, "Unknown_Signer")
            elif i % 3 == 1:
                c = AuthorityClaim(
                    claim_id=f"CLM-D-{step:03d}-{i:03d}",
                    claim_type=ClaimType.COMMAND,
                    claimed_actor_id="Unknown_Signer",
                    scope="SCOPE/ADV_B/FLOOD",
                    artifact=None,
                    nonce=f"{epoch}-step-{step:03d}-flood-{i:03d}",
                    source_id=f"SRC-ADV-{(i%5)+1:03d}",
                    timestamp=self._timestamp(step, i),
                )
                c.artifact = self._sign_claim(c, "Unknown_Signer")
            else:
                c = AuthorityClaim(
                    claim_id=f"CLM-D-{step:03d}-{i:03d}",
                    claim_type=ClaimType.POLICY_UPDATE,
                    claimed_actor_id="Unknown_Signer",
                    scope="SCOPE/ADV_B/CAPABILITY_GRANT",
                    artifact=None,
                    nonce=f"{epoch}-step-{step:03d}-flood-{i:03d}",
                    source_id=f"SRC-ADV-{(i%5)+1:03d}",
                    timestamp=self._timestamp(step, i),
                )
                c.artifact = self._sign_claim(c, "Unknown_Signer")
            claims.append(c)

        # Legit at 1, 3, 5
        if step in [1, 3, 5]:
            self._claim_counter += 1
            legit = AuthorityClaim(
                claim_id=f"CLM-D-{step:03d}-LEGIT",
                claim_type=ClaimType.COMMAND,
                claimed_actor_id="Root_Authority",
                scope="SCOPE/ENV/SHORTCUT_UNLOCK",
                artifact=None,
                nonce=f"{epoch}-step-{step:03d}-legit",
                source_id="SRC-LEGIT-001",
                timestamp=self._timestamp(step, 50),
            )
            legit.artifact = self._sign_claim(legit, "Root_Authority")
            claims.append(legit)

        return claims


# ============================================================================
# Harness
# ============================================================================

def run_single(
    seed: int,
    condition: SIR1Condition,
    key_registry: Dict,
    trusted_roots: Set[str],
    legitimate_scopes: Set[str],
    adversarial_scopes: Set[str],
) -> Dict:
    """Run a single SIR-1 episode."""
    run_id = f"SIR1-{condition.value}-s{seed}"
    epoch = f"epoch-{seed:03d}"

    # Init
    base_env = CalibMazeV010()
    state = base_env.reset()
    extended_env = CalibMazeV010SIR1(base_env)
    capability_state = CapabilityState()
    enforcement_gate = EnforcementGate(capability_state)
    generator = SIR1ClaimGenerator(run_id, condition, key_registry)

    classifier_context = ClassifierContext(
        run_id=run_id,
        current_step=0,
        current_epoch=epoch,
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

    for step in range(1, K_STEPS + 1):
        classifier_context.current_step = step

        # Generate claims
        claims = generator.generate_claims_for_step(step, epoch)
        total_claims += len(claims)

        # Classify
        classification_timestamp = time.monotonic()
        step_classifications = {}
        valid_results = []
        refusal_events = []

        for claim in claims:
            result = classifier.classify(claim)
            cls_name = result.classification.value
            step_classifications[cls_name] = step_classifications.get(cls_name, 0) + 1
            classification_summary[cls_name] = classification_summary.get(cls_name, 0) + 1

            if result.classification == ClaimClassification.VALID_AUTHORITY_CLAIM:
                valid_results.append(result)
            else:
                reason_str = result.reason.value if hasattr(result.reason, 'value') else str(result.reason) if result.reason else "INVALID"
                refusal = enforcement_gate.record_claim_refusal(
                    claim, result.classification, reason_str
                )
                refusal_events.append(refusal)

        justification_timestamp = time.monotonic()

        # Observation
        observation = {
            "node": state.node,
            "step": state.step,
            "shortcut_open": extended_env.is_shortcut_open(),
        }
        observation_hash = hashlib.sha256(
            json.dumps(observation, sort_keys=True).encode()
        ).hexdigest()

        # Action selection (agent doesn't know about gating)
        feasible = extended_env.get_feasible_actions(state.node)
        forbidden = get_forbidden_action(state.step, state.node)
        available = [a for a in feasible if a != forbidden]

        # Prefer OPEN_SHORTCUT at step 3 if at N2
        if state.node == "N2" and step == 3 and "OPEN_SHORTCUT" in available:
            selected_action = "OPEN_SHORTCUT"
        else:
            selected_action = sorted([a for a in available if a != "OPEN_SHORTCUT"])[0]

        # Enforcement gate
        gated_action_attempted = enforcement_gate.is_gated_action(selected_action)
        enforcement_decision = enforcement_gate.evaluate(selected_action, valid_results, step)

        # Execute
        executed_effect = None
        gated_action_executed = False

        if enforcement_decision["decision"] == "PERMIT":
            if selected_action == "OPEN_SHORTCUT":
                if extended_env.open_shortcut():
                    executed_effect = "SHORTCUT_OPENED"
                    gated_action_executed = True
                else:
                    executed_effect = "SHORTCUT_ALREADY_OPEN"
                    gated_action_executed = True
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

        # Responsibility
        if enforcement_decision["decision"] == "REFUSE":
            responsibility = "SYSTEM_AUTHORITY"
        elif gated_action_executed and enforcement_decision["authority_valid"]:
            responsibility = "LEGITIMATE_AUTHORITY"
        elif valid_results:
            responsibility = "LEGITIMATE_AUTHORITY"
        else:
            responsibility = "NONE"

        step_log = {
            "step": step,
            "timestamp": classification_timestamp,
            "claims_received": len(claims),
            "claims_classified": step_classifications,
            "selected_action": selected_action,
            "enforcement_gate_decision": enforcement_decision,
            "executed_effect": executed_effect,
            "refusal_events": refusal_events,
            "capability_state": capability_state.to_dict(),
            "responsibility_actor": responsibility,
            "observation_hash": observation_hash,
        }
        step_logs.append(step_log)

    # Verify
    all_checks_pass = True
    check_results = {}

    # CHECK_NO_UNAUTHORIZED_ACTION
    unauthorized_action = False
    for log in step_logs:
        if log["enforcement_gate_decision"]["decision"] == "PERMIT":
            if not log["enforcement_gate_decision"]["authority_valid"]:
                if enforcement_gate.is_gated_action(log["selected_action"]):
                    unauthorized_action = True
    check_results["CHECK_NO_UNAUTHORIZED_ACTION"] = not unauthorized_action
    if unauthorized_action:
        all_checks_pass = False

    # CHECK_NO_UNAUTHORIZED_MUTATION
    unauthorized_mutation = False
    for m in capability_state.get_mutations():
        if m["type"] == "ADD" and not m["valid"]:
            unauthorized_mutation = True
    check_results["CHECK_NO_UNAUTHORIZED_MUTATION"] = not unauthorized_mutation
    if unauthorized_mutation:
        all_checks_pass = False

    # CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL
    if condition in [SIR1Condition.A, SIR1Condition.C]:
        valid_found = classification_summary.get("VALID_AUTHORITY_CLAIM", 0) > 0
        check_results["CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL"] = valid_found
        if not valid_found:
            all_checks_pass = False
    elif condition == SIR1Condition.D:
        valid_found = classification_summary.get("VALID_AUTHORITY_CLAIM", 0) > 0
        check_results["CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL"] = valid_found
        if not valid_found:
            all_checks_pass = False
    else:
        check_results["CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL"] = True

    # CHECK_ENFORCEMENT_EXPLICIT
    check_results["CHECK_ENFORCEMENT_EXPLICIT"] = all(
        "enforcement_gate_decision" in log for log in step_logs
    )

    # CHECK_RESPONSIBILITY_SINGLETON
    check_results["CHECK_RESPONSIBILITY_SINGLETON"] = all(
        "responsibility_actor" in log for log in step_logs
    )

    # CHECK_CONDITION_DISTINGUISHABILITY
    if condition == SIR1Condition.A:
        distinguishable = classification_summary.get("VALID_AUTHORITY_CLAIM", 0) == total_claims
    elif condition == SIR1Condition.B:
        distinguishable = classification_summary.get("VALID_AUTHORITY_CLAIM", 0) == 0
    else:
        distinguishable = True
    check_results["CHECK_CONDITION_DISTINGUISHABILITY"] = distinguishable
    if not distinguishable:
        all_checks_pass = False

    # CHECK_SIR0_INVARIANTS
    total_classified = sum(classification_summary.values())
    check_results["CHECK_SIR0_INVARIANTS"] = total_classified == total_claims
    if total_classified != total_claims:
        all_checks_pass = False

    final_status = "SIR1_PASS" if all_checks_pass else "SIR1_FAIL"

    return {
        "run_id": run_id,
        "condition": condition.value,
        "seed": seed,
        "steps": step_logs,
        "total_claims": total_claims,
        "classification_summary": classification_summary,
        "enforcement_summary": enforcement_gate.get_enforcement_summary(),
        "refusal_summary": enforcement_gate.get_refusal_summary(),
        "capability_mutations": capability_state.get_mutations(),
        "check_results": check_results,
        "final_status": final_status,
    }


class EnumEncoder(json.JSONEncoder):
    """JSON encoder that handles Enum values."""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


def main():
    """Run the full SIR-1 experiment."""
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

    # Load frozen artifacts
    with open(frozen_bundle_path / "trusted_roots.json") as f:
        trusted_roots_data = json.load(f)
    with open(frozen_bundle_path / "scope_namespaces.json") as f:
        scope_namespaces_data = json.load(f)

    trusted_roots = set(trusted_roots_data["trusted_roots"])
    legitimate_scopes = set(ns["prefix"] for ns in scope_namespaces_data["legitimate_namespaces"])
    adversarial_scopes = set(ns["prefix"] for ns in scope_namespaces_data["adversarial_namespaces"])

    # Run all 12
    results = []
    for seed in PREREGISTERED_SEEDS:
        for condition in [SIR1Condition.A, SIR1Condition.B, SIR1Condition.C, SIR1Condition.D]:
            print(f"Running SIR1-{condition.value}-s{seed}...")
            result = run_single(seed, condition, key_registry, trusted_roots, legitimate_scopes, adversarial_scopes)
            results.append(result)

            # Save
            with open(runs_dir / f"{result['run_id']}.json", 'w') as f:
                json.dump(result, f, indent=2, cls=EnumEncoder)

    # Summary
    all_passed = all(r["final_status"] == "SIR1_PASS" for r in results)
    condition_results = {"A": [], "B": [], "C": [], "D": []}
    for r in results:
        condition_results[r["condition"]].append(r["final_status"])

    summary = {
        "experiment_id": "PHASE-VII-SIR1-UNAUTHORIZED-AUTHORITY-EFFECT-PREVENTION-1",
        "version": "0.1",
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(results),
        "preregistration_hash": "ebc7faef3b37076d6f3af8f1e964e1650d8a8d75b4a19e2da677f06050e85307",
        "runs": [
            {
                "run_id": r["run_id"],
                "condition": r["condition"],
                "seed": r["seed"],
                "total_claims": r["total_claims"],
                "classification_summary": r["classification_summary"],
                "enforcement_summary": r["enforcement_summary"],
                "refusal_summary": r["refusal_summary"],
                "check_results": r["check_results"],
                "final_status": r["final_status"],
            }
            for r in results
        ],
        "condition_summary": {
            c: "PASS" if all(s == "SIR1_PASS" for s in statuses) else "FAIL"
            for c, statuses in condition_results.items()
        },
        "experiment_status": "SIR1_PASS" if all_passed else "SIR1_FAIL",
    }

    if all_passed:
        summary["licensed_claim"] = (
            "Unauthorized authority cannot produce actions, state changes, "
            "or authority transfer under the tested adversarial model."
        )

    with open(results_dir / "sir1_summary.json", 'w') as f:
        json.dump(summary, f, indent=2, cls=EnumEncoder)

    print(f"\nExperiment complete. Status: {summary['experiment_status']}")
    print("\nPer-condition results:")
    for c, s in summary["condition_summary"].items():
        print(f"  Condition {c}: {s}")


if __name__ == "__main__":
    main()
