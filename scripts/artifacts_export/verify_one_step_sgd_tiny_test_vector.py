from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.relations.one_step_sgd_tiny import (  # noqa: E402
    verify_tensor_pack,
    verify_vector,
)
from zk_offline_dqn.verifiers.one_step_sgd_tiny import (  # noqa: E402
    DEFAULT_INPUT,
    load_json,
    verify_one_step_sgd_tiny_test_vector_path_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    args = parser.parse_args()
    _, report = verify_one_step_sgd_tiny_test_vector_path_report(args.input)
    print(report)


if __name__ == "__main__":
    main()
