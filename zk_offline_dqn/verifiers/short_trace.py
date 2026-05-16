"""Short-trace update artifact verifier adapter."""

from __future__ import annotations

import os
import traceback
from typing import Any, Dict, Optional

import torch

from zk_offline_dqn.artifacts.io import load_json_artifact
from zk_offline_dqn.io_utils import file_sha256
from zk_offline_dqn.relations.short_trace import (
    check_short_trace_artifact,
    step_checkpoint_paths,
    validate_short_trace_schema,
)
from zk_offline_dqn.verifiers.one_step_update import (
    format_one_step_update_report,
    verify_one_step_update_artifact,
)


DEFAULT_ARTIFACT_PATH = "artifacts/fixtures/short_trace/short_trace_update_artifact.json"


def load_json(path: str) -> Dict[str, Any]:
    return load_json_artifact(path)


def load_checkpoint(path: str) -> Dict[str, Any]:
    return torch.load(
        path,
        map_location="cpu",
        weights_only=False,
    )


def resolve_short_trace_paths(
    artifact: Dict[str, Any],
    *,
    merkle_path: Optional[str] = None,
    initial_checkpoint_path: Optional[str] = None,
    final_checkpoint_path: Optional[str] = None,
    work_dir: Optional[str] = None,
) -> tuple[str, str, str, str]:
    notes = artifact.get("notes", {})

    resolved_merkle_path = (
        merkle_path if merkle_path is not None else notes.get("merkle_path")
    )
    resolved_initial_checkpoint_path = (
        initial_checkpoint_path
        if initial_checkpoint_path is not None
        else notes.get("initial_checkpoint_path")
    )
    resolved_final_checkpoint_path = (
        final_checkpoint_path
        if final_checkpoint_path is not None
        else notes.get("final_checkpoint_path")
    )
    resolved_work_dir = (
        work_dir
        if work_dir is not None
        else (
            os.path.dirname(resolved_final_checkpoint_path)
            if resolved_final_checkpoint_path
            else ""
        )
    )

    if not resolved_merkle_path:
        raise ValueError(
            "Missing merkle path: provide SHORT_TRACE_MERKLE_PATH "
            "or keep notes['merkle_path']."
        )

    if not resolved_initial_checkpoint_path:
        raise ValueError(
            "Missing initial checkpoint path: provide SHORT_TRACE_INITIAL_CHECKPOINT_PATH "
            "or keep notes['initial_checkpoint_path']."
        )

    if not resolved_final_checkpoint_path:
        raise ValueError(
            "Missing final checkpoint path: provide SHORT_TRACE_FINAL_CHECKPOINT_PATH "
            "or keep notes['final_checkpoint_path']."
        )

    if not resolved_work_dir:
        raise ValueError(
            "Missing short-trace work dir: provide SHORT_TRACE_WORK_DIR "
            "or use a final checkpoint path located inside the trace work directory."
        )

    return (
        resolved_merkle_path,
        resolved_initial_checkpoint_path,
        resolved_final_checkpoint_path,
        resolved_work_dir,
    )


def verify_embedded_one_step_artifact(
    one_step_artifact: Dict[str, Any],
    *,
    merkle_path: str,
    checkpoint_path: str,
    post_checkpoint_path: str,
) -> Dict[str, Any]:
    embedded_artifact_path = "<embedded_one_step_artifact>"

    try:
        result = verify_one_step_update_artifact(
            one_step_artifact,
            artifact_path=embedded_artifact_path,
            merkle_path=merkle_path,
            checkpoint_path=checkpoint_path,
            post_checkpoint_path=post_checkpoint_path,
        )
        report = format_one_step_update_report(result, embedded_artifact_path)
        return {
            "accepted": bool(result["verification_passed"]),
            "returncode": 0,
            "stdout": report + "\n",
            "stderr": "",
            "result": result,
        }
    except Exception:
        return {
            "accepted": False,
            "returncode": 1,
            "stdout": "",
            "stderr": traceback.format_exc(),
            "result": None,
        }


