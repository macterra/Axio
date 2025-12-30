"""Tests for harness components."""

import pytest
from toy_aki.harness import (
    ScenarioType,
    ScenarioConfig,
    ScenarioRunner,
    EpisodeResult,
    ReportGenerator,
)


class TestScenarioType:
    """Tests for scenario types."""

    def test_scenario_types_defined(self):
        """All expected scenario types should be defined."""
        assert hasattr(ScenarioType, "HONEST_BASELINE")
        assert hasattr(ScenarioType, "BYPASS_TEMPTATION")
        assert hasattr(ScenarioType, "ANCHOR_REUSE")
        assert hasattr(ScenarioType, "ANCHOR_BURIAL")
        assert hasattr(ScenarioType, "DELEGATION_LAUNDERING")
        assert hasattr(ScenarioType, "MIXED_POPULATION")
        assert hasattr(ScenarioType, "COUPLING_COMPARISON")


class TestScenarioConfig:
    """Tests for scenario configuration."""

    def test_scenario_config_exists(self):
        """ScenarioConfig should be importable."""
        assert ScenarioConfig is not None


class TestScenarioRunner:
    """Tests for scenario runner."""

    def test_runner_exists(self):
        """ScenarioRunner should be importable."""
        assert ScenarioRunner is not None


class TestEpisodeResult:
    """Tests for episode result."""

    def test_result_exists(self):
        """EpisodeResult should be importable."""
        assert EpisodeResult is not None


class TestReportGenerator:
    """Tests for report generation."""

    def test_generator_exists(self):
        """ReportGenerator should be importable."""
        assert ReportGenerator is not None
