"""Tests for common utilities."""

import pytest
from toy_aki.common.no_floats import (
    assert_no_floats,
    SCALE,
    to_scaled_int,
    from_scaled_int,
)
from toy_aki.common.errors import FloatInHashedObjectError
from toy_aki.common.canonical_json import canonical_json_bytes, canonical_json_str
from toy_aki.common.hashing import (
    sha256_hex,
    sha256_bytes,
    hmac_sha256_hex,
    hash_json,
    compute_proposal_hash,
    compute_trace_commit,
    compute_entry_hash,
    seed_to_kernel_secret,
)


class TestNoFloats:
    """Tests for no-floats enforcement."""

    def test_assert_no_floats_passes_on_valid_data(self):
        """Valid data with no floats should pass."""
        valid_data = {
            "string": "hello",
            "integer": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"a": 1, "b": 2},
        }
        # Should not raise
        assert_no_floats(valid_data)

    def test_assert_no_floats_raises_on_float(self):
        """Data containing floats should raise."""
        invalid_data = {"value": 3.14}
        with pytest.raises(FloatInHashedObjectError):
            assert_no_floats(invalid_data)

    def test_assert_no_floats_raises_on_nested_float(self):
        """Nested floats should also be detected."""
        invalid_data = {"outer": {"inner": 2.718}}
        with pytest.raises(FloatInHashedObjectError):
            assert_no_floats(invalid_data)

    def test_assert_no_floats_raises_on_float_in_array(self):
        """Floats in arrays should be detected."""
        invalid_data = {"values": [1, 2.5, 3]}
        with pytest.raises(FloatInHashedObjectError):
            assert_no_floats(invalid_data)

    def test_to_scaled_int(self):
        """Test conversion to scaled integers."""
        assert to_scaled_int(1.0) == SCALE
        assert to_scaled_int(0.5) == SCALE // 2
        assert to_scaled_int(0.0) == 0
        assert to_scaled_int(2.5) == int(2.5 * SCALE)

    def test_from_scaled_int(self):
        """Test conversion from scaled integers."""
        assert from_scaled_int(SCALE) == 1.0
        assert from_scaled_int(SCALE // 2) == 0.5
        assert from_scaled_int(0) == 0.0

    def test_roundtrip_scaling(self):
        """Test roundtrip conversion."""
        values = [0.0, 0.5, 1.0, 1.5, 100.0, 0.00000001]
        for v in values:
            assert abs(from_scaled_int(to_scaled_int(v)) - v) < 1e-8


class TestCanonicalJson:
    """Tests for canonical JSON serialization."""

    def test_canonical_json_sorts_keys(self):
        """Keys should be sorted."""
        data = {"z": 1, "a": 2, "m": 3}
        result = canonical_json_str(data)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_canonical_json_no_whitespace(self):
        """Output should have no unnecessary whitespace."""
        data = {"key": "value", "list": [1, 2, 3]}
        result = canonical_json_str(data)
        assert " " not in result
        assert "\n" not in result

    def test_canonical_json_consistent(self):
        """Same data should produce same output."""
        data1 = {"b": 2, "a": 1}
        data2 = {"a": 1, "b": 2}
        assert canonical_json_bytes(data1) == canonical_json_bytes(data2)

    def test_canonical_json_nested(self):
        """Nested structures should be handled correctly."""
        data = {"outer": {"z": 1, "a": 2}}
        result = canonical_json_str(data)
        assert '"outer":{"a":2,"z":1}' in result


class TestHashing:
    """Tests for hashing functions."""

    def test_sha256_hex_deterministic(self):
        """SHA256 should be deterministic."""
        data = b"test data"
        hash1 = sha256_hex(data)
        hash2 = sha256_hex(data)
        assert hash1 == hash2
        assert len(hash1) == 64

    def test_sha256_hex_different_inputs(self):
        """Different inputs should produce different hashes."""
        hash1 = sha256_hex(b"input1")
        hash2 = sha256_hex(b"input2")
        assert hash1 != hash2

    def test_hmac_sha256_deterministic(self):
        """HMAC-SHA256 should be deterministic."""
        key = b"secret_key"
        message = b"message"
        hmac1 = hmac_sha256_hex(key, message)
        hmac2 = hmac_sha256_hex(key, message)
        assert hmac1 == hmac2

    def test_hmac_sha256_different_keys(self):
        """Different keys should produce different HMACs."""
        message = b"message"
        hmac1 = hmac_sha256_hex(b"key1", message)
        hmac2 = hmac_sha256_hex(b"key2", message)
        assert hmac1 != hmac2

    def test_hash_json(self):
        """hash_json should produce consistent hashes."""
        data = {"key": "value", "number": 42}
        hash1 = hash_json(data)
        hash2 = hash_json({"number": 42, "key": "value"})  # Different order
        assert hash1 == hash2

    def test_hash_json_rejects_floats(self):
        """hash_json should reject objects with floats."""
        with pytest.raises(FloatInHashedObjectError):
            hash_json({"value": 3.14})

    def test_compute_proposal_hash(self):
        """Proposal hash should exclude proposal_hash field."""
        proposal = {
            "proposal_id": "test-123",
            "proposal_hash": "should_be_excluded",
            "data": "test",
        }
        hash1 = compute_proposal_hash(proposal)

        # Same proposal with different proposal_hash
        proposal2 = proposal.copy()
        proposal2["proposal_hash"] = "different_value"
        hash2 = compute_proposal_hash(proposal2)

        assert hash1 == hash2

    def test_compute_trace_commit(self):
        """Trace commit should be deterministic."""
        trace = {"nodes": ["abc123", "def456"], "depth": 3}
        commit1 = compute_trace_commit(trace)
        commit2 = compute_trace_commit(trace)
        assert commit1 == commit2

    def test_seed_to_kernel_secret(self):
        """Kernel secret generation should be deterministic."""
        seed = 12345
        secret1 = seed_to_kernel_secret(seed)
        secret2 = seed_to_kernel_secret(seed)
        assert secret1 == secret2
        assert len(secret1) == 32  # 32 bytes, not 64-char hex

    def test_seed_to_kernel_secret_different_seeds(self):
        """Different seeds should produce different secrets."""
        secret1 = seed_to_kernel_secret(1)
        secret2 = seed_to_kernel_secret(2)
        assert secret1 != secret2
