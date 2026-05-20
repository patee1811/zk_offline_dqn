import contextlib
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from scripts.data.audit_replay_dataset import audit_dataset
from scripts.data.collect_audited_dataset import collect
from scripts.data.commit_audited_dataset import commit_dataset
from scripts.data.import_public_dataset import import_public
from zk_offline_dqn.data_pipeline import (
    AUDIT_REPORT_NAME,
    MERKLE_TREE_NAME,
    RAW_EPISODES_NAME,
    load_manifest,
    read_jsonl,
    verify_dataset_commitment,
    write_jsonl,
)


def gymnasium_available() -> bool:
    try:
        import gymnasium  # noqa: F401
    except ImportError:
        return False
    return True


class DatasetProvenanceTamperTests(unittest.TestCase):
    def test_tamper_reward_before_commit(self):
        self._assert_precommit_tamper_fails(lambda row: row.update({"reward": float(row["reward"]) + 1.0}))

    def test_tamper_next_state_before_commit(self):
        def tamper(row):
            row["next_state"][0] = float(row["next_state"][0]) + 1.0

        self._assert_precommit_tamper_fails(tamper)

    def test_tamper_done_before_commit(self):
        def tamper(row):
            row["terminated"] = not bool(row["terminated"])

        self._assert_precommit_tamper_fails(tamper)

    def test_tamper_action_before_commit(self):
        def tamper(row):
            row["action"] = 1 - int(row["action"])

        self._assert_precommit_tamper_fails(tamper)

    def test_tamper_manifest_hash_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self._committed_cartpole_dataset(Path(tmp))
            manifest_path = dataset_dir / "dataset_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["env_id"] = "CartPole-v1-tampered"
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            ok, errors = verify_dataset_commitment(dataset_dir)
            self.assertFalse(ok)
            self.assertTrue(any("manifest_hash mismatch" in error for error in errors))

    def test_tamper_audit_report_hash_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self._committed_cartpole_dataset(Path(tmp))
            self._tamper_json(dataset_dir / AUDIT_REPORT_NAME, "tampered", True)
            ok, errors = verify_dataset_commitment(dataset_dir)
            self.assertFalse(ok)
            self.assertTrue(any("audit_report_hash mismatch" in error for error in errors))

    def test_tamper_merkle_leaf_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self._committed_cartpole_dataset(Path(tmp))
            merkle_path = dataset_dir / MERKLE_TREE_NAME
            merkle = json.loads(merkle_path.read_text(encoding="utf-8"))
            merkle["leaf_hashes"][0] = "0" * 64
            merkle_path.write_text(json.dumps(merkle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            ok, errors = verify_dataset_commitment(dataset_dir)
            self.assertFalse(ok)
            self.assertTrue(any("leaf_hashes mismatch" in error for error in errors))

    def test_tamper_raw_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self._committed_cartpole_dataset(Path(tmp))
            rows = read_jsonl(dataset_dir / RAW_EPISODES_NAME)
            rows[0]["reward"] = float(rows[0]["reward"]) + 1.0
            write_jsonl(dataset_dir / RAW_EPISODES_NAME, rows)
            ok, errors = verify_dataset_commitment(dataset_dir)
            self.assertFalse(ok)
            self.assertTrue(any("raw_trajectory_hash mismatch" in error for error in errors))

    def test_tamper_collection_log_hash_after_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self._committed_cartpole_dataset(Path(tmp))
            log_path = dataset_dir / "collection_log.jsonl"
            rows = read_jsonl(log_path)
            rows[0]["current_log_hash"] = "0" * 64
            write_jsonl(log_path, rows)
            ok, errors = verify_dataset_commitment(dataset_dir)
            self.assertFalse(ok)
            self.assertTrue(any("collection log invalid" in error for error in errors))

    def test_public_jsonl_commitment_is_source_integrity_only_and_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_path = root / "source.jsonl"
            write_jsonl(source_path, [self._public_transition()])
            dataset_dir = root / "public-jsonl-v1"
            with contextlib.redirect_stdout(io.StringIO()):
                import_public(
                    Namespace(
                        source_jsonl=str(source_path),
                        source_npz=None,
                        minari_dataset_id=None,
                        dataset_id="public-jsonl-v1",
                        env_id="CartPole-v1",
                        out_dir=str(dataset_dir),
                        max_transitions=None,
                    )
                )
            self.assertTrue(audit_dataset(dataset_dir))
            commit_dataset(dataset_dir)
            ok, errors = verify_dataset_commitment(dataset_dir)
            self.assertTrue(ok, errors)
            manifest = load_manifest(dataset_dir)
            self.assertTrue(manifest["source_integrity_audit_passed"])
            self.assertFalse(manifest["replay_audit_passed"])
            self.assertFalse(manifest["reward_audit_passed"])
            merkle = json.loads((dataset_dir / MERKLE_TREE_NAME).read_text(encoding="utf-8"))
            self.assertIsNone(merkle["collection_log_final_hash"])

            self._tamper_json(dataset_dir / AUDIT_REPORT_NAME, "tampered", True)
            ok, errors = verify_dataset_commitment(dataset_dir)
            self.assertFalse(ok)
            self.assertTrue(any("audit_report_hash mismatch" in error for error in errors))

    def _assert_precommit_tamper_fails(self, tamper):
        with tempfile.TemporaryDirectory() as tmp:
            dataset_dir = self._collected_cartpole_dataset(Path(tmp))
            rows = read_jsonl(dataset_dir / RAW_EPISODES_NAME)
            tamper(rows[0])
            write_jsonl(dataset_dir / RAW_EPISODES_NAME, rows)
            self.assertFalse(audit_dataset(dataset_dir))
            with self.assertRaises(ValueError):
                commit_dataset(dataset_dir)

    def _collected_cartpole_dataset(self, root: Path) -> Path:
        if not gymnasium_available():
            self.skipTest("Gymnasium is unavailable")
        dataset_dir = root / "cartpole-tiny-v1"
        with contextlib.redirect_stdout(io.StringIO()):
            collect(
                Namespace(
                    env_id="CartPole-v1",
                    dataset_id="cartpole-tiny-v1",
                    policy="random",
                    num_episodes=1,
                    base_seed=12345,
                    max_steps_per_episode=10,
                    out_dir=str(dataset_dir),
                    audit_after_collect=False,
                    atol=1e-6,
                )
            )
        return dataset_dir

    def _committed_cartpole_dataset(self, root: Path) -> Path:
        dataset_dir = self._collected_cartpole_dataset(root)
        self.assertTrue(audit_dataset(dataset_dir))
        commit_dataset(dataset_dir)
        ok, errors = verify_dataset_commitment(dataset_dir)
        self.assertTrue(ok, errors)
        return dataset_dir

    def _tamper_json(self, path: Path, key: str, value):
        data = json.loads(path.read_text(encoding="utf-8"))
        data[key] = value
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _public_transition(self):
        return {
            "episode_id": 0,
            "t": 0,
            "state": [0.0, 0.0, 0.0, 0.0],
            "action": 1,
            "reward": 1.0,
            "next_state": [0.1, 0.0, 0.0, 0.0],
            "terminated": False,
            "truncated": False,
        }


if __name__ == "__main__":
    unittest.main()
