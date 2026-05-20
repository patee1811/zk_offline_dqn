from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import verify_dataset_commitment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True)
    args = parser.parse_args()

    ok, errors = verify_dataset_commitment(Path(args.dataset_dir))
    print(f"dataset_commitment_verified = {ok}")
    if not ok:
        for error in errors:
            print(f"verification_error = {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
