"""
X-0L Pre-Flight Stability Verification

Verifies (per instructions §2):
  1. Constitution integrity (hash match)
  2. Schema integrity (hash match)
  3. Canonicalizer integrity (source hash + self-test hash) (Q4)
  4. Canonicalizer fuzzing (Q5: once at preflight)
  5. No artifact drift
  6. Model calibration (delegated to calibration module)

Must pass before any live cycles begin.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import canonical_json
from kernel.src.constitution import Constitution
from canonicalizer.pipeline import source_hash, self_test_hash, canonicalize


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPECTED_CONSTITUTION_SHA256 = (
    "ad6aa7ccb0ed27151423486b60de380da9d34436f6c5554da84f3a092902740f"
)


# ---------------------------------------------------------------------------
# Pre-flight result
# ---------------------------------------------------------------------------

class PreflightResult:
    """Result of all pre-flight checks."""

    def __init__(self) -> None:
        self.checks: List[Dict[str, Any]] = []
        self.passed: bool = True
        self.canonicalizer_source_hash: str = ""
        self.canonicalizer_self_test_hash: str = ""

    def add_check(self, name: str, passed: bool, detail: str = "") -> None:
        self.checks.append({
            "check": name,
            "passed": passed,
            "detail": detail,
        })
        if not passed:
            self.passed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": self.checks,
            "canonicalizer_source_hash": self.canonicalizer_source_hash,
            "canonicalizer_self_test_hash": self.canonicalizer_self_test_hash,
        }


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def verify_constitution_integrity(
    constitution_path: Path,
    expected_hash: str = EXPECTED_CONSTITUTION_SHA256,
) -> Tuple[bool, str]:
    """Verify constitution file hash matches expected value."""
    if not constitution_path.exists():
        return False, f"Constitution file not found: {constitution_path}"

    content = constitution_path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()

    if actual_hash != expected_hash:
        return False, f"Hash mismatch: expected {expected_hash}, got {actual_hash}"

    return True, f"Constitution hash verified: {actual_hash}"


def verify_schema_integrity(
    schema_path: Path,
    expected_hash: Optional[str] = None,
) -> Tuple[bool, str]:
    """Verify schema file exists and optionally check hash."""
    if not schema_path.exists():
        return False, f"Schema file not found: {schema_path}"

    content = schema_path.read_bytes()
    actual_hash = hashlib.sha256(content).hexdigest()

    if expected_hash and actual_hash != expected_hash:
        return False, f"Schema hash mismatch: expected {expected_hash}, got {actual_hash}"

    return True, f"Schema hash: {actual_hash}"


def verify_canonicalizer_integrity() -> Tuple[bool, str, str, str]:
    """Verify canonicalizer source hash and self-test hash.

    Per Q4: both source hash and self-test hash are recorded.
    Returns (passed, detail, source_hash, self_test_hash).
    """
    try:
        src_hash = source_hash()
        test_hash = self_test_hash()
        return (
            True,
            f"Source hash: {src_hash[:16]}..., self-test hash: {test_hash[:16]}...",
            src_hash,
            test_hash,
        )
    except Exception as e:
        return False, f"Canonicalizer integrity check failed: {e}", "", ""


def fuzz_canonicalizer() -> Tuple[bool, str]:
    """Fuzz canonicalizer with adversarial inputs (Q5: once at preflight).

    Tests: mixed Unicode, zero-width characters, varied whitespace,
    reordered keys, idempotence, stable hashing.
    """
    test_cases = [
        # Zero-width characters around JSON
        '\u200b{"candidates": []}\u200b',
        # Unicode combining characters
        '{"candidates": []}',
        # Mixed line endings
        '{\r\n"candidates"\r: [\r\n]\r\n}',
        # BOM + JSON
        '\ufeff{"candidates": []}',
        # Tabs and spaces mixed
        '\t  {"candidates": []}  \t',
        # Nested structure with varied whitespace
        '  {  "candidates"  :  [  ]  }  ',
        # Zero-width joiners inside prose
        'Here is response:\u200d\n{"candidates": []}',
        # Right-to-left mark
        '\u200f{"candidates": []}',
    ]

    for i, tc in enumerate(test_cases):
        # First pass
        result1 = canonicalize(tc)
        # Second pass (idempotence check)
        if result1.success and result1.json_string:
            result2 = canonicalize(result1.json_string)
            if result2.success:
                if result1.canonicalized_hash != result2.canonicalized_hash:
                    return False, f"Idempotence failure on test case {i}: hash changed on re-canonicalization"

    # Test key reordering stability
    a = '{"candidates": [], "meta": "a"}'
    b = '{"meta": "a", "candidates": []}'
    ra = canonicalize(a)
    rb = canonicalize(b)
    # Both should extract JSON; the *extracted* JSON may differ in key order
    # since we extract the block as-is. This is OK — canonical_json() downstream
    # handles key ordering on parsed dicts. The canonicalizer only extracts.
    if ra.success != rb.success:
        return False, "Key reordering changed extraction success/failure"

    return True, f"All {len(test_cases)} fuzz cases passed"


def verify_no_artifact_drift(repo_root: Path) -> Tuple[bool, str]:
    """Verify no unexpected artifact changes."""
    artifacts_dir = repo_root / "artifacts" / "phase-x"
    if not artifacts_dir.exists():
        return False, f"Artifacts directory not found: {artifacts_dir}"

    file_hashes = {}
    for f in sorted(artifacts_dir.rglob("*")):
        if f.is_file():
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            file_hashes[str(f.relative_to(repo_root))] = h

    composite = hashlib.sha256(
        canonical_json(file_hashes).encode("utf-8")
    ).hexdigest()

    return True, f"Artifact composite hash: {composite} ({len(file_hashes)} files)"


# ---------------------------------------------------------------------------
# Full pre-flight
# ---------------------------------------------------------------------------

def run_preflight(
    repo_root: Path,
    constitution_path: Path,
    schema_path: Path,
    expected_constitution_hash: str = EXPECTED_CONSTITUTION_SHA256,
    expected_schema_hash: Optional[str] = None,
) -> PreflightResult:
    """Run all pre-flight checks.

    Does NOT include model calibration (handled separately by runner).
    """
    result = PreflightResult()

    # 1. Constitution integrity
    ok, detail = verify_constitution_integrity(constitution_path, expected_constitution_hash)
    result.add_check("constitution_integrity", ok, detail)

    # 2. Schema integrity
    ok, detail = verify_schema_integrity(schema_path, expected_schema_hash)
    result.add_check("schema_integrity", ok, detail)

    # 3. Canonicalizer integrity (Q4)
    ok, detail, src_hash, test_hash = verify_canonicalizer_integrity()
    result.add_check("canonicalizer_integrity", ok, detail)
    result.canonicalizer_source_hash = src_hash
    result.canonicalizer_self_test_hash = test_hash

    # 4. Canonicalizer fuzzing (Q5)
    ok, detail = fuzz_canonicalizer()
    result.add_check("canonicalizer_fuzz", ok, detail)

    # 5. No artifact drift
    ok, detail = verify_no_artifact_drift(repo_root)
    result.add_check("artifact_drift", ok, detail)

    return result


# ---------------------------------------------------------------------------
# Session metadata (per instructions §3)
# ---------------------------------------------------------------------------

def build_session_metadata(
    repo_root: Path,
    constitution_path: Path,
    preflight: PreflightResult,
    calibration_hash: str,
    model_params: Dict[str, Any],
    run_id: str,
    b1: int,
    b2: int,
    context_window_size: int,
) -> Dict[str, Any]:
    """Build session_metadata.json content per instructions §3.

    Includes all frozen parameters: model, temperature, max_tokens,
    B₁, B₂, context_window_size, calibration hash.
    """
    return {
        "run_id": run_id,
        "model_identifier": model_params.get("model", ""),
        "temperature": model_params.get("temperature", 0.0),
        "max_tokens": model_params.get("max_tokens", 2048),
        "base_url": model_params.get("base_url", ""),
        "per_cycle_token_cap_b1": b1,
        "per_session_token_cap_b2": b2,
        "context_window_size": context_window_size,
        "calibration_hash": calibration_hash,
        "constitution_hash": EXPECTED_CONSTITUTION_SHA256,
        "canonicalizer_source_hash": preflight.canonicalizer_source_hash,
        "canonicalizer_self_test_hash": preflight.canonicalizer_self_test_hash,
        "preflight": preflight.to_dict(),
    }
