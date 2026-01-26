"""
Compilation Discipline for ASI-0 v1.0

Implements:
- Constraint: Compiled constraint with binding
- compile_constraints(): Compile forbidden actions into constraints
- apply_mask(): Prune forbidden actions if bound, permit all if unbound
"""

from dataclasses import dataclass
from typing import List, Set

from normative_state import NormativeStateASI0, NULL_BINDING

# Type aliases
ActionID = str


@dataclass
class Constraint:
    """A compiled constraint with provenance binding.

    type: The constraint type (currently only "FORBID_ACTION")
    action_id: The action this constraint applies to
    binding: The binding root (non-null in Condition A, NULL_BINDING in Condition B)
    """
    type: str              # "FORBID_ACTION"
    action_id: ActionID    # e.g., "GO_N2"
    binding: bytes         # Non-null in A, NULL_BINDING in B

    def is_bound(self) -> bool:
        """Check if this constraint is bound (Condition A) or unbound (Condition B)."""
        return self.binding != NULL_BINDING


def compile_constraints(normative_state: NormativeStateASI0) -> List[Constraint]:
    """Compile forbidden actions into constraint objects.

    Each forbidden action in the normative state becomes a FORBID_ACTION
    constraint with the current binding_root.
    """
    constraints = []
    for action_id in normative_state.payload.forbidden_actions:
        constraints.append(Constraint(
            type="FORBID_ACTION",
            action_id=action_id,
            binding=normative_state.binding_root
        ))
    return constraints


def apply_mask(
    feasible_actions: Set[ActionID],
    constraints: List[Constraint]
) -> Set[ActionID]:
    """Prune forbidden actions if bound; permit all if unbound.

    Raises RuntimeError if constraints have mixed bindings (some bound, some unbound).

    Args:
        feasible_actions: Set of actions feasible in current state
        constraints: List of compiled constraints

    Returns:
        Set of actions after applying mask (may be pruned or unchanged)
    """
    if not constraints:
        return feasible_actions

    # Strict invariant: all constraints must share the same binding
    bindings = {c.binding for c in constraints}

    if bindings == {NULL_BINDING}:
        return feasible_actions  # Condition B: no pruning

    if len(bindings) != 1:
        raise RuntimeError("INVALID_RUN / MIXED_BINDING_SET")

    # All constraints bound to the same root
    forbidden = {c.action_id for c in constraints
                 if c.type == "FORBID_ACTION"}

    return feasible_actions - forbidden


def get_pruned_actions(
    feasible_actions: Set[ActionID],
    masked_actions: Set[ActionID]
) -> Set[ActionID]:
    """Get the set of actions that were pruned by the mask."""
    return feasible_actions - masked_actions


if __name__ == "__main__":
    print("Compilation Discipline Verification")
    print("=" * 40)

    from normative_state import (
        NormativePayload, create_bound_state, create_unbound_state
    )

    # Create sample payload with forbidden actions
    payload = NormativePayload(
        forbidden_actions=frozenset({"GO_N2", "GO_N4"}),
        target_node="N5"
    )

    # Test Condition A (bound)
    print("\n1. Condition A (bound):")
    bound_state = create_bound_state(payload, run_id="test-001")
    constraints_a = compile_constraints(bound_state)
    print(f"   Constraints: {[(c.type, c.action_id, c.is_bound()) for c in constraints_a]}")

    feasible = {"GO_N1", "GO_N2", "GO_N4", "STAY"}
    masked_a = apply_mask(feasible, constraints_a)
    print(f"   Feasible: {feasible}")
    print(f"   Masked:   {masked_a}")
    print(f"   Pruned:   {get_pruned_actions(feasible, masked_a)}")

    # Test Condition B (unbound)
    print("\n2. Condition B (unbound):")
    unbound_state = create_unbound_state(payload, run_id="test-001")
    constraints_b = compile_constraints(unbound_state)
    print(f"   Constraints: {[(c.type, c.action_id, c.is_bound()) for c in constraints_b]}")

    masked_b = apply_mask(feasible, constraints_b)
    print(f"   Feasible: {feasible}")
    print(f"   Masked:   {masked_b}")
    print(f"   Pruned:   {get_pruned_actions(feasible, masked_b)}")

    # Verify discriminability
    print("\n3. Discriminability check:")
    print(f"   A pruned actions: {get_pruned_actions(feasible, masked_a)}")
    print(f"   B pruned actions: {get_pruned_actions(feasible, masked_b)}")
    print(f"   Discriminable: {masked_a != masked_b}")

    # Test mixed binding error
    print("\n4. Mixed binding error test:")
    try:
        mixed_constraints = [
            Constraint(type="FORBID_ACTION", action_id="GO_N2", binding=bound_state.binding_root),
            Constraint(type="FORBID_ACTION", action_id="GO_N4", binding=NULL_BINDING),
        ]
        apply_mask(feasible, mixed_constraints)
        print("   ERROR: Should have raised RuntimeError")
    except RuntimeError as e:
        print(f"   Correctly raised: {e}")

    # Test empty constraints
    print("\n5. Empty constraints test:")
    masked_empty = apply_mask(feasible, [])
    print(f"   Feasible: {feasible}")
    print(f"   Masked:   {masked_empty}")
    print(f"   Equal: {masked_empty == feasible}")
