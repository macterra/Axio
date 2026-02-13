"""
RSA-0 X-0E — Append-Only Log I/O

Single source of truth for all JSONL log reading and writing.
All writes are append-only with fsync for crash safety.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from kernel.src.canonical import canonical_str


# ---------------------------------------------------------------------------
# Writing (host infrastructure — NOT a warranted action)
# ---------------------------------------------------------------------------

def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    """Append a single JSONL record with fsync for crash safety.

    Opens in binary-append mode, writes canonical JSON + newline,
    then flushes and fsyncs.
    """
    line = canonical_str(record) + "\n"
    raw = line.encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read all records from a JSONL file.  Returns [] if file missing."""
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {e}") from e
    return records


def read_jsonl_by_cycle(path: Path) -> Dict[int, List[Dict[str, Any]]]:
    """Read JSONL and group records by cycle_id."""
    records = read_jsonl(path)
    by_cycle: Dict[int, List[Dict[str, Any]]] = {}
    for rec in records:
        cid = rec.get("cycle_id")
        if cid is None:
            continue
        by_cycle.setdefault(cid, []).append(rec)
    return by_cycle


def extract_warrant_ids(path: Path) -> set:
    """Extract all warrant_id values from a JSONL file."""
    ids = set()
    for rec in read_jsonl(path):
        wid = rec.get("warrant_id")
        if wid:
            ids.add(wid)
    return ids
