import hashlib
import json

from zk_offline_dqn.zk_specs import (
    serialize_transition_leaf,
    compute_td_target_fp,
    compute_mse_loss_fp,
)


ARTIFACT_PATH = "artifacts/sample_minibatch_td_artifact.json"


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

    public = artifact["public"]
    items = artifact["items"]

    expected_root = public["dataset_root"]
    expected_batch_size = int(public["batch_size"])
    expected_batch_loss_fp = int(public["batch_loss_fp"])
    loss_type = public["loss_type"]

    if loss_type != "mse":
        raise ValueError(f"Expected loss_type='mse', got {loss_type}")

    if len(items) != expected_batch_size:
        raise ValueError(
            f"Batch size mismatch: len(items)={len(items)} vs public batch_size={expected_batch_size}"
        )

    total_loss_fp = 0
    all_items_ok = True

    print("=== VERIFY MINIBATCH TD ARTIFACT ===")
    print("artifact_path =", ARTIFACT_PATH)
    print("dataset_root =", expected_root)
    print("batch_size =", expected_batch_size)
    print("loss_type =", loss_type)

    print("\n=== PER-ITEM CHECKS ===")
    for item_id, item in enumerate(items):
        index = item["index"]
        transition = item["transition"]
        claimed_leaf = item["leaf"]
        claimed_leaf_hash = item["leaf_hash"]
        merkle_path = item["merkle_path"]
        td = item["td_witness"]

        q_online_fp = int(td["q_online_fp"])
        q_target_max_fp = int(td["q_target_max_fp"])
        claimed_target_fp = int(td["target_fp"])
        claimed_loss_fp = int(td["loss_fp"])

        recomputed_leaf = serialize_transition_leaf(transition)
        leaf_match = recomputed_leaf == claimed_leaf

        recomputed_leaf_hash = hash_leaf(recomputed_leaf)
        leaf_hash_match = recomputed_leaf_hash == claimed_leaf_hash

        merkle_ok, recomputed_root = verify_merkle_path(
            recomputed_leaf_hash, merkle_path, expected_root
        )

        reward_fp = recomputed_leaf[5]
        done_int = recomputed_leaf[-1]

        recomputed_target_fp = compute_td_target_fp(
            reward_fp=reward_fp,
            done=done_int,
            q_target_max_fp=q_target_max_fp,
        )
        target_match = recomputed_target_fp == claimed_target_fp

        recomputed_loss_fp = compute_mse_loss_fp(
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
        all_items_ok = all_items_ok and item_ok
        total_loss_fp += recomputed_loss_fp

        print(
            f"item[{item_id}] "
            f"index={index} "
            f"leaf_match={leaf_match} "
            f"leaf_hash_match={leaf_hash_match} "
            f"merkle_ok={merkle_ok} "
            f"target_match={target_match} "
            f"loss_match={loss_match} "
            f"item_ok={item_ok}"
        )

        if not item_ok:
            print("  claimed_leaf_hash =", claimed_leaf_hash)
            print("  recomputed_leaf_hash =", recomputed_leaf_hash)
            print("  claimed_target_fp =", claimed_target_fp)
            print("  recomputed_target_fp =", recomputed_target_fp)
            print("  claimed_loss_fp =", claimed_loss_fp)
            print("  recomputed_loss_fp =", recomputed_loss_fp)
            print("  recomputed_root =", recomputed_root)

    recomputed_batch_loss_fp = total_loss_fp // expected_batch_size
    batch_loss_match = recomputed_batch_loss_fp == expected_batch_loss_fp

    all_ok = all_items_ok and batch_loss_match

    print("\n=== BATCH CHECK ===")
    print("total_loss_fp =", total_loss_fp)
    print("claimed_batch_loss_fp =", expected_batch_loss_fp)
    print("recomputed_batch_loss_fp =", recomputed_batch_loss_fp)
    print("batch_loss_match =", batch_loss_match)

    print("\nverification_passed =", all_ok)


if __name__ == "__main__":
    main()