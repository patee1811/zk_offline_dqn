import os
import shutil
import tempfile
import unittest
from pathlib import Path

from zk_offline_dqn.backends.sp1.forward_td_mlp import (
    cargo_command,
    load_case,
    tampered_case,
    verify_case_reference,
    BACKEND_DIR,
)
from scripts.experiments.run_phase4_sp1_forward_td_mlp_validation import TAMPER_CASES, write_json
import subprocess


class Sp1ForwardTdMlpTamperTests(unittest.TestCase):
    def test_python_reference_rejects_tamper_cases(self):
        case = load_case()
        for name in TAMPER_CASES:
            result = verify_case_reference(tampered_case(case, name))
            self.assertFalse(result.accepted, name)

    def test_execute_mode_tamper_opt_in(self):
        if os.environ.get("RUN_SP1_EXECUTE") != "1":
            self.skipTest("SP1 execute test is opt-in with RUN_SP1_EXECUTE=1")
        if shutil.which("cargo") is None:
            self.skipTest("cargo is unavailable")
        case = load_case()
        with tempfile.TemporaryDirectory() as tmp:
            for name in TAMPER_CASES:
                path = Path(tmp) / f"{name}.json"
                write_json(path, tampered_case(case, name))
                result = subprocess.run(cargo_command(case_path=path), cwd=BACKEND_DIR, text=True, capture_output=True, timeout=1200)
                self.assertNotEqual(result.returncode, 0, name)


if __name__ == "__main__":
    unittest.main()

