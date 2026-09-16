"""One transition must hash to one leaf, in the pipeline, the relation and the guest.

Before this contract the dataset was committed under canonical JSON while the
training relation hashed fixed-point integers, so the two committed different
objects: merkle_membership proved membership in one tree, training_fragment in
another, and nothing stopped a prover from choosing the second one freely. The
pipeline now emits the relation's encoding for datasets that can express it, so
these three implementations have to stay byte-identical.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import (
    CANONICAL_JSON_LEAF_RULE,
    FIXED_POINT_LEAF_RULE,
    dataset_leaf_hash_rule,
    fixed_point_leaf_hash,
    fixed_point_transition_leaf,
    supports_fixed_point_leaf,
)
from zk_offline_dqn.merkle import hash_leaf
from zk_offline_dqn.relations.training_update import serialize_transition_leaf
from zk_offline_dqn.zk_specs import encode_fp

GUEST_SHARED = ROOT / "zk_backend/training_fragment/sp1/shared/src/lib.rs"

DISCRETE = {
    "state": [0.0471041277050972, 0.01049327477812767, 0.0028976858593523502, -0.018124572932720184],
    "next_state": [0.04731399193406105, 0.20557354390621185, 0.002535194391384721, -0.30989184975624084],
    "action": 1,
    "reward": 1.0,
    "terminated": False,
    "truncated": False,
}
CONTINUOUS = {
    "state": {"observation": [0.1, 0.2], "achieved_goal": [0.3, 0.4]},
    "next_state": {"observation": [0.1, 0.2], "achieved_goal": [0.3, 0.4]},
    "action": [1.0, 1.0],
    "reward": 0.0,
    "terminated": False,
    "truncated": False,
}


def as_fixed_point(transition):
    return {
        "state": [encode_fp(float(v)) for v in transition["state"]],
        "next_state": [encode_fp(float(v)) for v in transition["next_state"]],
        "action": int(transition["action"]),
        "reward": encode_fp(float(transition["reward"])),
        "terminated": transition["terminated"],
        "truncated": transition["truncated"],
    }


class DatasetLeafContractTests(unittest.TestCase):
    def test_pipeline_leaf_equals_the_relation_leaf(self) -> None:
        fp = as_fixed_point(DISCRETE)
        self.assertEqual(
            fixed_point_transition_leaf(DISCRETE),
            serialize_transition_leaf(fp, obs_dim=len(fp["state"]), action_dim=2),
        )
        self.assertEqual(
            fixed_point_leaf_hash(DISCRETE),
            hash_leaf(serialize_transition_leaf(fp, obs_dim=len(fp["state"]), action_dim=2)),
        )

    def test_leaf_field_order_is_state_action_reward_next_state_done(self) -> None:
        leaf = fixed_point_transition_leaf(DISCRETE)
        self.assertEqual(leaf, [47, 10, 3, -18, 1, 1000, 47, 206, 3, -310, 0])

    def test_done_is_set_by_truncation_as_well_as_termination(self) -> None:
        for terminated, truncated in ((True, False), (False, True), (True, True)):
            with self.subTest(terminated=terminated, truncated=truncated):
                transition = dict(DISCRETE, terminated=terminated, truncated=truncated)
                self.assertEqual(fixed_point_transition_leaf(transition)[-1], 1)
        self.assertEqual(fixed_point_transition_leaf(DISCRETE)[-1], 0)

    def test_guest_builds_the_same_leaf(self) -> None:
        # The Rust side is pinned by reading it: a drift there is invisible to
        # Python tests but breaks every proof against a committed dataset.
        source = GUEST_SHARED.read_text(encoding="utf-8")
        body = re.search(
            r"fn serialize_transition_leaf\((.|\n)*?\n\}", source
        )
        self.assertIsNotNone(body, "serialize_transition_leaf missing from the guest")
        text = body.group(0)
        order = [
            "leaf.extend_from_slice(&transition.state);",
            "leaf.push(transition.action as i64);",
            "leaf.push(transition.reward);",
            "leaf.extend_from_slice(&transition.next_state);",
        ]
        positions = [text.index(fragment) for fragment in order]
        self.assertEqual(positions, sorted(positions), "guest leaf field order changed")
        self.assertIn("transition.terminated || transition.truncated", text)
        self.assertIn('.join(",")', source)

    def test_continuous_action_datasets_keep_the_json_rule(self) -> None:
        self.assertTrue(supports_fixed_point_leaf(DISCRETE))
        self.assertFalse(supports_fixed_point_leaf(CONTINUOUS))
        self.assertEqual(dataset_leaf_hash_rule([DISCRETE]), FIXED_POINT_LEAF_RULE)
        self.assertEqual(dataset_leaf_hash_rule([CONTINUOUS]), CANONICAL_JSON_LEAF_RULE)
        # One unrepresentable transition disqualifies the whole dataset: a tree
        # may not mix encodings.
        self.assertEqual(
            dataset_leaf_hash_rule([DISCRETE, CONTINUOUS]), CANONICAL_JSON_LEAF_RULE
        )

    def test_an_empty_dataset_does_not_claim_the_fixed_point_rule(self) -> None:
        self.assertEqual(dataset_leaf_hash_rule([]), CANONICAL_JSON_LEAF_RULE)


if __name__ == "__main__":
    unittest.main()
