from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.forward_td_mlp import (  # noqa: E402
    build_deterministic_mlp,
    build_model_commitment,
    build_network_spec_hash,
    compute_one_step_sgd_tiny,
)


DEFAULT_INPUT = Path("artifacts/minibatch_td_from_dataset.json")
DEFAULT_OUT = Path("zk_backend/test_vectors/one_step_sgd_tiny_case_0.json")


def parse_layer_sizes(raw: str) -> List[int]:
    sizes = [int(value.strip()) for value in raw.split(",") if value.strip()]
    if len(sizes) != 3:
        raise ValueError("one_step_sgd_tiny_v1 expects one hidden layer, e.g. 4,8,2")
    if any(size <= 0 for size in sizes):
        raise ValueError(f"layer sizes must be positive, got {sizes}")
    return sizes


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_item(source_item: Dict[str, Any], forward_witness: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "index": int(source_item["index"]),
        "transition": copy.deepcopy(source_item["transition"]),
        "leaf": copy.deepcopy(source_item["leaf"]),
        "leaf_hash": source_item["leaf_hash"],
        "merkle_path": copy.deepcopy(source_item["merkle_path"]),
        "forward_witness": forward_witness,
        "td_witness": {
            "q_online_fp": forward_witness["q_online_action_fp"],
            "next_action_online": forward_witness["next_action_online"],
            "q_target_max_fp": forward_witness["q_target_max_fp"],
            "target_fp": forward_witness["target_fp"],
            "td_error_fp": forward_witness["td_error_fp"],
            "loss_fp": forward_witness["loss_fp"],
        },
    }


def build_vector(
    *,
    source_artifact: Dict[str, Any],
    source_path: Path,
    out_path: Path,
    layer_sizes: List[int],
    online_seed: int,
    target_seed: int,
    learning_rate_fp: int,
) -> Dict[str, Any]:
    public = source_artifact["public"]
    source_item = source_artifact["items"][0]
    fp_scale = int(public.get("fp_scale", 1000))
    gamma_fp = int(public.get("gamma_fp", 990))
    pre_model = build_deterministic_mlp(layer_sizes, fp_scale, online_seed)
    target_model = build_deterministic_mlp(layer_sizes, fp_scale, target_seed)
    update = compute_one_step_sgd_tiny(
        transition=source_item["transition"],
        pre_model=pre_model,
        target_model=target_model,
        fp_scale=fp_scale,
        gamma_fp=gamma_fp,
        learning_rate_fp=learning_rate_fp,
    )
    post_model = update["post_model"]
    network_spec_hash = build_network_spec_hash(layer_sizes, fp_scale)

    return {
        "schema_version": "one_step_sgd_tiny_v1",
        "source": {
            "artifact_path": source_path.as_posix(),
            "output_path": out_path.as_posix(),
            "construction": "single committed replay transition with synthetic 4-8-2 fixed-point MLP SGD update",
        },
        "statement": {
            "name": "one_step_sgd_tiny_v1",
            "description": (
                "Micro one-step SGD relation over a one-hidden-layer fixed-point Q-network. "
                "Includes committed transition membership, forward-TD, SmoothL1 derivative, "
                "backprop gradients, SGD deltas, and pre/post model commitments."
            ),
        },
        "public": {
            "dataset_root": public["dataset_root"],
            "fp_scale": fp_scale,
            "gamma_fp": gamma_fp,
            "loss_type": public["loss_type"],
            "optimizer_type": "sgd",
            "learning_rate_fp": learning_rate_fp,
            "batch_size": 1,
            "batch_mode": "distinct",
            "leaf_indices": [int(source_item["index"])],
            "network_spec_hash": network_spec_hash,
            "network_layer_sizes": layer_sizes,
            "pre_model_commitment": build_model_commitment(pre_model, fp_scale),
            "post_model_commitment": build_model_commitment(post_model, fp_scale),
            "target_model_commitment": build_model_commitment(target_model, fp_scale),
            "claimed_batch_loss_fp": int(update["forward_witness"]["loss_fp"]),
        },
        "private": {
            "online_model": pre_model,
            "target_model": target_model,
            "post_online_model": post_model,
            "items": [build_item(source_item, update["forward_witness"])],
            "update_witness": {
                "batch_loss_fp": int(update["forward_witness"]["loss_fp"]),
                "smooth_l1_grad_fp": int(update["smooth_l1_grad_fp"]),
                "gradient_tensors": update["gradient_tensors"],
                "delta_tensors": update["delta_tensors"],
            },
        },
        "relation": {
            "checks": [
                "forward_td_mlp_v1 holds for the single committed transition",
                "SmoothL1 derivative branch is correct",
                "one-hidden-layer backprop gradients are correct",
                "delta == -learning_rate * gradient for every parameter",
                "post_model == pre_model + delta for every parameter",
                "post_model hashes to public post_model_commitment",
            ],
            "non_goals": [
                "does not prove Adam",
                "does not prove target synchronization",
                "does not prove a long training trace",
                "does not prove full DQN training",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--layer-sizes", default="4,8,2")
    parser.add_argument("--online-seed", type=int, default=20260701)
    parser.add_argument("--target-seed", type=int, default=20260707)
    parser.add_argument("--learning-rate-fp", type=int, default=100)
    args = parser.parse_args()

    source_artifact = load_json(args.input)
    vector = build_vector(
        source_artifact=source_artifact,
        source_path=args.input,
        out_path=args.out,
        layer_sizes=parse_layer_sizes(args.layer_sizes),
        online_seed=args.online_seed,
        target_seed=args.target_seed,
        learning_rate_fp=args.learning_rate_fp,
    )
    write_json(args.out, vector)

    print("wrote_test_vector =", args.out.as_posix())
    print("schema_version =", vector["schema_version"])
    print("network_layer_sizes =", vector["public"]["network_layer_sizes"])
    print("learning_rate_fp =", vector["public"]["learning_rate_fp"])
    print("pre_model_commitment =", vector["public"]["pre_model_commitment"])
    print("post_model_commitment =", vector["public"]["post_model_commitment"])
    print("claimed_batch_loss_fp =", vector["public"]["claimed_batch_loss_fp"])


if __name__ == "__main__":
    main()
