import json
import hashlib
import torch
import torch.nn as nn

from zk_offline_dqn.zk_specs import (
    encode_fp,
    compute_td_target_fp,
    compute_smooth_l1_loss_fp,
)

TEMPLATE_ARTIFACT_PATH = "artifacts/sample_minibatch_td_artifact.json"
CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"
OUTPUT_PATH = "artifacts/sample_minibatch_td_artifact.json"


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


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(TEMPLATE_ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu")
    checkpoint_sha256 = file_sha256(CHECKPOINT_PATH)

    online_net = QNetwork(ckpt["obs_dim"], ckpt["n_actions"])
    online_net.load_state_dict(ckpt["model_state_dict"])
    online_net.eval()

    target_net = QNetwork(ckpt["obs_dim"], ckpt["n_actions"])
    target_net.load_state_dict(ckpt["target_net_state_dict"])
    target_net.eval()

    total_loss_fp = 0
    batch_size = int(artifact["public"]["batch_size"])

    for item in artifact["items"]:
        transition = item["transition"]

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

        item["td_witness"] = {
            "q_online_fp": q_online_fp,
            "q_target_max_fp": q_target_max_fp,
            "target_fp": target_fp,
            "loss_fp": loss_fp,
        }

        item["debug"] = {
            "q_online_real_for_debug": q_online_real,
            "q_next_online_for_debug": q_next_online.tolist(),
            "q_next_target_for_debug": q_next_target.tolist(),
            "next_action_online_for_debug": next_action_online,
            "q_target_max_real_for_debug": q_target_max_real,
        }

        total_loss_fp += loss_fp

    batch_loss_fp = total_loss_fp // batch_size

    artifact["public"]["loss_type"] = "smooth_l1"
    artifact["public"]["batch_loss_fp"] = batch_loss_fp
    artifact["public"]["checkpoint_sha256"] = checkpoint_sha256

    artifact["notes"] = {
        "checkpoint_path": CHECKPOINT_PATH,
        "q_target_source": "double_dqn_target_net_at_online_argmax",
        "purpose": "minibatch TD arithmetic test using checkpoint-derived Double DQN target",
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== MINIBATCH TD ARTIFACT EXPORTED ===")
    print("output_path =", OUTPUT_PATH)
    print("dataset_root =", artifact["public"]["dataset_root"])
    print("checkpoint_path =", CHECKPOINT_PATH)
    print("checkpoint_sha256 =", checkpoint_sha256)
    print("batch_size =", batch_size)
    print("batch_loss_fp =", batch_loss_fp)
    print()
    print("=== PER-ITEM SUMMARY ===")
    for i, item in enumerate(artifact["items"]):
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