"""Tree shape for binary native aggregation across depths.

The builder used to be written out by hand for T in {16, 32} with node_depth
literals, which capped a provable training run at 32 steps. These tests pin the
shape it produces now that it folds levels in a loop, so a regression that
silently flattens or mis-depths the tree fails here rather than after an hour of
GPU time.
"""

import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.io_utils import load_json


class BinaryTreeShapeTests(unittest.TestCase):
    def _build(self, target: int):
        from scripts.experiments.run_phase7_sp1_training_aggregation_validation import (
            prepare_binary_native_case,
        )

        with tempfile.TemporaryDirectory() as tmp:
            case_path, statuses, internal_dirs = prepare_binary_native_case(
                target, Path(tmp), run_child_proves=False
            )
            return load_json(case_path)["public_inputs"], statuses, dict(internal_dirs)

    def test_depth_and_leaf_count_double_per_level(self):
        for target, leaves, depth in [(16, 2, 1), (32, 4, 2), (64, 8, 3), (128, 16, 4)]:
            with self.subTest(target=target):
                public, _, _ = self._build(target)
                self.assertEqual(public["leaf_chunk_count"], leaves)
                self.assertEqual(public["node_depth"], depth)
                self.assertEqual(public["node_id"], "root")

    def test_root_spans_every_step(self):
        for target in (16, 32, 64, 128):
            with self.subTest(target=target):
                public, _, _ = self._build(target)
                self.assertEqual(public["step_start"], 0)
                self.assertEqual(public["step_end"], target)
                self.assertEqual(
                    public["step_end"] - public["step_start"],
                    public["leaf_chunk_count"] * public["chunk_size"],
                )

    def test_internal_node_count_matches_the_formula(self):
        # A binary tree over N leaves has N-1 internal nodes. The root is proved
        # by the host, so the builder proves N-2 of them itself.
        for target, leaves in [(16, 2), (32, 4), (64, 8), (128, 16)]:
            with self.subTest(target=target):
                _, _, internal_dirs = self._build(target)
                self.assertEqual(len(internal_dirs), leaves - 2)

    def test_root_always_has_exactly_two_children(self):
        # Arity stays 2 because the public input schema names its children
        # left_child_* and right_child_*. Widening it is a schema migration.
        for target in (16, 32, 64, 128):
            with self.subTest(target=target):
                public, _, _ = self._build(target)
                self.assertEqual(public["child_count"], 2)
                self.assertEqual(public["chunk_count"], 2)

    def test_non_power_of_two_leaf_count_is_refused(self):
        with self.assertRaises(SystemExit):
            self._build(24)


if __name__ == "__main__":
    unittest.main()
