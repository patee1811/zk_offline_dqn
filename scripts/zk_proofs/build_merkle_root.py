import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.merkle import build_merkle_levels

INPUT_PATH = "artifacts/fixtures/membership/cartpole_dqn_eps010_leaf_hashes.json"
OUTPUT_PATH = "artifacts/fixtures/membership/cartpole_dqn_eps010_merkle.json"


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
