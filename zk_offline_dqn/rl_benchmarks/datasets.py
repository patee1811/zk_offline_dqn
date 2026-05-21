from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

from zk_offline_dqn.data_pipeline import RAW_EPISODES_NAME, load_manifest, read_jsonl


SELF_COLLECTED_DATASETS = {
    "cartpole": ("cartpole-random-v1", "CartPole-v1"),
    "mountaincar": ("mountaincar-random-v1", "MountainCar-v0"),
}
MINARI_DATASETS = {
    "minari-pointmaze-umaze": (
        "minari-pointmaze-umaze-v2",
        "D4RL/pointmaze/umaze-v2",
    ),
    "minari-pointmaze-umaze-dense": (
        "minari-pointmaze-umaze-dense-v2",
        "D4RL/pointmaze/umaze-dense-v2",
    ),
    "minari-pointmaze-medium": (
        "minari-pointmaze-medium-v2",
        "D4RL/pointmaze/medium-v2",
    ),
    "minari-pointmaze-open": (
        "minari-pointmaze-open-v2",
        "D4RL/pointmaze/open-v2",
    ),
}


class DatasetUnavailable(RuntimeError):
    """Raised when a requested benchmark dataset cannot be loaded."""


@dataclass(frozen=True)
class OfflineDataset:
    name: str
    source_type: str
    env_id: str | None
    observations: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    next_observations: np.ndarray
    terminated: np.ndarray
    truncated: np.ndarray
    metadata: Dict[str, Any]

    @property
    def size(self) -> int:
        return int(self.rewards.shape[0])

    @property
    def observation_dim(self) -> int:
        return int(self.observations.shape[1])

    @property
    def action_kind(self) -> str:
        return str(self.metadata.get("action_kind", "discrete"))

    @property
    def action_dim(self) -> int:
        if self.action_kind == "discrete":
            return int(self.metadata["num_actions"])
        return int(self.actions.shape[1])

    def subset(self, max_transitions: int | None) -> "OfflineDataset":
        if max_transitions is None or max_transitions >= self.size:
            return self
        end = max(1, int(max_transitions))
        metadata = dict(self.metadata)
        metadata["loaded_transitions"] = end
        return replace(
            self,
            observations=self.observations[:end],
            actions=self.actions[:end],
            rewards=self.rewards[:end],
            next_observations=self.next_observations[:end],
            terminated=self.terminated[:end],
            truncated=self.truncated[:end],
            metadata=metadata,
        )


def _flat_float(value: Any) -> np.ndarray:
    if isinstance(value, dict):
        parts = [_flat_float(value[key]) for key in sorted(value)]
        if not parts:
            raise ValueError("observation dictionary is empty")
        return np.concatenate(parts, axis=0)
    array = np.asarray(value, dtype=np.float32)
    return array.reshape(-1)


def _source_type(manifest: Dict[str, Any]) -> str:
    if manifest.get("dataset_type") == "public_benchmark":
        return "public_source_integrity"
    return "audited_self_collected"


def _rows_to_dataset(
    *,
    name: str,
    env_id: str | None,
    source_type: str,
    rows: Sequence[Dict[str, Any]],
    metadata: Dict[str, Any],
) -> OfflineDataset:
    if not rows:
        raise DatasetUnavailable(f"{name} has no transitions")

    observations = np.stack([_flat_float(row["state"]) for row in rows]).astype(np.float32)
    next_observations = np.stack([_flat_float(row["next_state"]) for row in rows]).astype(
        np.float32
    )
    rewards = np.asarray([float(row["reward"]) for row in rows], dtype=np.float32)
    terminated = np.asarray([bool(row.get("terminated", False)) for row in rows], dtype=np.float32)
    truncated = np.asarray([bool(row.get("truncated", False)) for row in rows], dtype=np.float32)

    actions = [row["action"] for row in rows]
    discrete = all(np.asarray(action).ndim == 0 and isinstance(action, (int, np.integer)) for action in actions)
    dataset_metadata = dict(metadata)
    dataset_metadata["loaded_transitions"] = len(rows)
    if discrete:
        action_array = np.asarray(actions, dtype=np.int64)
        dataset_metadata["action_kind"] = "discrete"
        dataset_metadata["num_actions"] = max(1, int(action_array.max()) + 1)
    else:
        action_array = np.stack([_flat_float(action) for action in actions]).astype(np.float32)
        dataset_metadata["action_kind"] = "continuous"

    return OfflineDataset(
        name=name,
        source_type=source_type,
        env_id=env_id,
        observations=observations,
        actions=action_array,
        rewards=rewards,
        next_observations=next_observations,
        terminated=terminated,
        truncated=truncated,
        metadata=dataset_metadata,
    )


