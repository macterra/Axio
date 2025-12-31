"""
AKI v0.3 KNS Attacks Package.

Contains the 6 simulability attack classes:
1. Policy Mimicry
2. Evaluator Substitution
3. Reflective Shortcutting
4. Justification Self-Model Collapse
5. Constraint Cosmeticization
6. Wrapper / Containment Delegation

Each attack aims to pass all checks while hollowing kernel structure.
"""

from toy_aki.attacks.kns.kns_attacks import (
    # Base class
    KNSAttack,
    KNSAttackType,
    KNSAttackResult,

    # Attack implementations
    PolicyMimicryAttack,
    EvaluatorSubstitutionAttack,
    ReflectiveShortcuttingAttack,
    JustificationCollapseAttack,
    ConstraintCosmeticizationAttack,
    WrapperDelegationAttack,

    # Factory functions
    create_kns_attack,
    get_all_kns_attack_types,
)

__all__ = [
    "KNSAttack",
    "KNSAttackType",
    "KNSAttackResult",
    "PolicyMimicryAttack",
    "EvaluatorSubstitutionAttack",
    "ReflectiveShortcuttingAttack",
    "JustificationCollapseAttack",
    "ConstraintCosmeticizationAttack",
    "WrapperDelegationAttack",
    "create_kns_attack",
    "get_all_kns_attack_types",
]
