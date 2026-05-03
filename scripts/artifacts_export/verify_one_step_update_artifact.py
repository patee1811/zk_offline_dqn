import hashlib
import json
import os

import torch

from zk_offline_dqn.artifact_export_utils import (
    compute_training_loss,
    file_sha256,
    hash_leaf_serialized,
    load_checkpoint_nets,
    load_merkle_artifact,
    serialize_leaf,
)

from zk_offline_dqn.zk_specs import (
    compute_smooth_l1_loss_fp,
    compute_td_target_fp,
    encode_fp,
)

from zk_offline_dqn.artifact_schema_versions import (
    SCHEMA_ONE_STEP_UPDATE_V1,
    require_schema_version,
)

ARTIFACT_PATH = os.environ.get(
    "ONE_STEP_ARTIFACT_PATH",
    "artifacts/one_step_update_artifact.json",
)
MERKLE_PATH = os.environ.get(
    "ONE_STEP_MERKLE_PATH",
    "artifacts/cartpole_dqn_eps010_merkle.json",
)


def hash_internal_node(left_hex: str, right_hex: str) -> str:
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return hashlib.sha256(left_bytes + right_bytes).hexdigest()


def recompute_root_from_path(leaf_hash: str, merkle_path):
    cur = leaf_hash
    for step in merkle_path:
        sibling = step["sibling_hash"]
        if step["current_is_left"]:
            cur = hash_internal_node(cur, sibling)
        else:
            cur = hash_internal_node(sibling, cur)
    return cur


def compare_state_dicts(sd1, sd2):
    keys1 = set(sd1.keys())
    keys2 = set(sd2.keys())
    if keys1 != keys2:
        return False
    for k in keys1:
        if not torch.equal(sd1[k].detach().cpu(), sd2[k].detach().cpu()):
            return False
    return True


