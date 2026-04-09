import argparse
import csv
import json
import os
import subprocess
import sys
import time
from typing import List, Dict, Any


DEFAULT_TRACES = [
    [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15],
        [16, 17, 18, 19],
        [20, 21, 22, 23],
        [24, 25, 26, 27],
        [28, 29, 30, 31],
    ],
    [
        [32, 33, 34, 35],
        [36, 37, 38, 39],
        [40, 41, 42, 43],
        [44, 45, 46, 47],
        [48, 49, 50, 51],
        [52, 53, 54, 55],
        [56, 57, 58, 59],
        [60, 61, 62, 63],
    ],
    [
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20, 21, 22, 23],
        [24, 25, 26, 27, 28, 29, 30, 31],
        [32, 33, 34, 35, 36, 37, 38, 39],
        [40, 41, 42, 43, 44, 45, 46, 47],
        [48, 49, 50, 51, 52, 53, 54, 55],
        [56, 57, 58, 59, 60, 61, 62, 63],
    ],
]

def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark short-trace offline DQN update artifact export/verify."
    )
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--merkle", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--target-sync-every", type=int, default=2)
    parser.add_argument(
        "--traces-json",
        type=str,
        default="",
        help='Optional JSON string for traces, e.g. "[[[0,1],[2,3]],[[4,5],[6,7]]]"',
    )
    parser.add_argument(
        "--work-root",
        type=str,
        default="artifacts/benchmarks/short_trace_update/work",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="artifacts/benchmarks/short_trace_update",
    )
    parser.add_argument(
        "--summary-json",
        type=str,
        default="artifacts/benchmarks/short_trace_update/summary.json",
    )
    parser.add_argument(
        "--summary-csv",
        type=str,
        default="artifacts/benchmarks/short_trace_update/summary.csv",
    )
    return parser.parse_args()


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_traces(traces_json: str) -> List[List[List[int]]]:
    if not traces_json:
        return DEFAULT_TRACES
    parsed = json.loads(traces_json)
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("traces-json must be a non-empty JSON list.")
    out = []
    for trace in parsed:
        if not isinstance(trace, list) or not trace:
            raise ValueError("Each trace must be a non-empty list of minibatches.")
        trace_out = []
        for batch in trace:
            if not isinstance(batch, list) or not batch:
                raise ValueError("Each minibatch inside a trace must be a non-empty list.")
            trace_out.append([int(x) for x in batch])
        out.append(trace_out)
    return out


def run_command(cmd: List[str], env: Dict[str, str] = None) -> Dict[str, Any]:
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
    )
    elapsed = time.perf_counter() - start
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_sec": elapsed,
    }


