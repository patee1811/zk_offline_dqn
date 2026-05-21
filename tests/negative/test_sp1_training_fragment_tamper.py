import os
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.experiments.run_phase6_sp1_training_fragment_validation import (
    CORE_RUST_TAMPER_CASES,
    TAMPER_CASES,
)
from zk_offline_dqn.backends.sp1.training_fragment import (
    cargo_command,
    case_path_for_k,
    load_case,
    tampered_case,
    verify_case_reference,
)


class Sp1TrainingFragmentTamperTests(unittest.TestCase):
    def test_all_tamper_cases_rejected_by_reference(self):
        case = load_case(case_path_for_k(4))
        for name in TAMPER_CASES:
            with self.subTest(name=name):
                result = verify_case_reference(tampered_case(case, name))
                self.assertFalse(result.accepted, name)

    def test_core_tamper_cases_rejected_by_execute_mode_when_enabled(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute tamper test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        import json
        import subprocess

        case = load_case(case_path_for_k(4))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name in CORE_RUST_TAMPER_CASES:
                with self.subTest(name=name):
                    path = tmp_path / f"{name}.json"
                    path.write_text(
                        json.dumps(tampered_case(case, name), indent=2), encoding="utf-8"
                    )
                    result = subprocess.run(
                        cargo_command(case_path=path, mode="execute", max_steps=4),
                        cwd=Path("zk_backend/training_fragment/sp1"),
                        capture_output=True,
                        text=True,
                        timeout=1200,
                    )
                    self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
