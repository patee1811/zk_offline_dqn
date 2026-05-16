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
    compute_forward_td_item,
)


DEFAULT_INPUT = Path("artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json")
DEFAULT_OUT = Path("zk_backend/test_vectors/forward_td_mlp_case_0.json")
DEFAULT_LAYER_SIZES = [4, 16, 16, 2]


def parse_layer_sizes(raw: str) -> List[int]:
    sizes = [int(value.strip()) for value in raw.split(",") if value.strip()]
    if len(sizes) < 2:
        raise ValueError("layer sizes must include at least input and output")
    if any(size <= 0 for size in sizes):
        raise ValueError(f"layer sizes must be positive, got {sizes}")
    return sizes


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_forward_item(item: Dict[str, Any], forward_witness: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "index": int(item["index"]),
        "transition": copy.deepcopy(item["transition"]),
        "leaf": copy.deepcopy(item["leaf"]),
        "leaf_hash": item["leaf_hash"],
        "merkle_path": copy.deepcopy(item["merkle_path"]),
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


def build_forward_td_vector(
    *,
    source_artifact: Dict[str, Any],
    source_path: Path,
    out_path: Path,
    batch_size: int,
    layer_sizes: List[int],
    online_seed: int,
    target_seed: int,
) -> Dict[str, Any]:
    source_items = source_artifact["items"]
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if batch_size > len(source_items):
        raise ValueError(
            f"batch_size={batch_size} exceeds source item count={len(source_items)}"
        )

    public = source_artifact["public"]
    fp_scale = int(public.get("fp_scale", 1000))
    gamma_fp = int(public.get("gamma_fp", 990))
    online_model = build_deterministic_mlp(layer_sizes, fp_scale, online_seed)
    target_model = build_deterministic_mlp(layer_sizes, fp_scale, target_seed)
    network_spec_hash = build_network_spec_hash(layer_sizes, fp_scale)
    online_commitment = build_model_commitment(online_model, fp_scale)
    target_commitment = build_model_commitment(target_model, fp_scale)

    items = []
    total_loss_fp = 0
    for item in source_items[:batch_size]:
        forward_witness = compute_forward_td_item(
            transition=item["transition"],
            online_model=online_model,
            target_model=target_model,
            fp_scale=fp_scale,
            gamma_fp=gamma_fp,
        )
        items.append(build_forward_item(item, forward_witness))
        total_loss_fp += int(forward_witness["loss_fp"])

    claimed_item_losses_fp = [int(item["forward_witness"]["loss_fp"]) for item in items]
    claimed_batch_loss_fp = total_loss_fp // batch_size
    leaf_indices = [int(item["index"]) for item in items]

    return {
        "schema_version": "forward_td_mlp_v1",
        "source": {
            "artifact_path": source_path.as_posix(),
            "output_path": out_path.as_posix(),
            "construction": "distinct committed replay transitions with synthetic quantized MLP weights",
        },
        "statement": {
            "name": "forward_td_mlp_v1",
            "description": (
                "Fixed-point MLP forward, Double-DQN argmax/value selection, "
                "Bellman target, SmoothL1 loss, Merkle membership, and model commitments."
            ),
        },
        "public": {
            "dataset_root": public["dataset_root"],
            "fp_scale": fp_scale,
            "gamma_fp": gamma_fp,
            "loss_type": public["loss_type"],
            "batch_size": batch_size,
            "batch_mode": "distinct",
            "leaf_indices": leaf_indices,
            "network_spec_hash": network_spec_hash,
            "network_layer_sizes": layer_sizes,
            "online_model_commitment": online_commitment,
            "target_model_commitment": target_commitment,
            "claimed_item_losses_fp": claimed_item_losses_fp,
            "claimed_batch_loss_fp": claimed_batch_loss_fp,
        },
        "private": {
            "online_model": online_model,
            "target_model": target_model,
            "items": items,
        },
        "relation": {
            "checks": [
                "transition serializes canonically",
                "Merkle path authenticates to public dataset_root",
                "online weights hash to online_model_commitment",
                "target weights hash to target_model_commitment",
                "online MLP computes Q_online(s)",
                "online MLP computes Q_online(s')",
                "target MLP computes Q_target(s')",
                "q_online_action == Q_online(s)[action]",
                "next_action_online == first argmax_a Q_online(s')[a]",
                "q_target_max == Q_target(s')[next_action_online]",
                "Bellman target and SmoothL1 loss match public claims",
            ],
            "non_goals": [
                "does not prove gradient computation",
                "does not prove optimizer update",
                "does not prove full DQN training",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--layer-sizes", default=",".join(str(v) for v in DEFAULT_LAYER_SIZES))
    parser.add_argument("--online-seed", type=int, default=20260603)
    parser.add_argument("--target-seed", type=int, default=20260617)
    args = parser.parse_args()

    source_artifact = load_json(args.input)
    layer_sizes = parse_layer_sizes(args.layer_sizes)
    vector = build_forward_td_vector(
        source_artifact=source_artifact,
        source_path=args.input,
        out_path=args.out,
        batch_size=args.batch_size,
        layer_sizes=layer_sizes,
        online_seed=args.online_seed,
        target_seed=args.target_seed,
    )
    write_json(args.out, vector)

    print("wrote_test_vector =", args.out.as_posix())
    print("schema_version =", vector["schema_version"])
    print("batch_size =", vector["public"]["batch_size"])
    print("network_layer_sizes =", vector["public"]["network_layer_sizes"])
    print("network_spec_hash =", vector["public"]["network_spec_hash"])
    print("online_model_commitment =", vector["public"]["online_model_commitment"])
    print("target_model_commitment =", vector["public"]["target_model_commitment"])
    print("claimed_batch_loss_fp =", vector["public"]["claimed_batch_loss_fp"])


if __name__ == "__main__":
    main()
