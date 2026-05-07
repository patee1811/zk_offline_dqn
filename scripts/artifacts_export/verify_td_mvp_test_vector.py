from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


DEFAULT_INPUT = Path("zk_backend/test_vectors/td_mvp_case_0.json")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode_leaf_for_hash(leaf: List[int]) -> bytes:
    """
    Canonical byte encoding for a leaf.

    This must match scripts/zk_proofs/build_leaf_hashes.py:
        [18, -45, -28] -> b"18,-45,-28"
    """
    return ",".join(str(int(x)) for x in leaf).encode("utf-8")


def hash_leaf(leaf: List[int]) -> str:
    return sha256_hex(encode_leaf_for_hash(leaf))


def hash_internal_node(left_hex: str, right_hex: str) -> str:
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return sha256_hex(left_bytes + right_bytes)


def verify_merkle_path(
    leaf_hash: str,
    path: List[Dict[str, Any]],
    expected_root: str,
) -> Tuple[bool, str]:
    current = leaf_hash

    for step in path:
        sibling_hash = step["sibling_hash"]
        current_is_left = bool(step["current_is_left"])

        if current_is_left:
            current = hash_internal_node(current, sibling_hash)
        else:
            current = hash_internal_node(sibling_hash, current)

    return current == expected_root, current


def fixed_point_mul(a_fp: int, b_fp: int, fp_scale: int) -> int:
    """
    Match the current artifact convention: integer truncation after scaling.

    For the current TD fixtures:
        gamma_fp = 990
        q_target_max_fp = 769
        fp_scale = 1000
        (990 * 769) // 1000 = 761
        target_fp = reward_fp + 761 = 1761
    """
    return (a_fp * b_fp) // fp_scale


def smooth_l1_loss_fp(td_error_fp: int, fp_scale: int) -> int:
    """
    SmoothL1 / Huber loss with beta = 1.0 in fixed-point form.

    Real-valued definition:
        if abs(x) < 1:
            loss = 0.5 * x^2
        else:
            loss = abs(x) - 0.5

    Fixed-point convention:
        abs_x_fp = abs(td_error_fp)
        beta_fp = fp_scale

        if abs_x_fp < beta_fp:
            loss_fp = (abs_x_fp * abs_x_fp) // (2 * beta_fp)
        else:
            loss_fp = abs_x_fp - beta_fp // 2
    """
    abs_x_fp = abs(int(td_error_fp))
    beta_fp = int(fp_scale)

    if abs_x_fp < beta_fp:
        return (abs_x_fp * abs_x_fp) // (2 * beta_fp)

    return abs_x_fp - beta_fp // 2


def reward_to_fp(reward: Any, fp_scale: int) -> int:
    return int(round(float(reward) * fp_scale))


def done_to_bool(done: Any) -> bool:
    if isinstance(done, bool):
        return done
    if isinstance(done, (int, float)):
        return bool(done)
    if isinstance(done, str):
        return done.strip().lower() in {"1", "true", "yes"}
    return bool(done)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def verify_test_vector(tv: Dict[str, Any]) -> Dict[str, Any]:
    if tv.get("schema_version") != "td_mvp_test_vector_v1":
        raise ValueError(f"Unexpected schema_version: {tv.get('schema_version')}")

    public = tv["public"]
    private = tv["private"]

    dataset_root = public["dataset_root"]
    fp_scale = int(public["fp_scale"])
    gamma_fp = int(public["gamma_fp"])
    claimed_target_fp = int(public["claimed_target_fp"])
    claimed_loss_fp = int(public["claimed_loss_fp"])

    transition = private["transition"]
    leaf = private["leaf"]
    claimed_leaf_hash = private["leaf_hash"]
    merkle_path = private["merkle_path"]
    td = private["td_witness"]

    recomputed_leaf_hash = hash_leaf(leaf)
    leaf_hash_ok = recomputed_leaf_hash == claimed_leaf_hash

    merkle_ok, recomputed_root = verify_merkle_path(
        leaf_hash=claimed_leaf_hash,
        path=merkle_path,
        expected_root=dataset_root,
    )

    reward_fp = reward_to_fp(transition["reward"], fp_scale)
    done = done_to_bool(transition["done"])

    q_online_action_fp = int(td["q_online_action_fp"])
    q_target_max_fp = int(td["q_target_max_fp"])
    target_fp = int(td["target_fp"])
    td_error_fp = int(td["td_error_fp"])
    loss_fp = int(td["loss_fp"])

    if done:
        expected_target_fp = reward_fp
    else:
        expected_target_fp = reward_fp + fixed_point_mul(
            gamma_fp,
            q_target_max_fp,
            fp_scale,
        )

    expected_td_error_fp = q_online_action_fp - expected_target_fp
    expected_loss_fp = smooth_l1_loss_fp(expected_td_error_fp, fp_scale)

    target_ok = target_fp == expected_target_fp
    td_error_ok = td_error_fp == expected_td_error_fp
    loss_ok = loss_fp == expected_loss_fp
    claimed_target_ok = target_fp == claimed_target_fp
    claimed_loss_ok = loss_fp == claimed_loss_fp

    all_ok = all(
        [
            leaf_hash_ok,
            merkle_ok,
            target_ok,
            td_error_ok,
            loss_ok,
            claimed_target_ok,
            claimed_loss_ok,
        ]
    )

    return {
        "schema_version_ok": True,
        "leaf_hash_ok": leaf_hash_ok,
        "merkle_ok": merkle_ok,
        "target_ok": target_ok,
        "td_error_ok": td_error_ok,
        "loss_ok": loss_ok,
        "claimed_target_ok": claimed_target_ok,
        "claimed_loss_ok": claimed_loss_ok,
        "verification_passed": all_ok,
        "details": {
            "claimed_leaf_hash": claimed_leaf_hash,
            "recomputed_leaf_hash": recomputed_leaf_hash,
            "dataset_root": dataset_root,
            "recomputed_root": recomputed_root,
            "reward_fp": reward_fp,
            "done": done,
            "q_online_action_fp": q_online_action_fp,
            "q_target_max_fp": q_target_max_fp,
            "target_fp": target_fp,
            "expected_target_fp": expected_target_fp,
            "td_error_fp": td_error_fp,
            "expected_td_error_fp": expected_td_error_fp,
            "loss_fp": loss_fp,
            "expected_loss_fp": expected_loss_fp,
            "claimed_target_fp": claimed_target_fp,
            "claimed_loss_fp": claimed_loss_fp,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    tv = load_json(args.input)
    result = verify_test_vector(tv)

    print("=== TD MVP TEST VECTOR VERIFICATION ===")
    print(f"input_path = {args.input}")
    print(f"leaf_hash_ok = {result['leaf_hash_ok']}")
    print(f"merkle_ok = {result['merkle_ok']}")
    print(f"target_ok = {result['target_ok']}")
    print(f"td_error_ok = {result['td_error_ok']}")
    print(f"loss_ok = {result['loss_ok']}")
    print(f"claimed_target_ok = {result['claimed_target_ok']}")
    print(f"claimed_loss_ok = {result['claimed_loss_ok']}")
    print(f"verification_passed = {result['verification_passed']}")

    print("\n=== DETAILS ===")
    for key, value in result["details"].items():
        print(f"{key} = {value}")

    if not result["verification_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()