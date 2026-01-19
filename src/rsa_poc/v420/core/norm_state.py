"""
RSA-PoC v4.2 — NormState with Law Fingerprint

v4.2 additions:
- law_fingerprint: Content-addressed hash of the compiled law
- repair_epoch: Epoch identifier after law repair
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .dsl import (
    Rule,
    RuleType,
    Condition,
    ConditionOp,
    Effect,
    EffectType,
    ActionClass,
    ObligationTarget,
    canonical_json,
)


# ============================================================================
# Law Fingerprint
# ============================================================================


def law_fingerprint(rules: List[Rule]) -> str:
    """
    Compute content-addressed fingerprint of the law.

    Returns 64-character hex string (SHA-256).
    """
    canonical = canonical_json([r.to_dict() for r in rules])
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def norm_hash(rules: List[Rule]) -> str:
    """
    Compute short hash for norm state identity (first 16 chars).

    Used for quick comparisons and cross-law replay prevention.
    """
    return law_fingerprint(rules)[:16]


# ============================================================================
# NormState v4.2
# ============================================================================


@dataclass
class NormStateV420:
    """
    Normative state for v4.2.

    v4.2 additions:
    - law_fingerprint: Content-addressed hash
    - repair_epoch: Set after law repair
    """
    rules: List[Rule] = field(default_factory=list)
    repair_epoch: Optional[str] = None

    def __post_init__(self):
        # Ensure rules are Rule objects
        self.rules = [
            Rule.from_dict(r) if isinstance(r, dict) else r
            for r in self.rules
        ]

    @property
    def law_fingerprint(self) -> str:
        """Content-addressed fingerprint of the law."""
        return law_fingerprint(self.rules)

    @property
    def norm_hash(self) -> str:
        """Short hash for quick identity checks."""
        return norm_hash(self.rules)

    def has_rule(self, rule_id: str) -> bool:
        """Check if a rule exists by ID."""
        return any(r.id == rule_id for r in self.rules)

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        for r in self.rules:
            if r.id == rule_id:
                return r
        return None

    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Get all rules of a given type."""
        return [r for r in self.rules if r.type == rule_type]

    def expire_rules(self, episode: int) -> "NormStateV420":
        """Return new NormState with expired rules removed."""
        active_rules = [
            r for r in self.rules
            if r.expires_episode is None or episode < r.expires_episode
        ]
        return NormStateV420(rules=active_rules, repair_epoch=self.repair_epoch)

    def apply_patch(self, patched_rule: Rule) -> "NormStateV420":
        """Apply a patched rule (replace existing with same ID)."""
        new_rules = []
        replaced = False
        for r in self.rules:
            if r.id == patched_rule.id:
                new_rules.append(patched_rule)
                replaced = True
            else:
                new_rules.append(r)
        if not replaced:
            raise ValueError(f"Rule not found for patching: {patched_rule.id}")
        return NormStateV420(rules=new_rules, repair_epoch=self.repair_epoch)

    def with_repair_epoch(self, epoch: str) -> "NormStateV420":
        """Return new NormState with repair_epoch set."""
        return NormStateV420(rules=self.rules, repair_epoch=epoch)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "rules": [r.to_dict() for r in self.rules],
            "law_fingerprint": self.law_fingerprint,
            "norm_hash": self.norm_hash,
        }
        if self.repair_epoch is not None:
            d["repair_epoch"] = self.repair_epoch
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NormStateV420":
        return cls(
            rules=[Rule.from_dict(r) for r in d["rules"]],
            repair_epoch=d.get("repair_epoch"),
        )


# ============================================================================
# Initial Norm State Factory
# ============================================================================


def create_initial_norm_state_v420() -> NormStateV420:
    """
    Create the initial normative state for v4.2.

    v4.2 law includes:
    - R0: PERMISSION(MOVE) - Always can move
    - R1: OBLIGATION(DEPOSIT@ZONE_A) priority=10, expires_episode=2
    - R2: OBLIGATION(DEPOSIT@ZONE_B) priority=5
    - R3: OBLIGATION(DEPOSIT@ZONE_C) priority=5
    - R4: PERMISSION(COLLECT)
    - R5: PERMISSION(DEPOSIT)
    - R6: PROHIBITION(STAMP) - NEW: Creates contradiction under regime=1
    """
    rules = [
        # R0: Permission to move
        Rule(
            id="R0",
            type=RuleType.PERMISSION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.ACTION_CLASS,
                action_class=ActionClass.MOVE,
            ),
            priority=0,
        ),
        # R1: High-priority obligation to deposit at Zone A (expires)
        Rule(
            id="R1",
            type=RuleType.OBLIGATION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.OBLIGATION_TARGET,
                obligation_target=ObligationTarget(
                    kind="DEPOSIT_ZONE",
                    target_id="ZONE_A",
                ),
            ),
            priority=10,
            expires_episode=2,
        ),
        # R2: Obligation to deposit at Zone B
        Rule(
            id="R2",
            type=RuleType.OBLIGATION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.OBLIGATION_TARGET,
                obligation_target=ObligationTarget(
                    kind="DEPOSIT_ZONE",
                    target_id="ZONE_B",
                ),
            ),
            priority=5,
        ),
        # R3: Obligation to deposit at Zone C
        Rule(
            id="R3",
            type=RuleType.OBLIGATION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.OBLIGATION_TARGET,
                obligation_target=ObligationTarget(
                    kind="DEPOSIT_ZONE",
                    target_id="ZONE_C",
                ),
            ),
            priority=5,
        ),
        # R4: Permission to collect
        Rule(
            id="R4",
            type=RuleType.PERMISSION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.ACTION_CLASS,
                action_class=ActionClass.COLLECT,
            ),
            priority=0,
        ),
        # R5: Permission to deposit
        Rule(
            id="R5",
            type=RuleType.PERMISSION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.ACTION_CLASS,
                action_class=ActionClass.DEPOSIT,
            ),
            priority=0,
        ),
        # R6: PROHIBITION(STAMP) - Creates contradiction under regime=1
        # Agent cannot stamp, but under regime=1, stamping is required for deposit
        Rule(
            id="R6",
            type=RuleType.PROHIBITION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.ACTION_CLASS,
                action_class=ActionClass.STAMP,
            ),
            priority=0,
        ),
    ]
    return NormStateV420(rules=rules)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "NormStateV420",
    "law_fingerprint",
    "norm_hash",
    "create_initial_norm_state_v420",
]
