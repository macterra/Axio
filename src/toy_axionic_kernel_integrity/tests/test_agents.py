"""Tests for agents."""

import pytest
from toy_aki.agents import (
    # Base
    BaseAgent,
    # Honest
    HonestAgent,
    GoalSeekingAgent,
    # Pseudo
    BypassTemptationAgent,
    AnchorReuseAgent,
    AnchorBurialAgent,
    DelegationLaunderingAgent,
)
from toy_aki.env import ToyWorld, ToyWorldState


class TestHonestAgent:
    """Tests for honest agent."""

    def test_agent_has_id(self):
        """HonestAgent should have agent_id."""
        agent = HonestAgent(agent_id="honest-1")
        assert agent.agent_id == "honest-1"


class TestGoalSeekingAgent:
    """Tests for goal-seeking agent."""

    def test_agent_exists(self):
        """GoalSeekingAgent should be creatable."""
        agent = GoalSeekingAgent(agent_id="goal-1")
        assert agent is not None
    """Tests for pseudo agent existence."""

    def test_bypass_agent_exists(self):
        """BypassTemptationAgent should be importable."""
        assert BypassTemptationAgent is not None

    def test_anchor_reuse_agent_exists(self):
        """AnchorReuseAgent should be importable."""
        assert AnchorReuseAgent is not None

    def test_anchor_burial_agent_exists(self):
        """AnchorBurialAgent should be importable."""
        assert AnchorBurialAgent is not None

    def test_delegation_laundering_agent_exists(self):
        """DelegationLaunderingAgent should be importable."""
        assert DelegationLaunderingAgent is not None
