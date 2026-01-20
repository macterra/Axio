"""
RSA-PoC v4.3 — DSL Types and Patch Operations

Extends v4.2 DSL with:
- POSITION_EQ condition operator for zone-specific prohibitions
- CAN_DELIVER_A / CAN_DELIVER_B condition operators for Repair B exceptions
- All v4.2 types remain unchanged

v4.3 supersedes v4.2. All v4.2 DSL constraints remain binding.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union


# ============================================================================
# Condition Types (extended from v4.2)
# ============================================================================


class ConditionOp(str, Enum):
    """Condition operators (closed vocabulary)."""
    # v4.1 operators
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    EQ = "EQ"
    GT = "GT"
    LT = "LT"
    IN_STATE = "IN_STATE"
    HAS_RESOURCE = "HAS_RESOURCE"
    TRUE = "TRUE"
    FALSE = "FALSE"
    # v4.2 operators
    REGIME_EQ = "REGIME_EQ"  # Check regime == value
    STAMPED = "STAMPED"  # Check stamped == True
    # v4.3 operators (S_B predicates)
    POSITION_EQ = "POSITION_EQ"  # Check position == zone_name
    CAN_DELIVER_A = "CAN_DELIVER_A"  # position==ZONE_A AND inventory contains item_A
    CAN_DELIVER_B = "CAN_DELIVER_B"  # position==ZONE_B AND inventory contains item_B


@dataclass
class Condition:
    """Rule condition with operator and arguments."""
    op: ConditionOp
    args: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        serialized_args = []
        for arg in self.args:
            if isinstance(arg, Condition):
                serialized_args.append(arg.to_dict())
            elif isinstance(arg, dict) and "op" in arg:
                serialized_args.append(arg)
            else:
                serialized_args.append(arg)
        return {
            "op": self.op.value,
            "args": serialized_args
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Condition":
        args = []
        for arg in d.get("args", []):
            if isinstance(arg, dict) and "op" in arg:
                args.append(cls.from_dict(arg))
            else:
                args.append(arg)
        return cls(
            op=ConditionOp(d["op"]),
            args=args
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Condition):
            return self.op == other.op and self.args == other.args
        return False

    def __hash__(self) -> int:
        return hash(json.dumps(self.to_dict(), sort_keys=True))


# ============================================================================
# Effect Types (inherited from v4.2)
# ============================================================================


class ActionClass(str, Enum):
    """Effect action classes."""
    MOVE = "MOVE"
    COLLECT = "COLLECT"
    DEPOSIT = "DEPOSIT"
    STAMP = "STAMP"  # v4.2 addition
    WAIT = "WAIT"
    ANY = "ANY"


class EffectType(str, Enum):
    """Effect type discriminator."""
    ACTION_CLASS = "ACTION_CLASS"
    OBLIGATION_TARGET = "OBLIGATION_TARGET"


@dataclass
class ObligationTarget:
    """Obligation target for multi-step satisfaction."""
    kind: str
    target_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "target_id": self.target_id}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ObligationTarget":
        return cls(kind=d["kind"], target_id=d["target_id"])

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ObligationTarget):
            return self.kind == other.kind and self.target_id == other.target_id
        if isinstance(other, dict):
            return self.kind == other.get("kind") and self.target_id == other.get("target_id")
        return False

    def __hash__(self) -> int:
        return hash((self.kind, self.target_id))


@dataclass
class Effect:
    """Rule effect."""
    effect_type: EffectType
    action_class: Optional[ActionClass] = None
    obligation_target: Optional[ObligationTarget] = None

    def __post_init__(self):
        if self.effect_type == EffectType.ACTION_CLASS:
            if self.action_class is None:
                raise ValueError("ACTION_CLASS effect requires action_class")
        elif self.effect_type == EffectType.OBLIGATION_TARGET:
            if self.obligation_target is None:
                raise ValueError("OBLIGATION_TARGET effect requires obligation_target")

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"effect_type": self.effect_type.value}
        if self.action_class is not None:
            d["action_class"] = self.action_class.value
        if self.obligation_target is not None:
            d["obligation_target"] = self.obligation_target.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Effect":
        effect_type = EffectType(d["effect_type"])
        action_class = ActionClass(d["action_class"]) if d.get("action_class") else None
        obligation_target = ObligationTarget.from_dict(d["obligation_target"]) if d.get("obligation_target") else None
        return cls(
            effect_type=effect_type,
            action_class=action_class,
            obligation_target=obligation_target
        )


# ============================================================================
# Rule Types
# ============================================================================


class RuleType(str, Enum):
    """Normative rule types."""
    PERMISSION = "PERMISSION"
    PROHIBITION = "PROHIBITION"
    OBLIGATION = "OBLIGATION"


@dataclass
class Rule:
    """
    Normative rule in typed DSL (v4.3).

    v4.2 addition: repair_epoch field for repaired rules.
    v4.3 addition: exception_condition field for UNLESS clauses.
    """
    id: str
    type: RuleType
    condition: Condition
    effect: Effect
    expires_episode: Optional[int] = None
    priority: int = 0
    repair_epoch: Optional[str] = None  # v4.2: Set after law repair
    exception_condition: Optional[Condition] = None  # v4.3: UNLESS clause

    def __post_init__(self):
        if not re.match(r"^R[0-9]+$", self.id):
            raise ValueError(f"Invalid rule id pattern: {self.id}")
        if self.expires_episode is not None and self.expires_episode < 0:
            raise ValueError(f"expires_episode must be >= 0, got {self.expires_episode}")
        # Convert dict condition to Condition object
        if isinstance(self.condition, dict):
            self.condition = Condition.from_dict(self.condition)
        # Convert dict effect to Effect object
        if isinstance(self.effect, dict):
            self.effect = Effect.from_dict(self.effect)
        # Convert dict exception_condition to Condition object
        if isinstance(self.exception_condition, dict):
            self.exception_condition = Condition.from_dict(self.exception_condition)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "type": self.type.value,
            "condition": self.condition.to_dict(),
            "effect": self.effect.to_dict(),
            "expires_episode": self.expires_episode,
            "priority": self.priority,
        }
        if self.repair_epoch is not None:
            d["repair_epoch"] = self.repair_epoch
        if self.exception_condition is not None:
            d["exception_condition"] = self.exception_condition.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Rule":
        exception_condition = None
        if d.get("exception_condition"):
            exception_condition = Condition.from_dict(d["exception_condition"])
        return cls(
            id=d["id"],
            type=RuleType(d["type"]),
            condition=Condition.from_dict(d["condition"]),
            effect=Effect.from_dict(d["effect"]),
            expires_episode=d.get("expires_episode"),
            priority=d.get("priority", 0),
            repair_epoch=d.get("repair_epoch"),
            exception_condition=exception_condition,
        )

    def copy(self) -> "Rule":
        """Create a copy of the rule."""
        return Rule.from_dict(self.to_dict())


# ============================================================================
# Patch Operation Types (v4.2, unchanged for v4.3)
# ============================================================================


class PatchOp(str, Enum):
    """
    Permitted patch operations for LAW_REPAIR.

    Per v4.2 spec, only these operations are allowed:
    - MODIFY_CONDITION: Replace or refine a rule's 'when' predicate
    - ADD_EXCEPTION: Add a conjunctive exception clause to a prohibition
    - CHANGE_PRIORITY: Only if needed for deadlock resolution

    Explicitly disallowed:
    - DELETE_RULE
    - ADD_NEW_DEFAULT_PERMISSION
    - ADD_FALLBACK
    """
    MODIFY_CONDITION = "MODIFY_CONDITION"
    ADD_EXCEPTION = "ADD_EXCEPTION"
    CHANGE_PRIORITY = "CHANGE_PRIORITY"  # Only if needed


@dataclass
class PatchOperation:
    """
    A single patch operation on a rule.

    target_rule_id: The rule to modify
    op: The operation type
    new_condition: For MODIFY_CONDITION, the new condition
    exception_condition: For ADD_EXCEPTION, the exception to add
    new_priority: For CHANGE_PRIORITY, the new priority value
    """
    target_rule_id: str
    op: PatchOp
    new_condition: Optional[Condition] = None
    exception_condition: Optional[Condition] = None
    new_priority: Optional[int] = None

    def __post_init__(self):
        if not re.match(r"^R[0-9]+$", self.target_rule_id):
            raise ValueError(f"Invalid target_rule_id pattern: {self.target_rule_id}")

        if self.op == PatchOp.MODIFY_CONDITION:
            if self.new_condition is None:
                raise ValueError("MODIFY_CONDITION requires new_condition")
        elif self.op == PatchOp.ADD_EXCEPTION:
            if self.exception_condition is None:
                raise ValueError("ADD_EXCEPTION requires exception_condition")
        elif self.op == PatchOp.CHANGE_PRIORITY:
            if self.new_priority is None:
                raise ValueError("CHANGE_PRIORITY requires new_priority")

        # Convert dict conditions to Condition objects
        if isinstance(self.new_condition, dict):
            self.new_condition = Condition.from_dict(self.new_condition)
        if isinstance(self.exception_condition, dict):
            self.exception_condition = Condition.from_dict(self.exception_condition)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "target_rule_id": self.target_rule_id,
            "op": self.op.value,
        }
        if self.new_condition is not None:
            d["new_condition"] = self.new_condition.to_dict()
        if self.exception_condition is not None:
            d["exception_condition"] = self.exception_condition.to_dict()
        if self.new_priority is not None:
            d["new_priority"] = self.new_priority
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PatchOperation":
        new_condition = Condition.from_dict(d["new_condition"]) if d.get("new_condition") else None
        exception_condition = Condition.from_dict(d["exception_condition"]) if d.get("exception_condition") else None
        return cls(
            target_rule_id=d["target_rule_id"],
            op=PatchOp(d["op"]),
            new_condition=new_condition,
            exception_condition=exception_condition,
            new_priority=d.get("new_priority"),
        )

    def apply(self, rule: Rule) -> Rule:
        """
        Apply this patch operation to a rule.

        Returns a new Rule with the patch applied.
        """
        if rule.id != self.target_rule_id:
            raise ValueError(f"Rule ID mismatch: {rule.id} != {self.target_rule_id}")

        new_rule = rule.copy()

        if self.op == PatchOp.MODIFY_CONDITION:
            new_rule.condition = self.new_condition

        elif self.op == PatchOp.ADD_EXCEPTION:
            # v4.3: Set exception_condition directly instead of modifying condition
            # The compiler will evaluate: rule is active iff condition AND NOT exception
            if new_rule.exception_condition is not None:
                # Combine with existing exception using OR
                new_rule.exception_condition = Condition(
                    op=ConditionOp.OR,
                    args=[new_rule.exception_condition, self.exception_condition]
                )
            else:
                new_rule.exception_condition = self.exception_condition

        elif self.op == PatchOp.CHANGE_PRIORITY:
            new_rule.priority = self.new_priority

        return new_rule


# ============================================================================
# Canonical Fingerprinting
# ============================================================================


def canonical_json(obj: Any) -> str:
    """
    Serialize object to canonical JSON.

    - Sort keys
    - No whitespace
    - Stable ordering
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def patch_fingerprint(patch_ops: List[PatchOperation]) -> str:
    """
    Compute canonical fingerprint for a list of patch operations.

    Returns 64-character hex string (SHA-256).
    """
    canonical = canonical_json([p.to_dict() for p in patch_ops])
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


