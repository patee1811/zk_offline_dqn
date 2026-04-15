import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

import torch


SUPPORTED_SAMPLING_RULE = "contiguous_deterministic"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export a short verified training trace artifact by chaining one-step update artifacts."
    )
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--merkle", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument(
        "--trace-batches-json",
        type=str,
        required=True,
        help='JSON list of minibatches, e.g. "[[0,1,2,3],[4,5,6,7]]"',
    )
    parser.add_argument("--lr", type=float, required=True)
    parser.add_argument(
        "--target-sync-every",
        type=int,
        default=0,
        help="If > 0, sync target network after every k steps.",
    )
    parser.add_argument(
        "--sampling-rule-type",
        type=str,
        default=SUPPORTED_SAMPLING_RULE,
        help=f"Sampling rule enforced by the exporter. Currently supported: {SUPPORTED_SAMPLING_RULE}",
    )
    parser.add_argument(
        "--start-offset",
        type=int,
        default=0,
        help="Optional start offset for deterministic contiguous sampling.",
    )
    parser.add_argument(
        "--work-dir",
        type=str,
        default="artifacts/short_trace_work",
        help="Directory for intermediate per-step artifacts/checkpoints.",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output short-trace artifact JSON path.",
    )
    return parser.parse_args()


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_trace_batches(trace_batches_json: str) -> List[List[int]]:
    batches = json.loads(trace_batches_json)
    if not isinstance(batches, list) or not batches:
        raise ValueError("trace-batches-json must be a non-empty JSON list.")

    parsed: List[List[int]] = []
    for batch in batches:
        if not isinstance(batch, list) or not batch:
            raise ValueError("Each trace batch must be a non-empty list.")
        parsed.append([int(x) for x in batch])
    return parsed


def expected_contiguous_batch_indices(
    step_idx: int,
    batch_size: int,
    start_offset: int = 0,
) -> List[int]:
    start = start_offset + step_idx * batch_size
    return list(range(start, start + batch_size))


def validate_trace_batches_against_sampling_rule(
    trace_batches: List[List[int]],
    sampling_rule_type: str,
    start_offset: int,
) -> int:
    if sampling_rule_type != SUPPORTED_SAMPLING_RULE:
        raise ValueError(
            f"Unsupported sampling_rule_type={sampling_rule_type!r}. "
            f"Currently supported: {SUPPORTED_SAMPLING_RULE!r}"
        )

    if not trace_batches:
        raise ValueError("trace_batches must not be empty")

    batch_size = len(trace_batches[0])
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")

    for step_idx, batch_indices in enumerate(trace_batches):
        if len(batch_indices) != batch_size:
            raise ValueError(
                "all steps must use the same batch size for sampling-rule checking; "
                f"step 0 has batch_size={batch_size}, but step {step_idx} has "
                f"batch_size={len(batch_indices)}"
            )

        expected = expected_contiguous_batch_indices(
            step_idx=step_idx,
            batch_size=batch_size,
            start_offset=start_offset,
        )
        if batch_indices != expected:
            raise ValueError(
                f"sampling rule mismatch at step {step_idx}: "
                f"expected {expected}, got {batch_indices}"
            )

    return batch_size


def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def sync_target_network(in_ckpt_path: str, out_ckpt_path: str):
    ckpt = torch.load(in_ckpt_path, map_location="cpu")
    ckpt = copy.deepcopy(ckpt)
    ckpt["target_net_state_dict"] = copy.deepcopy(ckpt["model_state_dict"])

    meta = ckpt.get("short_trace_metadata", {})
    meta["target_sync_applied"] = True
    ckpt["short_trace_metadata"] = meta

    torch.save(ckpt, out_ckpt_path)


