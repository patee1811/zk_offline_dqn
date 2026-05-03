import argparse
import hashlib
import json
import os
import pickle
from typing import Any, Dict, List

import torch
import torch.nn as nn

from zk_offline_dqn import zk_specs
from zk_offline_dqn.artifact_schema_versions import SCHEMA_MINIBATCH_TD_V1

encode_fp = zk_specs.encode_fp
compute_td_target_fp = zk_specs.compute_td_target_fp
compute_smooth_l1_loss_fp = zk_specs.compute_smooth_l1_loss_fp

# Ưu tiên dùng đúng hàm serialize của project nếu đã có.
# Nếu chưa có thì fallback sang bản local để giữ script vẫn chạy được.
serialize_transition_leaf = getattr(zk_specs, "serialize_transition_leaf", None)


class QNetwork(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, n_actions),
        )

    def forward(self, x):
        return self.net(x)


def parse_args():
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
        required=True,
        help='Comma-separated minibatch indices, e.g. "0,1,2,3"',
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output artifact JSON path",
    )
    return parser.parse_args()


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_indices(indices_str: str) -> List[int]:
    indices = [int(x.strip()) for x in indices_str.split(",") if x.strip()]
    if not indices:
        raise ValueError("No indices provided.")
    if len(set(indices)) != len(indices):
        raise ValueError(f"Duplicate indices detected: {indices}")
    return indices


def load_transition_dataset(path: str):
    with open(path, "rb") as f:
        data = pickle.load(f)

    required_keys = {"obs", "actions", "rewards", "next_obs", "dones"}
    if not isinstance(data, dict) or not required_keys.issubset(set(data.keys())):
        raise ValueError(
            f"Dataset at {path} must be a dict with keys {sorted(required_keys)}. "
            f"Got keys={list(data.keys()) if isinstance(data, dict) else type(data)}"
        )
    return data


def get_dataset_size(data) -> int:
    return len(data["actions"])


def to_py_float_list(x) -> List[float]:
    return [float(v) for v in x.tolist()]


def get_transition_at(data, idx: int) -> Dict[str, Any]:
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


def hash_leaf_serialized(leaf: List[int]) -> str:
    s = ",".join(str(x) for x in leaf).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


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


def build_merkle_path(levels: List[List[str]], leaf_index: int) -> List[Dict[str, Any]]:
    """
    Sinh path cùng format gần với artifact mẫu:
    {
      "level": ...,
      "current_index": ...,
      "sibling_index": ...,
      "sibling_hash": ...,
      "current_is_left": ...
    }
    """
    path = []
    idx = leaf_index

    for level_idx, level_hashes in enumerate(levels[:-1]):
        if idx < 0 or idx >= len(level_hashes):
            raise IndexError(
                f"Leaf index {idx} out of range for level {level_idx} of size {len(level_hashes)}"
            )

        if idx % 2 == 0:
            sibling_idx = idx + 1 if idx + 1 < len(level_hashes) else idx
            current_is_left = True
        else:
            sibling_idx = idx - 1
            current_is_left = False

        path.append(
            {
                "level": level_idx,
                "current_index": idx,
                "sibling_index": sibling_idx,
                "sibling_hash": level_hashes[sibling_idx],
                "current_is_left": current_is_left,
            }
        )
        idx //= 2

    return path


def load_checkpoint_nets(checkpoint_path: str):
    ckpt = torch.load(checkpoint_path, map_location="cpu")

    required_keys = {"obs_dim", "n_actions", "model_state_dict", "target_net_state_dict"}
    missing = required_keys - set(ckpt.keys())
    if missing:
        raise KeyError(
            f"Checkpoint at {checkpoint_path} is missing required keys: {sorted(missing)}"
        )

    online_net = QNetwork(ckpt["obs_dim"], ckpt["n_actions"])
    online_net.load_state_dict(ckpt["model_state_dict"])
    online_net.eval()

    target_net = QNetwork(ckpt["obs_dim"], ckpt["n_actions"])
    target_net.load_state_dict(ckpt["target_net_state_dict"])
    target_net.eval()

    return ckpt, online_net, target_net


def compute_td_witness(
    transition: Dict[str, Any],
    online_net: nn.Module,
    target_net: nn.Module,
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


def main():
    args = parse_args()

    indices = parse_indices(args.indices)
    data = load_transition_dataset(args.data)
    dataset_size = get_dataset_size(data)

    for idx in indices:
        if idx < 0 or idx >= dataset_size:
            raise IndexError(
                f"Index {idx} out of range for dataset size {dataset_size}"
            )

    merkle = load_merkle_artifact(args.merkle)
    levels = merkle["levels"]
    dataset_root = merkle["merkle_root"]

    if len(levels[0]) != dataset_size:
        raise ValueError(
            f"Mismatch between dataset size ({dataset_size}) and Merkle leaf count ({len(levels[0])})"
        )

    _, online_net, target_net = load_checkpoint_nets(args.checkpoint)
    checkpoint_sha256 = file_sha256(args.checkpoint)

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
            "batch_size": batch_size,
            "loss_type": "smooth_l1",
            "batch_loss_fp": batch_loss_fp,
            "checkpoint_sha256": checkpoint_sha256,
        },
        "items": items,
        "notes": {
            "checkpoint_path": args.checkpoint,
            "data_path": args.data,
            "merkle_path_source": args.merkle,
            "q_target_source": "double_dqn_target_net_at_online_argmax",
            "purpose": "minibatch TD artifact built directly from dataset + merkle + checkpoint",
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
    print("batch_size =", batch_size)
    print("batch_loss_fp =", batch_loss_fp)
    print()

    print("=== PER-ITEM SUMMARY ===")
    for i, item in enumerate(items):
        w = item["td_witness"]
        d = item["debug"]
        print(
            f"item[{i}] index={item['index']} "
            f"next_action_online={d['next_action_online_for_debug']} "
            f"q_online_fp={w['q_online_fp']} "
            f"q_target_max_fp={w['q_target_max_fp']} "
            f"target_fp={w['target_fp']} "
            f"loss_fp={w['loss_fp']} "
            f"path_length={len(item['merkle_path'])}"
        )


if __name__ == "__main__":
    main()