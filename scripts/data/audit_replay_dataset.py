from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import (
    AUDIT_REPORT_NAME,
    COLLECTION_LOG_NAME,
    RAW_EPISODES_NAME,
    hash_jsonl_transitions,
    load_manifest,
    read_jsonl,
    validate_collection_log,
    write_audit_report,
    write_manifest,
)


def close_enough(left: Any, right: Any, atol: float) -> bool:
    import numpy as np

    return bool(np.allclose(np.asarray(left), np.asarray(right), atol=atol, rtol=0.0))


def audit_self_collected(dataset_dir: Path, manifest: Dict[str, Any], atol: float) -> tuple[bool, Dict[str, Any]]:
    try:
        import gymnasium as gym
    except ImportError as exc:
        raise SystemExit("Gymnasium is not installed. Install requirements.txt.") from exc

    raw_path = dataset_dir / RAW_EPISODES_NAME
    log_path = dataset_dir / COLLECTION_LOG_NAME
    rows = read_jsonl(raw_path)
    failures: List[Dict[str, Any]] = []

    log_ok, log_value = validate_collection_log(raw_path, log_path)
    if not log_ok:
        failures.append({"type": "collection_log", "detail": log_value})
    elif manifest.get("collection_log_final_hash") != log_value:
        failures.append({"type": "collection_log_final_hash", "detail": log_value})

    env = gym.make(manifest["env_id"])
    try:
        current_episode = None
        obs = None
        for row in rows:
            if row["episode_id"] != current_episode:
                current_episode = row["episode_id"]
                obs, _ = env.reset(seed=row["env_seed"])
                env.action_space.seed(row["action_seed"])
            if not close_enough(row["state"], obs, atol):
                failures.append({"type": "state", "episode_id": row["episode_id"], "t": row["t"]})
                break
            next_obs, reward, terminated, truncated, _ = env.step(row["action"])
            if not close_enough(row["next_state"], next_obs, atol):
                failures.append({"type": "next_state", "episode_id": row["episode_id"], "t": row["t"]})
            if abs(float(row["reward"]) - float(reward)) > atol:
                failures.append(
                    {
                        "type": "reward",
                        "episode_id": row["episode_id"],
                        "t": row["t"],
                        "expected": float(reward),
                        "actual": float(row["reward"]),
                    }
                )
            if bool(row["terminated"]) != bool(terminated):
                failures.append({"type": "terminated", "episode_id": row["episode_id"], "t": row["t"]})
            if bool(row["truncated"]) != bool(truncated):
                failures.append({"type": "truncated", "episode_id": row["episode_id"], "t": row["t"]})
            obs = next_obs
    finally:
        env.close()

    passed = not failures
    report = {
        "schema_version": "dataset_audit_report_v1",
        "dataset_id": manifest["dataset_id"],
        "dataset_type": manifest["dataset_type"],
        "audit_scope": "self_collected_replay_and_reward",
        "raw_trajectory_hash": hash_jsonl_transitions(raw_path),
        "collection_log_valid": log_ok,
        "collection_log_final_hash": log_value if log_ok else None,
        "replay_audit_passed": passed,
        "reward_audit_passed": passed,
        "failures": failures,
    }
    return passed, report


def audit_public(dataset_dir: Path, manifest: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
    raw_hash = hash_jsonl_transitions(dataset_dir / RAW_EPISODES_NAME)
    passed = raw_hash == manifest.get("raw_trajectory_hash")
    report = {
        "schema_version": "dataset_audit_report_v1",
        "dataset_id": manifest["dataset_id"],
        "dataset_type": manifest["dataset_type"],
        "audit_scope": "source_integrity_only",
        "raw_trajectory_hash": raw_hash,
        "source_file_hash": manifest.get("source_file_hash"),
        "source_integrity_audit_passed": passed,
        "replay_audit_passed": False,
        "reward_audit_passed": False,
        "failures": [] if passed else [{"type": "raw_trajectory_hash_mismatch"}],
    }
    return passed, report


def audit_dataset(dataset_dir: Path, atol: float = 1e-6) -> bool:
    dataset_dir = Path(dataset_dir)
    manifest = load_manifest(dataset_dir)
    raw_hash = hash_jsonl_transitions(dataset_dir / RAW_EPISODES_NAME)
    if raw_hash != manifest.get("raw_trajectory_hash"):
        report = {
            "schema_version": "dataset_audit_report_v1",
            "dataset_id": manifest.get("dataset_id"),
            "dataset_type": manifest.get("dataset_type"),
            "audit_scope": "precheck",
            "raw_trajectory_hash": raw_hash,
            "failures": [{"type": "raw_trajectory_hash_mismatch"}],
        }
        report_hash = write_audit_report(dataset_dir, report)
        manifest["audit_report_hash"] = report_hash
        if manifest.get("dataset_type") == "public_benchmark":
            manifest["source_integrity_audit_passed"] = False
            manifest["audit_scope"] = "source_integrity_failed"
        else:
            manifest["replay_audit_passed"] = False
            manifest["reward_audit_passed"] = False
        write_manifest(dataset_dir, manifest)
        return False

    if manifest.get("dataset_type") == "self_collected_replay_audited":
        passed, report = audit_self_collected(dataset_dir, manifest, atol)
        report_hash = write_audit_report(dataset_dir, report)
        manifest["replay_audit_passed"] = bool(passed)
        manifest["reward_audit_passed"] = bool(passed)
    elif manifest.get("dataset_type") == "public_benchmark":
        passed, report = audit_public(dataset_dir, manifest)
        report_hash = write_audit_report(dataset_dir, report)
        manifest["source_integrity_audit_passed"] = bool(passed)
        manifest["replay_audit_passed"] = False
        manifest["reward_audit_passed"] = False
        manifest["audit_scope"] = "source_integrity_only" if passed else "source_integrity_failed"
    else:
        raise ValueError(f"unsupported dataset_type: {manifest.get('dataset_type')}")
    manifest["audit_report_hash"] = report_hash
    write_manifest(dataset_dir, manifest)
    return bool(passed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--atol", type=float, default=1e-6)
    args = parser.parse_args()
    passed = audit_dataset(Path(args.dataset_dir), atol=args.atol)
    manifest = load_manifest(args.dataset_dir)
    print(f"dataset_id = {manifest['dataset_id']}")
    print(f"dataset_type = {manifest['dataset_type']}")
    print(f"audit_report = {(Path(args.dataset_dir) / AUDIT_REPORT_NAME).as_posix()}")
    print(f"audit_passed = {passed}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
