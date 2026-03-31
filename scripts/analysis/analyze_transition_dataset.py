import argparse
import json
import pickle
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    args = parser.parse_args()

    path = Path(args.data)
    with open(path, "rb") as f:
        data = pickle.load(f)

    obs = data["obs"]
    actions = data["actions"]
    rewards = data["rewards"]
    next_obs = data["next_obs"]
    dones = data["dones"]

    unique_actions, counts = np.unique(actions, return_counts=True)
    action_hist = {int(a): int(c) for a, c in zip(unique_actions, counts)}

    summary = {
        "path": str(path),
        "num_transitions": int(len(obs)),
        "obs_shape": list(obs.shape),
        "actions_shape": list(actions.shape),
        "rewards_shape": list(rewards.shape),
        "next_obs_shape": list(next_obs.shape),
        "dones_shape": list(dones.shape),
        "reward_mean": float(np.mean(rewards)),
        "reward_std": float(np.std(rewards)),
        "done_ratio": float(np.mean(dones)),
        "action_hist": action_hist,
        "obs_mean": np.mean(obs, axis=0).tolist(),
        "obs_std": np.std(obs, axis=0).tolist(),
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()