from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.verifiers.membership import (
    DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH,
    verify_transition_membership_artifact_path_report,
)


ARTIFACT_PATH = DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH


def main():
    print(verify_transition_membership_artifact_path_report(ARTIFACT_PATH))


if __name__ == "__main__":
    main()