def load_committed_dataset(dataset_dir: str | Path, max_transitions: int | None = None) -> OfflineDataset:
    dataset_dir = Path(dataset_dir)
    raw_path = dataset_dir / RAW_EPISODES_NAME
    if not raw_path.exists():
        raise DatasetUnavailable(f"missing canonical replay rows at {raw_path}")
    try:
        manifest = load_manifest(dataset_dir)
    except FileNotFoundError as exc:
        raise DatasetUnavailable(f"missing dataset manifest at {dataset_dir}") from exc

    rows = read_jsonl(raw_path)
    if max_transitions is not None:
        rows = rows[: max(1, int(max_transitions))]
    name = str(manifest.get("dataset_id") or dataset_dir.name)
    metadata = {
        "dataset_dir": dataset_dir.as_posix(),
        "manifest": manifest,
        "minari_dataset_id": manifest.get("source_dataset_id"),
    }
    return _rows_to_dataset(
        name=name,
        env_id=manifest.get("env_id"),
        source_type=_source_type(manifest),
        rows=rows,
        metadata=metadata,
    )


def _candidate_dirs(dataset_root: Path, dataset_name: str) -> Iterable[Path]:
    if dataset_name in SELF_COLLECTED_DATASETS:
        yield dataset_root / SELF_COLLECTED_DATASETS[dataset_name][0]
    elif dataset_name in MINARI_DATASETS:
        prefix, _ = MINARI_DATASETS[dataset_name]
        yield dataset_root / prefix
        yield from sorted(dataset_root.glob(f"{prefix}*"))
    else:
        yield dataset_root / dataset_name


def _rows_from_minari_episode(episode: Any) -> List[Dict[str, Any]]:
    observations = getattr(episode, "observations", None)
    actions = getattr(episode, "actions", None)
    rewards = getattr(episode, "rewards", None)
    terminations = getattr(episode, "terminations", None)
    truncations = getattr(episode, "truncations", None)
    if observations is None or actions is None or rewards is None:
        raise DatasetUnavailable("Minari episode does not expose transitions")
    rows: List[Dict[str, Any]] = []
    for index in range(len(actions)):
        rows.append(
            {
                "state": observations[index],
                "action": actions[index],
                "reward": rewards[index],
                "next_state": observations[index + 1],
                "terminated": False if terminations is None else bool(terminations[index]),
                "truncated": False if truncations is None else bool(truncations[index]),
            }
        )
    return rows


def _load_minari_direct(dataset_name: str, max_transitions: int | None) -> OfflineDataset:
    try:
        import minari
    except ImportError as exc:
        raise DatasetUnavailable("Minari is unavailable") from exc

    _, source_id = MINARI_DATASETS[dataset_name]
    try:
        minari_dataset = minari.load_dataset(source_id, download=True)
    except Exception as exc:
        raise DatasetUnavailable(f"Minari load failed for {source_id}: {exc}") from exc

    rows: List[Dict[str, Any]] = []
    try:
        episodes = minari_dataset.iterate_episodes()
    except AttributeError as exc:
        raise DatasetUnavailable("Minari dataset does not expose iterate_episodes") from exc
    for episode in episodes:
        rows.extend(_rows_from_minari_episode(episode))
        if max_transitions is not None and len(rows) >= max_transitions:
            rows = rows[: max(1, int(max_transitions))]
            break
    metadata = {
        "minari_dataset_id": source_id,
        "minari_dataset": minari_dataset,
        "source_dataset_id": source_id,
    }
    return _rows_to_dataset(
        name=MINARI_DATASETS[dataset_name][0],
        env_id=None,
        source_type="public_source_integrity",
        rows=rows,
        metadata=metadata,
    )


def load_named_dataset(
    dataset_name: str,
    dataset_root: str | Path,
    *,
    max_transitions: int | None = None,
    allow_minari_download: bool = True,
) -> OfflineDataset:
    root = Path(dataset_root)
    for candidate in _candidate_dirs(root, dataset_name):
        if (candidate / RAW_EPISODES_NAME).exists():
            return load_committed_dataset(candidate, max_transitions=max_transitions)
    if dataset_name in MINARI_DATASETS and allow_minari_download:
        return _load_minari_direct(dataset_name, max_transitions)
    raise DatasetUnavailable(f"dataset {dataset_name!r} is unavailable under {root}")


def ensure_self_collected_dataset(
    dataset_name: str,
    dataset_root: str | Path,
    *,
    target_transitions: int,
    base_seed: int,
) -> Path:
    if dataset_name not in SELF_COLLECTED_DATASETS:
        raise ValueError(f"{dataset_name} is not a self-collected discrete benchmark")
    dataset_id, env_id = SELF_COLLECTED_DATASETS[dataset_name]
    out_dir = Path(dataset_root) / dataset_id
    if (out_dir / RAW_EPISODES_NAME).exists():
        return out_dir

    from argparse import Namespace

    from scripts.data.audit_replay_dataset import audit_dataset
    from scripts.data.collect_audited_dataset import collect
    from scripts.data.commit_audited_dataset import commit_dataset

    mean_random_horizon = 50 if dataset_name == "cartpole" else 200
    num_episodes = max(8, math.ceil(target_transitions / mean_random_horizon) * 2)
    collect(
        Namespace(
            env_id=env_id,
            dataset_id=dataset_id,
            policy="random",
            num_episodes=num_episodes,
            base_seed=base_seed,
            max_steps_per_episode=500 if dataset_name == "cartpole" else 200,
            out_dir=str(out_dir),
            audit_after_collect=False,
            atol=1e-6,
        )
    )
    if not audit_dataset(out_dir):
        raise DatasetUnavailable(f"audited collection failed for {dataset_id}")
    commit_dataset(out_dir)
    return out_dir
