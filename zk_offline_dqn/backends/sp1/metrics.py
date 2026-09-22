"""Read-only helpers for existing SP1 benchmark summaries."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

LEAF_CYCLE_SUMMARY_KEY = "leaf_cycle_summary"


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


def load_tree_leaves(work_dir: str | Path) -> List[Dict[str, Any]]:
    """Every proved leaf of one aggregation tree, from its own provenance.

    Reads leaf_<i>/metrics.json for the cycle count and leaf_<i>/public_inputs.json
    for the settings the count was measured under, so a summary can say which
    population it covers instead of leaving that to whoever quotes it.
    """
    leaves: List[Dict[str, Any]] = []
    for leaf_dir in Path(work_dir).glob("leaf_*"):
        suffix = leaf_dir.name[len("leaf_"):]
        metrics_path = leaf_dir / "metrics.json"
        if not suffix.isdigit() or not metrics_path.exists():
            continue
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        public_path = leaf_dir / "public_inputs.json"
        public = (
            json.loads(public_path.read_text(encoding="utf-8"))
            if public_path.exists()
            else {}
        )
        leaves.append(
            {
                "chunk_id": int(suffix),
                "cycle_count": int(metrics["cycle_count"]),
                "num_steps": metrics.get("num_steps", public.get("num_steps")),
                "target_sync_interval": public.get("target_sync_interval"),
            }
        )
    return sorted(leaves, key=lambda leaf: leaf["chunk_id"])


def leaf_cycle_summary(leaves: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """The cycle range of a tree's leaves, with the population it was taken over.

    The paper once printed min/max ranges taken over four of eight leaves and
    twenty of thirty-two, because the range was read off by hand. A summary
    written beside the leaves, over all of them, is what the paper quotes now.
    Leaves measured under different settings are not one population, so they
    are refused rather than averaged into a range that describes neither.
    """
    rows = sorted(leaves, key=lambda leaf: leaf["chunk_id"])
    if not rows:
        raise ValueError("leaf_cycle_summary needs at least one proved leaf")
    for field in ("num_steps", "target_sync_interval"):
        values = {row.get(field) for row in rows}
        if len(values) != 1:
            raise ValueError(f"leaves disagree on {field}: {sorted(values, key=str)}")
    cycles = [int(row["cycle_count"]) for row in rows]
    return {
        "leaf_count": len(rows),
        "num_steps": rows[0].get("num_steps"),
        "target_sync_interval": rows[0].get("target_sync_interval"),
        "cycle_count_min": min(cycles),
        "cycle_count_max": max(cycles),
        "leaves": [
            {"chunk_id": row["chunk_id"], "cycle_count": int(row["cycle_count"])}
            for row in rows
        ],
    }
