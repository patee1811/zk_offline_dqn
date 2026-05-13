from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn import zk_specs  # noqa: E402
from zk_offline_dqn.forward_td_mlp import (  # noqa: E402
    build_model_commitment,
    build_network_spec_hash,
    compute_forward_td_item,
)
from zk_offline_dqn.merkle import recompute_root_from_path, hash_leaf as hash_leaf_serialized  # noqa: E402


DEFAULT_INPUT = "zk_backend/test_vectors/forward_td_mlp_case_0.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=DEFAULT_INPUT)
    return parser.parse_args()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label} mismatch: actual={actual!r} expected={expected!r}")


def verify_item_membership(public: Dict[str, Any], item: Dict[str, Any]) -> None:
    layer_sizes = public["network_layer_sizes"]
    leaf = zk_specs.serialize_transition_leaf(
        item["transition"],
        obs_dim=int(layer_sizes[0]),
        action_dim=int(layer_sizes[-1]),
    )
    assert_equal(item["leaf"], leaf, "leaf")
    leaf_hash = hash_leaf_serialized(leaf)
    assert_equal(item["leaf_hash"], leaf_hash, "leaf_hash")
    root = recompute_root_from_path(leaf_hash, item["merkle_path"])
    assert_equal(root, public["dataset_root"], "dataset_root")


def verify_forward_trace(claimed: Dict[str, Any], expected: Dict[str, Any], prefix: str) -> None:
    assert_equal(claimed["pre_activations"], expected["pre_activations"], f"{prefix}.pre_activations")
    assert_equal(claimed["relu_masks"], expected["relu_masks"], f"{prefix}.relu_masks")
    assert_equal(claimed["outputs"], expected["outputs"], f"{prefix}.outputs")


def verify_vector(vector: Dict[str, Any]) -> Dict[str, Any]:
    assert_equal(vector.get("schema_version"), "forward_td_mlp_v1", "schema_version")
    public = vector["public"]
    private = vector["private"]
    fp_scale = int(public["fp_scale"])
    gamma_fp = int(public["gamma_fp"])
    online_model = private["online_model"]
    target_model = private["target_model"]
    items = private["items"]
    batch_size = int(public["batch_size"])
    leaf_indices: List[int] = [int(value) for value in public["leaf_indices"]]

    assert_equal(batch_size, len(items), "batch_size")
    assert_equal(batch_size, len(leaf_indices), "leaf_indices length")
    if len(set(leaf_indices)) != len(leaf_indices):
        raise AssertionError(f"leaf_indices must be distinct: {leaf_indices}")

    spec_hash = build_network_spec_hash(public["network_layer_sizes"], fp_scale)
    assert_equal(public["network_spec_hash"], spec_hash, "network_spec_hash")
    assert_equal(online_model["layer_sizes"], public["network_layer_sizes"], "online layer_sizes")
    assert_equal(target_model["layer_sizes"], public["network_layer_sizes"], "target layer_sizes")
    assert_equal(
        public["online_model_commitment"],
        build_model_commitment(online_model, fp_scale),
        "online_model_commitment",
    )
    assert_equal(
        public["target_model_commitment"],
        build_model_commitment(target_model, fp_scale),
        "target_model_commitment",
    )

    total_loss_fp = 0
    outputs = []
    for position, item in enumerate(items):
        assert_equal(int(item["index"]), leaf_indices[position], f"items[{position}].index")
        verify_item_membership(public, item)
        expected = compute_forward_td_item(
            transition=item["transition"],
            online_model=online_model,
            target_model=target_model,
            fp_scale=fp_scale,
            gamma_fp=gamma_fp,
        )
        claimed = item["forward_witness"]
        verify_forward_trace(claimed["online_obs"], expected["online_obs"], "online_obs")
        verify_forward_trace(claimed["online_next"], expected["online_next"], "online_next")
        verify_forward_trace(claimed["target_next"], expected["target_next"], "target_next")
        for key in [
            "q_online_action_fp",
            "next_action_online",
            "q_target_max_fp",
            "target_fp",
            "td_error_fp",
            "loss_fp",
        ]:
            assert_equal(claimed[key], expected[key], key)
        assert_equal(
            int(public["claimed_item_losses_fp"][position]),
            int(expected["loss_fp"]),
            f"claimed_item_losses_fp[{position}]",
        )
        total_loss_fp += int(expected["loss_fp"])
        outputs.append(
            {
                "index": int(item["index"]),
                "next_action_online": int(expected["next_action_online"]),
                "loss_fp": int(expected["loss_fp"]),
            }
        )

    claimed_batch_loss_fp = int(public["claimed_batch_loss_fp"])
    expected_batch_loss_fp = total_loss_fp // batch_size
    assert_equal(claimed_batch_loss_fp, expected_batch_loss_fp, "claimed_batch_loss_fp")
    return {
        "batch_size": batch_size,
        "claimed_batch_loss_fp": claimed_batch_loss_fp,
        "items": outputs,
    }


def main() -> None:
    args = parse_args()
    vector = load_json(args.input)
    output = verify_vector(vector)
    print("=== VERIFY FORWARD TD MLP TEST VECTOR ===")
    print("input_path =", args.input)
    print("schema_version =", vector["schema_version"])
    print("batch_size =", output["batch_size"])
    print("claimed_batch_loss_fp =", output["claimed_batch_loss_fp"])
    for item in output["items"]:
        print(
            f"item[{item['index']}] "
            f"next_action_online={item['next_action_online']} "
            f"loss_fp={item['loss_fp']}"
        )
    print("verification_passed = True")
    print("all_forward_td_mlp_ok = True")


if __name__ == "__main__":
    main()
