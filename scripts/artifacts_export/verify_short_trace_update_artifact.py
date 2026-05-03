import hashlib
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

import torch

from zk_offline_dqn.artifact_schema_versions import (
    SCHEMA_SHORT_TRACE_UPDATE_V2,
    require_schema_version,
)
from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments


ARTIFACT_PATH = os.environ.get(
    "SHORT_TRACE_ARTIFACT_PATH",
    "artifacts/short_trace_update_artifact.json",
)

SUPPORTED_SAMPLING_RULE = "contiguous_deterministic"


def file_sha256(path: str) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def load_checkpoint(path: str) -> Dict[str, Any]:
    return torch.load(
        path,
        map_location="cpu",
        weights_only=False,
    )


def run_one_step_verifier_from_embedded_artifact(
    one_step_artifact: dict,
    merkle_path: str,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_artifact_path = os.path.join(tmpdir, "embedded_one_step_artifact.json")

        with open(temp_artifact_path, "w", encoding="utf-8") as f:
            json.dump(one_step_artifact, f, indent=2)

        env = os.environ.copy()
        env["ONE_STEP_ARTIFACT_PATH"] = temp_artifact_path
        env["ONE_STEP_MERKLE_PATH"] = merkle_path

        cmd = [
            sys.executable,
            "scripts/artifacts_export/verify_one_step_update_artifact.py",
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
        )

        return proc


def compare_state_dicts(sd1, sd2) -> bool:
    keys1 = set(sd1.keys())
    keys2 = set(sd2.keys())

    if keys1 != keys2:
        return False

    for key in keys1:
        if not torch.equal(sd1[key].detach().cpu(), sd2[key].detach().cpu()):
            return False

    return True


def expected_contiguous_batch_indices(
    step_idx: int,
    batch_size: int,
    start_offset: int = 0,
) -> List[int]:
    start = start_offset + step_idx * batch_size
    return list(range(start, start + batch_size))


def deserialize_tensor(obj: Dict[str, Any]) -> torch.Tensor:
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


def deserialize_state_dict(obj: Dict[str, Any]) -> Dict[str, torch.Tensor]:
    return {
        name: deserialize_tensor(tensor_obj)
        for name, tensor_obj in obj.items()
    }


def verify_short_trace_canonical_boundary_commitments(
    public: Dict[str, Any],
    initial_checkpoint_path: str,
    final_checkpoint_path: str,
) -> Dict[str, Any]:
    initial_checkpoint = load_checkpoint(initial_checkpoint_path)
    final_checkpoint = load_checkpoint(final_checkpoint_path)

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


def main() -> None:
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    require_schema_version(
        artifact,
        SCHEMA_SHORT_TRACE_UPDATE_V2,
        artifact_path=ARTIFACT_PATH,
    )

    public = artifact["public"]
    steps = artifact["steps"]
    notes = artifact.get("notes", {})

    dataset_root = public["dataset_root"]
    trace_batch_indices = public["trace_batch_indices"]
    num_steps = int(public["num_steps"])
    batch_size = int(public["batch_size"])
    optimizer_type = public["optimizer_type"]
    loss_type = public["loss_type"]
    initial_checkpoint_sha256 = public["initial_checkpoint_sha256"]
    final_checkpoint_sha256 = public["final_checkpoint_sha256"]
    target_sync_every = public["target_sync_every"]
    sampling_rule_type = public.get("sampling_rule_type", SUPPORTED_SAMPLING_RULE)
    start_offset = int(public.get("start_offset", 0))

    merkle_path = os.environ.get(
        "SHORT_TRACE_MERKLE_PATH",
        notes.get("merkle_path"),
    )
    initial_checkpoint_path = os.environ.get(
        "SHORT_TRACE_INITIAL_CHECKPOINT_PATH",
        notes.get("initial_checkpoint_path"),
    )
    final_checkpoint_path = os.environ.get(
        "SHORT_TRACE_FINAL_CHECKPOINT_PATH",
        notes.get("final_checkpoint_path"),
    )

    if not merkle_path:
        raise ValueError(
            "Missing merkle path: provide SHORT_TRACE_MERKLE_PATH "
            "or keep notes['merkle_path']."
        )

    if not initial_checkpoint_path:
        raise ValueError(
            "Missing initial checkpoint path: provide SHORT_TRACE_INITIAL_CHECKPOINT_PATH "
            "or keep notes['initial_checkpoint_path']."
        )

    if not final_checkpoint_path:
        raise ValueError(
            "Missing final checkpoint path: provide SHORT_TRACE_FINAL_CHECKPOINT_PATH "
            "or keep notes['final_checkpoint_path']."
        )

    print("=== VERIFY SHORT TRACE UPDATE ARTIFACT ===")
    print("artifact_path =", ARTIFACT_PATH)
    print("dataset_root =", dataset_root)
    print("num_steps =", num_steps)
    print("trace_batch_indices =", trace_batch_indices)
    print("batch_size =", batch_size)
    print("sampling_rule_type =", sampling_rule_type)
    print("start_offset =", start_offset)
    print("optimizer_type =", optimizer_type)
    print("loss_type =", loss_type)
    print("target_sync_every =", target_sync_every)
    print()

    num_steps_match = num_steps == len(steps) == len(trace_batch_indices)
    initial_checkpoint_ok = (
        file_sha256(initial_checkpoint_path) == initial_checkpoint_sha256
    )
    final_checkpoint_ok = (
        file_sha256(final_checkpoint_path) == final_checkpoint_sha256
    )

    canonical_boundary_checks = verify_short_trace_canonical_boundary_commitments(
        public=public,
        initial_checkpoint_path=initial_checkpoint_path,
        final_checkpoint_path=final_checkpoint_path,
    )

    sampling_rule_supported = sampling_rule_type == SUPPORTED_SAMPLING_RULE

    print("=== GLOBAL CHECKS ===")
    print("num_steps_match =", num_steps_match)
    print("initial_checkpoint_ok =", initial_checkpoint_ok)
    print("final_checkpoint_ok =", final_checkpoint_ok)
    print(
        "canonical_boundary_commitments_present =",
        canonical_boundary_checks["canonical_boundary_commitments_present"],
    )
    print(
        "checkpoint_commitment_type_ok =",
        canonical_boundary_checks["checkpoint_commitment_type_ok"],
    )
    print(
        "initial_online_state_dict_key_ok =",
        canonical_boundary_checks["initial_online_state_dict_key_ok"],
    )
    print(
        "initial_online_state_dict_sha256_ok =",
        canonical_boundary_checks["initial_online_state_dict_sha256_ok"],
    )
    print(
        "initial_target_state_dict_sha256_ok =",
        canonical_boundary_checks["initial_target_state_dict_sha256_ok"],
    )
    print(
        "final_online_state_dict_key_ok =",
        canonical_boundary_checks["final_online_state_dict_key_ok"],
    )
    print(
        "final_online_state_dict_sha256_ok =",
        canonical_boundary_checks["final_online_state_dict_sha256_ok"],
    )
    print(
        "final_target_state_dict_sha256_ok =",
        canonical_boundary_checks["final_target_state_dict_sha256_ok"],
    )
    print(
        "short_trace_canonical_boundary_commitments_ok =",
        canonical_boundary_checks["short_trace_canonical_boundary_commitments_ok"],
    )
    print("sampling_rule_supported =", sampling_rule_supported)
    print()

    all_step_verifications_ok = True
    all_chain_ok = True
    all_sync_logic_ok = True
    all_dataset_root_ok = True
    all_batch_indices_ok = True
    all_optimizer_ok = True
    all_loss_type_ok = True
    all_sampling_rule_ok = True

    prev_next_sha = None

    print("=== STEP CHECKS ===")
    for i, step in enumerate(steps):
        step_index = step["step_index"]
        input_sha = step["input_checkpoint_sha256"]
        raw_output_sha = step["raw_output_checkpoint_sha256"]
        next_sha = step["next_checkpoint_sha256"]
        target_sync_applied = step["target_sync_applied"]
        one_step_artifact = step["one_step_artifact"]

        step_index_ok = step_index == i

        expected_batch = expected_contiguous_batch_indices(
            step_idx=i,
            batch_size=batch_size,
            start_offset=start_offset,
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

        one_step_proc = run_one_step_verifier_from_embedded_artifact(
            one_step_artifact,
            merkle_path,
        )
        step_verification_ok = (
            one_step_proc.returncode == 0
            and "verification_passed = True" in one_step_proc.stdout
        )

        all_step_verifications_ok = all_step_verifications_ok and step_verification_ok
        all_chain_ok = all_chain_ok and chain_ok and step_index_ok
        all_sync_logic_ok = all_sync_logic_ok and sync_logic_ok
        all_dataset_root_ok = all_dataset_root_ok and dataset_root_ok
        all_batch_indices_ok = all_batch_indices_ok and batch_indices_ok
        all_optimizer_ok = all_optimizer_ok and optimizer_ok
        all_loss_type_ok = all_loss_type_ok and loss_type_ok
        all_sampling_rule_ok = all_sampling_rule_ok and sampling_rule_ok

        print(
            f"step={step_index} "
            f"step_index_ok={step_index_ok} "
            f"batch_indices_ok={batch_indices_ok} "
            f"sampling_rule_public_ok={sampling_rule_public_ok} "
            f"sampling_rule_step_ok={sampling_rule_step_ok} "
            f"dataset_root_ok={dataset_root_ok} "
            f"optimizer_ok={optimizer_ok} "
            f"loss_type_ok={loss_type_ok} "
            f"chain_ok={chain_ok} "
            f"sync_logic_ok={sync_logic_ok} "
            f"one_step_verification_ok={step_verification_ok}"
        )

        if not sampling_rule_ok:
            print("--- SAMPLING RULE DETAILS ---")
            print("expected_batch_indices =", expected_batch)
            print("public_batch_indices =", public_batch)
            print("step_batch_indices =", step_batch)

        if not step_verification_ok:
            print("--- ONE-STEP VERIFY STDOUT ---")
            print(one_step_proc.stdout)
            print("--- ONE-STEP VERIFY STDERR ---")
            print(one_step_proc.stderr)

        prev_next_sha = next_sha

    final_chain_ok = prev_next_sha == final_checkpoint_sha256

    print()
    print("=== FINAL CHAIN CHECK ===")
    print("final_chain_ok =", final_chain_ok)
    print()

    target_sync_state_ok = True

    print("=== TARGET SYNC STATE CHECKS ===")
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

        print(
            f"step={i} "
            f"target_sync_applied={target_sync_applied} "
            f"target_sync_state_ok={state_ok}"
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

    print()
    print("=== SUMMARY ===")
    print("all_step_verifications_ok =", all_step_verifications_ok)
    print("all_chain_ok =", all_chain_ok)
    print("all_sync_logic_ok =", all_sync_logic_ok)
    print("target_sync_state_ok =", target_sync_state_ok)
    print("all_dataset_root_ok =", all_dataset_root_ok)
    print("all_batch_indices_ok =", all_batch_indices_ok)
    print("all_sampling_rule_ok =", all_sampling_rule_ok)
    print("all_optimizer_ok =", all_optimizer_ok)
    print("all_loss_type_ok =", all_loss_type_ok)
    print(
        "short_trace_canonical_boundary_commitments_ok =",
        canonical_boundary_checks["short_trace_canonical_boundary_commitments_ok"],
    )
    print()
    print("verification_passed =", verification_passed)


if __name__ == "__main__":
    main()