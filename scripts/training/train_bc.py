import argparse
import csv
import pickle
import random
from pathlib import Path

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim


class PolicyNetwork(nn.Module):
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


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_transition_dataset(path: str):
    with open(path, "rb") as f:
        data = pickle.load(f)

    obs = data["obs"].astype(np.float32)
    actions = data["actions"].astype(np.int64)

    return obs, actions


def sample_batch(obs, actions, batch_size: int, device):
    idx = np.random.randint(0, obs.shape[0], size=batch_size)
    batch = {
        "obs": torch.tensor(obs[idx], dtype=torch.float32, device=device),
        "actions": torch.tensor(actions[idx], dtype=torch.long, device=device),
    }
    return batch


@torch.no_grad()
def evaluate_policy(policy_net, env_name: str, n_episodes: int, seed: int, device):
    env = gym.make(env_name)
    policy_net.eval()

    returns = []

    for ep in range(n_episodes):
        obs, info = env.reset(seed=seed + ep)
        done = False
        total_reward = 0.0

        while not done:
            obs_tensor = torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
            logits = policy_net(obs_tensor)
            action = int(torch.argmax(logits, dim=1).item())

            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            total_reward += reward

        returns.append(total_reward)

    env.close()
    policy_net.train()
    return float(np.mean(returns)), float(np.std(returns))


def add_suffix_to_path(path_str: str, suffix: str) -> Path:
    path = Path(path_str)
    return path.with_name(f"{path.stem}_{suffix}{path.suffix}")


def save_checkpoint(path: Path, policy_net, obs_dim, n_actions, step, seed, best_eval_return, best_step, args):
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": policy_net.state_dict(),
            "obs_dim": obs_dim,
            "n_actions": n_actions,
            "step": step,
            "seed": seed,
            "best_eval_return": best_eval_return,
            "best_step": best_step,
            "args": vars(args),
            "model_type": "bc_policy",
        },
        path,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/cartpole_dqn_eps010_transitions.pkl")
    parser.add_argument("--env", type=str, default="CartPole-v1")
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--eval-every", type=int, default=500)
    parser.add_argument("--eval-episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--patience-evals", type=int, default=4)
    parser.add_argument("--out", type=str, default="models/bc_cartpole.pt")
    parser.add_argument("--logcsv", type=str, default="logs/bc_cartpole_log.csv")
    args = parser.parse_args()

    set_seed(args.seed)

    models_dir = Path("models")
    logs_dir = Path("logs")
    models_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    best_ckpt_path = add_suffix_to_path(args.out, f"seed{args.seed}_best")
    last_ckpt_path = add_suffix_to_path(args.out, f"seed{args.seed}_last")
    logcsv_path = add_suffix_to_path(args.logcsv, f"seed{args.seed}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    obs, actions = load_transition_dataset(args.data)
    print("Loaded dataset:")
    print("  obs:", obs.shape)
    print("  actions:", actions.shape)

    obs_dim = obs.shape[1]
    n_actions = int(actions.max()) + 1

    policy_net = PolicyNetwork(obs_dim, n_actions).to(device)
    optimizer = optim.Adam(policy_net.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()

    log_rows = []
    running_losses = []

    best_eval_return = -float("inf")
    best_step = -1
    no_improve_count = 0
    stop_training = False

    for step in range(1, args.steps + 1):
        batch = sample_batch(
            obs=obs,
            actions=actions,
            batch_size=args.batch_size,
            device=device,
        )

        logits = policy_net(batch["obs"])
        loss = loss_fn(logits, batch["actions"])

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=10.0)
        optimizer.step()

        running_losses.append(float(loss.item()))

        if step % args.eval_every == 0 or step == 1 or step == args.steps:
            recent_losses = running_losses[-args.eval_every:] if len(running_losses) >= args.eval_every else running_losses
            mean_loss = float(np.mean(recent_losses)) if recent_losses else float(loss.item())

            eval_mean, eval_std = evaluate_policy(
                policy_net=policy_net,
                env_name=args.env,
                n_episodes=args.eval_episodes,
                seed=args.seed + 1000,
                device=device,
            )

            improved = eval_mean > best_eval_return
            if improved:
                best_eval_return = eval_mean
                best_step = step
                no_improve_count = 0

                save_checkpoint(
                    path=best_ckpt_path,
                    policy_net=policy_net,
                    obs_dim=obs_dim,
                    n_actions=n_actions,
                    step=step,
                    seed=args.seed,
                    best_eval_return=best_eval_return,
                    best_step=best_step,
                    args=args,
                )
            else:
                no_improve_count += 1

            row = {
                "step": step,
                "mean_loss": mean_loss,
                "eval_mean_return": eval_mean,
                "eval_std_return": eval_std,
                "best_eval_return": best_eval_return,
                "best_step": best_step,
                "is_best": int(improved),
                "no_improve_count": no_improve_count,
            }
            log_rows.append(row)

            print(
                f"step={step:5d} | "
                f"mean_loss={mean_loss:.6f} | "
                f"eval_mean_return={eval_mean:.2f} | "
                f"eval_std_return={eval_std:.2f} | "
                f"best_eval_return={best_eval_return:.2f} @ step {best_step} | "
                f"no_improve_count={no_improve_count}"
            )

            if args.patience_evals > 0 and no_improve_count >= args.patience_evals:
                print(
                    f"Early stopping triggered: no improvement for "
                    f"{args.patience_evals} evals."
                )
                stop_training = True

        if stop_training:
            break

    save_checkpoint(
        path=last_ckpt_path,
        policy_net=policy_net,
        obs_dim=obs_dim,
        n_actions=n_actions,
        step=step,
        seed=args.seed,
        best_eval_return=best_eval_return,
        best_step=best_step,
        args=args,
    )

    print(f"Saved BEST checkpoint to: {best_ckpt_path}")
    print(f"Saved LAST checkpoint to: {last_ckpt_path}")

    with open(logcsv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "step",
                "mean_loss",
                "eval_mean_return",
                "eval_std_return",
                "best_eval_return",
                "best_step",
                "is_best",
                "no_improve_count",
            ],
        )
        writer.writeheader()
        writer.writerows(log_rows)

    print(f"Saved training log to: {logcsv_path}")
    print(f"Training finished at step {step}")
    print(f"Best eval return = {best_eval_return:.2f} at step {best_step}")


if __name__ == "__main__":
    main()