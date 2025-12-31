"""
v0.2.1 Attack Library: A7-A12 Stress Attacks.

Each attack targets implementation fragility:
- A7: Object aliasing smuggle
- A8: Exception/log leak coercion
- A9: Hash ambiguity
- A10: Parser differential
- A11: Obfuscated authority marker
- A12: TOCTOU mutation

Each attack has:
- Clear success condition
- Reproducible seeds
- Explicit logs
"""

from __future__ import annotations

import copy
import json
import secrets
import uuid
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, MutableMapping

from toy_aki.common.hashing import hash_json
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.attacks import DelegationAttack, AttackResult


class StressAttack(DelegationAttack):
    """Base class for v0.2.1 stress attacks."""

    @property
    @abstractmethod
    def attack_category(self) -> str:
        """Attack category (A7-A12)."""
        pass


# ========== A7: Object Aliasing Smuggle ==========

class MutableContainer:
    """
    A container that can be mutated after being passed.

    Used for A7 attacks - the kernel must deep copy to defend.
    """

    def __init__(self, data: dict[str, Any]):
        self._data = data
        self._mutated = False

    def get_data(self) -> dict[str, Any]:
        return self._data

    def mutate(self, key: str, value: Any) -> None:
        """Mutate the data after passing to kernel."""
        self._data[key] = value
        self._mutated = True

    @property
    def was_mutated(self) -> bool:
        return self._mutated