def main():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    require_schema_version(
        artifact,
        SCHEMA_ONE_STEP_UPDATE_V1,
        artifact_path=ARTIFACT_PATH,
    )

    merkle = load_merkle_artifact(MERKLE_PATH)

    public = artifact["public"]
    update_witness = artifact["update_witness"]

    dataset_root = public["dataset_root"]
    batch_indices = public["batch_indices"]
    batch_size = public["batch_size"]
    loss_type = public["loss_type"]
    optimizer_type = public["optimizer_type"]
    learning_rate_fp = public["learning_rate_fp"]
    pre_checkpoint_sha256 = public["pre_checkpoint_sha256"]
    post_checkpoint_sha256 = public["post_checkpoint_sha256"]

    checkpoint_path = artifact["notes"]["checkpoint_path"]
    post_checkpoint_path = artifact["notes"]["post_checkpoint_path"]

    print("=== VERIFY ONE-STEP UPDATE ARTIFACT ===")
    print("artifact_path =", ARTIFACT_PATH)
    print("dataset_root =", dataset_root)
    print("batch_indices =", batch_indices)
    print("batch_size =", batch_size)
    print("loss_type =", loss_type)
    print("optimizer_type =", optimizer_type)
    print("learning_rate_fp =", learning_rate_fp)
    print()

    all_items_ok = True
    total_loss_fp = 0

    print("=== PER-ITEM CHECKS ===")
    for i, item in enumerate(artifact["items"]):
        idx = item["index"]
        transition = item["transition"]
        leaf = item["leaf"]
        claimed_leaf_hash = item["leaf_hash"]
        merkle_path = item["merkle_path"]
        w = item["td_witness"]

        recomputed_leaf = serialize_leaf(transition)
        leaf_match = (recomputed_leaf == leaf)

        recomputed_leaf_hash = hash_leaf_serialized(leaf)
        leaf_hash_match = (recomputed_leaf_hash == claimed_leaf_hash)

        recomputed_root = recompute_root_from_path(claimed_leaf_hash, merkle_path)
        merkle_ok = (recomputed_root == dataset_root)

        reward_fp = encode_fp(float(transition["reward"]))
        done = int(transition["done"])
        recomputed_target_fp = compute_td_target_fp(
            reward_fp=reward_fp,
            done=done,
            q_target_max_fp=int(w["q_target_max_fp"]),
        )
        target_match = (recomputed_target_fp == int(w["target_fp"]))

        recomputed_loss_fp = compute_smooth_l1_loss_fp(
            q_online_fp=int(w["q_online_fp"]),
            target_fp=int(w["target_fp"]),
        )
        loss_match = (recomputed_loss_fp == int(w["loss_fp"]))

        index_match = (idx == batch_indices[i])

        item_ok = (
            leaf_match
            and leaf_hash_match
            and merkle_ok
            and target_match
            and loss_match
            and index_match
        )
        all_items_ok = all_items_ok and item_ok
        total_loss_fp += int(w["loss_fp"])

        print(
            f"item[{i}] index={idx} "
            f"index_match={index_match} "
            f"leaf_match={leaf_match} "
            f"leaf_hash_match={leaf_hash_match} "
            f"merkle_ok={merkle_ok} "
            f"target_match={target_match} "
            f"loss_match={loss_match} "
            f"item_ok={item_ok}"
        )

    recomputed_batch_loss_fp = total_loss_fp // batch_size
    claimed_batch_loss_fp = int(update_witness["batch_loss_fp"])
    batch_loss_match = (recomputed_batch_loss_fp == claimed_batch_loss_fp)

    print()
    print("=== BATCH CHECK ===")
    print("total_loss_fp =", total_loss_fp)
    print("claimed_batch_loss_fp =", claimed_batch_loss_fp)
    print("recomputed_batch_loss_fp =", recomputed_batch_loss_fp)
    print("batch_loss_match =", batch_loss_match)

    pre_checkpoint_sha256_recomputed = file_sha256(checkpoint_path)
    post_checkpoint_sha256_recomputed = file_sha256(post_checkpoint_path)

    pre_checkpoint_ok = (pre_checkpoint_sha256_recomputed == pre_checkpoint_sha256)
    post_checkpoint_ok = (post_checkpoint_sha256_recomputed == post_checkpoint_sha256)

    pre_ckpt = torch.load(checkpoint_path, map_location="cpu")
    post_ckpt = torch.load(post_checkpoint_path, map_location="cpu")

    pre_online_state = pre_ckpt["model_state_dict"]
    pre_target_state = pre_ckpt["target_net_state_dict"]
    post_online_state = post_ckpt["model_state_dict"]
    post_target_state = post_ckpt["target_net_state_dict"]

    target_net_unchanged = compare_state_dicts(pre_target_state, post_target_state)
    online_net_changed = not compare_state_dicts(pre_online_state, post_online_state)

    pre_step = pre_ckpt.get("step", None)
    post_step = post_ckpt.get("step", None)
    step_increment_ok = (
        isinstance(pre_step, int)
        and isinstance(post_step, int)
        and post_step == pre_step + 1
    )

    source_checkpoint_sha_ok = (
        post_ckpt.get("source_checkpoint_sha256", None) == pre_checkpoint_sha256
    )

    metadata = post_ckpt.get("one_step_update_metadata", {})
    optimizer_type_ok = (metadata.get("optimizer_type") == optimizer_type)

    metadata_lr = metadata.get("learning_rate", None)
    learning_rate_real = float(metadata_lr) if metadata_lr is not None else 0.0
    learning_rate_ok = (
        metadata_lr is not None
        and encode_fp(learning_rate_real) == learning_rate_fp
    )

    batch_indices_ok = (metadata.get("batch_indices") == batch_indices)

    pre_named = {k: v.detach().cpu() for k, v in pre_online_state.items()}
    post_named = {k: v.detach().cpu() for k, v in post_online_state.items()}

    _, recompute_online_net, recompute_target_net = load_checkpoint_nets(checkpoint_path)
    transitions = [item["transition"] for item in artifact["items"]]

    recompute_online_net.zero_grad()
    recomputed_training_loss = compute_training_loss(
        online_net=recompute_online_net,
        target_net=recompute_target_net,
        transitions=transitions,
    )
    recomputed_training_loss.backward()

    gradient_tensors = update_witness["gradient_tensors"]
    delta_tensors = update_witness["delta_tensors"]

    gradient_match_all = True
    sgd_update_match_all = True
    delta_tensor_match_all = True

    print()
    print("=== GRADIENT / SGD UPDATE CHECKS ===")
    for name, p in recompute_online_net.named_parameters():
        recomputed_grad = p.grad.detach().cpu()
        claimed_grad = torch.tensor(
            gradient_tensors[name],
            dtype=recomputed_grad.dtype,
        )
        claimed_delta = torch.tensor(
            delta_tensors[name],
            dtype=recomputed_grad.dtype,
        )

        actual_pre = pre_named[name]
        actual_post = post_named[name]
        recomputed_delta = actual_post - actual_pre
        expected_post = actual_pre - learning_rate_real * claimed_grad

        gradient_match = torch.allclose(
            recomputed_grad, claimed_grad, atol=1e-8, rtol=1e-6
        )
        delta_tensor_match = torch.allclose(
            recomputed_delta, claimed_delta, atol=1e-8, rtol=1e-6
        )
        sgd_update_match = (
            learning_rate_ok
            and torch.allclose(
                actual_post, expected_post, atol=1e-8, rtol=1e-6
            )
        )

        gradient_match_all = gradient_match_all and gradient_match
        delta_tensor_match_all = delta_tensor_match_all and delta_tensor_match
        sgd_update_match_all = sgd_update_match_all and sgd_update_match

        print(
            f"{name}: "
            f"gradient_match={gradient_match} "
            f"delta_tensor_match={delta_tensor_match} "
            f"sgd_update_match={sgd_update_match}"
        )

    print()
    print("=== PUBLIC / CHECKPOINT CHECKS ===")
    print("pre_checkpoint_ok =", pre_checkpoint_ok)
    print("post_checkpoint_ok =", post_checkpoint_ok)
    print("target_net_unchanged =", target_net_unchanged)
    print("online_net_changed =", online_net_changed)
    print("step_increment_ok =", step_increment_ok)
    print("source_checkpoint_sha_ok =", source_checkpoint_sha_ok)
    print("optimizer_type_ok =", optimizer_type_ok)
    print("learning_rate_ok =", learning_rate_ok)
    print("batch_indices_ok =", batch_indices_ok)
    print("gradient_match_all =", gradient_match_all)
    print("delta_tensor_match_all =", delta_tensor_match_all)
    print("sgd_update_match_all =", sgd_update_match_all)

    verification_passed = (
        all_items_ok
        and batch_loss_match
        and pre_checkpoint_ok
        and post_checkpoint_ok
        and target_net_unchanged
        and online_net_changed
        and step_increment_ok
        and source_checkpoint_sha_ok
        and optimizer_type_ok
        and learning_rate_ok
        and batch_indices_ok
        and loss_type == "smooth_l1"
        and optimizer_type == "sgd"
        and gradient_match_all
        and delta_tensor_match_all
        and sgd_update_match_all
    )

    print()
    print("verification_passed =", verification_passed)

    if not verification_passed:
        print()
        print("NOTE: This verifier checks artifact consistency and checkpoint-step consistency.")
        print("It does NOT yet fully verify gradient arithmetic inside a proving backend.")


if __name__ == "__main__":
    main()