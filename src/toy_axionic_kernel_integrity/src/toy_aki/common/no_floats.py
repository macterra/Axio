"""No-floats enforcement for hashed objects.

Per spec: Any object passed to hash_json() MUST contain only integers,
strings, arrays, and objects. If a float is encountered → fatal error.
"""

from typing import Any

from .errors import FloatInHashedObjectError


def assert_no_floats(obj: Any, path: str = "") -> None:
    """Recursively check that an object contains no floats.

    Args:
        obj: Object to check (dict, list, or primitive)
        path: Current path for error reporting (e.g., "proposal.trace.nodes[0]")

    Raises:
        FloatInHashedObjectError: If a float is found anywhere in the object
    """
    if isinstance(obj, float):
        raise FloatInHashedObjectError(path or "<root>", obj)

    elif isinstance(obj, dict):
        for key, value in obj.items():
            child_path = f"{path}.{key}" if path else key
            assert_no_floats(value, child_path)

    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            child_path = f"{path}[{i}]"
            assert_no_floats(item, child_path)

    elif isinstance(obj, bool):
        # bool is a subclass of int in Python, check before int
        pass

    elif isinstance(obj, int):
        # Integers are allowed
        pass

    elif isinstance(obj, str):
        # Strings are allowed
        pass

    elif obj is None:
        # null is allowed
        pass

    else:
        # Unknown type - could be a problem
        # For now, allow it but it might fail JSON serialization later
        pass


# Scale factor for converting real values to integers
SCALE = 10**8


def to_scaled_int(value: float) -> int:
    """Convert a real value to a scaled integer.

    Args:
        value: Real value to convert

    Returns:
        Scaled integer representation
    """
    return round(value * SCALE)


def from_scaled_int(scaled: int) -> float:
    """Convert a scaled integer back to a real value.

    Args:
        scaled: Scaled integer

    Returns:
        Original real value (approximately)
    """
    return scaled / SCALE
