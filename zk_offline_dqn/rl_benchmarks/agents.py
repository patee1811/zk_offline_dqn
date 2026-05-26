from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from .datasets import OfflineDataset, flatten_observation


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class MLP(nn.Module):
    def __init__(self, input_dim: int, output_dim: int, hidden_dim: int = 64) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return self.net(value)


@dataclass
class TorchPolicy:
    module: nn.Module
    discrete: bool
    device: torch.device
    obs_mean: np.ndarray | None = None
    obs_std: np.ndarray | None = None

    def act(self, observation: Any) -> np.ndarray | int:
        obs_array = flatten_observation(observation).astype(np.float32)
        if self.obs_mean is not None and self.obs_std is not None:
            obs_array = (obs_array - self.obs_mean) / self.obs_std
        obs = torch.as_tensor(obs_array.reshape(1, -1), device=self.device)
        with torch.no_grad():
            output = self.module(obs)
        if self.discrete:
            return int(output.argmax(dim=-1).item())
        return output.detach().cpu().numpy()[0]


def _device(value: str | torch.device) -> torch.device:
    return value if isinstance(value, torch.device) else torch.device(value)


def _batch(dataset: OfflineDataset, batch_size: int, device: torch.device) -> Dict[str, torch.Tensor]:
    indices = torch.randint(dataset.size, (min(batch_size, dataset.size),))
    idx = indices.cpu().numpy()
    return {
        "obs": torch.as_tensor(dataset.observations[idx], dtype=torch.float32, device=device),
        "actions": torch.as_tensor(dataset.actions[idx], device=device),
        "rewards": torch.as_tensor(dataset.rewards[idx], dtype=torch.float32, device=device),
        "next_obs": torch.as_tensor(dataset.next_observations[idx], dtype=torch.float32, device=device),
        "done": torch.as_tensor(
            np.maximum(dataset.terminated[idx], dataset.truncated[idx]),
            dtype=torch.float32,
            device=device,
        ),
    }


def _obs_normalizer(dataset: OfflineDataset) -> tuple[np.ndarray, np.ndarray]:
    mean = dataset.observations.mean(axis=0, dtype=np.float64).astype(np.float32)
    std = dataset.observations.std(axis=0, dtype=np.float64).astype(np.float32)
    return mean, np.maximum(std, 1e-6)


def _normalize(batch: torch.Tensor, mean: torch.Tensor, std: torch.Tensor) -> torch.Tensor:
    return (batch - mean) / std


def _finite(loss: torch.Tensor, name: str) -> None:
    if not bool(torch.isfinite(loss).all()):
        raise FloatingPointError(f"{name} became NaN or Inf")


def train_behavior_cloning_discrete(
    dataset: OfflineDataset,
    *,
    train_steps: int,
    seed: int,
    device: str = "cpu",
    batch_size: int = 64,
    learning_rate: float = 3e-4,
) -> TorchPolicy:
    if dataset.action_kind != "discrete":
        raise ValueError("discrete BC requires scalar integer actions")
    seed_everything(seed)
    target_device = _device(device)
    policy = MLP(dataset.observation_dim, dataset.action_dim).to(target_device)
    optimizer = torch.optim.Adam(policy.parameters(), lr=learning_rate)
    policy.train()
    for _ in range(max(1, int(train_steps))):
        batch = _batch(dataset, batch_size, target_device)
        logits = policy(batch["obs"])
        loss = F.cross_entropy(logits, batch["actions"].long())
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    policy.eval()
    return TorchPolicy(policy, discrete=True, device=target_device)


def cql_lite_loss(q_values: torch.Tensor, actions: torch.Tensor, alpha: float) -> torch.Tensor:
    selected = q_values.gather(1, actions.long().view(-1, 1)).squeeze(1)
    return float(alpha) * (torch.logsumexp(q_values, dim=1) - selected).mean()


