"""State normalization for fork snapshot commitments."""

from typing import Any

from .gridworld import GridState


# Focus variable namespace
ALLOWED_FOCUS_VARS = {
    "tick",
    "self.pos",
    "self.energy",
    "self.inventory",
    "agents.pos",
    "agents.energy",
    "objects.at",
    "hazards.at",
    "walls.nearby",
    "tools.available",
    "rng_seed",
}

# Derived variables (computed on demand)
DERIVED_VAR_PREFIXES = {
    "dist.self_to_agent:",
    "dist.self_to_object:",
    "threat.nearest_hazard",
    "reachability.self.k",
    "reachability.agent:",
}


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)


def normalize_state(env: GridState, focus_vars: list[str]) -> dict:
    """Normalize environment state for hashing.

    Always includes:
    - tick
    - grid: {w, h}
    - rng_seed
    - self: {id, x, y}
    - env_flags (if present)

    Then includes requested focus vars with deterministic sorting.

    Args:
        env: Current environment state
        focus_vars: List of focus variable names to include

    Returns:
        Normalized state dict suitable for canonical JSON hashing
    """
    # Always-included base context
    result: dict[str, Any] = {
        "tick": env.tick,
        "grid": {
            "w": env.width,
            "h": env.height
        },
        "rng_seed": env.rng_seed,
        "self": {
            "id": env.self_entity.id,
            "x": env.self_entity.x,
            "y": env.self_entity.y
        }
    }

    # Include env_flags if non-default
    if env.env_flags.allow_omit_fork_snapshots or env.env_flags.bypass_available:
        result["env_flags"] = env.env_flags.to_dict()

    # Derived values go here
    derived: dict[str, Any] = {}

    sx, sy = env.self_entity.x, env.self_entity.y

    for var in focus_vars:
        if var == "tick":
            # Already included
            pass

        elif var == "self.pos":
            result["self"]["x"] = sx
            result["self"]["y"] = sy

        elif var == "self.energy":
            result["self"]["energy"] = env.self_entity.energy

        elif var == "self.inventory":
            result["self"]["inventory"] = sorted(env.self_entity.inventory)

        elif var == "agents.pos":
            result["agents"] = [
                {"id": a.id, "x": a.x, "y": a.y}
                for a in sorted(env.agents, key=lambda a: a.id)
            ]

        elif var == "agents.energy":
            if "agents" not in result:
                result["agents"] = []
            for a in sorted(env.agents, key=lambda a: a.id):
                existing = next((x for x in result.get("agents", []) if x.get("id") == a.id), None)
                if existing:
                    existing["energy"] = a.energy
                else:
                    result["agents"].append({"id": a.id, "energy": a.energy})

        elif var == "objects.at":
            # Objects within radius 5, sorted by (kind, id)
            objs = [
                o for o in env.objects
                if manhattan_distance(sx, sy, o.x, o.y) <= 5
            ]
            result["objects"] = [
                {"id": o.id, "kind": o.kind, "x": o.x, "y": o.y}
                for o in sorted(objs, key=lambda o: (o.kind, o.id))
            ]

        elif var == "hazards.at":
            # Hazards within radius 5, sorted by (kind, id)
            hazards = [
                h for h in env.hazards
                if manhattan_distance(sx, sy, h.x, h.y) <= 5
            ]
            result["hazards"] = [
                {"id": h.id, "kind": h.kind, "x": h.x, "y": h.y, "severity": h.severity}
                for h in sorted(hazards, key=lambda h: (h.kind, h.id))
            ]

        elif var == "walls.nearby":
            # Walls within radius 3, sorted by (x, y)
            walls = [
                w for w in env.walls
                if manhattan_distance(sx, sy, w.x, w.y) <= 3
            ]
            result["walls"] = [
                {"x": w.x, "y": w.y}
                for w in sorted(walls, key=lambda w: (w.x, w.y))
            ]

        elif var == "tools.available":
            result["tools"] = [
                {"id": t.id, "kind": t.kind, "charges": t.charges}
                for t in sorted(env.tools, key=lambda t: t.id)
                if t.charges > 0
            ]

        elif var == "rng_seed":
            # Already included
            pass

        elif var.startswith("dist.self_to_agent:"):
            agent_id = var.split(":")[1]
            for agent in env.agents:
                if agent.id == agent_id:
                    derived[var] = manhattan_distance(sx, sy, agent.x, agent.y)
                    break

        elif var.startswith("dist.self_to_object:"):
            obj_id = var.split(":")[1]
            for obj in env.objects:
                if obj.id == obj_id:
                    derived[var] = manhattan_distance(sx, sy, obj.x, obj.y)
                    break

        elif var == "threat.nearest_hazard":
            if env.hazards:
                min_dist = min(
                    manhattan_distance(sx, sy, h.x, h.y)
                    for h in env.hazards
                )
                derived[var] = min_dist
            else:
                derived[var] = -1  # No hazards

        elif var.startswith("reachability.self."):
            # Compute k-step reachability from self
            k = int(var.split(".")[-1])
            derived[var] = _compute_reachability(env, sx, sy, k)

        elif var.startswith("reachability.agent:"):
            # e.g., reachability.agent:A1.k
            parts = var.split(":")
            rest = parts[1]
            agent_id, k_str = rest.rsplit(".", 1)
            k = int(k_str)
            for agent in env.agents:
                if agent.id == agent_id:
                    derived[var] = _compute_reachability(env, agent.x, agent.y, k)
                    break

    if derived:
        result["derived"] = derived

    return result


def _compute_reachability(env: GridState, start_x: int, start_y: int, k: int) -> int:
    """Compute number of reachable cells within k steps."""
    visited = {(start_x, start_y)}
    frontier = [(start_x, start_y)]

    for _ in range(k):
        next_frontier = []
        for x, y in frontier:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited and env.is_valid_position(nx, ny):
                    visited.add((nx, ny))
                    next_frontier.append((nx, ny))
        frontier = next_frontier

    return len(visited)


def get_default_focus_vars() -> list[str]:
    """Get default focus variables for proposals."""
    return [
        "tick",
        "self.pos",
        "self.energy",
        "hazards.at",
        "objects.at",
        "agents.pos",
        "threat.nearest_hazard"
    ]
