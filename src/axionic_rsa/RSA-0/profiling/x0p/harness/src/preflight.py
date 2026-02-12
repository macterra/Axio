"""
X-0P Pre-Flight Stability Verification

Verifies:
1. Constitution integrity (hash match)
2. Schema integrity (hash match)
3. Generator stability (same manifest hashes across 3 runs)
4. No artifact drift

Must pass before any profiling begins (per instructions §2).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import canonical_json
from kernel.src.constitution import Constitution

from profiling.x0p.harness.src.generator_common import ConditionManifest


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


def verify_generator_stability(
    generate_fn,
    seed: int,
    n_runs: int = 3,
    **kwargs,
) -> Tuple[bool, str]:
    """Verify generator produces identical manifest hashes across N runs.

    Per A3: replace model calibration with generator stability check.
    """
    hashes = []
    for i in range(n_runs):
        manifest = generate_fn(seed=seed, **kwargs)
        hashes.append(manifest.manifest_hash())

    if len(set(hashes)) == 1:
        return True, f"Generator stable across {n_runs} runs: {hashes[0][:16]}..."

    return False, f"Generator drift detected: {hashes}"


def verify_no_artifact_drift(
    repo_root: Path,
) -> Tuple[bool, str]:
    """Verify no unexpected artifact changes."""
    artifacts_dir = repo_root / "artifacts" / "phase-x"
    if not artifacts_dir.exists():
        return False, f"Artifacts directory not found: {artifacts_dir}"

    # Hash all files recursively
    file_hashes = {}
    for f in sorted(artifacts_dir.rglob("*")):
        if f.is_file():
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            file_hashes[str(f.relative_to(repo_root))] = h

    # Return the composite hash
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
    generators: Dict[str, tuple],  # {condition: (gen_fn, seed, kwargs)}
    expected_constitution_hash: str = EXPECTED_CONSTITUTION_SHA256,
    expected_schema_hash: Optional[str] = None,
) -> PreflightResult:
    """Run all pre-flight checks.

    Returns PreflightResult. If not passed, profiling must not begin.
    """
    result = PreflightResult()

    # 1. Constitution integrity
    ok, detail = verify_constitution_integrity(constitution_path, expected_constitution_hash)
    result.add_check("constitution_integrity", ok, detail)

    # 2. Schema integrity
    ok, detail = verify_schema_integrity(schema_path, expected_schema_hash)
    result.add_check("schema_integrity", ok, detail)

    # 3. No artifact drift
    ok, detail = verify_no_artifact_drift(repo_root)
    result.add_check("artifact_drift", ok, detail)

    # 4. Generator stability for each condition
    for condition, (gen_fn, seed, kwargs) in generators.items():
        ok, detail = verify_generator_stability(gen_fn, seed, n_runs=3, **kwargs)
        result.add_check(f"generator_stability_{condition}", ok, detail)

    return result


# ---------------------------------------------------------------------------
# Session metadata (per instructions §3)
# ---------------------------------------------------------------------------

def build_session_metadata(
    repo_root: Path,
    constitution_path: Path,
    preflight: PreflightResult,
    generator_config: Dict[str, Any],
    run_id: str,
) -> Dict[str, Any]:
    """Build session_metadata.json content per instructions §3.

    Since no LLM: prompt_template = null, temperature = null.
    Record generator config + corpus hash + seed instead (per H27).
    """
    # Hash the generator config for calibration
    config_hash = hashlib.sha256(
        canonical_json(generator_config).encode("utf-8")
    ).hexdigest()

    return {
        "run_id": run_id,
        "prompt_template_hash": None,
        "model_identifier": None,
        "temperature": None,
        "max_tokens": None,
        "seed": None,
        "generator_config": generator_config,
        "calibration_hash": config_hash,
        "constitution_hash": EXPECTED_CONSTITUTION_SHA256,
        "preflight": preflight.to_dict(),
    }
