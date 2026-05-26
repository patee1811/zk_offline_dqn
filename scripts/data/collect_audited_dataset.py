from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import (
    RAW_EPISODES_NAME,
    canonical_json_bytes,
    hash_jsonl_transitions,
    sha256_hex_bytes,
    sha256_file,
    write_collection_log,
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


def collect(args: argparse.Namespace) -> None:
    if args.policy != "random":
        raise ValueError("Phase 2 supports --policy random")
    try:
        import gymnasium as gym
    except ImportError as exc:
        raise SystemExit("Gymnasium is not installed. Install requirements.txt.") from exc

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    env = gym.make(args.env_id)
    rows = []
    try:
        for episode_id in range(args.num_episodes):
            env_seed = args.base_seed + episode_id
            action_seed = args.base_seed + 100000 + episode_id
            obs, _ = env.reset(seed=env_seed)
            env.action_space.seed(action_seed)
            for t in range(args.max_steps_per_episode):
                action = env.action_space.sample()
                next_obs, reward, terminated, truncated, _ = env.step(action)
                rows.append(
                    {
                        "episode_id": episode_id,
                        "t": t,
                        "env_seed": env_seed,
                        "action_seed": action_seed,
                        "state": to_jsonable(obs),
                        "action": to_jsonable(action),
                        "reward": float(reward),
                        "next_state": to_jsonable(next_obs),
                        "terminated": bool(terminated),
                        "truncated": bool(truncated),
                    }
                )
                obs = next_obs
                if terminated or truncated:
                    break
    finally:
        env.close()

    raw_path = out_dir / RAW_EPISODES_NAME
    write_jsonl(raw_path, rows)
    final_log_hash = write_collection_log(raw_path, out_dir / "collection_log.jsonl")
    manifest = {
        "schema_version": "dataset_manifest_v1",
        "dataset_id": args.dataset_id,
        "dataset_type": "self_collected_replay_audited",
        "env_id": args.env_id,
        "env_version": getattr(getattr(env, "spec", None), "version", None),
        "collector_script_hash": sha256_file(Path(__file__)),
        "policy_type": args.policy,
        "policy_hash": sha256_hex_bytes(canonical_json_bytes({"policy": args.policy})),
        "base_seed": args.base_seed,
        "num_episodes": args.num_episodes,
        "total_transitions": len(rows),
        "raw_trajectory_hash": hash_jsonl_transitions(raw_path),
        "collection_log_final_hash": final_log_hash,
        "replay_audit_passed": False,
        "reward_audit_passed": False,
        "audit_report_hash": None,
        "merkle_root": None,
    }
    write_manifest(out_dir, manifest)

    if args.audit_after_collect:
        from scripts.data.audit_replay_dataset import audit_dataset

        audit_dataset(out_dir, atol=args.atol)

    print(f"dataset_id = {args.dataset_id}")
    print(f"dataset_type = self_collected_replay_audited")
    print(f"total_transitions = {len(rows)}")
    print(f"out_dir = {out_dir.as_posix()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--policy", default="random")
    parser.add_argument("--num-episodes", type=int, required=True)
    parser.add_argument("--base-seed", type=int, required=True)
    parser.add_argument("--max-steps-per-episode", type=int, required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--audit-after-collect", action="store_true")
    parser.add_argument("--atol", type=float, default=1e-6)
    collect(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
