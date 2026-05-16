"""Check release-readiness invariants without network or SP1 proof generation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FINAL_REPORTS = [
    Path("artifacts/reports/final_ndss/paper_numbers.json"),
    Path("artifacts/reports/final_ndss/benchmark_summary.csv"),
    Path("artifacts/reports/final_ndss/tamper_summary.csv"),
    Path("artifacts/reports/final_ndss/sp1_status.json"),
    Path("artifacts/reports/final_ndss/benchmark_snapshot.md"),
]

REQUIRED_DOCS = [
    Path("README.md"),
    Path("docs/reproducibility.md"),
    Path("docs/archive/internal_manifests/reporting_policy.md"),
    Path("docs/archive/internal_manifests/legacy_status.md"),
    Path("docs/paper_alignment_audit.md"),
    Path("docs/release_checklist.md"),
    Path("docs/archive/internal_manifests/artifact_release_manifest.md"),
    Path("paper/README.md"),
]

KAGGLE_LOCAL_PREFIXES = [
    "kaggle_phase6_outputs",
    "kaggle_phase6_zkp_drl",
    "kaggle_phase6_zkp_drl_backup",
]

GENERATED_TRACKED_TOKENS = [
    "python_smoke",
    "kaggle",
    "tmp",
    "cache",
]


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run_git(args: List[str]) -> List[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def has_provenance(node: Any) -> bool:
    return isinstance(node, dict) and isinstance(node.get("provenance"), dict)


def is_git_ignored(path: Path) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", path.as_posix()],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def check_required_paths(paths: Iterable[Path], label: str) -> List[str]:
    failures: List[str] = []
    for path in paths:
        if not (ROOT / path).exists():
            failures.append(f"missing_{label}: {path.as_posix()}")
    return failures


def check_paper_numbers() -> List[str]:
    failures: List[str] = []
    paper_numbers_path = ROOT / "artifacts/reports/final_ndss/paper_numbers.json"
    if not paper_numbers_path.exists():
        return ["missing paper_numbers.json"]

    data = load_json(paper_numbers_path)
    required = [
        ("regression", "all_passed"),
        ("regression", "num_checks"),
        ("final_ndss_existing", "benchmark_rows"),
        ("final_ndss_existing", "tamper_rows"),
        ("sp1_td_mvp_proof", "proof_generated"),
        ("sp1_td_mvp_proof", "proof_verified"),
        ("sp1_td_mvp_proof", "proving_time_sec"),
        ("sp1_td_mvp_proof", "verification_time_sec"),
        ("sp1_td_mvp_proof", "proof_size_bytes"),
        ("sp1_td_mvp_proof", "cycle_count"),
    ]
    for keys in required:
        node: Any = data
        for key in keys:
            node = node.get(key) if isinstance(node, dict) else None
        if not has_provenance(node):
            failures.append("missing_provenance: " + ".".join(keys))

    scope = data.get("sp1_td_mvp_proof", {}).get("claim_scope")
    if scope != "td_mvp_canonical_vector_only":
        failures.append(f"bad_sp1_claim_scope: {scope}")
    return failures


def check_git_hygiene() -> Dict[str, Any]:
    tracked_kaggle: List[str] = []
    for prefix in KAGGLE_LOCAL_PREFIXES:
        tracked_kaggle.extend(run_git(["ls-files", prefix]))

    tracked_artifacts = run_git(["ls-files", "artifacts"])
    tracked_generated = []
    for path in tracked_artifacts:
        if path.startswith("artifacts/reports/provenance/sp1/"):
            continue
        if any(token in path.lower() for token in GENERATED_TRACKED_TOKENS):
            tracked_generated.append(path)

    final_report_status: Dict[str, Dict[str, Any]] = {}
    tracked_files = set(run_git(["ls-files"]))
    for report in FINAL_REPORTS:
        final_report_status[report.as_posix()] = {
            "exists": (ROOT / report).exists(),
            "tracked": report.as_posix() in tracked_files,
            "ignored": is_git_ignored(report),
        }

    return {
        "tracked_kaggle_outputs": tracked_kaggle,
        "tracked_generated_artifacts": tracked_generated,
        "final_report_status": final_report_status,
    }


def main() -> int:
    failures: List[str] = []
    warnings: List[str] = []
    failures.extend(check_required_paths(FINAL_REPORTS, "final_report"))
    failures.extend(check_required_paths(REQUIRED_DOCS, "doc"))
    failures.extend(check_paper_numbers())

    hygiene = check_git_hygiene()
    if hygiene["tracked_kaggle_outputs"]:
        failures.append(
            "tracked_kaggle_outputs: " + ", ".join(hygiene["tracked_kaggle_outputs"])
        )
    if hygiene["tracked_generated_artifacts"]:
        failures.append(
            "tracked_generated_artifacts: "
            + ", ".join(hygiene["tracked_generated_artifacts"])
        )
    for path, status in hygiene["final_report_status"].items():
        if status["ignored"]:
            failures.append(f"final_report_ignored: {path}")
        if not status["tracked"]:
            warnings.append(f"final_report_present_but_untracked: {path}")

    status = "passed" if not failures else "failed"
    result = {
        "release_readiness": status,
        "failures": failures,
        "warnings": warnings,
        "git_hygiene": hygiene,
        "sp1_claim_scope": "td_mvp_canonical_vector_only",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
