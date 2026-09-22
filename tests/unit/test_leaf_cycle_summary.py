"""leaf_cycle_summary: the range the paper quotes, over a population it names.

The paper printed two leaf-cycle ranges that were the min and max of a subset
(four of eight leaves, then twenty of thirty-two), because each was read off the
leaves by hand. The summary replaces that reading, so what it must get right is
the population: all leaves, one setting, and nothing silently averaged across
settings that are not comparable.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.backends.sp1.metrics import (  # noqa: E402
    leaf_cycle_summary,
    load_tree_leaves,
)


def leaf(chunk_id, cycles, *, steps=156, sync=4):
    return {"chunk_id": chunk_id, "cycle_count": cycles,
            "num_steps": steps, "target_sync_interval": sync}


class LeafCycleSummaryTests(unittest.TestCase):
    def test_range_spans_every_leaf_not_the_first_few(self) -> None:
        # The defect the summary exists for: the extremes sit in the last leaves.
        leaves = [leaf(i, 100 + i) for i in range(8)]
        summary = leaf_cycle_summary(leaves)
        self.assertEqual(summary["leaf_count"], 8)
        self.assertEqual(summary["cycle_count_min"], 100)
        self.assertEqual(summary["cycle_count_max"], 107)

    def test_leaves_are_listed_in_chunk_order_whatever_order_they_arrive(self) -> None:
        summary = leaf_cycle_summary([leaf(2, 30), leaf(0, 10), leaf(1, 20)])
        self.assertEqual([row["chunk_id"] for row in summary["leaves"]], [0, 1, 2])

    def test_mixed_sync_intervals_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            leaf_cycle_summary([leaf(0, 10, sync=4), leaf(1, 11, sync=2000)])

    def test_mixed_leaf_sizes_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            leaf_cycle_summary([leaf(0, 10, steps=156), leaf(1, 11, steps=8)])

    def test_an_empty_tree_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            leaf_cycle_summary([])


class LoadTreeLeavesTests(unittest.TestCase):
    def test_reads_counts_and_settings_from_each_leaf_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            for i, cycles in ((10, 7), (2, 9), (0, 8)):
                d = work / f"leaf_{i}"
                d.mkdir()
                (d / "metrics.json").write_text(
                    json.dumps({"cycle_count": cycles, "num_steps": 156}), encoding="utf-8")
                (d / "public_inputs.json").write_text(
                    json.dumps({"target_sync_interval": 4}), encoding="utf-8")
            # Neither a non-numeric sibling nor the case directory is a leaf.
            (work / "leaf_cases").mkdir()
            leaves = load_tree_leaves(work)
        # Numeric order: leaf_10 after leaf_2, which a string sort gets wrong.
        self.assertEqual([row["chunk_id"] for row in leaves], [0, 2, 10])
        self.assertEqual([row["cycle_count"] for row in leaves], [8, 9, 7])
        self.assertTrue(all(row["target_sync_interval"] == 4 for row in leaves))


if __name__ == "__main__":
    unittest.main()
