from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .cases import MANDATORY_CATEGORIES, TABLE3_COLUMNS, check_mandatory_categories, validate_rows


TABLE3_FILENAMES = {
    "csv": "table3_tamper_rejection.csv",
    "json": "table3_tamper_rejection.json",
    "tex": "table3_tamper_rejection.tex",
    "md": "table3_tamper_rejection.md",
    "status": "table3_tamper_rejection_status.json",
}

COMPACT_COLUMNS = ["Tamper", "Component", "Expected Layer", "Observed Layer", "Status", "Notes"]


def write_table3_outputs(rows: List[Dict[str, Any]], out_dir: str | Path, *, status: Dict[str, Any]) -> Dict[str, Path]:
    validate_rows(rows)
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths = {key: target / name for key, name in TABLE3_FILENAMES.items()}
    table_rows = [{column: row.get(column, "") for column in TABLE3_COLUMNS} for row in rows]
    with paths["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE3_COLUMNS)
        writer.writeheader()
        writer.writerows(table_rows)
    paths["json"].write_text(
        json.dumps(
            {
                "table": "Table 3: Tamper rejection",
                "scope": "tamper rejection only for existing supported relations and provenance checks",
                "rows": table_rows,
                "summary": compact_summary(table_rows),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["md"].write_text(_markdown(table_rows), encoding="utf-8")
    paths["tex"].write_text(_tex(table_rows), encoding="utf-8")
    status_payload = dict(status)
    status_payload["mandatory_categories"] = MANDATORY_CATEGORIES
    status_payload["mandatory_check"] = check_mandatory_categories(table_rows)
    paths["status"].write_text(json.dumps(status_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return paths


def write_phase_outputs(
    rows: Iterable[Dict[str, Any]],
    phase_dir: str | Path,
    *,
    config: Dict[str, Any],
    status: Dict[str, Any],
) -> Dict[str, Path]:
    target = Path(phase_dir)
    target.mkdir(parents=True, exist_ok=True)
    rows_list = list(rows)
    results = target / "results.jsonl"
    with results.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows_list:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    config_path = target / "config.json"
    status_path = target / "status.json"
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"results": results, "config": config_path, "status": status_path}


def compact_summary(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    components: Dict[str, set[str]] = defaultdict(set)
    for row in rows:
        category = str(row.get("Tamper Category") or "")
        item = grouped.setdefault(
            category,
            {
                "tamper_category": category,
                "total_cases": 0,
                "rejected_as_expected": 0,
                "accepted_unexpectedly": 0,
                "not_applicable": 0,
                "components_covered": "",
            },
        )
        item["total_cases"] += 1
        status = row.get("Status")
        if status == "rejected_as_expected":
            item["rejected_as_expected"] += 1
        elif status == "accepted_unexpectedly":
            item["accepted_unexpectedly"] += 1
        elif status == "not_applicable":
            item["not_applicable"] += 1
        components[category].add(str(row.get("Relation / Component") or ""))
    for category, item in grouped.items():
        item["components_covered"] = ", ".join(sorted(value for value in components[category] if value))
    return [grouped[key] for key in sorted(grouped)]


def _markdown(rows: List[Dict[str, Any]]) -> str:
    compact = _compact_rows(rows)
    lines = [
        "# Table 3: Tamper Rejection",
        "",
        "| " + " | ".join(COMPACT_COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(COMPACT_COLUMNS)) + " |",
    ]
    for row in compact:
        lines.append(
            "| "
            + " | ".join(
                _md(str(row.get(column, "") or "")) for column in COMPACT_COLUMNS
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Table 3 reports tamper rejection only. Proof-manifest aggregation rows do not claim true recursive child-proof verification.",
            "",
        ]
    )
    return "\n".join(lines)


def _compact_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    selected = []
    seen = set()
    for category in MANDATORY_CATEGORIES:
        for row in rows:
            if row.get("Tamper Category") == category and row.get("Status") == "rejected_as_expected":
                key = row.get("Tamper ID")
                if key not in seen:
                    selected.append(
                        {
                            "Tamper": category,
                            "Component": row.get("Relation / Component"),
                            "Expected Layer": row.get("Expected Rejection Layer"),
                            "Observed Layer": row.get("Observed Rejection Layer"),
                            "Status": row.get("Status"),
                            "Notes": row.get("Notes"),
                        }
                    )
                    seen.add(key)
                break
    for item in compact_summary(rows):
        selected.append(
            {
                "Tamper": item["tamper_category"],
                "Component": item["components_covered"],
                "Expected Layer": "summary",
                "Observed Layer": "summary",
                "Status": f"{item['rejected_as_expected']}/{item['total_cases']} rejected",
                "Notes": f"{item['not_applicable']} not_applicable",
            }
        )
    return selected


def _tex(rows: List[Dict[str, Any]]) -> str:
    def esc(value: Any) -> str:
        text = str(value or "")
        return (
            text.replace("\\", r"\textbackslash{}")
            .replace("&", r"\&")
            .replace("_", r"\_")
            .replace("%", r"\%")
            .replace("#", r"\#")
        )

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Tamper rejection for supported provenance checks and proof-backed relations.}",
        r"\label{tab:tamper-rejection}",
        r"\begin{tabular}{llllll}",
        r"\toprule",
        " & ".join(COMPACT_COLUMNS) + r" \\",
        r"\midrule",
    ]
    for row in _compact_rows(rows):
        lines.append(" & ".join(esc(row.get(column)) for column in COMPACT_COLUMNS) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def _md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
