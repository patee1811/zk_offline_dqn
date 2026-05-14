import copy
import json
import pathlib
import unittest

from zk_offline_dqn.verifiers.short_trace import (
    DEFAULT_ARTIFACT_PATH,
    verify_short_trace_artifact,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_ARTIFACT = REPO_ROOT / DEFAULT_ARTIFACT_PATH
CANONICAL_MERKLE_PATH = "artifacts/cartpole_dqn_eps010_merkle.json"
CANONICAL_INITIAL_CHECKPOINT_PATH = "models/offline_dqn_with_target_seed42_best.pt"
CANONICAL_FINAL_CHECKPOINT_PATH = (
    "artifacts/short_trace_work/step_1_post_synced_4_5_6_7.pt"
)
CANONICAL_WORK_DIR = "artifacts/short_trace_work"


def load_canonical_artifact():
    with CANONICAL_ARTIFACT.open("r", encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical short-trace artifact not present")
class ShortTraceTamperTests(unittest.TestCase):
    def verify_tampered(self, artifact):
        return verify_short_trace_artifact(
            artifact,
            artifact_path=DEFAULT_ARTIFACT_PATH,
            merkle_path=CANONICAL_MERKLE_PATH,
            initial_checkpoint_path=CANONICAL_INITIAL_CHECKPOINT_PATH,
            final_checkpoint_path=CANONICAL_FINAL_CHECKPOINT_PATH,
            work_dir=CANONICAL_WORK_DIR,
        )

    def test_wrong_chained_checkpoint_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["steps"][1]["input_checkpoint_sha256"] = "0" * 64

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["all_chain_ok"])

    def test_wrong_step_ordering_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["steps"][1]["step_index"] = 7

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["all_chain_ok"])

    def test_wrong_update_witness_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["steps"][0]["one_step_artifact"]["update_witness"][
            "batch_loss_fp"
        ] += 1

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(result["all_step_verifications_ok"])
        self.assertFalse(result["step_results"][0]["one_step_verification_ok"])

    def test_wrong_final_checkpoint_commitment_rejected(self):
        artifact = load_canonical_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["public"]["final_online_state_dict_sha256"] = "0" * 64

        result = self.verify_tampered(tampered)

        self.assertFalse(result["verification_passed"])
        self.assertFalse(
            result["canonical_boundary_checks"][
                "final_online_state_dict_sha256_ok"
            ]
        )


if __name__ == "__main__":
    unittest.main()
