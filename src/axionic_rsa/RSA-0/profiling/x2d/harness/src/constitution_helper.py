"""
X-2D Profiling Constitution Helper

Creates a profiling-specific constitution derived from the frozen v0.3
constitution. The profiling constitution adds action_permissions for
AUTH_DELEGATION so that treaty grants can flow through the full admission
pipeline (Gate 6T → 7T → 8C).

  Background: In v0.3, AUTH_DELEGATION holds treaty_permissions (can issue
  TreatyGrant/TreatyRevocation) but has NO action_permissions. Gate 8C.2b
  requires the grantor to hold action_permissions for every granted action.
  This structural gap makes all grant admission impossible under v0.3.
  The X-2 profiling harness worked around this by pre-populating grants.
  X-2D needs grants to actually flow through admission for churn profiling.

  Solution: Add an action_permissions entry for AUTH_DELEGATION covering
  all delegable actions (Notify, ReadLocal, WriteLocal — excluding
  kernel-only LogAppend). This is a configuration change, not new physics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from kernel.src.rsax2.constitution_x2 import ConstitutionX2


def create_x2d_profiling_constitution(
    base_yaml_path: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> ConstitutionX2:
    """
    Create a profiling constitution derived from v0.3.

    Adds AUTH_DELEGATION to action_permissions with all delegable actions,
    enabling treaty grant admission through the standard pipeline.

    Args:
        base_yaml_path: Path to base constitution YAML. If None,
            uses default v0.3 path relative to repo_root.
        repo_root: RSA-0 root directory. Used if base_yaml_path is None.

    Returns:
        ConstitutionX2 instance with expanded permissions.
    """
    if base_yaml_path is None:
        if repo_root is None:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
        base_yaml_path = str(
            repo_root / "artifacts" / "phase-x" / "constitution"
            / "rsa_constitution.v0.3.yaml"
        )

    with open(base_yaml_path, "r") as f:
        raw = f.read()

    data = yaml.safe_load(raw)

    # Inject AUTH_DELEGATION action_permissions
    authority_model = data.get("AuthorityModel", {})
    action_perms = authority_model.get("action_permissions", [])

    # Check if already present
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

    # Re-serialize and construct
    modified_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
    return ConstitutionX2(yaml_string=modified_yaml)
