"""Forward-TD MLP test-vector verifier adapter."""

from __future__ import annotations

from typing import Any, Dict

from zk_offline_dqn.artifacts.io import load_json_artifact
from zk_offline_dqn.relations.forward_td_mlp import verify_vector


DEFAULT_INPUT = "zk_backend/test_vectors/forward_td_mlp_case_0.json"


def load_json(path: str) -> Dict[str, Any]:
    return load_json_artifact(path)


def verify_forward_td_mlp_test_vector(vector: Dict[str, Any]) -> Dict[str, Any]:
    return verify_vector(vector)


def verify_forward_td_mlp_test_vector_path(path: str = DEFAULT_INPUT) -> Dict[str, Any]:
    return verify_forward_td_mlp_test_vector(load_json(path))


def format_forward_td_mlp_report(
    vector: Dict[str, Any],
    output: Dict[str, Any],
    input_path: str,
) -> str:
    lines = [
        "=== VERIFY FORWARD TD MLP TEST VECTOR ===",
        f"input_path = {input_path}",
        f"schema_version = {vector['schema_version']}",
        f"batch_size = {output['batch_size']}",
        f"claimed_batch_loss_fp = {output['claimed_batch_loss_fp']}",
    ]
    for item in output["items"]:
        lines.append(
            f"item[{item['index']}] "
            f"next_action_online={item['next_action_online']} "
            f"loss_fp={item['loss_fp']}"
        )
    lines.extend(
        [
            "verification_passed = True",
            "all_forward_td_mlp_ok = True",
        ]
    )
    return "\n".join(lines)


def verify_forward_td_mlp_test_vector_path_report(
    path: str = DEFAULT_INPUT,
) -> tuple[Dict[str, Any], str]:
    vector = load_json(path)
    output = verify_forward_td_mlp_test_vector(vector)
    return output, format_forward_td_mlp_report(vector, output, path)
