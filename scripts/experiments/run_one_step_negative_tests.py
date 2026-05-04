import argparse
import copy
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_ARTIFACT_PATH = "artifacts/one_step_update_artifact.json"
DEFAULT_MERKLE_PATH = "artifacts/cartpole_dqn_eps010_merkle.json"
DEFAULT_CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"
DEFAULT_POST_CHECKPOINT_PATH = "artifacts/one_step_post_checkpoint.pt"
DEFAULT_OUT_DIR = "artifacts/one_step_negative_tests"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one-step update negative verification tests."
    )

    parser.add_argument(
        "--artifact",
        default=DEFAULT_ARTIFACT_PATH,
        help="Valid one-step update artifact path.",
    )
    parser.add_argument(
        "--merkle",
        default=DEFAULT_MERKLE_PATH,
        help="Merkle artifact path.",
    )
    parser.add_argument(
        "--checkpoint",
        default=DEFAULT_CHECKPOINT_PATH,
        help="Pre-update checkpoint path.",
    )
    parser.add_argument(
        "--post-checkpoint",
        default=DEFAULT_POST_CHECKPOINT_PATH,
        help="Post-update checkpoint path.",
    )
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help="Directory for tampered artifacts and summary.",
    )

    return parser.parse_args()


def load_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def run_one_step_verifier(
    artifact_path: Path,
    merkle_path: str,
    checkpoint_path: str,
    post_checkpoint_path: str,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["ONE_STEP_ARTIFACT_PATH"] = artifact_path.as_posix()
    env["ONE_STEP_MERKLE_PATH"] = merkle_path
    env["ONE_STEP_CHECKPOINT_PATH"] = checkpoint_path
    env["ONE_STEP_POST_CHECKPOINT_PATH"] = post_checkpoint_path

    cmd = [
        sys.executable,
        "scripts/artifacts_export/verify_one_step_update_artifact.py",
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


def mutate_first_numeric_leaf(obj: Any, delta: float = 1.0) -> bool:
    """
    Mutates the first numeric leaf found inside nested dict/list structures.
    Returns True if a mutation was applied.
    """
    if isinstance(obj, dict):
        for key in obj:
            if mutate_first_numeric_leaf(obj[key], delta=delta):
                return True
        return False

    if isinstance(obj, list):
        for i, value in enumerate(obj):
            if isinstance(value, bool):
                continue

            if isinstance(value, (int, float)):
                obj[i] = value + delta
                return True

            if mutate_first_numeric_leaf(value, delta=delta):
                return True

        return False

    return False


def make_tamper_next_action_online(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    td_witness = artifact["items"][0]["td_witness"]

    current = int(td_witness["next_action_online"])
    td_witness["next_action_online"] = 1 - current

    return artifact


def make_tamper_q_target_max_fp(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["items"][0]["td_witness"]["q_target_max_fp"] += 1
    return artifact


def make_tamper_loss_fp(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["items"][0]["td_witness"]["loss_fp"] += 1
    return artifact


def make_tamper_gradient_tensor(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    gradient_tensors = artifact["update_witness"]["gradient_tensors"]

    mutated = mutate_first_numeric_leaf(gradient_tensors, delta=1.0)
    if not mutated:
        raise ValueError("Could not mutate any gradient tensor numeric leaf.")

    return artifact


def make_tamper_delta_tensor(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    delta_tensors = artifact["update_witness"]["delta_tensors"]

    mutated = mutate_first_numeric_leaf(delta_tensors, delta=1.0)
    if not mutated:
        raise ValueError("Could not mutate any delta tensor numeric leaf.")

    return artifact


def make_tamper_post_checkpoint_sha256(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["public"]["post_checkpoint_sha256"] = "0" * 64
    return artifact


def make_tamper_post_online_state_dict_sha256(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["public"]["post_online_state_dict_sha256"] = "0" * 64
    return artifact


def make_tamper_learning_rate_fp(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["public"]["learning_rate_fp"] += 1
    return artifact


def make_tamper_batch_indices(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["public"]["batch_indices"][0] += 1
    return artifact


def add_case(
    rows: List[Dict[str, Any]],
    case_name: str,
    expected_accept: bool,
    artifact: Dict[str, Any],
    artifact_path: Path,
    merkle_path: str,
    checkpoint_path: str,
    post_checkpoint_path: str,
) -> Dict[str, Any]:
    save_json(artifact, artifact_path)

    result = run_one_step_verifier(
        artifact_path=artifact_path,
        merkle_path=merkle_path,
        checkpoint_path=checkpoint_path,
        post_checkpoint_path=post_checkpoint_path,
    )

    row = {
        "case_name": case_name,
        "expected_accept": expected_accept,
        "actual_accept": result["accepted"],
        "passed": result["accepted"] is expected_accept,
        "artifact_path": artifact_path.as_posix(),
        "returncode": result["returncode"],
    }

    rows.append(row)

    print(f"{case_name}_accept =", result["accepted"])
    print(f"{case_name}_passed =", row["passed"])

    if not row["passed"]:
        print(f"--- {case_name} STDOUT ---")
        print(result["stdout"])
        print(f"--- {case_name} STDERR ---")
        print(result["stderr"])

    return result


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_artifact = load_json(args.artifact)

    planned_cases = [
        "valid_one_step",
        "tamper_next_action_online",
        "tamper_q_target_max_fp",
        "tamper_loss_fp",
        "tamper_gradient_tensor",
        "tamper_delta_tensor",
        "tamper_post_checkpoint_sha256",
        "tamper_post_online_state_dict_sha256",
        "tamper_learning_rate_fp",
        "tamper_batch_indices",
    ]

    print("=== ONE-STEP NEGATIVE VERIFICATION TEST RUNNER ===")
    print("base_artifact =", args.artifact)
    print("merkle =", args.merkle)
    print("checkpoint =", args.checkpoint)
    print("post_checkpoint =", args.post_checkpoint)
    print("out_dir =", out_dir.as_posix())
    print("num_planned_cases =", len(planned_cases))
    print()

    for case_name in planned_cases:
        print("planned_case =", case_name)

    print()

    rows: List[Dict[str, Any]] = []

    add_case(
        rows=rows,
        case_name="valid_one_step",
        expected_accept=True,
        artifact=base_artifact,
        artifact_path=out_dir / "valid_one_step.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_next_action_online",
        expected_accept=False,
        artifact=make_tamper_next_action_online(base_artifact),
        artifact_path=out_dir / "tamper_next_action_online.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_q_target_max_fp",
        expected_accept=False,
        artifact=make_tamper_q_target_max_fp(base_artifact),
        artifact_path=out_dir / "tamper_q_target_max_fp.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_loss_fp",
        expected_accept=False,
        artifact=make_tamper_loss_fp(base_artifact),
        artifact_path=out_dir / "tamper_loss_fp.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_gradient_tensor",
        expected_accept=False,
        artifact=make_tamper_gradient_tensor(base_artifact),
        artifact_path=out_dir / "tamper_gradient_tensor.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_delta_tensor",
        expected_accept=False,
        artifact=make_tamper_delta_tensor(base_artifact),
        artifact_path=out_dir / "tamper_delta_tensor.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_post_checkpoint_sha256",
        expected_accept=False,
        artifact=make_tamper_post_checkpoint_sha256(base_artifact),
        artifact_path=out_dir / "tamper_post_checkpoint_sha256.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_post_online_state_dict_sha256",
        expected_accept=False,
        artifact=make_tamper_post_online_state_dict_sha256(base_artifact),
        artifact_path=out_dir / "tamper_post_online_state_dict_sha256.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_learning_rate_fp",
        expected_accept=False,
        artifact=make_tamper_learning_rate_fp(base_artifact),
        artifact_path=out_dir / "tamper_learning_rate_fp.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    add_case(
        rows=rows,
        case_name="tamper_batch_indices",
        expected_accept=False,
        artifact=make_tamper_batch_indices(base_artifact),
        artifact_path=out_dir / "tamper_batch_indices.json",
        merkle_path=args.merkle,
        checkpoint_path=args.checkpoint,
        post_checkpoint_path=args.post_checkpoint,
    )

    summary_csv_path = out_dir / "summary.csv"
    write_summary_csv(rows, summary_csv_path)

    print()
    print("summary_csv_path =", summary_csv_path.as_posix())
    print("all_tests_passed =", all(row["passed"] for row in rows))


if __name__ == "__main__":
    main()
