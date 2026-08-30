import json
import tempfile
import unittest
from pathlib import Path

from scripts.experiments.generate_artifact_manifest import ROOT, build_manifest
from zk_offline_dqn.experiments.report_tables import check_artifact_package_sources


class Phase10ArtifactPackageTests(unittest.TestCase):
    def test_makefile_contains_required_targets(self):
        text = (ROOT / "Makefile").read_text(encoding="utf-8")
        for target in [
            "reproduce-small",
            "reproduce-data-audit",
            "reproduce-sp1-proofs",
            "reproduce-benchmarks",
            "reproduce-tamper",
            "reproduce-paper-tables",
            "artifact-manifest",
        ]:
            self.assertIn(f"{target}:", text)

    def test_docker_files_are_scoped(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8").lower()
        dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").lower()
        self.assertIn("python:3.10-slim-bookworm", dockerfile)
        self.assertNotIn("artifacts/datasets", dockerfile)
        self.assertNotIn("*.proof", dockerfile)
        for pattern in ["artifacts/datasets/", "artifacts/data_sources/", "*.receipt", "*.proof", "target/"]:
            self.assertIn(pattern, dockerignore)
        self.assertNotIn("artifacts/reports/final_ndss/", dockerignore)

    def test_requirements_lock_exists(self):
        self.assertTrue((ROOT / "requirements.lock").exists())

    def test_manifest_generator_schema_and_omissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = build_manifest(Path(tmp))
            for key in [
                "git_commit",
                "generated_at",
                "python_version",
                "platform",
                "commands",
                "files",
                "tables",
                "proof_provenance",
                "dataset_hashes",
                "omitted_artifacts",
            ]:
                self.assertIn(key, manifest)
            text = json.dumps({"files": manifest["files"], "tables": manifest["tables"]}).lower()
            self.assertNotIn("raw_episodes.jsonl", text)
            self.assertNotIn(".receipt", text)
            self.assertNotIn(".proof", text)

    def test_readme_lists_reproduce_commands(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        for command in [
            "make reproduce-small",
            "make reproduce-data-audit",
            "make reproduce-sp1-proofs",
            "make reproduce-benchmarks",
            "make reproduce-tamper",
            "make reproduce-paper-tables",
        ]:
            self.assertIn(command, text)

    def test_paper_sections_match_final_outline(self):
        main = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
        for title in [
            "Introduction",
            "Threat Model",
            "System Overview",
            "Relations",
            "Proof Backend",
            "Training Fragment Proof",
            "Proof-Manifest Chunk-Chain Aggregation",
            "Experiments",
            "Related Work",
            "Limitations",
            "Conclusion",
        ]:
            self.assertIn(title, main + (ROOT / "paper/sections/conclusion.tex").read_text(encoding="utf-8"))

    def test_paper_scopes_recursive_aggregation(self):
        """Recursive aggregation may be claimed, but only within what was measured.

        It is proof-backed for T in {16,32,64} on a CUDA prover. The paper must
        keep the two aggregation modes distinct, state the GPU requirement, and
        keep saying which corners are untested. This replaces a blanket ban that
        no longer matches the artifact.
        """
        text = chr(10).join(path.read_text(encoding="utf-8", errors="replace") for path in (ROOT / "paper/sections").glob("*.tex")).lower()
        # Both modes stay named; recursion must not swallow the manifest rows.
        self.assertIn("proof-manifest chunk-chain aggregation", text)
        self.assertIn("recursive aggregation", text)
        # The limits that make the claim honest.
        self.assertIn("cuda prover", text)
        self.assertIn("untested", text)
        # Corners never measured.
        self.assertNotIn("recursive aggregation at t=128", text)
        self.assertNotIn("plonk child proofs are proof-backed", text)

    def test_report_sources_include_artifact_package(self):
        result = check_artifact_package_sources(ROOT)
        self.assertEqual(result["status"], "passed", result)


if __name__ == "__main__":
    unittest.main()
