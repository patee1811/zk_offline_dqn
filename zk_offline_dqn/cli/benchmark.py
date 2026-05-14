"""Benchmark CLI placeholders.

Benchmark scripts remain separate in Phase 4 to avoid changing generated
outputs, benchmark numbers, or SP1 invocation behavior.
"""

from __future__ import annotations

import argparse


def _benchmark_placeholder(args: argparse.Namespace) -> int:
    print("benchmark_cli_available = True")
    print("benchmark_refactor_status = not_migrated_in_phase4")
    return 0


def register_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "benchmark",
        help="Benchmark command namespace placeholder.",
        description=(
            "Benchmark workflows remain in scripts/experiments in Phase 4. "
            "This namespace is reserved for a later behavior-preserving migration."
        ),
    )
    parser.set_defaults(func=_benchmark_placeholder)
    return parser
