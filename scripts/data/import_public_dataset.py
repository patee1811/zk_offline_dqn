from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import (
    RAW_EPISODES_NAME,
    canonical_json_bytes,
    hash_jsonl_transitions,
    read_jsonl,
    sha256_file,
    sha256_hex_bytes,
    write_jsonl,
    write_manifest,
)


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return to_jsonable(value.tolist())
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "item"):
        return to_jsonable(value.item())
    return value


def canonical_transition(
    *,
    episode_id: int,
    t: int,
    state: Any,
    action: Any,
    reward: Any,
    next_state: Any,
    terminated: Any,
    truncated: Any,
) -> Dict[str, Any]:
    return {
        "episode_id": int(episode_id),
        "t": int(t),
        "env_seed": None,
        "action_seed": None,
        "state": to_jsonable(state),
        "action": to_jsonable(action),
        "reward": float(reward),
        "next_state": to_jsonable(next_state),
        "terminated": bool(terminated),
        "truncated": bool(truncated),
    }


def timestep_value(value: Any, index: int) -> Any:
    if isinstance(value, dict):
        return {str(k): timestep_value(v, index) for k, v in value.items()}
    return value[index]


def import_jsonl(path: Path, max_transitions: Optional[int]) -> tuple[List[Dict[str, Any]], List[str]]:
    rows = read_jsonl(path)
    out = []
    notes: List[str] = []
    for idx, row in enumerate(rows):
        if max_transitions is not None and len(out) >= max_transitions:
            break
        if {"state", "action", "reward", "next_state"}.issubset(row):
            if "terminated" in row:
                terminated = row["terminated"]
            else:
                terminated = row.get("done", False)
                if "done" in row and "converted done to terminated=true and truncated=false" not in notes:
                    notes.append("converted done to terminated=true and truncated=false")
            truncated = row.get("truncated", False)
            out.append(
                canonical_transition(
                    episode_id=int(row.get("episode_id", 0)),
                    t=int(row.get("t", idx)),
                    state=row["state"],
                    action=row["action"],
                    reward=row["reward"],
                    next_state=row["next_state"],
                    terminated=terminated,
                    truncated=truncated,
                )
            )
        else:
            raise ValueError("source JSONL rows must use canonical transition keys")
    return out, notes


def import_npz(path: Path, max_transitions: Optional[int]) -> tuple[List[Dict[str, Any]], List[str]]:
    import numpy as np

    data = np.load(path, allow_pickle=False)
    notes: List[str] = []
    required = {"observations", "actions", "rewards"}
    missing = required - set(data.files)
    if missing:
        raise ValueError(f"source npz missing required keys: {sorted(missing)}")
    observations = data["observations"]
    actions = data["actions"]
    rewards = data["rewards"]
    if "next_observations" in data.files:
        next_observations = data["next_observations"]
        n = len(next_observations)
    elif len(observations) == len(actions) + 1:
        next_observations = observations[1:]
        observations = observations[:-1]
        n = len(next_observations)
        notes.append("derived next_observations from observations with one extra row")
    else:
        raise ValueError("source npz must contain next_observations or observations with one extra row")

    if "terminals" in data.files:
        terminals = data["terminals"]
    elif "dones" in data.files:
        terminals = data["dones"]
        notes.append("converted dones to terminated=true and truncated=false")
    else:
        terminals = np.zeros(n, dtype=bool)
        notes.append("terminals missing; defaulted to false")

    if "timeouts" in data.files:
        timeouts = data["timeouts"]
    else:
        timeouts = np.zeros(n, dtype=bool)

    n = min(n, len(actions), len(rewards), len(terminals), len(timeouts))
    if max_transitions is not None:
        n = min(n, max_transitions)
    rows = [
        canonical_transition(
            episode_id=0,
            t=i,
            state=observations[i],
            action=actions[i],
            reward=rewards[i],
            next_state=next_observations[i],
            terminated=terminals[i],
            truncated=timeouts[i],
        )
        for i in range(n)
    ]
    return rows, notes


