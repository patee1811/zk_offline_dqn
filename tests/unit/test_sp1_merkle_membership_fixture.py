import os
import shutil
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.backends.sp1.merkle_membership import (
    DEFAULT_CASE_PATH,
    cargo_command,
    load_case,
    run_cargo,
    verify_case_reference,
)


class Sp1MerkleMembershipFixtureTests(unittest.TestCase):
    def test_fixture_reference_check_passes_and_public_inputs_are_complete(self):
        case = load_case()
        result = verify_case_reference(case)
        self.assertTrue(result.accepted, result.reason)
        public = case["public_inputs"]
        for key in [
            "dataset_root",
            "manifest_hash",
            "audit_report_hash",
            "collection_log_final_hash",
            "raw_trajectory_hash",
            "leaf_hash",
            "leaf_index",
        ]:
            self.assertIn(key, public)
            self.assertIsNotNone(public[key])

    def test_cargo_execute_command_shape(self):
        command = cargo_command()
        self.assertIn("merkle-membership-host", command)
        self.assertIn("--execute", command)
        self.assertIn(str(DEFAULT_CASE_PATH), command)

    def test_provenance_artifacts_are_complete_when_claimed(self):
        provenance_dir = (
            DEFAULT_CASE_PATH.parents[2]
            / "artifacts"
            / "reports"
            / "provenance"
            / "sp1"
            / "merkle_membership"
        )
        required = [
            "public_inputs.json",
            "witness_schema.json",
            "metrics.json",
            "verify_report.json",
            "tamper_report.json",
            "proof_artifact_policy.json",
        ]
        for name in required:
            self.assertTrue((provenance_dir / name).exists(), name)

        metrics = load_case(provenance_dir / "metrics.json")
        self.assertTrue(metrics["proof_generated"])
        self.assertTrue(metrics["proof_verified"])
        self.assertIsInstance(metrics["cycle_count"], int)
        self.assertEqual(metrics["relation"], "merkle_membership")

    def test_execute_mode_opt_in(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        result = run_cargo(mode="execute", timeout=900)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("execution_ok = true", result.stdout)

    def test_proof_mode_opt_in(self):
        if os.environ.get("RUN_SP1_PROVE") != "1":
            self.skipTest("SP1 proof test is opt-in with RUN_SP1_PROVE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cargo(mode="prove", out_dir=tmp, timeout=3600)
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            self.assertTrue((Path(tmp) / "public_inputs.json").exists())
            self.assertTrue((Path(tmp) / "witness_schema.json").exists())
            self.assertTrue((Path(tmp) / "metrics.json").exists())
            self.assertTrue((Path(tmp) / "verify_report.json").exists())


if __name__ == "__main__":
    unittest.main()
