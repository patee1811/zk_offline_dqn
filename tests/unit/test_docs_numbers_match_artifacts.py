"""The explainer and the slide deck must not quote a Table 2 row that has moved.

Both restate Table 2 by hand rather than reading the CSV, and both went stale
the moment the table was re-proved: the deck still had a fragment at 5,193,244
cycles and a Merkle row at 50.2 s on a CPU prover, hours after neither was
true. Nothing caught it, because the paper-side gates check the paper.

The check is deliberately narrow, and the shape matters. Scanning for "numbers
that look like cycle counts" flags proof sizes, byte counts and every derived
figure the prose is entitled to compute, which is a gate nobody would keep. So
this reads the line the row sits on instead: if a file writes the label of a
Table 2 row, the current cycle count for that row has to appear on that line.
A file is free to stop quoting a row; it is not free to quote a wrong one.

Making the deck read the CSV would remove the duplication entirely. That is a
larger change, and this test does not assume it.
"""

from __future__ import annotations

import csv
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FINAL = ROOT / "artifacts/reports/final_ndss"

# How each file writes a row's name, mapped to its Case ID. Only rows the two
# files actually tabulate are listed; adding a row here is how a new figure
# gets covered.
LABELS = {
    "TD MVP": "td_mvp",
    "Merkle (canonical)": "merkle_membership",
    "Fwd-TD MLP": "forward_td_mlp",
    "One-step SGD tiny": "one_step_sgd_tiny",
    "Training update": "training_update_batch1",
    "Fragment k=1": "training_fragment_k1",
    "Fragment k=8": "training_fragment_k8",
    "Merkle 100k": "merkle_membership_dataset_100000",
    "Agg. chain T=128": "training_aggregation_manifest_t128",
    "Recursive T=64": "native_flat_recursive_t64",
    "Whole run, CartPole": "binary_tree_native_t1248_cartpole",
    "Groth16 child T=16": "groth16_recursive_t16",
    "native_flat_recursive T=16": "native_flat_recursive_t16",
    "native_flat_recursive T=32": "native_flat_recursive_t32",
    "native_flat_recursive T=64": "native_flat_recursive_t64",
    "`native_flat_recursive_t16`": "native_flat_recursive_t16",
    "`native_flat_recursive_t32`": "native_flat_recursive_t32",
    "`native_flat_recursive_t64`": "native_flat_recursive_t64",
}

WATCHED = (
    ROOT / "docs/giai_thich_toan_canh.md",
    ROOT / "docs/slides/build_deck.py",
)


def spellings(value: int) -> set[str]:
    grouped = f"{value:,}"
    return {grouped, grouped.replace(",", "."), str(value)}


class DocsQuoteLiveNumbersTests(unittest.TestCase):
    def setUp(self) -> None:
        table2 = FINAL / "table2_zk_proof_cost.csv"
        if not table2.exists():
            self.skipTest("final_ndss tables not generated")
        with table2.open(encoding="utf-8") as handle:
            rows = {r["Case ID"]: r for r in csv.DictReader(handle)}
        self.cycles = {
            case: int(rows[case]["Cycle Count"])
            for case in set(LABELS.values())
            if rows.get(case, {}).get("Cycle Count")
        }

    def test_the_case_ids_the_labels_name_are_still_in_the_table(self) -> None:
        # A renamed or dropped Case ID would otherwise make this test vacuous.
        for label, case in LABELS.items():
            with self.subTest(label=label):
                self.assertIn(case, self.cycles, f"{case} is no longer a Table 2 row")

    def test_a_row_quoted_by_name_carries_its_current_cycle_count(self) -> None:
        for path in WATCHED:
            if not path.exists():
                self.skipTest(f"{path.name} missing")
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                # Strip the labels before looking for a figure, so that the "16"
                # inside "Groth16" or "T=128" does not read as a quoted number,
                # and require a run long enough to be a cycle count rather than
                # a prove time or a section number.
                stripped = line
                for label in LABELS:
                    stripped = stripped.replace(label, "")
                if not re.search(r"\d[\d.,]{4,}", stripped):
                    continue
                for label, case in LABELS.items():
                    if label not in line:
                        continue
                    wanted = spellings(self.cycles[case])
                    with self.subTest(file=path.name, line=number, row=label):
                        self.assertTrue(
                            any(spelling in line for spelling in wanted),
                            f"{path.name}:{number} names {label!r} beside a number, but "
                            f"not its current cycle count {self.cycles[case]:,}. "
                            "Re-run the docs update after re-proving.",
                        )


if __name__ == "__main__":
    unittest.main()
