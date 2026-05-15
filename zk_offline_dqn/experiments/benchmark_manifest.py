"""Benchmark and report source manifest for paper-facing summaries.

This module is descriptive only. It does not run benchmarks, move fixtures, or
mutate artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class BenchmarkReportEntry:
    entry_id: str
    command: str
    fixture_path: str | None
    expected_output_path: str
    status_type: str
    paper_relevance: str
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


BENCHMARK_REPORT_ENTRIES: tuple[BenchmarkReportEntry, ...] = (
    BenchmarkReportEntry(
        entry_id="td_mvp",
        command=(
            "python -m zk_offline_dqn.cli.main verify td-mvp "
            "--input zk_backend/test_vectors/td_mvp_case_0.json"
        ),
        fixture_path="zk_backend/test_vectors/td_mvp_case_0.json",
        expected_output_path="artifacts/regression_summary.json",
        status_type="canonical",
        paper_relevance="Canonical TD MVP Python verifier and SP1 host input.",
        required=True,
    ),
    BenchmarkReportEntry(
        entry_id="distinct_td",
        command=(
            "python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 "
            "--out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke"
        ),
        fixture_path="artifacts/benchmarks/distinct_td_sp1_python_smoke/fixtures",
        expected_output_path="artifacts/benchmarks/distinct_td_sp1_python_smoke/summary.json",
        status_type="smoke",
        paper_relevance="Python-side smoke for distinct/minibatch TD relation.",
        required=True,
    ),
    BenchmarkReportEntry(
        entry_id="forward_td_mlp",
        command=(
            "python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 "
            "--out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke"
        ),
        fixture_path=(
            "artifacts/benchmarks/forward_td_mlp_sp1/fixtures/"
            "forward_td_mlp_batch_size_1.json"
        ),
        expected_output_path="artifacts/benchmarks/forward_td_mlp_sp1_python_smoke/summary.json",
        status_type="smoke",
        paper_relevance="Python-side smoke for forward-TD MLP relation.",
        required=True,
    ),
    BenchmarkReportEntry(
        entry_id="one_step_sgd_tiny",
        command=(
            "python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 "
            "--out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke"
        ),
        fixture_path=(
            "artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/"
            "one_step_sgd_tiny_valid.json"
        ),
        expected_output_path="artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke/summary.json",
        status_type="smoke",
        paper_relevance="Python-side smoke for one-step SGD tiny relation.",
        required=True,
    ),
    BenchmarkReportEntry(
        entry_id="minibatch_td",
        command="python -m unittest tests.golden.test_minibatch_td_verifier",
        fixture_path="artifacts/minibatch_td_from_dataset.json",
        expected_output_path="artifacts/regression_summary.json",
        status_type="canonical",
        paper_relevance="Canonical minibatch TD verifier coverage through regression.",
        required=True,
    ),
    BenchmarkReportEntry(
        entry_id="one_step_update",
        command="python -m unittest tests.golden.test_one_step_update_verifier",
        fixture_path="artifacts/one_step_update_artifact.json",
        expected_output_path="artifacts/regression_summary.json",
        status_type="canonical",
        paper_relevance="Canonical one-step update verifier coverage through regression.",
        required=True,
    ),
    BenchmarkReportEntry(
        entry_id="short_trace",
        command="python -m unittest tests.golden.test_short_trace_verifier",
        fixture_path="artifacts/short_trace_update_artifact.json",
        expected_output_path="artifacts/regression_summary.json",
        status_type="canonical",
        paper_relevance="Canonical short-trace verifier coverage through regression.",
        required=True,
    ),
    BenchmarkReportEntry(
        entry_id="sp1_td_mvp_execute",
        command="cargo run --release -p td-mvp-host -- --execute",
        fixture_path="zk_backend/test_vectors/td_mvp_case_0.json",
        expected_output_path=(
            "kaggle_phase6_outputs/zk_offline_dqn_phase6b_archive/"
            "artifacts/reports/kaggle_sp1_validation_summary.json"
        ),
        status_type="optional",
        paper_relevance="Kaggle SP1 execute validation for TD MVP canonical vector only.",
        required=False,
    ),
    BenchmarkReportEntry(
        entry_id="sp1_td_mvp_prove",
        command="cargo run --release -p td-mvp-host -- --prove",
        fixture_path="zk_backend/test_vectors/td_mvp_case_0.json",
        expected_output_path=(
            "kaggle_phase6_outputs/zk_offline_dqn_phase6b_archive/"
            "artifacts/reports/kaggle_sp1_validation_summary.json"
        ),
        status_type="proof_required",
        paper_relevance="Kaggle SP1 proof validation for TD MVP canonical vector only.",
        required=False,
    ),
)


def benchmark_entries() -> List[BenchmarkReportEntry]:
    return list(BENCHMARK_REPORT_ENTRIES)


def entries_as_dicts() -> List[Dict[str, Any]]:
    return [entry.to_dict() for entry in BENCHMARK_REPORT_ENTRIES]


def _resolve(root: Path, raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def check_sources(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    entries: List[Dict[str, Any]] = []
    missing_required: List[str] = []
    missing_optional: List[str] = []
    missing_proof_required: List[str] = []

    for entry in BENCHMARK_REPORT_ENTRIES:
        output = _resolve(base, entry.expected_output_path)
        fixture = _resolve(base, entry.fixture_path)
        output_exists = output.exists() if output is not None else False
        fixture_exists = fixture.exists() if fixture is not None else True
        exists = output_exists and fixture_exists

        row = entry.to_dict()
        row.update(
            {
                "fixture_exists": fixture_exists,
                "expected_output_exists": output_exists,
                "exists": exists,
            }
        )
        entries.append(row)

        if not exists:
            if entry.required:
                missing_required.append(entry.entry_id)
            elif entry.status_type == "proof_required":
                missing_proof_required.append(entry.entry_id)
            else:
                missing_optional.append(entry.entry_id)

    return {
        "status": "passed" if not missing_required else "failed",
        "entries": entries,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "missing_proof_required": missing_proof_required,
    }
