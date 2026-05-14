import copy
import unittest

from zk_offline_dqn import artifact_schema_versions as old_schemas
from zk_offline_dqn.artifacts import schemas
from zk_offline_dqn.relations.forward_td_mlp import verify_vector as verify_forward_td_mlp
from zk_offline_dqn.relations.minibatch_td import check_minibatch_td_artifact
from zk_offline_dqn.relations.one_step_sgd_tiny import verify_vector as verify_one_step_sgd_tiny
from zk_offline_dqn.relations.td_mvp import verify_test_vector as verify_td_mvp
from zk_offline_dqn.artifacts.io import load_json_artifact


class ArtifactSchemaTests(unittest.TestCase):
    def test_central_constants_match_existing_artifact_constants(self):
        self.assertEqual(
            schemas.SCHEMA_MINIBATCH_TD_V1,
            old_schemas.SCHEMA_MINIBATCH_TD_V1,
        )
        self.assertEqual(
            schemas.SCHEMA_ONE_STEP_UPDATE_V1,
            old_schemas.SCHEMA_ONE_STEP_UPDATE_V1,
        )
        self.assertEqual(
            schemas.SCHEMA_SHORT_TRACE_UPDATE_V2,
            old_schemas.SCHEMA_SHORT_TRACE_UPDATE_V2,
        )

    def test_central_test_vector_constants_match_existing_strings(self):
        self.assertEqual(schemas.SCHEMA_TD_MVP_TEST_VECTOR_V1, "td_mvp_test_vector_v1")
        self.assertEqual(
            schemas.SCHEMA_TD_MVP_BATCH_TEST_VECTOR_V1,
            "td_mvp_batch_test_vector_v1",
        )
        self.assertEqual(schemas.SCHEMA_FORWARD_TD_MLP_V1, "forward_td_mlp_v1")
        self.assertEqual(
            schemas.SCHEMA_ONE_STEP_SGD_TINY_V1,
            "one_step_sgd_tiny_v1",
        )

    def test_require_schema_version_preserves_missing_error(self):
        old_error = None
        new_error = None

        try:
            old_schemas.require_schema_version({}, schemas.SCHEMA_MINIBATCH_TD_V1, "x.json")
        except ValueError as exc:
            old_error = str(exc)

        try:
            schemas.require_schema_version({}, schemas.SCHEMA_MINIBATCH_TD_V1, "x.json")
        except ValueError as exc:
            new_error = str(exc)

        self.assertEqual(new_error, old_error)

    def test_require_schema_version_preserves_wrong_version_error(self):
        artifact = {"schema_version": "wrong"}
        old_error = None
        new_error = None

        try:
            old_schemas.require_schema_version(
                artifact,
                schemas.SCHEMA_ONE_STEP_UPDATE_V1,
                "x.json",
            )
        except ValueError as exc:
            old_error = str(exc)

        try:
            schemas.require_schema_version(
                artifact,
                schemas.SCHEMA_ONE_STEP_UPDATE_V1,
                "x.json",
            )
        except ValueError as exc:
            new_error = str(exc)

        self.assertEqual(new_error, old_error)

    def test_wrong_minibatch_schema_still_rejected(self):
        artifact = load_json_artifact("artifacts/minibatch_td_from_dataset.json")
        tampered = copy.deepcopy(artifact)
        tampered["schema_version"] = "wrong"

        with self.assertRaises(ValueError):
            check_minibatch_td_artifact(tampered, artifact_path="tampered.json")

    def test_wrong_td_mvp_schema_still_rejected(self):
        vector = load_json_artifact("zk_backend/test_vectors/td_mvp_case_0.json")
        tampered = copy.deepcopy(vector)
        tampered["schema_version"] = "wrong"

        with self.assertRaises(ValueError):
            verify_td_mvp(tampered)

    def test_wrong_forward_td_mlp_schema_still_rejected(self):
        vector = load_json_artifact(
            "artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json"
        )
        tampered = copy.deepcopy(vector)
        tampered["schema_version"] = "wrong"

        with self.assertRaises(AssertionError):
            verify_forward_td_mlp(tampered)

    def test_wrong_one_step_sgd_tiny_schema_still_rejected(self):
        vector = load_json_artifact(
            "artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json"
        )
        tampered = copy.deepcopy(vector)
        tampered["schema_version"] = "wrong"

        with self.assertRaises(AssertionError):
            verify_one_step_sgd_tiny(tampered)


if __name__ == "__main__":
    unittest.main()
