import json
import hashlib

from zk_offline_dqn.zk_specs import (
    serialize_transition_leaf,
    compute_td_target_fp,
    compute_smooth_l1_loss_fp,
)

ARTIFACT_PATH = "artifacts/sample_td_artifact.json"
CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"


def encode_leaf_for_hash(leaf):
    s = ",".join(str(x) for x in leaf)
    return s.encode("utf-8")


def hash_leaf_serialized(leaf):
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


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    public = artifact["public"]
    membership = artifact["transition_membership"]
    td = artifact["td_witness"]

    transition = membership["transition"]
    claimed_leaf = membership.get("serialized_leaf", membership.get("leaf"))
    claimed_leaf_hash = membership["leaf_hash"]
    merkle_path = membership["merkle_path"]
    expected_root = membership["dataset_root"]

    q_online_fp = int(td["q_online_fp"])
    q_target_max_fp = int(td["q_target_max_fp"])
    claimed_target_fp = int(td["target_fp"])
    claimed_loss_fp = int(td["loss_fp"])

    # 1) Recompute leaf from transition
    recomputed_leaf = serialize_transition_leaf(transition)
    leaf_match = True if claimed_leaf is None else (recomputed_leaf == claimed_leaf)

    # 2) Recompute leaf hash
    recomputed_leaf_hash = hash_leaf_serialized(recomputed_leaf)
    leaf_hash_match = recomputed_leaf_hash == claimed_leaf_hash

    # 3) Verify Merkle membership
    merkle_ok, recomputed_root = verify_merkle_path(
        recomputed_leaf_hash,
        merkle_path,
        expected_root,
    )

    # 4) Recompute target
    reward_fp = recomputed_leaf[5]
    done_int = recomputed_leaf[-1]

    recomputed_target_fp = compute_td_target_fp(
        reward_fp=reward_fp,
        done=done_int,
        q_target_max_fp=q_target_max_fp,
    )
    target_match = recomputed_target_fp == claimed_target_fp

    # 5) Recompute loss
    recomputed_loss_fp = compute_smooth_l1_loss_fp(
        q_online_fp=q_online_fp,
        target_fp=recomputed_target_fp,
    )
    loss_match = recomputed_loss_fp == claimed_loss_fp

    # 6) Public checks
    root_match_public = expected_root == public["dataset_root"]
    loss_type_ok = public["loss_type"] == "smooth_l1"

    expected_checkpoint_sha256 = public.get("checkpoint_sha256")
    recomputed_checkpoint_sha256 = file_sha256(CHECKPOINT_PATH)
    checkpoint_sha256_ok = expected_checkpoint_sha256 == recomputed_checkpoint_sha256

    all_ok = (
        leaf_match
        and leaf_hash_match
        and merkle_ok
        and target_match
        and loss_match
        and root_match_public
        and loss_type_ok
        and checkpoint_sha256_ok
    )

    print("=== VERIFY TD SAMPLE ARTIFACT ===")
    print("artifact_path =", ARTIFACT_PATH)

    print("\n[Membership]")
    print("leaf_match =", leaf_match)
    print("leaf_hash_match =", leaf_hash_match)
    print("merkle_ok =", merkle_ok)
    print("expected_root =", expected_root)
    print("recomputed_root =", recomputed_root)

    print("\n[TD Arithmetic]")
    print("reward_fp =", reward_fp)
    print("done =", done_int)
    print("q_online_fp =", q_online_fp)
    print("q_target_max_fp =", q_target_max_fp)
    print("claimed_target_fp =", claimed_target_fp)
    print("recomputed_target_fp =", recomputed_target_fp)
    print("target_match =", target_match)
    print("claimed_loss_fp =", claimed_loss_fp)
    print("recomputed_loss_fp =", recomputed_loss_fp)
    print("loss_match =", loss_match)

    print("\n[Public Checks]")
    print("root_match_public =", root_match_public)
    print("loss_type_ok =", loss_type_ok)
    print("expected_checkpoint_sha256 =", expected_checkpoint_sha256)
    print("recomputed_checkpoint_sha256 =", recomputed_checkpoint_sha256)
    print("checkpoint_sha256_ok =", checkpoint_sha256_ok)

    print("\nverification_passed =", all_ok)


if __name__ == "__main__":
    main()