import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.experiments.run_phase7_sp1_training_aggregation_validation import (
    CORE_RUST_TAMPER_CASES,
    BINARY_NATIVE_T32_TAMPER_CASES,
    BINARY_NATIVE_TAMPER_CASES,
    GROTH16_RECURSIVE_TAMPER_CASES,
    PLONK_RECURSIVE_TAMPER_CASES,
    RECURSIVE_TAMPER_CASES,
    TAMPER_CASES,
)
from zk_offline_dqn.backends.sp1.training_aggregation import (
    cargo_command,
    case_path_for_target,
    load_case,
    tampered_case,
    verify_case_reference,
)
from zk_offline_dqn.relations.training_aggregation import (
    GROTH16_CHILD_PROOF_MODE,
    PLONK_CHILD_PROOF_MODE,
    generate_binary_native_case,
    generate_recursive_case,
)


class Sp1TrainingAggregationTamperTests(unittest.TestCase):
    def test_all_tamper_cases_rejected_by_reference(self):
        case = load_case(case_path_for_target(32))
        for name in TAMPER_CASES:
            with self.subTest(name=name):
                result = verify_case_reference(tampered_case(case, name))
                self.assertFalse(result.accepted, name)

    def test_recursive_tamper_cases_rejected_by_reference(self):
        case = generate_recursive_case(32)
        for name in RECURSIVE_TAMPER_CASES:
            with self.subTest(name=name):
                result = verify_case_reference(tampered_case(case, name))
                self.assertFalse(result.accepted, name)

    def test_snark_recursive_tamper_aliases_rejected_by_reference(self):
        cases = [
            (GROTH16_CHILD_PROOF_MODE, GROTH16_RECURSIVE_TAMPER_CASES),
            (PLONK_CHILD_PROOF_MODE, PLONK_RECURSIVE_TAMPER_CASES),
        ]
        for proof_mode, names in cases:
            case = generate_recursive_case(16, child_proof_mode=proof_mode)
            for name in names:
                with self.subTest(proof_mode=proof_mode, name=name):
                    result = verify_case_reference(tampered_case(case, name))
                    self.assertFalse(result.accepted, name)

    def test_binary_native_tamper_cases_rejected_by_reference(self):
        for target, names in [
            (16, BINARY_NATIVE_TAMPER_CASES),
            (32, [*BINARY_NATIVE_TAMPER_CASES, *BINARY_NATIVE_T32_TAMPER_CASES]),
        ]:
            case = generate_binary_native_case(target)
            for name in names:
                with self.subTest(target=target, name=name):
                    result = verify_case_reference(tampered_case(case, name))
                    self.assertFalse(result.accepted, name)

    def test_core_tamper_cases_rejected_by_execute_mode_when_enabled(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute tamper test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        import json
        import subprocess

        case = load_case(case_path_for_target(32))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name in CORE_RUST_TAMPER_CASES:
                with self.subTest(name=name):
                    path = tmp_path / f"{name}.json"
                    path.write_text(json.dumps(tampered_case(case, name), indent=2), encoding="utf-8")
                    result = subprocess.run(
                        cargo_command(case_path=path, mode="execute"),
                        cwd=Path("zk_backend/training_aggregation/sp1"),
                        capture_output=True,
                        text=True,
                        timeout=1200,
                    )
                    self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
