import argparse
import json
import pickle
from pathlib import Path

import numpy as np


def flatten_episodes(episodes):
    obs_list = []
    actions_list = []
    rewards_list = []
    next_obs_list = []
    dones_list = []
    episode_lengths = []

    for ep in episodes:
        obs_list.append(ep["obs"])
        actions_list.append(ep["actions"])
        rewards_list.append(ep["rewards"])
        next_obs_list.append(ep["next_obs"])
        dones_list.append(ep["dones"])
        episode_lengths.append(len(ep["actions"]))

    obs = np.concatenate(obs_list, axis=0).astype(np.float32)
    actions = np.concatenate(actions_list, axis=0).astype(np.int64)
    rewards = np.concatenate(rewards_list, axis=0).astype(np.float32)
    next_obs = np.concatenate(next_obs_list, axis=0).astype(np.float32)
    dones = np.concatenate(dones_list, axis=0).astype(np.float32)

    dataset = {
        "obs": obs,
        "actions": actions,
        "rewards": rewards,
        "next_obs": next_obs,
        "dones": dones,
    }

    summary = {
        "num_episodes": int(len(episodes)),
        "total_transitions": int(obs.shape[0]),
        "obs_shape": list(obs.shape),
        "actions_shape": list(actions.shape),
        "rewards_shape": list(rewards.shape),
        "next_obs_shape": list(next_obs.shape),
        "dones_shape": list(dones.shape),
        "avg_episode_length": float(np.mean(episode_lengths)),
        "min_episode_length": int(np.min(episode_lengths)),
        "max_episode_length": int(np.max(episode_lengths)),
    }

    return dataset, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    infile = Path(args.infile)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = out_path.with_suffix(".summary.json")

    with open(infile, "rb") as f:
        loaded = pickle.load(f)

    # Hỗ trợ cả 2 format:
    # 1) loaded là list episodes
    # 2) loaded là dict {"episodes": [...]}
    if isinstance(loaded, dict) and "episodes" in loaded:
        episodes = loaded["episodes"]
    else:
        episodes = loaded

    dataset, summary = flatten_episodes(episodes)

    with open(out_path, "wb") as f:
        pickle.dump(dataset, f)

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved flattened transition dataset to: {out_path}")
    print(f"Saved summary to: {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()