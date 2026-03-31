import hashlib
import json

from zk_offline_dqn.zk_specs import serialize_transition_leaf


ARTIFACT_PATH = "artifacts/sample_transition_membership.json"


def encode_leaf_for_hash(leaf):
    s = ",".join(str(x) for x in leaf)
    return s.encode("utf-8")


def hash_leaf(leaf):
    return hashlib.sha256(encode_leaf_for_hash(leaf)).hexdigest()


def hash_internal_node(left_hex: str, right_hex: str) -> str:
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return hashlib.sha256(left_bytes + right_bytes).hexdigest()


def verify_merkle_path(leaf_hash, merkle_path, expected_root):
    current = leaf_hash

    for step in merkle_path:
        sibling_hash = step["sibling_hash"]
        current_is_left = step["current_is_left"]

        if current_is_left:
            current = hash_internal_node(current, sibling_hash)
        else:
            current = hash_internal_node(sibling_hash, current)

    return current == expected_root, current


def main():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    transition = artifact["transition"]
    claimed_leaf = artifact["leaf"]
    claimed_leaf_hash = artifact["leaf_hash"]
    merkle_path = artifact["merkle_path"]
    expected_root = artifact["dataset_root"]

    recomputed_leaf = serialize_transition_leaf(transition)
    leaf_match = recomputed_leaf == claimed_leaf

    recomputed_leaf_hash = hash_leaf(recomputed_leaf)
    leaf_hash_match = recomputed_leaf_hash == claimed_leaf_hash

    merkle_ok, recomputed_root = verify_merkle_path(
        recomputed_leaf_hash, merkle_path, expected_root
    )

    all_ok = leaf_match and leaf_hash_match and merkle_ok

    print("=== VERIFY TRANSITION MEMBERSHIP ARTIFACT ===")
    print("artifact_path =", ARTIFACT_PATH)
    print("target_index =", artifact["target_index"])

    print("\nleaf_match =", leaf_match)
    print("claimed_leaf =", claimed_leaf)
    print("recomputed_leaf =", recomputed_leaf)

    print("\nleaf_hash_match =", leaf_hash_match)
    print("claimed_leaf_hash =", claimed_leaf_hash)
    print("recomputed_leaf_hash =", recomputed_leaf_hash)

    print("\nmerkle_ok =", merkle_ok)
    print("expected_root =", expected_root)
    print("recomputed_root =", recomputed_root)
    print("path_length =", len(merkle_path))

    print("\nverification_passed =", all_ok)


if __name__ == "__main__":
    main()