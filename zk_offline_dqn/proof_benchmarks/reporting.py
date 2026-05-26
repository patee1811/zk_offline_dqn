from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


TABLE2_FILENAMES = {
    "csv": "table2_zk_proof_cost.csv",
    "json": "table2_zk_proof_cost.json",
    "tex": "table2_zk_proof_cost.tex",
    "md": "table2_zk_proof_cost.md",
    "status": "table2_zk_proof_cost_status.json",
}

TABLE2_COLUMNS = [
    "Category",
    "Relation",
    "Variant",
    "Scale Axis",
    "Batch Size",
    "Network",
    "Trace Length",
    "Dataset Size",
    "Merkle Depth",
    "Aggregation T",
    "Proof Backed",
    "Status",
    "Prove Time (s)",
    "Verify Time (s)",
    "Proof Size (bytes)",
    "Cycle Count",
    "Prover Gas",
    "Peak RSS (MB)",
    "Max RSS (MB)",
    "Backend Version",
    "SP1 Version",
    "Git Commit",
    "Case ID",
    "Public Inputs SHA256",
    "Witness Schema SHA256",
    "Metrics Source",
    "Notes",
]

COMPACT_COLUMNS = [
    "Relation",
    "Variant",
    "Scale Axis",
    "Status",
    "Prove Time (s)",
    "Verify Time (s)",
    "Proof Size (bytes)",
    "Cycle Count",
    "Peak RSS (MB)",
]


def row_to_table(row: Dict[str, Any]) -> Dict[str, Any]:
    return {column: row.get(column, "") for column in TABLE2_COLUMNS}


def write_table2_outputs(
    rows: List[Dict[str, Any]],
    out_dir: str | Path,
    *,
    status: Dict[str, Any],
) -> Dict[str, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths = {key: target / name for key, name in TABLE2_FILENAMES.items()}
    table_rows = [row_to_table(row) for row in rows]
    with paths["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TABLE2_COLUMNS)
        writer.writeheader()
        writer.writerows(table_rows)
    paths["json"].write_text(
        json.dumps(
            {
                "table": "Table 2: ZK proof cost",
                "scope": "ZK proof cost only",
                "rows": table_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["md"].write_text(_markdown(table_rows), encoding="utf-8")
    paths["tex"].write_text(_tex(table_rows), encoding="utf-8")
    paths["status"].write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return paths


def _markdown(rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# Table 2: ZK Proof Cost",
        "",
        "| " + " | ".join(COMPACT_COLUMNS) + " |",
        "| " + " | ".join(["---"] * len(COMPACT_COLUMNS)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "") or "") for column in COMPACT_COLUMNS) + " |")
    lines.extend(["", "Table 2 is ZK-proof-cost-only; unsupported and execute-only rows are not proof-backed.", ""])
    return "\n".join(lines)


def _tex(rows: List[Dict[str, Any]]) -> str:
    def esc(value: Any) -> str:
        text = str(value or "")
        return text.replace("&", r"\&").replace("_", r"\_").replace("%", r"\%")

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{ZK proof cost for supported SP1-backed relations.}",
        r"\label{tab:zk-proof-cost}",
        r"\begin{tabular}{lllllllll}",
        r"\toprule",
        " & ".join(COMPACT_COLUMNS) + r" \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(" & ".join(esc(row.get(column)) for column in COMPACT_COLUMNS) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)
