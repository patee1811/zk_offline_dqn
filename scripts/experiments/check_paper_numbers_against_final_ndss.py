"""Check scoped paper numbers against Phase 7 paper-facing reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[2]
PAPER_NUMBERS_PATH = ROOT / "artifacts/reports/final_ndss/paper_numbers.json"
RESULTS_TEX_PATH = ROOT / "paper/sections/results.tex"
ABSTRACT_TEX_PATH = ROOT / "paper/sections/abstract.tex"


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _value(data: Dict[str, Any], *keys: str) -> Any:
    node: Any = data
    for key in keys:
        node = node[key]
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def _format_float(value: Any) -> str:
    return f"{float(value):.6f}"


def main() -> int:
    paper_numbers = _load_json(PAPER_NUMBERS_PATH)
    results_tex = RESULTS_TEX_PATH.read_text(encoding="utf-8")
    abstract_tex = ABSTRACT_TEX_PATH.read_text(encoding="utf-8")
    paper_text = results_tex + "\n" + abstract_tex

    failures: list[str] = []

    expected_values = {
        "benchmark_rows": str(_value(paper_numbers, "final_ndss_existing", "benchmark_rows")),
        "tamper_rows": str(_value(paper_numbers, "final_ndss_existing", "tamper_rows")),
        "regression_checks": str(_value(paper_numbers, "regression", "num_checks")),
        "proving_time_sec": _format_float(
            _value(paper_numbers, "sp1_td_mvp_proof", "proving_time_sec")
        ),
        "verification_time_sec": _format_float(
            _value(paper_numbers, "sp1_td_mvp_proof", "verification_time_sec")
        ),
        "proof_size_bytes": str(_value(paper_numbers, "sp1_td_mvp_proof", "proof_size_bytes")),
        "cycle_count": str(_value(paper_numbers, "sp1_td_mvp_proof", "cycle_count")),
    }

    for label, expected in expected_values.items():
        if expected not in paper_text:
            failures.append(f"{label}={expected} missing from paper text")

    sp1_scope = str(_value(paper_numbers, "sp1_td_mvp_proof", "claim_scope"))
    if sp1_scope != "td_mvp_canonical_vector_only":
        failures.append(f"unexpected SP1 proof scope: {sp1_scope}")

    if failures:
        print("paper_number_check_passed = False")
        for failure in failures:
            print(f"failure = {failure}")
        return 1

    print("paper_number_check_passed = True")
    print(f"paper_numbers_path = {PAPER_NUMBERS_PATH.relative_to(ROOT)}")
    print(f"benchmark_rows = {expected_values['benchmark_rows']}")
    print(f"tamper_rows = {expected_values['tamper_rows']}")
    print(f"td_mvp_proving_time_sec = {expected_values['proving_time_sec']}")
    print(f"td_mvp_verification_time_sec = {expected_values['verification_time_sec']}")
    print(f"td_mvp_proof_size_bytes = {expected_values['proof_size_bytes']}")
    print(f"td_mvp_cycle_count = {expected_values['cycle_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
