import json
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.io_utils import file_sha256
from zk_offline_dqn.models import QNetwork

from zk_offline_dqn.zk_specs import (
    encode_fp,
    compute_td_target_fp,
    compute_smooth_l1_loss_fp,
)

MEMBERSHIP_ARTIFACT_PATH = "artifacts/sample_transition_membership.json"
CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"
OUTPUT_PATH = "artifacts/sample_td_artifact.json"


def main():
    with open(MEMBERSHIP_ARTIFACT_PATH, "r", encoding="utf-8") as f:
        membership = json.load(f)

    transition = membership["transition"]

    obs = torch.tensor(transition["obs"], dtype=torch.float32).unsqueeze(0)
    next_obs = torch.tensor(transition["next_obs"], dtype=torch.float32).unsqueeze(0)

    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")
    checkpoint_sha256 = file_sha256(CHECKPOINT_PATH)

    online_net = QNetwork(ckpt["obs_dim"], ckpt["n_actions"])
    online_net.load_state_dict(ckpt["model_state_dict"])
    online_net.eval()

    target_net = QNetwork(ckpt["obs_dim"], ckpt["n_actions"])
    target_net.load_state_dict(ckpt["target_net_state_dict"])
    target_net.eval()

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

    artifact = {
        "public": {
            "dataset_root": membership["dataset_root"],
            "loss_type": "smooth_l1",
            "checkpoint_sha256": checkpoint_sha256,
        },
        "transition_membership": membership,
        "td_witness": {
            "q_online_fp": q_online_fp,
            "q_target_max_fp": q_target_max_fp,
            "target_fp": target_fp,
            "loss_fp": loss_fp,
        },
        "notes": {
            "checkpoint_path": CHECKPOINT_PATH,
            "q_online_real_for_debug": q_online_real,
            "q_next_online_for_debug": q_next_online.tolist(),
            "q_next_target_for_debug": q_next_target.tolist(),
            "next_action_online_for_debug": next_action_online,
            "q_target_max_real_for_debug": q_target_max_real,
            "q_target_source": "double_dqn_target_net_at_online_argmax",
            "purpose": "single-sample TD arithmetic test using checkpoint-derived Double DQN target",
        },
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== TD SAMPLE ARTIFACT EXPORTED ===")
    print("output_path =", OUTPUT_PATH)
    print("dataset_root =", artifact["public"]["dataset_root"])
    print("loss_type =", artifact["public"]["loss_type"])
    print("checkpoint_path =", CHECKPOINT_PATH)
    print("checkpoint_sha256 =", checkpoint_sha256)
    print("reward_fp =", reward_fp)
    print("done =", done_int)
    print("q_online_real =", q_online_real)
    print("next_action_online =", next_action_online)
    print("q_target_max_real =", q_target_max_real)
    print("q_online_fp =", q_online_fp)
    print("q_target_max_fp =", q_target_max_fp)
    print("target_fp =", target_fp)
    print("loss_fp =", loss_fp)


if __name__ == "__main__":
    main()