def train_offline_q(
    dataset: OfflineDataset,
    *,
    algorithm: str,
    train_steps: int,
    seed: int,
    device: str = "cpu",
    batch_size: int = 64,
    learning_rate: float = 3e-4,
    gamma: float = 0.99,
    target_update_interval: int = 100,
    cql_alpha: float = 0.1,
) -> TorchPolicy:
    if dataset.action_kind != "discrete":
        raise ValueError("offline Q baselines require scalar integer actions")
    if algorithm not in {"offline_dqn", "double_dqn", "cql_lite"}:
        raise ValueError(f"unsupported Q baseline: {algorithm}")
    seed_everything(seed)
    target_device = _device(device)
    online = MLP(dataset.observation_dim, dataset.action_dim).to(target_device)
    target = MLP(dataset.observation_dim, dataset.action_dim).to(target_device)
    target.load_state_dict(online.state_dict())
    optimizer = torch.optim.Adam(online.parameters(), lr=learning_rate)

    for step in range(max(1, int(train_steps))):
        batch = _batch(dataset, batch_size, target_device)
        q_values = online(batch["obs"])
        selected_q = q_values.gather(1, batch["actions"].long().view(-1, 1)).squeeze(1)
        with torch.no_grad():
            if algorithm == "double_dqn":
                next_actions = online(batch["next_obs"]).argmax(dim=1, keepdim=True)
                next_q = target(batch["next_obs"]).gather(1, next_actions).squeeze(1)
            else:
                next_q = target(batch["next_obs"]).max(dim=1).values
            td_target = batch["rewards"] + gamma * (1.0 - batch["done"]) * next_q
        loss = F.smooth_l1_loss(selected_q, td_target)
        if algorithm == "cql_lite":
            loss = loss + cql_lite_loss(q_values, batch["actions"], cql_alpha)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(online.parameters(), 10.0)
        optimizer.step()
        if (step + 1) % max(1, target_update_interval) == 0:
            target.load_state_dict(online.state_dict())
    online.eval()
    return TorchPolicy(online, discrete=True, device=target_device)


def train_behavior_cloning_continuous(
    dataset: OfflineDataset,
    *,
    train_steps: int,
    seed: int,
    device: str = "cpu",
    batch_size: int = 64,
    learning_rate: float = 3e-4,
) -> TorchPolicy:
    if dataset.action_kind != "continuous":
        raise ValueError("continuous BC requires vector actions")
    seed_everything(seed)
    target_device = _device(device)
    actor = MLP(dataset.observation_dim, dataset.action_dim).to(target_device)
    optimizer = torch.optim.Adam(actor.parameters(), lr=learning_rate)
    obs_mean_np, obs_std_np = _obs_normalizer(dataset)
    obs_mean = torch.as_tensor(obs_mean_np, dtype=torch.float32, device=target_device)
    obs_std = torch.as_tensor(obs_std_np, dtype=torch.float32, device=target_device)
    for _ in range(max(1, int(train_steps))):
        batch = _batch(dataset, batch_size, target_device)
        loss = F.mse_loss(actor(_normalize(batch["obs"], obs_mean, obs_std)), batch["actions"].float())
        _finite(loss, "continuous BC loss")
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(actor.parameters(), 10.0)
        optimizer.step()
    actor.eval()
    return TorchPolicy(
        actor,
        discrete=False,
        device=target_device,
        obs_mean=obs_mean_np,
        obs_std=obs_std_np,
    )


