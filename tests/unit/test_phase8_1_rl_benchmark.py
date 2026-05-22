import csv
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from scripts.data.audit_replay_dataset import audit_dataset
from scripts.data.commit_audited_dataset import commit_dataset
from scripts.experiments.run_phase8_1_rl_benchmark import public_benchmark_gate_failed
from zk_offline_dqn.data_pipeline import RAW_EPISODES_NAME, write_jsonl, write_manifest
from zk_offline_dqn.experiments.report_tables import check_table1_rl_performance
from zk_offline_dqn.rl_benchmarks.agents import (
    cql_lite_loss,
    train_behavior_cloning_continuous,
    train_behavior_cloning_discrete,
    train_iql_lite,
    train_offline_q,
)
from zk_offline_dqn.rl_benchmarks.datasets import (
    DatasetUnavailable,
    OfflineDataset,
    load_committed_dataset,
    load_named_dataset,
)
from zk_offline_dqn.rl_benchmarks.reporting import (
    TABLE_COLUMNS,
    skipped_result_rows,
    write_table_outputs,
)


class Phase81RlBenchmarkTests(unittest.TestCase):
    def test_phase2_canonical_jsonl_loads_and_extracts_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "minari-pointmaze-umaze-v2-10000"
            self._write_committed_public_dataset(dataset_dir, [self._transition(0), self._transition(1)])
            dataset = load_committed_dataset(dataset_dir)
            self.assertEqual(dataset.size, 2)
            self.assertEqual(dataset.action_kind, "discrete")
            self.assertEqual(dataset.action_dim, 2)
            self.assertEqual(dataset.source_type, "public_source_integrity")
            self.assertTrue(dataset.metadata["manifest_hash"])
            self.assertTrue(dataset.metadata["audit_report_hash"])
            self.assertEqual(dataset.metadata["dataset_root"], dataset.metadata["merkle_root"])

    def test_missing_phase2_commitment_files_fail_clearly(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "broken"
            write_jsonl(dataset_dir / RAW_EPISODES_NAME, [self._transition(0)])
            with self.assertRaisesRegex(DatasetUnavailable, "missing required Phase 2 file"):
                load_committed_dataset(dataset_dir)

    def test_dict_observation_flattening_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "minari-pointmaze-umaze-v2-10000"
            rows = [
                self._transition(
                    [0.1, -0.1],
                    state={
                        "desired_goal": [3.0],
                        "observation": [1.0, 2.0],
                        "achieved_goal": [0.5],
                    },
                    next_state={
                        "achieved_goal": [0.6],
                        "desired_goal": [3.0],
                        "observation": [1.1, 2.1],
                    },
                )
            ]
            self._write_committed_public_dataset(dataset_dir, rows)
            dataset = load_committed_dataset(dataset_dir)
            np.testing.assert_allclose(dataset.observations[0], [1.0, 2.0, 0.5, 3.0])
            self.assertEqual(
                dataset.metadata["observation_flatten_order"],
                ["observation", "achieved_goal", "desired_goal"],
            )

    def test_continuous_action_dataset_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "minari-pointmaze-umaze-v2-10000"
            rows = [
                self._transition([0.1, -0.1]),
                self._transition([0.2, 0.3]),
            ]
            self._write_committed_public_dataset(dataset_dir, rows)
            dataset = load_named_dataset("minari-pointmaze-umaze-v2-10000", tmp)
            self.assertEqual(dataset.action_kind, "continuous")
            self.assertEqual(dataset.action_dim, 2)

    def test_discrete_and_continuous_trainers_are_finite_on_tiny_data(self):
        discrete = self._offline_discrete_dataset()
        continuous = self._offline_continuous_dataset()
        bc = train_behavior_cloning_discrete(discrete, train_steps=2, seed=0)
        q_policy = train_offline_q(discrete, algorithm="offline_dqn", train_steps=1, seed=0)
        bc_continuous = train_behavior_cloning_continuous(continuous, train_steps=2, seed=0)
        iql = train_iql_lite(continuous, train_steps=1, seed=0)
        self.assertIn(bc.act(discrete.observations[0]), [0, 1])
        self.assertIn(q_policy.act(discrete.observations[1]), [0, 1])
        self.assertTrue(np.isfinite(bc_continuous.act(continuous.observations[0])).all())
        self.assertTrue(np.isfinite(iql.act(continuous.observations[1])).all())

    def test_cql_lite_regularizer_is_finite(self):
        value = cql_lite_loss(
            torch.tensor([[0.1, 0.5], [0.3, -0.2]], dtype=torch.float32),
            torch.tensor([1, 0]),
            alpha=0.1,
        )
        self.assertTrue(torch.isfinite(value))

    def test_incompatible_rows_keep_reason(self):
        row = skipped_result_rows(
            "minari-pointmaze-umaze-v2-10000",
            ["offline_dqn"],
            source_type="public_source_integrity",
            reason="offline_dqn is incompatible with continuous actions",
            status="incompatible_skipped",
            dataset_family="minari-pointmaze-umaze",
        )[0]
        self.assertEqual(row["status"], "incompatible_skipped")
        self.assertIn("continuous", row["reason"])

    def test_public_gate_fails_when_required_public_rows_are_missing(self):
        failed = public_benchmark_gate_failed(
            True,
            ["minari-pointmaze-umaze-v2-10000"],
            [self._result()],
        )
        self.assertTrue(failed)

    def test_table_formatting_includes_public_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = {"phase": "8.1", "scope": "RL performance only"}
            rows = [
                self._result(dataset="minari-pointmaze-umaze-v2-10000", source="public_source_integrity"),
                self._result(dataset="minari-pointmaze-umaze-v2-50000", source="public_source_integrity"),
                self._result(dataset="minari-pointmaze-umaze-v2-100000", source="public_source_integrity"),
            ]
            paths = write_table_outputs(rows, tmp, status=status)
            for path in paths.values():
                self.assertTrue(path.exists(), path)
            with paths["csv"].open("r", encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            self.assertEqual(list(csv_rows[0].keys()), TABLE_COLUMNS)
            self.assertEqual(
                [row["Dataset"] for row in csv_rows],
                [
                    "minari-pointmaze-umaze-v2-10000",
                    "minari-pointmaze-umaze-v2-50000",
                    "minari-pointmaze-umaze-v2-100000",
                ],
            )

    def test_report_source_checker_rejects_table_without_completed_public_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            table_dir = Path(tmp) / "artifacts/reports/final_ndss"
            write_table_outputs([self._result()], table_dir, status={"phase": "8.1"})
            result = check_table1_rl_performance(Path(tmp))
            self.assertEqual(result["status"], "failed")
            self.assertIn("no completed public", result["reason"])

    def test_missing_public_dataset_is_not_downloaded_directly(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(DatasetUnavailable, "Phase 2 dataset"):
                load_named_dataset("minari-pointmaze-umaze-v2-10000", tmp)

    def _write_committed_public_dataset(self, dataset_dir: Path, rows):
        write_jsonl(dataset_dir / RAW_EPISODES_NAME, rows)
        write_manifest(
            dataset_dir,
            {
                "schema_version": "dataset_manifest_v1",
                "dataset_id": dataset_dir.name,
                "dataset_type": "public_benchmark",
                "source": "jsonl",
                "source_dataset_id": "D4RL/pointmaze/umaze-v2",
                "env_id": "PointMaze_UMaze-v3",
                "total_transitions": len(rows),
                "raw_trajectory_hash": self._raw_hash(dataset_dir),
                "source_file_hash": "test-source",
                "source_integrity_audit_passed": False,
                "replay_audit_passed": False,
                "reward_audit_passed": False,
                "audit_scope": "not_audited_yet",
                "audit_report_hash": None,
                "merkle_root": None,
            },
        )
        self.assertTrue(audit_dataset(dataset_dir))
        commit_dataset(dataset_dir)

    def _raw_hash(self, dataset_dir: Path):
        from zk_offline_dqn.data_pipeline import hash_jsonl_transitions

        return hash_jsonl_transitions(dataset_dir / RAW_EPISODES_NAME)

    def _offline_discrete_dataset(self):
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

    def _offline_continuous_dataset(self):
        observations = np.asarray(
            [[0.0, 0.1], [0.2, -0.1], [0.3, 0.0], [0.1, 0.2]],
            dtype=np.float32,
        )
        return OfflineDataset(
            name="synthetic-continuous",
            source_type="public_source_integrity",
            env_id="PointMaze_UMaze-v3",
            observations=observations,
            actions=np.asarray([[0.1, -0.1], [0.2, 0.0], [-0.1, 0.1], [0.0, 0.2]], dtype=np.float32),
            rewards=np.asarray([0.0, 0.5, 1.0, 0.25], dtype=np.float32),
            next_observations=observations + 0.01,
            terminated=np.asarray([0.0, 0.0, 1.0, 0.0], dtype=np.float32),
            truncated=np.asarray([0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            metadata={"action_kind": "continuous"},
        )

    def _transition(self, action, state=None, next_state=None):
        return {
            "episode_id": 0,
            "t": 0,
            "env_seed": None,
            "action_seed": None,
            "state": state or [0.0, 0.1],
            "action": action,
            "reward": 1.0,
            "next_state": next_state or [0.1, 0.2],
            "terminated": False,
            "truncated": False,
        }

    def _result(
        self,
        dataset="cartpole-random-v1",
        source="audited_self_collected",
    ):
        return {
            "dataset": dataset,
            "dataset_id": dataset,
            "dataset_family": "minari-pointmaze-umaze" if source == "public_source_integrity" else "cartpole",
            "dataset_source_type": source,
            "baseline": "bc_continuous" if source == "public_source_integrity" else "bc",
            "status": "completed",
            "average_return_mean": 25.0,
            "average_return_std": 2.0,
            "normalized_score_mean": None,
            "normalized_score_std": None,
            "success_rate_mean": 0.0,
            "success_rate_std": 0.0,
            "num_seeds": 1,
            "seed_list": [0],
            "num_eval_episodes": 3,
            "train_steps": 10,
            "dataset_num_transitions": 3,
        }


if __name__ == "__main__":
    unittest.main()
