from __future__ import annotations

import unittest

from scripts.experiments import check_paper_claims


class PaperClaimTests(unittest.TestCase):
    def test_claim_scan_passes(self) -> None:
        self.assertEqual(check_paper_claims.scan_claims(), [])

    def test_paper_numbers_have_provenance(self) -> None:
        self.assertEqual(check_paper_claims.check_paper_numbers_provenance(), [])

    def test_table2_has_current_proof_coverage(self) -> None:
        self.assertEqual(check_paper_claims.check_table2_proof_coverage(), [])


if __name__ == "__main__":
    unittest.main()
