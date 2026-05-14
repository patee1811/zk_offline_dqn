"""Importable short-trace update relation checks."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Mapping

import torch

from zk_offline_dqn.artifact_schema_versions import (
    SCHEMA_SHORT_TRACE_UPDATE_V2,
    require_schema_version,
)
from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments
from zk_offline_dqn.relations.one_step_update import compare_state_dicts
from zk_offline_dqn.sampling_rules import (
    SAMPLING_RULE_CONTIGUOUS_DETERMINISTIC,
    SUPPORTED_SAMPLING_RULES,
    expected_batch_indices_for_rule,
)


DEFAULT_SAMPLING_RULE = SAMPLING_RULE_CONTIGUOUS_DETERMINISTIC


def validate_short_trace_schema(
    artifact: Mapping[str, Any],
    *,
    artifact_path: str = "",
) -> None:
    require_schema_version(
        dict(artifact),
        SCHEMA_SHORT_TRACE_UPDATE_V2,
        artifact_path=artifact_path,
    )


def deserialize_tensor(obj: Mapping[str, Any]) -> torch.Tensor:
    dtype_str = obj["dtype"]
    shape = obj["shape"]
    values = obj["values"]

    dtype_map = {
        "torch.float32": torch.float32,
        "torch.float64": torch.float64,
        "torch.int64": torch.int64,
        "torch.int32": torch.int32,
    }

    dtype = dtype_map.get(dtype_str, torch.float32)
    tensor = torch.tensor(values, dtype=dtype)

    return tensor.reshape(shape)


def deserialize_state_dict(obj: Mapping[str, Any]) -> Dict[str, torch.Tensor]:
    return {
        name: deserialize_tensor(tensor_obj)
        for name, tensor_obj in obj.items()
    }


def step_checkpoint_paths(
    work_dir: str,
    step_index: int,
    batch_indices: List[int],
) -> tuple[str, str]:
    batch_name = "_".join(str(x) for x in batch_indices)
    step_post_checkpoint_path = os.path.join(
        work_dir,
        f"step_{step_index}_post_{batch_name}.pt",
    )
    step_synced_checkpoint_path = os.path.join(
        work_dir,
        f"step_{step_index}_post_synced_{batch_name}.pt",
    )
    return step_post_checkpoint_path, step_synced_checkpoint_path


def verify_short_trace_canonical_boundary_commitments(
    public: Mapping[str, Any],
    initial_checkpoint: Mapping[str, Any],
    final_checkpoint: Mapping[str, Any],
) -> Dict[str, Any]:
    initial_recomputed = canonical_checkpoint_state_commitments(initial_checkpoint)
    final_recomputed = canonical_checkpoint_state_commitments(final_checkpoint)

    expected_commitment_type = public.get("checkpoint_commitment_type")

    expected_initial_online_key = public.get("initial_online_state_dict_key")
    expected_initial_online_sha = public.get("initial_online_state_dict_sha256")
    expected_initial_target_sha = public.get("initial_target_state_dict_sha256")

    expected_final_online_key = public.get("final_online_state_dict_key")
    expected_final_online_sha = public.get("final_online_state_dict_sha256")
    expected_final_target_sha = public.get("final_target_state_dict_sha256")

    has_boundary_fields = all(
        value is not None
        for value in [
            expected_commitment_type,
            expected_initial_online_key,
            expected_initial_online_sha,
            expected_initial_target_sha,
            expected_final_online_key,
            expected_final_online_sha,
            expected_final_target_sha,
        ]
    )

    # Backward compatibility for older short-trace artifacts.
    if not has_boundary_fields:
        return {
            "canonical_boundary_commitments_present": False,
            "checkpoint_commitment_type_ok": True,
            "initial_online_state_dict_key_ok": True,
            "initial_online_state_dict_sha256_ok": True,
            "initial_target_state_dict_sha256_ok": True,
            "final_online_state_dict_key_ok": True,
            "final_online_state_dict_sha256_ok": True,
            "final_target_state_dict_sha256_ok": True,
            "short_trace_canonical_boundary_commitments_ok": True,
        }

    checkpoint_commitment_type_ok = (
        expected_commitment_type == "sha256_file_and_canonical_state_dicts"
    )

    initial_online_state_dict_key_ok = (
        expected_initial_online_key == initial_recomputed["online_state_dict_key"]
    )
    initial_online_state_dict_sha256_ok = (
        expected_initial_online_sha == initial_recomputed["online_state_dict_sha256"]
    )
    initial_target_state_dict_sha256_ok = (
        expected_initial_target_sha == initial_recomputed["target_state_dict_sha256"]
    )

    final_online_state_dict_key_ok = (
        expected_final_online_key == final_recomputed["online_state_dict_key"]
    )
    final_online_state_dict_sha256_ok = (
        expected_final_online_sha == final_recomputed["online_state_dict_sha256"]
    )
    final_target_state_dict_sha256_ok = (
        expected_final_target_sha == final_recomputed["target_state_dict_sha256"]
    )

    short_trace_canonical_boundary_commitments_ok = (
        checkpoint_commitment_type_ok
        and initial_online_state_dict_key_ok
        and initial_online_state_dict_sha256_ok
        and initial_target_state_dict_sha256_ok
        and final_online_state_dict_key_ok
        and final_online_state_dict_sha256_ok
        and final_target_state_dict_sha256_ok
    )

    return {
        "canonical_boundary_commitments_present": True,
        "checkpoint_commitment_type_ok": checkpoint_commitment_type_ok,
        "initial_online_state_dict_key_ok": initial_online_state_dict_key_ok,
        "initial_online_state_dict_sha256_ok": initial_online_state_dict_sha256_ok,
        "initial_target_state_dict_sha256_ok": initial_target_state_dict_sha256_ok,
        "final_online_state_dict_key_ok": final_online_state_dict_key_ok,
        "final_online_state_dict_sha256_ok": final_online_state_dict_sha256_ok,
        "final_target_state_dict_sha256_ok": final_target_state_dict_sha256_ok,
        "short_trace_canonical_boundary_commitments_ok": (
            short_trace_canonical_boundary_commitments_ok
        ),
    }


def check_short_trace_artifact(
    artifact: Mapping[str, Any],
    *,
    initial_checkpoint_sha256_recomputed: str,
    final_checkpoint_sha256_recomputed: str,
    initial_checkpoint: Mapping[str, Any],
    final_checkpoint: Mapping[str, Any],
    one_step_verification_results: List[Mapping[str, Any]],
    artifact_path: str = "",
    validate_schema: bool = True,
) -> Dict[str, Any]:
    if validate_schema:
        validate_short_trace_schema(artifact, artifact_path=artifact_path)

    public = artifact["public"]
    steps = artifact["steps"]

    dataset_root = public["dataset_root"]
    trace_batch_indices = public["trace_batch_indices"]
    num_steps = int(public["num_steps"])
    batch_size = int(public["batch_size"])
    optimizer_type = public["optimizer_type"]
    loss_type = public["loss_type"]
    initial_checkpoint_sha256 = public["initial_checkpoint_sha256"]
    final_checkpoint_sha256 = public["final_checkpoint_sha256"]
    target_sync_every = public["target_sync_every"]
    sampling_rule_type = public.get("sampling_rule_type", DEFAULT_SAMPLING_RULE)
    start_offset = int(public.get("start_offset", 0))
    sampling_seed = public.get("sampling_seed")
    dataset_size = public.get("dataset_size")

    if sampling_seed is not None:
        sampling_seed = int(sampling_seed)

    if dataset_size is not None:
        dataset_size = int(dataset_size)

    num_steps_match = num_steps == len(steps) == len(trace_batch_indices)
    initial_checkpoint_ok = (
        initial_checkpoint_sha256_recomputed == initial_checkpoint_sha256
    )
    final_checkpoint_ok = (
        final_checkpoint_sha256_recomputed == final_checkpoint_sha256
    )

    canonical_boundary_checks = verify_short_trace_canonical_boundary_commitments(
        public=public,
        initial_checkpoint=initial_checkpoint,
        final_checkpoint=final_checkpoint,
    )

    sampling_rule_supported = sampling_rule_type in SUPPORTED_SAMPLING_RULES

    all_step_verifications_ok = True
    all_chain_ok = True
    all_sync_logic_ok = True
    all_dataset_root_ok = True
    all_batch_indices_ok = True
    all_optimizer_ok = True
    all_loss_type_ok = True
    all_sampling_rule_ok = True

    prev_next_sha = None
    step_results = []

    for i, step in enumerate(steps):
        step_index = step["step_index"]
        input_sha = step["input_checkpoint_sha256"]
        raw_output_sha = step["raw_output_checkpoint_sha256"]
        next_sha = step["next_checkpoint_sha256"]
        target_sync_applied = step["target_sync_applied"]
        one_step_artifact = step["one_step_artifact"]

        step_index_ok = step_index == i

        expected_batch = expected_batch_indices_for_rule(
            sampling_rule_type=sampling_rule_type,
            step_idx=i,
            batch_size=batch_size,
            start_offset=start_offset,
            dataset_size=dataset_size,
            sampling_seed=sampling_seed,
        )

        public_batch = trace_batch_indices[i]
        step_batch = one_step_artifact["public"]["batch_indices"]

        sampling_rule_public_ok = public_batch == expected_batch
        sampling_rule_step_ok = step_batch == expected_batch
        batch_indices_ok = step_batch == public_batch
        sampling_rule_ok = (
            sampling_rule_public_ok
            and sampling_rule_step_ok
            and batch_indices_ok
        )

        dataset_root_ok = (
            one_step_artifact["public"]["dataset_root"] == dataset_root
        )

        optimizer_ok = (
            one_step_artifact["public"]["optimizer_type"] == optimizer_type
        )
        loss_type_ok = one_step_artifact["public"]["loss_type"] == loss_type

        if i == 0:
            chain_ok = input_sha == initial_checkpoint_sha256
        else:
            chain_ok = input_sha == prev_next_sha

        if target_sync_applied:
            sync_logic_ok = raw_output_sha != next_sha
        else:
            sync_logic_ok = raw_output_sha == next_sha

        one_step_result = one_step_verification_results[i]
        step_verification_ok = bool(one_step_result["accepted"])

        all_step_verifications_ok = all_step_verifications_ok and step_verification_ok
        all_chain_ok = all_chain_ok and chain_ok and step_index_ok
        all_sync_logic_ok = all_sync_logic_ok and sync_logic_ok
        all_dataset_root_ok = all_dataset_root_ok and dataset_root_ok
        all_batch_indices_ok = all_batch_indices_ok and batch_indices_ok
        all_optimizer_ok = all_optimizer_ok and optimizer_ok
        all_loss_type_ok = all_loss_type_ok and loss_type_ok
        all_sampling_rule_ok = all_sampling_rule_ok and sampling_rule_ok

        step_results.append(
            {
                "step": i,
                "step_index": step_index,
                "step_index_ok": step_index_ok,
                "batch_indices_ok": batch_indices_ok,
                "sampling_rule_public_ok": sampling_rule_public_ok,
                "sampling_rule_step_ok": sampling_rule_step_ok,
                "sampling_rule_ok": sampling_rule_ok,
                "expected_batch_indices": expected_batch,
                "public_batch_indices": public_batch,
                "step_batch_indices": step_batch,
                "dataset_root_ok": dataset_root_ok,
                "optimizer_ok": optimizer_ok,
                "loss_type_ok": loss_type_ok,
                "chain_ok": chain_ok,
                "sync_logic_ok": sync_logic_ok,
                "one_step_verification_ok": step_verification_ok,
                "one_step_stdout": one_step_result.get("stdout", ""),
                "one_step_stderr": one_step_result.get("stderr", ""),
            }
        )

        prev_next_sha = next_sha

    final_chain_ok = prev_next_sha == final_checkpoint_sha256

    target_sync_state_ok = True
    target_sync_results = []

    for i, step in enumerate(steps):
        target_sync_applied = step["target_sync_applied"]
        sync_state_witness = step["sync_state_witness"]

        raw_online = deserialize_state_dict(
            sync_state_witness["raw_output_online_state_dict"]
        )
        raw_target = deserialize_state_dict(
            sync_state_witness["raw_output_target_state_dict"]
        )
        next_target = deserialize_state_dict(
            sync_state_witness["next_target_state_dict"]
        )

        if target_sync_applied:
            state_ok = compare_state_dicts(next_target, raw_online)
        else:
            state_ok = compare_state_dicts(next_target, raw_target)

        target_sync_state_ok = target_sync_state_ok and state_ok

        target_sync_results.append(
            {
                "step": i,
                "target_sync_applied": target_sync_applied,
                "target_sync_state_ok": state_ok,
            }
        )

    verification_passed = (
        num_steps_match
        and initial_checkpoint_ok
        and final_checkpoint_ok
        and canonical_boundary_checks["short_trace_canonical_boundary_commitments_ok"]
        and sampling_rule_supported
        and all_step_verifications_ok
        and all_chain_ok
        and final_chain_ok
        and all_sync_logic_ok
        and target_sync_state_ok
        and all_dataset_root_ok
        and all_batch_indices_ok
        and all_sampling_rule_ok
        and all_optimizer_ok
        and all_loss_type_ok
    )

    return {
        "public": public,
        "steps": steps,
        "dataset_root": dataset_root,
        "trace_batch_indices": trace_batch_indices,
        "num_steps": num_steps,
        "batch_size": batch_size,
        "optimizer_type": optimizer_type,
        "loss_type": loss_type,
        "target_sync_every": target_sync_every,
        "sampling_rule_type": sampling_rule_type,
        "start_offset": start_offset,
        "sampling_seed": sampling_seed,
        "dataset_size": dataset_size,
        "num_steps_match": num_steps_match,
        "initial_checkpoint_ok": initial_checkpoint_ok,
        "final_checkpoint_ok": final_checkpoint_ok,
        "canonical_boundary_checks": canonical_boundary_checks,
        "sampling_rule_supported": sampling_rule_supported,
        "step_results": step_results,
        "all_step_verifications_ok": all_step_verifications_ok,
        "all_chain_ok": all_chain_ok,
        "all_sync_logic_ok": all_sync_logic_ok,
        "all_dataset_root_ok": all_dataset_root_ok,
        "all_batch_indices_ok": all_batch_indices_ok,
        "all_optimizer_ok": all_optimizer_ok,
        "all_loss_type_ok": all_loss_type_ok,
        "all_sampling_rule_ok": all_sampling_rule_ok,
        "final_chain_ok": final_chain_ok,
        "target_sync_results": target_sync_results,
        "target_sync_state_ok": target_sync_state_ok,
        "verification_passed": verification_passed,
    }
