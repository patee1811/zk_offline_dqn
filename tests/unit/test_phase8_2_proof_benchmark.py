import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from zk_offline_dqn.experiments.report_tables import check_table2_zk_proof_cost
from zk_offline_dqn.proof_benchmarks.metrics import (
    normalize_metrics,
    proof_size,
    run_measured,
    validate_status,
)
from zk_offline_dqn.proof_benchmarks.merkle_cases import (
    build_membership_path,
    recompute_root,
    write_merkle_membership_case,
)
from zk_offline_dqn.proof_benchmarks.reporting import TABLE2_COLUMNS, write_table2_outputs
from zk_offline_dqn.proof_benchmarks.runner import build_rows, run_benchmark


class Phase82ProofBenchmarkTests(unittest.TestCase):
    def test_metrics_parser_accepts_existing_and_host_field_names(self):
        parsed = normalize_metrics(
            {
                "proving_time_sec": 1.5,
                "verification_time_sec": 0.2,
                "proof_size_bytes": 123,
                "cycle_count": 456,
                "peak_rss_megabytes": 78.0,
                "proof_generated": True,
                "proof_verified": True,
            }
        )
        self.assertEqual(parsed["prove_time_seconds"], 1.5)
        self.assertEqual(parsed["verify_time_seconds"], 0.2)
        self.assertEqual(parsed["proof_size_bytes"], 123)
        self.assertEqual(parsed["cycle_count"], 456)
        self.assertEqual(parsed["peak_rss_mb"], 78.0)

    def test_subprocess_measurement_returns_time_and_memory_fields(self):
        result = run_measured(["python", "-c", "print('ok')"], timeout_seconds=10)
        self.assertEqual(result.returncode, 0)
        self.assertGreaterEqual(result.elapsed_seconds, 0.0)
        self.assertIn("ok", result.stdout)
        self.assertTrue(hasattr(result, "peak_rss_mb"))

    def test_proof_size_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "proof.bin"
            path.write_bytes(b"abcde")
            self.assertEqual(proof_size(path), 5)

    def test_status_vocabulary_validation(self):
        self.assertEqual(validate_status("proof_verified"), "proof_verified")
        with self.assertRaisesRegex(ValueError, "unsupported Phase 8.2 status"):
            validate_status("completed")

    def test_table2_writer_creates_required_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            row = self._proof_row()
            paths = write_table2_outputs([row], tmp, status={"phase": "8.2"})
            for path in paths.values():
                self.assertTrue(path.exists(), path)
            payload = json.loads(paths["json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["table"], "Table 2: ZK proof cost")
            self.assertEqual(list(payload["rows"][0].keys()), TABLE2_COLUMNS)

    def test_unsupported_batch_sizes_are_not_proof_backed(self):
        rows = build_rows(batch_sizes=[1, 4, 8, 16], networks=["tiny"], trace_lengths=[1], dataset_sizes=[])
        unsupported = [row for row in rows if row["Scale Axis"] == "batch_size" and row["Batch Size"] in {4, 8, 16}]
        self.assertEqual({row["Status"] for row in unsupported}, {"not_supported_current_backend"})
        self.assertFalse(any(row["Proof Backed"] for row in unsupported))

    def test_unsupported_small_network_is_not_proof_backed(self):
        rows = build_rows(batch_sizes=[1], networks=["tiny", "small"], trace_lengths=[1], dataset_sizes=[])
        small = [row for row in rows if row["Scale Axis"] == "network" and row["Network"] == "small"]
        self.assertEqual(len(small), 1)
        self.assertEqual(small[0]["Status"], "not_supported_current_backend")
        self.assertFalse(small[0]["Proof Backed"])

    def test_execute_only_trace_lengths_are_not_proof_backed(self):
        rows = build_rows(trace_lengths=[16, 32, 128], batch_sizes=[1], networks=["tiny"], dataset_sizes=[])
        execute_only = [row for row in rows if row["Status"] == "execute_only"]
        self.assertEqual({row["Trace Length"] for row in execute_only}, {16, 32, 128})
        self.assertFalse(any(row["Proof Backed"] for row in execute_only))

    def test_manifest_aggregation_notes_do_not_claim_true_recursion(self):
        rows = build_rows(batch_sizes=[1], networks=["tiny"], trace_lengths=[1], dataset_sizes=[])
        aggregation = [row for row in rows if row["Relation"].startswith("training_aggregation_manifest")]
        self.assertTrue(aggregation)
        for row in aggregation:
            self.assertIn("does not recursively verify child proofs inside SP1", row["Notes"])

    def test_dataset_size_rows_mark_unrefreshed_large_depths_reference_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = build_rows(
                root=Path(tmp),
                dataset_sizes=[1000, 10000, 100000],
                batch_sizes=[1],
                networks=["tiny"],
                trace_lengths=[1],
            )
            dataset_rows = [row for row in rows if row["Scale Axis"] == "dataset_size"]
            by_size = {row["Dataset Size"]: row for row in dataset_rows}
            self.assertEqual(by_size[1000]["Merkle Depth"], 10)
            self.assertEqual(by_size[10000]["Status"], "reference_only")
            self.assertEqual(by_size[100000]["Status"], "reference_only")
            self.assertFalse(by_size[10000]["Proof Backed"])

    def test_synthetic_merkle_tree_path_verifies(self):
        levels = self._synthetic_levels(8)
        path = build_membership_path(levels, 4)
        self.assertEqual(len(path), 3)
        self.assertEqual(recompute_root(levels[0][4], path), levels[-1][0])

    def test_generated_membership_case_serializes_variable_depth(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "dataset"
            dataset_dir.mkdir()
            levels = self._synthetic_levels(8)
            tree = {
                "dataset_id": "synthetic-public-v1",
                "dataset_type": "public_benchmark",
                "dataset_root": levels[-1][0],
                "manifest_hash": "1" * 64,
                "audit_report_hash": "2" * 64,
                "collection_log_final_hash": None,
                "raw_trajectory_hash": "3" * 64,
                "num_leaves": 8,
                "leaf_hashes": levels[0],
                "levels": levels,
            }
            for name in ["dataset_manifest.json", "replay_audit_report.json"]:
                (dataset_dir / name).write_text("{}", encoding="utf-8")
            (dataset_dir / "merkle_tree.json").write_text(json.dumps(tree), encoding="utf-8")
            case_path = Path(tmp) / "case.json"
            info = write_merkle_membership_case(dataset_dir=dataset_dir, case_path=case_path, requested_size=8)
            case = json.loads(case_path.read_text(encoding="utf-8"))
            self.assertEqual(info["merkle_depth"], 3)
            self.assertEqual(len(case["private_witness"]["merkle_path"]), 3)
            self.assertEqual(case["public_inputs"]["dataset_root"], levels[-1][0])

    def test_dataset_size_row_uses_proof_metrics_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prov = root / "artifacts/reports/provenance/sp1/merkle_membership_dataset_10k"
            prov.mkdir(parents=True)
            (prov / "metrics.json").write_text(
                json.dumps(
                    {
                        "proof_generated": True,
                        "proof_verified": True,
                        "prove_time_seconds": 1.0,
                        "verify_time_seconds": 0.1,
                        "proof_size_bytes": 10,
                        "cycle_count": 20,
                        "dataset_size": 10000,
                        "merkle_depth": 14,
                    }
                ),
                encoding="utf-8",
            )
            rows = build_rows(root=root, dataset_sizes=[10000], batch_sizes=[1], networks=["tiny"], trace_lengths=[1])
            row = [r for r in rows if r["Case ID"] == "merkle_membership_dataset_10000"][0]
            self.assertEqual(row["Status"], "proof_verified")
            self.assertTrue(row["Proof Backed"])
            self.assertEqual(row["Merkle Depth"], 14)

    def test_failed_merkle_size_does_not_erase_successful_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok = root / "artifacts/reports/provenance/sp1/merkle_membership_dataset_10k"
            fail = root / "artifacts/reports/provenance/sp1/merkle_membership_dataset_100k"
            ok.mkdir(parents=True)
            fail.mkdir(parents=True)
            (ok / "metrics.json").write_text(json.dumps({"proof_generated": True, "proof_verified": True, "dataset_size": 10000, "merkle_depth": 14}), encoding="utf-8")
            (fail / "metrics.json").write_text(json.dumps({"proof_generated": False, "proof_verified": False, "status": "failed_oom"}), encoding="utf-8")
            rows = build_rows(root=root, dataset_sizes=[10000, 100000], batch_sizes=[1], networks=["tiny"], trace_lengths=[1])
            by_case = {r["Case ID"]: r for r in rows if r["Scale Axis"] == "dataset_size"}
            self.assertEqual(by_case["merkle_membership_dataset_10000"]["Status"], "proof_verified")
            self.assertEqual(by_case["merkle_membership_dataset_100000"]["Status"], "failed_oom")

    def test_proof_binary_paths_are_not_required_in_compact_report(self):
        row = self._proof_row()
        row["Metrics Source"] = "artifacts/reports/provenance/sp1/merkle_membership_dataset_10k/metrics.json"
        row["Notes"] = "proof binary deleted after metrics extraction"
        self.assertNotIn("proof.bin", json.dumps(row))

    def test_report_checker_rejects_missing_table2_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_dir = Path(tmp) / "artifacts/reports/final_ndss"
            table_dir.mkdir(parents=True)
            for suffix in ["csv", "tex", "md"]:
                (table_dir / f"table2_zk_proof_cost.{suffix}").write_text("", encoding="utf-8")
            (table_dir / "table2_zk_proof_cost_status.json").write_text("{}", encoding="utf-8")
            (table_dir / "table2_zk_proof_cost.json").write_text(
                json.dumps({"rows": [{"Relation": "td_mvp", "Status": "proof_verified"}]}),
                encoding="utf-8",
            )
            result = check_table2_zk_proof_cost(Path(tmp))
            self.assertEqual(result["status"], "failed")
            self.assertIn("missing required", result["reason"])

    def test_report_checker_requires_merkle_size_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_dir = Path(tmp) / "artifacts/reports/final_ndss"
            rows = [self._proof_row()]
            write_table2_outputs(rows, table_dir, status={"phase": "8.2"})
            result = check_table2_zk_proof_cost(Path(tmp))
            self.assertEqual(result["status"], "failed")
            self.assertIn("missing Merkle dataset-size row", result["reason"])

    def test_smoke_runner_writes_phase_outputs_under_requested_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = Namespace(
                paper=False,
                smoke=True,
                run_sp1_execute=True,
                run_sp1_prove=False,
                reuse_existing_provenance=True,
                refresh_proof_metrics=False,
                include_execute_only=True,
                include_known_failures=False,
                merkle_depth_proof_scaling=False,
                reuse_phase2_datasets=False,
                regenerate_missing_merkle_datasets=False,
                merkle_dataset_sizes=[1000],
                merkle_source_dataset="D4RL/pointmaze/umaze-v2",
                dataset_sizes=[1000],
                trace_lengths=[1],
                batch_sizes=[1],
                networks=["tiny"],
                aggregation_targets=[32],
                out_dir="artifacts/reports/final_ndss",
            )
            status = run_benchmark(args, root=Path(tmp))
            self.assertTrue((Path(tmp) / "artifacts/reports/final_ndss/table2_zk_proof_cost.json").exists())
            self.assertTrue((Path(tmp) / "artifacts/reports/phase8_2_proof_benchmark/results.jsonl").exists())
            self.assertGreaterEqual(status["row_count"], 1)

    def _proof_row(self):
        return {
            "Category": "core",
            "Relation": "td_mvp",
            "Variant": "canonical",
            "Scale Axis": "relation",
            "Batch Size": 1,
            "Network": "tiny",
            "Trace Length": None,
            "Dataset Size": None,
            "Merkle Depth": None,
            "Aggregation T": None,
            "Proof Backed": True,
            "Status": "proof_verified",
            "Prove Time (s)": 1.0,
            "Verify Time (s)": 0.1,
            "Proof Size (bytes)": 100,
            "Cycle Count": 200,
            "Prover Gas": None,
            "Peak RSS (MB)": 10.0,
            "Max RSS (MB)": 10.0,
            "Backend Version": "0.1.0",
            "SP1 Version": "6.1.0",
            "Git Commit": "abc",
            "Case ID": "td_mvp",
            "Public Inputs SHA256": "0" * 64,
            "Witness Schema SHA256": "1" * 64,
            "Metrics Source": "synthetic",
            "Notes": "",
        }

    def _synthetic_levels(self, n):
        import hashlib

        level = [hashlib.sha256(f"leaf-{i}".encode()).hexdigest() for i in range(n)]
        levels = [level]
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                next_level.append(hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest())
            levels.append(next_level)
            level = next_level
        return levels


if __name__ == "__main__":
    unittest.main()
