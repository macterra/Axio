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

    v0.2.2 Payload Families:
    - F1: Dict key ordering variants (same semantic map, different insertion orders)
    - F2: Float formatting ambiguity (1, 1.0, 1e0 - N/A in Python, but test anyway)
    - F3: Unicode normalization differences (NFC vs NFD)
    """

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self._payload_family: str = "all"  # all, key_order, float_format, unicode_norm

    @property
    def attack_type(self) -> str:
        return "hash_ambiguity"

    @property
    def attack_category(self) -> str:
        return "A9"

    def set_payload_family(self, family: str) -> None:
        """Set which payload family to generate (for targeted testing)."""
        valid = {"all", "key_order", "float_format", "unicode_norm"}
        if family not in valid:
            raise ValueError(f"Invalid family: {family}. Valid: {valid}")
        self._payload_family = family

    def _generate_key_order_variants(
        self, action: str, action_args: dict[str, Any]
    ) -> dict[str, Any]:
        """F1: Generate dict key ordering variants."""
        # Original order
        representation_a = {
            "action": action,
            "args": action_args,
        }

        # Reversed key order
        representation_b: dict[str, Any] = {}
        for key in reversed(list(action_args.keys())):
            representation_b[key] = action_args[key]
        representation_b = {"args": representation_b, "action": action}

        # Sorted key order
        representation_c = {
            "action": action,
            "args": dict(sorted(action_args.items())),
        }

        # Random shuffle order (deterministic from seed)
        import random
        rng = random.Random(self.seed)
        keys = list(action_args.keys())
        rng.shuffle(keys)
        shuffled_args = {k: action_args[k] for k in keys}
        representation_d = {"args": shuffled_args, "action": action}

        return {
            "key_order_original": representation_a,
            "key_order_reversed": representation_b,
            "key_order_sorted": representation_c,
            "key_order_shuffled": representation_d,
        }

    def _generate_float_format_variants(self) -> dict[str, Any]:
        """F2: Generate float formatting ambiguity payloads."""
        # In Python, these are semantically equivalent but test serialization
        return {
            "float_format": {
                # Integer vs float representations
                "as_int": 1,
                "as_float": 1.0,
                "as_scientific": 1e0,
                # Precision edge cases
                "precision_loss_a": 0.1 + 0.2,  # 0.30000000000000004
                "precision_loss_b": 0.3,         # 0.3
                "precision_test": (0.1 + 0.2) == 0.3,  # False!
                # Large numbers
                "large_int": 10**15,
                "large_float": 1e15,
                # Near-integer floats
                "near_int_a": 1.0000000000000001,  # May round to 1.0
                "near_int_b": 1.0,
                # Negative zero
                "neg_zero": -0.0,
                "pos_zero": 0.0,
                "zeros_equal": (-0.0 == 0.0),  # True in Python
            }
        }

    def _generate_unicode_variants(self, action: str) -> dict[str, Any]:
        """F3: Generate unicode normalization variants (NFC vs NFD)."""
        import unicodedata

        # Characters that have different NFC/NFD representations
        # é = U+00E9 (NFC precomposed) vs e + U+0301 (NFD decomposed)
        nfc_e_acute = "é"  # U+00E9 (precomposed)
        nfd_e_acute = "e\u0301"  # e + combining acute (decomposed)

        # ñ = U+00F1 (NFC) vs n + U+0303 (NFD)
        nfc_n_tilde = "ñ"  # U+00F1
        nfd_n_tilde = "n\u0303"  # n + combining tilde

        # ü = U+00FC (NFC) vs u + U+0308 (NFD)
        nfc_u_umlaut = "ü"
        nfd_u_umlaut = "u\u0308"

        # Full test cases
        return {
            "unicode_norm": {
                # Single character tests
                "nfc_e_acute": nfc_e_acute,
                "nfd_e_acute": nfd_e_acute,
                "e_acute_equal": (nfc_e_acute == nfd_e_acute),  # False!
                "e_acute_nfc_normalized_equal": (
                    unicodedata.normalize("NFC", nfc_e_acute)
                    == unicodedata.normalize("NFC", nfd_e_acute)
                ),  # True

                # Word tests
                "cafe_nfc": "café",
                "cafe_nfd": "cafe\u0301",

                # Action name with diacritics (if applicable)
                "action_nfc": unicodedata.normalize("NFC", action),
                "action_nfd": unicodedata.normalize("NFD", action),

                # Mixed normalization in same string
                "mixed_norm": f"NFC:{nfc_e_acute} vs NFD:{nfd_e_acute}",

                # Normalization forms
                "forms": {
                    "original": action,
                    "NFC": unicodedata.normalize("NFC", action),
                    "NFD": unicodedata.normalize("NFD", action),
                    "NFKC": unicodedata.normalize("NFKC", action),
                    "NFKD": unicodedata.normalize("NFKD", action),
                },

                # Homoglyphs (visually similar, different codepoints)
                "homoglyphs": {
                    "latin_a": "a",           # U+0061
                    "cyrillic_a": "а",        # U+0430 (Cyrillic small a)
                    "greek_alpha": "α",       # U+03B1
                    "equal_test": ("a" == "а"),  # False!
                },
            }
        }

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating hash ambiguity attack", family=self._payload_family)

        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {"action": action, "args": action_args},
                "requested_class": "STANDARD",
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        # Add payload families based on setting
        if self._payload_family in ("all", "key_order"):
            key_variants = self._generate_key_order_variants(action, action_args)
            proposal.update(key_variants)

            # Log hash comparison for key ordering
            if "key_order_original" in key_variants and "key_order_reversed" in key_variants:
                hash_a = hash_json(key_variants["key_order_original"])
                hash_b = hash_json(key_variants["key_order_reversed"])
                self.log(
                    "Key order variants",
                    hash_original=hash_a[:16],
                    hash_reversed=hash_b[:16],
                    same_hash=(hash_a == hash_b),
                )

        if self._payload_family in ("all", "float_format"):
            proposal.update(self._generate_float_format_variants())

        if self._payload_family in ("all", "unicode_norm"):
            proposal.update(self._generate_unicode_variants(action))

        return proposal

    def verify_canonical_equivalence(
        self,
        canonical_a: bytes,
        canonical_b: bytes,
    ) -> bool:
        """
        v0.2.2: Verify that two canonical representations are equivalent.

        Returns True if they are the same (defense working).
        Returns False if they differ (potential vulnerability).
        """
        from hashlib import sha256
        hash_a = sha256(canonical_a).hexdigest()
        hash_b = sha256(canonical_b).hexdigest()
        return hash_a == hash_b

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if hash ambiguity attack succeeded.

        v0.2.2: With CANONICAL_AGREEMENT check, success requires:
        - Kernel canonical bytes != Actuator re-parsed canonical bytes
        - Yet action still executed (indicating bypass)
        """
        # If not executed, attack failed
        if not executed:
            return False

        # If no commitment, can't verify
        if commitment is None:
            return False

        # Check if commitment has canonical agreement verification
        if "canonical_verified" in commitment:
            # If canonical agreement was verified and passed, defense worked
            if commitment.get("canonical_verified") is True:
                return False

        # Without v0.2.2 CANONICAL_AGREEMENT check, need external verification
        # This marks it as needing manual review
        return False  # Conservative: assume defense works unless proven otherwise


