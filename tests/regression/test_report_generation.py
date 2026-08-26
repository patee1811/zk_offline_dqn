from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.experiments import benchmark_manifest, paper_numbers, report_tables


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATHS = [
    ROOT / "zk_backend/test_vectors/td_mvp_case_0.json",
    ROOT
    / "artifacts/fixtures/forward_td_mlp/forward_td_mlp_batch_size_1.json",
    ROOT
    / "artifacts/fixtures/one_step_sgd_tiny/one_step_sgd_tiny_valid.json",
]

# benchmark_manifest marks these required, but run_full_regression.py writes
# them and .gitignore excludes them, so a fresh clone has none. Their absence
# is a missing prerequisite, not a regression.
GENERATED_SOURCES = [
    ROOT / "artifacts/regression_summary.json",
    ROOT / "artifacts/benchmarks/distinct_td_sp1_python_smoke/summary.json",
    ROOT / "artifacts/benchmarks/forward_td_mlp_sp1_python_smoke/summary.json",
    ROOT / "artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke/summary.json",
]


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReportGenerationTests(unittest.TestCase):
    def require_generated_sources(self) -> None:
        missing = [
            path.relative_to(ROOT).as_posix()
            for path in GENERATED_SOURCES
            if not path.exists()
        ]
        if missing:
            self.skipTest(
                "run scripts/experiments/run_full_regression.py first; "
                f"missing generated sources: {missing}"
            )

    def test_manifest_entries_are_importable(self) -> None:
        entries = benchmark_manifest.benchmark_entries()
        entry_ids = {entry.entry_id for entry in entries}
        self.assertIn("td_mvp", entry_ids)
        self.assertIn("sp1_td_mvp_prove", entry_ids)

    def test_report_generation_outputs_files_with_provenance(self) -> None:
        self.require_generated_sources()
        before = {path: file_digest(path) for path in FIXTURE_PATHS if path.exists()}
        with tempfile.TemporaryDirectory() as tmp:
            outputs = report_tables.generate_reports(Path(tmp), root=ROOT)
            for path in outputs.values():
                self.assertTrue((ROOT / path).exists() or Path(path).exists())

            paper_path = Path(tmp) / "paper_numbers.json"
            paper = json.loads(paper_path.read_text(encoding="utf-8"))
            self.assertIn("regression", paper)
            self.assertIn("sp1_td_mvp_proof", paper)
            self.assertIn("provenance", paper["regression"]["all_passed"])
            self.assertIn("provenance", paper["sp1_td_mvp_proof"]["prove_status"])

            sp1_status = paper["sp1_td_mvp_proof"]
            if paper_numbers.latest_kaggle_validation_summary(ROOT) is not None:
                self.assertEqual(sp1_status["status"], "validated")
                self.assertIs(
                    sp1_status["proof_generated"]["value"],
                    True,
                )
                self.assertIs(
                    sp1_status["proof_verified"]["value"],
                    True,
                )
            else:
                self.assertIn(sp1_status["status"], {"missing", "not_validated"})

        after = {path: file_digest(path) for path in before}
        self.assertEqual(before, after)

    def test_source_check_allows_optional_missing_only(self) -> None:
        self.require_generated_sources()
        result = report_tables.check_report_sources(ROOT)
        self.assertIn(result["status"], {"passed", "failed"})
        self.assertIsInstance(result["missing_optional"], list)
        self.assertIsInstance(result["missing_proof_required"], list)
        self.assertEqual(result["missing_required"], [])


if __name__ == "__main__":
    unittest.main()
