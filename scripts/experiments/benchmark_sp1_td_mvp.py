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
from typing import Any, Callable, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "zk_backend/test_vectors/td_mvp_case_0.json"
DEFAULT_OUT_DIR = ROOT / "artifacts/benchmarks/sp1_td_mvp"
PYTHON_VERIFIER = ROOT / "scripts/artifacts_export/verify_td_mvp_test_vector.py"
SP1_DIR = ROOT / "zk_backend/td_mvp/sp1"

Mutator = Callable[[Dict[str, Any]], None]


def mutate_reward(tv: Dict[str, Any]) -> None:
    tv["private"]["transition"]["reward"] = float(tv["private"]["transition"]["reward"]) + 1.0


def mutate_done(tv: Dict[str, Any]) -> None:
    done = int(tv["private"]["transition"]["done"])
    tv["private"]["transition"]["done"] = 1 - done


def mutate_transition_obs(tv: Dict[str, Any]) -> None:
    tv["private"]["transition"]["obs"][0] = (
        float(tv["private"]["transition"]["obs"][0]) + 1.0
    )


def mutate_leaf_encoding(tv: Dict[str, Any]) -> None:
    tv["private"]["leaf"][0] += 1


def mutate_merkle_path(tv: Dict[str, Any]) -> None:
    tv["private"]["merkle_path"][0]["sibling_hash"] = "00" * 32


