"""
X-3 Profiling Constitution Helper

Creates a profiling-specific EffectiveConstitutionFrame by:
  1. Loading the frozen v0.3 base constitution YAML
  2. Injecting AUTH_DELEGATION action_permissions (same fix as X-2D)
  3. Loading the frozen X-3 overlay JSON
  4. Wrapping in EffectiveConstitutionFrame(constitution, overlay)

This gives the profiling harness a unified frame with both
delegation admission (Gates 6T-8C) and succession/ratification
(Gates S1-S7, R0-R4) capabilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax3.constitution_x3 import EffectiveConstitutionFrame


def create_x3_profiling_constitution(
    base_yaml_path: Optional[str] = None,
    overlay_json_path: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> EffectiveConstitutionFrame:
    """
    Create a profiling constitution frame.

    1. Loads v0.3 base constitution YAML.
    2. Injects AUTH_DELEGATION action_permissions for Gate 8C.2b.
    3. Loads the frozen X-3 overlay (succession, ratification clauses).
    4. Returns EffectiveConstitutionFrame wrapping both.

    Args:
        base_yaml_path: Path to base constitution YAML.
        overlay_json_path: Path to the X-3 overlay JSON.
        repo_root: RSA-0 root directory (fallback for default paths).

    Returns:
        EffectiveConstitutionFrame instance.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent.parent

    # --- Base constitution ---
    if base_yaml_path is None:
        base_yaml_path = str(
            repo_root / "artifacts" / "phase-x" / "constitution"
            / "rsa_constitution.v0.3.yaml"
        )

    with open(base_yaml_path, "r") as f:
        raw = f.read()

    data = yaml.safe_load(raw)

    # Inject AUTH_DELEGATION action_permissions (same as X-2D)
    authority_model = data.get("AuthorityModel", {})
    action_perms = authority_model.get("action_permissions", [])

    has_delegation_perm = any(
        p.get("authority") == "AUTH_DELEGATION" for p in action_perms
    )
    if not has_delegation_perm:
        action_perms.append({
            "id": "CL-PERM-DELEGATION-ACTIONS",
            "authority": "AUTH_DELEGATION",
            "actions": ["Notify", "ReadLocal", "WriteLocal"],
        })
        authority_model["action_permissions"] = action_perms
        data["AuthorityModel"] = authority_model

    modified_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
    constitution = ConstitutionX2(yaml_string=modified_yaml)

    # --- X-3 overlay ---
    if overlay_json_path is None:
        overlay_json_path = str(
            repo_root / "artifacts" / "phase-x" / "x3"
            / "x3_overlay.v0.1.json"
        )

    with open(overlay_json_path, "r") as f:
        overlay = json.load(f)

    return EffectiveConstitutionFrame(constitution, overlay)
