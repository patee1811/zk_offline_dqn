import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.relations.short_trace import (  # noqa: E402
    DEFAULT_SAMPLING_RULE,
    deserialize_state_dict,
    deserialize_tensor,
    step_checkpoint_paths,
    validate_short_trace_schema,
    verify_short_trace_canonical_boundary_commitments,
)
from zk_offline_dqn.verifiers.short_trace import (  # noqa: E402
    DEFAULT_ARTIFACT_PATH,
    load_checkpoint,
    load_json,
    resolve_short_trace_paths,
    verify_embedded_one_step_artifact,
    verify_short_trace_artifact_path_report,
)


ARTIFACT_PATH = os.environ.get(
    "SHORT_TRACE_ARTIFACT_PATH",
    DEFAULT_ARTIFACT_PATH,
)


def main() -> None:
    result, report = verify_short_trace_artifact_path_report(
        artifact_path=ARTIFACT_PATH,
        merkle_path=os.environ.get("SHORT_TRACE_MERKLE_PATH"),
        initial_checkpoint_path=os.environ.get("SHORT_TRACE_INITIAL_CHECKPOINT_PATH"),
        final_checkpoint_path=os.environ.get("SHORT_TRACE_FINAL_CHECKPOINT_PATH"),
        work_dir=os.environ.get("SHORT_TRACE_WORK_DIR"),
    )
    print(report)


if __name__ == "__main__":
    main()
