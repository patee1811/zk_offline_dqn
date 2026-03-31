import json
import hashlib

from zk_offline_dqn.zk_specs import (
    serialize_transition_leaf,
    compute_td_target_fp,
    compute_smooth_l1_loss_fp,
)

ARTIFACT_PATH = "artifacts/sample_minibatch_td_artifact.json"
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
    items = artifact["items"]

    dataset_root = public["dataset_root"]
    batch_size = int(public["batch_size"])
    loss_type = public["loss_type"]
    claimed_batch_loss_fp = int(public["batch_loss_fp"])

    print("=== VERIFY MINIBATCH TD ARTIFACT ===")
    print("artifact_path =", ARTIFACT_PATH)
    print("dataset_root =", dataset_root)
    print("batch_size =", batch_size)
    print("loss_type =", loss_type)

    if loss_type != "smooth_l1":
        raise ValueError(f"Expected loss_type='smooth_l1', got {loss_type}")

    print("\n=== PER-ITEM CHECKS ===")

    all_items_ok = True
    total_loss_fp = 0

    for i, item in enumerate(items):
        transition = item["transition"]
        claimed_leaf = item.get("serialized_leaf", item.get("leaf"))
        claimed_leaf_hash = item["leaf_hash"]
        merkle_path = item["merkle_path"]

        td = item["td_witness"]
        q_online_fp = int(td["q_online_fp"])
        q_target_max_fp = int(td["q_target_max_fp"])
        claimed_target_fp = int(td["target_fp"])
        claimed_loss_fp = int(td["loss_fp"])

        recomputed_leaf = serialize_transition_leaf(transition)
        leaf_match = True if claimed_leaf is None else (recomputed_leaf == claimed_leaf)

        recomputed_leaf_hash = hash_leaf_serialized(recomputed_leaf)
        leaf_hash_match = recomputed_leaf_hash == claimed_leaf_hash

        merkle_ok, _ = verify_merkle_path(
            recomputed_leaf_hash,
            merkle_path,
            dataset_root,
        )

        reward_fp = recomputed_leaf[5]
        done_int = recomputed_leaf[-1]

        recomputed_target_fp = compute_td_target_fp(
            reward_fp=reward_fp,
            done=done_int,
            q_target_max_fp=q_target_max_fp,
        )
        target_match = recomputed_target_fp == claimed_target_fp

        recomputed_loss_fp = compute_smooth_l1_loss_fp(
            q_online_fp=q_online_fp,
            target_fp=recomputed_target_fp,
        )
        loss_match = recomputed_loss_fp == claimed_loss_fp

        item_ok = (
            leaf_match
            and leaf_hash_match
            and merkle_ok
            and target_match
            and loss_match
        )

        total_loss_fp += claimed_loss_fp
        all_items_ok = all_items_ok and item_ok

        print(
            f"item[{i}] index={item['index']} "
            f"leaf_match={leaf_match} "
            f"leaf_hash_match={leaf_hash_match} "
            f"merkle_ok={merkle_ok} "
            f"target_match={target_match} "
            f"loss_match={loss_match} "
            f"item_ok={item_ok}"
        )

    recomputed_batch_loss_fp = total_loss_fp // batch_size
    batch_loss_match = recomputed_batch_loss_fp == claimed_batch_loss_fp

    expected_checkpoint_sha256 = public.get("checkpoint_sha256")
    recomputed_checkpoint_sha256 = file_sha256(CHECKPOINT_PATH)
    checkpoint_sha256_ok = expected_checkpoint_sha256 == recomputed_checkpoint_sha256

    print("\n=== BATCH CHECK ===")
    print("total_loss_fp =", total_loss_fp)
    print("claimed_batch_loss_fp =", claimed_batch_loss_fp)
    print("recomputed_batch_loss_fp =", recomputed_batch_loss_fp)
    print("batch_loss_match =", batch_loss_match)

    print("\n=== PUBLIC CHECKS ===")
    print("expected_checkpoint_sha256 =", expected_checkpoint_sha256)
    print("recomputed_checkpoint_sha256 =", recomputed_checkpoint_sha256)
    print("checkpoint_sha256_ok =", checkpoint_sha256_ok)

    verification_passed = all_items_ok and batch_loss_match and checkpoint_sha256_ok
    print("\nverification_passed =", verification_passed)


if __name__ == "__main__":
    main()