def verify_short_trace_artifact(
    artifact: Dict[str, Any],
    *,
    artifact_path: str = "",
    merkle_path: Optional[str] = None,
    initial_checkpoint_path: Optional[str] = None,
    final_checkpoint_path: Optional[str] = None,
    work_dir: Optional[str] = None,
) -> Dict[str, Any]:
    validate_short_trace_schema(artifact, artifact_path=artifact_path)

    (
        resolved_merkle_path,
        resolved_initial_checkpoint_path,
        resolved_final_checkpoint_path,
        resolved_work_dir,
    ) = resolve_short_trace_paths(
        artifact,
        merkle_path=merkle_path,
        initial_checkpoint_path=initial_checkpoint_path,
        final_checkpoint_path=final_checkpoint_path,
        work_dir=work_dir,
    )

    initial_checkpoint_sha256_recomputed = file_sha256(
        resolved_initial_checkpoint_path
    )
    final_checkpoint_sha256_recomputed = file_sha256(resolved_final_checkpoint_path)

    initial_checkpoint = load_checkpoint(resolved_initial_checkpoint_path)
    final_checkpoint = load_checkpoint(resolved_final_checkpoint_path)

    current_step_checkpoint_path = resolved_initial_checkpoint_path
    one_step_results = []

    for i, step in enumerate(artifact["steps"]):
        one_step_artifact = step["one_step_artifact"]
        step_post_checkpoint_path, step_synced_checkpoint_path = step_checkpoint_paths(
            resolved_work_dir,
            i,
            one_step_artifact["public"]["batch_indices"],
        )

        one_step_result = verify_embedded_one_step_artifact(
            one_step_artifact=one_step_artifact,
            merkle_path=resolved_merkle_path,
            checkpoint_path=current_step_checkpoint_path,
            post_checkpoint_path=step_post_checkpoint_path,
        )
        one_step_results.append(one_step_result)

        if step["target_sync_applied"]:
            current_step_checkpoint_path = step_synced_checkpoint_path
        else:
            current_step_checkpoint_path = step_post_checkpoint_path

    result = check_short_trace_artifact(
        artifact,
        initial_checkpoint_sha256_recomputed=initial_checkpoint_sha256_recomputed,
        final_checkpoint_sha256_recomputed=final_checkpoint_sha256_recomputed,
        initial_checkpoint=initial_checkpoint,
        final_checkpoint=final_checkpoint,
        one_step_verification_results=one_step_results,
        artifact_path=artifact_path,
        validate_schema=False,
    )

    result["resolved_paths"] = {
        "merkle_path": resolved_merkle_path,
        "initial_checkpoint_path": resolved_initial_checkpoint_path,
        "final_checkpoint_path": resolved_final_checkpoint_path,
        "work_dir": resolved_work_dir,
    }
    return result


def verify_short_trace_artifact_path(
    artifact_path: str = DEFAULT_ARTIFACT_PATH,
    *,
    merkle_path: Optional[str] = None,
    initial_checkpoint_path: Optional[str] = None,
    final_checkpoint_path: Optional[str] = None,
    work_dir: Optional[str] = None,
) -> Dict[str, Any]:
    artifact = load_json(artifact_path)
    return verify_short_trace_artifact(
        artifact,
        artifact_path=artifact_path,
        merkle_path=merkle_path,
        initial_checkpoint_path=initial_checkpoint_path,
        final_checkpoint_path=final_checkpoint_path,
        work_dir=work_dir,
    )


