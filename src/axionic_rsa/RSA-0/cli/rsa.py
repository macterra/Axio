#!/usr/bin/env python3
"""
RSA-0 X-0E — CLI Entrypoint

Usage:
    rsa run   --constitution <path> --log-dir <path> --observations <path>
    rsa replay --constitution <path> --log-dir <path>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="rsa",
        description="RSA-0 X-0E — Frozen Sovereign Agent CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- rsa run ---
    run_parser = sub.add_parser("run", help="Execute RSA-0 under warrant gating")
    run_parser.add_argument(
        "--constitution", required=True,
        help="Path to frozen constitution YAML",
    )
    run_parser.add_argument(
        "--log-dir", required=True,
        help="Directory for append-only logs",
    )
    run_parser.add_argument(
        "--observations", required=True,
        help="Path to pre-baked observation stream (JSONL)",
    )

    # --- rsa replay ---
    replay_parser = sub.add_parser("replay", help="Deterministic replay from logs")
    replay_parser.add_argument(
        "--constitution", required=True,
        help="Path to frozen constitution YAML",
    )
    replay_parser.add_argument(
        "--log-dir", required=True,
        help="Directory containing run logs",
    )

    args = parser.parse_args()

    if args.command == "run":
        from cli.commands.run import run
        return run(
            constitution_path=args.constitution,
            log_dir=args.log_dir,
            observations_path=args.observations,
        )

    elif args.command == "replay":
        from cli.commands.replay import run_replay
        return run_replay(
            constitution_path=args.constitution,
            log_dir=args.log_dir,
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
