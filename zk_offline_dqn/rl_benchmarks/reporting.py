from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


TABLE_FILENAMES = {
    "csv": "table1_rl_performance.csv",
    "json": "table1_rl_performance.json",
    "tex": "table1_rl_performance.tex",
    "md": "table1_rl_performance.md",
    "status": "table1_rl_performance_status.json",
}
TABLE_COLUMNS = [
    "Dataset",
    "Family",
    "Source",
    "Transitions",
    "Baseline",
    "Seeds",
    "Avg Return",
    "Std Return",
    "Norm. Score",
    "Success Rate",
    "Train Steps",
    "Status",
]


def _json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return ""
    return f"{float(value):.{digits}f}"


def _mean_std(mean: float | None, std: float | None) -> str:
    if mean is None:
        return ""
    if std is None:
        return _fmt(mean)
    return f"{_fmt(mean)} +/- {_fmt(std)}"


def table_row(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Dataset": result["dataset"],
        "Family": result.get("dataset_family", ""),
        "Source": result.get("dataset_source_type", ""),
        "Transitions": result.get("dataset_num_transitions"),
        "Baseline": result["baseline"],
        "Seeds": result.get("num_seeds"),
        "Avg Return": _mean_std(
            result.get("average_return_mean"), result.get("average_return_std")
        ),
        "Norm. Score": _mean_std(
            result.get("normalized_score_mean"), result.get("normalized_score_std")
        ),
        "Success Rate": _mean_std(
            result.get("success_rate_mean"), result.get("success_rate_std")
        ),
        "Std Return": _fmt(result.get("average_return_std")),
        "Train Steps": result.get("train_steps"),
        "Status": result.get("status", "completed"),
    }


def skipped_result_rows(
    dataset: str,
    baselines: Iterable[str],
    *,
    source_type: str,
    reason: str,
    status: str = "skipped",
    dataset_family: str | None = None,
) -> List[Dict[str, Any]]:
    return [
        {
            "dataset": dataset,
            "baseline": baseline,
            "dataset_family": dataset_family or dataset,
            "dataset_source_type": source_type,
            "status": status,
            "reason": reason,
            "average_return_mean": None,
            "average_return_std": None,
            "normalized_score_mean": None,
            "normalized_score_std": None,
            "success_rate_mean": None,
            "success_rate_std": None,
            "num_seeds": 0,
            "num_eval_episodes": 0,
            "train_steps": 0,
            "dataset_num_transitions": 0,
        }
        for baseline in baselines
    ]


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _markdown(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Table 1: RL Performance",
        "",
        "| " + " | ".join(TABLE_COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(TABLE_COLUMNS)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "") or "") for column in TABLE_COLUMNS) + " |")
    lines.extend(
        [
            "",
            "Table 1 is RL-performance-only; SP1 proof-cost and tamper results are reported separately.",
            "",
        ]
    )
    return "\n".join(lines)


def _tex(rows: List[Dict[str, Any]]) -> str:
    escaped = {
        "&": r"\&",
        "_": r"\_",
        "%": r"\%",
    }

    def tex(value: Any) -> str:
        text = str(value or "")
        for source, target in escaped.items():
            text = text.replace(source, target)
        return text.replace("+/-", r"$\pm$")

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{RL performance on offline benchmark datasets.}",
        r"\label{tab:rl-performance}",
        r"\begin{tabular}{llllllllllll}",
        r"\toprule",
        " & ".join(TABLE_COLUMNS) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(tex(row.get(column)) for column in TABLE_COLUMNS) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def write_table_outputs(
    results: List[Dict[str, Any]],
    out_dir: str | Path,
    *,
    status: Dict[str, Any],
) -> Dict[str, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    rows = [table_row(result) for result in results]
    paths = {key: target / name for key, name in TABLE_FILENAMES.items()}
    _write_csv(paths["csv"], rows)
    _json_dump(
        paths["json"],
        {
            "table": "Table 1: RL performance",
            "scope": "RL performance only",
            "rows": results,
        },
    )
    paths["md"].write_text(_markdown(rows), encoding="utf-8")
    paths["tex"].write_text(_tex(rows), encoding="utf-8")
    _json_dump(paths["status"], status)
    return paths
