import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from zk_offline_dqn.data_pipeline import RAW_EPISODES_NAME, write_jsonl, write_manifest
from zk_offline_dqn.rl_benchmarks.agents import (
    cql_lite_loss,
    train_behavior_cloning_discrete,
    train_offline_q,
)
from zk_offline_dqn.rl_benchmarks.datasets import (
    DatasetUnavailable,
    OfflineDataset,
    load_committed_dataset,
    load_named_dataset,
)
from zk_offline_dqn.rl_benchmarks.reporting import TABLE_COLUMNS, skipped_result_rows, write_table_outputs


class Phase81RlBenchmarkTests(unittest.TestCase):
    def test_small_canonical_discrete_dataset_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "cartpole-random-v1"
            write_jsonl(dataset_dir / RAW_EPISODES_NAME, [self._transition(0), self._transition(1)])
            write_manifest(
                dataset_dir,
                {
                    "dataset_id": "cartpole-random-v1",
                    "dataset_type": "self_collected_replay_audited",
                    "env_id": "CartPole-v1",
                },
            )
            dataset = load_committed_dataset(dataset_dir)
            self.assertEqual(dataset.size, 2)
            self.assertEqual(dataset.action_kind, "discrete")
            self.assertEqual(dataset.action_dim, 2)

    def test_bc_discrete_and_offline_q_train_on_tiny_data(self):
        dataset = self._offline_dataset()
        bc = train_behavior_cloning_discrete(dataset, train_steps=2, seed=0)
        q_policy = train_offline_q(dataset, algorithm="offline_dqn", train_steps=1, seed=0)
        self.assertIn(bc.act(dataset.observations[0]), [0, 1])
        self.assertIn(q_policy.act(dataset.observations[1]), [0, 1])

    def test_cql_lite_regularizer_is_finite(self):
        value = cql_lite_loss(
            torch.tensor([[0.1, 0.5], [0.3, -0.2]], dtype=torch.float32),
            torch.tensor([1, 0]),
            alpha=0.1,
        )
        self.assertTrue(torch.isfinite(value))

    def test_table_formatting_writes_compact_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = {"phase": "8.1", "scope": "RL performance only"}
            paths = write_table_outputs([self._result()], tmp, status=status)
            for path in paths.values():
                self.assertTrue(path.exists(), path)
            with paths["csv"].open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["Dataset"], "cartpole-random-v1")
            self.assertEqual(list(rows[0].keys()), TABLE_COLUMNS)
            self.assertIn("Table 1", paths["md"].read_text(encoding="utf-8"))
            self.assertIn("\\begin{table}", paths["tex"].read_text(encoding="utf-8"))

    def test_missing_minari_dataset_can_be_reported_as_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DatasetUnavailable):
                load_named_dataset(
                    "minari-pointmaze-umaze",
                    tmp,
                    allow_minari_download=False,
                )
        row = skipped_result_rows(
            "minari-pointmaze-umaze",
            ["bc_continuous"],
            source_type="public_source_integrity",
            reason="missing",
        )[0]
        self.assertEqual(row["status"], "skipped")
        self.assertNotIn("checkpoint", row)

    def _offline_dataset(self):
        observations = np.asarray([[0.0, 0.1], [0.2, -0.1], [0.3, 0.0]], dtype=np.float32)
        return OfflineDataset(
            name="synthetic-discrete",
            source_type="audited_self_collected",
            env_id="CartPole-v1",
            observations=observations,
            actions=np.asarray([0, 1, 0], dtype=np.int64),
            rewards=np.asarray([1.0, 0.5, 1.0], dtype=np.float32),
            next_observations=observations + 0.01,
            terminated=np.asarray([0.0, 0.0, 1.0], dtype=np.float32),
            truncated=np.asarray([0.0, 0.0, 0.0], dtype=np.float32),
            metadata={"action_kind": "discrete", "num_actions": 2},
        )

    def _transition(self, action):
        return {
            "state": [0.0, 0.1],
            "action": action,
            "reward": 1.0,
            "next_state": [0.1, 0.2],
            "terminated": False,
            "truncated": False,
        }

    def _result(self):
        return {
            "dataset": "cartpole-random-v1",
            "dataset_source_type": "audited_self_collected",
            "baseline": "bc",
            "status": "completed",
            "average_return_mean": 25.0,
            "average_return_std": 2.0,
            "normalized_score_mean": None,
            "normalized_score_std": None,
            "success_rate_mean": 0.0,
            "success_rate_std": 0.0,
            "num_seeds": 1,
            "num_eval_episodes": 3,
            "train_steps": 10,
            "dataset_num_transitions": 3,
        }


if __name__ == "__main__":
    unittest.main()
