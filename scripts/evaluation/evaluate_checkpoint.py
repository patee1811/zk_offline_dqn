import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import gymnasium as gym
import numpy as np
import torch
from zk_offline_dqn.models import QNetwork


@torch.no_grad()
def evaluate_policy(q_net, env_name: str, n_episodes: int, seed: int, device):
    env = gym.make(env_name)
    q_net.eval()

    returns = []

    for ep in range(n_episodes):
        obs, info = env.reset(seed=seed + ep)
        done = False
        total_reward = 0.0

        while not done:
            obs_tensor = torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            q_values = q_net(obs_tensor)
            action = int(torch.argmax(q_values, dim=1).item())

            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            total_reward += reward

        returns.append(total_reward)

    env.close()
    returns = np.array(returns, dtype=np.float32)

    return {
        "mean": float(np.mean(returns)),
        "std": float(np.std(returns)),
        "min": float(np.min(returns)),
        "max": float(np.max(returns)),
        "median": float(np.median(returns)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt", type=str, required=True)
    parser.add_argument("--env", type=str, default="CartPole-v1")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt_path = Path(args.ckpt)

    payload = torch.load(ckpt_path, map_location=device)

    obs_dim = int(payload["obs_dim"])
    n_actions = int(payload["n_actions"])

    q_net = QNetwork(obs_dim, n_actions).to(device)
    q_net.load_state_dict(payload["model_state_dict"])

    stats = evaluate_policy(
        q_net=q_net,
        env_name=args.env,
        n_episodes=args.episodes,
        seed=args.seed,
        device=device,
    )

    print(f"Checkpoint: {ckpt_path}")
    if "best_eval_return" in payload:
        print(f"Saved best_eval_return: {payload['best_eval_return']}")
    if "best_step" in payload:
        print(f"Saved best_step: {payload['best_step']}")
    if "step" in payload:
        print(f"Saved at step: {payload['step']}")
    if "seed" in payload:
        print(f"Training seed: {payload['seed']}")

    print(f"Eval episodes: {args.episodes}")
    print(f"mean   = {stats['mean']:.2f}")
    print(f"std    = {stats['std']:.2f}")
    print(f"median = {stats['median']:.2f}")
    print(f"min    = {stats['min']:.2f}")
    print(f"max    = {stats['max']:.2f}")


if __name__ == "__main__":
    main()
