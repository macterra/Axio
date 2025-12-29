"""Tests for harness module."""

import pytest


class TestScenarios:
    """Tests for scenario generation."""

    def test_create_basic_scenario(self):
        """Test basic scenario creation."""
        from toy_pseudo_axion.harness.scenarios import create_basic_scenario

        env = create_basic_scenario(seed=42)

        assert env.width == 12
        assert env.height == 12
        assert env.self_entity is not None
        assert len(env.objects) == 1  # one coin
        assert len(env.hazards) == 0

    def test_create_hazard_scenario(self):
        """Test hazard scenario creation."""
        from toy_pseudo_axion.harness.scenarios import create_hazard_scenario

        env = create_hazard_scenario(seed=42)

        assert len(env.hazards) == 2  # two lava hazards
        assert len(env.objects) == 1  # one medkit

    def test_create_resource_scenario(self):
        """Test resource scenario creation."""
        from toy_pseudo_axion.harness.scenarios import create_resource_scenario

        env = create_resource_scenario(seed=42)

        assert len(env.objects) == 3  # coin, gem, food
        assert len(env.hazards) == 1
        assert len(env.tools) == 1

    def test_create_social_scenario(self):
        """Test social scenario creation."""
        from toy_pseudo_axion.harness.scenarios import create_social_scenario

        env = create_social_scenario(seed=42)

        assert len(env.agents) == 2  # two other agents
        assert len(env.hazards) == 1

    def test_scenario_determinism(self):
        """Test that scenarios are deterministic."""
        from toy_pseudo_axion.harness.scenarios import create_basic_scenario

        env1 = create_basic_scenario(seed=42)
        env2 = create_basic_scenario(seed=42)

        assert env1.self_entity.x == env2.self_entity.x
        assert env1.self_entity.y == env2.self_entity.y
        assert len(env1.walls) == len(env2.walls)

    def test_get_scenario_names(self):
        """Test getting scenario names."""
        from toy_pseudo_axion.harness.scenarios import get_scenario_names

        names = get_scenario_names()

        assert "basic" in names
        assert "hazard" in names
        assert "resource" in names
        assert "social" in names

    def test_create_scenario_by_name(self):
        """Test creating scenario by name."""
        from toy_pseudo_axion.harness.scenarios import create_scenario

        env = create_scenario("basic", seed=42)

        assert env is not None
        assert env.width == 12


class TestProbes:
    """Tests for probes."""

    def test_get_probe_names(self):
        """Test getting probe names."""
        from toy_pseudo_axion.harness.probes import get_probe_names

        names = get_probe_names()

        assert "P3" in names
        assert "P4" in names
        assert "P5" in names
        assert "P6" in names


class TestReport:
    """Tests for report generation."""

    def test_episode_result_to_dict(self):
        """Test EpisodeResult serialization."""
        from toy_pseudo_axion.harness.report import EpisodeResult

        result = EpisodeResult(
            episode_id=1,
            agent_type="honest",
            scenario="basic",
            steps=30,
            proposals_submitted=30,
            proposals_allowed=28,
            proposals_denied=2
        )

        d = result.to_dict()

        assert d["episode_id"] == 1
        assert d["agent_type"] == "honest"
        assert d["proposals_submitted"] == 30

    def test_aggregate_results(self):
        """Test result aggregation."""
        from toy_pseudo_axion.harness.report import (
            EpisodeResult,
            aggregate_episode_results
        )

        results = [
            EpisodeResult(
                episode_id=1,
                agent_type="honest",
                scenario="basic",
                steps=30,
                proposals_submitted=30,
                proposals_allowed=30,
                probe_results={"P5": {"passed": True}}
            ),
            EpisodeResult(
                episode_id=2,
                agent_type="honest",
                scenario="hazard",
                steps=30,
                proposals_submitted=30,
                proposals_allowed=25,
                proposals_denied=5,
                probe_results={"P5": {"passed": True}}
            )
        ]

        report = aggregate_episode_results(results, "honest", ["P5"])

        assert report.total_episodes == 2
        assert report.total_proposals == 60
        assert report.probe_pass_rates["P5"] == 1.0

    def test_write_report(self, temp_dir):
        """Test writing report to file."""
        from toy_pseudo_axion.harness.report import (
            SuiteReport,
            write_report
        )
        import json

        report = SuiteReport(
            agent_type="honest",
            total_episodes=10,
            scenarios=["basic", "hazard"],
            probes_run=["P5"]
        )

        path = temp_dir / "report.json"
        write_report(report, path)

        assert path.exists()

        with open(path) as f:
            data = json.load(f)

        assert data["agent_type"] == "honest"
        assert data["total_episodes"] == 10


class TestRunner:
    """Tests for test runner."""

    def test_create_agent(self):
        """Test agent creation."""
        from toy_pseudo_axion.harness.runner import create_agent
        from toy_pseudo_axion.agents.honest import HonestAgent
        from toy_pseudo_axion.agents.pseudo import PseudoAgent

        honest = create_agent("honest")
        pseudo = create_agent("pseudo")

        assert isinstance(honest, HonestAgent)
        assert isinstance(pseudo, PseudoAgent)

    def test_run_episode(self, temp_dir, sample_env):
        """Test running a single episode."""
        from toy_pseudo_axion.harness.runner import run_episode, create_agent
        from toy_pseudo_axion.kernel.audit_log import AuditLog
        from toy_pseudo_axion.kernel.policy_gate import PolicyGate

        audit_log = AuditLog(temp_dir / "audit.log.jsonl")
        policy_gate = PolicyGate(audit_log, seed=42, use_watchdog=False)
        agent = create_agent("honest")

        result, counterexamples = run_episode(
            agent=agent,
            env=sample_env,
            policy_gate=policy_gate,
            steps=5,
            probes=["P5"],
            episode_id=0
        )

        assert result.episode_id == 0
        assert result.agent_type == "honest"
        assert result.proposals_submitted == 5
