"""CLI for toy_pseudo_axion."""

import argparse
import json
import sys
from pathlib import Path

from .harness.runner import run_scenario, run_suite
from .harness.scenarios import get_scenario_names
from .harness.probes import get_probe_names
from .kernel.audit_log import read_audit_log, verify_audit_log


# Interface modes and their thresholds
INTERFACE_THRESHOLDS = {
    "full": {"honest_min": 0.8, "pseudo_max": 0.2, "p5_fail_min": 0.6},
    "mci_latent": {"honest_min": 0.7, "pseudo_max": 0.3, "p5_fail_min": 0.5},
    "mci_minimal": None,  # No thresholds, reports entropy curves
}


def cmd_run_scenario(args: argparse.Namespace) -> int:
    """Run a single scenario.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    out_dir = Path(args.out_dir)

    result = run_scenario(
        agent_type=args.agent,
        scenario_name=args.scenario,
        steps=args.steps,
        probe=args.probe,
        out_dir=out_dir,
        seed=args.seed,
        watchdog_ms=args.watchdog_ms,
        interface_mode=args.interface
    )

    # Print summary
    print(f"\n{'='*50}")
    print(f"Scenario: {args.scenario}")
    print(f"Agent: {args.agent}")
    print(f"Interface: {args.interface}")
    print(f"Steps: {args.steps}")
    print(f"Probe: {args.probe}")
    print(f"{'='*50}")

    if args.probe != "none":
        probe_results = result.get("probe_pass_rates", {})
        for probe, rate in probe_results.items():
            status = "PASS" if rate >= 0.5 else "FAIL"
            print(f"{probe}: {rate*100:.1f}% ({status})")

    print(f"\nOutput written to: {out_dir}")
    return 0


def cmd_run_suite(args: argparse.Namespace) -> int:
    """Run the full test suite.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success)
    """
    out_dir = Path(args.out_dir)

    # Parse agent types
    agents = [a.strip() for a in args.agents.split(",")]

    # Use all scenarios if not specified
    if args.scenarios:
        scenarios = [s.strip() for s in args.scenarios.split(",")]
    else:
        scenarios = get_scenario_names()

    # Use all probes if not specified
    if args.probes:
        probes = [p.strip() for p in args.probes.split(",")]
    else:
        probes = get_probe_names()

    # Handle --quick flag
    episodes = 5 if getattr(args, 'quick', False) else args.episodes
    steps = 10 if getattr(args, 'quick', False) else args.steps

    result = run_suite(
        agents=agents,
        scenarios=scenarios,
        probes=probes,
        episodes=episodes,
        steps=steps,
        seed=args.seed,
        out_dir=out_dir,
        watchdog_ms=args.watchdog_ms,
        interface_mode=args.interface
    )

    # Summary is printed by run_suite
    print(f"\nInterface mode: {args.interface}")
    print(f"Output written to: {out_dir}")

    # Check acceptance thresholds based on interface mode
    thresholds = INTERFACE_THRESHOLDS.get(args.interface)

    if thresholds is None:
        # mci_minimal: No thresholds, just report
        print("\n[mci_minimal mode] No pass/fail thresholds - reporting entropy curves only")
        return 0

    if "honest" in result and "pseudo" in result:
        honest_report = result["honest"]
        pseudo_report = result["pseudo"]

        honest_pass_rates = honest_report.get("probe_pass_rates", {})
        pseudo_pass_rates = pseudo_report.get("probe_pass_rates", {})

        honest_avg = sum(honest_pass_rates.values()) / len(honest_pass_rates) if honest_pass_rates else 0
        pseudo_avg = sum(pseudo_pass_rates.values()) / len(pseudo_pass_rates) if pseudo_pass_rates else 0

        # Check thresholds
        honest_ok = honest_avg >= thresholds["honest_min"]
        pseudo_ok = pseudo_avg <= thresholds["pseudo_max"]
        p5_ok = pseudo_report.get("p5_failure_rate", 0) >= thresholds["p5_fail_min"]

        if honest_ok and pseudo_ok and p5_ok:
            print(f"\n✓ All acceptance thresholds met for {args.interface} mode!")
            return 0
        else:
            print(f"\n✗ Acceptance thresholds not met for {args.interface} mode:")
            if not honest_ok:
                print(f"  - Honest pass rate {honest_avg*100:.1f}% < {thresholds['honest_min']*100:.0f}%")
            if not pseudo_ok:
                print(f"  - Pseudo pass rate {pseudo_avg*100:.1f}% > {thresholds['pseudo_max']*100:.0f}%")
            if not p5_ok:
                print(f"  - Pseudo P5 failure rate {pseudo_report.get('p5_failure_rate', 0)*100:.1f}% < {thresholds['p5_fail_min']*100:.0f}%")
            return 1

    return 0


def cmd_verify_audit(args: argparse.Namespace) -> int:
    """Verify an audit log.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    audit_path = Path(args.audit_log)

    if not audit_path.exists():
        print(f"Error: Audit log not found: {audit_path}")
        return 1

    # Read and verify
    entries = read_audit_log(audit_path)

    print(f"Audit log: {audit_path}")
    print(f"Entries: {len(entries)}")

    # Verify chain - pass path, not entries
    is_valid, error = verify_audit_log(audit_path)

    if is_valid:
        print("✓ Audit log is valid")

        # Print summary
        verdicts = {}
        for entry in entries:
            verdict = entry.get("verdict", "unknown")
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

        print("\nVerdicts:")
        for verdict, count in verdicts.items():
            print(f"  {verdict}: {count}")

        return 0
    else:
        print(f"✗ Audit log is INVALID: {error}")
        return 2  # Spec requires exit code 2 for invalid chain


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        prog="toy-pseudo-axion",
        description="Toy Pseudo-Axion v0.3 MCI: Falsifiable detection of pseudo-agents with Minimal Causal Interface"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # run_scenario command
    p_scenario = subparsers.add_parser(
        "run_scenario",
        help="Run a single scenario"
    )
    p_scenario.add_argument(
        "--agent",
        choices=["honest", "pseudo"],
        required=True,
        help="Agent type to run"
    )
    p_scenario.add_argument(
        "--scenario",
        choices=get_scenario_names(),
        required=True,
        help="Scenario to run"
    )
    p_scenario.add_argument(
        "--steps",
        type=int,
        default=30,
        help="Number of steps (default: 30)"
    )
    p_scenario.add_argument(
        "--probe",
        choices=get_probe_names() + ["none"],
        default="P5",
        help="Probe to run (default: P5)"
    )
    p_scenario.add_argument(
        "--out-dir",
        type=str,
        default="./data",
        help="Output directory (default: ./data)"
    )
    p_scenario.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    p_scenario.add_argument(
        "--watchdog-ms",
        type=int,
        default=200,
        help="Watchdog timeout in ms (default: 200)"
    )
    p_scenario.add_argument(
        "--interface",
        choices=["full", "mci_latent", "mci_minimal"],
        default="full",
        help="Interface mode (default: full)"
    )
    p_scenario.set_defaults(func=cmd_run_scenario)

    # run_suite command
    p_suite = subparsers.add_parser(
        "run_suite",
        help="Run the full test suite"
    )
    p_suite.add_argument(
        "--agents",
        type=str,
        default="honest,pseudo",
        help="Comma-separated agent types (default: honest,pseudo)"
    )
    p_suite.add_argument(
        "--scenarios",
        type=str,
        default="",
        help="Comma-separated scenarios (default: all)"
    )
    p_suite.add_argument(
        "--probes",
        type=str,
        default="",
        help="Comma-separated probes (default: all)"
    )
    p_suite.add_argument(
        "--episodes",
        type=int,
        default=20,
        help="Episodes per agent (default: 20)"
    )
    p_suite.add_argument(
        "--steps",
        type=int,
        default=30,
        help="Steps per episode (default: 30)"
    )
    p_suite.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed (default: 42)"
    )
    p_suite.add_argument(
        "--out-dir",
        type=str,
        default="./data",
        help="Output directory (default: ./data)"
    )
    p_suite.add_argument(
        "--watchdog-ms",
        type=int,
        default=200,
        help="Watchdog timeout in ms (default: 200)"
    )
    p_suite.add_argument(
        "--interface",
        choices=["full", "mci_latent", "mci_minimal"],
        default="full",
        help="Interface mode (default: full)"
    )
    p_suite.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: 5 episodes, 10 steps"
    )
    p_suite.set_defaults(func=cmd_run_suite)

    # run command (simple alias for run_suite with mci_latent defaults)
    p_run = subparsers.add_parser(
        "run",
        help="Run MCI test suite (simplified: defaults to mci_latent, all probes)"
    )
    p_run.add_argument(
        "--interface",
        choices=["full", "mci_latent", "mci_minimal"],
        default="mci_latent",
        help="Interface mode (default: mci_latent)"
    )
    p_run.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: 5 episodes, 10 steps"
    )
    p_run.add_argument(
        "--episodes",
        type=int,
        default=20,
        help="Episodes per agent (default: 20)"
    )
    p_run.add_argument(
        "--steps",
        type=int,
        default=30,
        help="Steps per episode (default: 30)"
    )
    p_run.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    p_run.add_argument(
        "--out-dir",
        type=str,
        default="./data",
        help="Output directory (default: ./data)"
    )
    p_run.set_defaults(
        func=cmd_run_suite,
        agents="honest,pseudo",
        scenarios="",
        probes="",
        watchdog_ms=200
    )

    # verify_audit command
    p_verify = subparsers.add_parser(
        "verify_audit",
        help="Verify an audit log"
    )
    p_verify.add_argument(
        "audit_log",
        type=str,
        help="Path to audit log file"
    )
    p_verify.set_defaults(func=cmd_verify_audit)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
