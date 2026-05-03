import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import torch

from zk_offline_dqn.artifact_schema_versions import SCHEMA_SHORT_TRACE_UPDATE_V2
from zk_offline_dqn.commitments import canonical_checkpoint_state_commitments
from zk_offline_dqn.sampling_rules import (
    SAMPLING_RULE_CONTIGUOUS_DETERMINISTIC,
    SAMPLING_RULE_SEEDED_PERMUTATION,
    SUPPORTED_SAMPLING_RULES,
    expected_batch_indices_for_rule,
)


DEFAULT_SAMPLING_RULE = SAMPLING_RULE_CONTIGUOUS_DETERMINISTIC

def to_posix_path(path: str) -> str:
    return Path(path).as_posix()


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
        default=DEFAULT_SAMPLING_RULE,
        help=(
            "Sampling rule enforced by the exporter. "
            f"Supported: {sorted(SUPPORTED_SAMPLING_RULES)}"
        ),
    )
    parser.add_argument(
        "--start-offset",
        type=int,
        default=0,
        help="Optional start offset for deterministic contiguous sampling.",
    )
    parser.add_argument(
        "--sampling-seed",
        type=int,
        default=None,
        help="Seed for seeded_permutation sampling.",
    )
    parser.add_argument(
        "--dataset-size",
        type=int,
        default=None,
        help=(
            "Dataset size for seeded_permutation sampling. "
            "If omitted, it is inferred from the Merkle artifact leaf count."
        ),
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


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_checkpoint(path: str) -> Dict[str, Any]:
    return torch.load(
        path,
        map_location="cpu",
        weights_only=False,
    )


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
def infer_dataset_size_from_merkle(merkle_path: str) -> int:
    with open(merkle_path, "r", encoding="utf-8") as f:
        merkle = json.load(f)

    levels = merkle.get("levels")

    if not isinstance(levels, list) or not levels:
        raise ValueError("Merkle artifact must contain a non-empty 'levels' list.")

    leaf_level = levels[0]

    if not isinstance(leaf_level, list) or not leaf_level:
        raise ValueError("Merkle artifact leaf level must be a non-empty list.")

    return len(leaf_level)

def validate_trace_batches_against_sampling_rule(
    trace_batches: List[List[int]],
    sampling_rule_type: str,
    start_offset: int,
    dataset_size: int | None = None,
    sampling_seed: int | None = None,
) -> int:
    if sampling_rule_type not in SUPPORTED_SAMPLING_RULES:
        raise ValueError(
            f"Unsupported sampling_rule_type={sampling_rule_type!r}. "
            f"Supported rules: {sorted(SUPPORTED_SAMPLING_RULES)}"
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

        expected = expected_batch_indices_for_rule(
            sampling_rule_type=sampling_rule_type,
            step_idx=step_idx,
            batch_size=batch_size,
            start_offset=start_offset,
            dataset_size=dataset_size,
            sampling_seed=sampling_seed,
        )

        if batch_indices != expected:
            raise ValueError(
                f"sampling rule mismatch at step {step_idx}: "
                f"expected {expected}, got {batch_indices}"
            )

    return batch_size


def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def sync_target_network(in_ckpt_path: str, out_ckpt_path: str) -> None:
    ckpt = load_checkpoint(in_ckpt_path)
    ckpt = copy.deepcopy(ckpt)
    ckpt["target_net_state_dict"] = copy.deepcopy(ckpt["model_state_dict"])

    meta = ckpt.get("short_trace_metadata", {})
    meta["target_sync_applied"] = True
    ckpt["short_trace_metadata"] = meta

    torch.save(ckpt, out_ckpt_path)


def serialize_tensor(t: torch.Tensor) -> Dict[str, Any]:
    t_cpu = t.detach().cpu()

    return {
        "dtype": str(t_cpu.dtype),
        "shape": list(t_cpu.shape),
        "values": t_cpu.reshape(-1).tolist(),
    }


def serialize_state_dict(state_dict: Dict[str, torch.Tensor]) -> Dict[str, Any]:
    return {
        name: serialize_tensor(tensor)
        for name, tensor in state_dict.items()
    }


def main() -> None:
    args = parse_args()

    trace_batches = load_trace_batches(args.trace_batches_json)

    dataset_size = args.dataset_size

    if args.sampling_rule_type == SAMPLING_RULE_SEEDED_PERMUTATION:
        if args.sampling_seed is None:
            raise ValueError("--sampling-seed is required for seeded_permutation")

        if dataset_size is None:
            dataset_size = infer_dataset_size_from_merkle(args.merkle)

    batch_size = validate_trace_batches_against_sampling_rule(
        trace_batches=trace_batches,
        sampling_rule_type=args.sampling_rule_type,
        start_offset=args.start_offset,
        dataset_size=dataset_size,
        sampling_seed=args.sampling_seed,
    )

    ensure_dir(args.work_dir)

    out_dir = os.path.dirname(args.out)
    if out_dir:
        ensure_dir(out_dir)

    initial_checkpoint_sha256 = file_sha256(args.checkpoint)
    initial_checkpoint = load_checkpoint(args.checkpoint)
    initial_state_commitments = canonical_checkpoint_state_commitments(
        initial_checkpoint
    )

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
            "--data",
            args.data,
            "--merkle",
            args.merkle,
            "--checkpoint",
            current_checkpoint_path,
            "--indices",
            ",".join(str(x) for x in batch),
            "--lr",
            str(args.lr),
            "--post-checkpoint-out",
            step_post_ckpt_path,
            "--out",
            step_artifact_path,
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

        raw_output_ckpt = load_checkpoint(step_post_ckpt_path)
        next_ckpt = load_checkpoint(next_checkpoint_path)

        sync_state_witness = {
            "raw_output_online_state_dict": serialize_state_dict(
                raw_output_ckpt["model_state_dict"]
            ),
            "raw_output_target_state_dict": serialize_state_dict(
                raw_output_ckpt["target_net_state_dict"]
            ),
            "next_target_state_dict": serialize_state_dict(
                next_ckpt["target_net_state_dict"]
            ),
        }

        steps.append(
            {
                "step_index": step_idx,
                "input_checkpoint_sha256": input_checkpoint_sha256,
                "raw_output_checkpoint_sha256": output_checkpoint_sha256,
                "next_checkpoint_sha256": next_checkpoint_sha256,
                "target_sync_applied": target_sync_applied,
                "sync_state_witness": sync_state_witness,
                "one_step_artifact": step_artifact,
            }
        )

        current_checkpoint_path = next_checkpoint_path

    final_checkpoint_sha256 = file_sha256(current_checkpoint_path)
    final_checkpoint = load_checkpoint(current_checkpoint_path)
    final_state_commitments = canonical_checkpoint_state_commitments(
        final_checkpoint
    )

    artifact: Dict[str, Any] = {
        "schema_version": SCHEMA_SHORT_TRACE_UPDATE_V2,
        "public": {
            "dataset_root": steps[0]["one_step_artifact"]["public"]["dataset_root"],
            "trace_batch_indices": trace_batches,
            "num_steps": len(trace_batches),
            "batch_size": batch_size,
            "loss_type": "smooth_l1",
            "optimizer_type": "sgd",
            "learning_rate_fp": steps[0]["one_step_artifact"]["public"][
                "learning_rate_fp"
            ],
            "sampling_rule_type": args.sampling_rule_type,
            "start_offset": args.start_offset,
            "sampling_seed": args.sampling_seed,
            "dataset_size": dataset_size,
            "target_sync_every": args.target_sync_every,
            "initial_checkpoint_sha256": initial_checkpoint_sha256,
            "final_checkpoint_sha256": final_checkpoint_sha256,
            "checkpoint_commitment_type": "sha256_file_and_canonical_state_dicts",
            "initial_online_state_dict_key": initial_state_commitments[
                "online_state_dict_key"
            ],
            "initial_online_state_dict_sha256": initial_state_commitments[
                "online_state_dict_sha256"
            ],
            "initial_target_state_dict_sha256": initial_state_commitments[
                "target_state_dict_sha256"
            ],
            "final_online_state_dict_key": final_state_commitments[
                "online_state_dict_key"
            ],
            "final_online_state_dict_sha256": final_state_commitments[
                "online_state_dict_sha256"
            ],
            "final_target_state_dict_sha256": final_state_commitments[
                "target_state_dict_sha256"
            ],
        },
        "steps": steps,
        "notes": {},
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    print("=== SHORT TRACE UPDATE ARTIFACT EXPORTED ===")
    print("output_path =", to_posix_path(args.out))
    print("num_steps =", len(trace_batches))
    print("trace_batch_indices =", trace_batches)
    print("batch_size =", batch_size)
    print("sampling_rule_type =", args.sampling_rule_type)
    print("start_offset =", args.start_offset)
    print("sampling_seed =", args.sampling_seed)
    print("dataset_size =", dataset_size)
    print("target_sync_every =", args.target_sync_every)
    print("initial_checkpoint_sha256 =", initial_checkpoint_sha256)
    print("final_checkpoint_sha256 =", final_checkpoint_sha256)
    print("final_checkpoint_path =", to_posix_path(current_checkpoint_path))
    print("checkpoint_commitment_type =", artifact["public"]["checkpoint_commitment_type"])
    print(
        "initial_online_state_dict_key =",
        artifact["public"]["initial_online_state_dict_key"],
    )
    print(
        "initial_online_state_dict_sha256 =",
        artifact["public"]["initial_online_state_dict_sha256"],
    )
    print(
        "initial_target_state_dict_sha256 =",
        artifact["public"]["initial_target_state_dict_sha256"],
    )
    print(
        "final_online_state_dict_key =",
        artifact["public"]["final_online_state_dict_key"],
    )
    print(
        "final_online_state_dict_sha256 =",
        artifact["public"]["final_online_state_dict_sha256"],
    )
    print(
        "final_target_state_dict_sha256 =",
        artifact["public"]["final_target_state_dict_sha256"],
    )
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