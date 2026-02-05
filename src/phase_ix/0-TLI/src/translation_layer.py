"""
Translation Layer

Per preregistration §2.4:
- Pure function mapping intent to artifact
- Precondition: only emit artifact when intent outcome is VALID
- AMBIGUOUS → TRANSLATION_REFUSED
- INCOMPLETE → TRANSLATION_FAILED
- Identity passthrough for user fields
- Deterministic generation for derived fields
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class TranslationStatus(Enum):
    """Status of translation attempt."""
    SUCCESS = "SUCCESS"
    TRANSLATION_REFUSED = "TRANSLATION_REFUSED"
    TRANSLATION_FAILED = "TRANSLATION_FAILED"


@dataclass
class TranslationResult:
    """Result of translation attempt."""
    status: TranslationStatus
    artifact: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    diagnostic: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        if self.status == TranslationStatus.SUCCESS:
            return self.artifact
        return {
            "status": self.status.value,
            "reason": self.reason,
            "diagnostic": self.diagnostic
        }


@dataclass
class FaultConfig:
    """
    Fault injection configuration per preregistration §9.3.

    inject_hidden_field: Tuple of (field_name, value) to inject (Condition D)
    modify_on_submission: Dict of field modifications for submission phase (Condition H)
    coerce_from_framing: Whether to apply framing values (should remain False) (Condition E)
    """
    inject_hidden_field: Optional[Tuple[str, Any]] = None
    modify_on_submission: Optional[Dict[str, Any]] = None
    coerce_from_framing: bool = False


# Required fields per intent schema §2.1
REQUIRED_INTENT_FIELDS = frozenset(['holder', 'scope', 'aav', 'expiry_epoch'])

# Valid AAV values per §2.1
VALID_AAV = frozenset(['READ', 'WRITE', 'EXECUTE', 'DELEGATE', 'ADMIN'])


class TranslationLayer:
    """
    Translation Layer for converting intent to authority artifact.

    Per preregistration §2.4 and §7.2:
    - Uses fixed clock for created_epoch
    - Uses sequence counter for authority_id generation
    - Supports sequence reset for replay determinism
    """

    def __init__(self, fixed_clock: int = 1738713600, sequence_seed: int = 1):
        """
        Initialize TL with determinism controls.

        Args:
            fixed_clock: Fixed epoch for created_epoch (default: 2025-02-05 00:00:00 UTC)
            sequence_seed: Starting value for sequence counter (default: 1)
        """
        self._fixed_clock = fixed_clock
        self._sequence = sequence_seed
        self._fault_config: Optional[FaultConfig] = None
        self._is_preview_phase = True  # For Condition H

    def reset_sequence(self, value: int) -> None:
        """
        Reset sequence counter to specified value.
        Per preregistration §7.2 Sequence Reset Rule.
        """
        self._sequence = value

    def set_fault_config(self, config: Optional[FaultConfig]) -> None:
        """Configure fault injection for adversarial testing."""
        self._fault_config = config

    def clear_fault_config(self) -> None:
        """Clear fault injection configuration."""
        self._fault_config = None

    def set_preview_phase(self, is_preview: bool) -> None:
        """Set whether current translation is preview (True) or submission (False)."""
        self._is_preview_phase = is_preview

    def _validate_intent(self, intent: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate intent structure.

        Returns:
            Tuple of (is_valid, failure_reason, diagnostic)
        """
        # Check for missing required fields (INCOMPLETE)
        for field_name in REQUIRED_INTENT_FIELDS:
            if field_name not in intent:
                return (False, "INCOMPLETE_INTENT", f"Required field '{field_name}' not specified")

        # Validate holder is string
        if not isinstance(intent.get('holder'), str):
            return (False, "INCOMPLETE_INTENT", "Field 'holder' must be a string")

        # Validate aav
        if intent.get('aav') not in VALID_AAV:
            return (False, "INCOMPLETE_INTENT", f"Field 'aav' must be one of {sorted(VALID_AAV)}")

        # Validate expiry_epoch
        expiry = intent.get('expiry_epoch')
        if not isinstance(expiry, int) or expiry < 0:
            return (False, "INCOMPLETE_INTENT", "Field 'expiry_epoch' must be a non-negative integer")

        # Validate scope
        scope = intent.get('scope')
        if not isinstance(scope, list) or len(scope) < 1:
            return (False, "INCOMPLETE_INTENT", "Field 'scope' must be a non-empty array")

        # Validate each scope entry
        for i, entry in enumerate(scope):
            if not isinstance(entry, dict):
                return (False, "INCOMPLETE_INTENT", f"Scope entry {i} must be an object")
            if 'resource' not in entry or 'operation' not in entry:
                return (False, "INCOMPLETE_INTENT", f"Scope entry {i} missing required field")
            if entry.get('operation') not in VALID_AAV:
                return (False, "INCOMPLETE_INTENT", f"Scope entry {i} has invalid operation")

        return (True, None, None)

    def _check_ambiguity(self, intent: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check for ambiguity per Scope Ambiguity Rule §2.1.

        Returns:
            Tuple of (is_ambiguous, reason, diagnostic)
        """
        scope = intent.get('scope', [])
        if len(scope) > 1:
            return (True, "AMBIGUOUS_SCOPE_MULTIPLE",
                    f"Scope contains {len(scope)} entries; exactly 1 required")
        return (False, None, None)

    def translate(self, intent: Dict[str, Any], framing: Optional[Dict[str, Any]] = None) -> TranslationResult:
        """
        Translate intent to authority artifact.

        Per preregistration §2.4:
        - Precondition: Only emit artifact when outcome is VALID
        - AMBIGUOUS → TRANSLATION_REFUSED
        - INCOMPLETE → TRANSLATION_FAILED

        Args:
            intent: User intent dictionary
            framing: Optional framing payload (must be ignored per Condition E)

        Returns:
            TranslationResult with artifact or refusal/failure
        """
        # Step 1: Validate completeness
        is_valid, fail_reason, fail_diagnostic = self._validate_intent(intent)
        if not is_valid:
            return TranslationResult(
                status=TranslationStatus.TRANSLATION_FAILED,
                reason=fail_reason,
                diagnostic=fail_diagnostic
            )

        # Step 2: Check ambiguity
        is_ambiguous, ambig_reason, ambig_diagnostic = self._check_ambiguity(intent)
        if is_ambiguous:
            return TranslationResult(
                status=TranslationStatus.TRANSLATION_REFUSED,
                reason=ambig_reason,
                diagnostic=ambig_diagnostic
            )

        # Step 3: Generate artifact (intent is VALID)
        authority_id = f"TLI-{self._sequence:03d}"
        self._sequence += 1

        # Build artifact with identity passthrough for user fields
        artifact = {
            "aav": intent["aav"],
            "authority_id": authority_id,
            "created_epoch": self._fixed_clock,
            "expiry_epoch": intent["expiry_epoch"],
            "holder": intent["holder"],
            "lineage": "VOID",
            "scope": intent["scope"],  # Array preserved
            "status": "PENDING"
        }

        # Apply fault injection if configured
        if self._fault_config:
            # Condition D: Hidden field injection
            if self._fault_config.inject_hidden_field:
                field_name, field_value = self._fault_config.inject_hidden_field
                artifact[field_name] = field_value

            # Condition H: Modify on submission (not preview)
            if not self._is_preview_phase and self._fault_config.modify_on_submission:
                for key, value in self._fault_config.modify_on_submission.items():
                    artifact[key] = value

            # Condition E: Coerce from framing (should remain False in correct TL)
            if self._fault_config.coerce_from_framing and framing:
                # This is intentionally a fault - correct TL never does this
                if 'suggested_aav' in framing:
                    artifact['aav'] = framing['suggested_aav']
                if 'suggested_expiry' in framing:
                    artifact['expiry_epoch'] = framing['suggested_expiry']

        return TranslationResult(
            status=TranslationStatus.SUCCESS,
            artifact=artifact
        )
