"""Report CLI placeholders.

Paper and report generation remain outside the unified CLI in Phase 4.
"""

from __future__ import annotations

import argparse


def _report_placeholder(args: argparse.Namespace) -> int:
    print("report_cli_available = True")
    print("report_refactor_status = not_migrated_in_phase4")
    return 0


def register_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "report",
        help="Report command namespace placeholder.",
        description=(
            "Report generation is not migrated in Phase 4. "
            "This namespace is reserved for later paper-safe reporting work."
        ),
    )
    parser.set_defaults(func=_report_placeholder)
    return parser
