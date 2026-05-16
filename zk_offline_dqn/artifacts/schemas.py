"""Central schema-version names for existing artifacts and test vectors."""

from __future__ import annotations

from typing import Mapping

from zk_offline_dqn.artifact_schema_versions import (
    SCHEMA_MINIBATCH_TD_V1,
    SCHEMA_ONE_STEP_UPDATE_V1,
    SCHEMA_SHORT_TRACE_UPDATE_V2,
    require_schema_version as _require_schema_version,
)


SCHEMA_TD_MVP_TEST_VECTOR_V1 = "td_mvp_test_vector_v1"
SCHEMA_TD_MVP_BATCH_TEST_VECTOR_V1 = "td_mvp_batch_test_vector_v1"
SCHEMA_FORWARD_TD_MLP_V1 = "forward_td_mlp_v1"
SCHEMA_ONE_STEP_SGD_TINY_V1 = "one_step_sgd_tiny_v1"


ARTIFACT_SCHEMA_VERSIONS = {
    "minibatch_td": SCHEMA_MINIBATCH_TD_V1,
    "one_step_update": SCHEMA_ONE_STEP_UPDATE_V1,
    "short_trace_update": SCHEMA_SHORT_TRACE_UPDATE_V2,
}

TEST_VECTOR_SCHEMA_VERSIONS = {
    "td_mvp": SCHEMA_TD_MVP_TEST_VECTOR_V1,
    "td_mvp_batch": SCHEMA_TD_MVP_BATCH_TEST_VECTOR_V1,
    "forward_td_mlp": SCHEMA_FORWARD_TD_MLP_V1,
    "one_step_sgd_tiny": SCHEMA_ONE_STEP_SGD_TINY_V1,
}


def require_schema_version(
    artifact: Mapping[str, object],
    expected: str,
    artifact_path: str = "",
) -> None:
    # Preserve the original helper's error text and accepted input shape.
    _require_schema_version(dict(artifact), expected, artifact_path=artifact_path)


def schema_version_of(artifact: Mapping[str, object]) -> object:
    return artifact.get("schema_version")