def main():
    args = parse_args()
    traces = load_traces(args.traces_json)

    ensure_dir(args.out_dir)
    ensure_dir(args.work_root)
    ensure_dir(os.path.dirname(args.summary_json) or ".")
    ensure_dir(os.path.dirname(args.summary_csv) or ".")

    results = []

    for run_idx, trace in enumerate(traces):
        trace_name_parts = []
        for batch in trace:
            trace_name_parts.append("_".join(str(x) for x in batch))
        trace_name = "__".join(trace_name_parts)

        work_dir = os.path.join(args.work_root, f"trace_{run_idx}_{trace_name}")
        artifact_path = os.path.join(args.out_dir, f"trace_{run_idx}_{trace_name}.json")

        export_cmd = [
            sys.executable,
            "scripts/artifacts_export/export_short_trace_update_artifact.py",
            "--data", args.data,
            "--merkle", args.merkle,
            "--checkpoint", args.checkpoint,
            "--trace-batches-json", json.dumps(trace),
            "--lr", str(args.lr),
            "--target-sync-every", str(args.target_sync_every),
            "--work-dir", work_dir,
            "--out", artifact_path,
        ]

        export_result = run_command(export_cmd)

        verify_result = {
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "elapsed_sec": None,
        }

        verification_passed = False
        num_steps = None
        initial_checkpoint_sha256 = None
        final_checkpoint_sha256 = None

        if export_result["returncode"] == 0:
            env = os.environ.copy()
            env["SHORT_TRACE_ARTIFACT_PATH"] = artifact_path

            verify_cmd = [
                sys.executable,
                "scripts/artifacts_export/verify_short_trace_update_artifact.py",
            ]
            verify_result = run_command(verify_cmd, env=env)

            if verify_result["stdout"]:
                verification_passed = "verification_passed = True" in verify_result["stdout"]

            if os.path.exists(artifact_path):
                with open(artifact_path, "r", encoding="utf-8") as f:
                    artifact = json.load(f)
                num_steps = artifact["public"]["num_steps"]
                initial_checkpoint_sha256 = artifact["public"]["initial_checkpoint_sha256"]
                final_checkpoint_sha256 = artifact["public"]["final_checkpoint_sha256"]

        result = {
            "run_idx": run_idx,
            "trace_batch_indices": trace,
            "num_steps": num_steps,
            "artifact_path": artifact_path,
            "work_dir": work_dir,
            "export_returncode": export_result["returncode"],
            "verify_returncode": verify_result["returncode"],
            "export_time_sec": export_result["elapsed_sec"],
            "verify_time_sec": verify_result["elapsed_sec"],
            "verification_passed": verification_passed,
            "initial_checkpoint_sha256": initial_checkpoint_sha256,
            "final_checkpoint_sha256": final_checkpoint_sha256,
            "export_stdout": export_result["stdout"],
            "export_stderr": export_result["stderr"],
            "verify_stdout": verify_result["stdout"],
            "verify_stderr": verify_result["stderr"],
        }
        results.append(result)

        print("=" * 80)
        print(f"RUN {run_idx}")
        print("trace_batch_indices =", trace)
        print("num_steps =", num_steps)
        print("export_returncode =", export_result["returncode"])
        print("verify_returncode =", verify_result["returncode"])
        print("export_time_sec =", round(export_result["elapsed_sec"], 6))
        print(
            "verify_time_sec =",
            None if verify_result["elapsed_sec"] is None else round(verify_result["elapsed_sec"], 6),
        )
        print("verification_passed =", verification_passed)

        if export_result["returncode"] != 0:
            print("--- EXPORT STDOUT ---")
            print(export_result["stdout"])
            print("--- EXPORT STDERR ---")
            print(export_result["stderr"])

        if verify_result["returncode"] not in (None, 0):
            print("--- VERIFY STDOUT ---")
            print(verify_result["stdout"])
            print("--- VERIFY STDERR ---")
            print(verify_result["stderr"])

    with open(args.summary_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    with open(args.summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_idx",
                "trace_batch_indices",
                "num_steps",
                "artifact_path",
                "work_dir",
                "export_returncode",
                "verify_returncode",
                "export_time_sec",
                "verify_time_sec",
                "verification_passed",
                "initial_checkpoint_sha256",
                "final_checkpoint_sha256",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "run_idx": row["run_idx"],
                    "trace_batch_indices": json.dumps(row["trace_batch_indices"]),
                    "num_steps": row["num_steps"],
                    "artifact_path": row["artifact_path"],
                    "work_dir": row["work_dir"],
                    "export_returncode": row["export_returncode"],
                    "verify_returncode": row["verify_returncode"],
                    "export_time_sec": row["export_time_sec"],
                    "verify_time_sec": row["verify_time_sec"],
                    "verification_passed": row["verification_passed"],
                    "initial_checkpoint_sha256": row["initial_checkpoint_sha256"],
                    "final_checkpoint_sha256": row["final_checkpoint_sha256"],
                }
            )

    print("=" * 80)
    print("DONE")
    print("summary_json =", args.summary_json)
    print("summary_csv =", args.summary_csv)


if __name__ == "__main__":
    main()