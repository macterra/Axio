"""
CalibMazeV010: 6-node directed graph environment for ASI-0 v1.0

Topology:
    N0 → {N1, N2}
    N1 → {N3, N4}
    N2 → {N3, N4}
    N3 → {N4, N5}
    N4 → {N3, N5}
    N5 → {N3, N4, N5}  # Includes self-loop

Plus STAY action at every node.

Episode: 5 steps (t=1..5), goal = node == N5 at end of step 5.
"""

from dataclasses import dataclass
from typing import Set, Dict, Tuple, Optional
from enum import Enum


# Type aliases
NodeID = str
ActionID = str


class Node(Enum):
    N0 = "N0"
    N1 = "N1"
    N2 = "N2"
    N3 = "N3"
    N4 = "N4"
    N5 = "N5"


# Graph topology: node -> set of reachable nodes via GO_* actions
TOPOLOGY: Dict[str, Set[str]] = {
    "N0": {"N1", "N2"},
    "N1": {"N3", "N4"},
    "N2": {"N3", "N4"},
    "N3": {"N4", "N5"},
    "N4": {"N3", "N5"},
    "N5": {"N3", "N4", "N5"},  # Includes self-loop
}


# Total FORBID mapping: (step, node) -> forbidden ActionID
# Missing keys are a hard error (no defaults)
FORBID_MAP: Dict[Tuple[int, str], str] = {
    (1, "N0"): "GO_N2",
    (2, "N0"): "STAY", (2, "N1"): "GO_N4", (2, "N2"): "GO_N4",
    (3, "N0"): "STAY", (3, "N1"): "STAY", (3, "N2"): "STAY", (3, "N3"): "STAY", (3, "N4"): "STAY",
    (4, "N0"): "STAY", (4, "N1"): "STAY", (4, "N2"): "STAY", (4, "N3"): "GO_N4", (4, "N4"): "GO_N3", (4, "N5"): "GO_N3",
    (5, "N0"): "STAY", (5, "N1"): "STAY", (5, "N2"): "STAY", (5, "N3"): "STAY", (5, "N4"): "STAY", (5, "N5"): "GO_N5",
}


def get_forbidden_action(step: int, node: NodeID) -> ActionID:
    """Total mapping: returns forbidden action for any reachable (step, node).

    Raises RuntimeError if (step, node) is not in the preregistered mapping.
    This enforces totality mechanically.
    """
    if (step, node) not in FORBID_MAP:
        raise RuntimeError(f"INVALID_RUN / MISSING_FORBID_MAPPING: {(step, node)}")
    return FORBID_MAP[(step, node)]


def get_feasible_actions(node: NodeID) -> Set[ActionID]:
    """Return all feasible actions from a given node.

    Actions are GO_<target> for each reachable node, plus STAY.
    """
    if node not in TOPOLOGY:
        raise ValueError(f"Unknown node: {node}")

    actions: Set[ActionID] = {"STAY"}
    for target in TOPOLOGY[node]:
        actions.add(f"GO_{target}")

    return actions


def execute_action(current_node: NodeID, action: ActionID) -> NodeID:
    """Execute an action and return the resulting node.

    Raises ValueError if action is not feasible from current node.
    """
    feasible = get_feasible_actions(current_node)
    if action not in feasible:
        raise ValueError(f"Action {action} not feasible from {current_node}. Feasible: {feasible}")

    if action == "STAY":
        return current_node

    # Parse GO_<target>
    if action.startswith("GO_"):
        target = action[3:]  # Remove "GO_" prefix
        if target in TOPOLOGY[current_node]:
            return target
        raise ValueError(f"Invalid GO action: {action} from {current_node}")

    raise ValueError(f"Unknown action format: {action}")


@dataclass
class EnvState:
    """Environment state for CalibMazeV010."""
    node: NodeID
    step: int  # 1-indexed, 1..5

    def is_terminal(self) -> bool:
        """Episode terminates after step 5."""
        return self.step > 5

    def goal_reached(self) -> bool:
        """Goal: node == N5 at end of step 5."""
        return self.step > 5 and self.node == "N5"


