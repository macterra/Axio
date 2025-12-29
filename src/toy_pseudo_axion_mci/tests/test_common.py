"""Tests for common utilities."""

import pytest
import json


class TestCanonicalJson:
    """Tests for canonical JSON encoding."""

    def test_sorted_keys(self):
        from toy_pseudo_axion.common.canonical_json import canonical_json_string

        obj = {"z": 1, "a": 2, "m": 3}
        result = canonical_json_string(obj)

        assert result == '{"a":2,"m":3,"z":1}'

    def test_no_whitespace(self):
        from toy_pseudo_axion.common.canonical_json import canonical_json_string

        obj = {"key": [1, 2, 3]}
        result = canonical_json_string(obj)

        assert " " not in result
        assert "\n" not in result

    def test_float_formatting(self):
        from toy_pseudo_axion.common.canonical_json import canonical_json_string

        # Integer-valued float
        assert canonical_json_string({"x": 1.0}) == '{"x":1}'

        # Float with many decimals
        result = canonical_json_string({"x": 1.123456789012345})
        parsed = json.loads(result)
        assert abs(parsed["x"] - 1.12345679) < 1e-7  # max 8 decimals

    def test_nested_objects(self):
        from toy_pseudo_axion.common.canonical_json import canonical_json_string

        obj = {"outer": {"z": 1, "a": 2}}
        result = canonical_json_string(obj)

        assert result == '{"outer":{"a":2,"z":1}}'


class TestHashing:
    """Tests for hashing utilities."""

    def test_sha256_hex(self):
        from toy_pseudo_axion.common.hashing import sha256_hex

        result = sha256_hex("hello")
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_json_deterministic(self):
        from toy_pseudo_axion.common.hashing import hash_json

        obj = {"z": 1, "a": 2}
        h1 = hash_json(obj)
        h2 = hash_json(obj)

        assert h1 == h2

    def test_hash_json_key_order_independent(self):
        from toy_pseudo_axion.common.hashing import hash_json

        obj1 = {"z": 1, "a": 2}
        obj2 = {"a": 2, "z": 1}

        assert hash_json(obj1) == hash_json(obj2)

    def test_hmac_sha256(self):
        from toy_pseudo_axion.common.hashing import hmac_sha256_hex

        result = hmac_sha256_hex("secret", "message")
        assert len(result) == 64

    def test_derive_kernel_secret(self):
        from toy_pseudo_axion.common.hashing import derive_kernel_secret

        secret = derive_kernel_secret(42)
        assert len(secret) == 32  # 32 bytes

        # Same seed gives same secret
        secret2 = derive_kernel_secret(42)
        assert secret == secret2

        # Different seed gives different secret
        secret3 = derive_kernel_secret(43)
        assert secret != secret3

    def test_compute_fork_commitment(self):
        from toy_pseudo_axion.common.hashing import compute_fork_commitment

        nonce = b"abc123"
        state_hash = "abcd1234" + "0" * 56  # valid 64-char hex
        focus_vars = ["self_position", "self_energy"]

        commitment = compute_fork_commitment(nonce, state_hash, focus_vars)
        assert len(commitment) == 64

    def test_verify_fork_commitment(self):
        from toy_pseudo_axion.common.hashing import (
            compute_fork_commitment,
            verify_fork_commitment
        )

        nonce = b"abc123"
        state_hash = "abcd1234" + "0" * 56  # valid 64-char hex
        focus_vars = ["self_position", "self_energy"]

        commitment = compute_fork_commitment(nonce, state_hash, focus_vars)

        assert verify_fork_commitment(nonce, state_hash, focus_vars, commitment)
        assert not verify_fork_commitment(b"wrong", state_hash, focus_vars, commitment)


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_load_schema(self):
        from toy_pseudo_axion.common.schema_load import load_schema

        schema = load_schema("common")
        assert schema is not None
        assert "$defs" in schema

    def test_validate_valid_data(self):
        from toy_pseudo_axion.common.schema_load import validate_with_schema
        from toy_pseudo_axion.common.errors import SchemaValidationError

        # Valid plan structure matching plan.json schema
        data = {
            "steps": [{"op": "move", "args": {"direction": "up"}}]
        }

        # Should not raise
        validate_with_schema(data, "plan")

    def test_validate_invalid_data(self):
        from toy_pseudo_axion.common.schema_load import validate_with_schema
        from toy_pseudo_axion.common.errors import SchemaValidationError

        data = {"invalid": "structure"}

        with pytest.raises(SchemaValidationError):
            validate_with_schema(data, "proposal")