def main():
    args = parse_args()
    trace_batches = load_trace_batches(args.trace_batches_json)
    batch_size = validate_trace_batches_against_sampling_rule(
        trace_batches=trace_batches,
        sampling_rule_type=args.sampling_rule_type,
        start_offset=args.start_offset,
    )

    ensure_dir(args.work_dir)
    out_dir = os.path.dirname(args.out)
    if out_dir:
        ensure_dir(out_dir)

    initial_checkpoint_sha256 = file_sha256(args.checkpoint)
    current_checkpoint_path = args.checkpoint

    steps = []

    for step_idx, batch in enumerate(trace_batches):
        batch_name = "_".join(str(x) for x in batch)

        step_artifact_path = os.path.join(
            args.work_dir,
            f"step_{step_idx}_artifact_{batch_name}.json",
        )
        step_post_ckpt_path = os.path.join(
            args.work_dir,
            f"step_{step_idx}_post_{batch_name}.pt",
        )

        cmd = [
            sys.executable,
            "scripts/artifacts_export/export_one_step_update_artifact.py",
            "--data", args.data,
            "--merkle", args.merkle,
            "--checkpoint", current_checkpoint_path,
            "--indices", ",".join(str(x) for x in batch),
            "--lr", str(args.lr),
            "--post-checkpoint-out", step_post_ckpt_path,
            "--out", step_artifact_path,
        ]

        result = run_command(cmd)
        if result.returncode != 0:
            print("=== STEP EXPORT FAILED ===")
            print("step_idx =", step_idx)
            print("batch =", batch)
            print("--- STDOUT ---")
            print(result.stdout)
            print("--- STDERR ---")
            print(result.stderr)
            raise RuntimeError(f"One-step exporter failed at step {step_idx}")

        with open(step_artifact_path, "r", encoding="utf-8") as f:
            step_artifact = json.load(f)

        input_checkpoint_sha256 = step_artifact["public"]["pre_checkpoint_sha256"]
        output_checkpoint_sha256 = step_artifact["public"]["post_checkpoint_sha256"]

        target_sync_applied = False
        next_checkpoint_path = step_post_ckpt_path

        if args.target_sync_every > 0 and (step_idx + 1) % args.target_sync_every == 0:
            synced_ckpt_path = os.path.join(
                args.work_dir,
                f"step_{step_idx}_post_synced_{batch_name}.pt",
            )
            sync_target_network(step_post_ckpt_path, synced_ckpt_path)
            next_checkpoint_path = synced_ckpt_path
            target_sync_applied = True

        next_checkpoint_sha256 = file_sha256(next_checkpoint_path)

        steps.append(
            {
                "step_index": step_idx,
                "input_checkpoint_sha256": input_checkpoint_sha256,
                "raw_output_checkpoint_path": step_post_ckpt_path,
                "raw_output_checkpoint_sha256": output_checkpoint_sha256,
                "next_checkpoint_path": next_checkpoint_path,
                "next_checkpoint_sha256": next_checkpoint_sha256,
                "target_sync_applied": target_sync_applied,
                "one_step_artifact": step_artifact,
            }
        )

        current_checkpoint_path = next_checkpoint_path

    final_checkpoint_sha256 = file_sha256(current_checkpoint_path)

    artifact: Dict[str, Any] = {
        "public": {
            "dataset_root": steps[0]["one_step_artifact"]["public"]["dataset_root"],
            "trace_batch_indices": trace_batches,
            "num_steps": len(trace_batches),
            "batch_size": batch_size,
            "loss_type": "smooth_l1",
            "optimizer_type": "sgd",
            "learning_rate_fp": steps[0]["one_step_artifact"]["public"]["learning_rate_fp"],
            "sampling_rule_type": args.sampling_rule_type,
            "start_offset": args.start_offset,
            "target_sync_every": args.target_sync_every,
            "initial_checkpoint_sha256": initial_checkpoint_sha256,
            "final_checkpoint_sha256": final_checkpoint_sha256,
        },
        "steps": steps,
        "notes": {
            "merkle_path": args.merkle,
            "initial_checkpoint_path": args.checkpoint,
            "final_checkpoint_path": current_checkpoint_path,
        },
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== SHORT TRACE UPDATE ARTIFACT EXPORTED ===")
    print("output_path =", args.out)
    print("num_steps =", len(trace_batches))
    print("trace_batch_indices =", trace_batches)
    print("batch_size =", batch_size)
    print("sampling_rule_type =", args.sampling_rule_type)
    print("start_offset =", args.start_offset)
    print("target_sync_every =", args.target_sync_every)
    print("initial_checkpoint_sha256 =", initial_checkpoint_sha256)
    print("final_checkpoint_sha256 =", final_checkpoint_sha256)
    print("final_checkpoint_path =", current_checkpoint_path)
    print()

    print("=== STEP SUMMARY ===")
    for step in steps:
        print(
            f"step={step['step_index']} "
            f"batch={step['one_step_artifact']['public']['batch_indices']} "
            f"input_sha={step['input_checkpoint_sha256']} "
            f"raw_output_sha={step['raw_output_checkpoint_sha256']} "
            f"next_sha={step['next_checkpoint_sha256']} "
            f"target_sync_applied={step['target_sync_applied']}"
        )


if __name__ == "__main__":
    main()