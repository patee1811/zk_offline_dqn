"""Minibatch TD artifact verifier adapter."""

from __future__ import annotations

from typing import Any, Dict

import torch

from zk_offline_dqn.artifacts.io import load_json_artifact
from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments
from zk_offline_dqn.io_utils import file_sha256
from zk_offline_dqn.relations.minibatch_td import check_minibatch_td_artifact


DEFAULT_ARTIFACT_PATH = "artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json"
DEFAULT_CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"


def load_json(path: str) -> Dict[str, Any]:
    return load_json_artifact(path)


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


def verify_minibatch_td_artifact(
    artifact: Dict[str, Any],
    *,
    checkpoint_path: str = DEFAULT_CHECKPOINT_PATH,
    artifact_path: str = "",
) -> Dict[str, Any]:
    result = check_minibatch_td_artifact(artifact, artifact_path=artifact_path)
    public = result["public"]

    expected_checkpoint_sha256 = public.get("checkpoint_sha256")
    recomputed_checkpoint_sha256 = file_sha256(checkpoint_path)
    checkpoint_sha256_ok = expected_checkpoint_sha256 == recomputed_checkpoint_sha256

    canonical_checks = verify_canonical_state_commitments(
        public=public,
        checkpoint_path=checkpoint_path,
    )

    verification_passed = (
        result["all_items_ok"]
        and result["batch_size_ok"]
        and result["leaf_indices_match"]
        and result["distinct_indices_ok"]
        and result["batch_loss_match"]
        and checkpoint_sha256_ok
        and canonical_checks["canonical_state_commitments_ok"]
    )

    return {
        **result,
        "expected_checkpoint_sha256": expected_checkpoint_sha256,
        "recomputed_checkpoint_sha256": recomputed_checkpoint_sha256,
        "checkpoint_sha256_ok": checkpoint_sha256_ok,
        "canonical_checks": canonical_checks,
        "verification_passed": verification_passed,
    }


def verify_minibatch_td_artifact_path(
    artifact_path: str = DEFAULT_ARTIFACT_PATH,
    checkpoint_path: str = DEFAULT_CHECKPOINT_PATH,
) -> Dict[str, Any]:
    artifact = load_json(artifact_path)
    return verify_minibatch_td_artifact(
        artifact,
        checkpoint_path=checkpoint_path,
        artifact_path=artifact_path,
    )


def format_minibatch_td_report(result: Dict[str, Any], artifact_path: str) -> str:
    lines = [
        "=== VERIFY MINIBATCH TD ARTIFACT ===",
        f"artifact_path = {artifact_path}",
        f"dataset_root = {result['dataset_root']}",
        f"batch_size = {result['batch_size']}",
        f"batch_mode = {result['batch_mode']}",
        f"leaf_indices = {result['leaf_indices']}",
        f"loss_type = {result['loss_type']}",
        "",
        "=== PER-ITEM CHECKS ===",
    ]

    for item in result["item_results"]:
        lines.append(
            f"item[{item['position']}] index={item['index']} "
            f"leaf_match={item['leaf_match']} "
            f"leaf_hash_match={item['leaf_hash_match']} "
            f"merkle_ok={item['merkle_ok']} "
            f"path_metadata_ok={item['path_metadata_ok']} "
            f"target_match={item['target_match']} "
            f"loss_match={item['loss_match']} "
            f"item_ok={item['item_ok']}"
        )

    canonical_checks = result["canonical_checks"]
    lines.extend(
        [
            "",
            "=== BATCH CHECK ===",
            f"batch_size_ok = {result['batch_size_ok']}",
            f"leaf_indices_match = {result['leaf_indices_match']}",
            f"distinct_indices_ok = {result['distinct_indices_ok']}",
            f"total_loss_fp = {result['total_loss_fp']}",
            f"claimed_batch_loss_fp = {result['claimed_batch_loss_fp']}",
            f"recomputed_batch_loss_fp = {result['recomputed_batch_loss_fp']}",
            f"batch_loss_match = {result['batch_loss_match']}",
            "",
            "=== PUBLIC CHECKS ===",
            f"expected_checkpoint_sha256 = {result['expected_checkpoint_sha256']}",
            f"recomputed_checkpoint_sha256 = {result['recomputed_checkpoint_sha256']}",
            f"checkpoint_sha256_ok = {result['checkpoint_sha256_ok']}",
            f"canonical_commitments_present = {canonical_checks['canonical_commitments_present']}",
            f"checkpoint_commitment_type_ok = {canonical_checks['checkpoint_commitment_type_ok']}",
            f"online_state_dict_key_ok = {canonical_checks['online_state_dict_key_ok']}",
            f"online_state_dict_sha256_ok = {canonical_checks['online_state_dict_sha256_ok']}",
            f"target_state_dict_sha256_ok = {canonical_checks['target_state_dict_sha256_ok']}",
            f"canonical_state_commitments_ok = {canonical_checks['canonical_state_commitments_ok']}",
            "",
            f"verification_passed = {result['verification_passed']}",
        ]
    )
    return "\n".join(lines)


def verify_minibatch_td_artifact_path_report(
    artifact_path: str = DEFAULT_ARTIFACT_PATH,
    checkpoint_path: str = DEFAULT_CHECKPOINT_PATH,
) -> tuple[Dict[str, Any], str]:
    result = verify_minibatch_td_artifact_path(
        artifact_path=artifact_path,
        checkpoint_path=checkpoint_path,
    )
    return result, format_minibatch_td_report(result, artifact_path)
