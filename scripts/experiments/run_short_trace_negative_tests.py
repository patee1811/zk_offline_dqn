import argparse
import copy
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_CONTIGUOUS_ARTIFACT = "artifacts/fixtures/short_trace/short_trace_update_artifact.json"
DEFAULT_SEEDED_ARTIFACT = "artifacts/fixtures/short_trace/short_trace_seeded_artifact.json"

DEFAULT_MERKLE_PATH = "artifacts/fixtures/membership/cartpole_dqn_eps010_merkle.json"
DEFAULT_INITIAL_CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"

DEFAULT_CONTIGUOUS_FINAL_CHECKPOINT_PATH = (
    "artifacts/fixtures/short_trace/short_trace_work/step_1_post_synced_4_5_6_7.pt"
)
DEFAULT_SEEDED_FINAL_CHECKPOINT_PATH = (
    "artifacts/fixtures/short_trace/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt"
)

DEFAULT_CONTIGUOUS_WORK_DIR = "artifacts/fixtures/short_trace/short_trace_work"
DEFAULT_SEEDED_WORK_DIR = "artifacts/fixtures/short_trace/short_trace_seeded_work"

DEFAULT_OUT_DIR = "artifacts/short_trace_negative_tests"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run short-trace negative verification tests by tampering trace artifacts."
    )

    parser.add_argument(
        "--contiguous-artifact",
        default=DEFAULT_CONTIGUOUS_ARTIFACT,
        help="Valid contiguous short-trace artifact path.",
    )
    parser.add_argument(
        "--seeded-artifact",
        default=DEFAULT_SEEDED_ARTIFACT,
        help="Valid seeded-permutation short-trace artifact path.",
    )
    parser.add_argument(
        "--merkle",
        default=DEFAULT_MERKLE_PATH,
        help="Merkle artifact path.",
    )
    parser.add_argument(
        "--initial-checkpoint",
        default=DEFAULT_INITIAL_CHECKPOINT_PATH,
        help="Initial checkpoint path.",
    )
    parser.add_argument(
        "--contiguous-final-checkpoint",
        default=DEFAULT_CONTIGUOUS_FINAL_CHECKPOINT_PATH,
        help="Final checkpoint path for the contiguous trace.",
    )
    parser.add_argument(
        "--contiguous-work-dir",
        default=DEFAULT_CONTIGUOUS_WORK_DIR,
        help="Work directory containing per-step checkpoints for the contiguous trace.",
    )
    parser.add_argument(
        "--seeded-final-checkpoint",
        default=DEFAULT_SEEDED_FINAL_CHECKPOINT_PATH,
        help="Final checkpoint path for the seeded trace.",
    )
    parser.add_argument(
        "--seeded-work-dir",
        default=DEFAULT_SEEDED_WORK_DIR,
        help="Work directory containing per-step checkpoints for the seeded trace.",
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


def run_short_trace_verifier(
    artifact_path: Path,
    merkle_path: str,
    initial_checkpoint_path: str,
    final_checkpoint_path: str,
    work_dir: str,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["SHORT_TRACE_ARTIFACT_PATH"] = artifact_path.as_posix()
    env["SHORT_TRACE_MERKLE_PATH"] = merkle_path
    env["SHORT_TRACE_INITIAL_CHECKPOINT_PATH"] = initial_checkpoint_path
    env["SHORT_TRACE_FINAL_CHECKPOINT_PATH"] = final_checkpoint_path
    env["SHORT_TRACE_WORK_DIR"] = work_dir

    cmd = [
        sys.executable,
        "scripts/artifacts_export/verify_short_trace_update_artifact.py",
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


def make_tamper_contiguous_public_batch(
    contiguous_artifact: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(contiguous_artifact)
    artifact["public"]["trace_batch_indices"][0] = [1, 2, 3, 4]
    return artifact


def make_tamper_seeded_public_batch(
    seeded_artifact: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(seeded_artifact)
    artifact["public"]["trace_batch_indices"][0] = [0, 1, 2, 3]
    return artifact


def make_tamper_sampling_seed(
    seeded_artifact: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(seeded_artifact)
    artifact["public"]["sampling_seed"] = int(artifact["public"]["sampling_seed"]) + 1
    return artifact


def make_tamper_dataset_size(
    seeded_artifact: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(seeded_artifact)
    artifact["public"]["dataset_size"] = 8
    return artifact


def make_tamper_final_checkpoint_sha256(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["public"]["final_checkpoint_sha256"] = "0" * 64
    return artifact


def make_tamper_final_online_state_dict_sha256(
    artifact_in: Dict[str, Any],
) -> Dict[str, Any]:
    artifact = copy.deepcopy(artifact_in)
    artifact["public"]["final_online_state_dict_sha256"] = "0" * 64
    return artifact


def add_case(
    rows: List[Dict[str, Any]],
    case_name: str,
    expected_accept: bool,
    artifact: Dict[str, Any],
    artifact_path: Path,
    merkle_path: str,
    initial_checkpoint_path: str,
    final_checkpoint_path: str,
    work_dir: str,
) -> Dict[str, Any]:
    save_json(artifact, artifact_path)

    result = run_short_trace_verifier(
        artifact_path=artifact_path,
        merkle_path=merkle_path,
        initial_checkpoint_path=initial_checkpoint_path,
        final_checkpoint_path=final_checkpoint_path,
        work_dir=work_dir,
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

    contiguous_artifact = load_json(args.contiguous_artifact)
    seeded_artifact = load_json(args.seeded_artifact)

    planned_cases = [
        "valid_contiguous",
        "valid_seeded",
        "tamper_contiguous_public_batch",
        "tamper_seeded_public_batch",
        "tamper_sampling_seed",
        "tamper_dataset_size",
        "tamper_final_checkpoint_sha256",
        "tamper_final_online_state_dict_sha256",
    ]

    print("=== SHORT-TRACE NEGATIVE VERIFICATION TEST RUNNER ===")
    print("contiguous_artifact =", args.contiguous_artifact)
    print("seeded_artifact =", args.seeded_artifact)
    print("merkle =", args.merkle)
    print("initial_checkpoint =", args.initial_checkpoint)
    print("contiguous_final_checkpoint =", args.contiguous_final_checkpoint)
    print("seeded_final_checkpoint =", args.seeded_final_checkpoint)
    print("contiguous_work_dir =", args.contiguous_work_dir)
    print("seeded_work_dir =", args.seeded_work_dir)
    print("out_dir =", out_dir.as_posix())
    print("num_planned_cases =", len(planned_cases))
    print()

    for case_name in planned_cases:
        print("planned_case =", case_name)

    print()

    rows: List[Dict[str, Any]] = []

    add_case(
        rows=rows,
        case_name="valid_contiguous",
        expected_accept=True,
        artifact=contiguous_artifact,
        artifact_path=out_dir / "valid_contiguous.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.contiguous_final_checkpoint,
        work_dir=args.contiguous_work_dir,
    )

    add_case(
        rows=rows,
        case_name="valid_seeded",
        expected_accept=True,
        artifact=seeded_artifact,
        artifact_path=out_dir / "valid_seeded.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.seeded_final_checkpoint,
        work_dir=args.seeded_work_dir,
    )

    add_case(
        rows=rows,
        case_name="tamper_contiguous_public_batch",
        expected_accept=False,
        artifact=make_tamper_contiguous_public_batch(contiguous_artifact),
        artifact_path=out_dir / "tamper_contiguous_public_batch.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.contiguous_final_checkpoint,
        work_dir=args.contiguous_work_dir,
    )

    add_case(
        rows=rows,
        case_name="tamper_seeded_public_batch",
        expected_accept=False,
        artifact=make_tamper_seeded_public_batch(seeded_artifact),
        artifact_path=out_dir / "tamper_seeded_public_batch.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.seeded_final_checkpoint,
        work_dir=args.seeded_work_dir,
    )

    add_case(
        rows=rows,
        case_name="tamper_sampling_seed",
        expected_accept=False,
        artifact=make_tamper_sampling_seed(seeded_artifact),
        artifact_path=out_dir / "tamper_sampling_seed.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.seeded_final_checkpoint,
        work_dir=args.seeded_work_dir,
    )

    add_case(
        rows=rows,
        case_name="tamper_dataset_size",
        expected_accept=False,
        artifact=make_tamper_dataset_size(seeded_artifact),
        artifact_path=out_dir / "tamper_dataset_size.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.seeded_final_checkpoint,
        work_dir=args.seeded_work_dir,
    )

    add_case(
        rows=rows,
        case_name="tamper_final_checkpoint_sha256",
        expected_accept=False,
        artifact=make_tamper_final_checkpoint_sha256(seeded_artifact),
        artifact_path=out_dir / "tamper_final_checkpoint_sha256.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.seeded_final_checkpoint,
        work_dir=args.seeded_work_dir,
    )

    add_case(
        rows=rows,
        case_name="tamper_final_online_state_dict_sha256",
        expected_accept=False,
        artifact=make_tamper_final_online_state_dict_sha256(seeded_artifact),
        artifact_path=out_dir / "tamper_final_online_state_dict_sha256.json",
        merkle_path=args.merkle,
        initial_checkpoint_path=args.initial_checkpoint,
        final_checkpoint_path=args.seeded_final_checkpoint,
        work_dir=args.seeded_work_dir,
    )

    summary_csv_path = out_dir / "summary.csv"
    write_summary_csv(rows, summary_csv_path)

    print()
    print("summary_csv_path =", summary_csv_path.as_posix())
    print("all_tests_passed =", all(row["passed"] for row in rows))


if __name__ == "__main__":
    main()