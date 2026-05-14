"""Pure one-step update artifact relation checks."""

from __future__ import annotations

from typing import Any, Dict

import torch

from zk_offline_dqn.artifact_export_utils import (
    compute_td_witness,
    compute_training_loss,
    hash_leaf_serialized,
    serialize_leaf,
)
from zk_offline_dqn.artifacts.schemas import (
    SCHEMA_ONE_STEP_UPDATE_V1,
    require_schema_version,
)
from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments
from zk_offline_dqn.core.merkle import recompute_root_from_path
from zk_offline_dqn.zk_specs import (
    compute_smooth_l1_loss_fp,
    compute_td_target_fp,
    encode_fp,
)


def compare_state_dicts(sd1, sd2) -> bool:
    keys1 = set(sd1.keys())
    keys2 = set(sd2.keys())

    if keys1 != keys2:
        return False

    for key in keys1:
        if not torch.equal(sd1[key].detach().cpu(), sd2[key].detach().cpu()):
            return False

    return True


def verify_one_step_canonical_commitments(
    public: Dict[str, Any],
    pre_ckpt: Dict[str, Any],
    post_ckpt: Dict[str, Any],
) -> Dict[str, Any]:
    pre_recomputed = canonical_checkpoint_state_commitments(pre_ckpt)
    post_recomputed = canonical_checkpoint_state_commitments(post_ckpt)

    expected_commitment_type = public.get("checkpoint_commitment_type")

    expected_pre_online_key = public.get("pre_online_state_dict_key")
    expected_pre_online_sha = public.get("pre_online_state_dict_sha256")
    expected_pre_target_sha = public.get("pre_target_state_dict_sha256")

    expected_post_online_key = public.get("post_online_state_dict_key")
    expected_post_online_sha = public.get("post_online_state_dict_sha256")
    expected_post_target_sha = public.get("post_target_state_dict_sha256")

    has_canonical_fields = all(
        value is not None
        for value in [
            expected_commitment_type,
            expected_pre_online_key,
            expected_pre_online_sha,
            expected_pre_target_sha,
            expected_post_online_key,
            expected_post_online_sha,
            expected_post_target_sha,
        ]
    )

    # Backward compatibility for older one-step artifacts.
    if not has_canonical_fields:
        return {
            "canonical_commitments_present": False,
            "checkpoint_commitment_type_ok": True,
            "pre_online_state_dict_key_ok": True,
            "pre_online_state_dict_sha256_ok": True,
            "pre_target_state_dict_sha256_ok": True,
            "post_online_state_dict_key_ok": True,
            "post_online_state_dict_sha256_ok": True,
            "post_target_state_dict_sha256_ok": True,
            "one_step_canonical_commitments_ok": True,
        }

    checkpoint_commitment_type_ok = (
        expected_commitment_type == "sha256_file_and_canonical_state_dicts"
    )

    pre_online_state_dict_key_ok = (
        expected_pre_online_key == pre_recomputed["online_state_dict_key"]
    )
    pre_online_state_dict_sha256_ok = (
        expected_pre_online_sha == pre_recomputed["online_state_dict_sha256"]
    )
    pre_target_state_dict_sha256_ok = (
        expected_pre_target_sha == pre_recomputed["target_state_dict_sha256"]
    )

    post_online_state_dict_key_ok = (
        expected_post_online_key == post_recomputed["online_state_dict_key"]
    )
    post_online_state_dict_sha256_ok = (
        expected_post_online_sha == post_recomputed["online_state_dict_sha256"]
    )
    post_target_state_dict_sha256_ok = (
        expected_post_target_sha == post_recomputed["target_state_dict_sha256"]
    )

    one_step_canonical_commitments_ok = (
        checkpoint_commitment_type_ok
        and pre_online_state_dict_key_ok
        and pre_online_state_dict_sha256_ok
        and pre_target_state_dict_sha256_ok
        and post_online_state_dict_key_ok
        and post_online_state_dict_sha256_ok
        and post_target_state_dict_sha256_ok
    )

    return {
        "canonical_commitments_present": True,
        "checkpoint_commitment_type_ok": checkpoint_commitment_type_ok,
        "pre_online_state_dict_key_ok": pre_online_state_dict_key_ok,
        "pre_online_state_dict_sha256_ok": pre_online_state_dict_sha256_ok,
        "pre_target_state_dict_sha256_ok": pre_target_state_dict_sha256_ok,
        "post_online_state_dict_key_ok": post_online_state_dict_key_ok,
        "post_online_state_dict_sha256_ok": post_online_state_dict_sha256_ok,
        "post_target_state_dict_sha256_ok": post_target_state_dict_sha256_ok,
        "one_step_canonical_commitments_ok": one_step_canonical_commitments_ok,
    }


