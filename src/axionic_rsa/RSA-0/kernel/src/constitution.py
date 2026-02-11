"""
RSA-0 Phase X — Constitution Loader

Loads the constitution YAML, verifies its SHA-256 hash,
builds a citation index for authority resolution.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class ConstitutionError(Exception):
    """Raised when the constitution cannot be loaded or verified."""
    pass


class CitationIndex:
    """
    Maps citation strings to constitution nodes.

    Two forms:
      - constitution:v0.1.1#<id>           (preferred, for nodes with 'id' field)
      - constitution:v0.1.1@<json_pointer>  (for nodes without 'id')
    """

    def __init__(self, version: str, data: Dict[str, Any]):
        self.version = version
        self._id_map: Dict[str, Any] = {}
        self._data = data
        self._build_id_index(data)

    def _build_id_index(self, obj: Any, path: str = "") -> None:
        """Recursively index all objects with an 'id' field."""
        if isinstance(obj, dict):
            if "id" in obj:
                self._id_map[obj["id"]] = obj
            for key, value in obj.items():
                self._build_id_index(value, f"{path}/{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._build_id_index(item, f"{path}/{i}")

    def resolve(self, citation: str) -> Optional[Any]:
        """
        Resolve a citation string to a constitution node.

        Returns None if unresolvable.
        """
        prefix = f"constitution:v{self.version}"

        if not citation.startswith(prefix):
            return None

        remainder = citation[len(prefix):]

        # ID-based: constitution:v0.1.1#<id>
        if remainder.startswith("#"):
            node_id = remainder[1:]
            return self._id_map.get(node_id)

        # Pointer-based: constitution:v0.1.1@<json_pointer>
        if remainder.startswith("@"):
            pointer = remainder[1:]
            return self._resolve_pointer(pointer)

        return None

    def _resolve_pointer(self, pointer: str) -> Optional[Any]:
        """Resolve a JSON-pointer-like path against the constitution data."""
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

    def all_ids(self) -> List[str]:
        return list(self._id_map.keys())

    def self_test(self) -> List[str]:
        """
        Run startup self-test: resolve all invariant IDs and key pointer paths.
        Returns list of failures (empty = pass).
        """
        failures = []

        # Test all invariant IDs
        for inv in self._data.get("invariants", []):
            inv_id = inv.get("id", "")
            citation = f"constitution:v{self.version}#{inv_id}"
            if self.resolve(citation) is None:
                failures.append(f"Failed to resolve invariant: {citation}")

        # Test key pointer paths used by system internals
        key_pointers = [
            "/telemetry_policy/required_logs",
            "/selection_policy/default_selector_rule",
            "/io_policy/allowlist",
            "/exit_policy/exit_mandatory_conditions",
            "/reflection_policy/proposal_budgets",
        ]
        for ptr in key_pointers:
            citation = f"constitution:v{self.version}@{ptr}"
            if self.resolve(citation) is None:
                failures.append(f"Failed to resolve pointer: {citation}")

        return failures


class Constitution:
    """Immutable, hash-verified constitution loaded at startup."""

    def __init__(self, yaml_path: str):
        self._yaml_path = Path(yaml_path).resolve()
        self._data: Dict[str, Any] = {}
        self._sha256: str = ""
        self._version: str = ""
        self._citation_index: Optional[CitationIndex] = None

        self._load_and_verify()

    def _load_and_verify(self) -> None:
        """Load YAML, verify hash, build citation index."""
        # Read raw bytes for hashing
        raw_bytes = self._yaml_path.read_bytes()
        self._sha256 = hashlib.sha256(raw_bytes).hexdigest()

        # Verify against stored hash
        hash_path = self._yaml_path.parent / self._yaml_path.name.replace(".yaml", ".sha256")
        if hash_path.exists():
            stored_hash = hash_path.read_text().strip().split()[0]
            if stored_hash != self._sha256:
                raise ConstitutionError(
                    f"Constitution hash mismatch: expected {stored_hash}, got {self._sha256}"
                )

        # Parse YAML
        self._data = yaml.safe_load(raw_bytes.decode("utf-8"))
        if not isinstance(self._data, dict):
            raise ConstitutionError("Constitution YAML root must be a mapping")

        self._version = self._data.get("meta", {}).get("version", "0.1.1")

        # Build citation index
        self._citation_index = CitationIndex(self._version, self._data)

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
    def citation_index(self) -> CitationIndex:
        assert self._citation_index is not None
        return self._citation_index

    # --- Convenience accessors ---

    def get_action_type_def(self, action_type: str) -> Optional[Dict[str, Any]]:
        """Look up an action type definition by type name."""
        for at in self._data.get("action_space", {}).get("action_types", []):
            if at.get("type") == action_type:
                return at
        return None

    def get_allowed_action_types(self) -> List[str]:
        return [
            at["type"]
            for at in self._data.get("action_space", {}).get("action_types", [])
        ]

    def get_read_paths(self) -> List[str]:
        return self._data.get("io_policy", {}).get("allowlist", {}).get("read_paths", [])

    def get_write_paths(self) -> List[str]:
        return self._data.get("io_policy", {}).get("allowlist", {}).get("write_paths", [])

    def is_network_enabled(self) -> bool:
        return self._data.get("io_policy", {}).get("network", {}).get("enabled", False)

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

    def get_exit_reason_codes(self) -> List[str]:
        for at in self._data.get("action_space", {}).get("action_types", []):
            if at.get("type") == "Exit":
                for f in at.get("required_fields", []):
                    if f.get("name") == "reason_code":
                        return f.get("allowed", [])
        return []

    def get_refusal_reason_codes(self) -> List[str]:
        return self._data.get("refusal_policy", {}).get("refusal_reason_codes", [])

    def get_admission_rejection_codes(self) -> List[str]:
        return self._data.get("refusal_policy", {}).get("admission_rejection_codes", [])

    def get_observation_kinds(self) -> List[str]:
        return [
            k["kind"]
            for k in self._data.get("observation_schema", {}).get("kinds", [])
        ]

    def get_required_logs(self) -> List[str]:
        return self._data.get("telemetry_policy", {}).get("required_logs", [])

    def resolve_citation(self, citation: str) -> Optional[Any]:
        return self.citation_index.resolve(citation)
