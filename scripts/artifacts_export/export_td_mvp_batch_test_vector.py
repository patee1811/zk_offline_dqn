from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_INPUT = Path("zk_backend/test_vectors/td_mvp_case_0.json")


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_item(single: Dict[str, Any]) -> Dict[str, Any]:
    private = single["private"]
    public = single["public"]
    return {
        "index": int(public["leaf_index"]),
        "transition": copy.deepcopy(private["transition"]),
        "leaf": copy.deepcopy(private["leaf"]),
        "leaf_hash": private["leaf_hash"],
        "merkle_path": copy.deepcopy(private["merkle_path"]),
        "td_witness": copy.deepcopy(private["td_witness"]),
    }


def build_batch_vector(single: Dict[str, Any], batch_size: int) -> Dict[str, Any]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    items = [build_item(single) for _ in range(batch_size)]
    total_loss_fp = sum(int(item["td_witness"]["loss_fp"]) for item in items)
    batch_loss_fp = total_loss_fp // batch_size

    public = single["public"]
    return {
        "schema_version": "td_mvp_batch_test_vector_v1",
        "source": {
            "single_test_vector_path": DEFAULT_INPUT.as_posix(),
            "construction": "repeat canonical single-transition vector",
            "batch_size": batch_size,
        },
        "statement": {
            "name": "td_mvp_minibatch_membership_bellman_smoothl1_average",
            "description": (
                "Minibatch TD MVP test vector for proving multiple Merkle memberships, "
                "per-sample Bellman/SmoothL1 checks, and integer average batch loss."
            ),
        },
        "public": {
            "dataset_root": public["dataset_root"],
            "fp_scale": int(public["fp_scale"]),
            "gamma_fp": int(public["gamma_fp"]),
            "loss_type": public["loss_type"],
            "batch_size": batch_size,
            "claimed_batch_loss_fp": batch_loss_fp,
            "checkpoint_commitments": public.get("checkpoint_commitments"),
        },
        "private": {
            "items": items,
        },
        "relation": {
            "checks": [
                "for each item: leaf == SerializeTransition(transition)",
                "for each item: leaf_hash == SHA256(CanonicalLeafEncoding(leaf))",
                "for each item: MerkleVerify(leaf_hash, merkle_path, dataset_root) == true",
                "for each item: target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)",
                "for each item: td_error_fp == q_online_action_fp - target_fp when provided",
                "for each item: loss_fp == SmoothL1(td_error_fp)",
                "batch_size == len(items)",
                "claimed_batch_loss_fp == floor(sum(loss_fp) / batch_size)",
            ],
            "non_goals": single.get("relation", {}).get("non_goals", []),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    args = parser.parse_args()

    single = load_json(args.input)
    batch = build_batch_vector(single, args.batch_size)
    batch["source"]["single_test_vector_path"] = args.input.as_posix()
    write_json(args.out, batch)

    print(f"wrote_test_vector = {args.out}")
    print(f"schema_version = {batch['schema_version']}")
    print(f"batch_size = {batch['public']['batch_size']}")
    print(f"claimed_batch_loss_fp = {batch['public']['claimed_batch_loss_fp']}")


if __name__ == "__main__":
    main()
