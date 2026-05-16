"""Report CLI commands for generated paper-facing summaries."""

from __future__ import annotations

import argparse
from pathlib import Path


def _report_generate(args: argparse.Namespace) -> int:
    from zk_offline_dqn.experiments.report_tables import generate_reports

    outputs = generate_reports(Path(args.out_dir))
    print("report_generate = passed")
    for name, path in outputs.items():
        print(f"{name} = {path}")
    return 0


def _report_check_sources(args: argparse.Namespace) -> int:
    from zk_offline_dqn.experiments.report_tables import check_report_sources

    result = check_report_sources()
    print("report_check_sources = " + result["status"])
    for missing in result["missing_required"]:
        print(f"missing_required = {missing}")
    for missing in result["missing_optional"]:
        print(f"missing_optional = {missing}")
    for missing in result["missing_proof_required"]:
        print(f"missing_proof_required = {missing}")
    return 0 if result["status"] == "passed" else 1


def _report_help(args: argparse.Namespace) -> int:
    args.parser.print_help()
    return 0


def register_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        "report",
        help="Generate and check paper-facing report snapshots.",
        description="Generate deterministic reports from existing benchmark outputs.",
    )
    report_subparsers = parser.add_subparsers(dest="report_command")

    generate = report_subparsers.add_parser(
        "generate",
        help="Generate report snapshots under artifacts/reports/final_ndss.",
    )
    generate.add_argument(
        "--out-dir",
        default="artifacts/reports/final_ndss",
        help="Directory for generated report files.",
    )
    generate.set_defaults(func=_report_generate)

    check = report_subparsers.add_parser(
        "check-sources",
        help="Check report source availability without running benchmarks.",
    )
    check.set_defaults(func=_report_check_sources)

    parser.set_defaults(func=_report_help, parser=parser)
    return parser
