from __future__ import annotations

import math
import tarfile
from argparse import Namespace
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

from zk_offline_dqn.data_pipeline import (
    AUDIT_REPORT_NAME,
    MERKLE_TREE_NAME,
    RAW_EPISODES_NAME,
    load_manifest,
    read_jsonl,
    sha256_file,
    verify_dataset_commitment,
)


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
OBSERVATION_FLATTEN_ORDER = ("observation", "achieved_goal", "desired_goal")


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
    infos: List[Dict[str, Any]] | None = None

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

    @property
    def terminations(self) -> np.ndarray:
        return self.terminated

    @property
    def truncations(self) -> np.ndarray:
        return self.truncated

    @property
    def dones(self) -> np.ndarray:
        return np.maximum(self.terminated, self.truncated)

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
            infos=None if self.infos is None else self.infos[:end],
        )


def flatten_observation(value: Any) -> np.ndarray:
    if isinstance(value, dict):
        ordered_keys = [key for key in OBSERVATION_FLATTEN_ORDER if key in value]
        ordered_keys.extend(sorted(key for key in value if key not in ordered_keys))
        if not ordered_keys:
            raise ValueError("observation dictionary is empty")
        parts = [flatten_observation(value[key]) for key in ordered_keys]
        return np.concatenate(parts, axis=0)
    array = np.asarray(value, dtype=np.float32)
    return array.reshape(-1)


def _source_type(manifest: Dict[str, Any]) -> str:
    if manifest.get("dataset_type") == "public_benchmark":
        return "public_source_integrity"
    return "audited_self_collected"


def public_dataset_id(dataset_family: str, size: int) -> str:
    if dataset_family not in MINARI_DATASETS:
        raise ValueError(f"unsupported public dataset family: {dataset_family}")
    return f"{MINARI_DATASETS[dataset_family][0]}-{int(size)}"


def public_family_for_dataset_id(dataset_id: str) -> str | None:
    for family, (prefix, _) in MINARI_DATASETS.items():
        if dataset_id == prefix or dataset_id.startswith(f"{prefix}-"):
            return family
    return None


def dataset_family_for_name(dataset_name: str) -> str:
    if dataset_name in SELF_COLLECTED_DATASETS:
        return dataset_name
    for family, (dataset_id, _) in SELF_COLLECTED_DATASETS.items():
        if dataset_name == dataset_id:
            return family
    public_family = public_family_for_dataset_id(dataset_name)
    if public_family is not None:
        return public_family
    return dataset_name


def source_id_for_public_dataset(dataset_id: str) -> str:
    family = public_family_for_dataset_id(dataset_id)
    if family is None:
        raise ValueError(f"{dataset_id} is not a configured Minari/D4RL PointMaze subset")
    return MINARI_DATASETS[family][1]


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

    observations = np.stack([flatten_observation(row["state"]) for row in rows]).astype(np.float32)
    next_observations = np.stack(
        [flatten_observation(row["next_state"]) for row in rows]
    ).astype(np.float32)
    rewards = np.asarray([float(row["reward"]) for row in rows], dtype=np.float32)
    terminated = np.asarray([bool(row.get("terminated", False)) for row in rows], dtype=np.float32)
    truncated = np.asarray([bool(row.get("truncated", False)) for row in rows], dtype=np.float32)

    actions = [row["action"] for row in rows]
    discrete = all(
        np.asarray(action).ndim == 0 and isinstance(action, (int, np.integer))
        for action in actions
    )
    dataset_metadata = dict(metadata)
    dataset_metadata["loaded_transitions"] = len(rows)
    dataset_metadata["observation_flatten_order"] = list(OBSERVATION_FLATTEN_ORDER)
    if discrete:
        action_array = np.asarray(actions, dtype=np.int64)
        dataset_metadata["action_kind"] = "discrete"
        dataset_metadata["num_actions"] = max(1, int(action_array.max()) + 1)
    else:
        action_array = np.stack([flatten_observation(action) for action in actions]).astype(np.float32)
        dataset_metadata["action_kind"] = "continuous"

    infos = []
    for row in rows:
        info = row.get("info", row.get("infos", {}))
        infos.append(info if isinstance(info, dict) else {})

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
        infos=infos,
    )


def validate_phase2_dataset(dataset_dir: str | Path) -> tuple[bool, List[str]]:
    dataset_dir = Path(dataset_dir)
    required = [RAW_EPISODES_NAME, AUDIT_REPORT_NAME, MERKLE_TREE_NAME, "dataset_manifest.json"]
    missing = [name for name in required if not (dataset_dir / name).exists()]
    if missing:
        return False, [f"missing required Phase 2 file: {name}" for name in missing]
    return verify_dataset_commitment(dataset_dir)


