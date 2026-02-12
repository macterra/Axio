"""
RSA X-1 — Constitution Loader Extension

Extends the RSA-0 Constitution loader with:
  - Hash-based citation resolution: constitution:<hash>#<id>
  - Authority namespace: authority:<hash>#AUTH_*
  - ECK section accessors (AmendmentProcedure, AuthorityModel, etc.)
  - Constitution canonicalization and byte-size enforcement
  - Support for loading constitution from YAML string (for proposed constitutions)
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..constitution import Constitution, CitationIndex, ConstitutionError


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------

def canonicalize_constitution_bytes(raw: bytes) -> bytes:
    """
    Canonical form of constitution bytes:
      - Normalize \\r\\n → \\n
      - Strip trailing whitespace per line
      - Require UTF-8
      - Reject tabs (do not normalize)

    Returns canonical UTF-8 bytes.
    Raises ConstitutionError on tabs or encoding issues.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ConstitutionError(f"Constitution is not valid UTF-8: {e}")

    if "\t" in text:
        raise ConstitutionError("Constitution contains tab characters (forbidden)")

    # Normalize line endings
    text = text.replace("\r\n", "\n")

    # Strip trailing whitespace per line
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    text = "\n".join(lines)

    return text.encode("utf-8")


def constitution_hash(raw: bytes) -> str:
    """SHA-256 hex digest of raw constitution bytes."""
    return hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# Extended Citation Index (hash-based)
# ---------------------------------------------------------------------------

