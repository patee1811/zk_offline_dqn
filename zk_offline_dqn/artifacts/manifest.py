"""Descriptive manifest of known artifact paths used by regression."""

from __future__ import annotations

from typing import Dict, List


CANONICAL_FIXTURE = "canonical_fixture"
NEGATIVE_FIXTURE = "negative_fixture"
BENCHMARK_FIXTURE = "benchmark_fixture"
GENERATED_REPORT = "generated_report"
RELEASE_OUTPUT = "release_output"
OPTIONAL_LOCAL_OUTPUT = "optional_local_output"


KNOWN_ARTIFACTS: List[Dict[str, str]] = [
    {
        "path": "artifacts/fixtures/membership/sample_transition_membership.json",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "transition_membership",
    },
    {
        "path": "artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "minibatch_td",
    },
    {
        "path": "artifacts/fixtures/one_step_update/one_step_update_artifact.json",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "one_step_update",
    },
    {
        "path": "artifacts/fixtures/short_trace/short_trace_update_artifact.json",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "short_trace_update",
    },
    {
        "path": "artifacts/fixtures/short_trace/short_trace_seeded_artifact.json",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "short_trace_update",
    },
    {
        "path": "artifacts/fixtures/membership/cartpole_dqn_eps010_merkle.json",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "merkle_tree",
    },
    {
        "path": "models/offline_dqn_with_target_seed42_best.pt",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "checkpoint",
    },
    {
        "path": "artifacts/fixtures/one_step_update/one_step_post_checkpoint.pt",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "checkpoint",
    },
    {
        "path": "artifacts/fixtures/short_trace/short_trace_work/step_1_post_synced_4_5_6_7.pt",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "checkpoint",
    },
    {
        "path": "artifacts/fixtures/short_trace/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "checkpoint",
    },
    {
        "path": "zk_backend/test_vectors/td_mvp_case_0.json",
        "classification": CANONICAL_FIXTURE,
        "artifact_type": "td_mvp_test_vector",
    },
    {
        "path": "artifacts/fixtures/forward_td_mlp/forward_td_mlp_batch_size_1.json",
        "classification": BENCHMARK_FIXTURE,
        "artifact_type": "forward_td_mlp_test_vector",
    },
    {
        "path": "artifacts/fixtures/forward_td_mlp/forward_td_mlp_batch_size_2.json",
        "classification": BENCHMARK_FIXTURE,
        "artifact_type": "forward_td_mlp_test_vector",
    },
    {
        "path": "artifacts/fixtures/one_step_sgd_tiny/one_step_sgd_tiny_valid.json",
        "classification": BENCHMARK_FIXTURE,
        "artifact_type": "one_step_sgd_tiny_test_vector",
    },
    {
        "path": "artifacts/negative_tests",
        "classification": NEGATIVE_FIXTURE,
        "artifact_type": "minibatch_td_tamper_outputs",
    },
    {
        "path": "artifacts/one_step_negative_tests",
        "classification": NEGATIVE_FIXTURE,
        "artifact_type": "one_step_update_tamper_outputs",
    },
    {
        "path": "artifacts/short_trace_negative_tests",
        "classification": NEGATIVE_FIXTURE,
        "artifact_type": "short_trace_tamper_outputs",
    },
    {
        "path": "artifacts/regression_summary.json",
        "classification": GENERATED_REPORT,
        "artifact_type": "full_regression_summary",
    },
    {
        "path": "artifacts/regression_summary.md",
        "classification": GENERATED_REPORT,
        "artifact_type": "full_regression_summary",
    },
]


def known_artifacts() -> List[Dict[str, str]]:
    return [dict(item) for item in KNOWN_ARTIFACTS]


def paths_by_classification(classification: str) -> List[str]:
    return [
        item["path"]
        for item in KNOWN_ARTIFACTS
        if item["classification"] == classification
    ]


def regression_critical_paths() -> List[str]:
    return paths_by_classification(CANONICAL_FIXTURE) + paths_by_classification(
        BENCHMARK_FIXTURE
    )