def import_minari(dataset_id: str, max_transitions: Optional[int]) -> tuple[List[Dict[str, Any]], str, List[str]]:
    try:
        import minari
    except ImportError as exc:
        raise SystemExit(
            "Minari is not installed. Install it separately to import Minari datasets."
        ) from exc

    dataset = minari.load_dataset(dataset_id, download=True)
    env_id = getattr(dataset, "env_spec", None)
    env_id = getattr(env_id, "id", None) or dataset_id
    rows: List[Dict[str, Any]] = []
    for episode_id, episode in enumerate(dataset.iterate_episodes()):
        observations = episode.observations
        actions = episode.actions
        rewards = episode.rewards
        terminations = getattr(episode, "terminations", None)
        truncations = getattr(episode, "truncations", None)
        n = min(len(actions), len(rewards))
        for t in range(n):
            if max_transitions is not None and len(rows) >= max_transitions:
                return rows, env_id, ["imported through Minari; source file hash records source identity"]
            rows.append(
                canonical_transition(
                    episode_id=episode_id,
                    t=t,
                    state=timestep_value(observations, t),
                    action=timestep_value(actions, t),
                    reward=timestep_value(rewards, t),
                    next_state=timestep_value(observations, t + 1),
                    terminated=False if terminations is None else terminations[t],
                    truncated=False if truncations is None else truncations[t],
                )
            )
    return rows, env_id, ["imported through Minari; source file hash records source identity"]


def import_public(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    conversion_notes: List[str] = []
    source_file_hash: str
    source = ""
    source_dataset_id = ""
    env_id = args.env_id

    if args.source_jsonl:
        source_path = Path(args.source_jsonl)
        rows, conversion_notes = import_jsonl(source_path, args.max_transitions)
        source = "jsonl"
        source_dataset_id = source_path.as_posix()
        source_file_hash = sha256_file(source_path)
    elif args.source_npz:
        source_path = Path(args.source_npz)
        rows, conversion_notes = import_npz(source_path, args.max_transitions)
        source = "npz"
        source_dataset_id = source_path.as_posix()
        source_file_hash = sha256_file(source_path)
    elif args.minari_dataset_id:
        rows, env_id, conversion_notes = import_minari(args.minari_dataset_id, args.max_transitions)
        source = "minari"
        source_dataset_id = args.minari_dataset_id
        source_file_hash = sha256_hex_bytes(canonical_json_bytes({"minari_dataset_id": args.minari_dataset_id}))
    else:
        raise ValueError("one of --source-jsonl, --source-npz, or --minari-dataset-id is required")

    raw_path = out_dir / RAW_EPISODES_NAME
    write_jsonl(raw_path, rows)
    manifest = {
        "schema_version": "dataset_manifest_v1",
        "dataset_id": args.dataset_id,
        "dataset_type": "public_benchmark",
        "source": source,
        "source_dataset_id": source_dataset_id,
        "env_id": env_id,
        "env_version": None,
        "base_seed": None,
        "total_transitions": len(rows),
        "raw_trajectory_hash": hash_jsonl_transitions(raw_path),
        "source_file_hash": source_file_hash,
        "source_integrity_audit_passed": False,
        "replay_audit_passed": False,
        "reward_audit_passed": False,
        "audit_scope": "not_audited_yet",
        "audit_report_hash": None,
        "merkle_root": None,
        "conversion_notes": conversion_notes,
    }
    write_manifest(out_dir, manifest)
    print(f"dataset_id = {args.dataset_id}")
    print("dataset_type = public_benchmark")
    print(f"total_transitions = {len(rows)}")
    print(f"out_dir = {out_dir.as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-jsonl")
    group.add_argument("--source-npz")
    group.add_argument("--minari-dataset-id")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--env-id")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--max-transitions", type=int)
    args = parser.parse_args()
    if not args.env_id and not args.minari_dataset_id:
        parser.error("--env-id is required for local source imports")
    import_public(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