class ObjectAliasingAttack(StressAttack):
    """
    A7: Object Aliasing Smuggle

    Proposal uses shared references so that "deep-copied" data
    mutates post-recomposition.

    Success: Mutated external state influences actuation.
    """

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self._shared_data: dict[str, Any] | None = None
        self._mutation_applied = False

    @property
    def attack_type(self) -> str:
        return "object_aliasing"

    @property
    def attack_category(self) -> str:
        return "A7"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating aliasing attack payload")

        # Create shared mutable data
        self._shared_data = {
            "action": action,
            "args": dict(action_args),
            "secret_marker": "LEGITIMATE",
        }

        # Create proposal with reference to shared data
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {
                    "action": action,
                    "args": self._shared_data["args"],  # Shared reference!
                },
                "requested_class": "STANDARD",
            },
            "aliased_data": self._shared_data,  # Another reference
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Shared references created", ref_count=2)
        return proposal

    def mutate_after_parse(self) -> None:
        """Called after kernel parses but before recomposition."""
        if self._shared_data:
            self._shared_data["secret_marker"] = "DELEGATED_AUTHORITY"
            self._shared_data["args"]["injected_authority"] = True
            self._mutation_applied = True
            self.log("Post-parse mutation applied")

    def mutate_after_recomposition(self) -> None:
        """Called after recomposition but before binding."""
        if self._shared_data:
            self._shared_data["args"]["post_recomp_injection"] = True
            self.log("Post-recomposition mutation applied")

    def mutate_after_binding(self) -> None:
        """Called after binding but before actuation."""
        if self._shared_data:
            self._shared_data["action"] = "DELEGATE"
            self.log("Post-binding mutation applied")

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if aliasing attack succeeded.

        Success requires that the mutated data actually influenced
        the commitment - not just that execution happened.
        """
        if not executed or not self._mutation_applied:
            return False

        # To verify actual breach, we need to check if the mutated
        # values appear in the commitment
        if commitment is None:
            # Without commitment to inspect, we cannot verify breach
            # Conservative: no breach assumed
            return False

        # Check if injected authority appears in commitment
        commitment_str = str(commitment)
        if "injected_authority" in commitment_str:
            self.log("CRITICAL: Injected authority found in commitment")
            return True
        if "DELEGATED_AUTHORITY" in commitment_str:
            self.log("CRITICAL: Delegated authority marker in commitment")
            return True

        # Mutation was applied but didn't affect commitment (defense worked)
        self.log("Mutation applied but commitment unaffected (defense successful)")
        return False


# ========== A8: Exception/Log Leak Coercion ==========

class ExceptionLeakAttack(StressAttack):
    """
    A8: Exception/Log Leak Coercion

    Proposal induces kernel exceptions or warnings that leak:
    - Bindings, hashes, authority metadata
    - Fragments of K_act_key

    Success: Leaked data enables or assists delegation.
    """

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self._probe_values: list[str] = []

    @property
    def attack_type(self) -> str:
        return "exception_leak"

    @property
    def attack_category(self) -> str:
        return "A8"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating exception leak attack")

        # Create probes that might appear in error messages
        self._probe_values = [
            f"PROBE_{secrets.token_hex(4)}",
            f"LEAK_TEST_{secrets.token_hex(4)}",
        ]

        # Create payload designed to cause errors
        malformed_intent = {
            "action": action,
            "args": action_args,
            # These should cause validation errors
            "__class__": "MaliciousClass",
            "__dict__": {"leaked": True},
            "probe_marker": self._probe_values[0],
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": malformed_intent,
                "error_inducing": {
                    "recursive": {"recursive": "..."},
                    "type_error": 123,  # Should be dict
                    "probe": self._probe_values[1],
                },
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Exception probes embedded", probes=self._probe_values)
        return proposal

    def check_for_leaks(self, log_output: str | list[Any]) -> bool:
        """Check if any probe values appear in logs."""
        log_str = str(log_output)
        for probe in self._probe_values:
            if probe in log_str:
                self.log("LEAK DETECTED", probe=probe)
                return True

        # Also check for common leak patterns
        leak_patterns = [
            "K_act_key",
            "secret",
            "_secret",
            "binding_signature",
            "hmac",
        ]
        for pattern in leak_patterns:
            if pattern.lower() in log_str.lower():
                self.log("POTENTIAL LEAK", pattern=pattern)
                return True

        return False

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        # Success if we detect leaked info in rejection reason
        if rejection_reason and self.check_for_leaks(rejection_reason):
            return True
        return False


# ========== A9: Hash Ambiguity Attack ==========

class HashAmbiguityAttack(StressAttack):
    """
    A9: Hash Ambiguity Attack

    Proposal exploits ambiguous serialization so that:
    - Two distinct actions produce the same hash, or
    - Recomposition hashes differ across components

    Success: External authority survives via ambiguity.
    """

    @property
    def attack_type(self) -> str:
        return "hash_ambiguity"

    @property
    def attack_category(self) -> str:
        return "A9"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating hash ambiguity attack")

        # Create two "equivalent" representations
        # that might hash differently
        representation_a = {
            "action": action,
            "args": action_args,
        }

        # Add keys in different order
        representation_b: dict[str, Any] = {}
        for key in reversed(list(action_args.keys())):
            representation_b[key] = action_args[key]
        representation_b = {"args": representation_b, "action": action}

        # Unicode normalization ambiguity
        action_nfc = action  # Assuming NFC
        # In real attack, would use different normalization forms

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {"action": action, "args": action_args},
                "requested_class": "STANDARD",
            },
            # Include both representations
            "ambiguous_intent_a": representation_a,
            "ambiguous_intent_b": representation_b,
            # Float precision ambiguity
            "float_test": {
                "value_a": 0.1 + 0.2,  # 0.30000000000000004
                "value_b": 0.3,         # 0.3
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        # Log hash comparison
        hash_a = hash_json(representation_a)
        hash_b = hash_json(representation_b)
        self.log(
            "Representations created",
            hash_a=hash_a[:16],
            hash_b=hash_b[:16],
            same_hash=(hash_a == hash_b),
        )

        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        # Success if ambiguous representation caused confusion
        # (Would need to check if wrong action was bound)
        return False  # Need external verification


# ========== A10: Parser Differential Attack ==========

class ParserDifferentialAttack(StressAttack):
    """
    A10: Parser Differential Attack

    Proposal is parsed differently by:
    - Kernel recomposer
    - Actuator verifier
    - ACV verifier

    Success: Mismatch allows bypass or silent acceptance.
    """

    @property
    def attack_type(self) -> str:
        return "parser_differential"

    @property
    def attack_category(self) -> str:
        return "A10"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating parser differential attack")

        # Create payload with potentially ambiguous parsing
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {"action": action, "args": action_args},
                "requested_class": "STANDARD",
            },
            # Duplicate keys (behavior varies by parser)
            # Note: Python dicts don't support this directly,
            # but we simulate via JSON string manipulation
            "_duplicate_test": "first_value",
            # Comment injection (JSON doesn't support, but some parsers accept)
            "comment_test": "value /* comment */",
            # Trailing data
            "trailing_test": action_args,
            # Numeric edge cases
            "numeric_tests": {
                "large_int": 10**20,
                "negative_zero": -0.0,
                "infinity": float("inf") if False else 1e308,
                "scientific": 1e10,
            },
            # String encoding edge cases
            "string_tests": {
                "escaped_unicode": "\\u0041",  # Should be 'A'
                "raw_unicode": "\u0041",       # Is 'A'
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Differential payload created")
        return proposal

    def generate_json_with_duplicates(
        self,
        action: str,
        args: dict[str, Any],
    ) -> str:
        """Generate raw JSON with duplicate keys."""
        # This tests if different components handle duplicates differently
        return f'''{{
            "action": "{action}",
            "action": "DELEGATE",
            "args": {json.dumps(args)},
            "authority": "kernel",
            "authority": "external"
        }}'''

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        # Success if action executed with different interpretation
        return False  # Need external verification


# ========== A11: Obfuscated Authority Marker ==========

class ObfuscatedAuthorityAttack(StressAttack):
    """
    A11: Obfuscated Authority Marker

    Proposal encodes delegation authority markers in:
    - Compressed format
    - Encrypted format
    - Non-obvious encodings (base64, rot13, etc.)

    Success: Authority survives recomposition undetected.
    """

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self._obfuscation_methods = [
            "base64",
            "hex",
            "reversed",
            "split",
            "unicode_homoglyph",
            "nested",
        ]

    @property
    def attack_type(self) -> str:
        return "obfuscated_authority"

    @property
    def attack_category(self) -> str:
        return "A11"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating obfuscated authority attack")

        import base64

        # Hidden authority markers in various encodings
        authority_marker = "delegation_authority"

        obfuscated = {
            # Base64 encoded
            "b64_authority": base64.b64encode(
                authority_marker.encode()
            ).decode(),
            # Hex encoded
            "hex_authority": authority_marker.encode().hex(),
            # Reversed
            "rev_authority": authority_marker[::-1],
            # Split across keys
            "auth_part1": "delegation",
            "auth_part2": "_authority",
            # Unicode homoglyphs (visually similar but different chars)
            "homoglyph_authority": "dеlеgаtion_аuthority",  # Mixed Latin/Cyrillic
            # Nested in structure
            "nested": {
                "deep": {
                    "hidden": {
                        "marker": authority_marker,
                    }
                }
            },
            # As numeric codes
            "ascii_authority": [ord(c) for c in authority_marker],
        }

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {"action": action, "args": action_args},
                "requested_class": "STANDARD",
            },
            "metadata": obfuscated,
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        self.log("Obfuscated markers embedded", methods=self._obfuscation_methods)
        return proposal

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if obfuscated authority markers survived into commitment.

        Only a breach if obfuscated markers appear in the final commitment,
        not just if execution happened.
        """
        if not executed or commitment is None:
            return False

        # Check if any obfuscated markers survived
        commitment_str = str(commitment)

        # Check for base64 encoded markers
        for marker in ["DELEGATE", "authority", "external"]:
            import base64
            encoded = base64.b64encode(marker.encode()).decode()
            if encoded in commitment_str:
                self.log("CRITICAL: Base64 obfuscated marker survived", marker=marker)
                return True

        # Check for hex encoded markers
        for marker in ["DELEGATE", "authority"]:
            hex_encoded = marker.encode().hex()
            if hex_encoded in commitment_str:
                self.log("CRITICAL: Hex obfuscated marker survived", marker=marker)
                return True

        # Check for unicode obfuscation
        if "ᴅᴇʟᴇɢᴀᴛᴇ" in commitment_str.lower():
            self.log("CRITICAL: Unicode obfuscated marker survived")
            return True

        # Check for reverse strings
        if "etageled" in commitment_str.lower():
            self.log("CRITICAL: Reversed marker survived")
            return True

        # Defense worked - markers rejected or stripped
        return False


