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
        "merkle_root": "fcce8855ffa6ef7f11bb9723687b31776c9e060105661b156783452232382611",
        "raw_trajectory_hash": "1a78f1351fdcb267e599beaa91c5ab0622f7d3a4cdda64d393fc854001d96f86",
        "policy_checkpoint_sha256": None,
        "mean_return": 22.3,
    },
    "cartpole-medium-v2": {
        "total_transitions": 50045,
        "num_episodes": 187,
        "merkle_root": "97d6deb492691c5b777ceae323cb05c08d63778df91d5e41aa929a0249e7603a",
        "raw_trajectory_hash": "2930fa55f386626822cb1cc6adc71b8c5a4147c17ff2ca91695594ea97f0ad36",
        "policy_checkpoint_sha256": "01e89b8838c35db6ec228e2b2bdd6c226790fd08bc623308365fe8eb80e5f325",
        "mean_return": 267.6,
    },
    "cartpole-expert-v2": {
        "total_transitions": 50261,
        "num_episodes": 115,
        "merkle_root": "88cb5f28215a68b70a729bb7129ab61d4c6919e4add377726c78a9131b191a84",
        "raw_trajectory_hash": "f6c25677093f8a54372d4722f124b91e23c3c1141481ee5b4652323cb8c1cadf",
        "policy_checkpoint_sha256": "2e3bb4bf4b7bc21fc0690778f7c5f90b5239bab61c3e30409b23583bec7cd3f6",
        "mean_return": 437.1,
    },
    "lunarlander-random-v1": {
        "total_transitions": 50020,
        "num_episodes": 515,
        "merkle_root": "fb412e69cca5c9dad6923c50c3ef9b32d1fd35494a50a13579a41bedd5d3396f",
        "raw_trajectory_hash": "28751453e710ff954b2a110bcb515206a3c658db4c957d6ed79b8344b45149e2",
        "policy_checkpoint_sha256": None,
        "mean_return": -186.7,
    },
    "lunarlander-medium-v1": {
        "total_transitions": 50586,
        "num_episodes": 52,
        "merkle_root": "3fc9c4042f3a97f7de15dc7040d05712897cbb2e4b80c2a05eeb0969098be1df",
        "raw_trajectory_hash": "0667eaeb9877973d8618b67b5d2e4194a4c3024e8419e290e595335be5d8fb9c",
        "policy_checkpoint_sha256": "29780045675ebdc2e2af85fe9e5d52a7106456a4ac3df0cae66b9702e78aed48",
        "mean_return": 9.7,
    },
    "lunarlander-expert-v1": {
        "total_transitions": 50552,
        "num_episodes": 108,
        "merkle_root": "9539a4b406a1f9cc09610a4396e791428de69e564c4aefaaf259192d1f78a900",
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
