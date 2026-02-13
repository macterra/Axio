#!/usr/bin/env python3
"""
RSA-0 X-0E — Freeze Manifest Generator

Produces x-0e_profile.v0.1.json containing:
  - kernel_version_id
  - constitution_path + hash
  - dependency_lock_hash
  - action surface
  - log schema
  - JCS library + version
  - CLI commands + expected log files

Usage:
    python scripts/generate_x0e_manifest.py \
        --constitution artifacts/phase-x/constitution/rsa_constitution.v0.1.1.yaml \
        --lockfile requirements-lock.txt \
        --out artifacts/phase-x/x-0e/x-0e_profile.v0.1.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

# Ensure RSA-0 root is importable
RSA0_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RSA0_ROOT))

from kernel.src.state_hash import KERNEL_VERSION_ID
from kernel.src.constitution import Constitution


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Generate X-0E freeze manifest")
    parser.add_argument("--constitution", required=True, help="Path to constitution YAML")
    parser.add_argument("--lockfile", required=True, help="Path to requirements-lock.txt")
    parser.add_argument("--out", required=True, help="Output path for manifest JSON")
    args = parser.parse_args()

    const_path = Path(args.constitution)
    lock_path = Path(args.lockfile)
    out_path = Path(args.out)

    # Load constitution
    constitution = Constitution(str(const_path))

    # Compute lockfile hash
    lock_hash = file_sha256(lock_path)

    # Detect JCS library
    try:
        import canonicaljson
        jcs_version = getattr(canonicaljson, "__version__", "unknown")
        jcs_lib = f"canonicaljson=={jcs_version}"
    except ImportError:
        jcs_lib = "unknown"

    manifest = {
        "manifest_version": "0.1",
        "phase": "X-0E",
        "kernel_version_id": KERNEL_VERSION_ID,
        "constitution": {
            "path": str(const_path),
            "version": constitution.version,
            "sha256": constitution.sha256,
        },
        "dependencies": {
            "lockfile": str(lock_path),
            "lockfile_sha256": lock_hash,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "jcs_library": jcs_lib,
        "action_surface": ["Notify"],
        "cli_commands": {
            "run": "rsa run --constitution <path> --log-dir <path> --observations <path>",
            "replay": "rsa replay --constitution <path> --log-dir <path>",
        },
        "expected_log_files": [
            "observations.jsonl",
            "artifacts.jsonl",
            "admission_trace.jsonl",
            "selector_trace.jsonl",
            "execution_trace.jsonl",
            "outbox.jsonl",
            "state_hashes.jsonl",
            "run_meta.jsonl",
        ],
        "log_schema_version": "x0e-v0.1",
        "state_hash_chain": {
            "algorithm": "SHA-256",
            "components": [
                "artifacts",
                "admission_trace",
                "selector_trace",
                "execution_trace",
            ],
            "observations_included": False,
            "concatenation": "raw-32-byte-digests",
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[X-0E] Manifest written to {out_path}")
    print(f"  kernel_version_id: {KERNEL_VERSION_ID}")
    print(f"  constitution_hash: {constitution.sha256}")
    print(f"  lockfile_hash:     {lock_hash}")
    print(f"  jcs_library:       {jcs_lib}")


if __name__ == "__main__":
    main()
