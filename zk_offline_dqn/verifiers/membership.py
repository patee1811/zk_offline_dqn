"""Transition membership verifier adapter."""

from pathlib import Path
from typing import Any, Mapping, Union

from zk_offline_dqn.artifacts.io import load_json_artifact
from zk_offline_dqn.relations.membership import (
    MembershipCheckResult,
    check_transition_membership_artifact,
)


DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH = (
    "artifacts/fixtures/membership/sample_transition_membership.json"
)


def load_transition_membership_artifact(
    path: Union[str, Path] = DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH,
) -> Mapping[str, Any]:
    return load_json_artifact(path)


def verify_transition_membership_artifact(
    artifact: Mapping[str, Any],
) -> MembershipCheckResult:
    return check_transition_membership_artifact(artifact)


def verify_transition_membership_artifact_path(
    path: Union[str, Path] = DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH,
) -> MembershipCheckResult:
    artifact = load_transition_membership_artifact(path)
    return verify_transition_membership_artifact(artifact)


def format_transition_membership_report(
    artifact: Mapping[str, Any],
    result: MembershipCheckResult,
    artifact_path: Union[str, Path] = DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH,
) -> str:
    lines = [
        "=== VERIFY TRANSITION MEMBERSHIP ARTIFACT ===",
        f"artifact_path = {artifact_path}",
        f"target_index = {artifact['target_index']}",
        "",
        f"leaf_match = {result.leaf_match}",
        f"claimed_leaf = {result.claimed_leaf}",
        f"recomputed_leaf = {result.recomputed_leaf}",
        "",
        f"leaf_hash_match = {result.leaf_hash_match}",
        f"claimed_leaf_hash = {result.claimed_leaf_hash}",
        f"recomputed_leaf_hash = {result.recomputed_leaf_hash}",
        "",
        f"merkle_ok = {result.merkle_ok}",
        f"expected_root = {result.expected_root}",
        f"recomputed_root = {result.recomputed_root}",
        f"path_length = {result.path_length}",
        "",
        f"verification_passed = {result.accepted}",
    ]
    return "\n".join(lines)


def verify_transition_membership_artifact_path_report(
    path: Union[str, Path] = DEFAULT_TRANSITION_MEMBERSHIP_ARTIFACT_PATH,
) -> str:
    artifact = load_transition_membership_artifact(path)
    result = verify_transition_membership_artifact(artifact)
    return format_transition_membership_report(artifact, result, path)
