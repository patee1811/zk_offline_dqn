import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.merkle import build_merkle_path, verify_merkle_path

MERKLE_PATH = "artifacts/fixtures/membership/cartpole_dqn_eps010_merkle.json"
LEAF_HASHES_PATH = "artifacts/fixtures/membership/cartpole_dqn_eps010_leaf_hashes.json"
TARGET_INDEX = 0


def main():
    with open(MERKLE_PATH, "r", encoding="utf-8") as f:
        merkle_data = json.load(f)

    with open(LEAF_HASHES_PATH, "r", encoding="utf-8") as f:
        leaf_data = json.load(f)

    levels = merkle_data["levels"]
    merkle_root = merkle_data["merkle_root"]
    leaf_hashes = leaf_data["leaf_hashes"]

    if TARGET_INDEX < 0 or TARGET_INDEX >= len(leaf_hashes):
        raise ValueError(
            f"TARGET_INDEX must be in [0, {len(leaf_hashes) - 1}], got {TARGET_INDEX}"
        )

    leaf_hash = leaf_hashes[TARGET_INDEX]
    path = build_merkle_path(levels, TARGET_INDEX)
    ok, recomputed_root = verify_merkle_path(leaf_hash, path, merkle_root)

    print("=== MERKLE MEMBERSHIP CHECK ===")
    print("target_index =", TARGET_INDEX)
    print("leaf_hash =", leaf_hash)
    print("path_length =", len(path))
    print("expected_root =", merkle_root)
    print("recomputed_root =", recomputed_root)
    print("verification_passed =", ok)

    print("\n=== FIRST 5 PATH STEPS ===")
    for i, step in enumerate(path[:5]):
        print(
            f"step[{i}] "
            f"level={step['level']} "
            f"current_index={step['current_index']} "
            f"sibling_index={step['sibling_index']} "
            f"current_is_left={step['current_is_left']} "
            f"sibling_hash={step['sibling_hash']}"
        )


if __name__ == "__main__":
    main()
