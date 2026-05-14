"""Pure minibatch TD artifact relation checks."""

from __future__ import annotations

from typing import Any, Dict

from zk_offline_dqn.artifact_schema_versions import (
    SCHEMA_MINIBATCH_TD_V1,
    require_schema_version,
)
from zk_offline_dqn.core.merkle import hash_leaf as hash_leaf_serialized
from zk_offline_dqn.core.merkle import verify_merkle_path
from zk_offline_dqn.zk_specs import (
    compute_smooth_l1_loss_fp,
    compute_td_target_fp,
    serialize_transition_leaf,
)


def verify_merkle_path_metadata(merkle_path, leaf_index: int):
    expected_current_index = int(leaf_index)

    for expected_level, step in enumerate(merkle_path):
        level_ok = int(step["level"]) == expected_level
        current_index = int(step["current_index"])
        sibling_index = int(step["sibling_index"])
        current_is_left = bool(step["current_is_left"])

        current_ok = current_index == expected_current_index
        if current_is_left:
            sibling_ok = (
                expected_current_index % 2 == 0
                and sibling_index in {expected_current_index, expected_current_index + 1}
            )
        else:
            sibling_ok = (
                expected_current_index % 2 == 1
                and sibling_index == expected_current_index - 1
            )

        if not (level_ok and current_ok and sibling_ok):
            return False

        expected_current_index //= 2

    return True


def check_minibatch_td_artifact(
    artifact: Dict[str, Any],
    *,
    artifact_path: str = "",
) -> Dict[str, Any]:
    require_schema_version(
        artifact,
        SCHEMA_MINIBATCH_TD_V1,
        artifact_path=artifact_path,
    )

    public = artifact["public"]
    items = artifact["items"]

    dataset_root = public["dataset_root"]
    batch_size = int(public["batch_size"])
    batch_mode = public.get("batch_mode")
    claimed_leaf_indices = public.get("leaf_indices")
    loss_type = public["loss_type"]
    claimed_batch_loss_fp = int(public["batch_loss_fp"])

    if loss_type != "smooth_l1":
        raise ValueError(f"Expected loss_type='smooth_l1', got {loss_type}")

    all_items_ok = True
    total_loss_fp = 0
    item_indices = [int(item["index"]) for item in items]
    batch_size_ok = batch_size == len(items) and batch_size > 0
    leaf_indices_match = (
        True
        if claimed_leaf_indices is None
        else [int(index) for index in claimed_leaf_indices] == item_indices
    )
    distinct_required = batch_mode == "distinct" or claimed_leaf_indices is not None
    distinct_indices_ok = (
        True if not distinct_required else len(set(item_indices)) == len(item_indices)
    )

    item_results = []
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
        path_metadata_ok = verify_merkle_path_metadata(
            merkle_path=merkle_path,
            leaf_index=int(item["index"]),
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
            and path_metadata_ok
            and target_match
            and loss_match
        )

        total_loss_fp += claimed_loss_fp
        all_items_ok = all_items_ok and item_ok

        item_results.append(
            {
                "position": i,
                "index": item["index"],
                "leaf_match": leaf_match,
                "leaf_hash_match": leaf_hash_match,
                "merkle_ok": merkle_ok,
                "path_metadata_ok": path_metadata_ok,
                "target_match": target_match,
                "loss_match": loss_match,
                "item_ok": item_ok,
            }
        )

    recomputed_batch_loss_fp = total_loss_fp // batch_size if batch_size > 0 else None
    batch_loss_match = recomputed_batch_loss_fp == claimed_batch_loss_fp

    relation_passed = (
        all_items_ok
        and batch_size_ok
        and leaf_indices_match
        and distinct_indices_ok
        and batch_loss_match
    )

    return {
        "public": public,
        "items": items,
        "dataset_root": dataset_root,
        "batch_size": batch_size,
        "batch_mode": batch_mode,
        "leaf_indices": claimed_leaf_indices,
        "loss_type": loss_type,
        "item_results": item_results,
        "all_items_ok": all_items_ok,
        "batch_size_ok": batch_size_ok,
        "leaf_indices_match": leaf_indices_match,
        "distinct_indices_ok": distinct_indices_ok,
        "total_loss_fp": total_loss_fp,
        "claimed_batch_loss_fp": claimed_batch_loss_fp,
        "recomputed_batch_loss_fp": recomputed_batch_loss_fp,
        "batch_loss_match": batch_loss_match,
        "relation_passed": relation_passed,
    }
