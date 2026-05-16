from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "artifacts/benchmarks/final_ndss"


COMPONENTS = [
    {
        "component_id": "distinct_td",
        "relation_id": "td_batch_distinct_v1",
        "environment": "CartPole-v1",
        "network_spec": "witness_q_values",
        "summary_path": ROOT / "artifacts/benchmarks/final_ndss/source_summaries/distinct_td_sp1/summary.json",
        "command": "python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove",
        "smoke_command": "python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke",
    },
    {
        "component_id": "forward_td_cartpole",
        "relation_id": "forward_td_mlp_v1",
        "environment": "CartPole-v1",
        "network_spec_key": "layer_sizes",
        "summary_path": ROOT / "artifacts/benchmarks/final_ndss/source_summaries/forward_td_mlp_sp1/summary.json",
        "command": "python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove",
        "smoke_command": "python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke",
    },
    {
        "component_id": "forward_td_mountaincar",
        "relation_id": "forward_td_mlp_v1",
        "environment": "MountainCar-v0",
        "network_spec_key": "layer_sizes",
        "summary_path": ROOT / "artifacts/benchmarks/final_ndss/source_summaries/second_env_mountaincar/summary.json",
        "command": "python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove",
        "smoke_command": "python scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/second_env_mountaincar_python_smoke",
    },
    {
        "component_id": "one_step_sgd_tiny",
        "relation_id": "one_step_sgd_tiny_v1",
        "environment": "CartPole-v1",
        "network_spec_key": "layer_sizes",
        "summary_path": ROOT / "artifacts/benchmarks/final_ndss/source_summaries/one_step_sgd_tiny_sp1/summary.json",
        "command": "python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove",
        "smoke_command": "python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke",
    },
]


TAMPER_CATEGORIES = {
    "duplicate_index": "batch",
    "wrong_item_index": "batch",
    "swapped_item_order": "batch",
    "wrong_item_loss": "arithmetic",
    "wrong_claimed_batch_average": "batch",
    "wrong_path_order": "commitment",
    "online_model_weight": "model",
    "target_model_weight": "model",
    "activation": "forward",
    "relu_mask": "forward",
    "argmax": "forward",
    "selected_target_value": "forward",
    "claimed_batch_loss": "arithmetic",
    "gradient_tensor": "update",
    "delta_tensor": "update",
    "learning_rate": "update",
    "post_model_weight": "update",
    "post_model_commitment": "update",
    "smooth_l1_grad": "update",
}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def get_case_batch_size(case: Dict[str, Any], matrix_row: Optional[Dict[str, Any]]) -> int:
    if matrix_row and matrix_row.get("batch_size") is not None:
        return int(matrix_row["batch_size"])
    metrics = ((case.get("sp1") or {}).get("metrics") or {})
    if metrics.get("batch_size") is not None:
        return int(metrics["batch_size"])
    name = str(case.get("case_name", ""))
    for token in reversed(name.replace("_", "-").split("-")):
        if token.isdigit():
            return int(token)
    return 1


def fixture_merkle_depth(case: Dict[str, Any]) -> Optional[int]:
    raw = case.get("fixture_path")
    if not raw:
        return None
    path = ROOT / raw
    if not path.exists():
        return None
    try:
        fixture = load_json(path)
    except (OSError, json.JSONDecodeError):
        return None

    private = fixture.get("private") or {}
    items = private.get("items") or fixture.get("items") or []
    if items:
        path_value = items[0].get("merkle_path")
        return len(path_value) if isinstance(path_value, list) else None
    path_value = private.get("merkle_path") or fixture.get("merkle_path")
    return len(path_value) if isinstance(path_value, list) else None


def category_for(case_name: str) -> str:
    stripped = case_name.removeprefix("tamper_")
    for token, category in TAMPER_CATEGORIES.items():
        if token in stripped:
            return category
    return "relation"


def outcome(result: Optional[Dict[str, Any]]) -> str:
    if result is None:
        return "not_run"
    return "accepted" if result.get("accepted") else "rejected"


def platform_for(case: Dict[str, Any], summary: Dict[str, Any]) -> str:
    sp1 = case.get("sp1")
    if sp1:
        metrics = sp1.get("metrics") or {}
        input_path = str(metrics.get("input_path", ""))
        if input_path.startswith("/kaggle/"):
            return "Kaggle Linux SP1"
        return "SP1 host platform"
    if summary.get("skip_sp1"):
        return "Python smoke path"
    return "unknown"


def matrix_lookup(summary: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("case")): row for row in summary.get("benchmark_matrix", [])}


def count_cases(cases: Iterable[Dict[str, Any]], expected_accept: bool) -> int:
    return sum(1 for case in cases if bool(case.get("expected_accept")) == expected_accept)


