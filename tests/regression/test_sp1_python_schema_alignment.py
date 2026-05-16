from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

from zk_offline_dqn.artifacts import schemas
from zk_offline_dqn.backends.sp1 import commands, fixtures, metrics
from zk_offline_dqn.relations.td_mvp import verify_test_vector


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Sp1PythonSchemaAlignmentTests(unittest.TestCase):
    def load_json(self, path: pathlib.Path) -> dict:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_sp1_helper_modules_import_and_fixture_paths_exist(self) -> None:
        known = fixtures.known_fixtures()
        self.assertGreaterEqual(len(known), 3)
        for fixture in fixtures.regression_critical_fixtures():
            self.assertTrue(
                (REPO_ROOT / fixture.path).exists(),
                f"missing regression-critical SP1 fixture: {fixture.path}",
            )

    def test_td_mvp_sp1_vector_passes_python_relation(self) -> None:
        vector_path = REPO_ROOT / "zk_backend/test_vectors/td_mvp_case_0.json"
        result = verify_test_vector(self.load_json(vector_path))
        self.assertTrue(result["verification_passed"])
        self.assertTrue(result["leaf_hash_ok"])
        self.assertTrue(result["merkle_ok"])
        self.assertTrue(result["target_ok"])
        self.assertTrue(result["loss_ok"])

    def test_schema_constants_match_known_sp1_vectors(self) -> None:
        expected_by_path = {
            pathlib.Path("zk_backend/test_vectors/td_mvp_case_0.json"):
                schemas.SCHEMA_TD_MVP_TEST_VECTOR_V1,
            pathlib.Path(
                "artifacts/fixtures/forward_td_mlp/"
                "forward_td_mlp_batch_size_1.json"
            ): schemas.SCHEMA_FORWARD_TD_MLP_V1,
            pathlib.Path(
                "artifacts/fixtures/one_step_sgd_tiny/"
                "one_step_sgd_tiny_valid.json"
            ): schemas.SCHEMA_ONE_STEP_SGD_TINY_V1,
        }
        for relative_path, expected in expected_by_path.items():
            vector = self.load_json(REPO_ROOT / relative_path)
            if "schema_version" in vector:
                self.assertEqual(vector["schema_version"], expected)

    def test_command_builders_return_argv_lists(self) -> None:
        command_groups = [
            commands.local_python_sp1_smoke_commands(),
            commands.kaggle_setup_check_commands(),
            commands.kaggle_notebook_validation_commands(),
            commands.wsl2_linux_sp1_commands(),
        ]
        for group in command_groups:
            self.assertIsInstance(group, list)
            self.assertGreater(len(group), 0)
            for command in group:
                self.assertIsInstance(command, list)
                self.assertGreater(len(command), 0)
                self.assertTrue(all(isinstance(part, str) for part in command))

        self.assertIn("--execute", commands.sp1_execute_command())
        self.assertIn("--prove", commands.sp1_prove_command())

    def test_metrics_missing_status_does_not_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = pathlib.Path(tmpdir) / "missing_summary.json"
            result = metrics.load_json_summary(missing)
            self.assertEqual(result["status"], "missing")
            matrix = metrics.load_benchmark_matrix(pathlib.Path(tmpdir))
            self.assertEqual(matrix["status"], "missing")


if __name__ == "__main__":
    unittest.main()
