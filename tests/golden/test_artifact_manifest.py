import unittest
from pathlib import Path

from zk_offline_dqn.artifacts.field_roles import FIELD_ROLES
from zk_offline_dqn.artifacts.manifest import (
    BENCHMARK_FIXTURE,
    CANONICAL_FIXTURE,
    known_artifacts,
    paths_by_classification,
    regression_critical_paths,
)
from zk_offline_dqn.artifacts.schemas import (
    SCHEMA_FORWARD_TD_MLP_V1,
    SCHEMA_MINIBATCH_TD_V1,
    SCHEMA_ONE_STEP_SGD_TINY_V1,
    SCHEMA_ONE_STEP_UPDATE_V1,
    SCHEMA_SHORT_TRACE_UPDATE_V2,
    SCHEMA_TD_MVP_BATCH_TEST_VECTOR_V1,
    SCHEMA_TD_MVP_TEST_VECTOR_V1,
)


class ArtifactManifestTests(unittest.TestCase):
    def test_regression_critical_manifest_paths_exist(self):
        missing = [
            path
            for path in regression_critical_paths()
            if not Path(path).exists()
        ]
        self.assertEqual(missing, [])

    def test_manifest_contains_canonical_and_benchmark_paths(self):
        canonical_paths = set(paths_by_classification(CANONICAL_FIXTURE))
        benchmark_paths = set(paths_by_classification(BENCHMARK_FIXTURE))

        self.assertIn("artifacts/minibatch_td_from_dataset.json", canonical_paths)
        self.assertIn("artifacts/one_step_update_artifact.json", canonical_paths)
        self.assertIn("artifacts/short_trace_update_artifact.json", canonical_paths)
        self.assertIn("zk_backend/test_vectors/td_mvp_case_0.json", canonical_paths)
        self.assertIn(
            "artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json",
            benchmark_paths,
        )
        self.assertIn(
            "artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json",
            benchmark_paths,
        )

    def test_manifest_entries_have_required_keys(self):
        for item in known_artifacts():
            self.assertIn("path", item)
            self.assertIn("classification", item)
            self.assertIn("artifact_type", item)

    def test_field_role_maps_cover_existing_schema_families(self):
        for schema_version in [
            SCHEMA_MINIBATCH_TD_V1,
            SCHEMA_ONE_STEP_UPDATE_V1,
            SCHEMA_SHORT_TRACE_UPDATE_V2,
            SCHEMA_TD_MVP_TEST_VECTOR_V1,
            SCHEMA_TD_MVP_BATCH_TEST_VECTOR_V1,
            SCHEMA_FORWARD_TD_MLP_V1,
            SCHEMA_ONE_STEP_SGD_TINY_V1,
        ]:
            self.assertIn(schema_version, FIELD_ROLES)
            self.assertIn("public", FIELD_ROLES[schema_version])
            self.assertIn("private", FIELD_ROLES[schema_version])
            self.assertIn("items", FIELD_ROLES[schema_version])
            self.assertIn("steps", FIELD_ROLES[schema_version])
            self.assertIn("notes", FIELD_ROLES[schema_version])
            self.assertIn("debug", FIELD_ROLES[schema_version])


if __name__ == "__main__":
    unittest.main()
