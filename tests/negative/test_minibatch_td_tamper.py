import copy
import json
import pathlib
import unittest

from zk_offline_dqn.verifiers.minibatch_td import (
    DEFAULT_CHECKPOINT_PATH,
    verify_minibatch_td_artifact,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_ARTIFACT = REPO_ROOT / "artifacts/minibatch_td_from_dataset.json"


def load_canonical_artifact():
    with CANONICAL_ARTIFACT.open("r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical minibatch TD artifact not present")
class MinibatchTdTamperTests(unittest.TestCase):
    def verify_tampered(self, artifact):
        return verify_minibatch_td_artifact(
            artifact,
            checkpoint_path=DEFAULT_CHECKPOINT_PATH,
            artifact_path="artifacts/minibatch_td_from_dataset.json",
        )

    def test_duplicate_batch_indices_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["public"]["batch_mode"] = "distinct"
        tampered["items"][1] = copy.deepcopy(tampered["items"][0])
        tampered["public"]["leaf_indices"] = [
            int(item["index"]) for item in tampered["items"]
        ]

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["distinct_indices_ok"])

    def test_wrong_claimed_batch_loss_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["public"]["batch_loss_fp"] += 1

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["batch_loss_match"])

    def test_wrong_item_loss_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["items"][0]["td_witness"]["loss_fp"] += 1

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["item_results"][0]["loss_match"])

    def test_wrong_td_target_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["items"][0]["td_witness"]["target_fp"] += 1

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["item_results"][0]["target_match"])

    def test_wrong_merkle_path_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["items"][0]["merkle_path"][0]["sibling_hash"] = "0" * 64

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["item_results"][0]["merkle_ok"])


if __name__ == "__main__":
    unittest.main()
