import tempfile
import unittest
from pathlib import Path

from scripts.experiments.check_paper_claims import scan_claims
from scripts.experiments.check_theorem_artifact_map import ROOT, check_theorem_artifact_map


class TheoremArtifactMapTests(unittest.TestCase):
    def test_theorem_map_file_exists(self):
        self.assertTrue((ROOT / "docs/theorem_artifact_map.md").exists())

    def test_all_8_theorem_entries_exist(self):
        text = (ROOT / "docs/theorem_artifact_map.md").read_text(encoding="utf-8")
        for idx in range(1, 9):
            self.assertIn(f"Theorem {idx}", text)

    def test_theorem_7_is_proof_manifest_not_true_recursion(self):
        text = "\n".join(
            [
                (ROOT / "docs/theorem_artifact_map.md").read_text(encoding="utf-8"),
                (ROOT / "paper/sections/formal_statements.tex").read_text(encoding="utf-8"),
            ]
        ).lower()
        self.assertIn("proof-manifest", text)
        self.assertIn("chunk-chain", text)
        self.assertIn("not true recursive", text)
        self.assertNotIn("true recursive aggregation soundness", text)

    def test_non_theorems_section_lists_boundaries(self):
        text = (ROOT / "docs/theorem_artifact_map.md").read_text(encoding="utf-8").lower()
        self.assertIn("non-theorems", text)
        self.assertIn("not true recursive aggregation", text)
        self.assertIn("full dqn training", text)
        self.assertIn("honest public dataset collection", text)

    def test_threat_model_mentions_required_boundaries(self):
        text = (ROOT / "paper/sections/threat_model.tex").read_text(encoding="utf-8").lower()
        for term in [
            "prover",
            "verifier",
            "public input",
            "private witness",
            "reward",
            "public minari/d4rl",
            "honest collection",
        ]:
            self.assertIn(term, text)

    def test_theorem_artifact_validator_passes(self):
        result = check_theorem_artifact_map(ROOT)
        self.assertEqual(result["status"], "passed", result)

    def test_paper_claim_checker_rejects_known_bad_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            bad = root / "README.md"
            bad.write_text("We prove Offline DQN training.\n", encoding="utf-8")
            old_roots = list(__import__("scripts.experiments.check_paper_claims", fromlist=["SCANNED_ROOTS"]).SCANNED_ROOTS)
            module = __import__("scripts.experiments.check_paper_claims", fromlist=["SCANNED_ROOTS"])
            try:
                module.SCANNED_ROOTS[:] = [bad, root / "docs"]
                findings = scan_claims()
            finally:
                module.SCANNED_ROOTS[:] = old_roots
            self.assertTrue(any("prove offline dqn training" in item["phrase"] for item in findings))


if __name__ == "__main__":
    unittest.main()

