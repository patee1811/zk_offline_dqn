import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.backends.sp1.training_aggregation import (
    cargo_command,
    case_path_for_target,
    load_case,
    run_cargo,
    verify_case_reference,
)
from zk_offline_dqn.relations.training_aggregation import (
    CHUNK_RELATION_ID,
    GROTH16_CHILD_PROOF_MODE,
    PLONK_CHILD_PROOF_MODE,
    RECURSIVE_AGGREGATION_MODE,
    generate_recursive_case,
    recompute_roots,
)


PROVENANCE_FILES = [
    "public_inputs.json",
    "witness_schema.json",
    "metrics.json",
    "verify_report.json",
    "tamper_report.json",
    "proof_artifact_policy.json",
    "aggregation_manifest.json",
    "chunk_manifest.json",
]
RECURSIVE_PROVENANCE_FILES = [*PROVENANCE_FILES, "recursive_child_proof_manifest.json"]


class Sp1TrainingAggregationFixtureTests(unittest.TestCase):
    def test_t32_t64_t128_fixtures_load_and_match_reference(self):
        for target, chunk_count in [(32, 4), (64, 8), (128, 16)]:
            with self.subTest(target=target):
                case = load_case(case_path_for_target(target))
                self.assertEqual(case["schema_version"], "sp1_training_aggregation_case_v1")
                self.assertEqual(case["public_inputs"]["relation"], "training_aggregation")
                self.assertEqual(case["public_inputs"]["aggregation_mode"], "proof_manifest_chain")
                self.assertEqual(case["public_inputs"]["chunk_count"], chunk_count)
                result = verify_case_reference(case)
                self.assertTrue(result.accepted, result.reason)

    def test_reference_recomputes_chunk_chain_and_roots(self):
        for target in [32, 64, 128]:
            with self.subTest(target=target):
                case = load_case(case_path_for_target(target))
                public = case["public_inputs"]
                chunks = case["private_witness"]["chunks"]
                roots = recompute_roots(chunks)
                self.assertEqual(public["aggregate_root"], roots["aggregate_root"])
                self.assertEqual(public["chunk_public_inputs_root"], roots["chunk_public_inputs_root"])
                self.assertEqual(public["chunk_proof_root"], roots["chunk_proof_root"])
                self.assertEqual(public["chunk_verify_report_root"], roots["chunk_verify_report_root"])
                for index, chunk in enumerate(chunks):
                    self.assertEqual(chunk["chunk_id"], index)
                    self.assertEqual(chunk["step_end"] - chunk["step_start"], 8)
                    self.assertEqual(chunk["relation_id"], CHUNK_RELATION_ID)
                    self.assertEqual(chunk["dataset_root"], public["dataset_root"])
                    self.assertEqual(chunk["config_hash"], public["config_hash"])
                    if index + 1 < len(chunks):
                        next_chunk = chunks[index + 1]
                        self.assertEqual(chunk["step_end"], next_chunk["step_start"])
                        self.assertEqual(
                            chunk["output_checkpoint_hash"], next_chunk["input_checkpoint_hash"]
                        )
                        self.assertEqual(
                            chunk["output_target_checkpoint_hash"],
                            next_chunk["input_target_checkpoint_hash"],
                        )

    def test_recursive_t32_generated_case_validates_metadata(self):
        case = generate_recursive_case(32)
        self.assertEqual(case["public_inputs"]["aggregation_mode"], RECURSIVE_AGGREGATION_MODE)
        self.assertEqual(case["public_inputs"]["chunk_count"], 4)
        self.assertEqual(len(case["private_witness"]["child_proofs"]), 4)
        result = verify_case_reference(case)
        self.assertTrue(result.accepted, result.reason)
        roots = recompute_roots(case["private_witness"]["chunks"], recursive=True)
        self.assertEqual(case["public_inputs"]["chunk_vkey_root"], roots["chunk_vkey_root"])
        self.assertTrue(result.public_output["child_proof_verification_inside_guest"])

    def test_snark_recursive_t16_t32_generated_cases_validate_metadata(self):
        for proof_mode in [GROTH16_CHILD_PROOF_MODE, PLONK_CHILD_PROOF_MODE]:
            for target, chunk_count in [(16, 2), (32, 4)]:
                with self.subTest(proof_mode=proof_mode, target=target):
                    case = generate_recursive_case(target, child_proof_mode=proof_mode)
                    public = case["public_inputs"]
                    self.assertEqual(public["aggregation_mode"], RECURSIVE_AGGREGATION_MODE)
                    self.assertEqual(public["child_proof_mode"], proof_mode)
                    self.assertEqual(public["chunk_count"], chunk_count)
                    self.assertNotIn("expected_child_vkey_digest_words", public)
                    result = verify_case_reference(case)
                    self.assertTrue(result.accepted, result.reason)

    def test_cargo_execute_command_shape(self):
        command = cargo_command(case_path=case_path_for_target(32))
        self.assertIn("training-aggregation-host", command)
        self.assertIn("--execute", command)
        self.assertIn("--mode", command)
        self.assertIn("proof_manifest_chain", command)

    def test_execute_mode_opt_in(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        result = run_cargo(case_path=case_path_for_target(32), mode="execute", timeout=1200)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("execution_ok = true", result.stdout)

    def test_proof_mode_opt_in(self):
        if os.environ.get("RUN_SP1_PROVE") != "1":
            self.skipTest("SP1 proof test is opt-in with RUN_SP1_PROVE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cargo(
                case_path=case_path_for_target(32),
                mode="prove",
                out_dir=tmp,
                timeout=3600,
            )
            self.assertEqual(result.returncode, 0, result.stderr[-2000:])
            for name in ["public_inputs.json", "witness_schema.json", "metrics.json", "verify_report.json"]:
                self.assertTrue((Path(tmp) / name).exists(), name)

    def test_committed_provenance_if_present_is_complete(self):
        for target in [32, 64, 128]:
            provenance_dir = Path(f"artifacts/reports/provenance/sp1/training_aggregation_t{target}")
            if not provenance_dir.exists():
                continue
            with self.subTest(target=target):
                for name in PROVENANCE_FILES:
                    self.assertTrue((provenance_dir / name).exists(), name)
                metrics = json.loads((provenance_dir / "metrics.json").read_text(encoding="utf-8"))
                self.assertEqual(metrics["relation"], "training_aggregation")
                self.assertTrue(metrics["proof_generated"])
                self.assertTrue(metrics["proof_verified"])
                self.assertFalse(metrics["child_proof_verification_inside_guest"])

    def test_recursive_committed_provenance_if_present_is_complete(self):
        for target in [32, 64, 128]:
            provenance_dir = Path(
                f"artifacts/reports/provenance/sp1/training_aggregation_recursive_t{target}"
            )
            if not provenance_dir.exists():
                continue
            with self.subTest(target=target):
                for name in RECURSIVE_PROVENANCE_FILES:
                    self.assertTrue((provenance_dir / name).exists(), name)
                metrics = json.loads((provenance_dir / "metrics.json").read_text(encoding="utf-8"))
                self.assertEqual(metrics["aggregation_mode"], "recursive_sp1")
                self.assertTrue(metrics["proof_generated"])
                self.assertTrue(metrics["proof_verified"])
                self.assertTrue(metrics["child_proof_verification_inside_guest"])

        for mode in ["groth16", "plonk"]:
            for target in [16, 32]:
                provenance_dir = Path(
                    f"artifacts/reports/provenance/sp1/training_aggregation_{mode}_t{target}"
                )
                if not provenance_dir.exists():
                    continue
                with self.subTest(mode=mode, target=target):
                    for name in RECURSIVE_PROVENANCE_FILES:
                        self.assertTrue((provenance_dir / name).exists(), name)
                    metrics = json.loads((provenance_dir / "metrics.json").read_text(encoding="utf-8"))
                    self.assertEqual(metrics["aggregation_mode"], "recursive_sp1")
                    self.assertTrue(metrics["proof_generated"])
                    self.assertTrue(metrics["proof_verified"])
                    self.assertTrue(metrics["child_proof_verification_inside_guest"])


if __name__ == "__main__":
    unittest.main()
