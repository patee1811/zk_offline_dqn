from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List


BASE_VECTOR_PATH = Path("zk_backend/test_vectors/td_mvp_case_0.json")
OUT_DIR = Path("artifacts/td_mvp_test_vector_negative_tests")
VERIFIER = Path("scripts/artifacts_export/verify_td_mvp_test_vector.py")


Mutator = Callable[[Dict[str, Any]], None]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def run_verifier(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--input", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def mutate_reward(tv: Dict[str, Any]) -> None:
    tv["private"]["transition"]["reward"] = float(tv["private"]["transition"]["reward"]) + 1.0


def mutate_schema_version(tv: Dict[str, Any]) -> None:
    tv["schema_version"] = f"{tv['schema_version']}_invalid"


def mutate_fixed_point_rounding(tv: Dict[str, Any]) -> None:
    tv["private"]["transition"]["reward"] = float(tv["private"]["transition"]["reward"]) + 0.0006


def mutate_done(tv: Dict[str, Any]) -> None:
    done = int(tv["private"]["transition"]["done"])
    tv["private"]["transition"]["done"] = 1 - done


def smooth_l1_loss_fp(td_error_fp: int, fp_scale: int) -> int:
    abs_x_fp = abs(int(td_error_fp))
    if abs_x_fp < fp_scale:
        return (abs_x_fp * abs_x_fp) // (2 * fp_scale)
    return abs_x_fp - fp_scale // 2


def mutate_done_branch(tv: Dict[str, Any]) -> None:
    td = tv["private"]["td_witness"]
    reward_fp = int(tv["private"]["leaf"][5])
    q_online_action_fp = int(td["q_online_action_fp"])
    td_error_fp = q_online_action_fp - reward_fp
    td["target_fp"] = reward_fp
    td["td_error_fp"] = td_error_fp
    td["loss_fp"] = smooth_l1_loss_fp(td_error_fp, int(tv["public"]["fp_scale"]))


def mutate_transition_obs(tv: Dict[str, Any]) -> None:
    tv["private"]["transition"]["obs"][0] = (
        float(tv["private"]["transition"]["obs"][0]) + 1.0
    )


def mutate_leaf_encoding(tv: Dict[str, Any]) -> None:
    tv["private"]["leaf"][0] += 1


def mutate_merkle_path(tv: Dict[str, Any]) -> None:
    tv["private"]["merkle_path"][0]["sibling_hash"] = "00" * 32


def mutate_leaf_index(tv: Dict[str, Any]) -> None:
    tv["public"]["leaf_index"] += 1


def mutate_path_order(tv: Dict[str, Any]) -> None:
    tv["private"]["merkle_path"] = list(reversed(tv["private"]["merkle_path"]))


def mutate_q_target_max_fp(tv: Dict[str, Any]) -> None:
    tv["private"]["td_witness"]["q_target_max_fp"] += 1


def mutate_target_network_value(tv: Dict[str, Any]) -> None:
    mutate_q_target_max_fp(tv)


def mutate_claimed_target_fp(tv: Dict[str, Any]) -> None:
    tv["public"]["claimed_target_fp"] += 1


def mutate_claimed_loss_fp(tv: Dict[str, Any]) -> None:
    tv["public"]["claimed_loss_fp"] += 1


def mutate_leaf_hash(tv: Dict[str, Any]) -> None:
    tv["private"]["leaf_hash"] = "11" * 32


def mutate_td_error_fp(tv: Dict[str, Any]) -> None:
    tv["private"]["td_witness"]["td_error_fp"] += 1


def build_batch_vector(single: Dict[str, Any], batch_size: int) -> Dict[str, Any]:
    items = []
    for _ in range(batch_size):
        private = single["private"]
        public = single["public"]
        items.append(
            {
                "index": int(public["leaf_index"]),
                "transition": copy.deepcopy(private["transition"]),
                "leaf": copy.deepcopy(private["leaf"]),
                "leaf_hash": private["leaf_hash"],
                "merkle_path": copy.deepcopy(private["merkle_path"]),
                "td_witness": copy.deepcopy(private["td_witness"]),
            }
        )

    total_loss_fp = sum(int(item["td_witness"]["loss_fp"]) for item in items)
    return {
        "schema_version": "td_mvp_batch_test_vector_v1",
        "public": {
            "dataset_root": single["public"]["dataset_root"],
            "fp_scale": int(single["public"]["fp_scale"]),
            "gamma_fp": int(single["public"]["gamma_fp"]),
            "loss_type": single["public"]["loss_type"],
            "batch_size": batch_size,
            "claimed_batch_loss_fp": total_loss_fp // batch_size,
        },
        "private": {
            "items": items,
        },
    }


def mutate_batch_claimed_loss_fp(tv: Dict[str, Any]) -> None:
    tv["public"]["claimed_batch_loss_fp"] += 1


def mutate_batch_size(tv: Dict[str, Any]) -> None:
    tv["public"]["batch_size"] += 1


def mutate_batch_item_loss_fp(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["td_witness"]["loss_fp"] += 1


def mutate_batch_item_index(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["index"] += 1


def mutate_batch_path_order(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["merkle_path"] = list(
        reversed(tv["private"]["items"][0]["merkle_path"])
    )


def mutate_batch_target_network_value(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["td_witness"]["q_target_max_fp"] += 1


def mutate_batch_fixed_point_rounding(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["transition"]["reward"] = (
        float(tv["private"]["items"][0]["transition"]["reward"]) + 0.0006
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    base = load_json(BASE_VECTOR_PATH)
    batch_base = build_batch_vector(base, 2)

    cases: List[Dict[str, Any]] = [
        {
            "case_name": "valid_control",
            "expected_accept": True,
            "mutator": None,
        },
        {
            "case_name": "tamper_schema_version",
            "expected_accept": False,
            "mutator": mutate_schema_version,
        },
        {
            "case_name": "tamper_reward",
            "expected_accept": False,
            "mutator": mutate_reward,
        },
        {
            "case_name": "tamper_fixed_point_rounding",
            "expected_accept": False,
            "mutator": mutate_fixed_point_rounding,
        },
        {
            "case_name": "tamper_done",
            "expected_accept": False,
            "mutator": mutate_done,
        },
        {
            "case_name": "tamper_done_branch",
            "expected_accept": False,
            "mutator": mutate_done_branch,
        },
        {
            "case_name": "tamper_transition_obs",
            "expected_accept": False,
            "mutator": mutate_transition_obs,
        },
        {
            "case_name": "tamper_leaf_encoding",
            "expected_accept": False,
            "mutator": mutate_leaf_encoding,
        },
        {
            "case_name": "tamper_merkle_path",
            "expected_accept": False,
            "mutator": mutate_merkle_path,
        },
        {
            "case_name": "tamper_leaf_index",
            "expected_accept": False,
            "mutator": mutate_leaf_index,
        },
        {
            "case_name": "tamper_path_order",
            "expected_accept": False,
            "mutator": mutate_path_order,
        },
        {
            "case_name": "tamper_q_target_max_fp",
            "expected_accept": False,
            "mutator": mutate_q_target_max_fp,
        },
        {
            "case_name": "tamper_target_network_value",
            "expected_accept": False,
            "mutator": mutate_target_network_value,
        },
        {
            "case_name": "tamper_claimed_target_fp",
            "expected_accept": False,
            "mutator": mutate_claimed_target_fp,
        },
        {
            "case_name": "tamper_claimed_loss_fp",
            "expected_accept": False,
            "mutator": mutate_claimed_loss_fp,
        },
        {
            "case_name": "tamper_leaf_hash",
            "expected_accept": False,
            "mutator": mutate_leaf_hash,
        },
        {
            "case_name": "tamper_td_error_fp",
            "expected_accept": False,
            "mutator": mutate_td_error_fp,
        },
        {
            "case_name": "valid_batch_size_2",
            "expected_accept": True,
            "mutator": None,
            "base": batch_base,
        },
        {
            "case_name": "tamper_batch_claimed_loss_fp",
            "expected_accept": False,
            "mutator": mutate_batch_claimed_loss_fp,
            "base": batch_base,
        },
        {
            "case_name": "tamper_batch_size",
            "expected_accept": False,
            "mutator": mutate_batch_size,
            "base": batch_base,
        },
        {
            "case_name": "tamper_batch_item_loss_fp",
            "expected_accept": False,
            "mutator": mutate_batch_item_loss_fp,
            "base": batch_base,
        },
        {
            "case_name": "tamper_batch_item_index",
            "expected_accept": False,
            "mutator": mutate_batch_item_index,
            "base": batch_base,
        },
        {
            "case_name": "tamper_batch_path_order",
            "expected_accept": False,
            "mutator": mutate_batch_path_order,
            "base": batch_base,
        },
        {
            "case_name": "tamper_batch_target_network_value",
            "expected_accept": False,
            "mutator": mutate_batch_target_network_value,
            "base": batch_base,
        },
        {
            "case_name": "tamper_batch_fixed_point_rounding",
            "expected_accept": False,
            "mutator": mutate_batch_fixed_point_rounding,
            "base": batch_base,
        },
    ]

    rows = []

    for case in cases:
        case_name = case["case_name"]
        expected_accept = bool(case["expected_accept"])
        mutator = case["mutator"]

        tv = copy.deepcopy(case.get("base", base))
        if mutator is not None:
            mutator(tv)

        case_path = OUT_DIR / f"{case_name}.json"
        write_json(case_path, tv)

        result = run_verifier(case_path)
        actual_accept = result.returncode == 0
        passed = actual_accept == expected_accept

        stdout_path = OUT_DIR / f"{case_name}.stdout.txt"
        stderr_path = OUT_DIR / f"{case_name}.stderr.txt"
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")

        rows.append(
            {
                "case_name": case_name,
                "expected_accept": expected_accept,
                "actual_accept": actual_accept,
                "passed": passed,
                "returncode": result.returncode,
                "artifact_path": str(case_path),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
            }
        )

        print(
            f"{case_name}: "
            f"expected_accept={expected_accept} "
            f"actual_accept={actual_accept} "
            f"passed={passed}"
        )

    summary_path = OUT_DIR / "summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_name",
                "expected_accept",
                "actual_accept",
                "passed",
                "returncode",
                "artifact_path",
                "stdout_path",
                "stderr_path",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    all_tests_passed = all(row["passed"] for row in rows)

    print("summary_path =", summary_path)
    print("all_tests_passed =", all_tests_passed)

    if not all_tests_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
