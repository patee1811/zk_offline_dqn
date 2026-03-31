import hashlib
import json


MERKLE_PATH = "artifacts/cartpole_dqn_eps010_merkle.json"
LEAF_HASHES_PATH = "artifacts/cartpole_dqn_eps010_leaf_hashes.json"
TARGET_INDEX = 0


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_internal_node(left_hex: str, right_hex: str) -> str:
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return sha256_hex(left_bytes + right_bytes)


def get_merkle_path(levels, leaf_index):
    """
    Return Merkle path for one leaf index.
    Each element contains:
      - level
      - current_index
      - sibling_index
      - sibling_hash
      - current_is_left
    """
    path = []
    idx = leaf_index

    for level_id in range(len(levels) - 1):
        level = levels[level_id]

        if idx < 0 or idx >= len(level):
            raise ValueError(f"Invalid index {idx} at level {level_id}")

        if idx % 2 == 0:
            current_is_left = True
            sibling_index = idx + 1 if idx + 1 < len(level) else idx
        else:
            current_is_left = False
            sibling_index = idx - 1

        sibling_hash = level[sibling_index]

        path.append(
            {
                "level": level_id,
                "current_index": idx,
                "sibling_index": sibling_index,
                "sibling_hash": sibling_hash,
                "current_is_left": current_is_left,
            }
        )

        idx = idx // 2

    return path


def verify_merkle_path(leaf_hash, path, expected_root):
    current = leaf_hash

    for step in path:
        sibling_hash = step["sibling_hash"]
        current_is_left = step["current_is_left"]

        if current_is_left:
            current = hash_internal_node(current, sibling_hash)
        else:
            current = hash_internal_node(sibling_hash, current)

    return current == expected_root, current


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
    path = get_merkle_path(levels, TARGET_INDEX)
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