"""Online DQN used only to produce source policies for dataset collection.

The offline agents in `agents.py` learn from a fixed dataset. To collect data at
a chosen skill level we first need a policy of that skill, which means training
against the live environment. Nothing here is proved: this is the behaviour
policy that generates transitions, and the dataset commitment starts after it.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Tuple

import numpy as np
import torch
from torch import nn

from zk_offline_dqn.rl_benchmarks.agents import MLP


@dataclass(frozen=True)
class OnlineCheckpoint:
    """A snapshot of the online network plus the return it was scoring."""

    step: int
    episodes: int
    mean_return: float
    state_dict: Dict[str, Any]


def _greedy_action(module: nn.Module, obs: np.ndarray, device: torch.device) -> int:
    with torch.no_grad():
        values = module(torch.as_tensor(obs.reshape(1, -1), dtype=torch.float32, device=device))
    return int(values.argmax(dim=-1).item())


def train_online_dqn(
    env_id: str,
    *,
    total_steps: int,
    seed: int,
    hidden_dim: int = 64,
    buffer_size: int = 50_000,
    batch_size: int = 64,
    gamma: float = 0.99,
    learning_rate: float = 1e-3,
    target_sync_interval: int = 500,
    warmup_steps: int = 1_000,
    epsilon_start: float = 1.0,
    epsilon_end: float = 0.05,
    epsilon_decay_steps: int = 10_000,
    checkpoint_every: int = 0,
    device: str = "cpu",
) -> Tuple[List[OnlineCheckpoint], List[float]]:
    """Train a DQN against the live environment and snapshot it along the way.

    Returns the checkpoints and the per-episode returns. `checkpoint_every`
    defaults to a snapshot every tenth of training, which is what gives us a
    "medium" policy partway through and an "expert" one at the end.
    """
    import gymnasium as gym

    if checkpoint_every <= 0:
        checkpoint_every = max(1, total_steps // 10)

    torch.manual_seed(seed)
    rng = random.Random(seed)
    dev = torch.device(device)

    env = gym.make(env_id)
    obs_dim = int(np.prod(env.observation_space.shape))
    n_actions = int(env.action_space.n)

    online = MLP(obs_dim, n_actions, hidden_dim=hidden_dim).to(dev)
    target = MLP(obs_dim, n_actions, hidden_dim=hidden_dim).to(dev)
    target.load_state_dict(online.state_dict())
    optimizer = torch.optim.Adam(online.parameters(), lr=learning_rate)

    buffer: Deque[Tuple[np.ndarray, int, float, np.ndarray, float]] = deque(maxlen=buffer_size)
    checkpoints: List[OnlineCheckpoint] = []
    returns: List[float] = []

    obs, _ = env.reset(seed=seed)
    obs = np.asarray(obs, dtype=np.float32).reshape(-1)
    episode_return = 0.0
    episodes = 0

    try:
        for step in range(1, total_steps + 1):
            fraction = min(1.0, step / epsilon_decay_steps)
            epsilon = epsilon_start + fraction * (epsilon_end - epsilon_start)
            if step < warmup_steps or rng.random() < epsilon:
                action = rng.randrange(n_actions)
            else:
                action = _greedy_action(online, obs, dev)

            next_obs, reward, terminated, truncated, _ = env.step(action)
            next_obs = np.asarray(next_obs, dtype=np.float32).reshape(-1)
            buffer.append((obs, action, float(reward), next_obs, float(terminated)))
            episode_return += float(reward)
            obs = next_obs

            if terminated or truncated:
                returns.append(episode_return)
                episodes += 1
                episode_return = 0.0
                obs, _ = env.reset()
                obs = np.asarray(obs, dtype=np.float32).reshape(-1)

            if len(buffer) >= batch_size and step >= warmup_steps:
                batch = rng.sample(buffer, batch_size)
                states = torch.as_tensor(np.stack([b[0] for b in batch]), device=dev)
                actions = torch.as_tensor([b[1] for b in batch], device=dev, dtype=torch.long)
                rewards = torch.as_tensor([b[2] for b in batch], device=dev, dtype=torch.float32)
                next_states = torch.as_tensor(np.stack([b[3] for b in batch]), device=dev)
                dones = torch.as_tensor([b[4] for b in batch], device=dev, dtype=torch.float32)

                q_taken = online(states).gather(1, actions.unsqueeze(1)).squeeze(1)
                with torch.no_grad():
                    q_next = target(next_states).max(dim=1).values
                    backup = rewards + gamma * (1.0 - dones) * q_next
                loss = nn.functional.smooth_l1_loss(q_taken, backup)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            if step % target_sync_interval == 0:
                target.load_state_dict(online.state_dict())

            if step % checkpoint_every == 0:
                recent = returns[-20:] or [0.0]
                checkpoints.append(
                    OnlineCheckpoint(
                        step=step,
                        episodes=episodes,
                        mean_return=float(np.mean(recent)),
                        state_dict={k: v.detach().cpu().clone() for k, v in online.state_dict().items()},
                    )
                )
    finally:
        env.close()

    return checkpoints, returns


def evaluate_greedy(
    env_id: str,
    state_dict: Dict[str, Any],
    *,
    obs_dim: int,
    n_actions: int,
    hidden_dim: int,
    episodes: int = 20,
    seed: int = 0,
    device: str = "cpu",
) -> float:
    """Mean return of the greedy policy, with no exploration noise.

    The returns logged during training come from epsilon-greedy episodes, so
    they understate what a snapshot can actually do. Skill has to be measured
    with exploration switched off or medium and expert get picked wrong.
    """
    import gymnasium as gym

    dev = torch.device(device)
    module = MLP(obs_dim, n_actions, hidden_dim=hidden_dim).to(dev)
    module.load_state_dict(state_dict)
    module.eval()

    env = gym.make(env_id)
    totals: List[float] = []
    try:
        for episode in range(episodes):
            obs, _ = env.reset(seed=seed * 1000 + episode)
            obs = np.asarray(obs, dtype=np.float32).reshape(-1)
            total = 0.0
            for _ in range(10_000):
                action = _greedy_action(module, obs, dev)
                obs, reward, terminated, truncated, _ = env.step(action)
                obs = np.asarray(obs, dtype=np.float32).reshape(-1)
                total += float(reward)
                if terminated or truncated:
                    break
            totals.append(total)
    finally:
        env.close()
    return float(np.mean(totals))


def pick_medium_and_expert(
    checkpoints: List[OnlineCheckpoint],
) -> Tuple[OnlineCheckpoint, OnlineCheckpoint]:
    """The best snapshot is the expert; the one nearest half its return is medium.

    Taking medium by return rather than by wall-clock position matters: training
    is not monotone, so the midpoint checkpoint is not reliably mid-skill.
    """
    if not checkpoints:
        raise ValueError("no checkpoints were recorded")
    expert = max(checkpoints, key=lambda c: c.mean_return)
    worst = min(c.mean_return for c in checkpoints)
    midpoint = worst + (expert.mean_return - worst) / 2.0
    medium = min(checkpoints, key=lambda c: abs(c.mean_return - midpoint))
    return medium, expert
