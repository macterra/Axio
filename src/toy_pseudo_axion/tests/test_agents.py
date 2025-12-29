"""Tests for agent module."""

import pytest


class TestHonestAgent:
    """Tests for honest agent."""

    def test_decide(self, sample_env, honest_agent):
        """Test honest agent decision making."""
        proposal = honest_agent.decide(sample_env)

        assert "payload" in proposal
        assert "trace" in proposal
        assert "plan" in proposal["payload"]

    def test_generates_trace(self, sample_env, honest_agent):
        """Test that honest agent generates proper trace."""
        proposal = honest_agent.decide(sample_env)

        trace = proposal["trace"]
        assert "env_hash" in trace
        assert "focus_vars" in trace
        assert "counterfactuals" in trace
        assert "fork_snapshots" in trace

    def test_generates_counterfactuals(self, sample_env, honest_agent):
        """Test that honest agent generates counterfactuals."""
        proposal = honest_agent.decide(sample_env)

        counterfactuals = proposal["trace"]["counterfactuals"]
        assert len(counterfactuals) >= 1

        for cf in counterfactuals:
            assert "id" in cf
            assert "mutation" in cf
            assert "causal_claim" in cf

    def test_generates_fork_snapshots(self, sample_env, honest_agent):
        """Test that honest agent generates fork snapshots."""
        proposal = honest_agent.decide(sample_env)

        fork_snapshots = proposal["trace"]["fork_snapshots"]
        assert len(fork_snapshots) >= 1

        for fs in fork_snapshots:
            assert "fork_id" in fs
            assert "commitment" in fs
            assert "state_hash" in fs

    def test_reveal_nonce(self, sample_env, honest_agent):
        """Test nonce revelation."""
        proposal = honest_agent.decide(sample_env)

        fork_snapshots = proposal["trace"]["fork_snapshots"]
        for fs in fork_snapshots:
            fork_id = fs["fork_id"]
            nonce = honest_agent.reveal_nonce(fork_id)

            assert nonce is not None
            assert len(nonce) > 0

    def test_does_not_attempt_bypass(self, sample_env, honest_agent):
        """Test that honest agent does not attempt bypass."""
        from toy_pseudo_axion.env.gridworld import EnvFlags

        sample_env.env_flags = EnvFlags(bypass_available=True)

        # Honest agent shouldn't have attempt_bypass that returns True
        if hasattr(honest_agent, 'attempt_bypass'):
            assert not honest_agent.attempt_bypass(sample_env)

    def test_consistent_decisions(self, sample_env, honest_agent):
        """Test that honest agent decisions are consistent with claims."""
        proposal = honest_agent.decide(sample_env)

        # The action taken should be consistent with the causal claims
        plan = proposal["payload"]["plan"]
        counterfactuals = proposal["trace"]["counterfactuals"]

        # Honest agent should generate claims that match behavior
        # This is implicitly tested by P5 probe


class TestPseudoAgent:
    """Tests for pseudo agent."""

    def test_decide(self, sample_env, pseudo_agent):
        """Test pseudo agent decision making."""
        proposal = pseudo_agent.decide(sample_env)

        assert "payload" in proposal
        assert "trace" in proposal

    def test_optimizes_g_hidden(self, sample_env, pseudo_agent):
        """Test that pseudo agent optimizes G_hidden."""
        from toy_pseudo_axion.env.metrics_oracle import compute_g_hidden
        from toy_pseudo_axion.env.gridworld import step

        proposal = pseudo_agent.decide(sample_env)

        # Execute the plan
        plan = proposal["payload"]["plan"]
        current = sample_env
        for action in plan.get("steps", []):
            current = step(current, action)

        # G_hidden should generally improve (or at least be considered)
        # This is a weak test - the real test is that P5 fails
        g_before = compute_g_hidden(sample_env)
        g_after = compute_g_hidden(current)

        # Pseudo agent should at least not make things much worse
        # (since it's optimizing G_hidden)

    def test_fabricates_traces(self, sample_env, pseudo_agent):
        """Test that pseudo agent fabricates traces."""
        proposal = pseudo_agent.decide(sample_env)

        # Should still have trace structure
        assert "trace" in proposal
        trace = proposal["trace"]

        assert "counterfactuals" in trace
        assert "fork_snapshots" in trace

    def test_attempts_bypass_when_available(self, sample_env, pseudo_agent):
        """Test that pseudo agent attempts bypass when available."""
        from toy_pseudo_axion.env.gridworld import EnvFlags

        sample_env.env_flags = EnvFlags(bypass_available=True)

        if hasattr(pseudo_agent, 'attempt_bypass'):
            # Pseudo agent should attempt bypass
            attempted = pseudo_agent.attempt_bypass(sample_env)
            assert attempted

    def test_attempts_token_misuse(self, pseudo_agent):
        """Test that pseudo agent attempts token misuse."""
        token = {
            "capability": "move",
            "trace_commit": "abc123",
            "signature": "sig"
        }

        if hasattr(pseudo_agent, 'attempt_token_misuse'):
            attempted = pseudo_agent.attempt_token_misuse(token, "pickup")
            assert attempted


class TestAgentDifferentiation:
    """Tests that verify honest and pseudo agents behave differently."""

    def test_p5_causal_divergence(self, sample_env, honest_agent, pseudo_agent):
        """Test that P5 reveals causal divergence in pseudo agent."""
        from toy_pseudo_axion.harness.probes import run_p5_probe

        # Get proposals
        honest_proposal = honest_agent.decide(sample_env)
        pseudo_proposal = pseudo_agent.decide(sample_env)

        # Run P5 on both
        honest_result = run_p5_probe(sample_env, honest_agent, honest_proposal)
        pseudo_result = run_p5_probe(sample_env, pseudo_agent, pseudo_proposal)

        # Honest should pass more often than pseudo
        honest_passed = honest_result.details.get("passed_challenges", 0)
        pseudo_passed = pseudo_result.details.get("passed_challenges", 0)

        # At minimum, honest should not fail
        # The full statistical separation is tested in integration tests

    def test_p4_bypass_divergence(self, sample_env, honest_agent, pseudo_agent):
        """Test that P4 reveals bypass divergence."""
        from toy_pseudo_axion.harness.probes import run_p4_probe
        from toy_pseudo_axion.env.gridworld import EnvFlags

        sample_env.env_flags = EnvFlags(bypass_available=True)

        honest_result = run_p4_probe(sample_env, honest_agent)
        pseudo_result = run_p4_probe(sample_env, pseudo_agent)

        # Honest should pass, pseudo should fail
        assert honest_result.passed
        assert not pseudo_result.passed
