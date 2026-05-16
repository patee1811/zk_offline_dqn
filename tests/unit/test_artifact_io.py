import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.artifacts.io import load_json_artifact, write_json_artifact


class ArtifactIoTests(unittest.TestCase):
    def test_load_json_artifact_reads_existing_artifact(self):
        artifact = load_json_artifact("artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json")

        self.assertEqual(artifact["schema_version"], "minibatch_td_v1")
        self.assertIn("public", artifact)
        self.assertIn("items", artifact)

    def test_load_json_artifact_reads_test_vector(self):
        vector = load_json_artifact("zk_backend/test_vectors/td_mvp_case_0.json")

        self.assertEqual(vector["schema_version"], "td_mvp_test_vector_v1")
        self.assertIn("public", vector)
        self.assertIn("private", vector)

    def test_write_json_artifact_preserves_existing_format_convention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "artifact.json"
            write_json_artifact(path, {"schema_version": "example", "value": 1})

            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.endswith("\n"))
            self.assertIn('  "schema_version": "example"', text)
            self.assertEqual(load_json_artifact(path)["value"], 1)


if __name__ == "__main__":
    unittest.main()