def build_rows(component: Dict[str, Any], summary: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    case_results = list(summary.get("case_results", []))
    accepted_count = count_cases(case_results, True)
    rejected_count = count_cases(case_results, False)
    lookup = matrix_lookup(summary)
    network_spec = component.get("network_spec") or summary.get(component.get("network_spec_key", "")) or "unspecified"
    benchmark_rows: List[Dict[str, Any]] = []
    tamper_rows: List[Dict[str, Any]] = []

    for case in case_results:
        case_name = str(case.get("case_name"))
        matrix_row = lookup.get(case_name)
        sp1 = case.get("sp1") or {}
        metrics = sp1.get("metrics") or {}
        batch_size = get_case_batch_size(case, matrix_row)
        depth = fixture_merkle_depth(case)
        backend = "SP1 proof" if metrics.get("proof_generated") else "SP1 execute" if sp1 else "Python oracle"
        status = "accepted" if case.get("expected_accept") and case.get("passed") else (
            "rejected" if (not case.get("expected_accept") and case.get("passed")) else "failed"
        )
        common = {
            "relation_id": component["relation_id"],
            "environment": component["environment"],
            "network_spec": str(network_spec),
            "batch_size": batch_size,
            "merkle_depth": depth,
            "accepted_fixtures": accepted_count,
            "rejected_tamper_fixtures": rejected_count,
            "prove_time_sec": metrics.get("proving_time_sec"),
            "verify_time_sec": metrics.get("verification_time_sec"),
            "proof_size_bytes": metrics.get("proof_size_bytes"),
            "cycle_count": metrics.get("cycle_count") or (matrix_row or {}).get("cycle_count"),
            "platform": platform_for(case, summary),
            "command": component["command"],
            "source_summary": rel(component["summary_path"]),
            "source_case": case_name,
            "fixture_path": case.get("fixture_path"),
            "backend": backend,
            "status": status,
        }
        benchmark_rows.append(common)
        if not case.get("expected_accept"):
            tamper_rows.append(
                {
                    "relation_id": component["relation_id"],
                    "environment": component["environment"],
                    "network_spec": str(network_spec),
                    "case": case_name,
                    "category": category_for(case_name),
                    "expected_outcome": "reject",
                    "python_outcome": outcome(case.get("python")),
                    "sp1_outcome": outcome(case.get("sp1")),
                    "passed": bool(case.get("passed")),
                    "fixture_path": case.get("fixture_path"),
                    "source_summary": rel(component["summary_path"]),
                }
            )
    return benchmark_rows, tamper_rows


def write_summary_md(path: Path, summary: Dict[str, Any], benchmark_rows: List[Dict[str, Any]]) -> None:
    proved_rows = [row for row in benchmark_rows if row["backend"] == "SP1 proof" and row["status"] == "accepted"]
    lines = [
        "# Achieved Relation Benchmark Artifact",
        "",
        "## Status",
        "",
        f"- Components loaded: `{len(summary['components'])}`",
        f"- Benchmark rows: `{len(benchmark_rows)}`",
        f"- Tamper rows: `{summary['tamper_rows']}`",
        f"- All loaded components passed expected outcomes: `{summary['all_components_passed']}`",
        "",
        "## Accepted SP1 Proof Rows",
        "",
        "| Relation | Environment | Network | Batch | Prove (s) | Verify (s) | Proof bytes | Cycles |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in proved_rows:
        lines.append(
            f"| `{row['relation_id']}` | `{row['environment']}` | `{row['network_spec']}` | "
            f"{row['batch_size']} | {row['prove_time_sec']} | {row['verify_time_sec']} | "
            f"{row['proof_size_bytes']} | {row['cycle_count']} |"
        )
    lines.extend(
        [
            "",
            "## Source Files",
            "",
            "- `summary.json`: machine-readable aggregate.",
            "- `benchmark_matrix.csv`: normalized benchmark and rejection rows.",
            "- `tamper_matrix.csv`: normalized tamper coverage.",
            "- `reproduction.md`: reviewer commands for Python smoke and SP1/Kaggle paths.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reproduction_md(path: Path, components: List[Dict[str, Any]]) -> None:
    lines = [
        "# Final NDSS Reproduction Notes",
        "",
        "Run commands from the repository root.",
        "",
        "## Fast Python Smoke Path",
        "",
        "```powershell",
        "python scripts/experiments/run_full_regression.py",
        "python scripts/experiments/run_final_ndss_regression.py",
        "```",
        "",
        "The smoke path verifies Python semantics and regenerates the final aggregate from existing component summaries.",
        "",
        "## Component Smoke Commands",
        "",
        "```powershell",
    ]
    for component in components:
        lines.append(str(component["smoke_command"]))
    lines.extend(
        [
            "python scripts/experiments/run_final_ndss_regression.py",
            "```",
            "",
            "## SP1 / WSL2 Ubuntu / Kaggle Path",
            "",
            "Install the SP1 toolchain first, then run:",
            "",
            "```bash",
            "cd /path/to/zk_offline_dqn",
        ]
    )
    for component in components:
        lines.append(str(component["command"]))
    lines.extend(
        [
            "python3 scripts/experiments/run_final_ndss_regression.py",
            "```",
            "",
            "For the distinct-TD benchmark, accepted cases can be proved one at a time:",
            "",
            "```bash",
            "python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-1",
            "python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-2",
            "python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-4",
            "python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-8",
            "```",
            "",
            "Expected aggregate outputs:",
            "",
            "```text",
            "artifacts/benchmarks/final_ndss/summary.json",
            "artifacts/benchmarks/final_ndss/benchmark_matrix.csv",
            "artifacts/benchmarks/final_ndss/tamper_matrix.csv",
            "artifacts/benchmarks/final_ndss/summary.md",
            "artifacts/benchmarks/final_ndss/reproduction.md",
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    benchmark_rows: List[Dict[str, Any]] = []
    tamper_rows: List[Dict[str, Any]] = []
    component_summaries: List[Dict[str, Any]] = []

    for component in COMPONENTS:
        path = component["summary_path"]
        if not path.exists():
            raise FileNotFoundError(f"missing component summary: {rel(path)}")
        summary = load_json(path)
        rows, tampers = build_rows(component, summary)
        benchmark_rows.extend(rows)
        tamper_rows.extend(tampers)
        component_summaries.append(
            {
                "component_id": component["component_id"],
                "relation_id": component["relation_id"],
                "environment": component["environment"],
                "summary_path": rel(path),
                "all_passed": summary.get("all_passed"),
                "all_python_expected": summary.get("all_python_expected"),
                "all_sp1_expected": summary.get("all_sp1_expected"),
                "python_sp1_agreement": summary.get("python_sp1_agreement"),
                "skip_sp1": summary.get("skip_sp1"),
                "prove": summary.get("prove"),
            }
        )

    aggregate = {
        "artifact_id": "achieved_relation_benchmark_v1",
        "output_dir": rel(out_dir),
        "components": component_summaries,
        "benchmark_rows": len(benchmark_rows),
        "tamper_rows": len(tamper_rows),
        "all_components_passed": all(item.get("all_passed") for item in component_summaries),
        "benchmark_matrix_path": rel(out_dir / "benchmark_matrix.csv"),
        "tamper_matrix_path": rel(out_dir / "tamper_matrix.csv"),
        "reproduction_path": rel(out_dir / "reproduction.md"),
        "benchmark_matrix": benchmark_rows,
        "tamper_matrix": tamper_rows,
    }

    benchmark_fields = [
        "relation_id",
        "environment",
        "network_spec",
        "batch_size",
        "merkle_depth",
        "accepted_fixtures",
        "rejected_tamper_fixtures",
        "prove_time_sec",
        "verify_time_sec",
        "proof_size_bytes",
        "cycle_count",
        "platform",
        "command",
        "source_summary",
        "source_case",
        "fixture_path",
        "backend",
        "status",
    ]
    tamper_fields = [
        "relation_id",
        "environment",
        "network_spec",
        "case",
        "category",
        "expected_outcome",
        "python_outcome",
        "sp1_outcome",
        "passed",
        "fixture_path",
        "source_summary",
    ]

    write_json(out_dir / "summary.json", aggregate)
    write_csv(out_dir / "benchmark_matrix.csv", benchmark_rows, benchmark_fields)
    write_csv(out_dir / "tamper_matrix.csv", tamper_rows, tamper_fields)
    write_summary_md(out_dir / "summary.md", aggregate, benchmark_rows)
    write_reproduction_md(out_dir / "reproduction.md", COMPONENTS)

    print("summary_json_path =", rel(out_dir / "summary.json"))
    print("benchmark_matrix_csv_path =", rel(out_dir / "benchmark_matrix.csv"))
    print("tamper_matrix_csv_path =", rel(out_dir / "tamper_matrix.csv"))
    print("summary_md_path =", rel(out_dir / "summary.md"))
    print("reproduction_md_path =", rel(out_dir / "reproduction.md"))
    print("benchmark_rows =", len(benchmark_rows))
    print("tamper_rows =", len(tamper_rows))
    print("all_components_passed =", aggregate["all_components_passed"])

    if not aggregate["all_components_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
