import copy
import json
import pathlib
import subprocess
import sys
import unittest

from zk_offline_dqn.relations.forward_td_mlp import verify_vector
from zk_offline_dqn.verifiers.forward_td_mlp import (
    format_forward_td_mlp_report,
    verify_forward_td_mlp_test_vector,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_FIXTURE = (
    REPO_ROOT
    / "artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json"
)
CANONICAL_FIXTURE_ARG = (
    "artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json"
)


def load_canonical_fixture():
    with CANONICAL_FIXTURE.open("r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(CANONICAL_FIXTURE.exists(), "canonical forward-TD MLP fixture not present")
class ForwardTdMlpVerifierTests(unittest.TestCase):
    def test_modules_import_normally(self):
        __import__("zk_offline_dqn.relations.forward_td_mlp")
        __import__("zk_offline_dqn.verifiers.forward_td_mlp")

    def test_canonical_fixture_is_accepted(self):
        vector = load_canonical_fixture()

        output = verify_vector(vector)

        self.assertEqual(output["batch_size"], 1)
        self.assertEqual(output["claimed_batch_loss_fp"], 496)
        self.assertEqual(output["items"][0]["next_action_online"], 1)

    def test_verifier_adapter_accepts_canonical_fixture(self):
        vector = load_canonical_fixture()

        output = verify_forward_td_mlp_test_vector(vector)

        self.assertEqual(output["items"][0]["loss_fp"], 496)

    def test_tampered_claimed_batch_loss_is_rejected(self):
        vector = load_canonical_fixture()
        tampered = copy.deepcopy(vector)
        tampered["public"]["claimed_batch_loss_fp"] += 1

        with self.assertRaisesRegex(AssertionError, "claimed_batch_loss_fp mismatch"):
            verify_forward_td_mlp_test_vector(tampered)

    def test_script_keeps_helper_imports_for_existing_dependents(self):
        from scripts.artifacts_export.verify_forward_td_mlp_test_vector import (
            assert_equal,
            verify_forward_trace,
            verify_item_membership,
        )

        self.assertTrue(callable(assert_equal))
        self.assertTrue(callable(verify_forward_trace))
        self.assertTrue(callable(verify_item_membership))

    def test_script_success_markers_are_preserved(self):
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/artifacts_export/verify_forward_td_mlp_test_vector.py",
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
        self.assertIn("all_forward_td_mlp_ok = True", completed.stdout)

    def test_script_stdout_matches_formatter_for_canonical_fixture(self):
        vector = load_canonical_fixture()
        output = verify_forward_td_mlp_test_vector(vector)
        expected_stdout = (
            format_forward_td_mlp_report(vector, output, CANONICAL_FIXTURE_ARG)
            + "\n"
        )

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/artifacts_export/verify_forward_td_mlp_test_vector.py",
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
