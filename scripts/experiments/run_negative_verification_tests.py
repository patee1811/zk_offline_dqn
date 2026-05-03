# scripts/experiments/run_negative_verification_tests.py

import copy
import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_ARTIFACT = "artifacts/minibatch_td_from_dataset.json"
DEFAULT_MERKLE = "artifacts/cartpole_dqn_eps010_merkle.json"
DEFAULT_CHECKPOINT = "models/offline_dqn_with_target_seed42_best.pt"
DEFAULT_OUT_DIR = "artifacts/negative_tests"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run negative verification tests by tampering artifacts."
    )

    parser.add_argument(
        "--artifact",
        default=DEFAULT_ARTIFACT,
        help="Base valid minibatch TD artifact.",
    )
    parser.add_argument(
        "--merkle",
        default=DEFAULT_MERKLE,
        help="Merkle artifact path.",
    )
    parser.add_argument(
        "--checkpoint",
        default=DEFAULT_CHECKPOINT,
        help="Checkpoint path.",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help="Directory for tampered artifacts and summary.",
    )

    return parser.parse_args()


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def make_tamper_loss_fp(base_artifact: Dict[str, Any]) -> Dict[str, Any]:
    artifact = copy.deepcopy(base_artifact)
    artifact["items"][0]["td_witness"]["loss_fp"] += 1
    return artifact

def make_tamper_reward(base_artifact: Dict[str, Any]) -> Dict[str, Any]:
    artifact = copy.deepcopy(base_artifact)
    artifact["items"][0]["transition"]["reward"] += 1.0
    return artifact
def make_tamper_checkpoint_sha256(base_artifact: Dict[str, Any]) -> Dict[str, Any]:
    artifact = copy.deepcopy(base_artifact)
    artifact["public"]["checkpoint_sha256"] = "0" * 64
    return artifact
def make_tamper_leaf_hash(base_artifact: Dict[str, Any]) -> Dict[str, Any]:
    artifact = copy.deepcopy(base_artifact)
    artifact["items"][0]["leaf_hash"] = "0" * 64
    return artifact
def make_tamper_merkle_path(base_artifact: Dict[str, Any]) -> Dict[str, Any]:
    artifact = copy.deepcopy(base_artifact)

    path = artifact["items"][0]["merkle_path"]
    if not path:
        raise ValueError("Cannot tamper empty merkle_path")

    path[0]["sibling_hash"] = "0" * 64
    return artifact
def make_tamper_online_state_dict_sha256(base_artifact: Dict[str, Any]) -> Dict[str, Any]:
    artifact = copy.deepcopy(base_artifact)
    artifact["public"]["online_state_dict_sha256"] = "0" * 64
    return artifact



def run_minibatch_verifier(
    artifact_path: Path,
    checkpoint_path: str,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["MINIBATCH_TD_ARTIFACT_PATH"] = artifact_path.as_posix()
    env["MINIBATCH_TD_CHECKPOINT_PATH"] = checkpoint_path

    cmd = [
        sys.executable,
        "scripts/artifacts_export/verify_minibatch_td_artifact.py",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
    )

    accepted = (
        result.returncode == 0
        and "verification_passed = True" in result.stdout
    )

    return {
        "returncode": result.returncode,
        "accepted": accepted,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def write_summary_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "case_name",
        "expected_accept",
        "actual_accept",
        "passed",
        "artifact_path",
        "returncode",
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})

