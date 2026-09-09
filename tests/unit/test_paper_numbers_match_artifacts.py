"""Every number the paper states in prose must match the committed artifacts.

The tables are generated and cannot drift. The sentences around them can, and
did: the results section argued from a measurement round the tables no longer
contained, quoting 440.6s for a fragment the table reported at 3.8s. Two of
those sentences were not merely stale but false, because "all rows verify under
0.21s" and "all proofs below 2.84MB" silently excluded the one row that does
neither.

Claims are listed here by hand rather than scraped. A scraper cannot tell a
measurement from a year, and the point is to make someone who changes a number
in the paper look at where it came from.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FINAL = ROOT / "artifacts/reports/final_ndss"
SECTIONS = ROOT / "paper/sections"
PROVENANCE = ROOT / "artifacts/reports/provenance/sp1"

# Figures the paper used to quote and must not quote again. Kaggle is on the
# list because no row in the table came from there.
RETIRED = ["440.6", "254.1", "163.1", "167.7", "121.7", "104.8", "82.3",
           "159.5", "198.5", "253.2", "2.84", "Kaggle"]


def live_sections():
    main = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    names = set(re.findall(r"sections/([a-z_]+)", main)) | {"theorems"}
    return [SECTIONS / f"{n}.tex" for n in sorted(names) if (SECTIONS / f"{n}.tex").exists()]


def proved_rows():
    with (FINAL / "table2_zk_proof_cost.csv").open(encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r["Status"] == "proof_verified"]


def metrics(name):
    return json.loads((PROVENANCE / name / "metrics.json").read_text(encoding="utf-8"))


class PaperNumbersTests(unittest.TestCase):
    def setUp(self) -> None:
        if not (FINAL / "table2_zk_proof_cost.csv").exists():
            self.skipTest("final_ndss tables not generated")
        self.rows = proved_rows()
        self.by_case = {r["Case ID"]: r for r in self.rows}
        with (FINAL / "table1_rl_performance.csv").open(encoding="utf-8") as handle:
            self.rl = list(csv.DictReader(handle))
        with (FINAL / "table3_tamper_rejection.csv").open(encoding="utf-8") as handle:
            self.tamper = list(csv.DictReader(handle))

    def rl_score(self, dataset, baseline, optimizer=None):
        for row in self.rl:
            if row["Dataset"] == dataset and row["Baseline"] == baseline:
                if optimizer is None or row["Optimizer"] == optimizer:
                    return round(float(row["Avg Return"].split()[0]), 1)
        raise AssertionError(f"no Table 1 row for {dataset} {baseline} {optimizer}")

    def test_row_counts_the_paper_states(self) -> None:
        self.assertEqual(len(self.rows), 25)
        self.assertEqual(len(self.rl), 54)
        self.assertEqual(len(self.tamper), 236)
        rejected = sum(1 for r in self.tamper if r["Status"] == "rejected_as_expected")
        self.assertEqual(rejected, 233)

    def test_the_verify_and_size_ranges_exclude_only_groth16(self) -> None:
        # The claim is a range over 24 rows plus a named exception, so both the
        # range and the exception have to hold.
        verifies = {r["Case ID"]: float(r["Verify Time (s)"]) for r in self.rows}
        sizes = {r["Case ID"]: int(r["Proof Size (bytes)"]) for r in self.rows}
        outlier = "groth16_recursive_t16"

        others_v = [v for case, v in verifies.items() if case != outlier]
        others_s = [s for case, s in sizes.items() if case != outlier]
        self.assertEqual(round(min(others_v), 3), 0.054)
        self.assertEqual(round(max(others_v), 3), 0.197)
        self.assertEqual(round(min(others_s) / 1e6, 2), 1.27)
        self.assertEqual(round(max(others_s) / 1e6, 2), 4.31)

        self.assertEqual(round(verifies[outlier], 1), 68.0)
        self.assertEqual(round(sizes[outlier] / 1e9, 2), 1.47)

    def test_recursion_costs_the_stated_amount_per_child(self) -> None:
        # The paper quotes these three to one decimal and calls the cost flat
        # in T. Rounding all three to the same integer hid a real 0.5% spread.
        for case, children, expected in (("native_flat_recursive_t16", 2, 211.4),
                                         ("native_flat_recursive_t32", 4, 210.5),
                                         ("native_flat_recursive_t64", 8, 210.4)):
            with self.subTest(case=case):
                cycles = int(self.by_case[case]["Cycle Count"])
                self.assertEqual(round(cycles / children / 1e6, 1), expected)

    def test_whole_run_proofs_cover_the_stated_ranges(self) -> None:
        for name, end, cycles, prove in (
            ("training_aggregation_binary_native_t1248_cartpole", 1248, 422415621, 199.7),
            ("training_aggregation_binary_native_t1248_lunarlander", 1248, 422396109, 198.1),
            ("training_aggregation_binary_native_t4992_lunarlander_random", 4992, 422386830, 188.8),
        ):
            with self.subTest(run=name):
                m = metrics(name)
                self.assertEqual(m["step_start"], 0)
                self.assertEqual(m["step_end"], end)
                self.assertEqual(m["cycle_count"], cycles)
                self.assertEqual(round(m["prove_time_seconds"], 1), prove)
                self.assertTrue(m["proof_verified"])

    def test_the_provable_configuration_row_the_paper_quotes(self) -> None:
        self.assertEqual(self.rl_score("lunarlander-random-v1", "double_dqn_provable"), -152.7)
        self.assertEqual(self.rl_score("lunarlander-random-v1", "double_dqn", "sgd"), -215.3)
        self.assertEqual(self.rl_score("cartpole-random-v2", "double_dqn", "sgd"), 311.0)

    def test_no_section_quotes_a_retired_figure(self) -> None:
        for path in live_sections():
            text = path.read_text(encoding="utf-8")
            for token in RETIRED:
                with self.subTest(section=path.stem, token=token):
                    self.assertNotIn(token, text)

    def test_no_section_carries_a_mangled_escape(self) -> None:
        # A lost backslash turns \texttt into a tab plus "exttt", which LaTeX
        # renders without complaint. One reached the abstract that way.
        for path in live_sections():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                with self.subTest(section=path.stem, line=number):
                    self.assertNotIn("\t", line)


if __name__ == "__main__":
    unittest.main()
