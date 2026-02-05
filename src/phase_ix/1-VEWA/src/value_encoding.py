"""
Value Encoding Harness (VEH)

Per preregistration §2.5 and §8.2:
- Pure function: value declaration → authority artifact
- Deterministic sequence counter for authority_id generation
- Fixed clock for created_epoch
- Strict 1:1 bijection: one value → one artifact
- No interpretation, inference, or default injection beyond the encoding table

Schema validation per §2.1 (value declarations) and §2.2 (authority artifacts).
"""

import json
from typing import Any, Dict, List, Optional

from .canonical import canonicalize

# Valid AAV operations per §2.1, §2.2
VALID_OPERATIONS = frozenset(["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"])

# Valid commitments per §2.1
VALID_COMMITMENTS = frozenset(["ALLOW", "DENY"])

# Fixed holder per §2.2, §2.5
FIXED_HOLDER = "VALUE_AUTHORITY"

# Fixed lineage type per §2.5
FIXED_LINEAGE_TYPE = "VALUE_DECLARATION"

# Fixed encoding epoch per §2.5
FIXED_ENCODING_EPOCH = 0

# Fixed expiry epoch per §2.5 (perpetual in IX-1)
FIXED_EXPIRY_EPOCH = 0

# Fixed status per §2.2, §2.5
FIXED_STATUS = "ACTIVE"


class ValueEncodingError(Exception):
    """Raised when a value declaration cannot be encoded."""
    pass


