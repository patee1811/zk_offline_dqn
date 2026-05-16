import copy
import json
import pathlib
import unittest

from zk_offline_dqn.verifiers.one_step_update import (
    DEFAULT_CHECKPOINT_PATH,
    DEFAULT_MERKLE_PATH,
    DEFAULT_POST_CHECKPOINT_PATH,
    verify_one_step_update_artifact,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_ARTIFACT = REPO_ROOT / "artifacts/fixtures/one_step_update/one_step_update_artifact.json"


def load_canonical_artifact():
    with CANONICAL_ARTIFACT.open("r", encoding="utf-8") as f:
        return json.load(f)


def mutate_first_numeric_leaf(obj, delta=1.0):
    if isinstance(obj, dict):
        for key in obj:
            if mutate_first_numeric_leaf(obj[key], delta=delta):
                return True
        return False
    if isinstance(obj, list):
        for i, value in enumerate(obj):
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                obj[i] = value + delta
                return True
            if mutate_first_numeric_leaf(value, delta=delta):
                return True
        return False
    return False


@unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical one-step update artifact not present")
class OneStepUpdateTamperTests(unittest.TestCase):
    def verify_tampered(self, artifact):
        return verify_one_step_update_artifact(
            artifact,
            artifact_path="artifacts/fixtures/one_step_update/one_step_update_artifact.json",
            merkle_path=DEFAULT_MERKLE_PATH,
            checkpoint_path=DEFAULT_CHECKPOINT_PATH,
            post_checkpoint_path=DEFAULT_POST_CHECKPOINT_PATH,
        )

    def test_wrong_post_model_commitment_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["public"]["post_online_state_dict_sha256"] = "0" * 64

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(
            result["canonical_checks"]["post_online_state_dict_sha256_ok"]
        )

    def test_wrong_batch_loss_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["update_witness"]["batch_loss_fp"] += 1

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["batch_loss_match"])

    def test_wrong_gradient_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        self.assertTrue(
            mutate_first_numeric_leaf(tampered["update_witness"]["gradient_tensors"])
        )

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["gradient_match_all"])

    def test_wrong_delta_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        self.assertTrue(
            mutate_first_numeric_leaf(tampered["update_witness"]["delta_tensors"])
        )

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["delta_tensor_match_all"])

    def test_wrong_post_checkpoint_sha_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["public"]["post_checkpoint_sha256"] = "0" * 64

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["post_checkpoint_ok"])


if __name__ == "__main__":
    unittest.main()
