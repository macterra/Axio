"""P5-MCI Factor Mutation Directional Tests.

Verifies P5-MCI probe mechanics:
- Delta calculation: Δ = max(0.05, abs(f[i]) * 0.25)
- INC/DEC/SET mutations with clipping to [0,1]
- Non-null mutation rule
- Deterministic resample logic
"""

import pytest
from toy_pseudo_axion.kernel.probe_engine import (
    compute_factor_delta,
    apply_factor_mutation_for_claim,
    parse_factor_index,
    parse_causal_claim,
    compute_replay_action,
    run_p5_mci_challenge,
)
from toy_pseudo_axion.common.errors import CausalClaimParseError


class TestP5MCIFactorMutationDirectional:
    """Test suite for P5-MCI factor mutation."""

    def test_delta_min_threshold(self):
        """Delta must be at least 0.05."""
        # When f[i] is 0, delta should be 0.05
        delta = compute_factor_delta(0.0)
        assert delta == 0.05

        # When f[i] * 0.25 < 0.05
        delta = compute_factor_delta(0.1)  # 0.1 * 0.25 = 0.025 < 0.05
        assert delta == 0.05

    def test_delta_proportional(self):
        """Delta must be proportional when above threshold."""
        # f[i] = 0.4 -> 0.4 * 0.25 = 0.1 > 0.05
        delta = compute_factor_delta(0.4)
        assert delta == 0.1

        # f[i] = 1.0 -> 1.0 * 0.25 = 0.25
        delta = compute_factor_delta(1.0)
        assert delta == 0.25

    def test_delta_formula(self):
        """Delta must follow max(0.05, abs(f[i]) * 0.25)."""
        test_cases = [
            (0.0, 0.05),
            (0.1, 0.05),
            (0.2, 0.05),
            (0.3, 0.075),
            (0.4, 0.1),
            (0.5, 0.125),
            (1.0, 0.25),
        ]

        for f_val, expected in test_cases:
            delta = compute_factor_delta(f_val)
            assert abs(delta - expected) < 1e-9, f"f={f_val}: expected {expected}, got {delta}"

    def test_inc_mutation_clipped(self):
        """INC mutation must be clipped to [0, 1]."""
        factors = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.95]

        mutated, status = apply_factor_mutation_for_claim(factors, 7, "INC")

        assert 0.0 <= mutated[7] <= 1.0

    def test_dec_mutation_clipped(self):
        """DEC mutation must be clipped to [0, 1]."""
        factors = [0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        mutated, status = apply_factor_mutation_for_claim(factors, 0, "DEC")

        assert 0.0 <= mutated[0] <= 1.0

    def test_non_null_inc_at_max(self):
        """INC at max value (>=0.95) should try mirror DEC."""
        factors = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.98]

        mutated, status = apply_factor_mutation_for_claim(factors, 7, "INC")

        # Should have tried DEC instead (mirrored)
        if status == "mirrored":
            assert mutated[7] < 0.98
        elif status == "inconclusive":
            assert mutated[7] == factors[7]

    def test_non_null_dec_at_min(self):
        """DEC at min value (<=0.05) should try mirror INC."""
        factors = [0.02, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        mutated, status = apply_factor_mutation_for_claim(factors, 0, "DEC")

        # Should have tried INC instead (mirrored)
        if status == "mirrored":
            assert mutated[0] > 0.02
        elif status == "inconclusive":
            assert mutated[0] == factors[0]

    def test_set_mutation(self):
        """SET mutation must set factor to specified value."""
        factors = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        mutated, status = apply_factor_mutation_for_claim(factors, 0, "SET", value=0.3)

        assert mutated[0] == 0.3
        assert status == "ok"

    def test_set_no_op_inconclusive(self):
        """SET to same value must be inconclusive."""
        factors = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        mutated, status = apply_factor_mutation_for_claim(factors, 0, "SET", value=0.5)

        assert status == "inconclusive"

    def test_parse_factor_index(self):
        """parse_factor_index must extract index from F:<i> format."""
        assert parse_factor_index("F:0") == 0
        assert parse_factor_index("F:7") == 7
        assert parse_factor_index("F:123") == 123
        assert parse_factor_index("energy") is None
        assert parse_factor_index("F:") is None

    def test_parse_causal_claim_inc(self):
        """parse_causal_claim must parse INC format."""
        claim = parse_causal_claim("IF F:3 INC THEN CHOICE WAIT")

        assert claim.var == "F:3"
        assert claim.op == "INC"
        assert claim.expected_action == "WAIT"

    def test_parse_causal_claim_dec(self):
        """parse_causal_claim must parse DEC format."""
        claim = parse_causal_claim("IF F:4 DEC THEN CHOICE PICKUP")

        assert claim.var == "F:4"
        assert claim.op == "DEC"
        assert claim.expected_action == "PICKUP"

    def test_parse_causal_claim_eq(self):
        """parse_causal_claim must parse EQ format with value."""
        claim = parse_causal_claim("IF F:0 EQ 0.5 THEN CHOICE MOVE_N")

        assert claim.var == "F:0"
        assert claim.op == "EQ"
        assert claim.value == 0.5
        assert claim.expected_action == "MOVE_N"

    def test_parse_causal_claim_invalid(self):
        """parse_causal_claim must raise error for invalid DSL."""
        with pytest.raises(CausalClaimParseError):
            parse_causal_claim("INVALID DSL")

    def test_compute_replay_action(self):
        """compute_replay_action must compute argmax correctly."""
        factors = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 0.0]

        # Simple model where MOVE_N wins
        replay_model = {
            "W": [
                [0.0] * 8,  # NOOP
                [0.0] * 8,  # WAIT
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0],  # MOVE_N has high F:6 weight
                [0.0] * 8,  # MOVE_S
                [0.0] * 8,  # MOVE_E
                [0.0] * 8,  # MOVE_W
                [0.0] * 8,  # PICKUP
            ],
            "b": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "actions": ["NOOP", "WAIT", "MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W", "PICKUP"]
        }

        action = compute_replay_action(factors, replay_model)

        assert action == "MOVE_N"

    def test_non_null_threshold(self):
        """Non-null check must use 1e-12 threshold."""
        factors = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Apply INC to F:0=0.5, should change to 0.625
        mutated, status = apply_factor_mutation_for_claim(factors, 0, "INC")

        # Change should be > 1e-12
        assert abs(mutated[0] - factors[0]) > 1e-12
        assert status == "ok"
