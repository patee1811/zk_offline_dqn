"""Generate deterministic report snapshots from existing benchmark outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from zk_offline_dqn.experiments import benchmark_manifest, paper_numbers


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = ROOT / "artifacts/reports/final_ndss"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in names})


def _final_ndss_summary(root: Path) -> tuple[Dict[str, Any] | None, Path]:
    path = root / "artifacts/benchmarks/final_ndss/summary.json"
    return read_json(path), path


def build_benchmark_summary_rows(root: Path | None = None) -> List[Dict[str, Any]]:
    base = root or ROOT
    summary, path = _final_ndss_summary(base)
    if summary is None:
        return [
            {
                "status": "missing",
                "source_path": rel(path),
                "relation_id": None,
                "environment": None,
                "backend": None,
            }
        ]

    rows: List[Dict[str, Any]] = []
    for row in summary.get("benchmark_matrix", []):
        out = dict(row)
        out.setdefault("status", "missing")
        out["source_path"] = rel(path)
        rows.append(out)
    return rows


def build_tamper_summary_rows(root: Path | None = None) -> List[Dict[str, Any]]:
    base = root or ROOT
    summary, path = _final_ndss_summary(base)
    if summary is None:
        return [
            {
                "status": "missing",
                "source_path": rel(path),
                "relation_id": None,
                "environment": None,
                "case": None,
            }
        ]

    rows: List[Dict[str, Any]] = []
    for row in summary.get("tamper_matrix", []):
        out = dict(row)
        if "status" not in out:
            if out.get("passed") is None:
                out["status"] = "missing"
            else:
                out["status"] = "passed" if out.get("passed") else "failed"
        out.setdefault("observed_outcome", out.get("sp1_outcome") or out.get("python_outcome"))
        out.setdefault("backend", "SP1 proof" if out.get("sp1_outcome") else "Python oracle")
        out["source_path"] = rel(path)
        rows.append(out)
    return rows


def build_sp1_status(root: Path | None = None) -> Dict[str, Any]:
    return {
        "artifact_id": "phase7_sp1_status_v1",
        "td_mvp": paper_numbers.build_sp1_td_mvp_status(root),
        "scope_note": (
            "Validated status, if present, applies only to the TD MVP SP1 "
            "backend and zk_backend/test_vectors/td_mvp_case_0.json."
        ),
    }


def write_benchmark_snapshot(path: Path, numbers: Dict[str, Any], sp1_status: Dict[str, Any]) -> None:
    regression = numbers.get("regression", {})
    final_ndss = numbers.get("final_ndss_existing", {})
    sp1 = sp1_status.get("td_mvp", {})
    lines = [
        "# Phase 7 Benchmark Snapshot",
        "",
        "This file is generated from existing regression, benchmark, and Kaggle",
        "validation outputs. Missing values are not inferred.",
        "",
        "## Regression",
        "",
        f"- Status: {regression.get('status', 'missing')}",
        f"- All passed: {(regression.get('all_passed') or {}).get('value')}",
        f"- Checks: {(regression.get('num_passed') or {}).get('value')}/"
        f"{(regression.get('num_checks') or {}).get('value')}",
        "",
        "## Existing Final NDSS Benchmark Summary",
        "",
        f"- Status: {final_ndss.get('status', 'missing')}",
        f"- Benchmark rows: {(final_ndss.get('benchmark_rows') or {}).get('value')}",
        f"- Tamper rows: {(final_ndss.get('tamper_rows') or {}).get('value')}",
        f"- Components passed: {(final_ndss.get('all_components_passed') or {}).get('value')}",
        "",
        "## SP1 TD MVP Proof",
        "",
        f"- Status: {sp1.get('status')}",
        f"- Scope: {sp1.get('claim_scope')}",
        f"- Proof generated: {(sp1.get('proof_generated') or {}).get('value')}",
        f"- Proof verified: {(sp1.get('proof_verified') or {}).get('value')}",
        f"- Proving time sec: {(sp1.get('proving_time_sec') or {}).get('value')}",
        f"- Verification time sec: {(sp1.get('verification_time_sec') or {}).get('value')}",
        f"- Proof size bytes: {(sp1.get('proof_size_bytes') or {}).get('value')}",
        f"- Cycle count: {(sp1.get('cycle_count') or {}).get('value')}",
        "",
        "The SP1 proof claim is scoped only to the TD MVP canonical vector.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_reports(out_dir: Path | str | None = None, root: Path | None = None) -> Dict[str, str]:
    base = root or ROOT
    target = Path(out_dir) if out_dir is not None else DEFAULT_OUT_DIR
    if not target.is_absolute():
        target = base / target
    target.mkdir(parents=True, exist_ok=True)

    numbers = paper_numbers.assemble_paper_numbers(base)
    sp1_status = build_sp1_status(base)
    benchmark_rows = build_benchmark_summary_rows(base)
    tamper_rows = build_tamper_summary_rows(base)

    paths = {
        "paper_numbers": target / "paper_numbers.json",
        "benchmark_summary": target / "benchmark_summary.csv",
        "tamper_summary": target / "tamper_summary.csv",
        "sp1_status": target / "sp1_status.json",
        "benchmark_snapshot": target / "benchmark_snapshot.md",
    }

    write_json(paths["paper_numbers"], numbers)
    write_json(paths["sp1_status"], sp1_status)
    write_csv(
        paths["benchmark_summary"],
        benchmark_rows,
        [
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
            "source_path",
        ],
    )
    write_csv(
        paths["tamper_summary"],
        tamper_rows,
        [
            "relation_id",
            "environment",
            "network_spec",
            "case",
            "category",
            "expected_outcome",
            "observed_outcome",
            "python_outcome",
            "sp1_outcome",
            "passed",
            "backend",
            "source_summary",
            "fixture_path",
            "status",
            "source_path",
        ],
    )
    write_benchmark_snapshot(paths["benchmark_snapshot"], numbers, sp1_status)

    return {key: rel(path) for key, path in paths.items()}


def check_report_sources(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    result = benchmark_manifest.check_sources(base)
    table1 = check_table1_rl_performance(base)
    table2 = check_table2_zk_proof_cost(base)
    result["table1_rl_performance"] = table1
    result["table2_zk_proof_cost"] = table2
    if table1["status"] != "passed" or table2["status"] != "passed":
        result["status"] = "failed"
    return result


def check_table1_rl_performance(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    table_dir = base / "artifacts/reports/final_ndss"
    required = [
        "table1_rl_performance.csv",
        "table1_rl_performance.json",
        "table1_rl_performance.tex",
        "table1_rl_performance.md",
        "table1_rl_performance_status.json",
    ]
    missing = [name for name in required if not (table_dir / name).exists()]
    if missing:
        return {
            "status": "failed",
            "missing_files": missing,
            "completed_public_rows": 0,
            "required_public_size_coverage": {},
            "reason": "Table 1 compact outputs are missing",
        }

    payload = read_json(table_dir / "table1_rl_performance.json") or {}
    rows = payload.get("rows", [])
    completed_public = [
        row
        for row in rows
        if row.get("status") == "completed"
        and row.get("dataset_source_type") == "public_source_integrity"
    ]
    status_payload = read_json(table_dir / "table1_rl_performance_status.json") or {}
    status_text = json.dumps(status_payload, sort_keys=True)
    coverage = {}
    for size in ("10000", "50000", "100000"):
        covered = any(size in str(row.get("dataset", "")) for row in rows)
        documented = size in status_text
        coverage[size] = {"row_present": covered, "documented_in_status": documented}

    reasons = []
    if not completed_public:
        reasons.append("no completed public Minari/D4RL Table 1 row")
    if not all(item["row_present"] or item["documented_in_status"] for item in coverage.values()):
        reasons.append("required public 10k/50k/100k coverage is undocumented")
    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": [],
        "completed_public_rows": len(completed_public),
        "required_public_size_coverage": coverage,
        "reason": "; ".join(reasons) if reasons else None,
    }


def check_table2_zk_proof_cost(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    table_dir = base / "artifacts/reports/final_ndss"
    required = [
        "table2_zk_proof_cost.csv",
        "table2_zk_proof_cost.json",
        "table2_zk_proof_cost.tex",
        "table2_zk_proof_cost.md",
        "table2_zk_proof_cost_status.json",
    ]
    missing = [name for name in required if not (table_dir / name).exists()]
    if missing:
        return {
            "status": "failed",
            "missing_files": missing,
            "reason": "Table 2 compact outputs are missing",
            "proof_verified_rows": 0,
        }

    payload = read_json(table_dir / "table2_zk_proof_cost.json") or {}
    rows = payload.get("rows", [])
    required_relations = {
        "td_mvp",
        "merkle_membership",
        "forward_td_mlp",
        "one_step_sgd_tiny",
        "short_trace",
        "training_update",
        "training_fragment_k1",
        "training_fragment_k4",
        "training_fragment_k8",
        "training_aggregation_manifest_t32",
        "training_aggregation_manifest_t64",
        "training_aggregation_manifest_t128",
    }
    present_text = " ".join(
        " ".join(str(value) for value in row.values()) for row in rows if isinstance(row, dict)
    )
    missing_relations = sorted(relation for relation in required_relations if relation not in present_text)
    required_fields = [
        "Prove Time (s)",
        "Verify Time (s)",
        "Proof Size (bytes)",
        "Cycle Count",
        "Peak RSS (MB)",
        "Status",
    ]
    missing_fields = [
        field
        for field in required_fields
        if any(isinstance(row, dict) and field not in row for row in rows)
    ]
    proof_verified = [row for row in rows if isinstance(row, dict) and row.get("Status") == "proof_verified"]
    metric_gaps = []
    for row in proof_verified:
        for field in ["Prove Time (s)", "Verify Time (s)", "Proof Size (bytes)", "Cycle Count"]:
            if row.get(field) in {None, ""}:
                metric_gaps.append(f"{row.get('Case ID')}:{field}")
    reasons = []
    if missing_relations:
        reasons.append("missing required proof rows: " + ", ".join(missing_relations))
    if missing_fields:
        reasons.append("missing required fields: " + ", ".join(sorted(set(missing_fields))))
    if not proof_verified:
        reasons.append("no proof_verified Table 2 rows")
    if metric_gaps:
        reasons.append("proof_verified metric gaps: " + ", ".join(metric_gaps[:10]))
    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": [],
        "missing_required_relations": missing_relations,
        "proof_verified_rows": len(proof_verified),
        "reason": "; ".join(reasons) if reasons else None,
    }
