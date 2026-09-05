"""Lock the identity of the six collected source datasets.

The datasets themselves are 251MB and stay gitignored, so what a reviewer gets
is the collection spec plus these hashes: regenerate, and the merkle_root has to
land on the value recorded here. That check is only meaningful because
`ensure_self_collected_dataset` now takes its arguments from the spec -- when it
derived them from a target size instead, regeneration produced a different
dataset whose root matched nothing.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import sha256_file
from zk_offline_dqn.rl_benchmarks.datasets import SELF_COLLECTED_DATASETS

DATASET_ROOT = ROOT / "artifacts" / "datasets"

# Collected on 2026-09-05 by scripts/data/collect_audited_dataset.py against the
# checkpoints in artifacts/source_policies/. mean_return is the average episode
# return in the raw trajectories, and is what makes the quality label checkable:
# CartPole runs 22.3 -> 267.6 -> 437.1, LunarLander -186.7 -> 9.7 -> 203.4.
EXPECTED = {
    "cartpole-random-v2": {
        "total_transitions": 50006,
        "num_episodes": 2238,
        "merkle_root": "6f586441d6efef700687ce83ed8ff4573e3a064e49803723e1e2f571a2d171c4",
        "raw_trajectory_hash": "1a78f1351fdcb267e599beaa91c5ab0622f7d3a4cdda64d393fc854001d96f86",
        "policy_checkpoint_sha256": None,
        "mean_return": 22.3,
    },
    "cartpole-medium-v2": {
        "total_transitions": 50045,
        "num_episodes": 187,
        "merkle_root": "f5002ce505f8a63a57e3d0d64c0061e4ae7eb7495826013dc8b36b593643b311",
        "raw_trajectory_hash": "2930fa55f386626822cb1cc6adc71b8c5a4147c17ff2ca91695594ea97f0ad36",
        "policy_checkpoint_sha256": "01e89b8838c35db6ec228e2b2bdd6c226790fd08bc623308365fe8eb80e5f325",
        "mean_return": 267.6,
    },
    "cartpole-expert-v2": {
        "total_transitions": 50261,
        "num_episodes": 115,
        "merkle_root": "02de61a980455ea1e894e5ec77a7948faa622b4ddc4d1a56b710b2ce10b410d2",
        "raw_trajectory_hash": "f6c25677093f8a54372d4722f124b91e23c3c1141481ee5b4652323cb8c1cadf",
        "policy_checkpoint_sha256": "2e3bb4bf4b7bc21fc0690778f7c5f90b5239bab61c3e30409b23583bec7cd3f6",
        "mean_return": 437.1,
    },
    "lunarlander-random-v1": {
        "total_transitions": 50020,
        "num_episodes": 515,
        "merkle_root": "24eebb925e4f3ed990c17c4b4fd9ca0188eb519a22909cec56de7076f169cd86",
        "raw_trajectory_hash": "28751453e710ff954b2a110bcb515206a3c658db4c957d6ed79b8344b45149e2",
        "policy_checkpoint_sha256": None,
        "mean_return": -186.7,
    },
    "lunarlander-medium-v1": {
        "total_transitions": 50586,
        "num_episodes": 52,
        "merkle_root": "eb3e4f6ca980c27cce3ae003d7d729a0108fdef6c6ed39294c433fd236e7f208",
        "raw_trajectory_hash": "0667eaeb9877973d8618b67b5d2e4194a4c3024e8419e290e595335be5d8fb9c",
        "policy_checkpoint_sha256": "29780045675ebdc2e2af85fe9e5d52a7106456a4ac3df0cae66b9702e78aed48",
        "mean_return": 9.7,
    },
    "lunarlander-expert-v1": {
        "total_transitions": 50552,
        "num_episodes": 108,
        "merkle_root": "328eb8b413623e73ed1cc377153686cb8f0ff1e6bb56d0b6e45386bd846fd151",
        "raw_trajectory_hash": "69de86df8d078cacd5b7c804fe0dde2fb0ed352defb329b31de97b84e791c3d5",
        "policy_checkpoint_sha256": "2a692cffb2f019dafbe100db58e1ebe423c57f8ebfebd048666d61a81a765030",
        "mean_return": 203.4,
    },
}


class SourceDatasetIdentityTests(unittest.TestCase):
    def test_every_spec_is_locked(self) -> None:
        specs = {spec.dataset_id for spec in SELF_COLLECTED_DATASETS.values()}
        self.assertEqual(specs, set(EXPECTED))

    def test_quality_labels_are_ordered_by_return(self) -> None:
        for env_prefix in ("cartpole", "lunarlander"):
            returns = {
                spec.quality: EXPECTED[spec.dataset_id]["mean_return"]
                for spec in SELF_COLLECTED_DATASETS.values()
                if spec.dataset_id.startswith(env_prefix)
            }
            self.assertLess(returns["random"], returns["medium"], env_prefix)
            self.assertLess(returns["medium"], returns["expert"], env_prefix)

    def test_committed_manifests_match_the_lock(self) -> None:
        for dataset_id, expected in EXPECTED.items():
            manifest_path = DATASET_ROOT / dataset_id / "dataset_manifest.json"
            if not manifest_path.exists():
                continue
            with self.subTest(dataset_id=dataset_id):
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                for field in (
                    "total_transitions",
                    "num_episodes",
                    "merkle_root",
                    "raw_trajectory_hash",
                    "policy_checkpoint_sha256",
                ):
                    self.assertEqual(manifest.get(field), expected[field], field)
                self.assertTrue(manifest["replay_audit_passed"], "replay audit")

    def test_source_policy_checkpoints_match_the_lock(self) -> None:
        for spec in SELF_COLLECTED_DATASETS.values():
            if spec.checkpoint is None:
                continue
            path = ROOT / spec.checkpoint
            if not path.exists():
                continue
            with self.subTest(checkpoint=spec.checkpoint):
                self.assertEqual(
                    sha256_file(path),
                    EXPECTED[spec.dataset_id]["policy_checkpoint_sha256"],
                )


if __name__ == "__main__":
    unittest.main()
