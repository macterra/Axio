"""
RSA-PoC v4.3 — NormState with Epoch-Chained Continuity

v4.3 additions over v4.2:
- R7: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A
- R8: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_B
- epoch_chain: [epoch_0, epoch_1, epoch_2] for multi-repair identity
- repair_count: Track number of repairs applied

v4.3 supersedes v4.2. All v4.2 constraints remain binding.
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
# Epoch Chain Construction (v4.3)
# ============================================================================


def compute_epoch_0(law_fp: str, env_nonce: bytes) -> str:
    """
    Compute epoch_0 := H(law_fingerprint || env_nonce_0)

    Initial epoch before any repairs.
    """
    h = hashlib.sha256()
    h.update(law_fp.encode('utf-8'))
    h.update(env_nonce)
    return h.hexdigest()


def compute_epoch_n(prior_epoch: str, repair_fingerprint: str, env_nonce: bytes) -> str:
    """
    Compute epoch_n := H(epoch_{n-1} || repair_fingerprint || env_nonce_n)

    Epoch after repair n.
    """
    h = hashlib.sha256()
    h.update(prior_epoch.encode('utf-8'))
    h.update(repair_fingerprint.encode('utf-8'))
    h.update(env_nonce)
    return h.hexdigest()


# ============================================================================
# NormState v4.3
# ============================================================================


@dataclass
class NormStateV430:
    """
    Normative state for v4.3.

    v4.3 additions over v4.2:
    - epoch_chain: List of epochs [epoch_0, epoch_1?, epoch_2?]
    - repair_count: Number of repairs applied (0, 1, or 2)
    - current_epoch: Latest epoch in chain

    Epoch chain semantics:
    - epoch_0: H(law_fingerprint_pre_A || nonce_0)
    - epoch_1: H(epoch_0 || repair_A_fingerprint || nonce_1)
    - epoch_2: H(epoch_1 || repair_B_fingerprint || nonce_2)
    """
    rules: List[Rule] = field(default_factory=list)
    epoch_chain: List[str] = field(default_factory=list)
    repair_count: int = 0

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

    @property
    def current_epoch(self) -> Optional[str]:
        """Latest epoch in chain (None if no epochs)."""
        return self.epoch_chain[-1] if self.epoch_chain else None

    @property
    def epoch_0(self) -> Optional[str]:
        """Initial epoch (before repairs)."""
        return self.epoch_chain[0] if len(self.epoch_chain) > 0 else None

    @property
    def epoch_1(self) -> Optional[str]:
        """Epoch after Repair A."""
        return self.epoch_chain[1] if len(self.epoch_chain) > 1 else None

    @property
    def epoch_2(self) -> Optional[str]:
        """Epoch after Repair B."""
        return self.epoch_chain[2] if len(self.epoch_chain) > 2 else None

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

    def expire_rules(self, episode: int) -> "NormStateV430":
        """Return new NormState with expired rules removed."""
        active_rules = [
            r for r in self.rules
            if r.expires_episode is None or episode < r.expires_episode
        ]
        return NormStateV430(
            rules=active_rules,
            epoch_chain=self.epoch_chain.copy(),
            repair_count=self.repair_count
        )

    def apply_patch(self, patched_rule: Rule) -> "NormStateV430":
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
        return NormStateV430(
            rules=new_rules,
            epoch_chain=self.epoch_chain.copy(),
            repair_count=self.repair_count
        )

    def initialize_epoch_0(self, env_nonce: bytes) -> "NormStateV430":
        """Initialize epoch_0 from current law fingerprint."""
        if self.epoch_chain:
            raise ValueError("epoch_chain already initialized")
        epoch_0 = compute_epoch_0(self.law_fingerprint, env_nonce)
        return NormStateV430(
            rules=self.rules,
            epoch_chain=[epoch_0],
            repair_count=0
        )

    def add_repair_epoch(self, repair_fingerprint: str, env_nonce: bytes) -> "NormStateV430":
        """Add new epoch after repair."""
        if not self.epoch_chain:
            raise ValueError("Cannot add repair epoch without epoch_0")
        if self.repair_count >= 2:
            raise ValueError("Cannot exceed 2 repairs")
        new_epoch = compute_epoch_n(self.current_epoch, repair_fingerprint, env_nonce)
        return NormStateV430(
            rules=self.rules,
            epoch_chain=self.epoch_chain + [new_epoch],
            repair_count=self.repair_count + 1
        )

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "rules": [r.to_dict() for r in self.rules],
            "law_fingerprint": self.law_fingerprint,
            "norm_hash": self.norm_hash,
            "epoch_chain": self.epoch_chain,
            "repair_count": self.repair_count,
        }
        if self.current_epoch:
            d["current_epoch"] = self.current_epoch
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NormStateV430":
        return cls(
            rules=[Rule.from_dict(r) for r in d["rules"]],
            epoch_chain=d.get("epoch_chain", []),
            repair_count=d.get("repair_count", 0),
        )


# ============================================================================
# Initial Norm State Factory (v4.3)
# ============================================================================


def create_initial_norm_state_v430() -> NormStateV430:
    """
    Create the initial normative state for v4.3.

    v4.3 law includes:
    - R0: PERMISSION(MOVE) - Always can move
    - R1: OBLIGATION(DEPOSIT@ZONE_A) priority=10, expires_episode=2
    - R2: OBLIGATION(DEPOSIT@ZONE_B) priority=5
    - R3: OBLIGATION(DEPOSIT@ZONE_C) priority=5
    - R4: PERMISSION(COLLECT)
    - R5: PERMISSION(DEPOSIT)
    - R9: PERMISSION(STAMP) - Baseline permission, blocked by R6
    - R6: PROHIBITION(STAMP) - Creates Contradiction A under regime=1
    - R7: PROHIBITION(DEPOSIT) IF regime==2 AND position==ZONE_A - Creates Contradiction B
    - R8: PROHIBITION(DEPOSIT) IF regime==2 AND position==ZONE_B - Creates Contradiction B
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
        # R9: Permission to stamp (baseline, before R6 prohibition)
        # This ensures STAMP is permitted when R6 prohibition is not active
        Rule(
            id="R9",
            type=RuleType.PERMISSION,
            condition=Condition(op=ConditionOp.TRUE),
            effect=Effect(
                effect_type=EffectType.ACTION_CLASS,
                action_class=ActionClass.STAMP,
            ),
            priority=0,
        ),
        # R6: PROHIBITION(STAMP) - Creates Contradiction A under regime=1
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
        # R7: PROHIBITION(DEPOSIT) at ZONE_A under regime=2
        # Condition: regime==2 AND position==ZONE_A
        # Creates Contradiction B (with R8)
        Rule(
            id="R7",
            type=RuleType.PROHIBITION,
            condition=Condition(
                op=ConditionOp.AND,
                args=[
                    Condition(op=ConditionOp.REGIME_EQ, args=[2]),
                    Condition(op=ConditionOp.POSITION_EQ, args=["ZONE_A"]),
                ]
            ),
            effect=Effect(
                effect_type=EffectType.ACTION_CLASS,
                action_class=ActionClass.DEPOSIT,
            ),
            priority=0,
        ),
        # R8: PROHIBITION(DEPOSIT) at ZONE_B under regime=2
        # Condition: regime==2 AND position==ZONE_B
        # Creates Contradiction B (with R7)
        Rule(
            id="R8",
            type=RuleType.PROHIBITION,
            condition=Condition(
                op=ConditionOp.AND,
                args=[
                    Condition(op=ConditionOp.REGIME_EQ, args=[2]),
                    Condition(op=ConditionOp.POSITION_EQ, args=["ZONE_B"]),
                ]
            ),
            effect=Effect(
                effect_type=EffectType.ACTION_CLASS,
                action_class=ActionClass.DEPOSIT,
            ),
            priority=0,
        ),
    ]
    return NormStateV430(rules=rules)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "NormStateV430",
    "law_fingerprint",
    "norm_hash",
    "compute_epoch_0",
    "compute_epoch_n",
    "create_initial_norm_state_v430",
]