def format_short_trace_report(result: Dict[str, Any], artifact_path: str) -> str:
    canonical_checks = result["canonical_boundary_checks"]

    lines = [
        "=== VERIFY SHORT TRACE UPDATE ARTIFACT ===",
        f"artifact_path = {artifact_path}",
        f"dataset_root = {result['dataset_root']}",
        f"num_steps = {result['num_steps']}",
        f"trace_batch_indices = {result['trace_batch_indices']}",
        f"batch_size = {result['batch_size']}",
        f"sampling_rule_type = {result['sampling_rule_type']}",
        f"start_offset = {result['start_offset']}",
        f"sampling_seed = {result['sampling_seed']}",
        f"dataset_size = {result['dataset_size']}",
        f"optimizer_type = {result['optimizer_type']}",
        f"loss_type = {result['loss_type']}",
        f"target_sync_every = {result['target_sync_every']}",
        "",
        "=== GLOBAL CHECKS ===",
        f"num_steps_match = {result['num_steps_match']}",
        f"initial_checkpoint_ok = {result['initial_checkpoint_ok']}",
        f"final_checkpoint_ok = {result['final_checkpoint_ok']}",
        "canonical_boundary_commitments_present = "
        f"{canonical_checks['canonical_boundary_commitments_present']}",
        "checkpoint_commitment_type_ok = "
        f"{canonical_checks['checkpoint_commitment_type_ok']}",
        "initial_online_state_dict_key_ok = "
        f"{canonical_checks['initial_online_state_dict_key_ok']}",
        "initial_online_state_dict_sha256_ok = "
        f"{canonical_checks['initial_online_state_dict_sha256_ok']}",
        "initial_target_state_dict_sha256_ok = "
        f"{canonical_checks['initial_target_state_dict_sha256_ok']}",
        "final_online_state_dict_key_ok = "
        f"{canonical_checks['final_online_state_dict_key_ok']}",
        "final_online_state_dict_sha256_ok = "
        f"{canonical_checks['final_online_state_dict_sha256_ok']}",
        "final_target_state_dict_sha256_ok = "
        f"{canonical_checks['final_target_state_dict_sha256_ok']}",
        "short_trace_canonical_boundary_commitments_ok = "
        f"{canonical_checks['short_trace_canonical_boundary_commitments_ok']}",
        f"sampling_rule_supported = {result['sampling_rule_supported']}",
        "",
        "=== STEP CHECKS ===",
    ]

    for step in result["step_results"]:
        lines.append(
            f"step={step['step_index']} "
            f"step_index_ok={step['step_index_ok']} "
            f"batch_indices_ok={step['batch_indices_ok']} "
            f"sampling_rule_public_ok={step['sampling_rule_public_ok']} "
            f"sampling_rule_step_ok={step['sampling_rule_step_ok']} "
            f"dataset_root_ok={step['dataset_root_ok']} "
            f"optimizer_ok={step['optimizer_ok']} "
            f"loss_type_ok={step['loss_type_ok']} "
            f"chain_ok={step['chain_ok']} "
            f"sync_logic_ok={step['sync_logic_ok']} "
            f"one_step_verification_ok={step['one_step_verification_ok']}"
        )

        if not step["sampling_rule_ok"]:
            lines.extend(
                [
                    "--- SAMPLING RULE DETAILS ---",
                    f"expected_batch_indices = {step['expected_batch_indices']}",
                    f"public_batch_indices = {step['public_batch_indices']}",
                    f"step_batch_indices = {step['step_batch_indices']}",
                ]
            )

        if not step["one_step_verification_ok"]:
            lines.extend(
                [
                    "--- ONE-STEP VERIFY STDOUT ---",
                    str(step["one_step_stdout"]).rstrip("\n"),
                    "--- ONE-STEP VERIFY STDERR ---",
                    str(step["one_step_stderr"]).rstrip("\n"),
                ]
            )

    lines.extend(
        [
            "",
            "=== FINAL CHAIN CHECK ===",
            f"final_chain_ok = {result['final_chain_ok']}",
            "",
            "=== TARGET SYNC STATE CHECKS ===",
        ]
    )

    for item in result["target_sync_results"]:
        lines.append(
            f"step={item['step']} "
            f"target_sync_applied={item['target_sync_applied']} "
            f"target_sync_state_ok={item['target_sync_state_ok']}"
        )

    lines.extend(
        [
            "",
            "=== SUMMARY ===",
            f"all_step_verifications_ok = {result['all_step_verifications_ok']}",
            f"all_chain_ok = {result['all_chain_ok']}",
            f"all_sync_logic_ok = {result['all_sync_logic_ok']}",
            f"target_sync_state_ok = {result['target_sync_state_ok']}",
            f"all_dataset_root_ok = {result['all_dataset_root_ok']}",
            f"all_batch_indices_ok = {result['all_batch_indices_ok']}",
            f"all_sampling_rule_ok = {result['all_sampling_rule_ok']}",
            f"all_optimizer_ok = {result['all_optimizer_ok']}",
            f"all_loss_type_ok = {result['all_loss_type_ok']}",
            "short_trace_canonical_boundary_commitments_ok = "
            f"{canonical_checks['short_trace_canonical_boundary_commitments_ok']}",
            "",
            f"verification_passed = {result['verification_passed']}",
        ]
    )

    return "\n".join(lines)


def verify_short_trace_artifact_path_report(
    artifact_path: str = DEFAULT_ARTIFACT_PATH,
    *,
    merkle_path: Optional[str] = None,
    initial_checkpoint_path: Optional[str] = None,
    final_checkpoint_path: Optional[str] = None,
    work_dir: Optional[str] = None,
) -> tuple[Dict[str, Any], str]:
    result = verify_short_trace_artifact_path(
        artifact_path=artifact_path,
        merkle_path=merkle_path,
        initial_checkpoint_path=initial_checkpoint_path,
        final_checkpoint_path=final_checkpoint_path,
        work_dir=work_dir,
    )
    return result, format_short_trace_report(result, artifact_path)
