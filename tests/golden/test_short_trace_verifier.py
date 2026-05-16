import json
import os
import pathlib
import subprocess
import sys
import unittest

from zk_offline_dqn.verifiers.short_trace import (
    DEFAULT_ARTIFACT_PATH,
    format_short_trace_report,
    verify_short_trace_artifact,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_ARTIFACT = REPO_ROOT / DEFAULT_ARTIFACT_PATH
CANONICAL_ARTIFACT_ARG = DEFAULT_ARTIFACT_PATH
CANONICAL_MERKLE_PATH = "artifacts/fixtures/membership/cartpole_dqn_eps010_merkle.json"
CANONICAL_INITIAL_CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"
CANONICAL_FINAL_CHECKPOINT_PATH = (
    "artifacts/fixtures/short_trace/short_trace_work/step_1_post_synced_4_5_6_7.pt"
)
CANONICAL_WORK_DIR = "artifacts/fixtures/short_trace/short_trace_work"


def load_canonical_artifact():
    with CANONICAL_ARTIFACT.open("r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical short-trace artifact not present")
class ShortTraceVerifierTests(unittest.TestCase):
    def test_modules_import_normally(self):
        __import__("zk_offline_dqn.relations.short_trace")
        __import__("zk_offline_dqn.verifiers.short_trace")

    def test_relation_and_verifier_modules_do_not_import_from_scripts(self):
        import zk_offline_dqn.relations.short_trace as relation
        import zk_offline_dqn.verifiers.short_trace as verifier

        relation_text = pathlib.Path(relation.__file__).read_text()
        verifier_text = pathlib.Path(verifier.__file__).read_text()

        self.assertNotIn("scripts.", relation_text)
        self.assertNotIn("scripts/", relation_text)
        self.assertNotIn("scripts.", verifier_text)
        self.assertNotIn("scripts/", verifier_text)

    def test_relation_module_does_not_call_subprocess(self):
        import zk_offline_dqn.relations.short_trace as relation

        relation_text = pathlib.Path(relation.__file__).read_text()
        self.assertNotIn("subprocess", relation_text)

    def test_verifier_accepts_canonical_artifact(self):
        artifact = load_canonical_artifact()

        result = verify_short_trace_artifact(
            artifact,
            artifact_path=CANONICAL_ARTIFACT_ARG,
            merkle_path=CANONICAL_MERKLE_PATH,
            initial_checkpoint_path=CANONICAL_INITIAL_CHECKPOINT_PATH,
            final_checkpoint_path=CANONICAL_FINAL_CHECKPOINT_PATH,
            work_dir=CANONICAL_WORK_DIR,
        )

        self.assertTrue(result["verification_passed"])
        self.assertTrue(result["all_step_verifications_ok"])
        self.assertTrue(result["all_chain_ok"])
        self.assertTrue(result["target_sync_state_ok"])

    def test_script_success_marker_is_preserved(self):
        env = os.environ.copy()
        env.update(
            {
                "SHORT_TRACE_ARTIFACT_PATH": CANONICAL_ARTIFACT_ARG,
                "SHORT_TRACE_MERKLE_PATH": CANONICAL_MERKLE_PATH,
                "SHORT_TRACE_INITIAL_CHECKPOINT_PATH": CANONICAL_INITIAL_CHECKPOINT_PATH,
                "SHORT_TRACE_FINAL_CHECKPOINT_PATH": CANONICAL_FINAL_CHECKPOINT_PATH,
                "SHORT_TRACE_WORK_DIR": CANONICAL_WORK_DIR,
            }
        )
        completed = subprocess.run(
            [sys.executable, "scripts/artifacts_export/verify_short_trace_update_artifact.py"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("verification_passed = True", completed.stdout)

    def test_script_stdout_matches_formatter_for_canonical_artifact(self):
        artifact = load_canonical_artifact()
        result = verify_short_trace_artifact(
            artifact,
            artifact_path=CANONICAL_ARTIFACT_ARG,
            merkle_path=CANONICAL_MERKLE_PATH,
            initial_checkpoint_path=CANONICAL_INITIAL_CHECKPOINT_PATH,
            final_checkpoint_path=CANONICAL_FINAL_CHECKPOINT_PATH,
            work_dir=CANONICAL_WORK_DIR,
        )
        expected_stdout = format_short_trace_report(
            result,
            CANONICAL_ARTIFACT_ARG,
        ) + "\n"

        env = os.environ.copy()
        env.update(
            {
                "SHORT_TRACE_ARTIFACT_PATH": CANONICAL_ARTIFACT_ARG,
                "SHORT_TRACE_MERKLE_PATH": CANONICAL_MERKLE_PATH,
                "SHORT_TRACE_INITIAL_CHECKPOINT_PATH": CANONICAL_INITIAL_CHECKPOINT_PATH,
                "SHORT_TRACE_FINAL_CHECKPOINT_PATH": CANONICAL_FINAL_CHECKPOINT_PATH,
                "SHORT_TRACE_WORK_DIR": CANONICAL_WORK_DIR,
            }
        )
        completed = subprocess.run(
            [sys.executable, "scripts/artifacts_export/verify_short_trace_update_artifact.py"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, expected_stdout)


if __name__ == "__main__":
    unittest.main()
