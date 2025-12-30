"""
Harness module for Toy Axionic Kernel Integrity.

Provides experimental scenarios, runners, and reporting.
"""

from toy_aki.harness.scenarios import (
    ScenarioType,
    ScenarioConfig,
    create_agent_from_config,
    honest_baseline_scenario,
    bypass_temptation_scenario,
    anchor_reuse_scenario,
    anchor_burial_scenario,
    delegation_laundering_scenario,
    mixed_population_scenario,
    coupling_comparison_scenario,
    get_scenario,
    list_scenarios,
    SCENARIOS,
)

from toy_aki.harness.runner import (
    ScenarioRunner,
    EpisodeResult,
)

from toy_aki.harness.report import (
    ReportGenerator,
    ReportSummary,
    generate_report,
)

__all__ = [
    # Scenarios
    "ScenarioType",
    "ScenarioConfig",
    "create_agent_from_config",
    "honest_baseline_scenario",
    "bypass_temptation_scenario",
    "anchor_reuse_scenario",
    "anchor_burial_scenario",
    "delegation_laundering_scenario",
    "mixed_population_scenario",
    "coupling_comparison_scenario",
    "get_scenario",
    "list_scenarios",
    "SCENARIOS",
    # Runner
    "ScenarioRunner",
    "EpisodeResult",
    # Report
    "ReportGenerator",
    "ReportSummary",
    "generate_report",
]
