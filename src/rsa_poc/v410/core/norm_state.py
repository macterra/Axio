"""
RSA-PoC v4.1 — Normative State Manager
Implements §3.1, §3.2, §3.3 of v41_design_freeze.md

NormStateV410 with patch semantics, content-addressing,
and append-only ledger root tracking.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .dsl import (
    ActionClass,
    Condition,
    ConditionOp,
    Effect,
    EffectType,
    NormPatchV410,
    ObligationTarget,
    PatchOp,
    Rule,
    RuleType,
    canonicalize,
    content_hash,
    create_initial_rules,
    hash_rules,
)


# ============================================================================
# §3.1 — NormStateV410 Schema
# ============================================================================


@dataclass
class NormStateV410:
    """
    Normative state container per §3.1 of v4.1 design freeze.

    Fields:
    - norm_hash: Content-address of canonical ruleset (16 hex chars)
    - rules: Canonical rule list in typed DSL
    - rev: Monotone revision counter
    - last_patch_hash: Hash pointer to most recent patch (16 hex chars)
    - ledger_root: Merkle root of append-only history (16 hex chars)
    """
    norm_hash: str
    rules: List[Rule]
    rev: int
    last_patch_hash: str
    ledger_root: str

    def to_dict(self) -> Dict:
        return {
            "norm_hash": self.norm_hash,
            "rules": [r.to_dict() for r in self.rules],
            "rev": self.rev,
            "last_patch_hash": self.last_patch_hash,
            "ledger_root": self.ledger_root
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "NormStateV410":
        return cls(
            norm_hash=d["norm_hash"],
            rules=[Rule.from_dict(r) for r in d["rules"]],
            rev=d["rev"],
            last_patch_hash=d["last_patch_hash"],
            ledger_root=d["ledger_root"]
        )

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get rule by ID, or None if not found."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def has_rule(self, rule_id: str) -> bool:
        """Check if rule exists."""
        return self.get_rule(rule_id) is not None

    def get_active_rules(self, current_episode: int) -> List[Rule]:
        """Get rules that haven't expired by current episode."""
        return [
            r for r in self.rules
            if r.expires_episode is None or r.expires_episode > current_episode
        ]

    def get_obligations(self, current_episode: int) -> List[Rule]:
        """Get active OBLIGATION rules."""
        return [
            r for r in self.get_active_rules(current_episode)
            if r.type == RuleType.OBLIGATION
        ]

    def get_permissions(self, current_episode: int) -> List[Rule]:
        """Get active PERMISSION rules."""
        return [
            r for r in self.get_active_rules(current_episode)
            if r.type == RuleType.PERMISSION
        ]

    def get_prohibitions(self, current_episode: int) -> List[Rule]:
        """Get active PROHIBITION rules."""
        return [
            r for r in self.get_active_rules(current_episode)
            if r.type == RuleType.PROHIBITION
        ]


# ============================================================================
# §3.2 — Initial NormState
# ============================================================================


def create_initial_norm_state() -> NormStateV410:
    """
    Create the initial NormState per §3.2 of v4.1 design freeze.

    Initial rules:
    - R1: OBLIGATION to prioritize Zone A (expires episode 1, priority 10)
    - R2: OBLIGATION to satisfy Zone B (never expires, priority 5)
    - R3: PERMISSION to collect at source
    - R4: PERMISSION to move anywhere
    - R5: PERMISSION to deposit at zones when inventory > 0
    """
    rules = create_initial_rules()
    norm_hash = hash_rules(rules)

    return NormStateV410(
        norm_hash=norm_hash,
        rules=rules,
        rev=0,
        last_patch_hash="0000000000000000",
        ledger_root="0000000000000000"
    )


# ============================================================================
# §3.3 — Update Semantics
# ============================================================================


class PatchError(Exception):
    """Raised when a patch cannot be applied."""
    pass


