import json
import pathlib
import subprocess
import sys
import unittest

from zk_offline_dqn.relations.minibatch_td import check_minibatch_td_artifact
from zk_offline_dqn.verifiers.minibatch_td import (
    DEFAULT_CHECKPOINT_PATH,
    format_minibatch_td_report,
    verify_minibatch_td_artifact,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_ARTIFACT = REPO_ROOT / "artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json"
CANONICAL_ARTIFACT_ARG = "artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json"


def load_canonical_artifact():
    with CANONICAL_ARTIFACT.open("r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical minibatch TD artifact not present")
class MinibatchTdVerifierTests(unittest.TestCase):
    def test_modules_import_normally(self):
        __import__("zk_offline_dqn.relations.minibatch_td")
        __import__("zk_offline_dqn.verifiers.minibatch_td")

    def test_relation_and_verifier_modules_do_not_import_from_scripts(self):
        import zk_offline_dqn.relations.minibatch_td as relation
        import zk_offline_dqn.verifiers.minibatch_td as verifier

        self.assertNotIn("scripts.", pathlib.Path(relation.__file__).read_text())
        self.assertNotIn("scripts.", pathlib.Path(verifier.__file__).read_text())

    def test_relation_accepts_canonical_artifact_items_and_batch(self):
        artifact = load_canonical_artifact()

        result = check_minibatch_td_artifact(
            artifact,
            artifact_path=CANONICAL_ARTIFACT_ARG,
        )

        self.assertTrue(result["relation_passed"])
        self.assertTrue(result["all_items_ok"])
        self.assertTrue(result["batch_size_ok"])
        self.assertTrue(result["distinct_indices_ok"])
        self.assertTrue(result["batch_loss_match"])

    def test_verifier_accepts_canonical_artifact(self):
        artifact = load_canonical_artifact()

        result = verify_minibatch_td_artifact(
            artifact,
            checkpoint_path=DEFAULT_CHECKPOINT_PATH,
            artifact_path=CANONICAL_ARTIFACT_ARG,
        )

        self.assertTrue(result["verification_passed"])
        self.assertTrue(result["checkpoint_sha256_ok"])
        self.assertTrue(result["canonical_checks"]["canonical_state_commitments_ok"])

    def test_script_success_marker_is_preserved(self):
        completed = subprocess.run(
            [sys.executable, "scripts/artifacts_export/verify_minibatch_td_artifact.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("verification_passed = True", completed.stdout)

    def test_script_stdout_matches_formatter_for_canonical_artifact(self):
        artifact = load_canonical_artifact()
        result = verify_minibatch_td_artifact(
            artifact,
            checkpoint_path=DEFAULT_CHECKPOINT_PATH,
            artifact_path=CANONICAL_ARTIFACT_ARG,
        )
        expected_stdout = (
            format_minibatch_td_report(result, CANONICAL_ARTIFACT_ARG)
            + "\n"
        )

        completed = subprocess.run(
            [sys.executable, "scripts/artifacts_export/verify_minibatch_td_artifact.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, expected_stdout)


if __name__ == "__main__":
    unittest.main()
