import json
import pickle
from pathlib import Path
import sys
from typing import Dict, Iterator, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.merkle import hash_leaf
from zk_offline_dqn.zk_specs import serialize_transition_leaf


DATASET_PATH = "data/cartpole_dqn_eps010_transitions.pkl"
OUTPUT_PATH = "artifacts/fixtures/membership/cartpole_dqn_eps010_leaf_hashes.json"


def load_dataset(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def iter_transitions(data) -> Iterator[Dict]:
    required_keys = ["obs", "actions", "rewards", "next_obs", "dones"]

    if not (isinstance(data, dict) and all(k in data for k in required_keys)):
        raise ValueError(
            "Expected columnar dict with keys "
            "['obs', 'actions', 'rewards', 'next_obs', 'dones']."
        )

    n = len(data["obs"])
    if not all(len(data[k]) == n for k in required_keys):
        raise ValueError("Column lengths do not match.")

    for i in range(n):
        yield {
            "obs": data["obs"][i],
            "action": data["actions"][i],
            "reward": data["rewards"][i],
            "next_obs": data["next_obs"][i],
            "done": data["dones"][i],
        }


def main():
    data = load_dataset(DATASET_PATH)

    leaf_hashes = []
    first_5_leaves = []
    first_5_hashes = []

    count = 0
    for transition in iter_transitions(data):
        leaf = serialize_transition_leaf(transition)
        leaf_hash = hash_leaf(leaf)

        if count < 5:
            first_5_leaves.append(leaf)
            first_5_hashes.append(leaf_hash)

        leaf_hashes.append(leaf_hash)
        count += 1

    output = {
        "dataset_name": "cartpole_dqn_eps010_transitions",
        "num_transitions": count,
        "hash_function": "sha256",
        "leaf_encoding": "comma-separated signed decimal integers encoded as utf-8",
        "leaf_hashes": leaf_hashes,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("=== LEAF HASH BUILD COMPLETE ===")
    print("num_transitions =", count)
    print("output_path =", OUTPUT_PATH)

    print("\n=== FIRST 5 LEAVES AND HASHES ===")
    for i, (leaf, leaf_hash) in enumerate(zip(first_5_leaves, first_5_hashes)):
        print(f"leaf[{i}] = {leaf}")
        print(f"hash[{i}] = {leaf_hash}")


if __name__ == "__main__":
    main()
