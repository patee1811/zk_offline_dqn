import copy
import contextlib
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from zk_offline_dqn.data_pipeline import (
    AUDIT_REPORT_NAME,
    COLLECTION_LOG_NAME,
    MANIFEST_NAME,
    RAW_EPISODES_NAME,
    canonical_json_bytes,
    hash_jsonl_transitions,
    load_manifest,
    manifest_commitment_hash,
    sha256_file,
    transition_hash,
    validate_collection_log,
    verify_dataset_commitment,
    write_audit_report,
    write_collection_log,
    write_jsonl,
    write_manifest,
)

from scripts.data.audit_replay_dataset import audit_dataset
from scripts.data.collect_audited_dataset import collect
from scripts.data.commit_audited_dataset import commit_dataset


class DataPipelineTests(unittest.TestCase):
    def test_canonical_json_hashing_is_key_order_stable(self):
        left = {"b": 2, "a": [1, {"z": 3}]}
        right = {"a": [1, {"z": 3}], "b": 2}
        self.assertEqual(canonical_json_bytes(left), canonical_json_bytes(right))

    def test_transition_hash_changes_when_reward_changes(self):
        transition = self._transition()
        tampered = copy.deepcopy(transition)
        tampered["reward"] = 2.0
        self.assertNotEqual(transition_hash(transition), transition_hash(tampered))

    def test_transition_hash_changes_when_next_state_changes(self):
        transition = self._transition()
        tampered = copy.deepcopy(transition)
        tampered["next_state"] = [0.2, 0.0, 0.0, 0.0]
        self.assertNotEqual(transition_hash(transition), transition_hash(tampered))

    def test_collection_log_validates_untampered_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp)
            raw_path = dataset_dir / RAW_EPISODES_NAME
            log_path = dataset_dir / COLLECTION_LOG_NAME
            write_jsonl(raw_path, [self._transition()])
            final_hash = write_collection_log(raw_path, log_path)
            ok, value = validate_collection_log(raw_path, log_path)
            self.assertTrue(ok)
            self.assertEqual(value, final_hash)

    def test_collection_log_fails_after_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp)
            raw_path = dataset_dir / RAW_EPISODES_NAME
            log_path = dataset_dir / COLLECTION_LOG_NAME
            write_jsonl(raw_path, [self._transition()])
            write_collection_log(raw_path, log_path)
            row = self._transition()
            row["reward"] = 9.0
            write_jsonl(raw_path, [row])
            ok, _ = validate_collection_log(raw_path, log_path)
            self.assertFalse(ok)

    def test_commit_refuses_when_audit_flags_are_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp)
            self._write_synthetic_self_dataset(dataset_dir, replay_passed=False)
            with self.assertRaises(ValueError):
                commit_dataset(dataset_dir)

    def test_commit_succeeds_for_tiny_audited_synthetic_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp)
            self._write_synthetic_self_dataset(dataset_dir, replay_passed=True)
            commitment = commit_dataset(dataset_dir)
            self.assertEqual(commitment["num_leaves"], 1)
            manifest = load_manifest(dataset_dir)
            self.assertEqual(manifest["merkle_root"], commitment["dataset_root"])
            self.assertTrue(verify_dataset_commitment(dataset_dir)[0])

    def test_manifest_commitment_hash_ignores_volatile_commitment_fields(self):
        manifest = {"dataset_id": "synthetic-v1", "merkle_root": None}
        committed = {"dataset_id": "synthetic-v1", "merkle_root": "abc", "manifest_hash": "def"}
        self.assertEqual(manifest_commitment_hash(manifest), manifest_commitment_hash(committed))

    def test_public_dataset_audit_sets_source_integrity_only_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp)
            raw_path = dataset_dir / RAW_EPISODES_NAME
            write_jsonl(raw_path, [self._transition(env_seed=None, action_seed=None)])
            write_manifest(
                dataset_dir,
                {
                    "schema_version": "dataset_manifest_v1",
                    "dataset_id": "public-jsonl-v1",
                    "dataset_type": "public_benchmark",
                    "source": "jsonl",
                    "source_dataset_id": "source.jsonl",
                    "env_id": "CartPole-v1",
                    "env_version": None,
                    "base_seed": None,
                    "total_transitions": 1,
                    "raw_trajectory_hash": hash_jsonl_transitions(raw_path),
                    "source_file_hash": "abc",
                    "source_integrity_audit_passed": False,
                    "replay_audit_passed": False,
                    "reward_audit_passed": False,
                    "audit_scope": "not_audited_yet",
                    "audit_report_hash": None,
                    "merkle_root": None,
                    "conversion_notes": [],
                },
            )
            self.assertTrue(audit_dataset(dataset_dir))
            manifest = load_manifest(dataset_dir)
            self.assertTrue(manifest["source_integrity_audit_passed"])
            self.assertFalse(manifest["replay_audit_passed"])
            self.assertFalse(manifest["reward_audit_passed"])
            self.assertEqual(manifest["audit_scope"], "source_integrity_only")

    def test_tiny_cartpole_audit_smoke_and_reward_tamper(self):
        try:
            import gymnasium  # noqa: F401
        except ImportError:
            self.skipTest("Gymnasium is unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = Path(tmp) / "cartpole-random-v1"
            with contextlib.redirect_stdout(io.StringIO()):
                collect(
                    Namespace(
                        env_id="CartPole-v1",
                        dataset_id="cartpole-random-v1",
                        policy="random",
                        num_episodes=1,
                        base_seed=12345,
                        max_steps_per_episode=5,
                        out_dir=str(dataset_dir),
                        audit_after_collect=False,
                        atol=1e-6,
                    )
                )
            self.assertTrue(audit_dataset(dataset_dir))

            rows = []
            for row in (dataset_dir / RAW_EPISODES_NAME).read_text(encoding="utf-8").splitlines():
                rows.append(json.loads(row))
            rows[0]["reward"] = float(rows[0]["reward"]) + 1.0
            write_jsonl(dataset_dir / RAW_EPISODES_NAME, rows)
            self.assertFalse(audit_dataset(dataset_dir))

    def _write_synthetic_self_dataset(self, dataset_dir: Path, replay_passed: bool) -> None:
        raw_path = dataset_dir / RAW_EPISODES_NAME
        write_jsonl(raw_path, [self._transition()])
        final_log_hash = write_collection_log(raw_path, dataset_dir / COLLECTION_LOG_NAME)
        report = {
            "schema_version": "dataset_audit_report_v1",
            "dataset_id": "synthetic-v1",
            "dataset_type": "self_collected_replay_audited",
            "audit_scope": "self_collected_replay_and_reward",
            "replay_audit_passed": replay_passed,
            "reward_audit_passed": replay_passed,
            "failures": [] if replay_passed else [{"type": "test"}],
        }
        report_hash = write_audit_report(dataset_dir, report)
        write_manifest(
            dataset_dir,
            {
                "schema_version": "dataset_manifest_v1",
                "dataset_id": "synthetic-v1",
                "dataset_type": "self_collected_replay_audited",
                "env_id": "CartPole-v1",
                "env_version": 1,
                "collector_script_hash": "abc",
                "policy_type": "random",
                "policy_hash": "def",
                "base_seed": 12345,
                "num_episodes": 1,
                "total_transitions": 1,
                "raw_trajectory_hash": hash_jsonl_transitions(raw_path),
                "collection_log_final_hash": final_log_hash,
                "replay_audit_passed": replay_passed,
                "reward_audit_passed": replay_passed,
                "audit_report_hash": report_hash,
                "merkle_root": None,
            },
        )
        self.assertTrue((dataset_dir / MANIFEST_NAME).exists())
        self.assertEqual(sha256_file(dataset_dir / AUDIT_REPORT_NAME), report_hash)

    def _transition(self, env_seed=12345, action_seed=112345):
        return {
            "episode_id": 0,
            "t": 0,
            "env_seed": env_seed,
            "action_seed": action_seed,
            "state": [0.0, 0.0, 0.0, 0.0],
            "action": 1,
            "reward": 1.0,
            "next_state": [0.1, 0.0, 0.0, 0.0],
            "terminated": False,
            "truncated": False,
        }


if __name__ == "__main__":
    unittest.main()
