"""Reference checker for the integrated one-step training update relation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Tuple


SCHEMA_VERSION = "sp1_training_update_case_v1"


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    reason: str
    public_output: Dict[str, Any] | None = None


def div_trunc_zero(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    return sign * (abs(numerator) // denominator)


def fixed_point_mul(a_fp: int, b_fp: int, fp_scale: int) -> int:
    return div_trunc_zero(a_fp * b_fp, fp_scale)


def smooth_l1_loss_fp(td_error_fp: int, fp_scale: int) -> int:
    abs_x_fp = abs(td_error_fp)
    if abs_x_fp < fp_scale:
        return div_trunc_zero(abs_x_fp * abs_x_fp, 2 * fp_scale)
    return abs_x_fp - fp_scale // 2


def smooth_l1_grad_fp(td_error_fp: int, fp_scale: int) -> int:
    abs_x_fp = abs(td_error_fp)
    if abs_x_fp < fp_scale:
        return td_error_fp
    return fp_scale if td_error_fp > 0 else -fp_scale


def sha256_json(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def model_commitment(model: Mapping[str, Any], fp_scale: int) -> str:
    return sha256_json(
        {
            "format": "quantized_mlp_v1",
            "fp_scale": fp_scale,
            "layer_sizes": model["layer_sizes"],
            "layers": model["layers"],
        }
    )


def gradient_commitment(gradients: Mapping[str, Any]) -> str:
    return sha256_json(
        {
            "format": "training_update_gradients_v1",
            "layers": gradients["layers"],
        }
    )


def update_commitment(
    checkpoint_hash_t: str,
    checkpoint_hash_t_plus_1: str,
    gradient_hash: str,
    learning_rate: int,
) -> str:
    return sha256_json(
        {
            "checkpoint_hash_t": checkpoint_hash_t,
            "checkpoint_hash_t_plus_1": checkpoint_hash_t_plus_1,
            "format": "training_update_update_v1",
            "gradient_hash": gradient_hash,
            "learning_rate": learning_rate,
        }
    )


def hash_leaf(leaf: List[int]) -> str:
    return hashlib.sha256(",".join(str(int(v)) for v in leaf).encode("utf-8")).hexdigest()


def hash_internal_node(left_hex: str, right_hex: str) -> str:
    left = bytes.fromhex(left_hex)
    right = bytes.fromhex(right_hex)
    if len(left) != 32 or len(right) != 32:
        raise AssertionError("Merkle node hashes must be 32 bytes")
    return hashlib.sha256(left + right).hexdigest()


def recompute_root_from_path(leaf_hash: str, merkle_path: List[Mapping[str, Any]]) -> str:
    current = leaf_hash
    expected_current = None
    for step in merkle_path:
        if expected_current is None:
            expected_current = int(step["current_index"])
        if bool(step["current_is_left"]):
            current = hash_internal_node(current, str(step["sibling_hash"]))
        else:
            current = hash_internal_node(str(step["sibling_hash"]), current)
    return current


def assert_path_metadata(merkle_path: List[Mapping[str, Any]], leaf_index: int) -> None:
    if not merkle_path:
        if leaf_index != 0:
            raise AssertionError("single-leaf Merkle path requires leaf_index 0")
        return
    expected_current = leaf_index
    for expected_level, step in enumerate(merkle_path):
        if int(step["level"]) != expected_level:
            raise AssertionError("Merkle path level metadata mismatch")
        if int(step["current_index"]) != expected_current:
            raise AssertionError("Merkle path current_index metadata mismatch")
        if bool(step["current_is_left"]):
            if expected_current % 2 != 0:
                raise AssertionError("left Merkle path step has odd index")
        elif expected_current % 2 != 1:
            raise AssertionError("right Merkle path step has even index")
        expected_current //= 2


def serialize_transition_leaf(
    transition: Mapping[str, Any], *, obs_dim: int, action_dim: int
) -> List[int]:
    state = [int(v) for v in transition["state"]]
    next_state = [int(v) for v in transition["next_state"]]
    action = int(transition["action"])
    if len(state) != obs_dim or len(next_state) != obs_dim:
        raise AssertionError("transition dimension mismatch")
    if action < 0 or action >= action_dim:
        raise AssertionError("action out of range")
    done = 1 if bool(transition["terminated"]) or bool(transition["truncated"]) else 0
    return state + [action, int(transition["reward"])] + next_state + [done]


def argmax_first(values: List[int]) -> int:
    best_idx = 0
    best_value = values[0]
    for idx, value in enumerate(values[1:], start=1):
        if value > best_value:
            best_idx = idx
            best_value = value
    return best_idx


def mlp_forward(model: Mapping[str, Any], input_fp: List[int], fp_scale: int) -> Dict[str, Any]:
    if len(model["layer_sizes"]) != 3:
        raise AssertionError("expected one hidden layer")
    if len(input_fp) != int(model["layer_sizes"][0]):
        raise AssertionError("input dimension mismatch")
    hidden_layer = model["layers"][0]
    output_layer = model["layers"][1]
    z1 = []
    for row, bias in zip(hidden_layer["weight"], hidden_layer["bias"]):
        acc = int(bias)
        for w_fp, x_fp in zip(row, input_fp):
            acc += fixed_point_mul(int(w_fp), int(x_fp), fp_scale)
        z1.append(acc)
    h1 = [value if value > 0 else 0 for value in z1]
    q = []
    for row, bias in zip(output_layer["weight"], output_layer["bias"]):
        acc = int(bias)
        for w_fp, h_fp in zip(row, h1):
            acc += fixed_point_mul(int(w_fp), int(h_fp), fp_scale)
        q.append(acc)
    return {"z1": z1, "h1": h1, "q": q}


def zero_update_tensors(layer_sizes: List[int]) -> Dict[str, Any]:
    return {
        "layers": [
            {
                "weight": [[0 for _ in range(in_dim)] for _ in range(out_dim)],
                "bias": [0 for _ in range(out_dim)],
            }
            for in_dim, out_dim in zip(layer_sizes[:-1], layer_sizes[1:])
        ]
    }


def apply_sgd_update(
    model: Mapping[str, Any], gradients: Mapping[str, Any], learning_rate: int, fp_scale: int
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    post = {
        "format": model["format"],
        "layer_sizes": list(model["layer_sizes"]),
        "fp_scale": int(model["fp_scale"]),
        "layers": [],
    }
    deltas = zero_update_tensors(list(model["layer_sizes"]))
    for layer_idx, layer in enumerate(model["layers"]):
        grad_layer = gradients["layers"][layer_idx]
        post_weight = []
        for row_idx, row in enumerate(layer["weight"]):
            post_row = []
            for col_idx, value in enumerate(row):
                delta = -fixed_point_mul(learning_rate, int(grad_layer["weight"][row_idx][col_idx]), fp_scale)
                deltas["layers"][layer_idx]["weight"][row_idx][col_idx] = delta
                post_row.append(int(value) + delta)
            post_weight.append(post_row)
        post_bias = []
        for bias_idx, value in enumerate(layer["bias"]):
            delta = -fixed_point_mul(learning_rate, int(grad_layer["bias"][bias_idx]), fp_scale)
            deltas["layers"][layer_idx]["bias"][bias_idx] = delta
            post_bias.append(int(value) + delta)
        post["layers"].append({"weight": post_weight, "bias": post_bias})
    return post, deltas


def compute_training_update(vector: Mapping[str, Any]) -> Dict[str, Any]:
    public = vector["public_inputs"]
    witness = vector["private_witness"]
    scale = int(public["fixed_point_scale"])
    online = witness["online_model_t"]
    target = witness["target_model"]
    transition = witness["transition"]

    online_forward = mlp_forward(online, [int(v) for v in transition["state"]], scale)
    online_next = mlp_forward(online, [int(v) for v in transition["next_state"]], scale)
    target_forward = mlp_forward(target, [int(v) for v in transition["next_state"]], scale)
    action = int(transition["action"])
    q_online_action = online_forward["q"][action]
    next_action = argmax_first(online_next["q"])
    q_target_next = target_forward["q"][next_action]
    done = bool(transition["terminated"]) or bool(transition["truncated"])
    td_target = int(transition["reward"]) if done else int(transition["reward"]) + fixed_point_mul(int(public["gamma"]), q_target_next, scale)
    td_error = q_online_action - td_target
    loss = smooth_l1_loss_fp(td_error, scale)
    loss_grad = smooth_l1_grad_fp(td_error, scale)

    gradients = zero_update_tensors(list(online["layer_sizes"]))
    gradients["layers"][1]["bias"][action] = loss_grad
    for hidden_idx, hidden_fp in enumerate(online_forward["h1"]):
        gradients["layers"][1]["weight"][action][hidden_idx] = fixed_point_mul(loss_grad, hidden_fp, scale)
    output_action_weights = online["layers"][1]["weight"][action]
    for hidden_idx, z_fp in enumerate(online_forward["z1"]):
        grad_hidden = fixed_point_mul(loss_grad, int(output_action_weights[hidden_idx]), scale)
        grad_z = grad_hidden if z_fp > 0 else 0
        gradients["layers"][0]["bias"][hidden_idx] = grad_z
        for input_idx, input_fp in enumerate(transition["state"]):
            gradients["layers"][0]["weight"][hidden_idx][input_idx] = fixed_point_mul(grad_z, int(input_fp), scale)
    post, deltas = apply_sgd_update(online, gradients, int(public["learning_rate"]), scale)
    gradient_hash = gradient_commitment(gradients)
    post_hash = model_commitment(post, scale)
    update_hash = update_commitment(str(public["checkpoint_hash_t"]), post_hash, gradient_hash, int(public["learning_rate"]))
    return {
        "online_forward": online_forward,
        "online_next": online_next,
        "target_forward": target_forward,
        "q_online_action": q_online_action,
        "q_target_next": q_target_next,
        "td_target": td_target,
        "td_error": td_error,
        "loss": loss,
        "gradients": gradients,
        "deltas": deltas,
        "post_model": post,
        "gradient_hash": gradient_hash,
        "checkpoint_hash_t_plus_1": post_hash,
        "update_hash": update_hash,
    }


def verify_vector(vector: Mapping[str, Any]) -> Dict[str, Any]:
    if vector.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError("schema_version mismatch")
    public = vector["public_inputs"]
    witness = vector["private_witness"]
    if public["relation"] != "training_update":
        raise AssertionError("relation mismatch")
    if public["batch_size"] != 1:
        raise AssertionError("batch_size mismatch")
    if public["dataset_type"] != "self_collected_replay_audited":
        raise AssertionError("dataset_type mismatch")
    if witness["provenance"] != {
        "dataset_id_hash": public["dataset_id_hash"],
        "dataset_type": public["dataset_type"],
        "manifest_hash": public["manifest_hash"],
        "audit_report_hash": public["audit_report_hash"],
        "collection_log_final_hash": public["collection_log_final_hash"],
        "raw_trajectory_hash": public["raw_trajectory_hash"],
    }:
        raise AssertionError("provenance witness mismatch")

    scale = int(public["fixed_point_scale"])
    online = witness["online_model_t"]
    target = witness["target_model"]
    if model_commitment(online, scale) != public["checkpoint_hash_t"]:
        raise AssertionError("checkpoint_hash_t mismatch")
    if model_commitment(target, scale) != public["target_checkpoint_hash"]:
        raise AssertionError("target_checkpoint_hash mismatch")
    leaf = serialize_transition_leaf(
        witness["transition"],
        obs_dim=int(online["layer_sizes"][0]),
        action_dim=int(online["layer_sizes"][-1]),
    )
    leaf_hash = hash_leaf(leaf)
    if leaf_hash != public["leaf_hash"]:
        raise AssertionError("leaf_hash mismatch")
    assert_path_metadata(witness["merkle_path"], int(public["leaf_index"]))
    if recompute_root_from_path(leaf_hash, witness["merkle_path"]) != public["dataset_root"]:
        raise AssertionError("dataset_root mismatch")

    computed = compute_training_update(vector)
    interm = witness["intermediates"]
    expected_intermediates = {
        "z1_online": computed["online_forward"]["z1"],
        "h1_online": computed["online_forward"]["h1"],
        "q_online": computed["online_forward"]["q"],
        "z1_target": computed["target_forward"]["z1"],
        "h1_target": computed["target_forward"]["h1"],
        "q_target": computed["target_forward"]["q"],
        "gradients": computed["gradients"],
        "deltas": computed["deltas"],
    }
    if interm != expected_intermediates:
        raise AssertionError("intermediates mismatch")
    expected_public = {
        "claimed_q_online_action": computed["q_online_action"],
        "claimed_q_target_next": computed["q_target_next"],
        "claimed_td_target": computed["td_target"],
        "claimed_td_error": computed["td_error"],
        "claimed_loss": computed["loss"],
        "checkpoint_hash_t_plus_1": computed["checkpoint_hash_t_plus_1"],
        "claimed_gradient_hash": computed["gradient_hash"],
        "claimed_update_hash": computed["update_hash"],
    }
    for key, expected in expected_public.items():
        if public[key] != expected:
            raise AssertionError(f"{key} mismatch: {public[key]!r} != {expected!r}")
    if witness["online_model_t_plus_1"] != computed["post_model"]:
        raise AssertionError("online_model_t_plus_1 mismatch")
    return public_output(vector, computed)


def public_output(vector: Mapping[str, Any], computed: Mapping[str, Any]) -> Dict[str, Any]:
    p = vector["public_inputs"]
    return {
        "schema_version": "sp1_training_update_public_v1",
        "relation": p["relation"],
        "case_id": p["case_id"],
        "dataset_id_hash": p["dataset_id_hash"],
        "dataset_type": p["dataset_type"],
        "dataset_root": p["dataset_root"],
        "manifest_hash": p["manifest_hash"],
        "audit_report_hash": p["audit_report_hash"],
        "collection_log_final_hash": p["collection_log_final_hash"],
        "raw_trajectory_hash": p["raw_trajectory_hash"],
        "leaf_hash": p["leaf_hash"],
        "leaf_index": p["leaf_index"],
        "checkpoint_hash_t": p["checkpoint_hash_t"],
        "checkpoint_hash_t_plus_1": p["checkpoint_hash_t_plus_1"],
        "target_checkpoint_hash": p["target_checkpoint_hash"],
        "batch_size": p["batch_size"],
        "fixed_point_scale": p["fixed_point_scale"],
        "gamma": p["gamma"],
        "learning_rate": p["learning_rate"],
        "q_online_action": computed["q_online_action"],
        "q_target_next": computed["q_target_next"],
        "td_target": computed["td_target"],
        "td_error": computed["td_error"],
        "loss": computed["loss"],
        "gradient_hash": computed["gradient_hash"],
        "update_hash": computed["update_hash"],
    }


def verify_case(vector: Mapping[str, Any]) -> VerificationResult:
    try:
        return VerificationResult(True, "accepted", verify_vector(vector))
    except Exception as exc:  # noqa: BLE001 - tests need compact rejection reasons
        return VerificationResult(False, str(exc), None)
