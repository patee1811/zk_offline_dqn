import json
import pathlib
import subprocess
import sys
import unittest

from zk_offline_dqn.verifiers.one_step_update import (
    DEFAULT_CHECKPOINT_PATH,
    DEFAULT_MERKLE_PATH,
    DEFAULT_POST_CHECKPOINT_PATH,
    format_one_step_update_report,
    verify_one_step_update_artifact,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_ARTIFACT = REPO_ROOT / "artifacts/fixtures/one_step_update/one_step_update_artifact.json"
CANONICAL_ARTIFACT_ARG = "artifacts/fixtures/one_step_update/one_step_update_artifact.json"


def load_canonical_artifact():
    with CANONICAL_ARTIFACT.open("r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical one-step update artifact not present")
class OneStepUpdateVerifierTests(unittest.TestCase):
    def test_modules_import_normally(self):
        __import__("zk_offline_dqn.relations.one_step_update")
        __import__("zk_offline_dqn.verifiers.one_step_update")

    def test_relation_and_verifier_modules_do_not_import_from_scripts(self):
        import zk_offline_dqn.relations.one_step_update as relation
        import zk_offline_dqn.verifiers.one_step_update as verifier

        self.assertNotIn("scripts.", pathlib.Path(relation.__file__).read_text())
        self.assertNotIn("scripts.", pathlib.Path(verifier.__file__).read_text())

    def test_verifier_accepts_canonical_artifact(self):
        artifact = load_canonical_artifact()

        result = verify_one_step_update_artifact(
            artifact,
            artifact_path=CANONICAL_ARTIFACT_ARG,
            merkle_path=DEFAULT_MERKLE_PATH,
            checkpoint_path=DEFAULT_CHECKPOINT_PATH,
            post_checkpoint_path=DEFAULT_POST_CHECKPOINT_PATH,
        )

        self.assertTrue(result["verification_passed"])
        self.assertTrue(result["batch_loss_match"])
        self.assertTrue(result["gradient_match_all"])
        self.assertTrue(result["delta_tensor_match_all"])
        self.assertTrue(result["sgd_update_match_all"])

    def test_script_success_marker_is_preserved(self):
        completed = subprocess.run(
            [sys.executable, "scripts/artifacts_export/verify_one_step_update_artifact.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("verification_passed = True", completed.stdout)

    def test_script_stdout_matches_formatter_for_canonical_artifact(self):
        artifact = load_canonical_artifact()
        result = verify_one_step_update_artifact(
            artifact,
            artifact_path=CANONICAL_ARTIFACT_ARG,
            merkle_path=DEFAULT_MERKLE_PATH,
            checkpoint_path=DEFAULT_CHECKPOINT_PATH,
            post_checkpoint_path=DEFAULT_POST_CHECKPOINT_PATH,
        )
        expected_stdout = (
            format_one_step_update_report(result, CANONICAL_ARTIFACT_ARG)
            + "\n"
        )

        completed = subprocess.run(
            [sys.executable, "scripts/artifacts_export/verify_one_step_update_artifact.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, expected_stdout)


if __name__ == "__main__":
    unittest.main()