class CitationIndexX1:
    """
    Extended citation index supporting:
      - constitution:<hash>#<id>           (invariants, CL-* clauses)
      - constitution:<hash>@<json_pointer> (structural paths)
      - authority:<hash>#AUTH_*            (authority identifiers)

    Also supports legacy constitution:v<version>#<id> format for backward compat.
    """

    def __init__(self, constitution_hash: str, version: str, data: Dict[str, Any]):
        self._hash = constitution_hash
        self._version = version
        self._data = data
        self._id_map: Dict[str, Any] = {}
        self._authority_set: set = set()
        self._build(data)

    def _build(self, obj: Any, path: str = "") -> None:
        """Recursively index all objects with an 'id' field, and collect authorities."""
        if isinstance(obj, dict):
            if "id" in obj:
                self._id_map[obj["id"]] = obj
            for key, value in obj.items():
                self._build(value, f"{path}/{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._build(item, f"{path}/{i}")

        # Build authority set from AuthorityModel
        authority_model = self._data.get("AuthorityModel", {})
        self._authority_set = set(authority_model.get("authorities", []))

    def resolve(self, citation: str) -> Optional[Any]:
        """
        Resolve a citation to a constitution/authority node.

        Supported formats:
          - constitution:<hash>#<id>
          - constitution:<hash>@<pointer>
          - constitution:v<version>#<id>    (legacy)
          - constitution:v<version>@<pointer>  (legacy)
          - authority:<hash>#AUTH_*
        """
        # Authority namespace
        if citation.startswith("authority:"):
            return self._resolve_authority(citation)

        # Constitution namespace
        if citation.startswith("constitution:"):
            return self._resolve_constitution(citation)

        return None

    def _resolve_authority(self, citation: str) -> Optional[Any]:
        """Resolve authority:<hash>#AUTH_<name>."""
        prefix = f"authority:{self._hash}"
        if not citation.startswith(prefix):
            return None

        remainder = citation[len(prefix):]
        if not remainder.startswith("#"):
            return None

        auth_id = remainder[1:]
        if auth_id in self._authority_set:
            # Return authority mapping info from AuthorityModel
            authority_model = self._data.get("AuthorityModel", {})
            for perm in authority_model.get("action_permissions", []):
                if perm.get("authority") == auth_id:
                    return perm
            for perm in authority_model.get("amendment_permissions", []):
                if perm.get("authority") == auth_id:
                    return perm
            # Authority exists but has no explicit permission mapping
            return {"authority": auth_id, "exists": True}

        return None

    def _resolve_constitution(self, citation: str) -> Optional[Any]:
        """Resolve constitution:<hash-or-version>#<id> or @<pointer>."""
        hash_prefix = f"constitution:{self._hash}"
        version_prefix = f"constitution:v{self._version}"

        for prefix in (hash_prefix, version_prefix):
            if citation.startswith(prefix):
                remainder = citation[len(prefix):]

                if remainder.startswith("#"):
                    node_id = remainder[1:]
                    return self._id_map.get(node_id)

                if remainder.startswith("@"):
                    pointer = remainder[1:]
                    return self._resolve_pointer(pointer)

        return None

    def _resolve_pointer(self, pointer: str) -> Optional[Any]:
        """Resolve JSON-pointer-like path against constitution data."""
        if not pointer or pointer == "/":
            return self._data

        parts = pointer.strip("/").split("/")
        current = self._data

        for part in parts:
            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    return None
            elif isinstance(current, list):
                try:
                    idx = int(part)
                    current = current[idx]
                except (ValueError, IndexError):
                    return None
            else:
                return None

        return current

    def has_id(self, node_id: str) -> bool:
        return node_id in self._id_map

    def has_authority(self, auth_id: str) -> bool:
        return auth_id in self._authority_set

    def all_ids(self) -> List[str]:
        return list(self._id_map.keys())

    def all_authorities(self) -> List[str]:
        return sorted(self._authority_set)

    def validate_citation_both(self, citations: List[str]) -> Tuple[bool, str]:
        """
        Validate citations under authority_reference_mode = BOTH.
        Requires:
          - At least one authority citation (authority:<hash>#AUTH_*)
          - At least one clause-or-invariant citation (constitution:<hash>#CL-* or #INV-*)
          - All citations must resolve.

        Returns (valid, error_message).
        """
        has_authority = False
        has_clause_or_invariant = False

        for citation in citations:
            resolved = self.resolve(citation)
            if resolved is None:
                return False, f"Unresolvable citation: {citation}"

            if citation.startswith("authority:"):
                has_authority = True
            elif citation.startswith("constitution:"):
                # Check if it references a CL-* or INV-* node
                for prefix_type in (f"constitution:{self._hash}#", f"constitution:v{self._version}#"):
                    if citation.startswith(prefix_type):
                        node_id = citation[len(prefix_type):]
                        if node_id.startswith("CL-") or node_id.startswith("INV-"):
                            has_clause_or_invariant = True

        if not has_authority:
            return False, "BOTH mode requires at least one authority citation"
        if not has_clause_or_invariant:
            return False, "BOTH mode requires at least one clause or invariant citation"

        return True, ""


# ---------------------------------------------------------------------------
# Extended Constitution (X-1)
# ---------------------------------------------------------------------------

class ConstitutionX1:
    """
    Constitution with X-1 extensions.

    Can be loaded from:
      - A YAML file path (for base constitutions)
      - A YAML string + known hash (for proposed constitutions during validation)
    """

    def __init__(
        self,
        *,
        yaml_path: Optional[str] = None,
        yaml_string: Optional[str] = None,
        expected_hash: Optional[str] = None,
    ):
        self._data: Dict[str, Any] = {}
        self._raw_bytes: bytes = b""
        self._sha256: str = ""
        self._version: str = ""
        self._citation_index: Optional[CitationIndexX1] = None

        if yaml_path:
            self._load_from_file(yaml_path, expected_hash)
        elif yaml_string is not None:
            self._load_from_string(yaml_string, expected_hash)
        else:
            raise ConstitutionError("Must provide yaml_path or yaml_string")

    def _load_from_file(self, yaml_path: str, expected_hash: Optional[str]) -> None:
        path = Path(yaml_path).resolve()
        raw = path.read_bytes()
        self._raw_bytes = raw
        self._sha256 = hashlib.sha256(raw).hexdigest()

        if expected_hash and expected_hash != self._sha256:
            raise ConstitutionError(
                f"Hash mismatch: expected {expected_hash}, got {self._sha256}"
            )

        # Also check .sha256 sidecar file
        hash_path = path.parent / path.name.replace(".yaml", ".sha256")
        if hash_path.exists():
            stored = hash_path.read_text().strip().split()[0]
            if stored != self._sha256:
                raise ConstitutionError(
                    f"Hash mismatch with sidecar: expected {stored}, got {self._sha256}"
                )

        self._data = yaml.safe_load(raw.decode("utf-8"))
        if not isinstance(self._data, dict):
            raise ConstitutionError("Constitution YAML root must be a mapping")

        self._version = self._data.get("meta", {}).get("version", "")
        self._citation_index = CitationIndexX1(self._sha256, self._version, self._data)

    def _load_from_string(self, yaml_string: str, expected_hash: Optional[str]) -> None:
        raw = yaml_string.encode("utf-8")
        self._raw_bytes = raw
        self._sha256 = hashlib.sha256(raw).hexdigest()

        if expected_hash and expected_hash != self._sha256:
            raise ConstitutionError(
                f"Hash mismatch: expected {expected_hash}, got {self._sha256}"
            )

        self._data = yaml.safe_load(yaml_string)
        if not isinstance(self._data, dict):
            raise ConstitutionError("Constitution YAML root must be a mapping")

        self._version = self._data.get("meta", {}).get("version", "")
        self._citation_index = CitationIndexX1(self._sha256, self._version, self._data)

    # --- Properties ---

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    @property
    def version(self) -> str:
        return self._version

    @property
    def sha256(self) -> str:
        return self._sha256

    @property
    def raw_bytes(self) -> bytes:
        return self._raw_bytes

    @property
    def citation_index(self) -> CitationIndexX1:
        assert self._citation_index is not None
        return self._citation_index

    # --- ECK Accessors ---

    @property
    def amendment_procedure(self) -> Dict[str, Any]:
        return self._data.get("AmendmentProcedure", {})

    @property
    def authority_model(self) -> Dict[str, Any]:
        return self._data.get("AuthorityModel", {})

    @property
    def warrant_definition(self) -> Dict[str, Any]:
        return self._data.get("WarrantDefinition", {})

    @property
    def scope_system(self) -> Dict[str, Any]:
        return self._data.get("ScopeSystem", {})

    def has_eck_sections(self) -> bool:
        """Check all 4 ECK sections are present."""
        return all(
            s in self._data
            for s in ("AmendmentProcedure", "AuthorityModel", "WarrantDefinition", "ScopeSystem")
        )

    # --- Amendment Policy Accessors ---

    def amendments_enabled(self) -> bool:
        return self._data.get("amendment_policy", {}).get("amendments_enabled", False)

    def max_constitution_bytes(self) -> int:
        return self._data.get("amendment_policy", {}).get("max_constitution_bytes", 32768)

    def max_amendment_candidates_per_cycle(self) -> int:
        return self._data.get("amendment_policy", {}).get("max_amendment_candidates_per_cycle", 3)

    def max_pending_amendments(self) -> int:
        return self._data.get("amendment_policy", {}).get("max_pending_amendments", 5)

    def cooling_period_cycles(self) -> int:
        return self.amendment_procedure.get("cooling_period_cycles", 2)

    def authorization_threshold(self) -> int:
        return self.amendment_procedure.get("authorization_threshold", 1)

    def authority_reference_mode(self) -> str:
        return self.amendment_procedure.get("authority_reference_mode", "BOTH")

    def density_upper_bound(self) -> Optional[float]:
        return self.amendment_procedure.get("density_upper_bound")

    # --- Action space accessors ---

    def get_action_types(self) -> List[str]:
        return [
            at["type"]
            for at in self._data.get("action_space", {}).get("action_types", [])
        ]

    def get_action_type_def(self, action_type: str) -> Optional[Dict[str, Any]]:
        for at in self._data.get("action_space", {}).get("action_types", []):
            if at.get("type") == action_type:
                return at
        return None

    # --- Authority model helpers ---

    def get_action_permissions(self) -> List[Dict[str, Any]]:
        return self.authority_model.get("action_permissions", [])

    def get_amendment_permissions(self) -> List[Dict[str, Any]]:
        return self.authority_model.get("amendment_permissions", [])

    def compute_density(self) -> Tuple[int, int, int, float]:
        """
        Compute authority-action density from action_permissions only.
        Returns (A, B, M, density).
        """
        action_perms = self.get_action_permissions()
        A = len(set(p["authority"] for p in action_perms))
        B = len(self.get_action_types())
        M = sum(len(p.get("actions", [])) for p in action_perms)

        if A == 0 or B == 0:
            return A, B, M, 0.0

        density = M / (A * B)
        return A, B, M, density

    # --- IO policy ---

    def get_read_paths(self) -> List[str]:
        return self._data.get("io_policy", {}).get("allowlist", {}).get("read_paths", [])

    def get_write_paths(self) -> List[str]:
        return self._data.get("io_policy", {}).get("allowlist", {}).get("write_paths", [])

    # --- Reflection policy ---

    def max_candidates_per_cycle(self) -> int:
        return (
            self._data.get("reflection_policy", {})
            .get("proposal_budgets", {})
            .get("max_candidates_per_cycle", 5)
        )

    def max_total_tokens_per_cycle(self) -> int:
        return (
            self._data.get("reflection_policy", {})
            .get("proposal_budgets", {})
            .get("max_total_tokens_per_cycle", 6000)
        )

    # --- Citation helpers ---

    def resolve_citation(self, citation: str) -> Optional[Any]:
        return self.citation_index.resolve(citation)

    def make_citation(self, node_id: str) -> str:
        """Create a hash-based citation for a node ID."""
        return f"constitution:{self._sha256}#{node_id}"

    def make_authority_citation(self, auth_id: str) -> str:
        """Create an authority citation."""
        return f"authority:{self._sha256}#{auth_id}"