class CalibMazeV010:
    """CalibMazeV010 environment for ASI-0 v1.0."""

    ENV_ID = "CalibMazeV010"
    MAX_STEPS = 5
    GOAL_NODE = "N5"

    def __init__(self):
        self.state: Optional[EnvState] = None

    def reset(self) -> EnvState:
        """Reset environment to initial state."""
        self.state = EnvState(node="N0", step=1)
        return self.state

    def get_feasible_actions(self) -> Set[ActionID]:
        """Get feasible actions from current state."""
        if self.state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return get_feasible_actions(self.state.node)

    def get_forbidden_action(self) -> ActionID:
        """Get the forbidden action for current (step, node)."""
        if self.state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return get_forbidden_action(self.state.step, self.state.node)

    def step(self, action: ActionID) -> EnvState:
        """Execute action and advance to next step.

        Returns new state after action.
        """
        if self.state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        if self.state.is_terminal():
            raise RuntimeError("Episode already terminated.")

        # Execute action
        new_node = execute_action(self.state.node, action)

        # Advance step
        self.state = EnvState(node=new_node, step=self.state.step + 1)

        return self.state

    def is_terminal(self) -> bool:
        """Check if episode is terminal."""
        if self.state is None:
            return False
        return self.state.is_terminal()

    def goal_reached(self) -> bool:
        """Check if goal is reached."""
        if self.state is None:
            return False
        return self.state.goal_reached()


# Verification utilities

def verify_topology() -> bool:
    """Verify topology is well-formed."""
    for node, targets in TOPOLOGY.items():
        for target in targets:
            if target not in TOPOLOGY:
                print(f"ERROR: {node} has edge to unknown node {target}")
                return False
    return True


def verify_forbid_map_coverage() -> bool:
    """Verify FORBID_MAP covers all reachable (step, node) pairs.

    Uses BFS to enumerate all reachable states.
    """
    reachable: Set[Tuple[int, str]] = set()
    frontier: Set[Tuple[int, str]] = {(1, "N0")}

    while frontier:
        step, node = frontier.pop()
        if (step, node) in reachable:
            continue
        reachable.add((step, node))

        if step >= 5:
            continue

        # Explore all feasible actions
        for action in get_feasible_actions(node):
            next_node = execute_action(node, action)
            frontier.add((step + 1, next_node))

    # Check coverage
    missing = reachable - set(FORBID_MAP.keys())
    extra = set(FORBID_MAP.keys()) - reachable

    if missing:
        print(f"ERROR: FORBID_MAP missing entries: {missing}")
        return False
    if extra:
        print(f"WARNING: FORBID_MAP has unreachable entries: {extra}")

    print(f"FORBID_MAP covers all {len(reachable)} reachable (step, node) pairs")
    return True


def verify_non_triviality() -> bool:
    """Verify each forbidden action is feasible at its (step, node)."""
    for (step, node), forbidden in FORBID_MAP.items():
        feasible = get_feasible_actions(node)
        if forbidden not in feasible:
            print(f"ERROR: Forbidden action {forbidden} not feasible at ({step}, {node})")
            print(f"       Feasible actions: {feasible}")
            return False

    print("All forbidden actions are feasible at their (step, node) pairs")
    return True


if __name__ == "__main__":
    print("CalibMazeV010 Verification")
    print("=" * 40)

    print("\n1. Topology verification:")
    verify_topology()

    print("\n2. FORBID_MAP coverage verification:")
    verify_forbid_map_coverage()

    print("\n3. Non-triviality verification:")
    verify_non_triviality()

    print("\n4. Sample episode:")
    env = CalibMazeV010()
    state = env.reset()
    print(f"  Initial: {state}")

    actions = ["GO_N1", "GO_N3", "GO_N5", "STAY", "STAY"]
    for action in actions:
        feasible = env.get_feasible_actions()
        forbidden = env.get_forbidden_action()
        print(f"  Step {state.step}: node={state.node}, feasible={feasible}, forbidden={forbidden}")
        state = env.step(action)
        print(f"           action={action} -> {state}")

    print(f"\n  Terminal: {env.is_terminal()}, Goal reached: {env.goal_reached()}")
