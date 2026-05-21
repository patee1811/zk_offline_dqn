import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.backends.sp1.training_fragment import (
    cargo_command,
    case_path_for_k,
    load_case,
    run_cargo,
    verify_case_reference,
)
from zk_offline_dqn.relations.training_fragment import lcg_sample_index, recompute_fragment


PROVENANCE_FILES = [
    "public_inputs.json",
    "witness_schema.json",
    "metrics.json",
    "verify_report.json",
    "tamper_report.json",
    "proof_artifact_policy.json",
]


class Sp1TrainingFragmentFixtureTests(unittest.TestCase):
    def test_k1_k4_k8_fixtures_load_and_match_reference(self):
        for k in [1, 4, 8]:
            with self.subTest(k=k):
                case = load_case(case_path_for_k(k))
                self.assertEqual(case["schema_version"], "sp1_training_fragment_case_v1")
                self.assertEqual(case["public_inputs"]["relation"], "training_fragment")
                self.assertEqual(case["public_inputs"]["num_steps"], k)
                self.assertEqual(case["public_inputs"]["batch_size"], 1)
                result = verify_case_reference(case)
                self.assertTrue(result.accepted, result.reason)

    def test_reference_recomputes_every_step_and_trace_hashes(self):
        for k in [1, 4, 8]:
            with self.subTest(k=k):
                case = load_case(case_path_for_k(k))
                public = case["public_inputs"]
                computed = recompute_fragment(case)
                self.assertEqual(public["final_checkpoint_hash"], computed["final_checkpoint_hash"])
                self.assertEqual(public["final_target_checkpoint_hash"], computed["final_target_checkpoint_hash"])
                self.assertEqual(public["checkpoint_chain_hash"], computed["checkpoint_chain_hash"])
                self.assertEqual(public["minibatch_indices_hash"], computed["minibatch_indices_hash"])
                self.assertEqual(public["loss_trace_hash"], computed["loss_trace_hash"])
                self.assertEqual(public["gradient_trace_hash"], computed["gradient_trace_hash"])
                self.assertEqual(public["update_trace_hash"], computed["update_trace_hash"])
                self.assertEqual(public["trace_hash"], computed["trace_hash"])
                for step in case["private_witness"]["steps"]:
                    idx = step["step_id"]
                    expected_index = lcg_sample_index(
                        public["sampler_seed"], idx, public["dataset_size"]
                    )
                    self.assertEqual(step["sample_index"], expected_index)
                    self.assertEqual(step["leaf_index"], expected_index)
                    self.assertEqual(
                        step["checkpoint_hash_after"],
                        computed["checkpoint_chain"][idx]["checkpoint_hash_after"],
                    )
                    if idx + 1 < len(case["private_witness"]["steps"]):
                        next_step = case["private_witness"]["steps"][idx + 1]
                        self.assertEqual(step["checkpoint_hash_after"], next_step["checkpoint_hash_before"])

    def test_k4_fixture_includes_target_sync(self):
        case = load_case(case_path_for_k(4))
        computed = recompute_fragment(case)
        self.assertEqual(computed["target_sync_events"], 1)
        self.assertTrue(case["private_witness"]["steps"][3]["intermediates"]["target_sync_applied"])
        self.assertEqual(
            case["private_witness"]["steps"][3]["target_model_after"],
            case["private_witness"]["steps"][3]["online_model_after"],
        )

    def test_cargo_execute_command_shape(self):
        command = cargo_command(case_path=case_path_for_k(1), max_steps=1)
        self.assertIn("training-fragment-host", command)
        self.assertIn("--execute", command)
        self.assertIn("--max-steps", command)

    def test_execute_mode_opt_in(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        result = run_cargo(case_path=case_path_for_k(1), mode="execute", max_steps=1, timeout=1200)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("execution_ok = true", result.stdout)

    def test_proof_mode_opt_in(self):
        if os.environ.get("RUN_SP1_PROVE") != "1":
            self.skipTest("SP1 proof test is opt-in with RUN_SP1_PROVE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cargo(
                case_path=case_path_for_k(1),
                mode="prove",
                out_dir=tmp,
                max_steps=1,
                timeout=3600,
            )
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            for name in ["public_inputs.json", "witness_schema.json", "metrics.json", "verify_report.json"]:
                self.assertTrue((Path(tmp) / name).exists(), name)

    def test_committed_provenance_if_present_is_complete(self):
        for k in [1, 4, 8, 32, 128]:
            provenance_dir = Path(f"artifacts/reports/provenance/sp1/training_fragment_k{k}")
            if not provenance_dir.exists():
                continue
            with self.subTest(k=k):
                for name in PROVENANCE_FILES:
                    self.assertTrue((provenance_dir / name).exists(), name)
                metrics = json.loads((provenance_dir / "metrics.json").read_text(encoding="utf-8"))
                self.assertEqual(metrics["relation"], "training_fragment")
                self.assertEqual(metrics["num_steps"], k)
                self.assertTrue(metrics["proof_generated"])
                self.assertTrue(metrics["proof_verified"])
                tamper = json.loads((provenance_dir / "tamper_report.json").read_text(encoding="utf-8"))
                self.assertTrue(tamper["all_passed"])


if __name__ == "__main__":
    unittest.main()
