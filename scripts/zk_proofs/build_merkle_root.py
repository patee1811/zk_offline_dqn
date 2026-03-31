import hashlib
import json
from typing import List


INPUT_PATH = "artifacts/cartpole_dqn_eps010_leaf_hashes.json"
OUTPUT_PATH = "artifacts/cartpole_dqn_eps010_merkle.json"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_internal_node(left_hex: str, right_hex: str) -> str:
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return sha256_hex(left_bytes + right_bytes)


def build_next_level(current_level: List[str]) -> List[str]:
    if len(current_level) == 0:
        raise ValueError("Current Merkle level is empty.")

    next_level = []

    i = 0
    while i < len(current_level):
        left = current_level[i]

        if i + 1 < len(current_level):
            right = current_level[i + 1]
        else:
            # odd number of nodes -> duplicate last
            right = left

        parent = hash_internal_node(left, right)
        next_level.append(parent)
        i += 2

    return next_level


def build_merkle_levels(leaf_hashes: List[str]) -> List[List[str]]:
    if len(leaf_hashes) == 0:
        raise ValueError("leaf_hashes is empty.")

    levels = [leaf_hashes]
    current = leaf_hashes

    while len(current) > 1:
        current = build_next_level(current)
        levels.append(current)

    return levels


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    leaf_hashes = data["leaf_hashes"]

    # basic sanity checks
    if not isinstance(leaf_hashes, list) or len(leaf_hashes) == 0:
        raise ValueError("leaf_hashes must be a non-empty list.")

    for i, h in enumerate(leaf_hashes[:10]):
        if not isinstance(h, str) or len(h) != 64:
            raise ValueError(f"Invalid hash at index {i}: {h}")

    levels = build_merkle_levels(leaf_hashes)
    merkle_root = levels[-1][0]

    output = {
        "dataset_name": data.get("dataset_name", "unknown_dataset"),
        "num_leaves": len(leaf_hashes),
        "leaf_hash_rule": data.get("hash_function", "sha256"),
        "leaf_encoding": data.get("leaf_encoding", "unknown"),
        "internal_node_hash_rule": "sha256(bytes.fromhex(left) + bytes.fromhex(right))",
        "odd_node_rule": "duplicate_last",
        "num_levels": len(levels),
        "merkle_root": merkle_root,
        "levels": levels,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print("=== MERKLE BUILD COMPLETE ===")
    print("input_path =", INPUT_PATH)
    print("output_path =", OUTPUT_PATH)
    print("num_leaves =", len(leaf_hashes))
    print("num_levels =", len(levels))
    print("merkle_root =", merkle_root)

    print("\n=== LEVEL SIZES ===")
    for depth, level in enumerate(levels):
        print(f"level[{depth}] size = {len(level)}")

    print("\n=== FIRST 3 ROOT-PROXIMAL VALUES ===")
    top_level = levels[-1]
    print("root =", top_level[0])

    if len(levels) >= 2:
        print("level[-2] first =", levels[-2][0])
        if len(levels[-2]) > 1:
            print("level[-2] second =", levels[-2][1])


if __name__ == "__main__":
    main()