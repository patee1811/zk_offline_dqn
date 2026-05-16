"""Generate Phase 7 paper-facing report snapshots from existing outputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from zk_offline_dqn.experiments.report_tables import DEFAULT_OUT_DIR, generate_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Directory for generated report files.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    outputs = generate_reports(Path(args.out_dir))
    print("paper_report_generation = passed")
    print(json.dumps(outputs, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
