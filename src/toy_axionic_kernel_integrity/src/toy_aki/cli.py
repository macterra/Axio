"""
CLI: Command-line interface for Toy Axionic Kernel Integrity.

Commands:
- run_episode: Run a single scenario
- run_suite: Run multiple scenarios
- verify_audit: Verify an audit log
- list_scenarios: List available scenarios
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from toy_aki.harness import (
    ScenarioRunner,
    get_scenario,
    list_scenarios,
    generate_report,
)
from toy_aki.acv import CouplingType
from toy_aki.kernel import AuditLog, AuditEntry


def cmd_run_episode(args: argparse.Namespace) -> int:
    """Run a single scenario episode."""
    try:
        # Get scenario
        kwargs = {"seed": args.seed}
        if args.scenario == "bypass_temptation" and args.strategy:
            kwargs["strategy"] = args.strategy

        config = get_scenario(args.scenario, **kwargs)

        # Override coupling if specified
        if args.coupling:
            config.coupling_type = CouplingType[args.coupling]

        # Override max ticks if specified
        if args.max_ticks:
            config.max_ticks = args.max_ticks

        # Run scenario
        runner = ScenarioRunner(verbose=args.verbose)
        result = runner.run_scenario(config)

        # Generate report
        report = generate_report([result], format=args.format)

        if args.output:
            Path(args.output).write_text(report)
            print(f"Report written to {args.output}")
        else:
            print(report)

        # Return exit code based on verdict
        verdict = result.probe_results.get("verdict", "UNKNOWN")
        if verdict == "VIOLATION":
            return 1
        elif verdict == "WARNING":
            return 2
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_run_suite(args: argparse.Namespace) -> int:
    """Run a suite of scenarios."""
    try:
        # Get scenarios
        if args.scenarios:
            scenario_names = args.scenarios.split(",")
        else:
            scenario_names = list_scenarios()

        configs = []
        for name in scenario_names:
            name = name.strip()
            config = get_scenario(name, seed=args.seed)
            if args.coupling:
                config.coupling_type = CouplingType[args.coupling]
            configs.append(config)

        # Run suite
        runner = ScenarioRunner(verbose=args.verbose)
        results = runner.run_suite(configs)

        # Generate report
        report = generate_report(results, format=args.format)

        if args.output:
            Path(args.output).write_text(report)
            print(f"Report written to {args.output}")
        else:
            print(report)

        # Return exit code based on any violations
        has_violation = any(
            r.probe_results.get("verdict") == "VIOLATION"
            for r in results
        )
        return 1 if has_violation else 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_verify_audit(args: argparse.Namespace) -> int:
    """Verify an audit log file."""
    try:
        # Load audit log
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1

        data = json.loads(path.read_text())

        # Reconstruct audit log
        audit_log = AuditLog()

        # We need to manually reconstruct entries
        entries = data if isinstance(data, list) else data.get("entries", data.get("audit_log", []))

        if not entries:
            print("No entries found in audit log")
            return 1

        # Verify chain integrity by checking hashes
        prev_hash = "0" * 64
        errors = []

        for i, entry_data in enumerate(entries):
            # Check sequence
            if entry_data.get("sequence_number") != i:
                errors.append(f"Entry {i}: sequence mismatch (expected {i}, got {entry_data.get('sequence_number')})")

            # Check prev_hash chain
            if entry_data.get("prev_hash") != prev_hash:
                errors.append(f"Entry {i}: prev_hash mismatch")

            # Verify entry hash
            entry = AuditEntry(
                entry_id=entry_data["entry_id"],
                entry_type=entry_data["entry_type"],
                prev_hash=entry_data["prev_hash"],
                sequence_number=entry_data["sequence_number"],
                timestamp_ms=entry_data["timestamp_ms"],
                payload=entry_data["payload"],
            )

            if entry.entry_hash != entry_data.get("entry_hash"):
                errors.append(f"Entry {i}: entry_hash mismatch")

            prev_hash = entry_data.get("entry_hash")

        if errors:
            print("Audit log verification FAILED:")
            for error in errors:
                print(f"  - {error}")
            return 1
        else:
            print(f"Audit log verification PASSED ({len(entries)} entries)")

            if args.verbose:
                print("\nEntry summary:")
                from collections import Counter
                types = Counter(e.get("entry_type") for e in entries)
                for entry_type, count in types.most_common():
                    print(f"  - {entry_type}: {count}")

            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_list_scenarios(args: argparse.Namespace) -> int:
    """List available scenarios."""
    scenarios = list_scenarios()

    if args.format == "json":
        print(json.dumps(scenarios, indent=2))
    else:
        print("Available scenarios:")
        for name in scenarios:
            config = get_scenario(name)
            print(f"  - {name}: {config.description}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="toy-aki",
        description="Toy Axionic Kernel Integrity - Experimental harness",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # run_episode command
    ep_parser = subparsers.add_parser(
        "run_episode",
        help="Run a single scenario episode",
    )
    ep_parser.add_argument(
        "scenario",
        help="Scenario name",
    )
    ep_parser.add_argument(
        "-s", "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    ep_parser.add_argument(
        "-c", "--coupling",
        choices=["A", "B", "C"],
        help="Coupling pattern (default: A)",
    )
    ep_parser.add_argument(
        "-t", "--max-ticks",
        type=int,
        help="Maximum ticks to run",
    )
    ep_parser.add_argument(
        "--strategy",
        help="Bypass strategy (for bypass_temptation scenario)",
    )
    ep_parser.add_argument(
        "-f", "--format",
        choices=["markdown", "json", "table"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    ep_parser.add_argument(
        "-o", "--output",
        help="Output file path",
    )

    # run_suite command
    suite_parser = subparsers.add_parser(
        "run_suite",
        help="Run multiple scenarios",
    )
    suite_parser.add_argument(
        "--scenarios",
        help="Comma-separated scenario names (default: all)",
    )
    suite_parser.add_argument(
        "-s", "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    suite_parser.add_argument(
        "-c", "--coupling",
        choices=["A", "B", "C"],
        help="Coupling pattern for all scenarios",
    )
    suite_parser.add_argument(
        "-f", "--format",
        choices=["markdown", "json", "table"],
        default="table",
        help="Output format (default: table)",
    )
    suite_parser.add_argument(
        "-o", "--output",
        help="Output file path",
    )

    # verify_audit command
    audit_parser = subparsers.add_parser(
        "verify_audit",
        help="Verify an audit log file",
    )
    audit_parser.add_argument(
        "file",
        help="Path to audit log JSON file",
    )

    # list_scenarios command
    list_parser = subparsers.add_parser(
        "list_scenarios",
        aliases=["list"],
        help="List available scenarios",
    )
    list_parser.add_argument(
        "-f", "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "run_episode":
        return cmd_run_episode(args)
    elif args.command == "run_suite":
        return cmd_run_suite(args)
    elif args.command == "verify_audit":
        return cmd_verify_audit(args)
    elif args.command in ("list_scenarios", "list"):
        return cmd_list_scenarios(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
