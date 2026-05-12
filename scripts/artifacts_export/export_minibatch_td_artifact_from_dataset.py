import argparse
import json
import os
import pickle
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn import zk_specs
from zk_offline_dqn.artifact_schema_versions import SCHEMA_MINIBATCH_TD_V1
from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments
from zk_offline_dqn.io_utils import file_sha256
from zk_offline_dqn.merkle import build_merkle_path, hash_leaf as hash_leaf_serialized
from zk_offline_dqn.models import QNetwork

encode_fp = zk_specs.encode_fp
compute_td_target_fp = zk_specs.compute_td_target_fp
compute_smooth_l1_loss_fp = zk_specs.compute_smooth_l1_loss_fp

# Prefer the project-level serializer if available.
# Fall back to a local serializer to keep this script runnable.
serialize_transition_leaf = getattr(zk_specs, "serialize_transition_leaf", None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export minibatch TD artifact directly from dataset + Merkle + checkpoint."
    )

    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to transition dataset .pkl",
    )
    parser.add_argument(
        "--merkle",
        type=str,
        required=True,
        help="Path to Merkle JSON artifact",
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        required=True,
        help="Path to trained checkpoint .pt",
    )
    parser.add_argument(
        "--indices",
        type=str,
        default=None,
        help=(
            'Comma-separated minibatch indices, e.g. "0,1,2,3". '
            "If omitted, --batch-size distinct indices are selected from "
            "--start-index with --stride."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of distinct indices to select when --indices is omitted.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="First dataset index for automatic distinct-index selection.",
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=1,
        help="Stride for automatic distinct-index selection.",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output artifact JSON path",
    )

    return parser.parse_args()


def parse_indices(indices_str: str) -> List[int]:
    indices = [int(x.strip()) for x in indices_str.split(",") if x.strip()]

    if not indices:
        raise ValueError("No indices provided.")

    if len(set(indices)) != len(indices):
        raise ValueError(f"Duplicate indices detected: {indices}")

    return indices


def select_distinct_indices(
    *,
    explicit_indices: Optional[str],
    batch_size: Optional[int],
    start_index: int,
    stride: int,
) -> List[int]:
    if explicit_indices is not None:
        return parse_indices(explicit_indices)

    if batch_size is None:
        raise ValueError("Either --indices or --batch-size must be provided.")
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive, got {batch_size}")
    if stride <= 0:
        raise ValueError(f"stride must be positive, got {stride}")

    return [start_index + stride * offset for offset in range(batch_size)]


def load_transition_dataset(path: str) -> Dict[str, Any]:
    with open(path, "rb") as f:
        data = pickle.load(f)

    required_keys = {"obs", "actions", "rewards", "next_obs", "dones"}

    if not isinstance(data, dict) or not required_keys.issubset(set(data.keys())):
        got = list(data.keys()) if isinstance(data, dict) else type(data)
        raise ValueError(
            f"Dataset at {path} must be a dict with keys {sorted(required_keys)}. "
            f"Got keys={got}"
        )

    return data


def get_dataset_size(data: Dict[str, Any]) -> int:
    return len(data["actions"])


def to_py_float_list(x: Any) -> List[float]:
    return [float(v) for v in x.tolist()]


def get_transition_at(data: Dict[str, Any], idx: int) -> Dict[str, Any]:
    return {
        "obs": to_py_float_list(data["obs"][idx]),
        "action": int(data["actions"][idx]),
        "reward": float(data["rewards"][idx]),
        "next_obs": to_py_float_list(data["next_obs"][idx]),
        "done": int(data["dones"][idx]),
    }


def local_serialize_transition_leaf(transition: Dict[str, Any]) -> List[int]:
    obs_fp = [encode_fp(float(x)) for x in transition["obs"]]
    action = int(transition["action"])
    reward_fp = encode_fp(float(transition["reward"]))
    next_obs_fp = [encode_fp(float(x)) for x in transition["next_obs"]]
    done = int(transition["done"])

    return obs_fp + [action, reward_fp] + next_obs_fp + [done]


def serialize_leaf(transition: Dict[str, Any]) -> List[int]:
    if serialize_transition_leaf is not None:
        return serialize_transition_leaf(transition)

    return local_serialize_transition_leaf(transition)


def load_merkle_artifact(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        merkle = json.load(f)

    required_keys = {"merkle_root", "levels"}

    if not required_keys.issubset(set(merkle.keys())):
        raise ValueError(
            f"Merkle JSON at {path} must contain keys {sorted(required_keys)}. "
            f"Got keys={list(merkle.keys())}"
        )

    if not isinstance(merkle["levels"], list) or len(merkle["levels"]) == 0:
        raise ValueError("Merkle artifact has invalid or empty levels.")

    return merkle


def get_online_state_dict_key(checkpoint: Dict[str, Any]) -> str:
    if "online_net_state_dict" in checkpoint:
        return "online_net_state_dict"

    if "model_state_dict" in checkpoint:
        return "model_state_dict"

    raise KeyError(
        "Checkpoint missing online network state dict. "
        "Expected either 'online_net_state_dict' or 'model_state_dict'. "
        f"Available keys: {sorted(checkpoint.keys())}"
    )


def load_checkpoint_nets(
    checkpoint_path: str,
) -> Tuple[Dict[str, Any], torch.nn.Module, torch.nn.Module, str]:
    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    if "obs_dim" not in checkpoint:
        raise KeyError(f"Checkpoint at {checkpoint_path} is missing key: obs_dim")

    if "n_actions" not in checkpoint:
        raise KeyError(f"Checkpoint at {checkpoint_path} is missing key: n_actions")

    if "target_net_state_dict" not in checkpoint:
        raise KeyError(
            f"Checkpoint at {checkpoint_path} is missing key: target_net_state_dict"
        )

    online_state_dict_key = get_online_state_dict_key(checkpoint)

    online_net = QNetwork(
        obs_dim=int(checkpoint["obs_dim"]),
        n_actions=int(checkpoint["n_actions"]),
    )
    online_net.load_state_dict(checkpoint[online_state_dict_key])
    online_net.eval()

    target_net = QNetwork(
        obs_dim=int(checkpoint["obs_dim"]),
        n_actions=int(checkpoint["n_actions"]),
    )
    target_net.load_state_dict(checkpoint["target_net_state_dict"])
    target_net.eval()

    return checkpoint, online_net, target_net, online_state_dict_key


def compute_td_witness(
    transition: Dict[str, Any],
    online_net: torch.nn.Module,
    target_net: torch.nn.Module,
) -> Dict[str, Any]:
    obs = torch.tensor(transition["obs"], dtype=torch.float32).unsqueeze(0)
    next_obs = torch.tensor(transition["next_obs"], dtype=torch.float32).unsqueeze(0)

    action = int(transition["action"])
    reward_fp = encode_fp(float(transition["reward"]))
    done_int = int(transition["done"])

    with torch.no_grad():
        q_obs_online = online_net(obs).squeeze(0)
        q_next_online = online_net(next_obs).squeeze(0)
        q_next_target = target_net(next_obs).squeeze(0)

    q_online_real = float(q_obs_online[action].item())

    next_action_online = int(torch.argmax(q_next_online).item())
    q_target_max_real = float(q_next_target[next_action_online].item())

    q_online_fp = encode_fp(q_online_real)
    q_target_max_fp = encode_fp(q_target_max_real)

    target_fp = compute_td_target_fp(
        reward_fp=reward_fp,
        done=done_int,
        q_target_max_fp=q_target_max_fp,
    )

    loss_fp = compute_smooth_l1_loss_fp(
        q_online_fp=q_online_fp,
        target_fp=target_fp,
    )

    return {
        "td_witness": {
            "q_online_fp": q_online_fp,
            "next_action_online": next_action_online,
            "q_target_max_fp": q_target_max_fp,
            "target_fp": target_fp,
            "loss_fp": loss_fp,
        },
        "debug": {
            "q_online_real_for_debug": q_online_real,
            "q_next_online_for_debug": q_next_online.tolist(),
            "q_next_target_for_debug": q_next_target.tolist(),
            "next_action_online_for_debug": next_action_online,
            "q_target_max_real_for_debug": q_target_max_real,
        },
    }


def main() -> None:
    args = parse_args()

    indices = select_distinct_indices(
        explicit_indices=args.indices,
        batch_size=args.batch_size,
        start_index=args.start_index,
        stride=args.stride,
    )

    data = load_transition_dataset(args.data)
    dataset_size = get_dataset_size(data)

    for idx in indices:
        if idx < 0 or idx >= dataset_size:
            raise IndexError(f"Index {idx} out of range for dataset size {dataset_size}")

    merkle = load_merkle_artifact(args.merkle)
    levels = merkle["levels"]
    dataset_root = merkle["merkle_root"]

    if len(levels[0]) != dataset_size:
        raise ValueError(
            f"Mismatch between dataset size ({dataset_size}) and Merkle leaf count "
            f"({len(levels[0])})"
        )

    checkpoint, online_net, target_net, online_state_dict_key = load_checkpoint_nets(
        args.checkpoint
    )

    checkpoint_sha256 = file_sha256(args.checkpoint)
    state_commitments = canonical_checkpoint_state_commitments(checkpoint)

    if state_commitments["online_state_dict_key"] != online_state_dict_key:
        raise ValueError(
            "Inconsistent online state-dict key between checkpoint loader and "
            "canonical commitment helper. "
            f"loader={online_state_dict_key}, "
            f"commitment={state_commitments['online_state_dict_key']}"
        )

    items = []
    total_loss_fp = 0

    for idx in indices:
        transition = get_transition_at(data, idx)
        leaf = serialize_leaf(transition)
        leaf_hash = hash_leaf_serialized(leaf)

        expected_leaf_hash = levels[0][idx]

        if leaf_hash != expected_leaf_hash:
            raise ValueError(
                f"Leaf hash mismatch at index {idx}.\n"
                f"computed={leaf_hash}\n"
                f"expected={expected_leaf_hash}"
            )

        merkle_path = build_merkle_path(levels, idx)

        witness_pack = compute_td_witness(
            transition=transition,
            online_net=online_net,
            target_net=target_net,
        )

        item = {
            "index": idx,
            "transition": transition,
            "leaf": leaf,
            "leaf_hash": leaf_hash,
            "merkle_path": merkle_path,
            "td_witness": witness_pack["td_witness"],
            "debug": witness_pack["debug"],
        }

        items.append(item)
        total_loss_fp += witness_pack["td_witness"]["loss_fp"]

    batch_size = len(items)
    batch_loss_fp = total_loss_fp // batch_size

    artifact = {
        "schema_version": SCHEMA_MINIBATCH_TD_V1,
        "public": {
            "dataset_root": dataset_root,
            "fp_scale": zk_specs.SPECS.FP_SCALE,
            "gamma_fp": zk_specs.SPECS.GAMMA_FP,
            "batch_size": batch_size,
            "batch_mode": "distinct",
            "leaf_indices": [int(item["index"]) for item in items],
            "loss_type": "smooth_l1",
            "batch_loss_fp": batch_loss_fp,
            "checkpoint_sha256": checkpoint_sha256,
            "checkpoint_commitment_type": "sha256_file_and_canonical_state_dicts",
            "online_state_dict_key": state_commitments["online_state_dict_key"],
            "online_state_dict_sha256": state_commitments["online_state_dict_sha256"],
            "target_state_dict_sha256": state_commitments["target_state_dict_sha256"],
        },
        "items": items,
        "notes": {
            "checkpoint_path": args.checkpoint,
            "data_path": args.data,
            "merkle_path_source": args.merkle,
            "q_target_source": "double_dqn_target_net_at_online_argmax",
            "purpose": "minibatch TD artifact built directly from dataset + merkle + checkpoint",
            "commitment_note": (
                "checkpoint_sha256 anchors the checkpoint file; "
                "online_state_dict_sha256 and target_state_dict_sha256 anchor "
                "canonical sorted state_dict tensor contents."
            ),
        },
    }

    out_dir = os.path.dirname(args.out)

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== MINIBATCH TD ARTIFACT EXPORTED FROM DATASET ===")
    print("output_path =", args.out)
    print("data_path =", args.data)
    print("merkle_path =", args.merkle)
    print("dataset_root =", dataset_root)
    print("checkpoint_path =", args.checkpoint)
    print("checkpoint_sha256 =", checkpoint_sha256)
    print("checkpoint_commitment_type =", artifact["public"]["checkpoint_commitment_type"])
    print("online_state_dict_key =", artifact["public"]["online_state_dict_key"])
    print("online_state_dict_sha256 =", artifact["public"]["online_state_dict_sha256"])
    print("target_state_dict_sha256 =", artifact["public"]["target_state_dict_sha256"])
    print("batch_size =", batch_size)
    print("batch_loss_fp =", batch_loss_fp)
    print()

    print("=== PER-ITEM SUMMARY ===")
    for i, item in enumerate(items):
        w = item["td_witness"]
        print(
            f"item[{i}] index={item['index']} "
            f"next_action_online={w['next_action_online']} "
            f"q_online_fp={w['q_online_fp']} "
            f"q_target_max_fp={w['q_target_max_fp']} "
            f"target_fp={w['target_fp']} "
            f"loss_fp={w['loss_fp']} "
            f"path_length={len(item['merkle_path'])}"
        )


if __name__ == "__main__":
    main()