def apply_patch(
    state: NormStateV410,
    patch: NormPatchV410
) -> Tuple[NormStateV410, str]:
    """
    Apply a NormPatch to the state per §3.3 update semantics.

    Steps:
    1. Apply NormPatch to rules list
    2. Increment rev
    3. Compute new norm_hash from canonical rules
    4. Set last_patch_hash to hash of the patch
    5. Update ledger_root by hashing (old_ledger_root || last_patch_hash)

    Returns:
        Tuple of (new_state, patch_hash)

    Raises:
        PatchError if the patch is invalid
    """
    # Deep copy rules
    new_rules = [Rule.from_dict(r.to_dict()) for r in state.rules]

    # Compute patch hash
    patch_hash = content_hash(patch.to_dict())

    # Apply operation
    if patch.op == PatchOp.ADD:
        # Check rule doesn't already exist
        if any(r.id == patch.target_rule_id for r in new_rules):
            raise PatchError(f"Rule {patch.target_rule_id} already exists")
        if patch.new_rule is None:
            raise PatchError("ADD requires new_rule")
        new_rules.append(patch.new_rule)

    elif patch.op == PatchOp.REMOVE:
        # Find and remove the rule
        found = False
        for i, r in enumerate(new_rules):
            if r.id == patch.target_rule_id:
                new_rules.pop(i)
                found = True
                break
        if not found:
            raise PatchError(f"Rule {patch.target_rule_id} not found for REMOVE")

    elif patch.op == PatchOp.REPLACE:
        # Find and replace the rule
        if patch.new_rule is None:
            raise PatchError("REPLACE requires new_rule")
        found = False
        for i, r in enumerate(new_rules):
            if r.id == patch.target_rule_id:
                new_rules[i] = patch.new_rule
                found = True
                break
        if not found:
            raise PatchError(f"Rule {patch.target_rule_id} not found for REPLACE")

    # Compute new hashes
    new_norm_hash = hash_rules(new_rules)

    # Compute new ledger root: hash(old_ledger_root || last_patch_hash)
    ledger_concat = state.ledger_root + patch_hash
    new_ledger_root = hashlib.sha256(ledger_concat.encode()).hexdigest()[:16]

    # Create new state
    new_state = NormStateV410(
        norm_hash=new_norm_hash,
        rules=new_rules,
        rev=state.rev + 1,
        last_patch_hash=patch_hash,
        ledger_root=new_ledger_root
    )

    return new_state, patch_hash


def expire_rules(state: NormStateV410, current_episode: int) -> NormStateV410:
    """
    Remove expired rules from the state.

    This is called at episode boundary to handle rule expiration.
    Does NOT increment rev (expiration is mechanical, not a patch).

    Note: R1 expires at episode 1, meaning at episode 2 start it is removed.
    The expires_episode field uses > comparison (expires when episode > value).
    """
    active_rules = [
        r for r in state.rules
        if r.expires_episode is None or r.expires_episode > current_episode
    ]

    if len(active_rules) == len(state.rules):
        return state  # No expiration

    # Recompute norm_hash
    new_norm_hash = hash_rules(active_rules)

    return NormStateV410(
        norm_hash=new_norm_hash,
        rules=active_rules,
        rev=state.rev,  # Not incremented for expiration
        last_patch_hash=state.last_patch_hash,
        ledger_root=state.ledger_root
    )


# ============================================================================
# State Persistence (for cross-episode continuity)
# ============================================================================


def serialize_state(state: NormStateV410) -> str:
    """Serialize state to canonical JSON string."""
    return canonicalize(state.to_dict())


def deserialize_state(json_str: str) -> NormStateV410:
    """Deserialize state from JSON string."""
    import json
    return NormStateV410.from_dict(json.loads(json_str))


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "NormStateV410",
    "create_initial_norm_state",
    "apply_patch",
    "expire_rules",
    "serialize_state",
    "deserialize_state",
    "PatchError",
]

