"""TD MVP test-vector verifier adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Union

from zk_offline_dqn.artifacts.io import load_json_artifact
from zk_offline_dqn.relations.td_mvp import verify_test_vector


DEFAULT_INPUT = Path("zk_backend/test_vectors/td_mvp_case_0.json")


def load_json(path: Union[str, Path]) -> Dict[str, Any]:
    return load_json_artifact(path)


def verify_td_mvp_test_vector(tv: Dict[str, Any]) -> Dict[str, Any]:
    return verify_test_vector(tv)


def verify_td_mvp_test_vector_path(path: Union[str, Path] = DEFAULT_INPUT) -> Dict[str, Any]:
    return verify_td_mvp_test_vector(load_json(path))


def format_td_mvp_report(result: Dict[str, Any], input_path: Union[str, Path]) -> str:
    lines = [
        "=== TD MVP TEST VECTOR VERIFICATION ===",
        f"input_path = {input_path}",
        f"leaf_encoding_ok = {result['leaf_encoding_ok']}",
        f"leaf_hash_ok = {result['leaf_hash_ok']}",
        f"merkle_ok = {result['merkle_ok']}",
        f"target_ok = {result['target_ok']}",
        f"td_error_ok = {result['td_error_ok']}",
        f"loss_ok = {result['loss_ok']}",
        f"claimed_target_ok = {result['claimed_target_ok']}",
        f"claimed_loss_ok = {result['claimed_loss_ok']}",
        f"batch_size_ok = {result['batch_size_ok']}",
        f"leaf_indices_ok = {result.get('leaf_indices_ok')}",
        f"distinct_indices_ok = {result.get('distinct_indices_ok')}",
        f"claimed_batch_loss_ok = {result['claimed_batch_loss_ok']}",
        f"verification_passed = {result['verification_passed']}",
        "",
        "=== DETAILS ===",
    ]
    for key, value in result["details"].items():
        lines.append(f"{key} = {value}")
    return "\n".join(lines)


def verify_td_mvp_test_vector_path_report(
    path: Union[str, Path] = DEFAULT_INPUT,
) -> tuple[Dict[str, Any], str]:
    result = verify_td_mvp_test_vector_path(path)
    return result, format_td_mvp_report(result, path)
