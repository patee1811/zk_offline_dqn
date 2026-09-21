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
           "159.5", "198.5", "253.2", "2.84", "Kaggle",
           # The MinAtar cost the paper used to estimate with no derivation,
           # and the leaf range that was the min and max of four of eight leaves.
           "16$--$33", "494.7", "494.2$--$495.3"]


def live_sections():
    main = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    names = set(re.findall(r"sections/([a-z_]+)", main)) | {"theorems"}
    return [SECTIONS / f"{n}.tex" for n in sorted(names) if (SECTIONS / f"{n}.tex").exists()]


def proved_rows():
    with (FINAL / "table2_zk_proof_cost.csv").open(encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r["Status"] == "proof_verified"]


def metrics(name):
    return json.loads((PROVENANCE / name / "metrics.json").read_text(encoding="utf-8"))


def cycle_sweep():
    path = ROOT / "artifacts/reports/paper_support/cycle_sweep.json"
    return json.loads(path.read_text(encoding="utf-8"))


def support(name):
    path = ROOT / "artifacts/reports/paper_support" / (name + ".json")
    return json.loads(path.read_text(encoding="utf-8"))


def tree_nodes(tree):
    """Leaf and internal-node metrics for one committed aggregation tree."""
    base = PROVENANCE.parent / tree
    leaves, nodes = [], []
    for m in base.rglob("metrics.json"):
        j = json.loads(m.read_text(encoding="utf-8"))
        if not isinstance(j.get("prove_time_seconds"), (int, float)):
            continue
        (leaves if m.parent.name.startswith("leaf_") else nodes).append(j)
    return leaves, nodes


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
        self.assertEqual(len(self.rows), 26)
        self.assertEqual(len(self.rl), 54)
        self.assertEqual(len(self.tamper), 236)
        rejected = sum(1 for r in self.tamper if r["Status"] == "rejected_as_expected")
        self.assertEqual(rejected, 233)

    def test_the_verify_and_size_ranges_exclude_only_groth16(self) -> None:
        # The claim is a range over 25 rows plus a named exception, so both the
        # range and the exception have to hold.
        verifies = {r["Case ID"]: float(r["Verify Time (s)"]) for r in self.rows}
        sizes = {r["Case ID"]: int(r["Proof Size (bytes)"]) for r in self.rows}
        outlier = "groth16_recursive_t16"

        others_v = [v for case, v in verifies.items() if case != outlier]
        others_s = [s for case, s in sizes.items() if case != outlier]
        self.assertEqual(round(min(others_v), 3), 0.054)
        self.assertEqual(round(max(others_v), 3), 0.130)
        self.assertEqual(round(min(others_s) / 1e6, 2), 1.27)
        self.assertEqual(round(max(others_s) / 1e6, 2), 2.85)

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
            ("training_aggregation_binary_native_t1248_cartpole", 1248, 422411631, 191.8),
            ("training_aggregation_binary_native_t1248_lunarlander", 1248, 422387142, 192.7),
            ("training_aggregation_binary_native_t4992_lunarlander_random", 4992, 422401017, 193.1),
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

    def test_the_network_scaling_figures_the_discussion_quotes(self) -> None:
        sweep = cycle_sweep()
        by_key = {(r["parameters"], r["num_steps"]): r["cycles"]
                  for r in sweep["step_sweep"]}
        baseline = by_key[(836, 4)]
        minatar = by_key[(132565, 4)]
        leaf = by_key[(836, 156)]

        # Cycle counts are deterministic given a guest ELF and an input, so
        # these are pinned exactly rather than to the precision the paper prints.
        self.assertEqual(baseline, 16133939)
        self.assertEqual(minatar, 2032685749)
        self.assertEqual(leaf, 494623692)

        # The ratio is the one measured claim; everything else follows from it.
        self.assertEqual(round(minatar / baseline), 126)
        self.assertEqual(round(minatar / 1e9, 3), 2.033)
        self.assertEqual(round(baseline / 1e6, 2), 16.13)
        self.assertEqual(round(leaf / 1e6, 1), 494.6)
        self.assertEqual(round(leaf * (minatar / baseline) / 1e9), 62)

        text = (SECTIONS / "discussion.tex").read_text(encoding="utf-8")
        for token in ("126", "2.033", "16.13", "494.6", "62", "132{,}566", "132{,}565"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_the_minatar_parameter_count_is_the_one_its_code_gives(self) -> None:
        # conv(4 -> 16, 3x3, stride 1) over 10x10x4, then 1024 -> 128 -> 6.
        conv = 4 * 16 * 3 * 3 + 16
        hidden = 8 * 8 * 16 * 128 + 128
        output = 128 * 6 + 6
        self.assertEqual(conv + hidden + output,
                         cycle_sweep()["minatar_reference"]["parameters"])
        # Our widest row matches that count to within one parameter.
        widest = max(r["parameters"] for r in cycle_sweep()["step_sweep"])
        self.assertEqual(widest, 13 * 10197 + 4)
        self.assertLessEqual(abs(widest - (conv + hidden + output)), 1)

    def test_the_leaf_range_the_results_section_quotes(self) -> None:
        leaves = cycle_sweep()["committed_whole_run_leaves"]["cycles"]
        self.assertEqual(len(leaves), 8)
        self.assertEqual(round(min(leaves) / 1e6, 1), 493.5)
        self.assertEqual(round(max(leaves) / 1e6, 1), 497.7)
        spread = (max(leaves) - min(leaves)) / min(leaves)
        self.assertLess(spread, 0.009)
        text = (SECTIONS / "results.tex").read_text(encoding="utf-8")
        self.assertIn("493.5", text)
        self.assertIn("497.7", text)

    def test_the_sweep_says_it_is_execute_only(self) -> None:
        # No row here is proof-backed, and the paper must not imply otherwise.
        self.assertIn("they do not prove", cycle_sweep()["what"])
        self.assertIn("execute mode",
                      (SECTIONS / "discussion.tex").read_text(encoding="utf-8"))

    def test_the_sweep_reproduces_a_committed_cycle_count(self) -> None:
        # What licenses the sweep: the same host re-running a committed vector
        # lands on the number the committed provenance already recorded.
        cal = cycle_sweep()["calibration"]
        self.assertEqual(cal["cycles_measured_here"],
                         cal["cycles_in_committed_provenance"])
        self.assertEqual(metrics("training_fragment_k156")["cycle_count"],
                         cal["cycles_in_committed_provenance"])

    def test_both_leaf_ranges_cover_every_leaf_of_their_tree(self) -> None:
        # Both ranges the results section prints were once the min and max of a
        # subset. Recompute them from every committed leaf instead.
        for tree, count, lo, hi in (
            ("sp1_t1248_lunarlander", 8, 493.5, 497.7),
            ("sp1_t4992_lunarlander_random", 32, 493.5, 495.3),
        ):
            with self.subTest(tree=tree):
                leaves, _ = tree_nodes(tree)
                cycles = [j["cycle_count"] for j in leaves]
                self.assertEqual(len(cycles), count)
                self.assertEqual(round(min(cycles) / 1e6, 1), lo)
                self.assertEqual(round(max(cycles) / 1e6, 1), hi)
                self.assertTrue(all(j["num_steps"] == 156 for j in leaves))

        text = (SECTIONS / "results.tex").read_text(encoding="utf-8")
        for token in ("493.5", "497.7", "495.3"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_the_per_node_times_behind_the_gpu_hour_projection(self) -> None:
        # The projection is a CartPole run, so it takes the CartPole tree's
        # times. Quoting another tree's leaf time as an internal-node time put
        # the estimate out by six hours.
        leaves, nodes = tree_nodes("sp1_t1248_cartpole")
        leaf = sum(j["prove_time_seconds"] for j in leaves) / len(leaves)
        node = sum(j["prove_time_seconds"] for j in nodes) / len(nodes)
        self.assertEqual(len(leaves), 8)
        self.assertEqual(len(nodes), 7)  # 4 at level 1, 2 at level 2, and the root
        self.assertEqual(round(leaf), 157)
        self.assertEqual(round(node), 193)
        for count, hours in ((321, 31), (512, 50)):
            with self.subTest(leaves=count):
                total = count * leaf + (count - 1) * node
                self.assertEqual(round(total / 3600), hours)

        # Whole phrases, not bare digits: "193" and "31" both occur elsewhere in
        # this section, so a substring check passes on a wrong sentence.
        flat = re.sub(r"\s+", " ", (SECTIONS / "results.tex").read_text(encoding="utf-8"))
        for phrase in (r"$157$\,s per leaf and $193$\,s per internal node",
                       r"about $31$ GPU-hours",
                       r"$512$-leaf tree at about $50$"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, flat)

    def test_the_cuda_speedup_range_the_discussion_quotes(self) -> None:
        rows = support("cpu_baseline")["rows"]
        self.assertEqual(len(rows), 10)
        # The claim only means anything because the work proved did not change.
        self.assertTrue(all(r["cycle_count_unchanged"] for r in rows))
        ratios = [r["cpu_prove_seconds"] / r["cuda_prove_seconds"] for r in rows]
        self.assertEqual(round(min(ratios)), 51)
        self.assertEqual(round(max(ratios)), 62)

        by_case = {r["case_id"]: r for r in rows}
        self.assertEqual(round(by_case["forward_td_mlp"]["cpu_prove_seconds"], 1), 90.4)
        self.assertEqual(round(by_case["merkle_membership"]["cpu_prove_seconds"], 1), 50.2)

        text = (SECTIONS / "discussion.tex").read_text(encoding="utf-8")
        for token in ("90.4", "50.2", "1.78", "0.86"):
            with self.subTest(token=token):
                self.assertIn(token, text)

    def test_the_kaizen_shares_recompute_from_kaizens_own_table(self) -> None:
        doc = support("kaizen_table2")
        text = (SECTIONS / "discussion.tex").read_text(encoding="utf-8")
        for model, expected in (
            ("LeNet", {"commitments": 55.1, "proof_of_aggregation": 10.3,
                       "proof_of_verifier_circuit": 27.3,
                       "proof_of_gradient_descent": 7.3}),
            ("VGG-11", {"commitments": 51.3, "proof_of_aggregation": 16.1,
                        "proof_of_verifier_circuit": 12.0,
                        "proof_of_gradient_descent": 20.7}),
        ):
            row = doc["models"][model]
            total = row["total_prover_seconds"]
            for part, share in expected.items():
                with self.subTest(model=model, part=part):
                    self.assertEqual(round(100 * row["seconds"][part] / total, 1), share)
                    self.assertIn("%.1f" % share, text)
        self.assertEqual(doc["models"]["LeNet"]["parameters"], 61706)
        self.assertEqual(doc["models"]["VGG-11"]["parameters"], 10100000)

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
