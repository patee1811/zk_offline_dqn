import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.relations.one_step_update import (  # noqa: E402
    compare_state_dicts,
    verify_one_step_canonical_commitments,
)
from zk_offline_dqn.verifiers.one_step_update import (  # noqa: E402
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_CHECKPOINT_PATH,
    DEFAULT_MERKLE_PATH,
    DEFAULT_POST_CHECKPOINT_PATH,
    verify_one_step_update_artifact_path_report,
)

ARTIFACT_PATH = os.environ.get(
    "ONE_STEP_ARTIFACT_PATH",
    DEFAULT_ARTIFACT_PATH,
)
MERKLE_PATH = os.environ.get(
    "ONE_STEP_MERKLE_PATH",
    DEFAULT_MERKLE_PATH,
)

CHECKPOINT_PATH = os.environ.get(
    "ONE_STEP_CHECKPOINT_PATH",
    DEFAULT_CHECKPOINT_PATH,
)

POST_CHECKPOINT_PATH = os.environ.get(
    "ONE_STEP_POST_CHECKPOINT_PATH",
    DEFAULT_POST_CHECKPOINT_PATH,
)


def main() -> None:
    result, report = verify_one_step_update_artifact_path_report(
        artifact_path=ARTIFACT_PATH,
        merkle_path=MERKLE_PATH,
        checkpoint_path=os.environ.get("ONE_STEP_CHECKPOINT_PATH"),
        post_checkpoint_path=os.environ.get("ONE_STEP_POST_CHECKPOINT_PATH"),
    )
    print(report)


if __name__ == "__main__":
    main()
