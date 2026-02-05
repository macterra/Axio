"""
Structural Diff Algorithm (reused from IX-0)

Per preregistration §5.1:
- Path-level recursive diff over nested dicts and arrays
- Dot notation for object keys, bracket notation for array indices
- Deterministic traversal order (sorted keys, ascending indices)
"""

from dataclasses import dataclass, field
from typing import Any, List


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
        if artifact_a != artifact_b:
            diffs.append(DiffEntry(path=path, left=artifact_a, right=artifact_b))

    return DiffResult(entries=diffs, count=len(diffs))
