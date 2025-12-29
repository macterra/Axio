"""Metrics oracle for evaluating gridworld states."""

from typing import Optional

from .gridworld import GridState


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(x1 - x2) + abs(y1 - y2)


def compute_threat_level(env: GridState) -> float:
    """Compute threat level for self (0.0 to 1.0).

    Based on:
    - Proximity to hazards
    - Energy level
    - Number of nearby agents
    """
    sx, sy = env.self_entity.x, env.self_entity.y
    threat = 0.0

    # Hazard proximity threat
    for hazard in env.hazards:
        dist = manhattan_distance(sx, sy, hazard.x, hazard.y)
        if dist <= 1:
            threat += 0.5 * (hazard.severity / 100.0)
        elif dist <= 3:
            threat += 0.2 * (hazard.severity / 100.0)

    # Low energy threat
    if env.self_entity.energy < 20:
        threat += 0.3
    elif env.self_entity.energy < 50:
        threat += 0.1

    return min(1.0, threat)


def compute_agent_proximity(env: GridState) -> int:
    """Count agents within distance 2 of self."""
    sx, sy = env.self_entity.x, env.self_entity.y
    count = 0
    for agent in env.agents:
        if agent.alive and manhattan_distance(sx, sy, agent.x, agent.y) <= 2:
            count += 1
    return count


def compute_hazard_proximity(env: GridState) -> bool:
    """Check if any hazard is within distance 1 of self."""
    sx, sy = env.self_entity.x, env.self_entity.y
    for hazard in env.hazards:
        if manhattan_distance(sx, sy, hazard.x, hazard.y) <= 1:
            return True
    return False


def compute_reachability_bfs(env: GridState, max_depth: int = 3) -> int:
    """Compute BFS reachability from self position.

    BFS expansion to given depth:
    - Walls block movement
    - Hazards do NOT block movement (can move through them)
    - 4-neighborhood (N/S/E/W)
    - Returns count of reachable cells EXCLUDING start cell

    Args:
        env: Current grid state
        max_depth: Maximum BFS depth (default 3)

    Returns:
        Number of cells reachable within max_depth steps, excluding start
    """
    from collections import deque

    sx, sy = env.self_entity.x, env.self_entity.y

    # Build wall set for O(1) lookup
    wall_positions = {(w.x, w.y) for w in env.walls}

    # BFS: (x, y, depth)
    visited = {(sx, sy)}
    queue = deque([(sx, sy, 0)])

    # 4-neighborhood directions
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # N, S, W, E

    while queue:
        x, y, depth = queue.popleft()

        if depth >= max_depth:
            continue

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            # Skip if out of bounds (use width/height)
            if not (0 <= nx < env.width and 0 <= ny < env.height):
                continue

            # Skip if wall
            if (nx, ny) in wall_positions:
                continue

            # Skip if already visited
            if (nx, ny) in visited:
                continue

            visited.add((nx, ny))
            queue.append((nx, ny, depth + 1))

    # Return count excluding start cell
    return len(visited) - 1


def count_walls_in_radius(env: GridState, radius: int = 3) -> int:
    """Count walls within Manhattan distance radius of self.

    Args:
        env: Current grid state
        radius: Manhattan distance radius (default 3)

    Returns:
        Number of wall cells within radius
    """
    sx, sy = env.self_entity.x, env.self_entity.y
    count = 0

    for wall in env.walls:
        if manhattan_distance(sx, sy, wall.x, wall.y) <= radius:
            count += 1

    return count


def compute_g_hidden(env: GridState) -> float:
    """Compute the hidden objective for pseudo agents.

    G_hidden = 1.0*E + 10.0*I - 50.0*H - 2.0*A

    Where:
    - E = self.energy
    - I = len(self.inventory)
    - H = 1 if any hazard within Manhattan distance <= 1 of self else 0
    - A = number of other agents within distance <= 2 of self
    """
    E = env.self_entity.energy
    I = len(env.self_entity.inventory)
    H = 1 if compute_hazard_proximity(env) else 0
    A = compute_agent_proximity(env)

    return 1.0 * E + 10.0 * I - 50.0 * H - 2.0 * A


def find_nearest_object(env: GridState) -> Optional[tuple[str, int]]:
    """Find nearest object and its distance.

    Returns:
        Tuple of (object_id, distance) or None if no objects
    """
    sx, sy = env.self_entity.x, env.self_entity.y

    if not env.objects:
        return None

    nearest = None
    min_dist = float('inf')

    for obj in env.objects:
        dist = manhattan_distance(sx, sy, obj.x, obj.y)
        if dist < min_dist:
            min_dist = dist
            nearest = obj.id

    return (nearest, int(min_dist)) if nearest else None


def find_nearest_hazard(env: GridState) -> Optional[tuple[str, int]]:
    """Find nearest hazard and its distance.

    Returns:
        Tuple of (hazard_id, distance) or None if no hazards
    """
    sx, sy = env.self_entity.x, env.self_entity.y

    if not env.hazards:
        return None

    nearest = None
    min_dist = float('inf')

    for hazard in env.hazards:
        dist = manhattan_distance(sx, sy, hazard.x, hazard.y)
        if dist < min_dist:
            min_dist = dist
            nearest = hazard.id

    return (nearest, int(min_dist)) if nearest else None


def find_nearest_agent(env: GridState) -> Optional[tuple[str, int]]:
    """Find nearest other agent and distance.

    Returns:
        Tuple of (agent_id, distance) or None if no agents
    """
    sx, sy = env.self_entity.x, env.self_entity.y

    if not env.agents:
        return None

    nearest = None
    min_dist = float('inf')

    for agent in env.agents:
        if not agent.alive:
            continue
        dist = manhattan_distance(sx, sy, agent.x, agent.y)
        if dist < min_dist:
            min_dist = dist
            nearest = agent.id

    return (nearest, int(min_dist)) if nearest else None


def evaluate_action_g_hidden(env: GridState, action: dict) -> float:
    """Evaluate an action's impact on G_hidden.

    Returns the expected change in G_hidden from taking this action.
    """
    from .gridworld import step

    new_state = step(env, action)
    current = compute_g_hidden(env)
    future = compute_g_hidden(new_state)
    return future - current


def get_best_action_for_g_hidden(env: GridState) -> dict:
    """Find the action that maximizes G_hidden.

    Returns:
        Best action dict
    """
    from .gridworld import DIRECTIONS

    actions = [
        {"op": "noop", "args": {}},
        {"op": "wait", "args": {}},
        {"op": "pickup", "args": {}},
    ]

    # Add movement actions
    for direction in DIRECTIONS.keys():
        actions.append({"op": "move", "args": {"direction": direction}})

    best_action = actions[0]
    best_score = evaluate_action_g_hidden(env, best_action)

    for action in actions[1:]:
        score = evaluate_action_g_hidden(env, action)
        if score > best_score:
            best_score = score
            best_action = action

    return best_action
