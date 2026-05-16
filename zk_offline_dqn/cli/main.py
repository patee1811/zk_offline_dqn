"""Unified command-line entrypoint for zk_offline_dqn."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from zk_offline_dqn.cli import benchmark, report, verify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zk_offline_dqn",
        description=(
            "Relation-level verification utilities for zk_offline_dqn research artifacts."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    verify.register_parser(subparsers)
    benchmark.register_parser(subparsers)
    report.register_parser(subparsers)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
