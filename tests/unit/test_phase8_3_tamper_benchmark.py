import json
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.tamper_benchmarks.cases import (
    LAYERS,
    MANDATORY_CATEGORIES,
    STATUSES,
    TABLE3_COLUMNS,
    check_mandatory_categories,
    row_from_case,
    validate_rows,
    TamperCase,
)
from zk_offline_dqn.tamper_benchmarks.reporting import write_table3_outputs


def make_case(tamper_id="tamper_reward", category="reward", layer="python_semantic_oracle"):
    return TamperCase(
        tamper_id=tamper_id,
        category=category,
        component="unit_component",
        artifact="unit_fixture.json",
        mutation="unit mutation",
        expected_layer=layer,
        backend="Python semantic oracle",
        proof_backed=False,
        source="unit",
    )


def make_row(category="reward", status="rejected_as_expected", tamper_id=None, notes=""):
    case = make_case(tamper_id or f"tamper_{category}", category)
    return row_from_case(
        case,
        observed_layer="python_semantic_oracle",
        status=status,
        observed_result="rejected" if status == "rejected_as_expected" else "accepted",
        notes=notes,
    )


class Phase83TamperBenchmarkTests(unittest.TestCase):
    def test_status_vocabulary_and_layer_taxonomy_are_explicit(self):
        self.assertIn("rejected_as_expected", STATUSES)
        self.assertIn("accepted_unexpectedly", STATUSES)
        self.assertIn("public_input_binding", LAYERS)
        self.assertIn("rust_execute", LAYERS)

    def test_tamper_case_schema_validation(self):
        row = make_row("reward")
        validate_rows([row])
        for column in TABLE3_COLUMNS:
            self.assertIn(column, row)

    def test_report_writer_creates_outputs(self):
        rows = [make_row(category) for category in MANDATORY_CATEGORIES]
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_table3_outputs(rows, Path(tmp), status={"status": "passed"})
            for key in ["csv", "json", "md", "tex", "status"]:
                self.assertTrue(paths[key].exists())
            payload = json.loads(paths["json"].read_text(encoding="utf-8"))
            self.assertEqual(payload["table"], "Table 3: Tamper rejection")

    def test_mandatory_category_checker_fails_if_missing(self):
        rows = [make_row("reward")]
        result = check_mandatory_categories(rows)
        self.assertEqual(result["status"], "failed")
        self.assertIn("next_state", result["missing_mandatory_rejections"])

    def test_mandatory_category_checker_fails_on_unexpected_acceptance(self):
        rows = [make_row(category) for category in MANDATORY_CATEGORIES]
        rows.append(make_row("reward", status="accepted_unexpectedly", tamper_id="tamper_reward_bad"))
        result = check_mandatory_categories(rows)
        self.assertEqual(result["status"], "failed")
        self.assertIn("tamper_reward_bad", result["accepted_unexpectedly"])

    def test_not_applicable_requires_reason(self):
        row = make_row("proof_public_input", status="not_applicable", tamper_id="tamper_receipt_if_available")
        row["Observed Rejection Layer"] = "not_applicable"
        with self.assertRaises(ValueError):
            validate_rows([row])
        row["Notes"] = "proof binary not retained by artifact policy"
        validate_rows([row])

    def test_aggregation_row_notes_disclaim_true_recursion(self):
        case = make_case(
            tamper_id="tamper_aggregation_child_proof_hash_t32",
            category="proof_public_input",
            layer="public_input_binding",
        )
        case = TamperCase(**{**case.__dict__, "notes": "proof-manifest-chain only; does not recursively verify child proofs inside SP1"})
        row = row_from_case(
            case,
            observed_layer="public_input_binding",
            status="rejected_as_expected",
            observed_result="rejected",
        )
        self.assertIn("does not recursively verify", row["Notes"])

    def test_proof_public_input_records_binding_layer(self):
        case = make_case("tamper_proof_public_input_merkle", "proof_public_input", "public_input_binding")
        case = TamperCase(**{**case.__dict__, "public_input_binding": True})
        row = row_from_case(
            case,
            observed_layer="public_input_binding",
            status="rejected_as_expected",
            observed_result="rejected",
        )
        self.assertTrue(row["Public Input Binding Checked"])
        self.assertEqual(row["Observed Rejection Layer"], "public_input_binding")

    def test_compact_report_does_not_leak_proof_binary_paths(self):
        rows = [make_row(category) for category in MANDATORY_CATEGORIES]
        rows[0]["Artifact / Fixture"] = "artifacts/reports/provenance/sp1/example/proof.bin"
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_table3_outputs(rows, Path(tmp), status={"status": "passed"})
            compact = paths["md"].read_text(encoding="utf-8")
            self.assertNotIn("proof.bin", compact)


if __name__ == "__main__":
    unittest.main()
