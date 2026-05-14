import copy
import json
import pathlib
import subprocess
import sys
import unittest

from zk_offline_dqn.relations.td_mvp import verify_test_vector
from zk_offline_dqn.verifiers.td_mvp import (
    format_td_mvp_report,
    verify_td_mvp_test_vector,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_VECTOR = REPO_ROOT / "zk_backend/test_vectors/td_mvp_case_0.json"


def load_canonical_vector():
    with CANONICAL_VECTOR.open("r", encoding="utf-8") as f:
        return json.load(f)


class TdMvpVerifierTests(unittest.TestCase):
    def test_modules_import_normally(self):
        __import__("zk_offline_dqn.relations.td_mvp")
        __import__("zk_offline_dqn.verifiers.td_mvp")

    def test_canonical_vector_is_accepted(self):
        vector = load_canonical_vector()

        result = verify_test_vector(vector)

        self.assertTrue(result["verification_passed"])
        self.assertTrue(result["target_ok"])
        self.assertTrue(result["td_error_ok"])
        self.assertTrue(result["loss_ok"])

    def test_verifier_adapter_accepts_canonical_vector(self):
        vector = load_canonical_vector()

        result = verify_td_mvp_test_vector(vector)

        self.assertTrue(result["verification_passed"])

    def test_tampered_loss_is_rejected(self):
        vector = load_canonical_vector()
        tampered = copy.deepcopy(vector)
        tampered["private"]["td_witness"]["loss_fp"] += 1

        result = verify_td_mvp_test_vector(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["loss_ok"])

    def test_script_success_marker_is_preserved(self):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/artifacts_export/verify_td_mvp_test_vector.py",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("verification_passed = True", completed.stdout)

    def test_script_stdout_matches_formatter_for_canonical_vector(self):
        vector = load_canonical_vector()
        result = verify_td_mvp_test_vector(vector)
        expected_stdout = (
            format_td_mvp_report(
                result,
                pathlib.Path("zk_backend/test_vectors/td_mvp_case_0.json"),
            )
            + "\n"
        )

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/artifacts_export/verify_td_mvp_test_vector.py",
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
