import argparse
import csv
import json
import os
import subprocess
import sys
import time
from typing import List, Dict, Any


DEFAULT_BATCHES = [
    [0, 1, 2, 3],
    [10, 11, 12, 13],
    [100, 101, 102, 103],
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark one-step offline DQN update artifact export/verify across multiple minibatches."
    )
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--merkle", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument(
        "--batches-json",
        type=str,
        default="",
        help='Optional JSON string for batches, e.g. "[[0,1,2,3],[10,11,12,13]]"',
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="artifacts/benchmarks/one_step_update",
    )
    parser.add_argument(
        "--summary-json",
        type=str,
        default="artifacts/benchmarks/one_step_update/summary.json",
    )
    parser.add_argument(
        "--summary-csv",
        type=str,
        default="artifacts/benchmarks/one_step_update/summary.csv",
    )
    return parser.parse_args()


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_batches(batches_json: str) -> List[List[int]]:
    if not batches_json:
        return DEFAULT_BATCHES
    parsed = json.loads(batches_json)
    if not isinstance(parsed, list) or not all(isinstance(x, list) for x in parsed):
        raise ValueError("batches-json must decode to a list of lists of integers.")
    return [[int(v) for v in batch] for batch in parsed]


def run_command(cmd: List[str]) -> Dict[str, Any]:
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - start
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_sec": elapsed,
    }


def extract_line_value(text: str, prefix: str):
    for line in text.splitlines():
        if line.strip().startswith(prefix):
            return line.split("=", 1)[1].strip()
    return None


def main():
    args = parse_args()
    batches = load_batches(args.batches_json)

    ensure_dir(args.out_dir)
    ensure_dir(os.path.dirname(args.summary_json) or ".")
    ensure_dir(os.path.dirname(args.summary_csv) or ".")

    results = []

    for run_idx, batch in enumerate(batches):
        batch_name = "_".join(str(x) for x in batch)
        artifact_path = os.path.join(args.out_dir, f"artifact_batch_{batch_name}.json")
        post_ckpt_path = os.path.join(args.out_dir, f"post_ckpt_batch_{batch_name}.pt")

        export_cmd = [
            sys.executable,
            "scripts/artifacts_export/export_one_step_update_artifact.py",
            "--data", args.data,
            "--merkle", args.merkle,
            "--checkpoint", args.checkpoint,
            "--indices", ",".join(str(x) for x in batch),
            "--lr", str(args.lr),
            "--post-checkpoint-out", post_ckpt_path,
            "--out", artifact_path,
        ]

        verify_cmd = [
            sys.executable,
            "scripts/artifacts_export/verify_one_step_update_artifact.py",
        ]

        export_result = run_command(export_cmd)

        verify_result = {
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "elapsed_sec": None,
        }

        verification_passed = False
        batch_loss_fp = None
        pre_checkpoint_sha256 = None
        post_checkpoint_sha256 = None

        if export_result["returncode"] == 0:
            old_artifact_env = os.environ.get("ONE_STEP_ARTIFACT_PATH")
            old_merkle_env = os.environ.get("ONE_STEP_MERKLE_PATH")

            try:
                os.environ["ONE_STEP_ARTIFACT_PATH"] = artifact_path
                os.environ["ONE_STEP_MERKLE_PATH"] = args.merkle
                verify_result = run_command(verify_cmd)
            finally:
                if old_artifact_env is None:
                    os.environ.pop("ONE_STEP_ARTIFACT_PATH", None)
                else:
                    os.environ["ONE_STEP_ARTIFACT_PATH"] = old_artifact_env

                if old_merkle_env is None:
                    os.environ.pop("ONE_STEP_MERKLE_PATH", None)
                else:
                    os.environ["ONE_STEP_MERKLE_PATH"] = old_merkle_env

            if verify_result["stdout"]:
                verification_passed = "verification_passed = True" in verify_result["stdout"]

            if os.path.exists(artifact_path):
                with open(artifact_path, "r", encoding="utf-8") as f:
                    artifact = json.load(f)

                batch_loss_fp = artifact["update_witness"]["batch_loss_fp"]
                pre_checkpoint_sha256 = artifact["public"]["pre_checkpoint_sha256"]
                post_checkpoint_sha256 = artifact["public"]["post_checkpoint_sha256"]

        result = {
            "run_idx": run_idx,
            "batch_indices": batch,
            "artifact_path": artifact_path,
            "post_checkpoint_path": post_ckpt_path,
            "export_returncode": export_result["returncode"],
            "verify_returncode": verify_result["returncode"],
            "export_time_sec": export_result["elapsed_sec"],
            "verify_time_sec": verify_result["elapsed_sec"],
            "verification_passed": verification_passed,
            "batch_loss_fp": batch_loss_fp,
            "pre_checkpoint_sha256": pre_checkpoint_sha256,
            "post_checkpoint_sha256": post_checkpoint_sha256,
            "export_stdout": export_result["stdout"],
            "export_stderr": export_result["stderr"],
            "verify_stdout": verify_result["stdout"],
            "verify_stderr": verify_result["stderr"],
        }
        results.append(result)

        print("=" * 80)
        print(f"RUN {run_idx}")
        print("batch_indices =", batch)
        print("export_returncode =", export_result["returncode"])
        print("verify_returncode =", verify_result["returncode"])
        print("export_time_sec =", round(export_result["elapsed_sec"], 6))
        print("verify_time_sec =", None if verify_result["elapsed_sec"] is None else round(verify_result["elapsed_sec"], 6))
        print("batch_loss_fp =", batch_loss_fp)
        print("verification_passed =", verification_passed)

    with open(args.summary_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(args.summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_idx",
                "batch_indices",
                "artifact_path",
                "post_checkpoint_path",
                "export_returncode",
                "verify_returncode",
                "export_time_sec",
                "verify_time_sec",
                "verification_passed",
                "batch_loss_fp",
                "pre_checkpoint_sha256",
                "post_checkpoint_sha256",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "run_idx": row["run_idx"],
                    "batch_indices": json.dumps(row["batch_indices"]),
                    "artifact_path": row["artifact_path"],
                    "post_checkpoint_path": row["post_checkpoint_path"],
                    "export_returncode": row["export_returncode"],
                    "verify_returncode": row["verify_returncode"],
                    "export_time_sec": row["export_time_sec"],
                    "verify_time_sec": row["verify_time_sec"],
                    "verification_passed": row["verification_passed"],
                    "batch_loss_fp": row["batch_loss_fp"],
                    "pre_checkpoint_sha256": row["pre_checkpoint_sha256"],
                    "post_checkpoint_sha256": row["post_checkpoint_sha256"],
                }
            )

    print("=" * 80)
    print("DONE")
    print("summary_json =", args.summary_json)
    print("summary_csv =", args.summary_csv)


if __name__ == "__main__":
    main()