class ValueEncodingHarness:
    """
    Value Encoding Harness (VEH).

    Converts value declarations to authority artifacts per §2.5.
    Pure deterministic mapping with sequence counter and fixed clock.
    """

    def __init__(self, fixed_clock: int, sequence_start: int = 1):
        """
        Initialize VEH.

        Args:
            fixed_clock: Frozen epoch timestamp for created_epoch (§6.2).
            sequence_start: Starting value for authority_id sequence counter.
        """
        self._fixed_clock = fixed_clock
        self._sequence_counter = sequence_start

    def reset_sequence(self, value: int = 1) -> None:
        """
        Reset the sequence counter per §6.2 Sequence Reset Rule.

        Args:
            value: New sequence counter start value.
        """
        self._sequence_counter = value

    @property
    def current_sequence(self) -> int:
        """Current sequence counter value."""
        return self._sequence_counter

    def _generate_authority_id(self) -> str:
        """
        Generate next authority_id in VEWA-<NNN> format per §2.5.

        Returns:
            Authority ID string (e.g., "VEWA-001").
        """
        authority_id = f"VEWA-{self._sequence_counter:03d}"
        self._sequence_counter += 1
        return authority_id

    def validate_value_declaration(self, value: Dict[str, Any]) -> None:
        """
        Validate a value declaration against §2.1 schema.

        Raises:
            ValueEncodingError: If validation fails.
        """
        # Check required fields
        required_fields = {"value_id", "scope", "commitment"}
        actual_fields = set(value.keys())

        missing = required_fields - actual_fields
        if missing:
            raise ValueEncodingError(
                f"Missing required fields: {sorted(missing)}"
            )

        # Check no additional properties (§2.1 additionalProperties: false)
        extra = actual_fields - required_fields
        if extra:
            raise ValueEncodingError(
                f"Forbidden additional fields: {sorted(extra)}"
            )

        # Validate value_id
        if not isinstance(value["value_id"], str) or not value["value_id"]:
            raise ValueEncodingError("value_id must be a non-empty string")

        # Validate commitment
        if value["commitment"] not in VALID_COMMITMENTS:
            raise ValueEncodingError(
                f"commitment must be one of {sorted(VALID_COMMITMENTS)}, "
                f"got: {value['commitment']!r}"
            )

        # Validate scope
        scope = value["scope"]
        if not isinstance(scope, list):
            raise ValueEncodingError("scope must be an array")
        if len(scope) < 1:
            raise ValueEncodingError("scope must have minItems: 1")
        if len(scope) > 1:
            raise ValueEncodingError(
                "scope must have maxItems: 1 (atomic scope in IX-1)"
            )

        # Validate scope atom
        atom = scope[0]
        if not isinstance(atom, dict):
            raise ValueEncodingError("scope atom must be an object")

        atom_required = {"target", "operation"}
        atom_fields = set(atom.keys())

        atom_missing = atom_required - atom_fields
        if atom_missing:
            raise ValueEncodingError(
                f"Scope atom missing required fields: {sorted(atom_missing)}"
            )

        atom_extra = atom_fields - atom_required
        if atom_extra:
            raise ValueEncodingError(
                f"Scope atom has forbidden additional fields: {sorted(atom_extra)}"
            )

        if not isinstance(atom["target"], str) or not atom["target"]:
            raise ValueEncodingError("scope atom target must be a non-empty string")

        if atom["operation"] not in VALID_OPERATIONS:
            raise ValueEncodingError(
                f"scope atom operation must be one of {sorted(VALID_OPERATIONS)}, "
                f"got: {atom['operation']!r}"
            )

    def encode_value(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encode a single value declaration as an authority artifact per §2.5.

        This is the core bijective mapping:
        - scope → scope (passthrough)
        - scope[0].operation → aav (identity)
        - commitment → commitment (passthrough)
        - value_id → lineage.value_id (passthrough)
        - Generated: authority_id, holder, lineage.type, lineage.encoding_epoch,
                     created_epoch, expiry_epoch, status

        Args:
            value: Validated value declaration dict.

        Returns:
            Authority artifact dict in canonical field order.

        Raises:
            ValueEncodingError: If encoding fails.
        """
        self.validate_value_declaration(value)

        authority_id = self._generate_authority_id()

        # Build artifact per §2.5 encoding table
        artifact = {
            "aav": value["scope"][0]["operation"],
            "authority_id": authority_id,
            "commitment": value["commitment"],
            "created_epoch": self._fixed_clock,
            "expiry_epoch": FIXED_EXPIRY_EPOCH,
            "holder": FIXED_HOLDER,
            "lineage": {
                "encoding_epoch": FIXED_ENCODING_EPOCH,
                "type": FIXED_LINEAGE_TYPE,
                "value_id": value["value_id"],
            },
            "scope": value["scope"],
            "status": FIXED_STATUS,
        }

        return artifact

    def encode(self, values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Encode a list of value declarations as authority artifacts.

        Per §2.5: strict 1:1 bijection — each value produces exactly one artifact.

        Args:
            values: List of value declaration dicts.

        Returns:
            List of authority artifact dicts, in encoding order.
        """
        return [self.encode_value(v) for v in values]

    def validate_artifact(self, artifact: Dict[str, Any]) -> List[str]:
        """
        Validate an authority artifact against §2.2 schema.
        Returns list of violation descriptions (empty = valid).

        Used by conflict_probe to detect injected fields (Condition D).
        """
        violations = []

        # Check required fields per §2.2
        required = {
            "authority_id", "holder", "scope", "aav", "commitment",
            "lineage", "created_epoch", "expiry_epoch", "status"
        }
        actual = set(artifact.keys())

        missing = required - actual
        if missing:
            violations.append(f"Missing required fields: {sorted(missing)}")

        # Check for forbidden additional properties
        extra = actual - required
        if extra:
            violations.append(
                f"Forbidden additional fields detected: {sorted(extra)}"
            )

        # Validate holder
        if artifact.get("holder") != FIXED_HOLDER:
            violations.append(
                f"holder must be '{FIXED_HOLDER}', "
                f"got: {artifact.get('holder')!r}"
            )

        # Validate aav
        if artifact.get("aav") not in VALID_OPERATIONS:
            violations.append(
                f"aav must be one of {sorted(VALID_OPERATIONS)}, "
                f"got: {artifact.get('aav')!r}"
            )

        # Validate commitment
        if artifact.get("commitment") not in VALID_COMMITMENTS:
            violations.append(
                f"commitment must be one of {sorted(VALID_COMMITMENTS)}, "
                f"got: {artifact.get('commitment')!r}"
            )

        # Validate scope (maxItems: 1)
        scope = artifact.get("scope")
        if isinstance(scope, list):
            if len(scope) < 1:
                violations.append("scope must have minItems: 1")
            elif len(scope) > 1:
                violations.append("scope must have maxItems: 1")
        else:
            violations.append("scope must be an array")

        # Validate status
        if artifact.get("status") != FIXED_STATUS:
            violations.append(
                f"status must be '{FIXED_STATUS}', "
                f"got: {artifact.get('status')!r}"
            )

        # Validate lineage
        lineage = artifact.get("lineage")
        if isinstance(lineage, dict):
            if lineage.get("type") != FIXED_LINEAGE_TYPE:
                violations.append(
                    f"lineage.type must be '{FIXED_LINEAGE_TYPE}', "
                    f"got: {lineage.get('type')!r}"
                )
        else:
            violations.append("lineage must be an object")

        return violations
