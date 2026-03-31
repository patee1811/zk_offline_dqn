import argparse
import json
import pickle
from pathlib import Path

import gymnasium as gym
import numpy as np
from stable_baselines3 import DQN


def collect_dataset_from_dqn(
    model_path: str,
    num_episodes: int,
    seed: int,
    epsilon: float,
):
    env = gym.make("CartPole-v1")
    model = DQN.load(model_path, env=env)

    episodes = []
    episode_returns = []
    episode_lengths = []

    rng = np.random.default_rng(seed)

    for ep in range(num_episodes):
        obs, info = env.reset(seed=seed + ep)
        env.action_space.seed(seed + ep)

        ep_obs = []
        ep_actions = []
        ep_rewards = []
        ep_next_obs = []
        ep_dones = []

        done = False
        total_reward = 0.0
        steps = 0

        while not done:
            if rng.random() < epsilon:
                action = env.action_space.sample()
            else:
                action, _ = model.predict(obs, deterministic=True)
                action = int(action)

            next_obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            ep_obs.append(obs.astype(np.float32))
            ep_actions.append(int(action))
            ep_rewards.append(float(reward))
            ep_next_obs.append(next_obs.astype(np.float32))
            ep_dones.append(bool(done))

            total_reward += reward
            steps += 1
            obs = next_obs

        episode_data = {
            "obs": np.array(ep_obs, dtype=np.float32),
            "actions": np.array(ep_actions, dtype=np.int64),
            "rewards": np.array(ep_rewards, dtype=np.float32),
            "next_obs": np.array(ep_next_obs, dtype=np.float32),
            "dones": np.array(ep_dones, dtype=np.bool_),
        }

        episodes.append(episode_data)
        episode_returns.append(total_reward)
        episode_lengths.append(steps)

    env.close()

    summary = {
        "env_name": "CartPole-v1",
        "num_episodes": num_episodes,
        "total_transitions": int(sum(episode_lengths)),
        "avg_return": float(np.mean(episode_returns)),
        "min_return": float(np.min(episode_returns)),
        "max_return": float(np.max(episode_returns)),
        "avg_length": float(np.mean(episode_lengths)),
        "min_length": int(np.min(episode_lengths)),
        "max_length": int(np.max(episode_lengths)),
        "seed": seed,
        "policy": f"dqn_epsilon_{epsilon:.2f}",
        "model_path": model_path,
    }

    return episodes, summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="models/dqn_cartpole_behavior")
    parser.add_argument("--episodes", type=int, default=200)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--epsilon", type=float, default=0.10)
    parser.add_argument(
        "--out",
        type=str,
        default="data/cartpole_dqn_eps010_episodes.pkl",
    )
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    episodes, summary = collect_dataset_from_dqn(
        model_path=args.model,
        num_episodes=args.episodes,
        seed=args.seed,
        epsilon=args.epsilon,
    )

    with open(out_path, "wb") as f:
        pickle.dump(episodes, f)

    summary_path = out_path.with_suffix(".summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("Dataset saved:", out_path)
    print("Summary saved:", summary_path)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()