def load_committed_dataset(
    dataset_dir: str | Path,
    max_transitions: int | None = None,
) -> OfflineDataset:
    dataset_dir = Path(dataset_dir)
    ok, errors = validate_phase2_dataset(dataset_dir)
    if not ok:
        raise DatasetUnavailable(
            f"invalid Phase 2 dataset at {dataset_dir}: " + "; ".join(errors)
        )

    manifest = load_manifest(dataset_dir)
    rows = read_jsonl(dataset_dir / RAW_EPISODES_NAME)
    if max_transitions is not None:
        rows = rows[: max(1, int(max_transitions))]

    merkle_tree = _read_json(dataset_dir / MERKLE_TREE_NAME)
    name = str(manifest.get("dataset_id") or dataset_dir.name)
    metadata = {
        "dataset_dir": dataset_dir.as_posix(),
        "dataset_family": dataset_family_for_name(name),
        "manifest": manifest,
        "minari_dataset_id": manifest.get("source_dataset_id"),
        "source_dataset_id": manifest.get("source_dataset_id"),
        "manifest_hash": merkle_tree.get("manifest_hash"),
        "audit_report_hash": manifest.get("audit_report_hash") or sha256_file(dataset_dir / AUDIT_REPORT_NAME),
        "dataset_root": merkle_tree.get("dataset_root"),
        "merkle_root": manifest.get("merkle_root") or merkle_tree.get("dataset_root"),
        "phase2_dataset_provenance": "reused_existing_artifact",
    }
    return _rows_to_dataset(
        name=name,
        env_id=manifest.get("env_id"),
        source_type=_source_type(manifest),
        rows=rows,
        metadata=metadata,
    )


def _read_json(path: Path) -> Dict[str, Any]:
    import json

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise DatasetUnavailable(f"{path} must contain a JSON object")
    return data


def _candidate_dirs(dataset_root: Path, dataset_name: str) -> Iterable[Path]:
    if dataset_name in SELF_COLLECTED_DATASETS:
        yield dataset_root / SELF_COLLECTED_DATASETS[dataset_name][0]
        return
    if dataset_name in MINARI_DATASETS:
        prefix, _ = MINARI_DATASETS[dataset_name]
        yield dataset_root / prefix
        yield from sorted(dataset_root.glob(f"{prefix}-*"))
        return
    yield dataset_root / dataset_name


def load_named_dataset(
    dataset_name: str,
    dataset_root: str | Path,
    *,
    max_transitions: int | None = None,
    allow_minari_download: bool = False,
) -> OfflineDataset:
    del allow_minari_download
    root = Path(dataset_root)
    errors: List[str] = []
    for candidate in _candidate_dirs(root, dataset_name):
        if not candidate.exists():
            continue
        try:
            return load_committed_dataset(candidate, max_transitions=max_transitions)
        except DatasetUnavailable as exc:
            errors.append(str(exc))
    if errors:
        raise DatasetUnavailable("; ".join(errors))
    raise DatasetUnavailable(
        f"Phase 2 dataset {dataset_name!r} is unavailable under {root}; "
        "run extraction or the Phase 2 pipeline before benchmarking"
    )


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
    ok, _ = validate_phase2_dataset(out_dir)
    if ok:
        return out_dir

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


def regenerate_public_phase2_dataset(dataset_id: str, dataset_root: str | Path) -> Path:
    out_dir = Path(dataset_root) / dataset_id
    ok, _ = validate_phase2_dataset(out_dir)
    if ok:
        return out_dir

    size = _dataset_size_suffix(dataset_id)
    from scripts.data.audit_replay_dataset import audit_dataset
    from scripts.data.commit_audited_dataset import commit_dataset
    from scripts.data.import_public_dataset import import_public

    import_public(
        Namespace(
            source_jsonl=None,
            source_npz=None,
            minari_dataset_id=source_id_for_public_dataset(dataset_id),
            dataset_id=dataset_id,
            env_id=None,
            out_dir=str(out_dir),
            max_transitions=size,
        )
    )
    if not audit_dataset(out_dir):
        raise DatasetUnavailable(f"source-integrity audit failed for {dataset_id}")
    commit_dataset(out_dir)
    return out_dir


def _dataset_size_suffix(dataset_id: str) -> int:
    try:
        return int(dataset_id.rsplit("-", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"public dataset id must end in a transition count: {dataset_id}") from exc


def extract_phase2_datasets_from_tarball(
    tarball: str | Path,
    dataset_root: str | Path,
    dataset_ids: Iterable[str],
) -> List[str]:
    tarball = Path(tarball)
    if not tarball.exists():
        return []
    wanted = set(dataset_ids)
    extracted: set[str] = set()
    root = Path(dataset_root)
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            dataset_id, filename = _phase2_tar_member_dataset_file(member.name)
            if dataset_id not in wanted or filename is None:
                continue
            stream = archive.extractfile(member)
            if stream is None:
                continue
            target = root / dataset_id / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("wb") as handle:
                handle.write(stream.read())
            extracted.add(dataset_id)
    return sorted(extracted)


def _phase2_tar_member_dataset_file(member_name: str) -> tuple[str | None, str | None]:
    parts = PurePosixPath(member_name).parts
    try:
        datasets_index = parts.index("datasets")
    except ValueError:
        return None, None
    if len(parts) != datasets_index + 3:
        return None, None
    return parts[datasets_index + 1], parts[datasets_index + 2]
