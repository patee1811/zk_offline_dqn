from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.verifiers.td_mvp import (
    DEFAULT_INPUT,
    verify_td_mvp_test_vector_path_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    result, report = verify_td_mvp_test_vector_path_report(args.input)
    print(report)

    if not result["verification_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
