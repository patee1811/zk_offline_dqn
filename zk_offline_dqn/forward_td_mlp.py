from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List


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


def argmax_first(values: List[int]) -> int:
    if not values:
        raise ValueError("argmax requires at least one value")
    best_idx = 0
    best_value = values[0]
    for idx, value in enumerate(values[1:], start=1):
        if value > best_value:
            best_idx = idx
            best_value = value
    return best_idx


@dataclass(frozen=True)
class ForwardTrace:
    pre_activations: List[List[int]]
    relu_masks: List[List[int]]
    outputs: List[int]

    def to_json(self) -> Dict[str, Any]:
        return {
            "pre_activations": self.pre_activations,
            "relu_masks": self.relu_masks,
            "outputs": self.outputs,
        }


def build_network_spec_hash(layer_sizes: List[int], fp_scale: int) -> str:
    payload = {
        "format": "network_spec_v1",
        "layer_sizes": layer_sizes,
        "activation": "relu_hidden_identity_output",
        "fp_scale": fp_scale,
    }
    return sha256_json(payload)


def build_model_commitment(model: Dict[str, Any], fp_scale: int) -> str:
    payload = {
        "format": "quantized_mlp_v1",
        "fp_scale": fp_scale,
        "layer_sizes": model["layer_sizes"],
        "layers": model["layers"],
    }
    return sha256_json(payload)


def sha256_json(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_deterministic_mlp(layer_sizes: List[int], fp_scale: int, seed: int) -> Dict[str, Any]:
    if len(layer_sizes) < 2:
        raise ValueError("network must have at least input and output layers")
    layers = []
    state = seed & 0x7FFFFFFF
    for in_dim, out_dim in zip(layer_sizes[:-1], layer_sizes[1:]):
        weights = []
        for _ in range(out_dim):
            row = []
            for _ in range(in_dim):
                state = (1103515245 * state + 12345) & 0x7FFFFFFF
                row.append((state % 401) - 200)
            weights.append(row)
        bias = []
        for _ in range(out_dim):
            state = (1103515245 * state + 12345) & 0x7FFFFFFF
            bias.append((state % 101) - 50)
        layers.append({"weight": weights, "bias": bias})
    return {
        "format": "quantized_mlp_v1",
        "layer_sizes": layer_sizes,
        "fp_scale": fp_scale,
        "layers": layers,
    }


def mlp_forward(model: Dict[str, Any], input_fp: List[int], fp_scale: int) -> ForwardTrace:
    layer_sizes = model["layer_sizes"]
    if len(input_fp) != layer_sizes[0]:
        raise ValueError(f"input length mismatch: got {len(input_fp)}, expected {layer_sizes[0]}")

    activations = [int(v) for v in input_fp]
    pre_activations: List[List[int]] = []
    relu_masks: List[List[int]] = []

    for layer_idx, layer in enumerate(model["layers"]):
        weight = layer["weight"]
        bias = layer["bias"]
        out_dim = layer_sizes[layer_idx + 1]
        if len(weight) != out_dim or len(bias) != out_dim:
            raise ValueError("layer shape mismatch")
        pre = []
        for row, bias_fp in zip(weight, bias):
            if len(row) != len(activations):
                raise ValueError("weight row shape mismatch")
            acc = int(bias_fp)
            for w_fp, x_fp in zip(row, activations):
                acc += fixed_point_mul(int(w_fp), int(x_fp), fp_scale)
            pre.append(acc)

        is_hidden = layer_idx + 1 < len(model["layers"])
        if is_hidden:
            mask = [1 if value > 0 else 0 for value in pre]
            activations = [value if value > 0 else 0 for value in pre]
            pre_activations.append(pre)
            relu_masks.append(mask)
        else:
            activations = pre

    return ForwardTrace(
        pre_activations=pre_activations,
        relu_masks=relu_masks,
        outputs=activations,
    )


def compute_forward_td_item(
    *,
    transition: Dict[str, Any],
    online_model: Dict[str, Any],
    target_model: Dict[str, Any],
    fp_scale: int,
    gamma_fp: int,
) -> Dict[str, Any]:
    obs_fp = [int(round(float(value) * fp_scale)) for value in transition["obs"]]
    next_obs_fp = [int(round(float(value) * fp_scale)) for value in transition["next_obs"]]
    reward_fp = int(round(float(transition["reward"]) * fp_scale))
    action = int(transition["action"])
    done = int(transition["done"])

    online_obs = mlp_forward(online_model, obs_fp, fp_scale)
    online_next = mlp_forward(online_model, next_obs_fp, fp_scale)
    target_next = mlp_forward(target_model, next_obs_fp, fp_scale)

    q_online_action_fp = online_obs.outputs[action]
    next_action_online = argmax_first(online_next.outputs)
    q_target_max_fp = target_next.outputs[next_action_online]
    if done == 1:
        target_fp = reward_fp
    elif done == 0:
        target_fp = reward_fp + fixed_point_mul(gamma_fp, q_target_max_fp, fp_scale)
    else:
        raise ValueError(f"done must be 0 or 1, got {done}")

    td_error_fp = q_online_action_fp - target_fp
    loss_fp = smooth_l1_loss_fp(td_error_fp, fp_scale)

    return {
        "online_obs": online_obs.to_json(),
        "online_next": online_next.to_json(),
        "target_next": target_next.to_json(),
        "q_online_action_fp": q_online_action_fp,
        "next_action_online": next_action_online,
        "q_target_max_fp": q_target_max_fp,
        "target_fp": target_fp,
        "td_error_fp": td_error_fp,
        "loss_fp": loss_fp,
    }
