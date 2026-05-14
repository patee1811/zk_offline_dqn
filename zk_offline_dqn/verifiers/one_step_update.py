"""One-step update artifact verifier adapter."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import torch

from zk_offline_dqn.artifact_export_utils import (
    file_sha256,
    load_checkpoint_nets,
    load_merkle_artifact,
)
from zk_offline_dqn.relations.one_step_update import (
    check_one_step_update_artifact,
    validate_one_step_update_schema,
)


DEFAULT_ARTIFACT_PATH = "artifacts/one_step_update_artifact.json"
DEFAULT_MERKLE_PATH = "artifacts/cartpole_dqn_eps010_merkle.json"
DEFAULT_CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"
DEFAULT_POST_CHECKPOINT_PATH = "artifacts/one_step_post_checkpoint.pt"


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_checkpoint_paths(
    artifact: Dict[str, Any],
    *,
    checkpoint_path: Optional[str] = None,
    post_checkpoint_path: Optional[str] = None,
) -> tuple[str, str]:
    notes = artifact.get("notes", {})
    resolved_checkpoint_path = (
        checkpoint_path
        if checkpoint_path is not None
        else notes.get("checkpoint_path", DEFAULT_CHECKPOINT_PATH)
    )
    resolved_post_checkpoint_path = (
        post_checkpoint_path
        if post_checkpoint_path is not None
        else notes.get("post_checkpoint_path", DEFAULT_POST_CHECKPOINT_PATH)
    )
    return resolved_checkpoint_path, resolved_post_checkpoint_path


def verify_one_step_update_artifact(
    artifact: Dict[str, Any],
    *,
    artifact_path: str = "",
    merkle_path: str = DEFAULT_MERKLE_PATH,
    checkpoint_path: Optional[str] = None,
    post_checkpoint_path: Optional[str] = None,
) -> Dict[str, Any]:
    validate_one_step_update_schema(artifact, artifact_path=artifact_path)

    # Preserve the old verifier's file validation behavior. The loaded Merkle
    # artifact is not otherwise used by the one-step checks.
    load_merkle_artifact(merkle_path)

    resolved_checkpoint_path, resolved_post_checkpoint_path = resolve_checkpoint_paths(
        artifact,
        checkpoint_path=checkpoint_path,
        post_checkpoint_path=post_checkpoint_path,
    )

    _, verifier_online_net, verifier_target_net = load_checkpoint_nets(
        resolved_checkpoint_path
    )

    pre_checkpoint_sha256_recomputed = file_sha256(resolved_checkpoint_path)
    post_checkpoint_sha256_recomputed = file_sha256(resolved_post_checkpoint_path)

    pre_ckpt = torch.load(
        resolved_checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )
    post_ckpt = torch.load(
        resolved_post_checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    _, recompute_online_net, recompute_target_net = load_checkpoint_nets(
        resolved_checkpoint_path
    )

    return check_one_step_update_artifact(
        artifact,
        verifier_online_net=verifier_online_net,
        verifier_target_net=verifier_target_net,
        recompute_online_net=recompute_online_net,
        recompute_target_net=recompute_target_net,
        pre_ckpt=pre_ckpt,
        post_ckpt=post_ckpt,
        pre_checkpoint_sha256_recomputed=pre_checkpoint_sha256_recomputed,
        post_checkpoint_sha256_recomputed=post_checkpoint_sha256_recomputed,
        artifact_path=artifact_path,
        validate_schema=False,
    )


def verify_one_step_update_artifact_path(
    artifact_path: str = DEFAULT_ARTIFACT_PATH,
    *,
    merkle_path: str = DEFAULT_MERKLE_PATH,
    checkpoint_path: Optional[str] = None,
    post_checkpoint_path: Optional[str] = None,
) -> Dict[str, Any]:
    artifact = load_json(artifact_path)
    return verify_one_step_update_artifact(
        artifact,
        artifact_path=artifact_path,
        merkle_path=merkle_path,
        checkpoint_path=checkpoint_path,
        post_checkpoint_path=post_checkpoint_path,
    )


def format_one_step_update_report(result: Dict[str, Any], artifact_path: str) -> str:
    lines = [
        "=== VERIFY ONE-STEP UPDATE ARTIFACT ===",
        f"artifact_path = {artifact_path}",
        f"dataset_root = {result['dataset_root']}",
        f"batch_indices = {result['batch_indices']}",
        f"batch_size = {result['batch_size']}",
        f"loss_type = {result['loss_type']}",
        f"optimizer_type = {result['optimizer_type']}",
        f"learning_rate_fp = {result['learning_rate_fp']}",
        "",
        "=== PER-ITEM CHECKS ===",
    ]

    for item in result["item_results"]:
        lines.append(
            f"item[{item['position']}] index={item['index']} "
            f"index_match={item['index_match']} "
            f"leaf_match={item['leaf_match']} "
            f"leaf_hash_match={item['leaf_hash_match']} "
            f"merkle_ok={item['merkle_ok']} "
            f"next_action_match={item['next_action_match']} "
            f"q_target_max_match={item['q_target_max_match']} "
            f"target_match={item['target_match']} "
            f"loss_match={item['loss_match']} "
            f"item_ok={item['item_ok']}"
        )

    lines.extend(
        [
            "",
            "=== BATCH CHECK ===",
            f"total_loss_fp = {result['total_loss_fp']}",
            f"claimed_batch_loss_fp = {result['claimed_batch_loss_fp']}",
            f"recomputed_batch_loss_fp = {result['recomputed_batch_loss_fp']}",
            f"batch_loss_match = {result['batch_loss_match']}",
            "",
            "=== GRADIENT / SGD UPDATE CHECKS ===",
        ]
    )

    for item in result["gradient_results"]:
        lines.append(
            f"{item['name']}: "
            f"gradient_match={item['gradient_match']} "
            f"delta_tensor_match={item['delta_tensor_match']} "
            f"sgd_update_match={item['sgd_update_match']}"
        )

    canonical_checks = result["canonical_checks"]
    lines.extend(
        [
            "",
            "=== PUBLIC / CHECKPOINT CHECKS ===",
            f"pre_checkpoint_ok = {result['pre_checkpoint_ok']}",
            f"post_checkpoint_ok = {result['post_checkpoint_ok']}",
            f"canonical_commitments_present = {canonical_checks['canonical_commitments_present']}",
            f"checkpoint_commitment_type_ok = {canonical_checks['checkpoint_commitment_type_ok']}",
            f"pre_online_state_dict_key_ok = {canonical_checks['pre_online_state_dict_key_ok']}",
            f"pre_online_state_dict_sha256_ok = {canonical_checks['pre_online_state_dict_sha256_ok']}",
            f"pre_target_state_dict_sha256_ok = {canonical_checks['pre_target_state_dict_sha256_ok']}",
            f"post_online_state_dict_key_ok = {canonical_checks['post_online_state_dict_key_ok']}",
            f"post_online_state_dict_sha256_ok = {canonical_checks['post_online_state_dict_sha256_ok']}",
            f"post_target_state_dict_sha256_ok = {canonical_checks['post_target_state_dict_sha256_ok']}",
            f"one_step_canonical_commitments_ok = {canonical_checks['one_step_canonical_commitments_ok']}",
            f"target_net_unchanged = {result['target_net_unchanged']}",
            f"online_net_changed = {result['online_net_changed']}",
            f"step_increment_ok = {result['step_increment_ok']}",
            f"source_checkpoint_sha_ok = {result['source_checkpoint_sha_ok']}",
            f"optimizer_type_ok = {result['optimizer_type_ok']}",
            f"learning_rate_ok = {result['learning_rate_ok']}",
            f"batch_indices_ok = {result['batch_indices_ok']}",
            f"gradient_match_all = {result['gradient_match_all']}",
            f"delta_tensor_match_all = {result['delta_tensor_match_all']}",
            f"sgd_update_match_all = {result['sgd_update_match_all']}",
            "",
            f"verification_passed = {result['verification_passed']}",
        ]
    )

    if not result["verification_passed"]:
        lines.extend(
            [
                "",
                "NOTE: This verifier checks artifact consistency and checkpoint-step consistency.",
                "It does NOT yet fully verify gradient arithmetic inside a proving backend.",
            ]
        )

    return "\n".join(lines)


def verify_one_step_update_artifact_path_report(
    artifact_path: str = DEFAULT_ARTIFACT_PATH,
    *,
    merkle_path: str = DEFAULT_MERKLE_PATH,
    checkpoint_path: Optional[str] = None,
    post_checkpoint_path: Optional[str] = None,
) -> tuple[Dict[str, Any], str]:
    result = verify_one_step_update_artifact_path(
        artifact_path=artifact_path,
        merkle_path=merkle_path,
        checkpoint_path=checkpoint_path,
        post_checkpoint_path=post_checkpoint_path,
    )
    return result, format_one_step_update_report(result, artifact_path)
