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
    return benchmark_manifest.check_sources(root)
