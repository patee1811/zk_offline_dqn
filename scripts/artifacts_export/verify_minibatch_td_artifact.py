import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.relations.minibatch_td import (  # noqa: E402
    verify_merkle_path_metadata,
)
from zk_offline_dqn.verifiers.minibatch_td import (  # noqa: E402
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_CHECKPOINT_PATH,
    verify_canonical_state_commitments,
    verify_minibatch_td_artifact_path_report,
)

ARTIFACT_PATH = os.environ.get(
    "MINIBATCH_TD_ARTIFACT_PATH",
    DEFAULT_ARTIFACT_PATH,
)

CHECKPOINT_PATH = os.environ.get(
    "MINIBATCH_TD_CHECKPOINT_PATH",
    DEFAULT_CHECKPOINT_PATH,
)


def main():
    _, report = verify_minibatch_td_artifact_path_report(
        artifact_path=ARTIFACT_PATH,
        checkpoint_path=CHECKPOINT_PATH,
    )
    print(report)


if __name__ == "__main__":
    main()
