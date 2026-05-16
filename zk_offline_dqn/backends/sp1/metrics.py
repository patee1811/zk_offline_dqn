"""Read-only helpers for existing SP1 benchmark summaries."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_SUMMARY_PATHS = (
    Path("artifacts/benchmarks/final_ndss/source_summaries/distinct_td_sp1/summary.json"),
    Path("artifacts/benchmarks/final_ndss/source_summaries/forward_td_mlp_sp1/summary.json"),
    Path("artifacts/benchmarks/final_ndss/source_summaries/one_step_sgd_tiny_sp1/summary.json"),
    Path("artifacts/benchmarks/distinct_td_sp1_python_smoke/summary.json"),
    Path("artifacts/benchmarks/forward_td_mlp_sp1_python_smoke/summary.json"),
    Path("artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke/summary.json"),
)

SP1_PROVENANCE_SUMMARY_PATHS = (
    Path("artifacts/reports/provenance/sp1/kaggle_sp1_validation_summary.json"),
    Path("artifacts/reports/provenance/sp1/kaggle_sp1_setup_summary.json"),
)


def load_json_summary(path: str | Path) -> Dict[str, Any]:
    summary_path = Path(path)
    if not summary_path.exists():
        return {
            "path": summary_path.as_posix(),
            "status": "missing",
            "data": None,
        }
    with summary_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        "path": summary_path.as_posix(),
        "status": "loaded",
        "data": data,
    }


def load_csv_rows(path: str | Path) -> Dict[str, Any]:
    csv_path = Path(path)
    if not csv_path.exists():
        return {
            "path": csv_path.as_posix(),
            "status": "missing",
            "rows": [],
        }
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows: List[Dict[str, str]] = list(csv.DictReader(handle))
    return {
        "path": csv_path.as_posix(),
        "status": "loaded",
        "rows": rows,
    }


def load_default_summaries() -> List[Dict[str, Any]]:
    return [load_json_summary(path) for path in DEFAULT_SUMMARY_PATHS]


def load_sp1_provenance_summaries() -> List[Dict[str, Any]]:
    return [load_json_summary(path) for path in SP1_PROVENANCE_SUMMARY_PATHS]


def load_benchmark_matrix(summary_dir: str | Path) -> Dict[str, Any]:
    return load_csv_rows(Path(summary_dir) / "benchmark_matrix.csv")
