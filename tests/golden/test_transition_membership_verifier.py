import copy
import importlib
import json
import pathlib
import subprocess
import sys
import unittest

from zk_offline_dqn.core.merkle import build_merkle_levels, build_merkle_path, hash_leaf
from zk_offline_dqn.relations.membership import check_transition_membership_artifact
from zk_offline_dqn.verifiers.membership import (
    format_transition_membership_report,
    verify_transition_membership_artifact,
)
from zk_offline_dqn.zk_specs import serialize_transition_leaf


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_ARTIFACT = REPO_ROOT / "artifacts/fixtures/membership/sample_transition_membership.json"


def make_tiny_membership_artifact():
    transitions = [
        {
            "obs": [0.1, -0.2, 0.3, -0.4],
            "action": 1,
            "reward": 1.0,
            "next_obs": [0.0, 0.2, -0.1, 0.4],
            "done": 0,
        },
        {
            "obs": [-0.5, 0.25, 0.75, -0.125],
            "action": 0,
            "reward": -1.0,
            "next_obs": [0.5, -0.25, -0.75, 0.125],
            "done": 1,
        },
    ]
    leaves = [serialize_transition_leaf(transition) for transition in transitions]
    leaf_hashes = [hash_leaf(leaf) for leaf in leaves]
    levels = build_merkle_levels(leaf_hashes)
    target_index = 0
    merkle_path = build_merkle_path(levels, target_index)

    return {
        "dataset_name": "tiny_test_dataset",
        "target_index": target_index,
        "dataset_root": levels[-1][0],
        "transition": transitions[target_index],
        "leaf": leaves[target_index],
        "leaf_hash": leaf_hashes[target_index],
        "merkle_path": merkle_path,
        "path_length": len(merkle_path),
    }


class TransitionMembershipVerifierTests(unittest.TestCase):
    def test_modules_import_normally(self):
        self.assertIsNotNone(importlib.import_module("zk_offline_dqn.relations.membership"))
        self.assertIsNotNone(importlib.import_module("zk_offline_dqn.verifiers.membership"))

    def test_relation_accepts_tiny_valid_artifact(self):
        artifact = make_tiny_membership_artifact()
        result = check_transition_membership_artifact(artifact)

        self.assertTrue(result.accepted)
        self.assertIsNone(result.reason)
        self.assertTrue(result.leaf_match)
        self.assertTrue(result.leaf_hash_match)
        self.assertTrue(result.merkle_ok)

    def test_relation_rejects_tampered_root_without_raising(self):
        artifact = make_tiny_membership_artifact()
        tampered = copy.deepcopy(artifact)
        tampered["dataset_root"] = "0" * 64

        result = verify_transition_membership_artifact(tampered)

        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "merkle_root_mismatch")
        self.assertTrue(result.leaf_match)
        self.assertTrue(result.leaf_hash_match)
        self.assertFalse(result.merkle_ok)

    @unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical artifact not present")
    def test_canonical_artifact_is_accepted(self):
        with open(CANONICAL_ARTIFACT, "r", encoding="utf-8") as f:
            artifact = json.load(f)

        result = verify_transition_membership_artifact(artifact)

        self.assertTrue(result.accepted)

    @unittest.skipUnless(CANONICAL_ARTIFACT.exists(), "canonical artifact not present")
    def test_script_output_matches_verifier_report_for_canonical_artifact(self):
        with open(CANONICAL_ARTIFACT, "r", encoding="utf-8") as f:
            artifact = json.load(f)

        result = verify_transition_membership_artifact(artifact)
        expected_stdout = (
            format_transition_membership_report(
                artifact,
                result,
                "artifacts/fixtures/membership/sample_transition_membership.json",
            )
            + "\n"
        )

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/artifacts_export/verify_transition_membership_artifact.py",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(completed.stdout, expected_stdout)
        self.assertIn("verification_passed = True", completed.stdout)


if __name__ == "__main__":
    unittest.main()
