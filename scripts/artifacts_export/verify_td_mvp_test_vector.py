from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from zk_offline_dqn.merkle import hash_leaf, verify_merkle_path
from zk_offline_dqn.zk_specs import serialize_transition_leaf

DEFAULT_INPUT = Path("zk_backend/test_vectors/td_mvp_case_0.json")


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


def get_q_online_action_fp(td: Dict[str, Any]) -> int:
    if "q_online_action_fp" in td:
        return int(td["q_online_action_fp"])
    return int(td["q_online_fp"])


def verify_merkle_path_metadata(merkle_path: list[Dict[str, Any]], leaf_index: int) -> bool:
    expected_current_index = int(leaf_index)

    for expected_level, step in enumerate(merkle_path):
        level_ok = int(step["level"]) == expected_level
        current_index = int(step["current_index"])
        sibling_index = int(step["sibling_index"])
        current_is_left = bool(step["current_is_left"])

        current_ok = current_index == expected_current_index
        if current_is_left:
            sibling_ok = (
                expected_current_index % 2 == 0
                and sibling_index in {expected_current_index, expected_current_index + 1}
            )
        else:
            sibling_ok = (
                expected_current_index % 2 == 1
                and sibling_index == expected_current_index - 1
            )

        if not (level_ok and current_ok and sibling_ok):
            return False

        expected_current_index //= 2

    return True


def verify_item(
    item: Dict[str, Any],
    *,
    dataset_root: str,
    fp_scale: int,
    gamma_fp: int,
) -> Dict[str, Any]:
    transition = item["transition"]
    leaf = item["leaf"]
    claimed_leaf_hash = item["leaf_hash"]
    merkle_path = item["merkle_path"]
    td = item["td_witness"]

    recomputed_leaf = serialize_transition_leaf(transition)
    leaf_encoding_ok = leaf == recomputed_leaf
    provided_leaf_hash = hash_leaf(leaf)
    recomputed_leaf_hash = hash_leaf(recomputed_leaf)
    leaf_hash_ok = recomputed_leaf_hash == claimed_leaf_hash

    merkle_ok, recomputed_root = verify_merkle_path(
        leaf_hash=recomputed_leaf_hash,
        merkle_path=merkle_path,
        expected_root=dataset_root,
    )
    index_ok = True
    path_metadata_ok = True
    if "index" in item and merkle_path:
        index_ok = int(merkle_path[0]["current_index"]) == int(item["index"])
        path_metadata_ok = verify_merkle_path_metadata(
            merkle_path=merkle_path,
            leaf_index=int(item["index"]),
        )

    reward_fp = reward_to_fp(transition["reward"], fp_scale)
    done = done_to_bool(transition["done"])

    q_online_action_fp = get_q_online_action_fp(td)
    q_target_max_fp = int(td["q_target_max_fp"])
    target_fp = int(td["target_fp"])
    td_error_fp = int(td["td_error_fp"]) if "td_error_fp" in td else None
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
    td_error_ok = True if td_error_fp is None else td_error_fp == expected_td_error_fp
    loss_ok = loss_fp == expected_loss_fp

    all_ok = all(
        [
            leaf_hash_ok,
            leaf_encoding_ok,
            merkle_ok,
            index_ok,
            path_metadata_ok,
            target_ok,
            td_error_ok,
            loss_ok,
        ]
    )

    return {
        "leaf_encoding_ok": leaf_encoding_ok,
        "leaf_hash_ok": leaf_hash_ok,
        "merkle_ok": merkle_ok,
        "index_ok": index_ok,
        "path_metadata_ok": path_metadata_ok,
        "target_ok": target_ok,
        "td_error_ok": td_error_ok,
        "loss_ok": loss_ok,
        "item_passed": all_ok,
        "details": {
            "claimed_leaf_hash": claimed_leaf_hash,
            "provided_leaf": leaf,
            "recomputed_leaf": recomputed_leaf,
            "provided_leaf_hash": provided_leaf_hash,
            "recomputed_leaf_hash": recomputed_leaf_hash,
            "dataset_root": dataset_root,
            "recomputed_root": recomputed_root,
            "index_ok": index_ok,
            "path_metadata_ok": path_metadata_ok,
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
        },
    }


def verify_single_test_vector(tv: Dict[str, Any]) -> Dict[str, Any]:
    public = tv["public"]
    private = tv["private"]

    dataset_root = public["dataset_root"]
    fp_scale = int(public["fp_scale"])
    gamma_fp = int(public["gamma_fp"])
    claimed_target_fp = int(public["claimed_target_fp"])
    claimed_loss_fp = int(public["claimed_loss_fp"])

    item_result = verify_item(
        {
            "index": int(public["leaf_index"]),
            "transition": private["transition"],
            "leaf": private["leaf"],
            "leaf_hash": private["leaf_hash"],
            "merkle_path": private["merkle_path"],
            "td_witness": private["td_witness"],
        },
        dataset_root=dataset_root,
        fp_scale=fp_scale,
        gamma_fp=gamma_fp,
    )

    target_fp = int(private["td_witness"]["target_fp"])
    loss_fp = int(private["td_witness"]["loss_fp"])
    claimed_target_ok = target_fp == claimed_target_fp
    claimed_loss_ok = loss_fp == claimed_loss_fp
    verification_passed = (
        item_result["item_passed"] and claimed_target_ok and claimed_loss_ok
    )

    return {
        "schema_version_ok": True,
        **{key: item_result[key] for key in [
            "leaf_encoding_ok",
            "leaf_hash_ok",
            "merkle_ok",
            "target_ok",
            "td_error_ok",
            "loss_ok",
        ]},
        "claimed_target_ok": claimed_target_ok,
        "claimed_loss_ok": claimed_loss_ok,
        "batch_size_ok": None,
        "claimed_batch_loss_ok": None,
        "verification_passed": verification_passed,
        "details": {
            **item_result["details"],
            "claimed_target_fp": claimed_target_fp,
            "claimed_loss_fp": claimed_loss_fp,
        },
    }


