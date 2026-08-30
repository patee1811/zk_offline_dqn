"""Scan paper-facing text for unsupported overclaims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
PAPER_NUMBERS_PATH = ROOT / "artifacts/reports/final_ndss/paper_numbers.json"
TABLE2_PATH = ROOT / "artifacts/reports/final_ndss/table2_zk_proof_cost.json"

SCANNED_ROOTS = [
    ROOT / "README.md",
    ROOT / "docs",
    ROOT / "paper",
]

EXCLUDED_RELATIVE_PATHS = {
    "docs/paper_alignment_audit.md",
}

BANNED_PHRASES = [
    "end-to-end proof of dqn training",
    "proves offline rl training",
    "all relations are proven in sp1",
    "proves selected relations in an sp1",
    "sp1 proofs are recorded for",
    "distinct replay minibatch td is proved in sp1",
    "model-grounded forward-td is proved in sp1",
    "one-step sgd update is proved in sp1",
    "full sp1 proof runs",
    "public benchmark honest collection proof",
    "privacy-preserving full dataset collection",
]

NEGATED_PHRASES = [
    "proof of full dqn training",
    "prove offline dqn training",
    "prove full dqn training",
    "proof coverage for every relation",
    # Recursive aggregation is now proof-backed at T in {16,32,64}, so the broad
    # phrase is no longer forbidden. What remains unproven is guarded instead:
    # T=128, PLONK child proofs, and recursion on a CPU prover.
    "recursive aggregation at t=128",
    "recursive aggregation for t=128",
    "plonk child proofs are proof-backed",
    "recursive aggregation on cpu",
    "honest public collection proof",
    "adam proof",
    "batch-size 4/8/16 training proof",
    "batch-size 4/8/16 proof-backed",
    "k={16,32,128} are proof-backed",
    "k={16, 32, 128} are proof-backed",
    "k=16/32/128 proof-backed",
    "all d4rl tasks",
    "table 3 proves training",
]

ALLOWED_NEGATION_MARKERS = [
    "untested",
    "not ",
    "does not ",
    "do not ",
    "no ",
    "without ",
    "unsupported",
    "future work",
    "not claimed",
]


def iter_text_files() -> Iterable[Path]:
    for root in SCANNED_ROOTS:
        if root.is_file():
            yield root
        elif root.is_dir():
            for suffix in ("*.md", "*.tex"):
                yield from root.rglob(suffix)


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_negated(line: str, phrase: str) -> bool:
    index = line.find(phrase)
    if index < 0:
        return False
    prefix = line[max(0, index - 80) : index]
    return any(marker in prefix for marker in ALLOWED_NEGATION_MARKERS)


def scan_claims() -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for path in iter_text_files():
        if path.name in {"main.aux", "main.log"}:
            continue
        if rel(path) in EXCLUDED_RELATIVE_PATHS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for phrase in BANNED_PHRASES:
                if phrase in lowered:
                    findings.append(
                        {
                            "path": rel(path),
                            "line": lineno,
                            "phrase": phrase,
                            "text": line.strip(),
                        }
                    )
            for phrase in NEGATED_PHRASES:
                if phrase in lowered and not is_negated(lowered, phrase):
                    findings.append(
                        {
                            "path": rel(path),
                            "line": lineno,
                            "phrase": phrase,
                            "text": line.strip(),
                        }
                    )
    return findings


def load_paper_numbers() -> Dict[str, Any]:
    with PAPER_NUMBERS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_table2() -> Dict[str, Any]:
    with TABLE2_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def has_provenance(node: Any) -> bool:
    return isinstance(node, dict) and isinstance(node.get("provenance"), dict)


def check_paper_numbers_provenance() -> List[str]:
    failures: List[str] = []
    if not PAPER_NUMBERS_PATH.exists():
        return [f"missing {rel(PAPER_NUMBERS_PATH)}"]

    data = load_paper_numbers()
    required_paths = [
        ("regression", "all_passed"),
        ("regression", "num_checks"),
        ("final_ndss_existing", "benchmark_rows"),
        ("final_ndss_existing", "tamper_rows"),
        ("sp1_td_mvp_proof", "cargo_test_status"),
        ("sp1_td_mvp_proof", "execute_status"),
        ("sp1_td_mvp_proof", "prove_status"),
        ("sp1_td_mvp_proof", "proof_generated"),
        ("sp1_td_mvp_proof", "proof_verified"),
        ("sp1_td_mvp_proof", "proving_time_sec"),
        ("sp1_td_mvp_proof", "verification_time_sec"),
        ("sp1_td_mvp_proof", "proof_size_bytes"),
        ("sp1_td_mvp_proof", "cycle_count"),
    ]
    for path in required_paths:
        node: Any = data
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
        if not has_provenance(node):
            failures.append("missing provenance for " + ".".join(path))

    return failures


def check_table2_proof_coverage() -> List[str]:
    if not TABLE2_PATH.exists():
        return [f"missing {rel(TABLE2_PATH)}"]

    data = load_table2()
    rows = data.get("rows", [])
    if not isinstance(rows, list):
        return [f"invalid rows in {rel(TABLE2_PATH)}"]

    proof_verified = {
        str(row.get("Case ID"))
        for row in rows
        if row.get("Proof Backed") is True and row.get("Status") == "proof_verified"
    }
    required_cases = {
        "td_mvp",
        "merkle_membership",
        "forward_td_mlp",
        "one_step_sgd_tiny",
        "short_trace",
        "training_update_batch1",
        "training_fragment_k1",
        "training_fragment_k4",
        "training_fragment_k8",
        "training_aggregation_manifest_t32",
        "training_aggregation_manifest_t64",
        "training_aggregation_manifest_t128",
        "merkle_membership_dataset_1000",
        "merkle_membership_dataset_10000",
        "merkle_membership_dataset_100000",
    }
    missing = sorted(required_cases - proof_verified)
    if missing:
        return ["missing proof_verified Table 2 cases: " + ", ".join(missing)]
    return []


def main() -> int:
    claim_findings = scan_claims()
    provenance_failures = check_paper_numbers_provenance()
    table2_failures = check_table2_proof_coverage()

    if claim_findings or provenance_failures or table2_failures:
        print("paper_claim_check_passed = False")
        for finding in claim_findings:
            print(
                "overclaim = "
                f"{finding['path']}:{finding['line']}: {finding['phrase']}: {finding['text']}"
            )
        for failure in provenance_failures:
            print(f"provenance_failure = {failure}")
        for failure in table2_failures:
            print(f"table2_failure = {failure}")
        return 1

    print("paper_claim_check_passed = True")
    print(f"paper_numbers_path = {rel(PAPER_NUMBERS_PATH)}")
    print(f"table2_proof_cost_path = {rel(TABLE2_PATH)}")
    print("sp1_claim_scope = supported proof_verified Table 2 cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
