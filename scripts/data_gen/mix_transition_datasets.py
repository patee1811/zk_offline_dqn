import argparse
import json
import pickle
from pathlib import Path

import numpy as np


def load_transitions(path: str):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-a", type=str, required=True)
    parser.add_argument("--data-b", type=str, required=True)
    parser.add_argument("--frac-a", type=float, default=0.5)
    parser.add_argument("--total-transitions", type=int, default=47450)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    data_a = load_transitions(args.data_a)
    data_b = load_transitions(args.data_b)

    n_a = int(args.total_transitions * args.frac_a)
    n_b = args.total_transitions - n_a

    idx_a = rng.choice(len(data_a["obs"]), size=n_a, replace=(len(data_a["obs"]) < n_a))
    idx_b = rng.choice(len(data_b["obs"]), size=n_b, replace=(len(data_b["obs"]) < n_b))

    mixed = {
        "obs": np.concatenate([data_a["obs"][idx_a], data_b["obs"][idx_b]], axis=0).astype(np.float32),
        "actions": np.concatenate([data_a["actions"][idx_a], data_b["actions"][idx_b]], axis=0).astype(np.int64),
        "rewards": np.concatenate([data_a["rewards"][idx_a], data_b["rewards"][idx_b]], axis=0).astype(np.float32),
        "next_obs": np.concatenate([data_a["next_obs"][idx_a], data_b["next_obs"][idx_b]], axis=0).astype(np.float32),
        "dones": np.concatenate([data_a["dones"][idx_a], data_b["dones"][idx_b]], axis=0).astype(np.float32),
    }

    perm = rng.permutation(args.total_transitions)
    for k in mixed:
        mixed[k] = mixed[k][perm]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path = out_path.with_suffix(".summary.json")

    with open(out_path, "wb") as f:
        pickle.dump(mixed, f)

    summary = {
        "data_a": args.data_a,
        "data_b": args.data_b,
        "frac_a": args.frac_a,
        "frac_b": 1.0 - args.frac_a,
        "total_transitions": args.total_transitions,
        "seed": args.seed,
        "obs_shape": list(mixed["obs"].shape),
        "actions_shape": list(mixed["actions"].shape),
        "rewards_shape": list(mixed["rewards"].shape),
        "next_obs_shape": list(mixed["next_obs"].shape),
        "dones_shape": list(mixed["dones"].shape),
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved mixed transition dataset to: {out_path}")
    print(f"Saved summary to: {summary_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()