def validate_one_step_update_schema(
    artifact: Dict[str, Any],
    *,
    artifact_path: str = "",
) -> None:
    require_schema_version(
        artifact,
        SCHEMA_ONE_STEP_UPDATE_V1,
        artifact_path=artifact_path,
    )


def check_one_step_update_artifact(
    artifact: Dict[str, Any],
    *,
    verifier_online_net,
    verifier_target_net,
    recompute_online_net,
    recompute_target_net,
    pre_ckpt: Dict[str, Any],
    post_ckpt: Dict[str, Any],
    pre_checkpoint_sha256_recomputed: str,
    post_checkpoint_sha256_recomputed: str,
    artifact_path: str = "",
    validate_schema: bool = True,
) -> Dict[str, Any]:
    if validate_schema:
        validate_one_step_update_schema(artifact, artifact_path=artifact_path)

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

    all_items_ok = True
    total_loss_fp = 0
    item_results = []

    for i, item in enumerate(artifact["items"]):
        idx = item["index"]
        transition = item["transition"]
        leaf = item["leaf"]
        claimed_leaf_hash = item["leaf_hash"]
        merkle_path = item["merkle_path"]
        w = item["td_witness"]

        recomputed_witness_pack = compute_td_witness(
            transition=transition,
            online_net=verifier_online_net,
            target_net=verifier_target_net,
        )

        recomputed_w = recomputed_witness_pack["td_witness"]

        recomputed_leaf = serialize_leaf(transition)
        leaf_match = recomputed_leaf == leaf

        recomputed_leaf_hash = hash_leaf_serialized(leaf)
        leaf_hash_match = recomputed_leaf_hash == claimed_leaf_hash

        recomputed_root = recompute_root_from_path(claimed_leaf_hash, merkle_path)
        merkle_ok = recomputed_root == dataset_root

        next_action_match = (
            int(w["next_action_online"]) == int(recomputed_w["next_action_online"])
        )

        q_target_max_match = (
            int(w["q_target_max_fp"]) == int(recomputed_w["q_target_max_fp"])
        )

        reward_fp = encode_fp(float(transition["reward"]))
        done = int(transition["done"])

        recomputed_target_fp = compute_td_target_fp(
            reward_fp=reward_fp,
            done=done,
            q_target_max_fp=int(w["q_target_max_fp"]),
        )
        target_match = recomputed_target_fp == int(w["target_fp"])

        recomputed_loss_fp = compute_smooth_l1_loss_fp(
            q_online_fp=int(w["q_online_fp"]),
            target_fp=int(w["target_fp"]),
        )
        loss_match = recomputed_loss_fp == int(w["loss_fp"])

        index_match = idx == batch_indices[i]

        item_ok = (
            leaf_match
            and leaf_hash_match
            and merkle_ok
            and next_action_match
            and q_target_max_match
            and target_match
            and loss_match
            and index_match
        )

        all_items_ok = all_items_ok and item_ok
        total_loss_fp += int(w["loss_fp"])

        item_results.append(
            {
                "position": i,
                "index": idx,
                "index_match": index_match,
                "leaf_match": leaf_match,
                "leaf_hash_match": leaf_hash_match,
                "merkle_ok": merkle_ok,
                "next_action_match": next_action_match,
                "q_target_max_match": q_target_max_match,
                "target_match": target_match,
                "loss_match": loss_match,
                "item_ok": item_ok,
            }
        )

    recomputed_batch_loss_fp = total_loss_fp // batch_size
    claimed_batch_loss_fp = int(update_witness["batch_loss_fp"])
    batch_loss_match = recomputed_batch_loss_fp == claimed_batch_loss_fp

    pre_checkpoint_ok = pre_checkpoint_sha256_recomputed == pre_checkpoint_sha256
    post_checkpoint_ok = post_checkpoint_sha256_recomputed == post_checkpoint_sha256

    canonical_checks = verify_one_step_canonical_commitments(
        public=public,
        pre_ckpt=pre_ckpt,
        post_ckpt=post_ckpt,
    )

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
    optimizer_type_ok = metadata.get("optimizer_type") == optimizer_type

    metadata_lr = metadata.get("learning_rate", None)
    learning_rate_real = float(metadata_lr) if metadata_lr is not None else 0.0
    learning_rate_ok = (
        metadata_lr is not None
        and encode_fp(learning_rate_real) == learning_rate_fp
    )

    batch_indices_ok = metadata.get("batch_indices") == batch_indices

    pre_named = {
        key: value.detach().cpu()
        for key, value in pre_online_state.items()
    }
    post_named = {
        key: value.detach().cpu()
        for key, value in post_online_state.items()
    }

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
    gradient_results = []

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
            recomputed_grad,
            claimed_grad,
            atol=1e-8,
            rtol=1e-6,
        )
        delta_tensor_match = torch.allclose(
            recomputed_delta,
            claimed_delta,
            atol=1e-8,
            rtol=1e-6,
        )
        sgd_update_match = (
            learning_rate_ok
            and torch.allclose(
                actual_post,
                expected_post,
                atol=1e-8,
                rtol=1e-6,
            )
        )

        gradient_match_all = gradient_match_all and gradient_match
        delta_tensor_match_all = delta_tensor_match_all and delta_tensor_match
        sgd_update_match_all = sgd_update_match_all and sgd_update_match

        gradient_results.append(
            {
                "name": name,
                "gradient_match": gradient_match,
                "delta_tensor_match": delta_tensor_match,
                "sgd_update_match": sgd_update_match,
            }
        )

    verification_passed = (
        all_items_ok
        and batch_loss_match
        and pre_checkpoint_ok
        and post_checkpoint_ok
        and canonical_checks["one_step_canonical_commitments_ok"]
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

    return {
        "public": public,
        "update_witness": update_witness,
        "dataset_root": dataset_root,
        "batch_indices": batch_indices,
        "batch_size": batch_size,
        "loss_type": loss_type,
        "optimizer_type": optimizer_type,
        "learning_rate_fp": learning_rate_fp,
        "item_results": item_results,
        "all_items_ok": all_items_ok,
        "total_loss_fp": total_loss_fp,
        "claimed_batch_loss_fp": claimed_batch_loss_fp,
        "recomputed_batch_loss_fp": recomputed_batch_loss_fp,
        "batch_loss_match": batch_loss_match,
        "pre_checkpoint_sha256_recomputed": pre_checkpoint_sha256_recomputed,
        "post_checkpoint_sha256_recomputed": post_checkpoint_sha256_recomputed,
        "pre_checkpoint_ok": pre_checkpoint_ok,
        "post_checkpoint_ok": post_checkpoint_ok,
        "canonical_checks": canonical_checks,
        "target_net_unchanged": target_net_unchanged,
        "online_net_changed": online_net_changed,
        "step_increment_ok": step_increment_ok,
        "source_checkpoint_sha_ok": source_checkpoint_sha_ok,
        "optimizer_type_ok": optimizer_type_ok,
        "learning_rate_ok": learning_rate_ok,
        "batch_indices_ok": batch_indices_ok,
        "gradient_results": gradient_results,
        "gradient_match_all": gradient_match_all,
        "delta_tensor_match_all": delta_tensor_match_all,
        "sgd_update_match_all": sgd_update_match_all,
        "verification_passed": verification_passed,
    }
