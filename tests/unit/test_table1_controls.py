"""The rate-selection rule decides a number the paper prints, so pin it.

Two wrong rules are easy to reach for and both were rejected against the real
sweep: a raw mean lets LunarLander's -1400..200 range outvote CartPole's
0..500, and counting cells won ignores margin, which is how 0.5 led on wins
while collapsing on cartpole-random.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "run_table1_controls", ROOT / "scripts/experiments/run_table1_controls.py"
)
controls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(controls)


def row(dataset, baseline, rate, mean_return):
    return {
        "dataset": dataset,
        "baseline": baseline,
        "learning_rate": rate,
        "mean_return": mean_return,
    }


class RateSelectionTests(unittest.TestCase):
    def test_every_swept_sgd_rate_is_one_the_relation_can_express(self) -> None:
        for rate in controls.SGD_RATES:
            self.assertEqual(controls.provable_learning_rate(rate), rate)

    def test_a_wide_scale_cell_does_not_outvote_a_narrow_one(self) -> None:
        # Cell one prefers 0.01 by 40 points out of a 40-point span; cell two
        # prefers 0.05 by 200 points out of a 1000-point span. Normalising makes
        # those a tie rather than letting the second decide alone.
        rows = [
            row("cartpole", "bc", 0.01, 440.0),
            row("cartpole", "bc", 0.05, 400.0),
            row("lunarlander", "bc", 0.01, -1000.0),
            row("lunarlander", "bc", 0.05, -800.0),
        ]
        summary = controls.summarise(rows)
        self.assertEqual(summary["cells"], 2)
        self.assertAlmostEqual(summary["mean_normalised_score"][0.01], 0.5)
        self.assertAlmostEqual(summary["mean_normalised_score"][0.05], 0.5)

    def test_margin_beats_bare_cell_counts(self) -> None:
        # The shape the real sweep had: 0.5 takes more cells but collapses in
        # the ones it loses, while 0.05 is never far off the best. Note the
        # spread has to come from more than two rates -- with two, min-max hands
        # the winner 1.0 and the loser 0.0 and no margin survives.
        rows = [
            row("a", "bc", 0.001, 0.0), row("a", "bc", 0.05, 95.0), row("a", "bc", 0.5, 100.0),
            row("b", "bc", 0.001, 0.0), row("b", "bc", 0.05, 95.0), row("b", "bc", 0.5, 100.0),
            row("c", "bc", 0.001, 0.0), row("c", "bc", 0.05, 300.0), row("c", "bc", 0.5, 10.0),
        ]
        summary = controls.summarise(rows)
        self.assertEqual(summary["cells_won"][0.5], 2)
        self.assertEqual(summary["cells_won"][0.05], 1)
        self.assertEqual(summary["best_rate"], 0.05)
        self.assertGreater(
            summary["mean_normalised_score"][0.05],
            summary["mean_normalised_score"][0.5],
        )

    def test_a_cell_missing_a_rate_is_left_out_rather_than_guessed(self) -> None:
        rows = [
            row("a", "bc", 0.05, 10.0), row("a", "bc", 0.5, 20.0),
            row("b", "bc", 0.05, 10.0),
        ]
        summary = controls.summarise(rows)
        self.assertEqual(summary["cells"], 2)
        self.assertEqual(summary["cells_won"], {0.05: 0, 0.5: 1})

    def test_a_flat_cell_contributes_no_preference(self) -> None:
        rows = [row("a", "bc", 0.05, 7.0), row("a", "bc", 0.5, 7.0)]
        summary = controls.summarise(rows)
        self.assertEqual(summary["mean_normalised_score"][0.05], 0.0)
        self.assertEqual(summary["mean_normalised_score"][0.5], 0.0)

    def test_controls_sweep_the_datasets_table_1_reports(self) -> None:
        from zk_offline_dqn.rl_benchmarks.datasets import SELF_COLLECTED_DATASETS

        self.assertEqual(
            set(controls.dataset_ids()),
            {spec.dataset_id for spec in SELF_COLLECTED_DATASETS.values()},
        )


if __name__ == "__main__":
    unittest.main()
