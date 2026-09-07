"""Every proved row of Table 2 must name the guest that produced it.

Rebuilding a guest moves its ELF, so a table assembled from a provenance tree
that was only partly re-proved reports one guest's cycle count beside another's.
Nothing failed loudly when that happened: the phase scripts exited 0 and the
rows still read proof_verified, because the stale metrics.json was simply never
overwritten. Three separate causes produced it in one afternoon -- a relative
--out-dir, a prover that refused to start, and a script that skipped a step --
and each was caught only by reading guest_elf_sha256 row by row.

These checks are cheap and need no prover, so they run in the normal suite.
"""

from __future__ import annotations

import csv
import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TABLE2 = ROOT / "artifacts/reports/final_ndss/table2_zk_proof_cost.csv"


def proved_rows():
    with TABLE2.open(encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row["Status"] == "proof_verified"]


def metrics_for(row):
    source = row.get("Metrics Source") or ""
    if not source:
        return None
    path = ROOT / source
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


class Table2GuestConsistencyTests(unittest.TestCase):
    def setUp(self) -> None:
        if not TABLE2.exists():
            self.skipTest(f"{TABLE2.relative_to(ROOT).as_posix()} not generated")

    def test_every_proved_row_points_at_provenance_that_exists(self) -> None:
        for row in proved_rows():
            with self.subTest(case=row["Case ID"]):
                self.assertTrue(row.get("Metrics Source"), "row cites no metrics file")
                self.assertIsNotNone(metrics_for(row), f"missing {row['Metrics Source']}")

    def test_every_proved_row_records_the_guest_that_produced_it(self) -> None:
        for row in proved_rows():
            with self.subTest(case=row["Case ID"]):
                metrics = metrics_for(row)
                self.assertIsNotNone(metrics)
                elf = metrics.get("guest_elf_sha256")
                self.assertTrue(elf, "metrics.json carries no guest_elf_sha256")
                self.assertEqual(len(str(elf)), 64, f"not a sha256: {elf}")

    def test_rows_of_one_relation_share_one_guest(self) -> None:
        # The failure this catches: half a relation re-proved, half not.
        #
        # Group by the relation the host recorded, not the Relation column: that
        # column carries a per-variant label like training_fragment_k4, which
        # puts every fragment row in a group of one and makes the check vacuous.
        # metrics["relation"] names the workspace whose guest actually ran, so
        # the five fragment rows and the eight aggregation rows compare.
        by_relation = defaultdict(dict)
        for row in proved_rows():
            metrics = metrics_for(row) or {}
            elf = metrics.get("guest_elf_sha256")
            if elf:
                by_relation[str(metrics.get("relation") or row["Relation"])][row["Case ID"]] = str(elf)
        for relation, cases in by_relation.items():
            with self.subTest(relation=relation):
                distinct = sorted(set(cases.values()))
                self.assertEqual(
                    len(distinct),
                    1,
                    f"{relation} rows split across {len(distinct)} guests: "
                    + ", ".join(f"{case}={elf[:8]}" for case, elf in sorted(cases.items())),
                )

    def test_a_proved_row_reports_the_cycle_count_it_was_measured_at(self) -> None:
        # A row whose cycle count drifted from its own provenance is a row
        # assembled from a table that was edited rather than regenerated.
        for row in proved_rows():
            with self.subTest(case=row["Case ID"]):
                metrics = metrics_for(row) or {}
                recorded = metrics.get("cycle_count")
                if recorded is None or not row["Cycle Count"]:
                    continue
                self.assertEqual(int(row["Cycle Count"]), int(recorded))


if __name__ == "__main__":
    unittest.main()
