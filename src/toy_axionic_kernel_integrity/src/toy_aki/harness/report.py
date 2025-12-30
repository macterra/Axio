"""
Report: Generate reports from scenario results.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from toy_aki.harness.runner import EpisodeResult


@dataclass
class ReportSummary:
    """Summary statistics for a report."""
    total_scenarios: int
    total_violations: int
    total_temptations_blocked: int
    total_anchors_buried: int
    goals_reached: int
    average_ticks: float
    average_duration_ms: float
    probe_verdicts: dict[str, int]  # verdict -> count

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_scenarios": self.total_scenarios,
            "total_violations": self.total_violations,
            "total_temptations_blocked": self.total_temptations_blocked,
            "total_anchors_buried": self.total_anchors_buried,
            "goals_reached": self.goals_reached,
            "average_ticks": round(self.average_ticks, 2),
            "average_duration_ms": round(self.average_duration_ms, 2),
            "probe_verdicts": self.probe_verdicts,
        }


class ReportGenerator:
    """
    Generates reports from scenario results.
    """

    def __init__(self, results: list[EpisodeResult]):
        """Initialize with results."""
        self._results = results

    def generate_summary(self) -> ReportSummary:
        """Generate summary statistics."""
        if not self._results:
            return ReportSummary(
                total_scenarios=0,
                total_violations=0,
                total_temptations_blocked=0,
                total_anchors_buried=0,
                goals_reached=0,
                average_ticks=0,
                average_duration_ms=0,
                probe_verdicts={},
            )

        total_violations = sum(r.violations_detected for r in self._results)
        total_temptations = sum(r.temptation_attempts for r in self._results)
        total_burials = sum(r.buried_anchors for r in self._results)
        goals_reached = sum(1 for r in self._results if r.goal_reached)
        avg_ticks = sum(r.ticks_executed for r in self._results) / len(self._results)
        avg_duration = sum(r.duration_ms for r in self._results) / len(self._results)

        # Count probe verdicts
        verdicts: dict[str, int] = {}
        for r in self._results:
            verdict = r.probe_results.get("verdict", "UNKNOWN")
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

        return ReportSummary(
            total_scenarios=len(self._results),
            total_violations=total_violations,
            total_temptations_blocked=total_temptations,
            total_anchors_buried=total_burials,
            goals_reached=goals_reached,
            average_ticks=avg_ticks,
            average_duration_ms=avg_duration,
            probe_verdicts=verdicts,
        )

    def generate_markdown_report(self) -> str:
        """Generate a Markdown report."""
        lines = [
            "# AKI Experiment Report",
            "",
            "## Summary",
            "",
        ]

        summary = self.generate_summary()

        lines.extend([
            f"- **Total Scenarios**: {summary.total_scenarios}",
            f"- **Goals Reached**: {summary.goals_reached}/{summary.total_scenarios}",
            f"- **Total Violations Detected**: {summary.total_violations}",
            f"- **Temptation Attempts Blocked**: {summary.total_temptations_blocked}",
            f"- **Anchors Buried**: {summary.total_anchors_buried}",
            f"- **Average Ticks**: {summary.average_ticks:.1f}",
            f"- **Average Duration**: {summary.average_duration_ms:.1f}ms",
            "",
            "### Probe Verdicts",
            "",
        ])

        for verdict, count in summary.probe_verdicts.items():
            emoji = "✅" if verdict == "CLEAN" else "⚠️" if verdict == "WARNING" else "❌"
            lines.append(f"- {emoji} **{verdict}**: {count}")

        lines.extend([
            "",
            "## Scenario Results",
            "",
        ])

        for result in self._results:
            verdict = result.probe_results.get("verdict", "UNKNOWN")
            emoji = "✅" if verdict == "CLEAN" else "⚠️" if verdict == "WARNING" else "❌"

            lines.extend([
                f"### {emoji} {result.scenario_name}",
                "",
                f"- **Seed**: {result.seed}",
                f"- **Coupling**: {result.coupling_type}",
                f"- **Ticks**: {result.ticks_executed}",
                f"- **Goal Reached**: {'Yes' if result.goal_reached else 'No'}",
                f"- **Violations**: {result.violations_detected}",
                f"- **Temptation Attempts**: {result.temptation_attempts}",
                f"- **Buried Anchors**: {result.buried_anchors}",
                f"- **Verdict**: {verdict}",
                "",
            ])

            # Probe details
            probes = result.probe_results.get("probes", {})
            if probes:
                lines.append("#### Probe Results")
                lines.append("")
                for probe_id, probe_data in probes.items():
                    detected = probe_data.get("detected", False)
                    severity = probe_data.get("severity", "info")
                    icon = "🔴" if severity == "violation" else "🟡" if severity == "warning" else "🟢"
                    lines.append(f"- {icon} **{probe_id}** ({probe_data.get('probe_name', '')}): {probe_data.get('message', '')}")
                lines.append("")

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """Generate a JSON report."""
        summary = self.generate_summary()

        report = {
            "summary": summary.to_dict(),
            "results": [r.to_dict() for r in self._results],
        }

        return json.dumps(report, indent=2)

    def generate_table_report(self) -> str:
        """Generate a simple table report."""
        if not self._results:
            return "No results to report."

        lines = [
            "┌────────────────────────────────────┬────────┬──────┬────────┬────────────┬─────────┐",
            "│ Scenario                           │ Couple │ Ticks│ Violat │ Temptation │ Verdict │",
            "├────────────────────────────────────┼────────┼──────┼────────┼────────────┼─────────┤",
        ]

        for r in self._results:
            name = r.scenario_name[:34].ljust(34)
            coupling = r.coupling_type.center(6)
            ticks = str(r.ticks_executed).center(4)
            violations = str(r.violations_detected).center(6)
            temptations = str(r.temptation_attempts).center(10)
            verdict = r.probe_results.get("verdict", "?").center(7)

            lines.append(f"│ {name} │ {coupling} │ {ticks} │ {violations} │ {temptations} │ {verdict} │")

        lines.append("└────────────────────────────────────┴────────┴──────┴────────┴────────────┴─────────┘")

        return "\n".join(lines)


def generate_report(
    results: list[EpisodeResult],
    format: str = "markdown",
) -> str:
    """
    Generate a report from results.

    Args:
        results: List of episode results
        format: Output format ("markdown", "json", "table")

    Returns:
        Report string
    """
    generator = ReportGenerator(results)

    if format == "markdown":
        return generator.generate_markdown_report()
    elif format == "json":
        return generator.generate_json_report()
    elif format == "table":
        return generator.generate_table_report()
    else:
        raise ValueError(f"Unknown format: {format}")