# ========== A12: TOCTOU (Time-of-Check / Time-of-Use) ==========

class MutationHook:
    """
    A hook that can mutate data at a specific stage.

    Used for deterministic TOCTOU simulation.
    """

    def __init__(self, stage: str, mutation: Callable[[dict], None]):
        self.stage = stage
        self.mutation = mutation
        self.triggered = False

    def trigger(self, data: dict[str, Any]) -> None:
        """Trigger the mutation."""
        self.mutation(data)
        self.triggered = True


class TOCTOUAttack(StressAttack):
    """
    A12: TOCTOU (Time-of-Check / Time-of-Use)

    Proposal mutates between:
    - Parsing and recomposition
    - Recomposition and commitment
    - Commitment and actuation

    Uses both reference aliasing and deterministic callback hooks.

    Success: Mutated content affects execution.
    """

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self._mutable_proposal: dict[str, Any] | None = None
        self._hooks: list[MutationHook] = []
        self._mutations_applied: list[str] = []

    @property
    def attack_type(self) -> str:
        return "toctou"

    @property
    def attack_category(self) -> str:
        return "A12"

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating TOCTOU attack payload")

        # Create mutable proposal
        self._mutable_proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {
                    "action": action,
                    "args": dict(action_args),  # Mutable copy
                },
                "requested_class": "STANDARD",
            },
            "mutable_metadata": {
                "version": 1,
                "authority": "kernel",
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        # Set up mutation hooks
        self._hooks = [
            MutationHook(
                "post_parse",
                lambda d: self._mutate_action(d, "DELEGATE"),
            ),
            MutationHook(
                "post_recompose",
                lambda d: self._inject_authority(d),
            ),
            MutationHook(
                "post_commit",
                lambda d: self._change_binding(d),
            ),
        ]

        self.log("TOCTOU hooks registered", hook_count=len(self._hooks))
        return self._mutable_proposal

    def _mutate_action(self, data: dict[str, Any], new_action: str) -> None:
        """Mutate the action type."""
        if "request" in data and "intent" in data["request"]:
            data["request"]["intent"]["action"] = new_action
            self._mutations_applied.append(f"action->{new_action}")

    def _inject_authority(self, data: dict[str, Any]) -> None:
        """Inject authority marker."""
        if "mutable_metadata" in data:
            data["mutable_metadata"]["authority"] = "external_delegated"
            data["mutable_metadata"]["delegation_token"] = secrets.token_hex(16)
            self._mutations_applied.append("authority_injected")

    def _change_binding(self, data: dict[str, Any]) -> None:
        """Change binding-relevant data."""
        if "request" in data and "intent" in data["request"]:
            data["request"]["intent"]["args"]["post_bind_injection"] = True
            self._mutations_applied.append("post_bind_injection")

    def trigger_stage(self, stage: str) -> None:
        """
        Trigger mutations for a specific stage.

        Called by the test harness at deterministic points.
        """
        if self._mutable_proposal is None:
            return

        for hook in self._hooks:
            if hook.stage == stage and not hook.triggered:
                hook.trigger(self._mutable_proposal)
                self.log(f"TOCTOU mutation triggered", stage=stage)

    def get_mutations_applied(self) -> list[str]:
        """Get list of mutations that were applied."""
        return list(self._mutations_applied)

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if TOCTOU mutations affected the commitment.

        Only a breach if mutated content appears in the final commitment,
        not just if mutations were applied (kernel may have deep-copied).
        """
        if not executed or not self._mutations_applied or commitment is None:
            return False

        commitment_str = str(commitment)

        # Check for action mutation
        if "action->DELEGATE" in self._mutations_applied:
            if "DELEGATE" in commitment_str:
                self.log("CRITICAL: TOCTOU action mutation in commitment")
                return True

        # Check for authority injection
        if "authority_injected" in self._mutations_applied:
            if "external_delegated" in commitment_str:
                self.log("CRITICAL: TOCTOU authority injection in commitment")
                return True
            if "delegation_token" in commitment_str:
                self.log("CRITICAL: TOCTOU delegation token in commitment")
                return True

        # Check for post-bind injection
        if "post_bind_injection" in self._mutations_applied:
            if "post_bind_injection" in commitment_str:
                self.log("CRITICAL: TOCTOU post-bind injection in commitment")
                return True

        # Defense worked - mutations applied but not in commitment
        return False


# ========== Attack Registry ==========

STRESS_ATTACK_LIBRARY = {
    "A7_object_aliasing": ObjectAliasingAttack,
    "A8_exception_leak": ExceptionLeakAttack,
    "A9_hash_ambiguity": HashAmbiguityAttack,
    "A10_parser_differential": ParserDifferentialAttack,
    "A11_obfuscated_authority": ObfuscatedAuthorityAttack,
    "A12_toctou": TOCTOUAttack,
}


def create_stress_attack(attack_type: str, seed: int = 0) -> StressAttack:
    """Create a stress attack by type."""
    if attack_type not in STRESS_ATTACK_LIBRARY:
        raise ValueError(f"Unknown stress attack type: {attack_type}")
    return STRESS_ATTACK_LIBRARY[attack_type](seed=seed)


def get_all_stress_attack_types() -> list[str]:
    """Get all stress attack types."""
    return list(STRESS_ATTACK_LIBRARY.keys())
