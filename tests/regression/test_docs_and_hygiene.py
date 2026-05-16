from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class DocsAndHygieneTests(unittest.TestCase):
    def test_reviewer_docs_exist(self) -> None:
        for relative in [
            "README.md",
            "docs/architecture.md",
            "docs/reproducibility.md",
            "docs/archive/internal_manifests/legacy_status.md",
            "docs/archive/internal_manifests/reporting_policy.md",
        ]:
            self.assertTrue((ROOT / relative).exists(), relative)

    def test_phase7_report_files_exist_when_report_dir_exists(self) -> None:
        report_dir = ROOT / "artifacts/reports/final_ndss"
        if not report_dir.exists():
            self.skipTest("Phase 7 report directory has not been generated")

        for name in [
            "paper_numbers.json",
            "benchmark_summary.csv",
            "tamper_summary.csv",
            "sp1_status.json",
            "benchmark_snapshot.md",
        ]:
            self.assertTrue((report_dir / name).exists(), name)

    def test_gitignore_contains_generated_output_rules(self) -> None:
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in [
            "kaggle_phase6_zkp_drl/",
            "kaggle_phase6_zkp_drl_backup/",
            "kaggle_phase6_outputs/",
            "__pycache__/",
            ".pytest_cache/",
            ".mypy_cache/",
            "artifacts/benchmarks/*_python_smoke/",
            "*_phase6b_workspace.zip",
        ]:
            self.assertIn(pattern, text)

    def test_final_reports_remain_trackable(self) -> None:
        lines = set((ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        self.assertNotIn("artifacts/", lines)
        self.assertNotIn("artifacts/reports/", lines)
        self.assertNotIn("artifacts/reports/final_ndss/", lines)
        self.assertIn("!artifacts/reports/final_ndss/", lines)
        self.assertIn("!artifacts/reports/final_ndss/**", lines)


if __name__ == "__main__":
    unittest.main()
