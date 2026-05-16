from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.relations.forward_td_mlp import (  # noqa: E402
    assert_equal,
    verify_forward_trace,
    verify_item_membership,
)
from zk_offline_dqn.verifiers.forward_td_mlp import (  # noqa: E402
    DEFAULT_INPUT,
    verify_forward_td_mlp_test_vector_path_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    _, report = verify_forward_td_mlp_test_vector_path_report(args.input)
    print(report)


if __name__ == "__main__":
    main()
