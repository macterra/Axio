"""
Structural Diff Algorithm

Per preregistration §5.1:
- Path-level recursive diff over nested dicts and arrays
- Dot notation for object keys, bracket notation for array indices
- Deterministic traversal order (sorted keys, ascending indices)
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


class _Missing:
    """Sentinel for missing values in diff comparison."""
    def __repr__(self) -> str:
        return "<MISSING>"

MISSING = _Missing()


@dataclass
class DiffEntry:
    """Single diff entry with path and values."""
    path: str
    left: Any
    right: Any


@dataclass
class DiffResult:
    """Result of structural diff operation."""
    entries: List[DiffEntry] = field(default_factory=list)
    count: int = 0

    def __post_init__(self):
        self.count = len(self.entries)


# User-field roots per preregistration §5.2
USER_FIELD_ROOTS = frozenset(['holder', 'scope', 'aav', 'expiry_epoch'])

# Derived-field roots per preregistration §5.2
DERIVED_FIELD_ROOTS = frozenset(['authority_id', 'lineage', 'created_epoch', 'status'])


def structural_diff(artifact_a: Any, artifact_b: Any, path: str = "") -> DiffResult:
    """
    Compute path-level differences between two artifacts.
    Recursively traverses nested dicts and arrays.
    Returns list of (path, value_a, value_b) tuples for differing values.

    Per preregistration §5.1, traversal order is deterministic:
    - Dict keys are sorted lexicographically
    - Array indices are ascending
    """
    diffs: List[DiffEntry] = []

    if isinstance(artifact_a, dict) and isinstance(artifact_b, dict):
        all_keys = set(artifact_a.keys()) | set(artifact_b.keys())
        for key in sorted(all_keys):
            new_path = f"{path}.{key}" if path else key
            val_a = artifact_a.get(key, MISSING)
            val_b = artifact_b.get(key, MISSING)
            if isinstance(val_a, _Missing) or isinstance(val_b, _Missing):
                diffs.append(DiffEntry(path=new_path, left=val_a, right=val_b))
            elif val_a != val_b:
                sub_result = structural_diff(val_a, val_b, new_path)
                diffs.extend(sub_result.entries)

    elif isinstance(artifact_a, list) and isinstance(artifact_b, list):
        max_len = max(len(artifact_a), len(artifact_b))
        for i in range(max_len):
            new_path = f"{path}[{i}]"
            val_a = artifact_a[i] if i < len(artifact_a) else MISSING
            val_b = artifact_b[i] if i < len(artifact_b) else MISSING
            if isinstance(val_a, _Missing) or isinstance(val_b, _Missing):
                diffs.append(DiffEntry(path=new_path, left=val_a, right=val_b))
            elif val_a != val_b:
                sub_result = structural_diff(val_a, val_b, new_path)
                diffs.extend(sub_result.entries)

    else:
        # Leaf values differ
        if artifact_a != artifact_b:
            diffs.append(DiffEntry(path=path, left=artifact_a, right=artifact_b))

    return DiffResult(entries=diffs, count=len(diffs))


def get_path_root(path: str) -> str:
    """Extract root field name from path (e.g., 'scope[0].operation' -> 'scope')."""
    if not path:
        return ""
    # Handle both dot notation and bracket notation at start
    if path.startswith('['):
        return ""
    dot_pos = path.find('.')
    bracket_pos = path.find('[')
    if dot_pos == -1 and bracket_pos == -1:
        return path
    if dot_pos == -1:
        return path[:bracket_pos]
    if bracket_pos == -1:
        return path[:dot_pos]
    return path[:min(dot_pos, bracket_pos)]


def is_user_field_path(path: str) -> bool:
    """Check if path is rooted at a user field."""
    return get_path_root(path) in USER_FIELD_ROOTS


def is_derived_field_path(path: str) -> bool:
    """Check if path is rooted at a derived field."""
    return get_path_root(path) in DERIVED_FIELD_ROOTS


def classify_diff(diff_result: DiffResult) -> str:
    """
    Classify diff result per preregistration §5.2.

    Returns one of:
    - IDENTICAL: 0 diffs
    - MINIMAL_DELTA: 1 user-field path
    - DERIVED_DELTA: 1 derived-field path only
    - EXCESSIVE_DELTA: >1 user-field paths
    - INJECTION_DETECTED: extra top-level field present
    """
    if diff_result.count == 0:
        return "IDENTICAL"

    user_field_diffs = [e for e in diff_result.entries if is_user_field_path(e.path)]
    derived_field_diffs = [e for e in diff_result.entries if is_derived_field_path(e.path)]

    # Check for injection (extra top-level field not in either category)
    for entry in diff_result.entries:
        root = get_path_root(entry.path)
        if root and root not in USER_FIELD_ROOTS and root not in DERIVED_FIELD_ROOTS:
            # Check if this is a new field (right side has value, left is MISSING, or vice versa)
            if isinstance(entry.left, _Missing) or isinstance(entry.right, _Missing):
                return "INJECTION_DETECTED"

    if len(user_field_diffs) == 0 and len(derived_field_diffs) == 1:
        return "DERIVED_DELTA"

    if len(user_field_diffs) == 1:
        return "MINIMAL_DELTA"

    if len(user_field_diffs) > 1:
        return "EXCESSIVE_DELTA"

    # Edge case: only derived field diffs
    if len(derived_field_diffs) > 0:
        return "DERIVED_DELTA"

    return "IDENTICAL"
