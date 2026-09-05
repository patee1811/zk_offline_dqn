"""Train the behaviour policies that dataset collection samples from.

Offline RL needs data of a known skill level. This trains a DQN online against
each environment and saves two snapshots: the best one it reached (expert) and
one at roughly half that return (medium). Nothing here is proved -- the
commitment chain starts at collection, which reads these checkpoints back.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.rl_benchmarks.online_dqn import (
    OnlineCheckpoint,
    evaluate_greedy,
    train_online_dqn,
)

# MountainCar is absent on purpose: 200k steps produced exactly -200.0 at every
# one of ten checkpoints, meaning the agent never once reached the flag. Vanilla
# DQN needs reward shaping or n-step returns there, and without a skill gradient
# it cannot yield a medium/expert pair.
ENV_BUDGET = {
    "CartPole-v1": 60_000,
    "LunarLander-v3": 300_000,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--total-steps", type=int)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--eval-episodes", type=int, default=20)
    parser.add_argument("--checkpoint-every", type=int, default=2_000)
    args = parser.parse_args()

    total_steps = args.total_steps or ENV_BUDGET.get(args.env_id, 50_000)
    decay = max(1, total_steps // 3)
    checkpoints, returns = train_online_dqn(
        args.env_id,
        total_steps=total_steps,
        seed=args.seed,
        hidden_dim=args.hidden_dim,
        epsilon_decay_steps=decay,
        checkpoint_every=args.checkpoint_every,
    )
    # Rank by greedy return, not by the epsilon-greedy returns logged during
    # training: those carry exploration noise and rank the snapshots wrongly.
    import gymnasium as gym
    import numpy as np

    probe = gym.make(args.env_id)
    obs_dim = int(np.prod(probe.observation_space.shape))
    n_actions = int(probe.action_space.n)
    probe.close()

    scored = []
    for snapshot in checkpoints:
        score = evaluate_greedy(
            args.env_id,
            snapshot.state_dict,
            obs_dim=obs_dim,
            n_actions=n_actions,
            hidden_dim=args.hidden_dim,
            episodes=args.eval_episodes,
            seed=args.seed,
        )
        scored.append(
            OnlineCheckpoint(
                step=snapshot.step,
                episodes=snapshot.episodes,
                mean_return=score,
                state_dict=snapshot.state_dict,
            )
        )
        print(f"  step={snapshot.step:<7} greedy_return={score:.1f}")

    expert = max(scored, key=lambda c: c.mean_return)
    worst = min(c.mean_return for c in scored)
    midpoint = worst + (expert.mean_return - worst) / 2.0
    medium = min(scored, key=lambda c: abs(c.mean_return - midpoint))

    # Taking the best of ~30 snapshots on one seed set overfits that set, so the
    # number the paper reports is a rescore on seeds selection never saw.
    holdout = {}
    for label, snapshot in (("medium", medium), ("expert", expert)):
        holdout[label] = evaluate_greedy(
            args.env_id,
            snapshot.state_dict,
            obs_dim=obs_dim,
            n_actions=n_actions,
            hidden_dim=args.hidden_dim,
            episodes=args.eval_episodes,
            seed=args.seed + 1000,
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "env_id": args.env_id,
        "seed": args.seed,
        "total_steps": total_steps,
        "hidden_dim": args.hidden_dim,
        "episodes": len(returns),
        "eval_episodes": args.eval_episodes,
        "checkpoints": [
            {"step": c.step, "episodes": c.episodes, "greedy_return": c.mean_return}
            for c in scored
        ],
        "medium": {
            "step": medium.step,
            "greedy_return": medium.mean_return,
            "holdout_return": holdout["medium"],
        },
        "expert": {
            "step": expert.step,
            "greedy_return": expert.mean_return,
            "holdout_return": holdout["expert"],
        },
    }
    for label, snapshot in (("medium", medium), ("expert", expert)):
        torch.save(
            {
                "state_dict": snapshot.state_dict,
                "hidden_dim": args.hidden_dim,
                "env_id": args.env_id,
                "step": snapshot.step,
                "greedy_return": snapshot.mean_return,
                "holdout_return": holdout[label],
            },
            out_dir / f"{label}.pt",
        )
    (out_dir / "training_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"env_id = {args.env_id}")
    print(f"episodes = {len(returns)}")
    print(f"medium_return = {medium.mean_return:.1f} holdout {holdout['medium']:.1f} (step {medium.step})")
    print(f"expert_return = {expert.mean_return:.1f} holdout {holdout['expert']:.1f} (step {expert.step})")
    print(f"out_dir = {out_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
