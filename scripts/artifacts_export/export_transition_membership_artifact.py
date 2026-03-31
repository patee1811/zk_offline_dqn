import json
import pickle
import hashlib

from zk_offline_dqn.zk_specs import serialize_transition_leaf


DATASET_PATH = "data/cartpole_dqn_eps010_transitions.pkl"
LEAF_HASHES_PATH = "artifacts/cartpole_dqn_eps010_leaf_hashes.json"
MERKLE_PATH = "artifacts/cartpole_dqn_eps010_merkle.json"
OUTPUT_PATH = "artifacts/sample_transition_membership.json"

TARGET_INDEX = 0


def encode_leaf_for_hash(leaf):
    s = ",".join(str(x) for x in leaf)
    return s.encode("utf-8")


def hash_leaf(leaf):
    return hashlib.sha256(encode_leaf_for_hash(leaf)).hexdigest()


def load_dataset(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def get_transition_at_index(data, idx):
    required_keys = ["obs", "actions", "rewards", "next_obs", "dones"]

    if not (isinstance(data, dict) and all(k in data for k in required_keys)):
        raise ValueError(
            "Expected columnar dict with keys "
            "['obs', 'actions', 'rewards', 'next_obs', 'dones']."
        )

    n = len(data["obs"])
    if idx < 0 or idx >= n:
        raise ValueError(f"idx must be in [0, {n-1}], got {idx}")

    return {
        "obs": [float(x) for x in data["obs"][idx]],
        "action": int(data["actions"][idx]),
        "reward": float(data["rewards"][idx]),
        "next_obs": [float(x) for x in data["next_obs"][idx]],
        "done": int(data["dones"][idx]),
    }


def get_merkle_path(levels, leaf_index):
    path = []
    idx = leaf_index

    for level_id in range(len(levels) - 1):
        level = levels[level_id]

        if idx % 2 == 0:
            current_is_left = True
            sibling_index = idx + 1 if idx + 1 < len(level) else idx
        else:
            current_is_left = False
            sibling_index = idx - 1

        path.append(
            {
                "level": level_id,
                "current_index": idx,
                "sibling_index": sibling_index,
                "sibling_hash": level[sibling_index],
                "current_is_left": current_is_left,
            }
        )

        idx = idx // 2

    return path


def main():
    data = load_dataset(DATASET_PATH)

    with open(LEAF_HASHES_PATH, "r", encoding="utf-8") as f:
        leaf_hash_data = json.load(f)

    with open(MERKLE_PATH, "r", encoding="utf-8") as f:
        merkle_data = json.load(f)

    transition = get_transition_at_index(data, TARGET_INDEX)
    leaf = serialize_transition_leaf(transition)
    recomputed_leaf_hash = hash_leaf(leaf)

    stored_leaf_hash = leaf_hash_data["leaf_hashes"][TARGET_INDEX]
    if recomputed_leaf_hash != stored_leaf_hash:
        raise ValueError(
            "Recomputed leaf hash does not match stored leaf hash.\n"
            f"recomputed={recomputed_leaf_hash}\n"
            f"stored={stored_leaf_hash}"
        )

    merkle_path = get_merkle_path(merkle_data["levels"], TARGET_INDEX)

    artifact = {
        "dataset_name": merkle_data["dataset_name"],
        "target_index": TARGET_INDEX,
        "dataset_root": merkle_data["merkle_root"],
        "transition": transition,
        "leaf": leaf,
        "leaf_hash": recomputed_leaf_hash,
        "merkle_path": merkle_path,
        "path_length": len(merkle_path),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== TRANSITION MEMBERSHIP ARTIFACT EXPORTED ===")
    print("target_index =", TARGET_INDEX)
    print("output_path =", OUTPUT_PATH)
    print("dataset_root =", artifact["dataset_root"])
    print("leaf =", leaf)
    print("leaf_hash =", recomputed_leaf_hash)
    print("path_length =", len(merkle_path))


if __name__ == "__main__":
    main()