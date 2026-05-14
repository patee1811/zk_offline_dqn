import copy
import json
import pathlib
import subprocess
import sys
import unittest

from zk_offline_dqn.relations.one_step_sgd_tiny import verify_vector
from zk_offline_dqn.verifiers.one_step_sgd_tiny import (
    format_one_step_sgd_tiny_report,
    verify_one_step_sgd_tiny_test_vector,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_FIXTURE = (
    REPO_ROOT
    / "artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json"
)
CANONICAL_FIXTURE_ARG = (
    "artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json"
)


def load_canonical_fixture():
    with CANONICAL_FIXTURE.open("r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(
    CANONICAL_FIXTURE.exists(), "canonical one-step SGD tiny fixture not present"
)
class OneStepSgdTinyVerifierTests(unittest.TestCase):
    def test_modules_import_normally(self):
        __import__("zk_offline_dqn.relations.one_step_sgd_tiny")
        __import__("zk_offline_dqn.verifiers.one_step_sgd_tiny")

    def test_relation_and_verifier_modules_do_not_import_from_scripts(self):
        import zk_offline_dqn.relations.one_step_sgd_tiny as relation
        import zk_offline_dqn.verifiers.one_step_sgd_tiny as verifier

        self.assertNotIn("scripts.", pathlib.Path(relation.__file__).read_text())
        self.assertNotIn("scripts.", pathlib.Path(verifier.__file__).read_text())

    def test_canonical_fixture_is_accepted(self):
        vector = load_canonical_fixture()

        result = verify_vector(vector)

        self.assertEqual(result["index"], 0)
        self.assertEqual(result["loss_fp"], 556)
        self.assertEqual(result["smooth_l1_grad_fp"], -1000)

    def test_verifier_adapter_accepts_canonical_fixture(self):
        vector = load_canonical_fixture()

        result = verify_one_step_sgd_tiny_test_vector(vector)

        self.assertEqual(result["loss_fp"], 556)

    def test_tampered_learning_rate_is_rejected(self):
        vector = load_canonical_fixture()
        tampered = copy.deepcopy(vector)
        tampered["public"]["learning_rate_fp"] += 1

        with self.assertRaisesRegex(AssertionError, "delta_tensors mismatch"):
            verify_one_step_sgd_tiny_test_vector(tampered)

    def test_script_success_markers_are_preserved(self):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py",
                "--input",
                CANONICAL_FIXTURE_ARG,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("verification_passed = True", completed.stdout)
        self.assertIn("all_one_step_sgd_tiny_ok = True", completed.stdout)

    def test_script_stdout_matches_formatter_for_canonical_fixture(self):
        vector = load_canonical_fixture()
        result = verify_one_step_sgd_tiny_test_vector(vector)
        expected_stdout = (
            format_one_step_sgd_tiny_report(vector, result, CANONICAL_FIXTURE_ARG)
            + "\n"
        )

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py",
                "--input",
                CANONICAL_FIXTURE_ARG,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, expected_stdout)


if __name__ == "__main__":
    unittest.main()
