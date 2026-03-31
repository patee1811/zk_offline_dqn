import argparse
import json
import pickle
import random
from pathlib import Path

import gymnasium as gym
import numpy as np


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=str, default="CartPole-v1")
    parser.add_argument("--target-transitions", type=int, default=47450)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="data/cartpole_random_matched_episodes.pkl")
    args = parser.parse_args()

    set_seed(args.seed)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = out_path.with_suffix(".summary.json")

    env = gym.make(args.env)

    episodes = []
    total_transitions = 0
    episode_returns = []
    episode_lengths = []

    ep_idx = 0
    while total_transitions < args.target_transitions:
        obs, info = env.reset(seed=args.seed + ep_idx)
        done = False

        ep_obs = []
        ep_actions = []
        ep_rewards = []
        ep_next_obs = []
        ep_dones = []

        total_reward = 0.0

        while not done:
            action = env.action_space.sample()

            next_obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            ep_obs.append(obs)
            ep_actions.append(action)
            ep_rewards.append(reward)
            ep_next_obs.append(next_obs)
            ep_dones.append(done)

            obs = next_obs
            total_reward += reward

        episode = {
            "obs": np.asarray(ep_obs, dtype=np.float32),
            "actions": np.asarray(ep_actions, dtype=np.int64),
            "rewards": np.asarray(ep_rewards, dtype=np.float32),
            "next_obs": np.asarray(ep_next_obs, dtype=np.float32),
            "dones": np.asarray(ep_dones, dtype=np.float32),
        }

        episodes.append(episode)
        ep_len = len(ep_actions)
        total_transitions += ep_len
        episode_returns.append(float(total_reward))
        episode_lengths.append(int(ep_len))

        ep_idx += 1

        if ep_idx % 100 == 0:
            print(f"episodes={ep_idx} total_transitions={total_transitions}")

    env.close()

    with open(out_path, "wb") as f:
        pickle.dump({"episodes": episodes}, f)

    summary = {
        "env": args.env,
        "seed": args.seed,
        "num_episodes": len(episodes),
        "total_transitions": total_transitions,
        "avg_return": float(np.mean(episode_returns)),
        "std_return": float(np.std(episode_returns)),
        "avg_episode_length": float(np.mean(episode_lengths)),
        "min_episode_length": int(np.min(episode_lengths)),
        "max_episode_length": int(np.max(episode_lengths)),
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved episode dataset to: {out_path}")
    print(f"Saved summary to: {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()