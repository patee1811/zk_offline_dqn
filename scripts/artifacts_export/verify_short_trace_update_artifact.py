import json
import os
import subprocess
import sys
import hashlib
import tempfile
from typing import List

import torch


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


def run_one_step_verifier_from_embedded_artifact(one_step_artifact: dict, merkle_path: str):
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
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return proc


def compare_state_dicts(sd1, sd2):
    keys1 = set(sd1.keys())
    keys2 = set(sd2.keys())
    if keys1 != keys2:
        return False
    for k in keys1:
        if not torch.equal(sd1[k].detach().cpu(), sd2[k].detach().cpu()):
            return False
    return True


def expected_contiguous_batch_indices(
    step_idx: int,
    batch_size: int,
    start_offset: int = 0,
) -> List[int]:
    start = start_offset + step_idx * batch_size
    return list(range(start, start + batch_size))


def main():
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        artifact = json.load(f)

    public = artifact["public"]
    steps = artifact["steps"]
    notes = artifact["notes"]

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

    merkle_path = notes["merkle_path"]
    initial_checkpoint_path = notes["initial_checkpoint_path"]
    final_checkpoint_path = notes["final_checkpoint_path"]

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

    num_steps_match = (num_steps == len(steps) == len(trace_batch_indices))
    initial_checkpoint_ok = (file_sha256(initial_checkpoint_path) == initial_checkpoint_sha256)
    final_checkpoint_ok = (file_sha256(final_checkpoint_path) == final_checkpoint_sha256)
    sampling_rule_supported = (sampling_rule_type == SUPPORTED_SAMPLING_RULE)

    print("=== GLOBAL CHECKS ===")
    print("num_steps_match =", num_steps_match)
    print("initial_checkpoint_ok =", initial_checkpoint_ok)
    print("final_checkpoint_ok =", final_checkpoint_ok)
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

        step_index_ok = (step_index == i)

        expected_batch = expected_contiguous_batch_indices(
            step_idx=i,
            batch_size=batch_size,
            start_offset=start_offset,
        )
        public_batch = trace_batch_indices[i]
        step_batch = one_step_artifact["public"]["batch_indices"]

        sampling_rule_public_ok = (public_batch == expected_batch)
        sampling_rule_step_ok = (step_batch == expected_batch)
        batch_indices_ok = (step_batch == public_batch)
        sampling_rule_ok = sampling_rule_public_ok and sampling_rule_step_ok and batch_indices_ok

        dataset_root_ok = (
            one_step_artifact["public"]["dataset_root"] == dataset_root
        )

        optimizer_ok = (
            one_step_artifact["public"]["optimizer_type"] == optimizer_type
        )
        loss_type_ok = (
            one_step_artifact["public"]["loss_type"] == loss_type
        )

        if i == 0:
            chain_ok = (input_sha == initial_checkpoint_sha256)
        else:
            chain_ok = (input_sha == prev_next_sha)

        if target_sync_applied:
            sync_logic_ok = (raw_output_sha != next_sha)
        else:
            sync_logic_ok = (raw_output_sha == next_sha)

        one_step_proc = run_one_step_verifier_from_embedded_artifact(one_step_artifact, merkle_path)
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

    final_chain_ok = (prev_next_sha == final_checkpoint_sha256)

    print()
    print("=== FINAL CHAIN CHECK ===")
    print("final_chain_ok =", final_chain_ok)
    print()

    target_sync_state_ok = True
    print("=== TARGET SYNC STATE CHECKS ===")
    for i, step in enumerate(steps):
        raw_output_checkpoint_path = step["raw_output_checkpoint_path"]
        next_checkpoint_path = step["next_checkpoint_path"]
        target_sync_applied = step["target_sync_applied"]

        raw_ckpt = torch.load(raw_output_checkpoint_path, map_location="cpu")
        next_ckpt = torch.load(next_checkpoint_path, map_location="cpu")

        raw_online = raw_ckpt["model_state_dict"]
        raw_target = raw_ckpt["target_net_state_dict"]
        next_online = next_ckpt["model_state_dict"]
        next_target = next_ckpt["target_net_state_dict"]

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
    print()
    print("verification_passed =", verification_passed)


if __name__ == "__main__":
    main()