def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_artifact = load_json(args.artifact)

    planned_cases = [
        "valid_control",
        "tamper_reward",
        "tamper_loss_fp",
        "tamper_checkpoint_sha256",
        "tamper_online_state_dict_sha256",
        "tamper_leaf_hash",
        "tamper_merkle_path",
    ]

    print("=== NEGATIVE VERIFICATION TEST RUNNER ===")
    print("base_artifact =", args.artifact)
    print("merkle =", args.merkle)
    print("checkpoint =", args.checkpoint)
    print("out_dir =", out_dir.as_posix())
    print("num_planned_cases =", len(planned_cases))
    print()

    for case_name in planned_cases:
        print("planned_case =", case_name)

    # Save a copy of the valid artifact as a first sanity output.
    valid_copy_path = out_dir / "valid_control.json"
    save_json(base_artifact, valid_copy_path)

    rows: List[Dict[str, Any]] = []

    valid_result = run_minibatch_verifier(
        artifact_path=valid_copy_path,
        checkpoint_path=args.checkpoint,
    )

    valid_row = {
        "case_name": "valid_control",
        "expected_accept": True,
        "actual_accept": valid_result["accepted"],
        "passed": valid_result["accepted"] is True,
        "artifact_path": valid_copy_path.as_posix(),
        "returncode": valid_result["returncode"],
    }

    rows.append(valid_row)

    tamper_loss_path = out_dir / "tamper_loss_fp.json"
    tamper_loss_artifact = make_tamper_loss_fp(base_artifact)
    save_json(tamper_loss_artifact, tamper_loss_path)

    tamper_loss_result = run_minibatch_verifier(
        artifact_path=tamper_loss_path,
        checkpoint_path=args.checkpoint,
    )

    tamper_loss_row = {
        "case_name": "tamper_loss_fp",
        "expected_accept": False,
        "actual_accept": tamper_loss_result["accepted"],
        "passed": tamper_loss_result["accepted"] is False,
        "artifact_path": tamper_loss_path.as_posix(),
        "returncode": tamper_loss_result["returncode"],
    }

    rows.append(tamper_loss_row)


    tamper_reward_path = out_dir / "tamper_reward.json"
    tamper_reward_artifact = make_tamper_reward(base_artifact)
    save_json(tamper_reward_artifact, tamper_reward_path)

    tamper_reward_result = run_minibatch_verifier(
        artifact_path=tamper_reward_path,
        checkpoint_path=args.checkpoint,
    )

    tamper_reward_row = {
        "case_name": "tamper_reward",
        "expected_accept": False,
        "actual_accept": tamper_reward_result["accepted"],
        "passed": tamper_reward_result["accepted"] is False,
        "artifact_path": tamper_reward_path.as_posix(),
        "returncode": tamper_reward_result["returncode"],
    }

    rows.append(tamper_reward_row)

    tamper_checkpoint_path = out_dir / "tamper_checkpoint_sha256.json"
    tamper_checkpoint_artifact = make_tamper_checkpoint_sha256(base_artifact)
    save_json(tamper_checkpoint_artifact, tamper_checkpoint_path)

    tamper_checkpoint_result = run_minibatch_verifier(
        artifact_path=tamper_checkpoint_path,
        checkpoint_path=args.checkpoint,
    )

    tamper_checkpoint_row = {
        "case_name": "tamper_checkpoint_sha256",
        "expected_accept": False,
        "actual_accept": tamper_checkpoint_result["accepted"],
        "passed": tamper_checkpoint_result["accepted"] is False,
        "artifact_path": tamper_checkpoint_path.as_posix(),
        "returncode": tamper_checkpoint_result["returncode"],
    }

    rows.append(tamper_checkpoint_row)

    tamper_leaf_hash_path = out_dir / "tamper_leaf_hash.json"
    tamper_leaf_hash_artifact = make_tamper_leaf_hash(base_artifact)
    save_json(tamper_leaf_hash_artifact, tamper_leaf_hash_path)

    tamper_leaf_hash_result = run_minibatch_verifier(
        artifact_path=tamper_leaf_hash_path,
        checkpoint_path=args.checkpoint,
    )

    tamper_leaf_hash_row = {
        "case_name": "tamper_leaf_hash",
        "expected_accept": False,
        "actual_accept": tamper_leaf_hash_result["accepted"],
        "passed": tamper_leaf_hash_result["accepted"] is False,
        "artifact_path": tamper_leaf_hash_path.as_posix(),
        "returncode": tamper_leaf_hash_result["returncode"],
    }

    rows.append(tamper_leaf_hash_row)

    tamper_merkle_path_path = out_dir / "tamper_merkle_path.json"
    tamper_merkle_path_artifact = make_tamper_merkle_path(base_artifact)
    save_json(tamper_merkle_path_artifact, tamper_merkle_path_path)

    tamper_merkle_path_result = run_minibatch_verifier(
        artifact_path=tamper_merkle_path_path,
        checkpoint_path=args.checkpoint,
    )

    tamper_merkle_path_row = {
        "case_name": "tamper_merkle_path",
        "expected_accept": False,
        "actual_accept": tamper_merkle_path_result["accepted"],
        "passed": tamper_merkle_path_result["accepted"] is False,
        "artifact_path": tamper_merkle_path_path.as_posix(),
        "returncode": tamper_merkle_path_result["returncode"],
    }

    rows.append(tamper_merkle_path_row)

    tamper_online_state_path = out_dir / "tamper_online_state_dict_sha256.json"
    tamper_online_state_artifact = make_tamper_online_state_dict_sha256(base_artifact)
    save_json(tamper_online_state_artifact, tamper_online_state_path)

    tamper_online_state_result = run_minibatch_verifier(
        artifact_path=tamper_online_state_path,
        checkpoint_path=args.checkpoint,
    )

    tamper_online_state_row = {
        "case_name": "tamper_online_state_dict_sha256",
        "expected_accept": False,
        "actual_accept": tamper_online_state_result["accepted"],
        "passed": tamper_online_state_result["accepted"] is False,
        "artifact_path": tamper_online_state_path.as_posix(),
        "returncode": tamper_online_state_result["returncode"],
    }

    rows.append(tamper_online_state_row)

    summary_csv_path = out_dir / "summary.csv"
    write_summary_csv(rows, summary_csv_path)

    print()
    print("valid_control_path =", valid_copy_path.as_posix())
    print("valid_control_accept =", valid_result["accepted"])
    print("tamper_loss_fp_accept =", tamper_loss_result["accepted"])
    print("tamper_loss_fp_passed =", tamper_loss_row["passed"])
    print("tamper_reward_accept =", tamper_reward_result["accepted"])
    print("tamper_reward_passed =", tamper_reward_row["passed"])
    print("tamper_checkpoint_sha256_accept =", tamper_checkpoint_result["accepted"])
    print("tamper_checkpoint_sha256_passed =", tamper_checkpoint_row["passed"])
    print("tamper_online_state_dict_sha256_accept =", tamper_online_state_result["accepted"])
    print("tamper_online_state_dict_sha256_passed =", tamper_online_state_row["passed"])
    print("tamper_leaf_hash_accept =", tamper_leaf_hash_result["accepted"])
    print("tamper_leaf_hash_passed =", tamper_leaf_hash_row["passed"])
    print("tamper_merkle_path_accept =", tamper_merkle_path_result["accepted"])
    print("tamper_merkle_path_passed =", tamper_merkle_path_row["passed"])
    print("summary_csv_path =", summary_csv_path.as_posix())
    print("all_tests_passed =", all(row["passed"] for row in rows))


if __name__ == "__main__":
    main()