import hashlib
import json
import pickle

from zk_offline_dqn.zk_specs import (
    encode_fp,
    serialize_transition_leaf,
    compute_td_target_fp,
    compute_mse_loss_fp,
)


DATASET_PATH = "data/cartpole_dqn_eps010_transitions.pkl"
LEAF_HASHES_PATH = "artifacts/cartpole_dqn_eps010_leaf_hashes.json"
MERKLE_PATH = "artifacts/cartpole_dqn_eps010_merkle.json"
OUTPUT_PATH = "artifacts/sample_minibatch_td_artifact.json"

BATCH_INDICES = [0, 1, 2, 3]

# Tạm thời gán tay witness Q-values để test batch arithmetic
Q_ONLINE_REALS = [1.234, 0.800, 1.100, 0.950]
Q_TARGET_MAX_REALS = [1.500, 1.200, 1.300, 1.100]


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
    if len(BATCH_INDICES) != len(Q_ONLINE_REALS):
        raise ValueError("BATCH_INDICES and Q_ONLINE_REALS must have same length.")
    if len(BATCH_INDICES) != len(Q_TARGET_MAX_REALS):
        raise ValueError("BATCH_INDICES and Q_TARGET_MAX_REALS must have same length.")

    data = load_dataset(DATASET_PATH)

    with open(LEAF_HASHES_PATH, "r", encoding="utf-8") as f:
        leaf_hash_data = json.load(f)

    with open(MERKLE_PATH, "r", encoding="utf-8") as f:
        merkle_data = json.load(f)

    items = []
    batch_loss_sum_fp = 0

    for idx, q_online_real, q_target_max_real in zip(
        BATCH_INDICES, Q_ONLINE_REALS, Q_TARGET_MAX_REALS
    ):
        transition = get_transition_at_index(data, idx)
        leaf = serialize_transition_leaf(transition)
        recomputed_leaf_hash = hash_leaf(leaf)
        stored_leaf_hash = leaf_hash_data["leaf_hashes"][idx]

        if recomputed_leaf_hash != stored_leaf_hash:
            raise ValueError(
                "Recomputed leaf hash does not match stored leaf hash.\n"
                f"idx={idx}\n"
                f"recomputed={recomputed_leaf_hash}\n"
                f"stored={stored_leaf_hash}"
            )

        reward_fp = encode_fp(float(transition["reward"]))
        done_int = int(transition["done"])

        q_online_fp = encode_fp(q_online_real)
        q_target_max_fp = encode_fp(q_target_max_real)

        target_fp = compute_td_target_fp(
            reward_fp=reward_fp,
            done=done_int,
            q_target_max_fp=q_target_max_fp,
        )
        loss_fp = compute_mse_loss_fp(
            q_online_fp=q_online_fp,
            target_fp=target_fp,
        )

        batch_loss_sum_fp += loss_fp

        item = {
            "index": idx,
            "transition": transition,
            "leaf": leaf,
            "leaf_hash": recomputed_leaf_hash,
            "merkle_path": get_merkle_path(merkle_data["levels"], idx),
            "td_witness": {
                "q_online_fp": q_online_fp,
                "q_target_max_fp": q_target_max_fp,
                "target_fp": target_fp,
                "loss_fp": loss_fp,
            },
            "debug": {
                "q_online_real": q_online_real,
                "q_target_max_real": q_target_max_real,
            },
        }
        items.append(item)

    batch_size = len(items)
    batch_loss_fp = batch_loss_sum_fp // batch_size

    artifact = {
        "public": {
            "dataset_root": merkle_data["merkle_root"],
            "batch_size": batch_size,
            "loss_type": "mse",
            "batch_loss_fp": batch_loss_fp,
        },
        "items": items,
        "notes": {
            "purpose": "minibatch TD arithmetic test before ZK circuit",
            "batch_indices": BATCH_INDICES,
        },
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== MINIBATCH TD ARTIFACT EXPORTED ===")
    print("output_path =", OUTPUT_PATH)
    print("dataset_root =", artifact["public"]["dataset_root"])
    print("batch_size =", batch_size)
    print("batch_loss_fp =", batch_loss_fp)

    print("\n=== PER-ITEM SUMMARY ===")
    for i, item in enumerate(items):
        td = item["td_witness"]
        print(
            f"item[{i}] "
            f"index={item['index']} "
            f"q_online_fp={td['q_online_fp']} "
            f"q_target_max_fp={td['q_target_max_fp']} "
            f"target_fp={td['target_fp']} "
            f"loss_fp={td['loss_fp']} "
            f"path_length={len(item['merkle_path'])}"
        )


if __name__ == "__main__":
    main()