class ContinuousQ(nn.Module):
    def __init__(self, observation_dim: int, action_dim: int) -> None:
        super().__init__()
        self.net = MLP(observation_dim + action_dim, 1)

    def forward(self, observations: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        return self.net(torch.cat([observations, actions], dim=1)).squeeze(1)


def _train_iql_lite_once(
    dataset: OfflineDataset,
    *,
    train_steps: int,
    seed: int,
    device: str = "cpu",
    batch_size: int = 64,
    learning_rate: float = 3e-4,
    gamma: float = 0.99,
    expectile: float = 0.7,
    beta: float = 3.0,
    max_actor_weight: float = 100.0,
) -> TorchPolicy:
    if dataset.action_kind != "continuous":
        raise ValueError("IQL-lite requires vector actions")
    seed_everything(seed)
    target_device = _device(device)
    actor = MLP(dataset.observation_dim, dataset.action_dim).to(target_device)
    q_net = ContinuousQ(dataset.observation_dim, dataset.action_dim).to(target_device)
    value = MLP(dataset.observation_dim, 1).to(target_device)
    q_optimizer = torch.optim.Adam(q_net.parameters(), lr=learning_rate)
    v_optimizer = torch.optim.Adam(value.parameters(), lr=learning_rate)
    actor_optimizer = torch.optim.Adam(actor.parameters(), lr=learning_rate)
    obs_mean_np, obs_std_np = _obs_normalizer(dataset)
    obs_mean = torch.as_tensor(obs_mean_np, dtype=torch.float32, device=target_device)
    obs_std = torch.as_tensor(obs_std_np, dtype=torch.float32, device=target_device)

    for _ in range(max(1, int(train_steps))):
        batch = _batch(dataset, batch_size, target_device)
        obs = _normalize(batch["obs"], obs_mean, obs_std)
        next_obs = _normalize(batch["next_obs"], obs_mean, obs_std)
        actions = batch["actions"].float()
        with torch.no_grad():
            value_next = value(next_obs).squeeze(1)
            q_target = batch["rewards"] + gamma * (1.0 - batch["done"]) * value_next
        q_pred = q_net(obs, actions)
        q_loss = F.mse_loss(q_pred, q_target)
        _finite(q_loss, "IQL-lite Q loss")
        q_optimizer.zero_grad()
        q_loss.backward()
        torch.nn.utils.clip_grad_norm_(q_net.parameters(), 10.0)
        q_optimizer.step()

        with torch.no_grad():
            q_detached = q_net(obs, actions)
        v_pred = value(obs).squeeze(1)
        diff = q_detached - v_pred
        weight = torch.where(diff >= 0.0, expectile, 1.0 - expectile)
        v_loss = (weight * diff.square()).mean()
        _finite(v_loss, "IQL-lite value loss")
        v_optimizer.zero_grad()
        v_loss.backward()
        torch.nn.utils.clip_grad_norm_(value.parameters(), 10.0)
        v_optimizer.step()

        with torch.no_grad():
            advantage = q_net(obs, actions) - value(obs).squeeze(1)
            actor_weight = torch.exp((beta * advantage).clamp(max=10.0)).clamp(
                max=max_actor_weight
            )
        actor_loss = (actor_weight[:, None] * (actor(obs) - actions).square()).mean()
        _finite(actor_loss, "IQL-lite actor loss")
        actor_optimizer.zero_grad()
        actor_loss.backward()
        torch.nn.utils.clip_grad_norm_(actor.parameters(), 10.0)
        actor_optimizer.step()
    actor.eval()
    return TorchPolicy(
        actor,
        discrete=False,
        device=target_device,
        obs_mean=obs_mean_np,
        obs_std=obs_std_np,
    )


def train_iql_lite(
    dataset: OfflineDataset,
    *,
    train_steps: int,
    seed: int,
    device: str = "cpu",
    batch_size: int = 64,
    learning_rate: float = 3e-4,
    gamma: float = 0.99,
    expectile: float = 0.7,
    beta: float = 3.0,
) -> TorchPolicy:
    attempts = [
        (learning_rate, beta, 100.0),
        (min(learning_rate, 1e-4), min(beta, 1.0), 20.0),
    ]
    failures = []
    for attempt_learning_rate, attempt_beta, max_actor_weight in attempts:
        try:
            return _train_iql_lite_once(
                dataset,
                train_steps=train_steps,
                seed=seed,
                device=device,
                batch_size=batch_size,
                learning_rate=attempt_learning_rate,
                gamma=gamma,
                expectile=expectile,
                beta=attempt_beta,
                max_actor_weight=max_actor_weight,
            )
        except FloatingPointError as exc:
            failures.append(str(exc))
    raise FloatingPointError("IQL-lite stabilization failed: " + "; ".join(failures))
