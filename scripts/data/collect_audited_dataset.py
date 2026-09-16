from __future__ import annotations

import argparse
import random
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


def greedy_action(module: Any, observation: Any) -> int:
    import numpy as np
    import torch

    obs = np.asarray(observation, dtype=np.float32).reshape(1, -1)
    with torch.no_grad():
        values = module(torch.as_tensor(obs))
    return int(values.argmax(dim=-1).item())


def load_checkpoint_policy(checkpoint_path: Path, env: Any) -> Any:
    """Rebuild the online network a source policy was saved from."""
    import numpy as np
    import torch

    from zk_offline_dqn.rl_benchmarks.agents import MLP

    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    state_dict = payload["state_dict"] if "state_dict" in payload else payload
    obs_dim = int(np.prod(env.observation_space.shape))
    n_actions = int(env.action_space.n)
    hidden_dim = int(payload.get("hidden_dim", 64)) if isinstance(payload, dict) else 64
    module = MLP(obs_dim, n_actions, hidden_dim=hidden_dim)
    module.load_state_dict(state_dict)
    module.eval()
    return module


def collect(args: argparse.Namespace) -> None:
    # In-process callers (rl_benchmarks, tamper_benchmarks, tests) build a
    # Namespace by hand, so every flag added after they were written has to
    # degrade to its default rather than raise.
    policy_label = getattr(args, "policy_label", None)
    checkpoint = getattr(args, "checkpoint", None)
    epsilon = getattr(args, "epsilon", 0.1)
    max_transitions = getattr(args, "max_transitions", 0)

    if args.policy not in {"random", "checkpoint"}:
        raise ValueError("--policy must be random or checkpoint")
    if args.policy == "checkpoint" and not checkpoint:
        raise ValueError("--policy checkpoint requires --checkpoint")
    try:
        import gymnasium as gym
    except ImportError as exc:
        raise SystemExit("Gymnasium is not installed. Install requirements.txt.") from exc

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    env = gym.make(args.env_id)
    module = None
    checkpoint_hash = None
    if args.policy == "checkpoint":
        checkpoint_path = Path(checkpoint)
        module = load_checkpoint_policy(checkpoint_path, env)
        checkpoint_hash = sha256_file(checkpoint_path)
    rows = []
    try:
        for episode_id in range(args.num_episodes):
            env_seed = args.base_seed + episode_id
            action_seed = args.base_seed + 100000 + episode_id
            obs, _ = env.reset(seed=env_seed)
            env.action_space.seed(action_seed)
            # Exploration draws come from their own seeded stream so a rerun with
            # the same seeds reproduces the dataset byte for byte.
            explore_rng = random.Random(action_seed)
            for t in range(args.max_steps_per_episode):
                if module is None or explore_rng.random() < epsilon:
                    action = env.action_space.sample()
                else:
                    action = greedy_action(module, obs)
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
            # Stopping on an episode boundary rather than mid-episode keeps every
            # trajectory whole, so an offline learner never sees a fabricated end.
            if max_transitions and len(rows) >= max_transitions:
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
        "policy_type": policy_label or args.policy,
        # The hash pins what actually produced the data: for a checkpoint policy
        # that is the network weights and the exploration rate, not just a name.
        "policy_hash": sha256_hex_bytes(
            canonical_json_bytes(
                {
                    "policy": args.policy,
                    "label": policy_label,
                    "checkpoint_sha256": checkpoint_hash,
                    "epsilon": epsilon if args.policy == "checkpoint" else None,
                }
            )
        ),
        "policy_checkpoint_sha256": checkpoint_hash,
        "policy_epsilon": epsilon if args.policy == "checkpoint" else None,
        "base_seed": args.base_seed,
        "num_episodes": len({row["episode_id"] for row in rows}),
        "requested_episodes": args.num_episodes,
        "max_transitions": max_transitions or None,
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
    parser.add_argument("--policy", default="random", choices=["random", "checkpoint"])
    parser.add_argument("--checkpoint", help="Torch checkpoint for --policy checkpoint")
    parser.add_argument("--policy-label", help="Name recorded as policy_type, e.g. medium")
    parser.add_argument("--epsilon", type=float, default=0.1)
    parser.add_argument("--num-episodes", type=int, required=True)
    parser.add_argument(
        "--max-transitions",
        type=int,
        default=0,
        help="Stop after the episode that reaches this many transitions (0 = no cap)",
    )
    parser.add_argument("--base-seed", type=int, required=True)
    parser.add_argument("--max-steps-per-episode", type=int, required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--audit-after-collect", action="store_true")
    parser.add_argument("--atol", type=float, default=1e-6)
    collect(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
