from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json"
DEFAULT_OUT_DIR = ROOT / "artifacts/benchmarks/one_step_sgd_tiny_sp1"
EXPORTER = ROOT / "scripts/artifacts_export/export_one_step_sgd_tiny_test_vector.py"
PYTHON_VERIFIER = ROOT / "scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py"
SP1_DIR = ROOT / "zk_backend/td_mvp/sp1"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_command(
    command: List[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
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
        "returncode": result.returncode,
        "elapsed_sec": round(elapsed_sec, 6),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
    }


def parse_key_values(stdout: str) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for line in stdout.splitlines():
        if " = " not in line:
            continue
        key, raw = line.split(" = ", 1)
        raw = raw.strip()
        if raw in {"true", "True"}:
            parsed[key.strip()] = True
        elif raw in {"false", "False"}:
            parsed[key.strip()] = False
        else:
            try:
                parsed[key.strip()] = int(raw)
            except ValueError:
                try:
                    parsed[key.strip()] = float(raw)
                except ValueError:
                    parsed[key.strip()] = raw
    return parsed


def export_fixture(source: Path, out_path: Path, layer_sizes: str, learning_rate_fp: int) -> Dict[str, Any]:
    result = run_command(
        [
            sys.executable,
            str(EXPORTER),
            "--input",
            str(source),
            "--out",
            str(out_path),
            "--layer-sizes",
            layer_sizes,
            "--learning-rate-fp",
            str(learning_rate_fp),
        ],
        cwd=ROOT,
        stdout_path=out_path.with_suffix(".export.stdout.txt"),
        stderr_path=out_path.with_suffix(".export.stderr.txt"),
    )
    if result["returncode"] != 0:
        raise RuntimeError(f"one-step SGD tiny export failed: {result['stderr']}")
    return load_json(out_path)


def run_python_case(case_name: str, fixture_path: Path, out_dir: Path) -> Dict[str, Any]:
    result = run_command(
        [sys.executable, str(PYTHON_VERIFIER), "--input", str(fixture_path)],
        cwd=ROOT,
        stdout_path=out_dir / "logs" / f"python_{case_name}.stdout.txt",
        stderr_path=out_dir / "logs" / f"python_{case_name}.stderr.txt",
    )
    return {
        "accepted": result["returncode"] == 0,
        "returncode": result["returncode"],
        "elapsed_sec": result["elapsed_sec"],
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "metrics": parse_key_values(result["stdout"]),
    }


def run_sp1_case(
    *,
    case_name: str,
    fixture_path: Path,
    out_dir: Path,
    cargo_bin: str,
    expected_accept: bool,
    prove: bool,
) -> Dict[str, Any]:
    command = [
        cargo_bin,
        "run",
        "--release",
        "-p",
        "td-mvp-host",
        "--",
        "--input",
        str(fixture_path.resolve()),
        "--case",
        "valid_control",
        "--execute",
    ]
    if not expected_accept:
        command.append("--skip-host-precheck")
    if prove and expected_accept:
        command.append("--prove")
    result = run_command(
        command,
        cwd=SP1_DIR,
        stdout_path=out_dir / "logs" / f"sp1_{case_name}.stdout.txt",
        stderr_path=out_dir / "logs" / f"sp1_{case_name}.stderr.txt",
    )
    return {
        "accepted": result["returncode"] == 0,
        "returncode": result["returncode"],
        "elapsed_sec": result["elapsed_sec"],
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "metrics": parse_key_values(result["stdout"]),
    }


def mutate_gradient_tensor(tv: Dict[str, Any]) -> None:
    tv["private"]["update_witness"]["gradient_tensors"]["layers"][0]["weight"][0][0] += 1


def mutate_delta_tensor(tv: Dict[str, Any]) -> None:
    tv["private"]["update_witness"]["delta_tensors"]["layers"][0]["weight"][0][0] += 1


def mutate_learning_rate(tv: Dict[str, Any]) -> None:
    tv["public"]["learning_rate_fp"] += 1


def mutate_post_model_weight(tv: Dict[str, Any]) -> None:
    tv["private"]["post_online_model"]["layers"][0]["weight"][0][0] += 1


def mutate_post_model_commitment(tv: Dict[str, Any]) -> None:
    tv["public"]["post_model_commitment"] = "00" * 32


def mutate_smooth_l1_grad(tv: Dict[str, Any]) -> None:
    tv["private"]["update_witness"]["smooth_l1_grad_fp"] += 1


NEGATIVE_CASES: List[tuple[str, Callable[[Dict[str, Any]], None]]] = [
    ("tamper_gradient_tensor", mutate_gradient_tensor),
    ("tamper_delta_tensor", mutate_delta_tensor),
    ("tamper_learning_rate_fp", mutate_learning_rate),
    ("tamper_post_model_weight", mutate_post_model_weight),
    ("tamper_post_model_commitment", mutate_post_model_commitment),
    ("tamper_smooth_l1_grad", mutate_smooth_l1_grad),
]


def evaluate_case(
    *,
    case_name: str,
    expected_accept: bool,
    fixture_path: Path,
    out_dir: Path,
    skip_sp1: bool,
    cargo_bin: str,
    prove: bool,
) -> Dict[str, Any]:
    python_result = run_python_case(case_name, fixture_path, out_dir)
    sp1_result: Optional[Dict[str, Any]] = None
    if not skip_sp1:
        sp1_result = run_sp1_case(
            case_name=case_name,
            fixture_path=fixture_path,
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
        "fixture_path": fixture_path.relative_to(ROOT).as_posix(),
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
        "# One-Step SGD Tiny SP1 Benchmark Snapshot",
        "",
        "## Commands",
        "",
        "```bash",
        "python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1",
        "python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove",
        "```",
        "",
        "## Overall",
        "",
        f"- Relation: `one_step_sgd_tiny_v1`",
        f"- Network spec: `{summary['layer_sizes']}`",
        f"- Learning rate fp: `{summary['learning_rate_fp']}`",
        f"- Python expected outcomes passed: `{summary['all_python_expected']}`",
        f"- SP1 expected outcomes passed: `{summary['all_sp1_expected']}`",
        f"- Python/SP1 agreement: `{summary['python_sp1_agreement']}`",
        "",
        "## Matrix",
        "",
        "| Case | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in summary["benchmark_matrix"]:
        lines.append(
            f"| `{row['case']}` | `{row['status']}` | `{row['prove_time_sec']}` | "
            f"`{row['verify_time_sec']}` | `{row['proof_size_bytes']}` | "
            f"`{row['cycle_count']}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--layer-sizes", default="4,8,2")
    parser.add_argument("--learning-rate-fp", type=int, default=100)
    parser.add_argument("--cargo-bin", default="cargo")
    parser.add_argument("--skip-sp1", action="store_true")
    parser.add_argument("--prove", action="store_true")
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    fixtures_dir = out_dir / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=== ONE STEP SGD TINY SP1 BENCHMARK ===")
    print("input_path =", args.input)
    print("out_dir =", out_dir)
    print("layer_sizes =", args.layer_sizes)
    print("learning_rate_fp =", args.learning_rate_fp)
    print("skip_sp1 =", args.skip_sp1)
    print("prove =", args.prove)
    print()

    valid_path = fixtures_dir / "one_step_sgd_tiny_valid.json"
    valid_fixture = export_fixture(args.input, valid_path, args.layer_sizes, args.learning_rate_fp)
    results = [
        evaluate_case(
            case_name="one-step-SGD-tiny-1",
            expected_accept=True,
            fixture_path=valid_path,
            out_dir=out_dir,
            skip_sp1=args.skip_sp1,
            cargo_bin=args.cargo_bin,
            prove=args.prove,
        )
    ]
    print(
        "one-step-SGD-tiny-1: "
        f"python_accept={results[0]['python']['accepted']} "
        f"sp1_accept={None if results[0]['sp1'] is None else results[0]['sp1']['accepted']} "
        f"passed={results[0]['passed']}"
    )

    for case_name, mutator in NEGATIVE_CASES:
        tv = copy.deepcopy(valid_fixture)
        mutator(tv)
        fixture_path = fixtures_dir / f"{case_name}.json"
        write_json(fixture_path, tv)
        result = evaluate_case(
            case_name=case_name,
            expected_accept=False,
            fixture_path=fixture_path,
            out_dir=out_dir,
            skip_sp1=args.skip_sp1,
            cargo_bin=args.cargo_bin,
            prove=False,
        )
        results.append(result)
        print(
            f"{case_name}: python_accept={result['python']['accepted']} "
            f"sp1_accept={None if result['sp1'] is None else result['sp1']['accepted']} "
            f"passed={result['passed']}"
        )

    benchmark_matrix = []
    for result in results:
        metrics = (result.get("sp1") or {}).get("metrics") or {}
        status = "python_only" if args.skip_sp1 else (
            "accepted" if result["expected_accept"] and result["passed"] else
            "rejected" if (not result["expected_accept"] and result["passed"]) else
            "failed"
        )
        benchmark_matrix.append(
            {
                "case": result["case_name"],
                "status": status,
                "prove_time_sec": metrics.get("proving_time_sec"),
                "verify_time_sec": metrics.get("verification_time_sec"),
                "proof_size_bytes": metrics.get("proof_size_bytes"),
                "cycle_count": metrics.get("cycle_count"),
            }
        )

    all_python_expected = all(item["python_expected_ok"] for item in results)
    all_sp1_expected = None if args.skip_sp1 else all(item["sp1_expected_ok"] for item in results)
    python_sp1_agreement = None if args.skip_sp1 else all(item["python_sp1_agree"] for item in results)
    all_passed = all(item["passed"] for item in results)
    summary = {
        "input_path": args.input.relative_to(ROOT).as_posix() if args.input.is_relative_to(ROOT) else str(args.input),
        "out_dir": out_dir.relative_to(ROOT).as_posix(),
        "layer_sizes": args.layer_sizes,
        "learning_rate_fp": args.learning_rate_fp,
        "skip_sp1": args.skip_sp1,
        "prove": args.prove,
        "case_results": results,
        "benchmark_matrix": benchmark_matrix,
        "all_python_expected": all_python_expected,
        "all_sp1_expected": all_sp1_expected,
        "python_sp1_agreement": python_sp1_agreement,
        "all_passed": all_passed,
    }

    write_json(out_dir / "summary.json", summary)
    write_csv(out_dir / "benchmark_matrix.csv", benchmark_matrix)
    write_markdown(out_dir / "summary.md", summary)
    print()
    print("summary_json_path =", (out_dir / "summary.json").relative_to(ROOT).as_posix())
    print("benchmark_matrix_csv_path =", (out_dir / "benchmark_matrix.csv").relative_to(ROOT).as_posix())
    print("summary_md_path =", (out_dir / "summary.md").relative_to(ROOT).as_posix())
    print("all_python_expected =", all_python_expected)
    print("all_sp1_expected =", all_sp1_expected)
    print("python_sp1_agreement =", python_sp1_agreement)
    print("all_passed =", all_passed)
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
