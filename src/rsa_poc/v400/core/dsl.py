"""
RSA-PoC v4.0 — DSL Validators and Canonicalization
Implements §1.1, §1.2, §1.3 of v40_design_freeze.md

JustificationV400 and NormPatchV400 schema validators with
deterministic canonicalization and content-addressing.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

# ============================================================================
# §1.1 — Justification Schema Types
# ============================================================================


class Predicate(str, Enum):
    """Closed vocabulary for predicate claims."""
    PERMITS = "PERMITS"
    FORBIDS = "FORBIDS"
    REQUIRES = "REQUIRES"
    SATISFIES = "SATISFIES"
    CONFLICTS_WITH = "CONFLICTS_WITH"


class ConflictType(str, Enum):
    """Conflict declaration types."""
    MUTUAL_EXCLUSION = "MUTUAL_EXCLUSION"
    RESOURCE_CONTENTION = "RESOURCE_CONTENTION"
    TEMPORAL_OVERLAP = "TEMPORAL_OVERLAP"
    PRIORITY_DEADLOCK = "PRIORITY_DEADLOCK"


@dataclass
class Claim:
    """Typed predicate claim supporting an action."""
    predicate: Predicate
    args: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "predicate": self.predicate.value,
            "args": self.args
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Claim":
        return cls(
            predicate=Predicate(d["predicate"]),
            args=d["args"]
        )


@dataclass
class Conflict:
    """Conflict declaration between two rules."""
    type: ConflictType
    rule_a: str
    rule_b: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "rule_a": self.rule_a,
            "rule_b": self.rule_b
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Conflict":
        return cls(
            type=ConflictType(d["type"]),
            rule_a=d["rule_a"],
            rule_b=d["rule_b"]
        )


@dataclass
class JustificationV400:
    """
    Justification output from deliberator.
    Schema: §1.1 of design freeze.
    """
    action_id: str
    rule_refs: List[str]
    claims: List[Claim]
    conflict: Optional[Conflict] = None
    counterfactual: Optional[str] = None

    def __post_init__(self):
        # Validate action_id pattern
        if not re.match(r"^A[0-9]+$", self.action_id):
            raise ValueError(f"Invalid action_id pattern: {self.action_id}")
        # Validate rule_refs pattern
        for ref in self.rule_refs:
            if not re.match(r"^R[0-9]+$", ref):
                raise ValueError(f"Invalid rule_ref pattern: {ref}")
        # Validate claims non-empty
        if len(self.claims) < 1:
            raise ValueError("claims must have at least 1 item")
        if len(self.rule_refs) < 1:
            raise ValueError("rule_refs must have at least 1 item")
        # Validate counterfactual pattern if present
        if self.counterfactual and not re.match(r"^A[0-9]+$", self.counterfactual):
            raise ValueError(f"Invalid counterfactual pattern: {self.counterfactual}")
        # Validate claim args
        for claim in self.claims:
            if len(claim.args) < 1 or len(claim.args) > 3:
                raise ValueError(f"Claim args must have 1-3 items, got {len(claim.args)}")

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "action_id": self.action_id,
            "rule_refs": self.rule_refs,
            "claims": [c.to_dict() for c in self.claims]
        }
        if self.conflict:
            d["conflict"] = self.conflict.to_dict()
        if self.counterfactual:
            d["counterfactual"] = self.counterfactual
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JustificationV400":
        return cls(
            action_id=d["action_id"],
            rule_refs=d["rule_refs"],
            claims=[Claim.from_dict(c) for c in d["claims"]],
            conflict=Conflict.from_dict(d["conflict"]) if d.get("conflict") else None,
            counterfactual=d.get("counterfactual")
        )


# ============================================================================
# §1.2 — NormPatch Schema Types
# ============================================================================


class PatchOp(str, Enum):
    """Patch operation types."""
    ADD = "ADD"
    REMOVE = "REMOVE"
    REPLACE = "REPLACE"


class RuleType(str, Enum):
    """Normative rule types."""
    PERMISSION = "PERMISSION"
    PROHIBITION = "PROHIBITION"
    OBLIGATION = "OBLIGATION"


class ConditionOp(str, Enum):
    """Condition operators (closed vocabulary)."""
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


class ActionClass(str, Enum):
    """Effect action classes."""
    MOVE = "MOVE"
    COLLECT = "COLLECT"
    DEPOSIT = "DEPOSIT"
    WAIT = "WAIT"
    ANY = "ANY"


@dataclass
class Condition:
    """Rule condition with operator and arguments."""
    op: ConditionOp
    args: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        # Recursively convert nested conditions
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


@dataclass
class Effect:
    """Rule effect specifying action class and optional target."""
    action_class: ActionClass
    target: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"action_class": self.action_class.value}
        if self.target:
            d["target"] = self.target
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Effect":
        return cls(
            action_class=ActionClass(d["action_class"]),
            target=d.get("target")
        )


@dataclass
class Rule:
    """
    Normative rule in typed DSL.
    Includes priority field for OBLIGATION conflict resolution.
    """
    id: str
    type: RuleType
    condition: Condition
    effect: Effect
    expires_episode: Optional[int] = None
    priority: int = 0

    def __post_init__(self):
        if not re.match(r"^R[0-9]+$", self.id):
            raise ValueError(f"Invalid rule id pattern: {self.id}")
        if self.expires_episode is not None and self.expires_episode < 0:
            raise ValueError(f"expires_episode must be >= 0, got {self.expires_episode}")

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "type": self.type.value,
            "condition": self.condition.to_dict(),
            "effect": self.effect.to_dict(),
            "expires_episode": self.expires_episode,
            "priority": self.priority
        }
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Rule":
        return cls(
            id=d["id"],
            type=RuleType(d["type"]),
            condition=Condition.from_dict(d["condition"]),
            effect=Effect.from_dict(d["effect"]),
            expires_episode=d.get("expires_episode"),
            priority=d.get("priority", 0)
        )


@dataclass
class NormPatchV400:
    """
    Normative patch operation.
    Schema: §1.2 of design freeze.
    """
    op: PatchOp
    target_rule_id: str
    justification_ref: str
    new_rule: Optional[Rule] = None

    def __post_init__(self):
        # Validate target_rule_id pattern
        if not re.match(r"^R[0-9]+$", self.target_rule_id):
            raise ValueError(f"Invalid target_rule_id pattern: {self.target_rule_id}")
        # Validate justification_ref pattern (16 hex chars)
        if not re.match(r"^[a-f0-9]{16}$", self.justification_ref):
            raise ValueError(f"Invalid justification_ref pattern: {self.justification_ref}")
        # Validate new_rule required for ADD/REPLACE
        if self.op in (PatchOp.ADD, PatchOp.REPLACE) and self.new_rule is None:
            raise ValueError(f"new_rule required for {self.op.value} operation")

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "op": self.op.value,
            "target_rule_id": self.target_rule_id,
            "justification_ref": self.justification_ref
        }
        if self.new_rule:
            d["new_rule"] = self.new_rule.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "NormPatchV400":
        return cls(
            op=PatchOp(d["op"]),
            target_rule_id=d["target_rule_id"],
            justification_ref=d["justification_ref"],
            new_rule=Rule.from_dict(d["new_rule"]) if d.get("new_rule") else None
        )


# ============================================================================
# §1.3 — Canonicalization Rules
# ============================================================================


def canonicalize(obj: Dict[str, Any]) -> str:
    """
    Canonical JSON serialization per §1.3:
    - Keys in lexicographic order
    - No whitespace outside strings
    - Single-line output
    """
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def content_hash(obj: Dict[str, Any]) -> str:
    """
    SHA-256 hash truncated to 16 hex characters (64 bits).
    Per §1.3 of design freeze.
    """
    return hashlib.sha256(canonicalize(obj).encode()).hexdigest()[:16]


def hash_justification(j: JustificationV400) -> str:
    """Compute content hash of a justification."""
    return content_hash(j.to_dict())


def hash_patch(p: NormPatchV400) -> str:
    """Compute content hash of a patch."""
    return content_hash(p.to_dict())


def hash_rules(rules: List[Rule]) -> str:
    """Compute content hash of a rule list."""
    return content_hash({"rules": [r.to_dict() for r in rules]})


# ============================================================================
# Validation Helpers
# ============================================================================


class ValidationError(Exception):
    """Raised when schema validation fails."""
    pass


class ParseError(Exception):
    """Raised when JSON parsing fails."""
    pass


class ReferenceError(Exception):
    """Raised when rule reference is not found."""
    pass


def validate_justification_json(json_str: str) -> JustificationV400:
    """
    Parse and validate a JSON string as JustificationV400.
    Raises ParseError or ValidationError on failure.
    """
    try:
        d = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e}")

    try:
        return JustificationV400.from_dict(d)
    except (KeyError, ValueError, TypeError) as e:
        raise ValidationError(f"Schema validation failed: {e}")


def validate_patch_json(json_str: str) -> NormPatchV400:
    """
    Parse and validate a JSON string as NormPatchV400.
    Raises ParseError or ValidationError on failure.
    """
    try:
        d = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ParseError(f"Invalid JSON: {e}")

    try:
        return NormPatchV400.from_dict(d)
    except (KeyError, ValueError, TypeError) as e:
        raise ValidationError(f"Schema validation failed: {e}")


# ============================================================================
# Initial Rules (§3.2 of design freeze)
# ============================================================================


def create_initial_rules() -> List[Rule]:
    """
    Create the initial ruleset per §3.2 of design freeze.
    R1: OBLIGATION to prioritize Zone A (expires episode 1, priority 10)
    R2: OBLIGATION to satisfy Zone B (never expires, priority 5)
    R3: PERMISSION to collect at source
    R4: PERMISSION to move anywhere
    """
    return [
        Rule(
            id="R1",
            type=RuleType.OBLIGATION,
            condition=Condition(
                op=ConditionOp.AND,
                args=[
                    Condition(op=ConditionOp.GT, args=["zone_a_demand", 0]),
                    Condition(op=ConditionOp.EQ, args=["zone_a_satisfied", False])
                ]
            ),
            effect=Effect(action_class=ActionClass.DEPOSIT, target="ZONE_A"),
            expires_episode=1,
            priority=10
        ),
        Rule(
            id="R2",
            type=RuleType.OBLIGATION,
            condition=Condition(
                op=ConditionOp.AND,
                args=[
                    Condition(op=ConditionOp.GT, args=["zone_b_demand", 0]),
                    Condition(op=ConditionOp.EQ, args=["zone_b_satisfied", False])
                ]
            ),
            effect=Effect(action_class=ActionClass.DEPOSIT, target="ZONE_B"),
            expires_episode=None,
            priority=5
        ),
        Rule(
            id="R3",
            type=RuleType.PERMISSION,
            condition=Condition(op=ConditionOp.IN_STATE, args=["SOURCE"]),
            effect=Effect(action_class=ActionClass.COLLECT),
            expires_episode=None,
            priority=0
        ),
        Rule(
            id="R4",
            type=RuleType.PERMISSION,
            condition=Condition(op=ConditionOp.TRUE, args=[]),
            effect=Effect(action_class=ActionClass.MOVE),
            expires_episode=None,
            priority=0
        )
    ]


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Justification types
    "Predicate",
    "ConflictType",
    "Claim",
    "Conflict",
    "JustificationV400",
    # Patch types
    "PatchOp",
    "RuleType",
    "ConditionOp",
    "ActionClass",
    "Condition",
    "Effect",
    "Rule",
    "NormPatchV400",
    # Canonicalization
    "canonicalize",
    "content_hash",
    "hash_justification",
    "hash_patch",
    "hash_rules",
    # Validation
    "ValidationError",
    "ParseError",
    "ReferenceError",
    "validate_justification_json",
    "validate_patch_json",
    # Initial state
    "create_initial_rules",
]
