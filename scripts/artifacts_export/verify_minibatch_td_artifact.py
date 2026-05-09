import json
import os
from pathlib import Path
import sys

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments
from zk_offline_dqn.io_utils import file_sha256
from zk_offline_dqn.merkle import hash_leaf as hash_leaf_serialized
from zk_offline_dqn.merkle import verify_merkle_path
from zk_offline_dqn.zk_specs import (
    serialize_transition_leaf,
    compute_td_target_fp,
    compute_smooth_l1_loss_fp,
)

from zk_offline_dqn.artifact_schema_versions import (
    SCHEMA_MINIBATCH_TD_V1,
    require_schema_version,
)

ARTIFACT_PATH = os.environ.get(
    "MINIBATCH_TD_ARTIFACT_PATH",
    "artifacts/minibatch_td_from_dataset.json",
)

CHECKPOINT_PATH = os.environ.get(
    "MINIBATCH_TD_CHECKPOINT_PATH",
    "models/offline_dqn_with_target_seed42_best.pt",
)


def verify_canonical_state_commitments(public, checkpoint_path: str):
    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    recomputed = canonical_checkpoint_state_commitments(checkpoint)

    expected_commitment_type = public.get("checkpoint_commitment_type")
    expected_online_key = public.get("online_state_dict_key")
    expected_online_sha = public.get("online_state_dict_sha256")
    expected_target_sha = public.get("target_state_dict_sha256")

    # Backward compatibility: older artifacts may not contain canonical commitments.
    has_canonical_fields = all(
        value is not None
        for value in [
            expected_commitment_type,
            expected_online_key,
            expected_online_sha,
            expected_target_sha,
        ]
    )

    if not has_canonical_fields:
        return {
            "canonical_commitments_present": False,
            "checkpoint_commitment_type_ok": True,
            "online_state_dict_key_ok": True,
            "online_state_dict_sha256_ok": True,
            "target_state_dict_sha256_ok": True,
            "canonical_state_commitments_ok": True,
            "recomputed": recomputed,
        }

    checkpoint_commitment_type_ok = (
        expected_commitment_type == "sha256_file_and_canonical_state_dicts"
    )
    online_state_dict_key_ok = (
        expected_online_key == recomputed["online_state_dict_key"]
    )
    online_state_dict_sha256_ok = (
        expected_online_sha == recomputed["online_state_dict_sha256"]
    )
    target_state_dict_sha256_ok = (
        expected_target_sha == recomputed["target_state_dict_sha256"]
    )

    canonical_state_commitments_ok = (
        checkpoint_commitment_type_ok
        and online_state_dict_key_ok
        and online_state_dict_sha256_ok
        and target_state_dict_sha256_ok
    )

    return {
        "canonical_commitments_present": True,
        "checkpoint_commitment_type_ok": checkpoint_commitment_type_ok,
        "online_state_dict_key_ok": online_state_dict_key_ok,
        "online_state_dict_sha256_ok": online_state_dict_sha256_ok,
        "target_state_dict_sha256_ok": target_state_dict_sha256_ok,
        "canonical_state_commitments_ok": canonical_state_commitments_ok,
        "recomputed": recomputed,
    }

def main():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    require_schema_version(
        artifact,
        SCHEMA_MINIBATCH_TD_V1,
        artifact_path=ARTIFACT_PATH,
    )

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

    canonical_checks = verify_canonical_state_commitments(
        public=public,
        checkpoint_path=CHECKPOINT_PATH,
    )

    print("\n=== BATCH CHECK ===")
    print("total_loss_fp =", total_loss_fp)
    print("claimed_batch_loss_fp =", claimed_batch_loss_fp)
    print("recomputed_batch_loss_fp =", recomputed_batch_loss_fp)
    print("batch_loss_match =", batch_loss_match)

    print("\n=== PUBLIC CHECKS ===")
    print("expected_checkpoint_sha256 =", expected_checkpoint_sha256)
    print("recomputed_checkpoint_sha256 =", recomputed_checkpoint_sha256)
    print("checkpoint_sha256_ok =", checkpoint_sha256_ok)

    print(
        "canonical_commitments_present =",
        canonical_checks["canonical_commitments_present"],
    )
    print(
        "checkpoint_commitment_type_ok =",
        canonical_checks["checkpoint_commitment_type_ok"],
    )
    print(
        "online_state_dict_key_ok =",
        canonical_checks["online_state_dict_key_ok"],
    )
    print(
        "online_state_dict_sha256_ok =",
        canonical_checks["online_state_dict_sha256_ok"],
    )
    print(
        "target_state_dict_sha256_ok =",
        canonical_checks["target_state_dict_sha256_ok"],
    )
    print(
        "canonical_state_commitments_ok =",
        canonical_checks["canonical_state_commitments_ok"],
    )

    verification_passed = (
        all_items_ok
        and batch_loss_match
        and checkpoint_sha256_ok
        and canonical_checks["canonical_state_commitments_ok"]
    )
    print("\nverification_passed =", verification_passed)


if __name__ == "__main__":
    main()
