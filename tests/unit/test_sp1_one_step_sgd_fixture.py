import os
import shutil
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.backends.sp1.one_step_sgd_tiny import (
    DEFAULT_CASE_PATH,
    cargo_command,
    load_case,
    run_cargo,
    verify_case_reference,
)


class Sp1OneStepSgdFixtureTests(unittest.TestCase):
    def test_fixture_matches_python_oracle(self):
        result = verify_case_reference(load_case())
        self.assertTrue(result.accepted, result.reason)

    def test_cargo_execute_command_shape(self):
        command = cargo_command()
        self.assertIn("one-step-sgd-tiny-host", command)
        self.assertIn("--execute", command)
        self.assertIn(str(DEFAULT_CASE_PATH), command)

    def test_execute_mode_opt_in(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        result = run_cargo(mode="execute", timeout=1200)
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
            for name in ["public_inputs.json", "witness_schema.json", "metrics.json", "verify_report.json"]:
                self.assertTrue((Path(tmp) / name).exists(), name)


if __name__ == "__main__":
    unittest.main()

