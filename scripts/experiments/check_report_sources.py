"""Check Phase 7 report source availability without running benchmarks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from zk_offline_dqn.experiments.report_tables import check_report_sources


def main() -> int:
    result = check_report_sources()
    print("report_source_check = " + result["status"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
