"""Reference checker and fixture generator for multi-step training fragments."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Tuple

from zk_offline_dqn.relations.training_update import (
    apply_sgd_update,
    argmax_first,
    assert_path_metadata,
    fixed_point_mul,
    gradient_commitment,
    hash_internal_node,
    hash_leaf,
    mlp_forward,
    model_commitment,
    recompute_root_from_path,
    serialize_transition_leaf,
    sha256_json,
    smooth_l1_grad_fp,
    smooth_l1_loss_fp,
    update_commitment,
    zero_update_tensors,
)


SCHEMA_VERSION = "sp1_training_fragment_case_v1"
PUBLIC_SCHEMA_VERSION = "sp1_training_fragment_public_v1"
LCG_A = 1_664_525
LCG_C = 1_013_904_223
LCG_M = 2**32
DEFAULT_SAMPLER_SEED = 12_345


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    reason: str
    public_output: Dict[str, Any] | None = None


def lcg_sample_index(seed: int, step_id: int, dataset_size: int) -> int:
    if dataset_size <= 0:
        raise AssertionError("dataset_size must be positive")
    state = int(seed) % LCG_M
    for _ in range(int(step_id) + 1):
        state = (LCG_A * state + LCG_C) % LCG_M
    return state % int(dataset_size)


def trace_commitment(format_name: str, values: Any) -> str:
    return sha256_json({"format": format_name, "values": values})


def fragment_trace_hash(
    checkpoint_chain_hash: str,
    minibatch_indices_hash: str,
    loss_trace_hash: str,
    gradient_trace_hash: str,
    update_trace_hash: str,
) -> str:
    return sha256_json(
        {
            "checkpoint_chain_hash": checkpoint_chain_hash,
            "format": "training_fragment_trace_v1",
            "gradient_trace_hash": gradient_trace_hash,
            "loss_trace_hash": loss_trace_hash,
            "minibatch_indices_hash": minibatch_indices_hash,
            "update_trace_hash": update_trace_hash,
        }
    )


def compute_step(
    public: Mapping[str, Any], step: Mapping[str, Any], online: Mapping[str, Any], target: Mapping[str, Any]
) -> Dict[str, Any]:
    scale = int(public["fixed_point_scale"])
    transition = step["transition"]
    online_forward = mlp_forward(online, [int(v) for v in transition["state"]], scale)
    online_next = mlp_forward(online, [int(v) for v in transition["next_state"]], scale)
    target_forward = mlp_forward(target, [int(v) for v in transition["next_state"]], scale)
    action = int(transition["action"])
    q_online_action = online_forward["q"][action]
    next_action = argmax_first(online_next["q"])
    q_target_next = target_forward["q"][next_action]
    done = bool(transition["terminated"]) or bool(transition["truncated"])
    td_target = (
        int(transition["reward"])
        if done
        else int(transition["reward"]) + fixed_point_mul(int(public["gamma"]), q_target_next, scale)
    )
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
    before_hash = model_commitment(online, scale)
    post_hash = model_commitment(post, scale)
    update_hash = update_commitment(before_hash, post_hash, gradient_hash, int(public["learning_rate"]))
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
        "checkpoint_hash_after": post_hash,
        "update_hash": update_hash,
    }


def recompute_fragment(vector: Mapping[str, Any]) -> Dict[str, Any]:
    public = vector["public_inputs"]
    witness = vector["private_witness"]
    scale = int(public["fixed_point_scale"])
    checkpoint_chain = []
    minibatch_indices = []
    loss_trace = []
    gradient_trace = []
    update_trace = []
    target_sync_events = 0
    expected_online_hash = str(public["start_checkpoint_hash"])
    expected_target_hash = str(public["start_target_checkpoint_hash"])
    for index, step in enumerate(witness["steps"]):
        if int(step["step_id"]) != index:
            raise AssertionError("step_id mismatch")
        if int(step["global_step"]) != int(public.get("global_step_start", 0)) + index:
            raise AssertionError("global_step mismatch")
        sample_index = lcg_sample_index(int(public["sampler_seed"]), index, int(public["dataset_size"]))
        if int(step["sample_index"]) != sample_index:
            raise AssertionError("deterministic sample index mismatch")
        if int(step["leaf_index"]) != sample_index:
            raise AssertionError("leaf_index must match deterministic sample index")
        online_before = step["online_model_before"]
        target_before = step["target_model_before"]
        online_after = step["online_model_after"]
        target_after = step["target_model_after"]
        online_before_hash = model_commitment(online_before, scale)
        target_before_hash = model_commitment(target_before, scale)
        if online_before_hash != step["checkpoint_hash_before"]:
            raise AssertionError("checkpoint_hash_before mismatch")
        if target_before_hash != step["target_checkpoint_hash_before"]:
            raise AssertionError("target_checkpoint_hash_before mismatch")
        if online_before_hash != expected_online_hash:
            raise AssertionError("checkpoint chain mismatch")
        if target_before_hash != expected_target_hash:
            raise AssertionError("target checkpoint chain mismatch")
        leaf = serialize_transition_leaf(
            step["transition"],
            obs_dim=int(online_before["layer_sizes"][0]),
            action_dim=int(online_before["layer_sizes"][-1]),
        )
        leaf_hash = hash_leaf(leaf)
        if leaf_hash != step["leaf_hash"]:
            raise AssertionError("leaf_hash mismatch")
        assert_path_metadata(step["merkle_path"], int(step["leaf_index"]))
        if recompute_root_from_path(leaf_hash, step["merkle_path"]) != public["dataset_root"]:
            raise AssertionError("dataset_root mismatch")
        computed = compute_step(public, step, online_before, target_before)
        expected_intermediates = {
            "q_online_action": computed["q_online_action"],
            "q_target_next": computed["q_target_next"],
            "td_target": computed["td_target"],
            "td_error": computed["td_error"],
            "loss": computed["loss"],
            "z1_online": computed["online_forward"]["z1"],
            "h1_online": computed["online_forward"]["h1"],
            "q_online": computed["online_forward"]["q"],
            "z1_target": computed["target_forward"]["z1"],
            "h1_target": computed["target_forward"]["h1"],
            "q_target": computed["target_forward"]["q"],
            "gradients": computed["gradients"],
            "deltas": computed["deltas"],
            "gradient_hash": computed["gradient_hash"],
            "update_hash": computed["update_hash"],
            "target_sync_applied": _target_sync_applies(public, index),
        }
        if step["intermediates"] != expected_intermediates:
            raise AssertionError("intermediates mismatch")
        if online_after != computed["post_model"]:
            raise AssertionError("online_model_after mismatch")
        online_after_hash = model_commitment(online_after, scale)
        if online_after_hash != step["checkpoint_hash_after"]:
            raise AssertionError("checkpoint_hash_after mismatch")
        sync_applied = _target_sync_applies(public, index)
        expected_target_after = online_after if sync_applied else target_before
        if target_after != expected_target_after:
            raise AssertionError("target_model_after mismatch")
        target_after_hash = model_commitment(target_after, scale)
        if target_after_hash != step["target_checkpoint_hash_after"]:
            raise AssertionError("target_checkpoint_hash_after mismatch")
        if sync_applied:
            target_sync_events += 1
        checkpoint_chain.append(
            {
                "checkpoint_hash_before": online_before_hash,
                "checkpoint_hash_after": online_after_hash,
                "target_checkpoint_hash_before": target_before_hash,
                "target_checkpoint_hash_after": target_after_hash,
                "target_sync_applied": sync_applied,
            }
        )
        minibatch_indices.append(sample_index)
        loss_trace.append(
            {
                "q_online_action": computed["q_online_action"],
                "q_target_next": computed["q_target_next"],
                "td_target": computed["td_target"],
                "td_error": computed["td_error"],
                "loss": computed["loss"],
            }
        )
        gradient_trace.append(computed["gradient_hash"])
        update_trace.append(computed["update_hash"])
        expected_online_hash = online_after_hash
        expected_target_hash = target_after_hash
    checkpoint_chain_hash = trace_commitment("training_fragment_checkpoint_chain_v1", checkpoint_chain)
    minibatch_indices_hash = trace_commitment("training_fragment_minibatch_indices_v1", minibatch_indices)
    loss_trace_hash = trace_commitment("training_fragment_loss_trace_v1", loss_trace)
    gradient_trace_hash = trace_commitment("training_fragment_gradient_trace_v1", gradient_trace)
    update_trace_hash = trace_commitment("training_fragment_update_trace_v1", update_trace)
    trace_hash = fragment_trace_hash(
        checkpoint_chain_hash,
        minibatch_indices_hash,
        loss_trace_hash,
        gradient_trace_hash,
        update_trace_hash,
    )
    return {
        "final_checkpoint_hash": expected_online_hash,
        "final_target_checkpoint_hash": expected_target_hash,
        "checkpoint_chain": checkpoint_chain,
        "minibatch_indices": minibatch_indices,
        "loss_trace": loss_trace,
        "gradient_trace": gradient_trace,
        "update_trace": update_trace,
        "checkpoint_chain_hash": checkpoint_chain_hash,
        "minibatch_indices_hash": minibatch_indices_hash,
        "loss_trace_hash": loss_trace_hash,
        "gradient_trace_hash": gradient_trace_hash,
        "update_trace_hash": update_trace_hash,
        "trace_hash": trace_hash,
        "target_sync_events": target_sync_events,
    }


def verify_vector(vector: Mapping[str, Any]) -> Dict[str, Any]:
    if vector.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError("schema_version mismatch")
    public = vector["public_inputs"]
    witness = vector["private_witness"]
    if public["relation"] != "training_fragment":
        raise AssertionError("relation mismatch")
    if public["batch_size"] != 1:
        raise AssertionError("batch_size mismatch")
    if public["sampler_type"] != "lcg_mod_dataset_size":
        raise AssertionError("sampler_type mismatch")
    if public["target_sync_mode"] != "hard":
        raise AssertionError("target_sync_mode mismatch")
    if public["dataset_type"] != "self_collected_replay_audited":
        raise AssertionError("dataset_type mismatch")
    if int(public["num_steps"]) != len(witness["steps"]):
        raise AssertionError("num_steps mismatch")
    if witness["provenance"] != {
        "dataset_id_hash": public["dataset_id_hash"],
        "dataset_type": public["dataset_type"],
        "manifest_hash": public["manifest_hash"],
        "audit_report_hash": public["audit_report_hash"],
        "collection_log_final_hash": public["collection_log_final_hash"],
        "raw_trajectory_hash": public["raw_trajectory_hash"],
    }:
        raise AssertionError("provenance witness mismatch")
    computed = recompute_fragment(vector)
    for key in [
        "final_checkpoint_hash",
        "final_target_checkpoint_hash",
        "checkpoint_chain_hash",
        "minibatch_indices_hash",
        "loss_trace_hash",
        "gradient_trace_hash",
        "update_trace_hash",
        "trace_hash",
    ]:
        if public[key] != computed[key]:
            raise AssertionError(f"{key} mismatch")
    return public_output(vector, computed)


def public_output(vector: Mapping[str, Any], computed: Mapping[str, Any]) -> Dict[str, Any]:
    p = vector["public_inputs"]
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "relation": p["relation"],
        "case_id": p["case_id"],
        "dataset_id_hash": p["dataset_id_hash"],
        "dataset_type": p["dataset_type"],
        "dataset_root": p["dataset_root"],
        "manifest_hash": p["manifest_hash"],
        "audit_report_hash": p["audit_report_hash"],
        "collection_log_final_hash": p["collection_log_final_hash"],
        "raw_trajectory_hash": p["raw_trajectory_hash"],
        "start_checkpoint_hash": p["start_checkpoint_hash"],
        "final_checkpoint_hash": computed["final_checkpoint_hash"],
        "start_target_checkpoint_hash": p["start_target_checkpoint_hash"],
        "final_target_checkpoint_hash": computed["final_target_checkpoint_hash"],
        "num_steps": p["num_steps"],
        "batch_size": p["batch_size"],
        "fixed_point_scale": p["fixed_point_scale"],
        "gamma": p["gamma"],
        "learning_rate": p["learning_rate"],
        "sampler_seed": p["sampler_seed"],
        "sampler_type": p["sampler_type"],
        "dataset_size": p["dataset_size"],
        "target_sync_interval": p["target_sync_interval"],
        "target_sync_mode": p["target_sync_mode"],
        "trace_hash": computed["trace_hash"],
        "checkpoint_chain_hash": computed["checkpoint_chain_hash"],
        "minibatch_indices_hash": computed["minibatch_indices_hash"],
        "loss_trace_hash": computed["loss_trace_hash"],
        "gradient_trace_hash": computed["gradient_trace_hash"],
        "update_trace_hash": computed["update_trace_hash"],
        "target_sync_events": computed["target_sync_events"],
    }


def verify_case(vector: Mapping[str, Any]) -> VerificationResult:
    try:
        return VerificationResult(True, "accepted", verify_vector(vector))
    except Exception as exc:  # noqa: BLE001 - tests need compact rejection reasons
        return VerificationResult(False, str(exc), None)


def generate_case(num_steps: int, *, dataset_size: int = 128) -> Dict[str, Any]:
    scale = 1000
    public = {
        "relation": "training_fragment",
        "case_id": f"training_fragment_k{num_steps}_case_0",
        "dataset_id_hash": _hash_label("phase6_dataset_id"),
        "dataset_type": "self_collected_replay_audited",
        "dataset_root": "",
        "manifest_hash": _hash_label("phase6_manifest"),
        "audit_report_hash": _hash_label("phase6_audit_report"),
        "collection_log_final_hash": _hash_label("phase6_collection_log"),
        "raw_trajectory_hash": _hash_label("phase6_raw_trajectory"),
        "start_checkpoint_hash": "",
        "final_checkpoint_hash": "",
        "start_target_checkpoint_hash": "",
        "final_target_checkpoint_hash": "",
        "num_steps": num_steps,
        "batch_size": 1,
        "fixed_point_scale": scale,
        "gamma": 990,
        "learning_rate": 10,
        "sampler_seed": DEFAULT_SAMPLER_SEED,
        "sampler_type": "lcg_mod_dataset_size",
        "dataset_size": dataset_size,
        "target_sync_interval": 4,
        "target_sync_mode": "hard",
        "global_step_start": 0,
        "trace_hash": "",
        "checkpoint_chain_hash": "",
        "minibatch_indices_hash": "",
        "loss_trace_hash": "",
        "gradient_trace_hash": "",
        "update_trace_hash": "",
    }
    dataset = [_transition_for_index(index, scale) for index in range(dataset_size)]
    leaves = [
        hash_leaf(serialize_transition_leaf(item, obs_dim=2, action_dim=2))
        for item in dataset
    ]
    root, paths = _merkle_paths(leaves)
    public["dataset_root"] = root
    online = _initial_online_model(scale)
    target = _initial_target_model(scale)
    public["start_checkpoint_hash"] = model_commitment(online, scale)
    public["start_target_checkpoint_hash"] = model_commitment(target, scale)
    steps = []
    for step_id in range(num_steps):
        sample_index = lcg_sample_index(DEFAULT_SAMPLER_SEED, step_id, dataset_size)
        transition = copy.deepcopy(dataset[sample_index])
        before_hash = model_commitment(online, scale)
        target_before_hash = model_commitment(target, scale)
        step_shell = {"transition": transition}
        computed = compute_step(public, step_shell, online, target)
        online_after = computed["post_model"]
        sync_applied = _target_sync_applies(public, step_id)
        target_after = copy.deepcopy(online_after if sync_applied else target)
        step = {
            "step_id": step_id,
            "global_step": step_id,
            "sample_index": sample_index,
            "transition": transition,
            "leaf_hash": leaves[sample_index],
            "leaf_index": sample_index,
            "merkle_path": paths[sample_index],
            "checkpoint_hash_before": before_hash,
            "checkpoint_hash_after": model_commitment(online_after, scale),
            "target_checkpoint_hash_before": target_before_hash,
            "target_checkpoint_hash_after": model_commitment(target_after, scale),
            "online_model_before": copy.deepcopy(online),
            "target_model_before": copy.deepcopy(target),
            "online_model_after": copy.deepcopy(online_after),
            "target_model_after": copy.deepcopy(target_after),
            "intermediates": {
                "q_online_action": computed["q_online_action"],
                "q_target_next": computed["q_target_next"],
                "td_target": computed["td_target"],
                "td_error": computed["td_error"],
                "loss": computed["loss"],
                "z1_online": computed["online_forward"]["z1"],
                "h1_online": computed["online_forward"]["h1"],
                "q_online": computed["online_forward"]["q"],
                "z1_target": computed["target_forward"]["z1"],
                "h1_target": computed["target_forward"]["h1"],
                "q_target": computed["target_forward"]["q"],
                "gradients": computed["gradients"],
                "deltas": computed["deltas"],
                "gradient_hash": computed["gradient_hash"],
                "update_hash": computed["update_hash"],
                "target_sync_applied": sync_applied,
            },
        }
        steps.append(step)
        online = online_after
        target = target_after
    vector = {
        "schema_version": SCHEMA_VERSION,
        "public_inputs": public,
        "private_witness": {
            "provenance": {
                "dataset_id_hash": public["dataset_id_hash"],
                "dataset_type": public["dataset_type"],
                "manifest_hash": public["manifest_hash"],
                "audit_report_hash": public["audit_report_hash"],
                "collection_log_final_hash": public["collection_log_final_hash"],
                "raw_trajectory_hash": public["raw_trajectory_hash"],
            },
            "steps": steps,
        },
    }
    computed_fragment = recompute_fragment(vector)
    for key in [
        "final_checkpoint_hash",
        "final_target_checkpoint_hash",
        "checkpoint_chain_hash",
        "minibatch_indices_hash",
        "loss_trace_hash",
        "gradient_trace_hash",
        "update_trace_hash",
        "trace_hash",
    ]:
        public[key] = computed_fragment[key]
    return vector


def _target_sync_applies(public: Mapping[str, Any], step_id: int) -> bool:
    interval = int(public["target_sync_interval"])
    if interval <= 0:
        raise AssertionError("target_sync_interval must be positive")
    return (int(public.get("global_step_start", 0)) + int(step_id) + 1) % interval == 0


def _hash_label(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _initial_online_model(scale: int) -> Dict[str, Any]:
    return {
        "format": "quantized_mlp_v1",
        "layer_sizes": [2, 2, 2],
        "fp_scale": scale,
        "layers": [
            {"weight": [[700, -200], [300, 500]], "bias": [50, -40]},
            {"weight": [[600, -300], [-250, 450]], "bias": [20, -30]},
        ],
    }


def _initial_target_model(scale: int) -> Dict[str, Any]:
    model = _initial_online_model(scale)
    model["layers"][0]["weight"][0][0] = 650
    model["layers"][1]["bias"][1] = -20
    return model


def _transition_for_index(index: int, scale: int) -> Dict[str, Any]:
    state0 = ((index % 11) - 5) * 100
    state1 = (((index * 3) % 13) - 6) * 80
    next_state0 = state0 + (((index % 3) - 1) * 50)
    next_state1 = state1 + ((((index + 1) % 5) - 2) * 40)
    return {
        "state": [state0, state1],
        "action": index % 2,
        "reward": (((index * 7) % 5) - 2) * (scale // 10),
        "next_state": [next_state0, next_state1],
        "terminated": index % 29 == 0,
        "truncated": index % 31 == 0,
    }


def _merkle_paths(leaves: List[str]) -> Tuple[str, List[List[Dict[str, Any]]]]:
    if not leaves:
        raise AssertionError("Merkle tree requires at least one leaf")
    levels = [leaves[:]]
    while len(levels[-1]) > 1:
        level = levels[-1]
        next_level = []
        for pos in range(0, len(level), 2):
            left = level[pos]
            right = level[pos + 1] if pos + 1 < len(level) else left
            next_level.append(hash_internal_node(left, right))
        levels.append(next_level)
    paths: List[List[Dict[str, Any]]] = []
    for leaf_index in range(len(leaves)):
        current_index = leaf_index
        path = []
        for level_num, level in enumerate(levels[:-1]):
            current_is_left = current_index % 2 == 0
            sibling_index = current_index + 1 if current_is_left else current_index - 1
            if sibling_index >= len(level):
                sibling_index = current_index
            path.append(
                {
                    "level": level_num,
                    "current_index": current_index,
                    "sibling_index": sibling_index,
                    "sibling_hash": level[sibling_index],
                    "current_is_left": current_is_left,
                }
            )
            current_index //= 2
        paths.append(path)
    return levels[-1][0], paths
