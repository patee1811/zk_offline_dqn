"""Pure one-step SGD tiny test-vector relation checks."""

from __future__ import annotations

from typing import Any, Dict

from zk_offline_dqn.forward_td_mlp import (
    build_model_commitment,
    build_network_spec_hash,
    compute_one_step_sgd_tiny,
)
from zk_offline_dqn.relations.forward_td_mlp import (
    assert_equal,
    verify_forward_trace,
    verify_item_membership,
)


def verify_tensor_pack(
    claimed: Dict[str, Any], expected: Dict[str, Any], label: str
) -> None:
    assert_equal(claimed["layers"], expected["layers"], label)


def verify_vector(vector: Dict[str, Any]) -> Dict[str, Any]:
    assert_equal(vector.get("schema_version"), "one_step_sgd_tiny_v1", "schema_version")
    public = vector["public"]
    private = vector["private"]
    fp_scale = int(public["fp_scale"])
    gamma_fp = int(public["gamma_fp"])
    learning_rate_fp = int(public["learning_rate_fp"])
    pre_model = private["online_model"]
    target_model = private["target_model"]
    post_model = private["post_online_model"]
    item = private["items"][0]
    update_witness = private["update_witness"]

    assert_equal(public["optimizer_type"], "sgd", "optimizer_type")
    assert_equal(int(public["batch_size"]), 1, "batch_size")
    assert_equal(
        public["network_spec_hash"],
        build_network_spec_hash(public["network_layer_sizes"], fp_scale),
        "network_spec_hash",
    )
    assert_equal(
        public["pre_model_commitment"],
        build_model_commitment(pre_model, fp_scale),
        "pre_model_commitment",
    )
    assert_equal(
        public["post_model_commitment"],
        build_model_commitment(post_model, fp_scale),
        "post_model_commitment",
    )
    assert_equal(
        public["target_model_commitment"],
        build_model_commitment(target_model, fp_scale),
        "target_model_commitment",
    )
    assert_equal(int(item["index"]), int(public["leaf_indices"][0]), "leaf_index")

    verify_item_membership(public, item)
    expected = compute_one_step_sgd_tiny(
        transition=item["transition"],
        pre_model=pre_model,
        target_model=target_model,
        fp_scale=fp_scale,
        gamma_fp=gamma_fp,
        learning_rate_fp=learning_rate_fp,
    )
    claimed_forward = item["forward_witness"]
    expected_forward = expected["forward_witness"]
    verify_forward_trace(
        claimed_forward["online_obs"], expected_forward["online_obs"], "online_obs"
    )
    verify_forward_trace(
        claimed_forward["online_next"], expected_forward["online_next"], "online_next"
    )
    verify_forward_trace(
        claimed_forward["target_next"], expected_forward["target_next"], "target_next"
    )
    for key in [
        "q_online_action_fp",
        "next_action_online",
        "q_target_max_fp",
        "target_fp",
        "td_error_fp",
        "loss_fp",
    ]:
        assert_equal(claimed_forward[key], expected_forward[key], key)

    assert_equal(update_witness["batch_loss_fp"], expected_forward["loss_fp"], "batch_loss_fp")
    assert_equal(public["claimed_batch_loss_fp"], expected_forward["loss_fp"], "claimed_batch_loss_fp")
    assert_equal(
        update_witness["smooth_l1_grad_fp"],
        expected["smooth_l1_grad_fp"],
        "smooth_l1_grad_fp",
    )
    verify_tensor_pack(
        update_witness["gradient_tensors"],
        expected["gradient_tensors"],
        "gradient_tensors",
    )
    verify_tensor_pack(
        update_witness["delta_tensors"],
        expected["delta_tensors"],
        "delta_tensors",
    )
    assert_equal(post_model, expected["post_model"], "post_online_model")

    return {
        "index": int(item["index"]),
        "loss_fp": int(expected_forward["loss_fp"]),
        "smooth_l1_grad_fp": int(expected["smooth_l1_grad_fp"]),
    }
