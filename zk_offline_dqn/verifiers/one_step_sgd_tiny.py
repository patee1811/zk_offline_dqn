"""One-step SGD tiny test-vector verifier adapter."""

from __future__ import annotations

from typing import Any, Dict

from zk_offline_dqn.artifacts.io import load_json_artifact
from zk_offline_dqn.relations.one_step_sgd_tiny import verify_vector


DEFAULT_INPUT = "zk_backend/test_vectors/one_step_sgd_tiny_case_0.json"


def load_json(path: str) -> Dict[str, Any]:
    return load_json_artifact(path)


def verify_one_step_sgd_tiny_test_vector(vector: Dict[str, Any]) -> Dict[str, Any]:
    return verify_vector(vector)


def verify_one_step_sgd_tiny_test_vector_path(
    path: str = DEFAULT_INPUT,
) -> Dict[str, Any]:
    return verify_one_step_sgd_tiny_test_vector(load_json(path))


def format_one_step_sgd_tiny_report(
    vector: Dict[str, Any],
    result: Dict[str, Any],
    input_path: str,
) -> str:
    lines = [
        "=== VERIFY ONE STEP SGD TINY TEST VECTOR ===",
        f"input_path = {input_path}",
        f"schema_version = {vector['schema_version']}",
        f"item_index = {result['index']}",
        f"loss_fp = {result['loss_fp']}",
        f"smooth_l1_grad_fp = {result['smooth_l1_grad_fp']}",
        "verification_passed = True",
        "all_one_step_sgd_tiny_ok = True",
    ]
    return "\n".join(lines)


def verify_one_step_sgd_tiny_test_vector_path_report(
    path: str = DEFAULT_INPUT,
) -> tuple[Dict[str, Any], str]:
    vector = load_json(path)
    result = verify_one_step_sgd_tiny_test_vector(vector)
    return result, format_one_step_sgd_tiny_report(vector, result, path)
