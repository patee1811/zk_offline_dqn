from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any, Dict, List

import numpy as np

from .datasets import OfflineDataset


@dataclass(frozen=True)
class EvaluationSummary:
    metrics: Dict[str, Any]
    returns: List[float]
    successes: List[float]


def _make_env(dataset: OfflineDataset):
    try:
        import gymnasium as gym
    except ImportError as exc:
        raise RuntimeError("Gymnasium is required for policy evaluation") from exc

    if dataset.env_id:
        try:
            return gym.make(dataset.env_id)
        except Exception:
            pass
    minari_dataset = dataset.metadata.get("minari_dataset")
    if minari_dataset is None and dataset.metadata.get("minari_dataset_id"):
        try:
            import minari

            minari_dataset = minari.load_dataset(dataset.metadata["minari_dataset_id"], download=True)
        except Exception as exc:
            raise RuntimeError(f"evaluation environment unavailable for {dataset.name}: {exc}") from exc
    if minari_dataset is not None and hasattr(minari_dataset, "recover_environment"):
        return minari_dataset.recover_environment()
    raise RuntimeError(f"evaluation environment unavailable for {dataset.name}")


def _scalar_success(info: Dict[str, Any], env_id: str | None, episode_return: float, terminated: bool):
    if "success" in info:
        return float(np.asarray(info["success"]).reshape(-1)[0] > 0)
    if env_id == "CartPole-v1":
        return float(episode_return >= 475.0)
    if env_id == "MountainCar-v0":
        return float(terminated)
    return None


def _summary(values: List[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    return float(mean(values)), float(pstdev(values)) if len(values) > 1 else 0.0


def evaluate_policy(
    policy,
    dataset: OfflineDataset,
    *,
    seeds: List[int],
    eval_episodes: int,
) -> EvaluationSummary:
    env = _make_env(dataset)
    per_seed_returns: List[float] = []
    per_seed_successes: List[float] = []
    raw_returns: List[float] = []
    raw_successes: List[float] = []
    try:
        for seed in seeds:
            seed_returns: List[float] = []
            seed_successes: List[float] = []
            for episode in range(max(1, int(eval_episodes))):
                observation, _ = env.reset(seed=int(seed) * 1000 + episode)
                terminated = False
                truncated = False
                final_info: Dict[str, Any] = {}
                episode_return = 0.0
                while not (terminated or truncated):
                    action = policy.act(observation)
                    if hasattr(env.action_space, "low") and not dataset.action_kind == "discrete":
                        action = np.clip(action, env.action_space.low, env.action_space.high)
                    observation, reward, terminated, truncated, info = env.step(action)
                    final_info = info if isinstance(info, dict) else {}
                    episode_return += float(reward)
                seed_returns.append(episode_return)
                raw_returns.append(episode_return)
                success = _scalar_success(final_info, dataset.env_id, episode_return, bool(terminated))
                if success is not None:
                    seed_successes.append(success)
                    raw_successes.append(success)
            per_seed_returns.append(float(mean(seed_returns)))
            if seed_successes:
                per_seed_successes.append(float(mean(seed_successes)))
    finally:
        env.close()

    return_mean, return_std = _summary(per_seed_returns)
    success_mean, success_std = _summary(per_seed_successes)
    success_definition = None
    if dataset.env_id == "CartPole-v1":
        success_definition = "episode_return >= 475"
    elif dataset.env_id == "MountainCar-v0":
        success_definition = "environment termination reaches the goal"
    elif per_seed_successes:
        success_definition = "environment info['success']"
    metrics = {
        "average_return_mean": return_mean,
        "average_return_std": return_std,
        "normalized_score_mean": None,
        "normalized_score_std": None,
        "success_rate_mean": success_mean,
        "success_rate_std": success_std,
        "success_definition": success_definition,
        "num_seeds": len(seeds),
        "num_eval_episodes": int(eval_episodes),
    }
    return EvaluationSummary(metrics=metrics, returns=raw_returns, successes=raw_successes)
