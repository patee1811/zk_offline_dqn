import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.backends.sp1.merkle_membership import (
    load_case,
    run_cargo,
    tampered_case,
    verify_case_reference,
)


TAMPER_CASES = [
    "tamper_leaf_hash",
    "tamper_dataset_root",
    "tamper_path_sibling",
    "tamper_leaf_index",
    "tamper_manifest_hash_public_input",
    "tamper_audit_report_hash_public_input",
    "tamper_collection_log_hash_public_input",
]


class Sp1MerkleMembershipTamperTests(unittest.TestCase):
    def test_python_reference_rejects_path_and_root_tamper(self):
        case = load_case()
        for name in [
            "tamper_leaf_hash",
            "tamper_dataset_root",
            "tamper_path_sibling",
            "tamper_leaf_index",
        ]:
            with self.subTest(name=name):
                result = verify_case_reference(tampered_case(case, name))
                self.assertFalse(result.accepted)

    def test_public_provenance_hash_tamper_changes_public_inputs(self):
        case = load_case()
        for name in [
            "tamper_manifest_hash_public_input",
            "tamper_audit_report_hash_public_input",
            "tamper_collection_log_hash_public_input",
        ]:
            with self.subTest(name=name):
                mutated = tampered_case(case, name)
                self.assertNotEqual(mutated["public_inputs"], case["public_inputs"])
                self.assertTrue(verify_case_reference(mutated).accepted)

    def test_execute_mode_rejects_path_and_root_tamper_opt_in(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute tamper test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        case = load_case()
        with tempfile.TemporaryDirectory() as tmp:
            for name in TAMPER_CASES:
                path = Path(tmp) / f"{name}.json"
                path.write_text(json.dumps(tampered_case(case, name), indent=2) + "\n", encoding="utf-8")
                kwargs = {}
                if name in {
                    "tamper_manifest_hash_public_input",
                    "tamper_audit_report_hash_public_input",
                    "tamper_collection_log_hash_public_input",
                }:
                    expected_path = Path(tmp) / "expected_public_inputs.json"
                    expected_path.write_text(
                        json.dumps(case["public_inputs"], indent=2) + "\n",
                        encoding="utf-8",
                    )
                    kwargs["expected_public_inputs"] = expected_path
                result = run_cargo(case_path=path, mode="execute", timeout=900, **kwargs)
                self.assertNotEqual(result.returncode, 0, name)


if __name__ == "__main__":
    unittest.main()
