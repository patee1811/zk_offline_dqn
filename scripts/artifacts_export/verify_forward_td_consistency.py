# scripts/artifacts_export/verify_forward_td_consistency.py

import argparse
import json
from typing import Any, Dict, Tuple

import torch
import torch.nn as nn

from zk_offline_dqn import zk_specs
from zk_offline_dqn.artifact_schema_versions import (
    SCHEMA_MINIBATCH_TD_V1,
    require_schema_version,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that TD witness values in a minibatch artifact are "
            "consistent with the checkpoint forward-pass semantics."
        )
    )

    parser.add_argument(
        "--artifact",
        default="artifacts/minibatch_td_from_dataset.json",
        help="Path to minibatch TD artifact.",
    )

    parser.add_argument(
        "--checkpoint",
        default="models/offline_dqn_with_target_seed42_best.pt",
        help="Path to checkpoint containing online_net_state_dict and target_net_state_dict.",
    )

    return parser.parse_args()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
class QNetwork(nn.Module):
    def __init__(self, obs_dim: int = 4, hidden_dim: int = 128, n_actions: int = 2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
    
def load_networks_from_checkpoint(
    checkpoint_path: str,
) -> Tuple[QNetwork, QNetwork, Dict[str, Any]]:
    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    # Baseline checkpoints use "model_state_dict".
    # Some artifact/export code may use "online_net_state_dict".
    if "online_net_state_dict" in checkpoint:
        online_state_dict_key = "online_net_state_dict"
    elif "model_state_dict" in checkpoint:
        online_state_dict_key = "model_state_dict"
    else:
        raise KeyError(
            "checkpoint missing online network state dict. "
            "Expected either 'online_net_state_dict' or 'model_state_dict'. "
            f"Available keys: {sorted(checkpoint.keys())}"
        )

    if "target_net_state_dict" not in checkpoint:
        raise KeyError(
            "checkpoint missing target_net_state_dict. "
            f"Available keys: {sorted(checkpoint.keys())}"
        )

    online_net = QNetwork()
    target_net = QNetwork()

    online_net.load_state_dict(checkpoint[online_state_dict_key])
    target_net.load_state_dict(checkpoint["target_net_state_dict"])

    online_net.eval()
    target_net.eval()

    checkpoint["_online_state_dict_key_used"] = online_state_dict_key

    return online_net, target_net, checkpoint

def get_transition_from_item(item: Dict[str, Any]) -> Dict[str, Any]:
    if "transition" in item:
        return item["transition"]

    if "private" in item and "transition" in item["private"]:
        return item["private"]["transition"]

    raise KeyError(
        "Cannot find transition in artifact item. "
        "Expected item['transition'] or item['private']['transition']."
    )

def verify_forward_for_item(
    item: Dict[str, Any],
    online_net: QNetwork,
    target_net: QNetwork,
) -> Dict[str, Any]:
    transition = get_transition_from_item(item)

    obs = torch.tensor(transition["obs"], dtype=torch.float32).unsqueeze(0)
    next_obs = torch.tensor(transition["next_obs"], dtype=torch.float32).unsqueeze(0)
    action = int(transition["action"])

    with torch.no_grad():
        q_online_all = online_net(obs)
        q_online = q_online_all[0, action].item()

        q_next_online_all = online_net(next_obs)
        next_action = int(torch.argmax(q_next_online_all, dim=1).item())

        q_target_all = target_net(next_obs)
        q_target = q_target_all[0, next_action].item()

    q_online_fp = zk_specs.encode_fp(q_online)
    q_target_max_fp = zk_specs.encode_fp(q_target)

    claimed_q_online_fp = int(item["td_witness"]["q_online_fp"])
    claimed_next_action = int(item["td_witness"]["next_action_online"])
    claimed_q_target_max_fp = int(item["td_witness"]["q_target_max_fp"])

    q_online_match = q_online_fp == claimed_q_online_fp
    next_action_match = next_action == claimed_next_action
    q_target_match = q_target_max_fp == claimed_q_target_max_fp

    return {
        "index": item["index"],
        "q_online_real": q_online,
        "q_online_fp": q_online_fp,
        "claimed_q_online_fp": claimed_q_online_fp,
        "q_online_match": q_online_match,
        "next_action": next_action,
        "claimed_next_action": claimed_next_action,
        "next_action_match": next_action_match,
        "q_target_real": q_target,
        "q_target_max_fp": q_target_max_fp,
        "claimed_q_target_max_fp": claimed_q_target_max_fp,
        "q_target_match": q_target_match,
        "item_forward_ok": q_online_match and next_action_match and q_target_match,
    }


def main() -> None:
    args = parse_args()

    artifact = load_json(args.artifact)
    require_schema_version(
        artifact,
        SCHEMA_MINIBATCH_TD_V1,
        artifact_path=args.artifact,
    )

    public = artifact["public"]
    items = artifact["items"]

    online_net, target_net, checkpoint = load_networks_from_checkpoint(args.checkpoint)

    print("=== VERIFY FORWARD TD CONSISTENCY ===")
    print("artifact_path =", args.artifact)
    print("checkpoint_path =", args.checkpoint)
    print("schema_version =", artifact["schema_version"])
    print("dataset_root =", public["dataset_root"])
    print("batch_size =", public["batch_size"])
    print("num_items =", len(items))
    print("loss_type =", public["loss_type"])
    print("checkpoint_keys =", sorted(checkpoint.keys()))
    print("online_state_dict_key_used =", checkpoint["_online_state_dict_key_used"])
    print("online_net_loaded = True")
    print("target_net_loaded = True")
    print()
    print("=== PER-ITEM FORWARD CHECKS ===")

    all_forward_ok = True

    for item in items:
        check = verify_forward_for_item(
            item=item,
            online_net=online_net,
            target_net=target_net,
        )
        all_forward_ok = all_forward_ok and check["item_forward_ok"]

        print(
            f"item[{check['index']}] "
            f"q_online_match={check['q_online_match']} "
            f"next_action_match={check['next_action_match']} "
            f"q_target_match={check['q_target_match']} "
            f"item_forward_ok={check['item_forward_ok']}"
        )

    print()
    print("all_forward_ok =", all_forward_ok)
    print("verification_passed =", all_forward_ok)

if __name__ == "__main__":
    main()