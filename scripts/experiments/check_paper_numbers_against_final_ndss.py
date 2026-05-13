"""Check paper proof-metric numbers against the final NDSS artifact JSON.

The script intentionally checks the exact table values used in
paper/sections/results.tex. Rounded prose in the abstract remains editorial,
but the authoritative table must contain the exact JSON values.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUMMARY_PATH = ROOT / "artifacts" / "benchmarks" / "final_ndss" / "summary.json"
RESULTS_TEX_PATH = ROOT / "paper" / "sections" / "results.tex"
ABSTRACT_TEX_PATH = ROOT / "paper" / "sections" / "abstract.tex"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _format_decimal(value: float) -> str:
    return f"{value:.6f}"


def main() -> int:
    summary = _load_json(SUMMARY_PATH)
    results_tex = RESULTS_TEX_PATH.read_text(encoding="utf-8")
    abstract_tex = ABSTRACT_TEX_PATH.read_text(encoding="utf-8")
    paper_text = results_tex + "\n" + abstract_tex

    failures: list[str] = []

    for key in ("benchmark_rows", "tamper_rows"):
        expected = str(summary[key])
        if expected not in paper_text:
            failures.append(f"{key}={expected} missing from paper text")

    proof_rows = [
        row
        for row in summary["benchmark_matrix"]
        if row["status"] == "accepted" and row["backend"] == "SP1 proof"
    ]
    if len(proof_rows) != 7:
        failures.append(f"expected 7 accepted SP1 proof rows, found {len(proof_rows)}")

    for row in proof_rows:
        label = (
            f"{row['relation_id']} {row['environment']} "
            f"{row['network_spec']} batch={row['batch_size']}"
        )
        for field in ("prove_time_sec", "verify_time_sec"):
            expected = _format_decimal(row[field])
            if expected not in results_tex:
                failures.append(f"{label}: {field}={expected} missing from results table")
        for field in ("proof_size_bytes",):
            expected = str(row[field])
            if expected not in results_tex:
                failures.append(f"{label}: {field}={expected} missing from results table")

    if failures:
        print("paper_number_check_passed = False")
        for failure in failures:
            print(f"failure = {failure}")
        return 1

    print("paper_number_check_passed = True")
    print(f"summary_path = {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"accepted_sp1_proof_rows = {len(proof_rows)}")
    print(f"benchmark_rows = {summary['benchmark_rows']}")
    print(f"tamper_rows = {summary['tamper_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