def verify_batch_test_vector(tv: Dict[str, Any]) -> Dict[str, Any]:
    public = tv["public"]
    private = tv["private"]

    dataset_root = public["dataset_root"]
    fp_scale = int(public["fp_scale"])
    gamma_fp = int(public["gamma_fp"])
    claimed_batch_loss_fp = int(
        public.get("claimed_batch_loss_fp", public.get("batch_loss_fp"))
    )
    batch_size = int(public["batch_size"])
    items = private["items"]
    item_indices = [int(item["index"]) for item in items]
    claimed_leaf_indices = public.get("leaf_indices")
    batch_mode = public.get("batch_mode")

    item_results = [
        verify_item(
            item,
            dataset_root=dataset_root,
            fp_scale=fp_scale,
            gamma_fp=gamma_fp,
        )
        for item in items
    ]
    total_loss_fp = sum(int(item["td_witness"]["loss_fp"]) for item in items)
    recomputed_batch_loss_fp = total_loss_fp // batch_size
    batch_size_ok = batch_size == len(items) and batch_size > 0
    leaf_indices_ok = (
        True
        if claimed_leaf_indices is None
        else [int(index) for index in claimed_leaf_indices] == item_indices
    )
    distinct_required = batch_mode == "distinct" or claimed_leaf_indices is not None
    distinct_indices_ok = (
        True if not distinct_required else len(set(item_indices)) == len(item_indices)
    )
    claimed_batch_loss_ok = recomputed_batch_loss_fp == claimed_batch_loss_fp
    verification_passed = (
        all(result["item_passed"] for result in item_results)
        and batch_size_ok
        and leaf_indices_ok
        and distinct_indices_ok
        and claimed_batch_loss_ok
    )

    return {
        "schema_version_ok": True,
        "leaf_encoding_ok": all(result["leaf_encoding_ok"] for result in item_results),
        "leaf_hash_ok": all(result["leaf_hash_ok"] for result in item_results),
        "merkle_ok": all(result["merkle_ok"] for result in item_results),
        "target_ok": all(result["target_ok"] for result in item_results),
        "td_error_ok": all(result["td_error_ok"] for result in item_results),
        "loss_ok": all(result["loss_ok"] for result in item_results),
        "claimed_target_ok": None,
        "claimed_loss_ok": None,
        "batch_size_ok": batch_size_ok,
        "leaf_indices_ok": leaf_indices_ok,
        "distinct_indices_ok": distinct_indices_ok,
        "claimed_batch_loss_ok": claimed_batch_loss_ok,
        "verification_passed": verification_passed,
        "details": {
            "batch_size": batch_size,
            "item_count": len(items),
            "batch_mode": batch_mode,
            "leaf_indices": claimed_leaf_indices,
            "item_indices": item_indices,
            "leaf_indices_ok": leaf_indices_ok,
            "distinct_indices_ok": distinct_indices_ok,
            "total_loss_fp": total_loss_fp,
            "claimed_batch_loss_fp": claimed_batch_loss_fp,
            "recomputed_batch_loss_fp": recomputed_batch_loss_fp,
            "items": [result["details"] for result in item_results],
        },
    }


def verify_test_vector(tv: Dict[str, Any]) -> Dict[str, Any]:
    schema_version = tv.get("schema_version")
    if schema_version == "td_mvp_test_vector_v1":
        return verify_single_test_vector(tv)
    if schema_version == "td_mvp_batch_test_vector_v1":
        return verify_batch_test_vector(tv)
    raise ValueError(f"Unexpected schema_version: {schema_version}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    tv = load_json(args.input)
    result = verify_test_vector(tv)

    print("=== TD MVP TEST VECTOR VERIFICATION ===")
    print(f"input_path = {args.input}")
    print(f"leaf_encoding_ok = {result['leaf_encoding_ok']}")
    print(f"leaf_hash_ok = {result['leaf_hash_ok']}")
    print(f"merkle_ok = {result['merkle_ok']}")
    print(f"target_ok = {result['target_ok']}")
    print(f"td_error_ok = {result['td_error_ok']}")
    print(f"loss_ok = {result['loss_ok']}")
    print(f"claimed_target_ok = {result['claimed_target_ok']}")
    print(f"claimed_loss_ok = {result['claimed_loss_ok']}")
    print(f"batch_size_ok = {result['batch_size_ok']}")
    print(f"leaf_indices_ok = {result.get('leaf_indices_ok')}")
    print(f"distinct_indices_ok = {result.get('distinct_indices_ok')}")
    print(f"claimed_batch_loss_ok = {result['claimed_batch_loss_ok']}")
    print(f"verification_passed = {result['verification_passed']}")

    print("\n=== DETAILS ===")
    for key, value in result["details"].items():
        print(f"{key} = {value}")

    if not result["verification_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
