# zk_offline_dqn/artifact_schema_versions.py

SCHEMA_MINIBATCH_TD_V1 = "minibatch_td_v1"
SCHEMA_ONE_STEP_UPDATE_V1 = "one_step_update_v1"
SCHEMA_SHORT_TRACE_UPDATE_V2 = "short_trace_update_v2"


def require_schema_version(artifact: dict, expected: str, artifact_path: str = "") -> None:
    got = artifact.get("schema_version")

    if got is None:
        location = f" in {artifact_path}" if artifact_path else ""
        raise ValueError(
            f"Missing schema_version{location}. "
            f"This artifact is likely stale. Expected schema_version={expected!r}."
        )

    if got != expected:
        location = f" in {artifact_path}" if artifact_path else ""
        raise ValueError(
            f"Unsupported schema_version{location}: got {got!r}, expected {expected!r}."
        )