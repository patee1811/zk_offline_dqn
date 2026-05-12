from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "data/cartpole_dqn_eps010_transitions.pkl"
DEFAULT_MERKLE = ROOT / "artifacts/cartpole_dqn_eps010_merkle.json"
DEFAULT_CHECKPOINT = ROOT / "models/offline_dqn_with_target_seed42_best.pt"
DEFAULT_OUT_DIR = ROOT / "artifacts/benchmarks/distinct_td_sp1"
EXPORTER = ROOT / "scripts/artifacts_export/export_minibatch_td_artifact_from_dataset.py"
PYTHON_VERIFIER = ROOT / "scripts/artifacts_export/verify_td_mvp_test_vector.py"
SP1_DIR = ROOT / "zk_backend/td_mvp/sp1"

sys.path.insert(0, str(ROOT))

from scripts.artifacts_export.export_td_mvp_batch_test_vector import (  # noqa: E402
    build_distinct_batch_vector,
)
from scripts.artifacts_export.export_td_mvp_test_vector import (  # noqa: E402
    build_td_mvp_test_vector,
)


def parse_batch_sizes(raw: str) -> List[int]:
    values = [int(item.strip()) for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("at least one batch size is required")
    if any(value <= 0 for value in values):
        raise ValueError(f"batch sizes must be positive, got {values}")
    return values


def parse_case_filter(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_command(
    command: List[str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    env_updates: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    if env_updates:
        env.update(env_updates)

    started = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed_sec = time.perf_counter() - started

    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")

    return {
        "command": " ".join(command),
        "cwd": str(cwd),
        "returncode": result.returncode,
        "elapsed_sec": round(elapsed_sec, 6),
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def parse_key_values(stdout: str) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for line in stdout.splitlines():
        if " = " not in line:
            continue
        key, raw_value = line.split(" = ", 1)
        raw_value = raw_value.strip()
        if raw_value in {"true", "True"}:
            parsed[key.strip()] = True
        elif raw_value in {"false", "False"}:
            parsed[key.strip()] = False
        else:
            try:
                parsed[key.strip()] = int(raw_value)
            except ValueError:
                try:
                    parsed[key.strip()] = float(raw_value)
                except ValueError:
                    parsed[key.strip()] = raw_value
    return parsed


def export_distinct_minibatch_artifact(
    *,
    data: Path,
    merkle: Path,
    checkpoint: Path,
    batch_size: int,
    start_index: int,
    stride: int,
    out_path: Path,
) -> Dict[str, Any]:
    result = run_command(
        [
            sys.executable,
            str(EXPORTER),
            "--data",
            str(data),
            "--merkle",
            str(merkle),
            "--checkpoint",
            str(checkpoint),
            "--batch-size",
            str(batch_size),
            "--start-index",
            str(start_index),
            "--stride",
            str(stride),
            "--out",
            str(out_path),
        ],
        cwd=ROOT,
        stdout_path=out_path.with_suffix(".export.stdout.txt"),
        stderr_path=out_path.with_suffix(".export.stderr.txt"),
    )
    if result["returncode"] != 0:
        raise RuntimeError(f"distinct minibatch export failed: {result['stderr']}")
    return load_json(out_path)


def build_td_vector(
    minibatch_artifact: Dict[str, Any],
    batch_size: int,
    source_path: Path,
) -> Dict[str, Any]:
    if batch_size == 1:
        return build_td_mvp_test_vector(
            artifact=minibatch_artifact,
            item_index=0,
            source_path=source_path,
        )
    return build_distinct_batch_vector(
        artifact=minibatch_artifact,
        batch_size=batch_size,
        input_path=source_path,
    )


def mutate_duplicate_index(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][1] = copy.deepcopy(tv["private"]["items"][0])
    tv["public"]["leaf_indices"] = [int(item["index"]) for item in tv["private"]["items"]]


def mutate_wrong_item_index(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["index"] += 1


def mutate_swapped_item_order(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0], tv["private"]["items"][1] = (
        tv["private"]["items"][1],
        tv["private"]["items"][0],
    )


def mutate_wrong_item_loss(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["td_witness"]["loss_fp"] += 1


def mutate_wrong_claimed_batch_average(tv: Dict[str, Any]) -> None:
    tv["public"]["claimed_batch_loss_fp"] += 1


def mutate_wrong_path_order(tv: Dict[str, Any]) -> None:
    tv["private"]["items"][0]["merkle_path"] = list(
        reversed(tv["private"]["items"][0]["merkle_path"])
    )


NEGATIVE_CASES = [
    ("tamper_duplicate_index", mutate_duplicate_index),
    ("tamper_wrong_item_index", mutate_wrong_item_index),
    ("tamper_swapped_item_order", mutate_swapped_item_order),
    ("tamper_wrong_item_loss", mutate_wrong_item_loss),
    ("tamper_wrong_claimed_batch_average", mutate_wrong_claimed_batch_average),
    ("tamper_wrong_path_order", mutate_wrong_path_order),
]


def run_python_case(case_name: str, artifact_path: Path, out_dir: Path) -> Dict[str, Any]:
    result = run_command(
        [sys.executable, str(PYTHON_VERIFIER), "--input", str(artifact_path)],
        cwd=ROOT,
        stdout_path=out_dir / "logs" / f"python_{case_name}.stdout.txt",
        stderr_path=out_dir / "logs" / f"python_{case_name}.stderr.txt",
    )
    parsed = parse_key_values(result["stdout"])
    return {
        "accepted": result["returncode"] == 0,
        "returncode": result["returncode"],
        "elapsed_sec": result["elapsed_sec"],
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "verification_passed": parsed.get("verification_passed"),
    }


def run_sp1_case(
    *,
    case_name: str,
    artifact_path: Path,
    out_dir: Path,
    cargo_bin: str,
    expected_accept: bool,
    prove: bool,
) -> Dict[str, Any]:
    args = [
        cargo_bin,
        "run",
        "--release",
        "-p",
        "td-mvp-host",
        "--",
        "--input",
        str(artifact_path.resolve()),
        "--case",
        "valid_control",
        "--execute",
    ]
    if not expected_accept:
        args.append("--skip-host-precheck")
    if prove and expected_accept:
        args.append("--prove")

    result = run_command(
        args,
        cwd=SP1_DIR,
        stdout_path=out_dir / "logs" / f"sp1_{case_name}.stdout.txt",
        stderr_path=out_dir / "logs" / f"sp1_{case_name}.stderr.txt",
    )
    parsed = parse_key_values(result["stdout"])
    return {
        "accepted": result["returncode"] == 0,
        "returncode": result["returncode"],
        "elapsed_sec": result["elapsed_sec"],
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "metrics": parsed,
    }


def evaluate_case(
    *,
    case_name: str,
    expected_accept: bool,
    artifact_path: Path,
    out_dir: Path,
    skip_sp1: bool,
    cargo_bin: str,
    prove: bool,
) -> Dict[str, Any]:
    python_result = run_python_case(case_name, artifact_path, out_dir)
    sp1_result = None
    if not skip_sp1:
        sp1_result = run_sp1_case(
            case_name=case_name,
            artifact_path=artifact_path,
            out_dir=out_dir,
            cargo_bin=cargo_bin,
            expected_accept=expected_accept,
            prove=prove,
        )

    python_expected_ok = python_result["accepted"] == expected_accept
    sp1_expected_ok = None if sp1_result is None else sp1_result["accepted"] == expected_accept
    python_sp1_agree = (
        None if sp1_result is None else python_result["accepted"] == sp1_result["accepted"]
    )
    passed = python_expected_ok if sp1_result is None else (
        python_expected_ok and bool(sp1_expected_ok) and bool(python_sp1_agree)
    )

    return {
        "case_name": case_name,
        "expected_accept": expected_accept,
        "fixture_path": artifact_path.relative_to(ROOT).as_posix(),
        "python": python_result,
        "sp1": sp1_result,
        "python_expected_ok": python_expected_ok,
        "sp1_expected_ok": sp1_expected_ok,
        "python_sp1_agree": python_sp1_agree,
        "passed": passed,
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# Distinct TD SP1 Benchmark Snapshot",
        "",
        f"Generated at UTC: `{summary['generated_at_utc']}`",
        "",
        "## Command",
        "",
        "```bash",
        "python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1",
        "python scripts/experiments/benchmark_distinct_td_sp1.py --prove",
        "```",
        "",
        "## Overall",
        "",
        f"- Dataset: `{summary['data_path']}`",
        f"- Merkle artifact: `{summary['merkle_path']}`",
        f"- Checkpoint: `{summary['checkpoint_path']}`",
        f"- Batch sizes: `{summary['batch_sizes']}`",
        f"- Python expected outcomes passed: `{summary['all_python_expected']}`",
        f"- SP1 expected outcomes passed: `{summary['all_sp1_expected']}`",
        f"- Python/SP1 agreement: `{summary['python_sp1_agreement']}`",
        "",
        "## Benchmark Matrix",
        "",
        "| Case | Relation | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count | Notes |",
        "|---|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in summary["benchmark_matrix"]:
        lines.append(
            "| "
            f"`{row['case']}` | "
            f"{row['relation']} | "
            f"`{row['batch_size']}` | "
            f"`{row['status']}` | "
            f"`{row['prove_time_sec']}` | "
            f"`{row['verify_time_sec']}` | "
            f"`{row['proof_size_bytes']}` | "
            f"`{row['cycle_count']}` | "
            f"{row['notes']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--merkle", type=Path, default=DEFAULT_MERKLE)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--batch-sizes", default="1,2,4,8")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--cargo-bin", default="cargo")
    parser.add_argument("--skip-sp1", action="store_true")
    parser.add_argument("--prove", action="store_true")
    parser.add_argument("--prove-cases", default="TD-1,TD-2,TD-4,TD-8")
    args = parser.parse_args()

    batch_sizes = parse_batch_sizes(args.batch_sizes)
    max_batch_size = max(batch_sizes)
    export_batch_size = max(max_batch_size, 2)
    prove_cases = parse_case_filter(args.prove_cases) if args.prove else set()
    out_dir = args.out_dir.resolve()
    fixtures_dir = out_dir / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== DISTINCT TD SP1 BENCHMARK ===")
    print("data_path =", args.data)
    print("merkle_path =", args.merkle)
    print("checkpoint_path =", args.checkpoint)
    print("out_dir =", out_dir)
    print("batch_sizes =", batch_sizes)
    print("skip_sp1 =", args.skip_sp1)
    print("prove =", args.prove)
    print()

    minibatch_path = fixtures_dir / f"distinct_minibatch_td_{export_batch_size}.json"
    minibatch_artifact = export_distinct_minibatch_artifact(
        data=args.data,
        merkle=args.merkle,
        checkpoint=args.checkpoint,
        batch_size=export_batch_size,
        start_index=args.start_index,
        stride=args.stride,
        out_path=minibatch_path,
    )

    results: List[Dict[str, Any]] = []

    for batch_size in batch_sizes:
        case_name = f"TD-{batch_size}"
        tv = build_td_vector(minibatch_artifact, batch_size, minibatch_path)
        fixture_path = fixtures_dir / f"td_distinct_batch_size_{batch_size}.json"
        write_json(fixture_path, tv)

        result = evaluate_case(
            case_name=case_name,
            expected_accept=True,
            artifact_path=fixture_path,
            out_dir=out_dir,
            skip_sp1=args.skip_sp1,
            cargo_bin=args.cargo_bin,
            prove=args.prove and case_name in prove_cases,
        )
        results.append(result)
        print(
            f"{case_name}: expected_accept=True "
            f"python_accept={result['python']['accepted']} "
            f"sp1_accept={None if result['sp1'] is None else result['sp1']['accepted']} "
            f"passed={result['passed']}"
        )

    negative_base = build_td_vector(minibatch_artifact, 2, minibatch_path)
    for case_name, mutator in NEGATIVE_CASES:
        tv = copy.deepcopy(negative_base)
        mutator(tv)
        fixture_path = fixtures_dir / f"{case_name}.json"
        write_json(fixture_path, tv)
        result = evaluate_case(
            case_name=case_name,
            expected_accept=False,
            artifact_path=fixture_path,
            out_dir=out_dir,
            skip_sp1=args.skip_sp1,
            cargo_bin=args.cargo_bin,
            prove=False,
        )
        results.append(result)
        print(
            f"{case_name}: expected_accept=False "
            f"python_accept={result['python']['accepted']} "
            f"sp1_accept={None if result['sp1'] is None else result['sp1']['accepted']} "
            f"passed={result['passed']}"
        )

    benchmark_matrix = []
    for result in results:
        is_valid = result["expected_accept"]
        metrics = (result.get("sp1") or {}).get("metrics") or {}
        batch_size = int(result["case_name"].split("-")[1]) if result["case_name"].startswith("TD-") else 2
        if args.skip_sp1:
            status = "python_only" if is_valid else "rejected_python_only"
        else:
            status = "completed" if result["passed"] and is_valid else "rejected" if result["passed"] else "failed"
        benchmark_matrix.append(
            {
                "case": result["case_name"],
                "relation": "td_batch_distinct_v1" if is_valid else "invalid distinct batch witness",
                "batch_size": batch_size,
                "status": status,
                "prove_time_sec": metrics.get("proving_time_sec"),
                "verify_time_sec": metrics.get("verification_time_sec"),
                "proof_size_bytes": metrics.get("proof_size_bytes"),
                "cycle_count": metrics.get("cycle_count"),
                "notes": (
                    "distinct committed replay minibatch"
                    if is_valid
                    else "negative test for duplicate/order/index/loss/average/path"
                ),
            }
        )

    all_python_expected = all(item["python_expected_ok"] for item in results)
    all_sp1_expected = None if args.skip_sp1 else all(item["sp1_expected_ok"] for item in results)
    python_sp1_agreement = None if args.skip_sp1 else all(item["python_sp1_agree"] for item in results)
    all_passed = all(item["passed"] for item in results)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_path": args.data.relative_to(ROOT).as_posix() if args.data.is_relative_to(ROOT) else str(args.data),
        "merkle_path": args.merkle.relative_to(ROOT).as_posix() if args.merkle.is_relative_to(ROOT) else str(args.merkle),
        "checkpoint_path": args.checkpoint.relative_to(ROOT).as_posix() if args.checkpoint.is_relative_to(ROOT) else str(args.checkpoint),
        "out_dir": out_dir.relative_to(ROOT).as_posix(),
        "batch_sizes": batch_sizes,
        "start_index": args.start_index,
        "stride": args.stride,
        "skip_sp1": args.skip_sp1,
        "prove": args.prove,
        "prove_cases": sorted(prove_cases),
        "minibatch_artifact_path": minibatch_path.relative_to(ROOT).as_posix(),
        "case_results": results,
        "benchmark_matrix": benchmark_matrix,
        "all_python_expected": all_python_expected,
        "all_sp1_expected": all_sp1_expected,
        "python_sp1_agreement": python_sp1_agreement,
        "all_passed": all_passed,
    }

    summary_json = out_dir / "summary.json"
    matrix_csv = out_dir / "benchmark_matrix.csv"
    summary_md = out_dir / "summary.md"
    write_json(summary_json, summary)
    write_csv(matrix_csv, benchmark_matrix)
    write_markdown(summary_md, summary)

    print()
    print("summary_json_path =", summary_json.relative_to(ROOT).as_posix())
    print("benchmark_matrix_csv_path =", matrix_csv.relative_to(ROOT).as_posix())
    print("summary_md_path =", summary_md.relative_to(ROOT).as_posix())
    print("all_python_expected =", all_python_expected)
    print("all_sp1_expected =", all_sp1_expected)
    print("python_sp1_agreement =", python_sp1_agreement)
    print("all_passed =", all_passed)

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