# ============================================================================
# Justification Types (v4.3)
# ============================================================================


class Predicate(str, Enum):
    """Closed vocabulary for predicate claims."""
    PERMITS = "PERMITS"
    FORBIDS = "FORBIDS"
    OBLIGATES_TARGET = "OBLIGATES_TARGET"
    TARGET_SATISFIED = "TARGET_SATISFIED"
    PROGRESS_ACTION = "PROGRESS_ACTION"
    CONFLICTS_WITH = "CONFLICTS_WITH"


@dataclass
class Claim:
    """Typed predicate claim supporting an action."""
    predicate: Predicate
    args: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"predicate": self.predicate.value, "args": self.args}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Claim":
        return cls(predicate=Predicate(d["predicate"]), args=d["args"])


@dataclass
class JustificationV430:
    """
    Justification output from deliberator (v4.3).

    Same structure as v4.2 but with v4.3 context awareness.
    """
    action_id: str
    rule_refs: List[str]
    claims: List[Claim]
    counterfactual: Optional[str] = None

    def __post_init__(self):
        if not re.match(r"^A[0-9]+$", self.action_id):
            raise ValueError(f"Invalid action_id pattern: {self.action_id}")
        for ref in self.rule_refs:
            if not re.match(r"^R[0-9]+$", ref):
                raise ValueError(f"Invalid rule_ref pattern: {ref}")
        if len(self.claims) < 1:
            raise ValueError("claims must have at least 1 item")
        if len(self.rule_refs) < 1:
            raise ValueError("rule_refs must have at least 1 item")
        self.claims = [
            Claim.from_dict(c) if isinstance(c, dict) else c
            for c in self.claims
        ]

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "action_id": self.action_id,
            "rule_refs": self.rule_refs,
            "claims": [c.to_dict() for c in self.claims]
        }
        if self.counterfactual:
            d["counterfactual"] = self.counterfactual
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JustificationV430":
        return cls(
            action_id=d["action_id"],
            rule_refs=d["rule_refs"],
            claims=[Claim.from_dict(c) for c in d["claims"]],
            counterfactual=d.get("counterfactual")
        )


# ============================================================================
# Type Aliases
# ============================================================================

# NormativeRule is an alias for Rule for semantic clarity
NormativeRule = Rule


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Conditions
    "ConditionOp",
    "Condition",
    # Effects
    "ActionClass",
    "EffectType",
    "ObligationTarget",
    "Effect",
    # Rules
    "RuleType",
    "Rule",
    "NormativeRule",
    # Patch operations
    "PatchOp",
    "PatchOperation",
    "patch_fingerprint",
    "canonical_json",
    # Justifications
    "Predicate",
    "Claim",
    "JustificationV430",
]
