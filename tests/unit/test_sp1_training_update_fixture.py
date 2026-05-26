import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.backends.sp1.training_update import (
    DEFAULT_CASE_PATH,
    cargo_command,
    load_case,
    run_cargo,
    verify_case_reference,
)
from zk_offline_dqn.relations.training_update import compute_training_update


PROVENANCE_DIR = Path("artifacts/reports/provenance/sp1/training_update")
PROVENANCE_FILES = [
    "public_inputs.json",
    "witness_schema.json",
    "metrics.json",
    "verify_report.json",
    "tamper_report.json",
    "proof_artifact_policy.json",
]


class Sp1TrainingUpdateFixtureTests(unittest.TestCase):
    def test_fixture_loads_and_matches_reference(self):
        case = load_case()
        self.assertEqual(case["schema_version"], "sp1_training_update_case_v1")
        self.assertEqual(case["public_inputs"]["relation"], "training_update")
        self.assertEqual(case["public_inputs"]["batch_size"], 1)
        result = verify_case_reference(case)
        self.assertTrue(result.accepted, result.reason)

    def test_reference_recomputes_training_update_components(self):
        case = load_case()
        computed = compute_training_update(case)
        public = case["public_inputs"]
        self.assertEqual(public["claimed_q_online_action"], computed["q_online_action"])
        self.assertEqual(public["claimed_q_target_next"], computed["q_target_next"])
        self.assertEqual(public["claimed_td_target"], computed["td_target"])
        self.assertEqual(public["claimed_td_error"], computed["td_error"])
        self.assertEqual(public["claimed_loss"], computed["loss"])
        self.assertEqual(public["claimed_gradient_hash"], computed["gradient_hash"])
        self.assertEqual(public["claimed_update_hash"], computed["update_hash"])
        self.assertEqual(public["checkpoint_hash_t_plus_1"], computed["checkpoint_hash_t_plus_1"])
        self.assertEqual(case["private_witness"]["online_model_t_plus_1"], computed["post_model"])

    def test_cargo_execute_command_shape(self):
        command = cargo_command()
        self.assertIn("training-update-host", command)
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

    def test_committed_provenance_is_complete(self):
        for name in PROVENANCE_FILES:
            self.assertTrue((PROVENANCE_DIR / name).exists(), name)
        metrics = json.loads((PROVENANCE_DIR / "metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(metrics["relation"], "training_update")
        self.assertEqual(metrics["batch_size"], 1)
        self.assertTrue(metrics["proof_generated"])
        self.assertTrue(metrics["proof_verified"])
        self.assertIsInstance(metrics["proof_size_bytes"], int)
        self.assertIsInstance(metrics["cycle_count"], int)
        tamper = json.loads((PROVENANCE_DIR / "tamper_report.json").read_text(encoding="utf-8"))
        self.assertTrue(tamper["all_passed"])


if __name__ == "__main__":
    unittest.main()