def mutate_q_target_max_fp(tv: Dict[str, Any]) -> None:
    tv["private"]["td_witness"]["q_target_max_fp"] += 1


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
    batch_loss_fp = total_loss_fp // batch_size
    public = single["public"]
    return {
        "schema_version": "td_mvp_batch_test_vector_v1",
        "source": {
            "single_test_vector_path": str(DEFAULT_INPUT.relative_to(ROOT)),
            "construction": "repeat canonical single-transition vector",
            "batch_size": batch_size,
        },
        "statement": {
            "name": "td_mvp_minibatch_membership_bellman_smoothl1_average",
            "description": (
                "Minibatch TD MVP vector for multiple membership checks, per-sample TD loss, "
                "and integer average batch loss."
            ),
        },
        "public": {
            "dataset_root": public["dataset_root"],
            "fp_scale": int(public["fp_scale"]),
            "gamma_fp": int(public["gamma_fp"]),
            "loss_type": public["loss_type"],
            "batch_size": batch_size,
            "claimed_batch_loss_fp": batch_loss_fp,
            "checkpoint_commitments": public.get("checkpoint_commitments"),
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


CASES: List[Dict[str, Any]] = [
    {"case_name": "valid_control", "expected_accept": True, "mutator": None},
    {"case_name": "tamper_reward", "expected_accept": False, "mutator": mutate_reward},
    {"case_name": "tamper_done", "expected_accept": False, "mutator": mutate_done},
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
        "case_name": "tamper_q_target_max_fp",
        "expected_accept": False,
        "mutator": mutate_q_target_max_fp,
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
    {"case_name": "tamper_leaf_hash", "expected_accept": False, "mutator": mutate_leaf_hash},
    {
        "case_name": "tamper_td_error_fp",
        "expected_accept": False,
        "mutator": mutate_td_error_fp,
    },
]

BATCH_NEGATIVE_CASES: List[Dict[str, Any]] = [
    {
        "case_name": "tamper_batch_claimed_loss_fp",
        "expected_accept": False,
        "mutator": mutate_batch_claimed_loss_fp,
    },
    {
        "case_name": "tamper_batch_size",
        "expected_accept": False,
        "mutator": mutate_batch_size,
    },
    {
        "case_name": "tamper_batch_item_loss_fp",
        "expected_accept": False,
        "mutator": mutate_batch_item_loss_fp,
    },
    {
        "case_name": "tamper_batch_item_index",
        "expected_accept": False,
        "mutator": mutate_batch_item_index,
    },
]


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
        "cwd": str(cwd),
        "returncode": result.returncode,
        "elapsed_sec": round(elapsed_sec, 6),
        "stdout_path": str(stdout_path.relative_to(ROOT)),
        "stderr_path": str(stderr_path.relative_to(ROOT)),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def parse_key_values(stdout: str) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for line in stdout.splitlines():
        if " = " not in line:
            continue
        key, raw_value = line.split(" = ", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value in {"true", "True"}:
            parsed[key] = True
        elif raw_value in {"false", "False"}:
            parsed[key] = False
        else:
            try:
                parsed[key] = int(raw_value)
            except ValueError:
                try:
                    parsed[key] = float(raw_value)
                except ValueError:
                    parsed[key] = raw_value
    return parsed


def parse_case_filter(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def run_python_case(case_name: str, artifact_path: Path, out_dir: Path) -> Dict[str, Any]:
    stdout_path = out_dir / "logs" / f"python_{case_name}.stdout.txt"
    stderr_path = out_dir / "logs" / f"python_{case_name}.stderr.txt"
    result = run_command(
        [sys.executable, str(PYTHON_VERIFIER), "--input", str(artifact_path)],
        cwd=ROOT,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
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

    stdout_path = out_dir / "logs" / f"sp1_{case_name}.stdout.txt"
    stderr_path = out_dir / "logs" / f"sp1_{case_name}.stderr.txt"
    result = run_command(args, cwd=SP1_DIR, stdout_path=stdout_path, stderr_path=stderr_path)
    parsed = parse_key_values(result["stdout"])
    return {
        "accepted": result["returncode"] == 0,
        "returncode": result["returncode"],
        "elapsed_sec": result["elapsed_sec"],
        "stdout_path": result["stdout_path"],
        "stderr_path": result["stderr_path"],
        "metrics": parsed,
    }


def build_matrix_rows(
    case_results: List[Dict[str, Any]],
    batch_results: List[Dict[str, Any]],
    prove_cases: set[str],
    skip_sp1: bool,
) -> List[Dict[str, Any]]:
    valid = next(item for item in case_results if item["case_name"] == "valid_control")
    sp1_metrics = (valid.get("sp1") or {}).get("metrics") or {}
    td_1_status = "not_run" if skip_sp1 else "completed"
    if not valid.get("sp1_expected_ok"):
        td_1_status = "failed"
    if skip_sp1:
        td_1_status = "python_only"

    rows: List[Dict[str, Any]] = [
        {
            "case": "TD-1",
            "relation": "Merkle + TD + SmoothL1",
            "batch_size": 1,
            "status": td_1_status,
            "prove_time_sec": sp1_metrics.get("proving_time_sec") if "TD-1" in prove_cases else None,
            "verify_time_sec": sp1_metrics.get("verification_time_sec") if "TD-1" in prove_cases else None,
            "proof_size_bytes": sp1_metrics.get("proof_size_bytes") if "TD-1" in prove_cases else None,
            "cycle_count": sp1_metrics.get("cycle_count"),
            "notes": "single-transition SP1 relation",
        }
    ]

    for batch_size in [2, 4, 8]:
        label = f"TD-{batch_size}"
        result = next(item for item in batch_results if item["case_name"] == label)
        metrics = (result.get("sp1") or {}).get("metrics") or {}
        if skip_sp1:
            status = "python_only"
        elif result["passed"]:
            status = "completed"
        else:
            status = "failed"
        rows.append(
            {
                "case": label,
                "relation": "Merkle + TD + SmoothL1 + average loss",
                "batch_size": batch_size,
                "status": status,
                "prove_time_sec": metrics.get("proving_time_sec") if label in prove_cases else None,
                "verify_time_sec": metrics.get("verification_time_sec") if label in prove_cases else None,
                "proof_size_bytes": metrics.get("proof_size_bytes") if label in prove_cases else None,
                "cycle_count": metrics.get("cycle_count"),
                "notes": "SP1 minibatch relation over repeated canonical TD item",
            }
        )

    tamper_map = {
        "tamper_reward": "Tamper-reward",
        "tamper_merkle_path": "Tamper-path",
        "tamper_claimed_loss_fp": "Tamper-loss",
    }
    for case_name, label in tamper_map.items():
        item = next(result for result in case_results if result["case_name"] == case_name)
        if skip_sp1:
            notes = "SP1 skipped; Python verifier rejected as expected"
        elif item["python_sp1_agree"]:
            notes = "Python verifier and SP1 execution agree"
        else:
            notes = "Python verifier and SP1 execution disagree"
        rows.append(
            {
                "case": label,
                "relation": "invalid witness",
                "batch_size": 1,
                "status": "rejected" if item["passed"] else "failed",
                "prove_time_sec": None,
                "verify_time_sec": None,
                "proof_size_bytes": None,
                "cycle_count": None,
                "notes": notes,
            }
        )

    batch_tamper_map = {
        "tamper_batch_claimed_loss_fp": "Tamper-batch-loss",
        "tamper_batch_size": "Tamper-batch-size",
        "tamper_batch_item_loss_fp": "Tamper-batch-item-loss",
        "tamper_batch_item_index": "Tamper-batch-index",
    }
    for case_name, label in batch_tamper_map.items():
        item = next(result for result in batch_results if result["case_name"] == case_name)
        if skip_sp1:
            notes = "SP1 skipped; Python verifier rejected as expected"
        elif item["python_sp1_agree"]:
            notes = "Python verifier and SP1 execution agree"
        else:
            notes = "Python verifier and SP1 execution disagree"
        rows.append(
            {
                "case": label,
                "relation": "invalid batch witness",
                "batch_size": 2,
                "status": "rejected" if item["passed"] else "failed",
                "prove_time_sec": None,
                "verify_time_sec": None,
                "proof_size_bytes": None,
                "cycle_count": None,
                "notes": notes,
            }
        )

    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, summary: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# SP1 TD MVP Benchmark Snapshot")
    lines.append("")
    lines.append(f"Generated at UTC: `{summary['generated_at_utc']}`")
    lines.append("")
    lines.append("## Commands")
    lines.append("")
    lines.append("```bash")
    lines.append("python scripts/experiments/benchmark_sp1_td_mvp.py --prove")
    lines.append("```")
    lines.append("")
    lines.append("Python-only smoke command:")
    lines.append("")
    lines.append("```bash")
    lines.append("python scripts/experiments/benchmark_sp1_td_mvp.py --skip-sp1")
    lines.append("```")
    lines.append("")
    lines.append("## Overall")
    lines.append("")
    lines.append(f"- Input vector: `{summary['input_path']}`")
    lines.append(f"- Prove requested: `{summary['prove_valid']}`")
    lines.append(f"- Prove cases: `{summary['prove_cases']}`")
    lines.append(f"- Python expected outcomes passed: `{summary['all_python_expected']}`")
    lines.append(f"- SP1 expected outcomes passed: `{summary['all_sp1_expected']}`")
    lines.append(f"- Python/SP1 agreement: `{summary['python_sp1_agreement']}`")
    lines.append("")
    lines.append("## Benchmark Matrix")
    lines.append("")
    lines.append(
        "| Case | Relation | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count | Notes |"
    )
    lines.append("|---|---|---:|---|---:|---:|---:|---:|---|")
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
    lines.append("")
    lines.append("## Agreement Cases")
    lines.append("")
    lines.append("| Case | Expected accept | Python accept | SP1 accept | Passed |")
    lines.append("|---|---:|---:|---:|---:|")
    for case in summary["case_results"] + summary["batch_results"]:
        lines.append(
            "| "
            f"`{case['case_name']}` | "
            f"`{case['expected_accept']}` | "
            f"`{case['python']['accepted']}` | "
            f"`{None if case['sp1'] is None else case['sp1']['accepted']}` | "
            f"`{case['passed']}` |"
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--cargo-bin", default="cargo")
    parser.add_argument("--prove", action="store_true", help="Generate and verify the valid proof.")
    parser.add_argument(
        "--prove-cases",
        default="TD-1,TD-2,TD-4,TD-8",
        help=(
            "Comma-separated accepted cases to prove when --prove is set. "
            "Use this to avoid proving TD-1/2/4/8 in one WSL run."
        ),
    )
    parser.add_argument(
        "--skip-sp1",
        action="store_true",
        help="Only run Python semantic checks; useful on machines without SP1.",
    )
    args = parser.parse_args()
    prove_cases = parse_case_filter(args.prove_cases) if args.prove else set()

    out_dir = args.out_dir.resolve()
    vectors_dir = out_dir / "fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)

    base = load_json(args.input)
    case_results: List[Dict[str, Any]] = []
    batch_results: List[Dict[str, Any]] = []

    print("=== SP1 TD MVP BENCHMARK ===")
    print(f"input_path = {args.input}")
    print(f"out_dir = {out_dir}")
    print(f"prove_valid = {args.prove}")
    print(f"prove_cases = {','.join(sorted(prove_cases)) if prove_cases else None}")
    print(f"skip_sp1 = {args.skip_sp1}")
    print()

    for case in CASES:
        case_name = case["case_name"]
        expected_accept = bool(case["expected_accept"])
        tv = copy.deepcopy(base)
        mutator: Optional[Mutator] = case["mutator"]
        if mutator is not None:
            mutator(tv)

        artifact_path = vectors_dir / f"{case_name}.json"
        write_json(artifact_path, tv)

        python_result = run_python_case(case_name, artifact_path, out_dir)
        sp1_result = None
        if not args.skip_sp1:
            sp1_result = run_sp1_case(
                case_name=case_name,
                artifact_path=artifact_path,
                out_dir=out_dir,
                cargo_bin=args.cargo_bin,
                expected_accept=expected_accept,
                prove=args.prove and case_name == "valid_control" and "TD-1" in prove_cases,
            )

        python_expected_ok = python_result["accepted"] == expected_accept
        sp1_expected_ok = None if sp1_result is None else sp1_result["accepted"] == expected_accept
        python_sp1_agree = (
            None if sp1_result is None else python_result["accepted"] == sp1_result["accepted"]
        )
        passed = python_expected_ok if sp1_result is None else (
            python_expected_ok and bool(sp1_expected_ok) and bool(python_sp1_agree)
        )

        case_results.append(
            {
                "case_name": case_name,
                "expected_accept": expected_accept,
                "fixture_path": str(artifact_path.relative_to(ROOT)),
                "python": python_result,
                "sp1": sp1_result,
                "python_expected_ok": python_expected_ok,
                "sp1_expected_ok": sp1_expected_ok,
                "python_sp1_agree": python_sp1_agree,
                "passed": passed,
            }
        )

        print(
            f"{case_name}: expected_accept={expected_accept} "
            f"python_accept={python_result['accepted']} "
            f"sp1_accept={None if sp1_result is None else sp1_result['accepted']} "
            f"passed={passed}"
        )

    for batch_size in [2, 4, 8]:
        case_name = f"TD-{batch_size}"
        tv = build_batch_vector(base, batch_size)
        artifact_path = vectors_dir / f"td_mvp_batch_size_{batch_size}.json"
        write_json(artifact_path, tv)

        python_result = run_python_case(case_name, artifact_path, out_dir)
        sp1_result = None
        if not args.skip_sp1:
            sp1_result = run_sp1_case(
                case_name=case_name,
                artifact_path=artifact_path,
                out_dir=out_dir,
                cargo_bin=args.cargo_bin,
                expected_accept=True,
                prove=args.prove and case_name in prove_cases,
            )

        python_expected_ok = python_result["accepted"]
        sp1_expected_ok = None if sp1_result is None else sp1_result["accepted"]
        python_sp1_agree = (
            None if sp1_result is None else python_result["accepted"] == sp1_result["accepted"]
        )
        passed = python_expected_ok if sp1_result is None else (
            python_expected_ok and bool(sp1_expected_ok) and bool(python_sp1_agree)
        )
        batch_results.append(
            {
                "case_name": case_name,
                "expected_accept": True,
                "fixture_path": str(artifact_path.relative_to(ROOT)),
                "python": python_result,
                "sp1": sp1_result,
                "python_expected_ok": python_expected_ok,
                "sp1_expected_ok": sp1_expected_ok,
                "python_sp1_agree": python_sp1_agree,
                "passed": passed,
            }
        )
        print(
            f"{case_name}: expected_accept=True "
            f"python_accept={python_result['accepted']} "
            f"sp1_accept={None if sp1_result is None else sp1_result['accepted']} "
            f"passed={passed}"
        )

    batch_base = build_batch_vector(base, 2)
    for case in BATCH_NEGATIVE_CASES:
        case_name = case["case_name"]
        expected_accept = bool(case["expected_accept"])
        tv = copy.deepcopy(batch_base)
        mutator: Mutator = case["mutator"]
        mutator(tv)

        artifact_path = vectors_dir / f"{case_name}.json"
        write_json(artifact_path, tv)

        python_result = run_python_case(case_name, artifact_path, out_dir)
        sp1_result = None
        if not args.skip_sp1:
            sp1_result = run_sp1_case(
                case_name=case_name,
                artifact_path=artifact_path,
                out_dir=out_dir,
                cargo_bin=args.cargo_bin,
                expected_accept=expected_accept,
                prove=False,
            )

        python_expected_ok = python_result["accepted"] == expected_accept
        sp1_expected_ok = None if sp1_result is None else sp1_result["accepted"] == expected_accept
        python_sp1_agree = (
            None if sp1_result is None else python_result["accepted"] == sp1_result["accepted"]
        )
        passed = python_expected_ok if sp1_result is None else (
            python_expected_ok and bool(sp1_expected_ok) and bool(python_sp1_agree)
        )
        batch_results.append(
            {
                "case_name": case_name,
                "expected_accept": expected_accept,
                "fixture_path": str(artifact_path.relative_to(ROOT)),
                "python": python_result,
                "sp1": sp1_result,
                "python_expected_ok": python_expected_ok,
                "sp1_expected_ok": sp1_expected_ok,
                "python_sp1_agree": python_sp1_agree,
                "passed": passed,
            }
        )
        print(
            f"{case_name}: expected_accept={expected_accept} "
            f"python_accept={python_result['accepted']} "
            f"sp1_accept={None if sp1_result is None else sp1_result['accepted']} "
            f"passed={passed}"
        )

    benchmark_matrix = build_matrix_rows(
        case_results=case_results,
        batch_results=batch_results,
        prove_cases=prove_cases,
        skip_sp1=args.skip_sp1,
    )
    all_results = case_results + batch_results
    all_python_expected = all(item["python_expected_ok"] for item in all_results)
    all_sp1_expected = (
        None if args.skip_sp1 else all(item["sp1_expected_ok"] for item in all_results)
    )
    python_sp1_agreement = (
        None if args.skip_sp1 else all(item["python_sp1_agree"] for item in all_results)
    )
    all_passed = all(item["passed"] for item in all_results)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": str(args.input),
        "out_dir": str(out_dir.relative_to(ROOT)),
        "prove_valid": args.prove,
        "prove_cases": sorted(prove_cases),
        "skip_sp1": args.skip_sp1,
        "python_verifier": str(PYTHON_VERIFIER.relative_to(ROOT)),
        "sp1_workspace": str(SP1_DIR.relative_to(ROOT)),
        "case_results": case_results,
        "batch_results": batch_results,
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
