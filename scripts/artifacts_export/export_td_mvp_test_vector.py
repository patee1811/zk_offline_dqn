from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_INPUT = Path("artifacts/minibatch_td_from_dataset.json")
DEFAULT_OUTPUT = Path("zk_backend/test_vectors/td_mvp_case_0.json")

# Fallback values matching the current CartPole TD artifact convention.
# These are kept here to make the test-vector exporter independent from
# internal constant names in zk_offline_dqn.zk_specs.
DEFAULT_FP_SCALE = 1000
DEFAULT_GAMMA_FP = 990
DEFAULT_LOSS_TYPE = "smooth_l1"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def infer_fp_scale(artifact: Dict[str, Any]) -> int:
    public = artifact.get("public", {})
    notes = artifact.get("notes", {})

    for container in (public, notes):
        if "fp_scale" in container:
            return int(container["fp_scale"])
        if "scale" in container:
            return int(container["scale"])

    return DEFAULT_FP_SCALE


def infer_gamma_fp(artifact: Dict[str, Any]) -> int:
    public = artifact.get("public", {})
    notes = artifact.get("notes", {})

    for container in (public, notes):
        if "gamma_fp" in container:
            return int(container["gamma_fp"])

    return DEFAULT_GAMMA_FP


def infer_loss_type(artifact: Dict[str, Any]) -> str:
    public = artifact.get("public", {})
    notes = artifact.get("notes", {})

    for container in (public, notes):
        if "loss_type" in container:
            return str(container["loss_type"])

    return DEFAULT_LOSS_TYPE


def build_td_mvp_test_vector(artifact: Dict[str, Any], item_index: int, source_path: Path) -> Dict[str, Any]:
    public = artifact["public"]
    items = artifact["items"]

    if item_index < 0 or item_index >= len(items):
        raise IndexError(f"item_index={item_index} out of range for {len(items)} items")

    item = items[item_index]
    td = item["td_witness"]
    transition = item["transition"]

    fp_scale = infer_fp_scale(artifact)
    gamma_fp = infer_gamma_fp(artifact)
    loss_type = infer_loss_type(artifact)

    q_online_action_fp = int(td["q_online_fp"])
    target_fp = int(td["target_fp"])
    loss_fp = int(td["loss_fp"])

    test_vector = {
        "schema_version": "td_mvp_test_vector_v1",
        "source": {
            "artifact_path": source_path.as_posix(),
            "artifact_schema_version": artifact.get("schema_version"),
            "item_index_in_artifact": item_index,
            "transition_index": int(item["index"]),
        },
        "statement": {
            "name": "td_mvp_membership_bellman_smoothl1",
            "description": (
                "Single-transition MVP test vector for proving Merkle membership, "
                "Bellman target correctness, TD error correctness, and SmoothL1 TD loss correctness."
            ),
        },
        "public": {
            "dataset_root": public["dataset_root"],
            "fp_scale": fp_scale,
            "gamma_fp": gamma_fp,
            "loss_type": loss_type,
            "claimed_target_fp": target_fp,
            "claimed_loss_fp": loss_fp,
            "leaf_index": int(item["index"]),
            "checkpoint_commitments": {
                "checkpoint_sha256": public.get("checkpoint_sha256"),
                "checkpoint_commitment_type": public.get("checkpoint_commitment_type"),
                "online_state_dict_key": public.get("online_state_dict_key"),
                "online_state_dict_sha256": public.get("online_state_dict_sha256"),
                "target_state_dict_sha256": public.get("target_state_dict_sha256"),
            },
        },
        "private": {
            "transition": transition,
            "leaf": item["leaf"],
            "leaf_hash": item["leaf_hash"],
            "merkle_path": item["merkle_path"],
            "td_witness": {
                "q_online_action_fp": q_online_action_fp,
                "next_action_online": int(td["next_action_online"]),
                "q_target_max_fp": int(td["q_target_max_fp"]),
                "target_fp": target_fp,
                "td_error_fp": q_online_action_fp - target_fp,
                "loss_fp": loss_fp,
            },
            "artifact_path": source_path.as_posix(),
        },
        "relation": {
            "checks": [
                "leaf == SerializeTransition(transition)",
                "leaf_hash == SHA256(CanonicalLeafEncoding(leaf))",
                "MerkleVerify(leaf_hash, merkle_path, dataset_root) == true",
                "target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)",
                "td_error_fp == q_online_action_fp - target_fp",
                "loss_fp == SmoothL1(td_error_fp)",
                "target_fp == claimed_target_fp",
                "loss_fp == claimed_loss_fp",
            ],
            "non_goals": [
                "does not prove neural-network forward pass",
                "does not prove argmax action selection",
                "does not prove gradient computation",
                "does not prove optimizer update",
                "does not prove full DQN training",
            ],
        },
    }

    return test_vector


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--item-index", type=int, default=0)
    args = parser.parse_args()

    artifact = load_json(args.input)
    test_vector = build_td_mvp_test_vector(
        artifact=artifact,
        item_index=args.item_index,
        source_path=args.input,
    )
    write_json(args.out, test_vector)

    print(f"wrote_test_vector = {args.out}")
    print(f"schema_version = {test_vector['schema_version']}")
    print(f"source_artifact_schema_version = {test_vector['source']['artifact_schema_version']}")
    print(f"transition_index = {test_vector['source']['transition_index']}")
    print(f"fp_scale = {test_vector['public']['fp_scale']}")
    print(f"gamma_fp = {test_vector['public']['gamma_fp']}")
    print(f"loss_type = {test_vector['public']['loss_type']}")
    print(f"claimed_target_fp = {test_vector['public']['claimed_target_fp']}")
    print(f"claimed_loss_fp = {test_vector['public']['claimed_loss_fp']}")


if __name__ == "__main__":
    main()
