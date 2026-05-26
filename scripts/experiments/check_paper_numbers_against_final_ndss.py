"""Validate paper-facing number sources against final NDSS report artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
FINAL_DIR = ROOT / "artifacts/reports/final_ndss"
PAPER_NUMBERS_PATH = FINAL_DIR / "paper_numbers.json"


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    failures: list[str] = []
    required = [
        "paper_numbers.json",
        "table1_rl_performance.csv",
        "table1_rl_performance.json",
        "table2_zk_proof_cost.csv",
        "table2_zk_proof_cost.json",
        "table3_tamper_rejection.csv",
        "table3_tamper_rejection.json",
    ]
    for name in required:
        if not (FINAL_DIR / name).exists():
            failures.append(f"missing {name}")

    if PAPER_NUMBERS_PATH.exists():
        numbers = _load_json(PAPER_NUMBERS_PATH)
        for key in ["regression", "final_ndss_existing", "sp1_td_mvp_proof"]:
            if key not in numbers:
                failures.append(f"paper_numbers missing {key}")
        sp1_scope = numbers.get("sp1_td_mvp_proof", {}).get("claim_scope")
        if sp1_scope != "td_mvp_canonical_vector_only":
            failures.append(f"unexpected legacy TD MVP scope field: {sp1_scope}")

    table3 = _load_json(FINAL_DIR / "table3_tamper_rejection.json") if (FINAL_DIR / "table3_tamper_rejection.json").exists() else {"rows": []}
    accepted = [
        row.get("Tamper ID")
        for row in table3.get("rows", [])
        if isinstance(row, dict) and row.get("Status") == "accepted_unexpectedly"
    ]
    if accepted:
        failures.append("Table 3 has accepted_unexpectedly rows: " + ", ".join(str(item) for item in accepted[:10]))

    paper_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in [
            ROOT / "paper/sections/abstract.tex",
            ROOT / "paper/sections/results.tex",
            ROOT / "paper/sections/limitations.tex",
        ]
        if path.exists()
    ).lower()
    stale_refs = ["artifacts/benchmarks/final_ndss/summary.json", "benchmark_matrix.csv", "tamper_matrix.csv"]
    for ref in stale_refs:
        if ref in paper_text:
            failures.append(f"stale paper source reference: {ref}")

    if failures:
        print("paper_number_check_passed = False")
        for failure in failures:
            print(f"failure = {failure}")
        return 1

    print("paper_number_check_passed = True")
    print(f"paper_numbers_path = {PAPER_NUMBERS_PATH.relative_to(ROOT)}")
    print("tables = table1_rl_performance, table2_zk_proof_cost, table3_tamper_rejection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