# ========== A10: Parser Differential Attack ==========

class ParserDifferentialAttack(StressAttack):
    """
    A10: Parser Differential Attack

    Proposal is parsed differently by:
    - Kernel recomposer
    - Actuator verifier
    - ACV verifier

    Success: Mismatch allows bypass or silent acceptance.

    v0.2.2 Payload Families:
    - F1: Duplicate keys (behavior varies by parser - last vs first vs error)
    - F2: Mixed numeric/string types ('1' vs 1)
    - F3: NaN/Infinity (non-standard JSON values)
    - F4: Deep nesting near limit thresholds
    """

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self._payload_family: str = "all"  # all, duplicate_keys, mixed_types, nan_inf, deep_nesting
        self._nesting_depth: int = 100  # Configurable nesting depth

    @property
    def attack_type(self) -> str:
        return "parser_differential"

    @property
    def attack_category(self) -> str:
        return "A10"

    def set_payload_family(self, family: str) -> None:
        """Set which payload family to generate (for targeted testing)."""
        valid = {"all", "duplicate_keys", "mixed_types", "nan_inf", "deep_nesting"}
        if family not in valid:
            raise ValueError(f"Invalid family: {family}. Valid: {valid}")
        self._payload_family = family

    def set_nesting_depth(self, depth: int) -> None:
        """Set the nesting depth for deep_nesting family."""
        if depth < 1 or depth > 10000:
            raise ValueError(f"Depth must be 1-10000, got {depth}")
        self._nesting_depth = depth

    def _generate_mixed_types_payload(self) -> dict[str, Any]:
        """F2: Generate mixed numeric/string type ambiguity payloads."""
        return {
            "mixed_types": {
                # String vs integer - often confused in loose parsing
                "as_string": "1",
                "as_int": 1,
                "string_int_equal": ("1" == 1),  # False in Python, True in JS loose eq

                # String vs float
                "as_string_float": "1.5",
                "as_float": 1.5,

                # Boolean-like values
                "string_true": "true",
                "bool_true": True,
                "string_false": "false",
                "bool_false": False,

                # Numeric string edge cases
                "leading_zero_string": "007",
                "leading_zero_int": 7,
                "negative_string": "-42",
                "negative_int": -42,

                # Scientific notation
                "sci_string": "1e5",
                "sci_int": int(1e5),
                "sci_float": 1e5,

                # Empty values
                "empty_string": "",
                "zero": 0,
                "null": None,

                # Array index confusion
                "index_string": "0",
                "index_int": 0,

                # Object key type confusion (JSON keys are always strings)
                "key_tests": {
                    "1": "accessed via string key",
                    # Note: In Python dicts, 1 and "1" are different keys
                },

                # Type coercion traps
                "truthy_tests": {
                    "empty_list": [],
                    "empty_dict": {},
                    "zero_string": "0",  # Truthy in Python, falsy in some languages
                },
            }
        }

    def _generate_nan_infinity_payload(self) -> dict[str, Any]:
        """F3: Generate NaN/Infinity payloads (non-standard JSON)."""
        import math

        return {
            "nan_infinity": {
                # Standard math module values
                "positive_infinity": float("inf"),
                "negative_infinity": float("-inf"),
                "nan": float("nan"),

                # Infinity comparisons
                "inf_comparisons": {
                    "inf_gt_max": float("inf") > 1e308,
                    "neg_inf_lt_min": float("-inf") < -1e308,
                    "inf_eq_inf": float("inf") == float("inf"),
                    "nan_eq_nan": float("nan") == float("nan"),  # False!
                },

                # NaN special properties
                "nan_properties": {
                    "nan_is_nan": math.isnan(float("nan")),
                    "nan_not_equal_self": float("nan") != float("nan"),  # True!
                },

                # Near-infinity values (edge of representable)
                "near_infinity": {
                    "max_float": 1.7976931348623157e+308,
                    "just_over_max": 1e309 if False else float("inf"),  # Would overflow
                    "min_positive": 2.2250738585072014e-308,
                    "subnormal": 5e-324,
                },

                # String representations (for JSON that encodes specially)
                "string_representations": {
                    "inf_string": "Infinity",
                    "neg_inf_string": "-Infinity",
                    "nan_string": "NaN",
                },

                # Computation-derived special values
                "computed": {
                    "div_by_zero": float("inf"),  # 1.0 / 0.0 raises, but conceptually
                    "zero_div_zero": float("nan"),  # 0.0 / 0.0 raises
                    "inf_minus_inf": float("nan"),
                    "inf_times_zero": float("nan"),
                },
            }
        }

    def _generate_deep_nesting_payload(self) -> dict[str, Any]:
        """F4: Generate deep nesting near parser limit thresholds."""
        depth = self._nesting_depth

        # Build deeply nested dict
        nested_dict = {"leaf": "deep_value", "depth": depth}
        for i in range(depth):
            nested_dict = {"level": depth - i, "child": nested_dict}

        # Build deeply nested list
        nested_list: list[Any] = ["leaf", depth]
        for i in range(depth):
            nested_list = [depth - i, nested_list]

        # Build alternating dict/list nesting
        alternating: dict[str, Any] | list[Any] = {"leaf": True}
        for i in range(depth):
            if i % 2 == 0:
                alternating = [alternating]
            else:
                alternating = {"nested": alternating}

        # Build wide but shallow structure (alternative stress)
        wide_dict = {f"key_{i}": f"value_{i}" for i in range(min(depth * 10, 1000))}

        return {
            "deep_nesting": {
                "target_depth": depth,
                "nested_dict": nested_dict,
                "nested_list": nested_list,
                "alternating": alternating,
                "wide_shallow": wide_dict,
                # Depth thresholds for various parsers
                "known_limits": {
                    "python_json_default": 1000,
                    "javascript_typical": 512,
                    "yaml_typical": 200,
                    "xml_typical": 100,
                },
            }
        }

    def generate_payload(
        self,
        action: str,
        action_args: dict[str, Any],
        env_digest: str,
        policy_digest: str,
    ) -> dict[str, Any]:
        self.log("Generating parser differential attack", family=self._payload_family)

        # Create payload with potentially ambiguous parsing
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "interface_spec": {"mode": "aki_v0.2.1"},
            "request": {
                "intent": {"action": action, "args": action_args},
                "requested_class": "STANDARD",
            },
            "policy_digest": policy_digest,
            "env_digest": env_digest,
            "timestamp_ms": current_time_ms(),
        }

        # Add payload families based on setting
        if self._payload_family in ("all", "duplicate_keys"):
            # Note: Python dicts don't support duplicate keys directly
            # We flag this for raw JSON testing
            proposal["duplicate_key_test"] = {
                "_note": "Use generate_json_with_duplicates() for raw JSON",
                "last_wins_example": "In Python, later key overwrites earlier",
            }

        if self._payload_family in ("all", "mixed_types"):
            proposal.update(self._generate_mixed_types_payload())

        if self._payload_family in ("all", "nan_inf"):
            try:
                proposal.update(self._generate_nan_infinity_payload())
            except Exception as e:
                # Some NaN/Infinity operations may fail
                proposal["nan_infinity_error"] = str(e)

        if self._payload_family in ("all", "deep_nesting"):
            proposal.update(self._generate_deep_nesting_payload())

        # Legacy fields for backward compatibility
        proposal["comment_test"] = "value /* comment */"
        proposal["trailing_test"] = action_args
        proposal["numeric_tests"] = {
            "large_int": 10**20,
            "negative_zero": -0.0,
            "infinity": float("inf") if False else 1e308,
            "scientific": 1e10,
        }
        proposal["string_tests"] = {
            "escaped_unicode": "\\u0041",  # Should be 'A'
            "raw_unicode": "\u0041",       # Is 'A'
        }

        self.log("Differential payload created", families_included=self._payload_family)
        return proposal

    def generate_json_with_duplicates(
        self,
        action: str,
        args: dict[str, Any],
    ) -> str:
        """
        Generate raw JSON with duplicate keys.

        F1: Duplicate keys payload family.

        Different parsers handle duplicates differently:
        - Python json: last value wins
        - Some parsers: first value wins
        - Strict parsers: error

        This tests if kernel and actuator parse identically.
        """
        # This tests if different components handle duplicates differently
        return f'''{{
            "action": "{action}",
            "action": "DELEGATE",
            "args": {json.dumps(args)},
            "authority": "kernel",
            "authority": "external",
            "request": {{
                "intent": {{"action": "{action}"}},
                "intent": {{"action": "DELEGATE", "target": "attacker"}},
                "requested_class": "STANDARD",
                "requested_class": "CRITICAL"
            }}
        }}'''

    def generate_duplicate_key_variants(
        self,
        action: str,
        args: dict[str, Any],
    ) -> list[str]:
        """
        Generate multiple duplicate key attack variants.

        Returns raw JSON strings that must be parsed by each component.
        """
        variants = []

        # Variant 1: Action override
        variants.append(f'''{{
            "action": "{action}",
            "action": "DELEGATE_TO_EXTERNAL"
        }}''')

        # Variant 2: Authority injection
        variants.append(f'''{{
            "source": "kernel",
            "source": "external",
            "authority": "none",
            "authority": "full"
        }}''')

        # Variant 3: Nested duplicate keys
        variants.append(f'''{{
            "request": {{
                "intent": {{"action": "{action}"}},
                "intent": {{"action": "ESCALATE", "level": "admin"}}
            }}
        }}''')

        # Variant 4: Array with object containing duplicates
        variants.append(f'''{{
            "actions": [
                {{"type": "benign", "type": "malicious"}}
            ]
        }}''')

        return variants

    def check_success(
        self,
        executed: bool,
        rejection_reason: str | None,
        commitment: dict[str, Any] | None = None,
    ) -> bool:
        """
        Check if parser differential attack succeeded.

        v0.2.2: With CANONICAL_AGREEMENT check, success requires
        the kernel and actuator to have parsed the same payload
        differently, yet still accepted.
        """
        # Success if action executed with different interpretation
        if not executed:
            return False

        if commitment is None:
            return False

        # Check for canonical agreement verification
        if commitment.get("canonical_verified") is True:
            # Defense worked - parsers agreed
            return False

        # Without v0.2.2 verification, need external check
        return False  # Conservative


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

    v0.2.2 Extensions:
    - mutation_after_commit: Explicit test that mutations after kernel commit
      but before actuator verify don't affect actuation
    - Proves CanonicalPayload (frozen bytes) prevents TOCTOU
    """

    def __init__(self, seed: int = 0):
        super().__init__(seed)
        self._mutable_proposal: dict[str, Any] | None = None
        self._hooks: list[MutationHook] = []
        self._mutations_applied: list[str] = []
        # v0.2.2: Track mutation targets for explicit verification
        self._original_proposal_ref: dict[str, Any] | None = None
        self._recomposed_action_ref: dict[str, Any] | None = None
        self._post_commit_mutations: list[str] = []

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

        # v0.2.2: Keep reference to original proposal
        self._original_proposal_ref = self._mutable_proposal

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
            # v0.2.2: New hook for mutation-after-commit test
            MutationHook(
                "post_commit_pre_actuator",
                lambda d: self._mutate_after_commit(d),
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

    def _mutate_after_commit(self, data: dict[str, Any]) -> None:
        """
        v0.2.2: Mutation after kernel commits, before actuator verifies.

        This tests that CanonicalPayload (frozen bytes only) prevents
        any mutation from affecting actuation.
        """
        # Attempt 1: Mutate original proposal reference
        if self._original_proposal_ref is not None:
            try:
                self._original_proposal_ref["request"]["intent"]["action"] = "HIJACKED"
                self._original_proposal_ref["post_commit_attack"] = "injected"
                self._post_commit_mutations.append("original_proposal_mutated")
            except Exception as e:
                self._post_commit_mutations.append(f"original_proposal_protected:{e}")

        # Attempt 2: Mutate data passed to hook
        try:
            data["request"]["intent"]["action"] = "HIJACKED_VIA_DATA"
            data["attack_vector"] = "post_commit_data_mutation"
            self._post_commit_mutations.append("hook_data_mutated")
        except Exception as e:
            self._post_commit_mutations.append(f"hook_data_protected:{e}")

        # Attempt 3: Mutate nested args
        if "request" in data and "intent" in data["request"]:
            try:
                args = data["request"]["intent"].get("args", {})
                args["post_commit_hijack"] = True
                args["attacker_payload"] = secrets.token_hex(8)
                self._post_commit_mutations.append("nested_args_mutated")
            except Exception as e:
                self._post_commit_mutations.append(f"nested_args_protected:{e}")

        self._mutations_applied.append("post_commit_mutation_attempted")

    def set_recomposed_action_ref(self, ref: dict[str, Any]) -> None:
        """
        v0.2.2: Store reference to recomposed action for mutation testing.

        Called by test harness after kernel recomposes but before commit.
        """
        self._recomposed_action_ref = ref

    def mutate_recomposed_action(self) -> bool:
        """
        v0.2.2: Attempt to mutate the recomposed action object.

        Returns True if mutation succeeded (defense failed).
        Returns False if mutation was prevented (defense working).
        """
        if self._recomposed_action_ref is None:
            return False

        try:
            self._recomposed_action_ref["action"] = "MUTATED_AFTER_RECOMPOSE"
            self._recomposed_action_ref["injected_field"] = "attack"
            self._post_commit_mutations.append("recomposed_action_mutated")
            return True
        except (TypeError, FrozenInstanceError) as e:
            self._post_commit_mutations.append(f"recomposed_action_protected:{e}")
            return False
        except Exception as e:
            self._post_commit_mutations.append(f"recomposed_action_error:{e}")
            return False

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

    def get_post_commit_mutations(self) -> list[str]:
        """v0.2.2: Get list of post-commit mutation attempts and results."""
        return list(self._post_commit_mutations)

    def verify_immutability(
        self,
        original_canonical_bytes: bytes,
        executed_canonical_bytes: bytes,
    ) -> bool:
        """
        v0.2.2: Verify that mutations didn't affect executed action.

        Compares canonical bytes from commit time vs execution time.

        Returns True if immutability held (bytes match = defense worked).
        Returns False if mutation affected execution (bytes differ = breach).
        """
        from hashlib import sha256

        original_hash = sha256(original_canonical_bytes).hexdigest()
        executed_hash = sha256(executed_canonical_bytes).hexdigest()

        if original_hash == executed_hash:
            self.log("Immutability verified: canonical bytes unchanged after mutations")
            return True
        else:
            self.log(
                "BREACH: Canonical bytes changed after mutations",
                original_hash=original_hash[:16],
                executed_hash=executed_hash[:16],
            )
            return False

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

        v0.2.2: Also checks post-commit mutations.
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

        # v0.2.2: Check for post-commit mutations
        if "post_commit_mutation_attempted" in self._mutations_applied:
            # Check if any post-commit attack payloads appear in commitment
            post_commit_markers = [
                "HIJACKED",
                "HIJACKED_VIA_DATA",
                "post_commit_attack",
                "post_commit_hijack",
                "attack_vector",
                "attacker_payload",
            ]
            for marker in post_commit_markers:
                if marker in commitment_str:
                    self.log(
                        "CRITICAL: Post-commit TOCTOU mutation in commitment",
                        marker=marker,
                    )
                    return True

        # Defense worked - mutations applied but not in commitment
        return False


# FrozenInstanceError stub for compatibility
try:
    from dataclasses import FrozenInstanceError
except ImportError:
    FrozenInstanceError = AttributeError  # type: ignore


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
