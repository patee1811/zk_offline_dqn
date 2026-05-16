import importlib
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FULL_REGRESSION_SCRIPT = REPO_ROOT / "scripts/experiments/run_full_regression.py"


class FullRegressionWrapperTests(unittest.TestCase):
    def test_full_regression_runner_exists(self):
        self.assertTrue(FULL_REGRESSION_SCRIPT.exists())

    def test_full_regression_runner_imports_without_running(self):
        module = importlib.import_module("scripts.experiments.run_full_regression")

        self.assertTrue(callable(module.main))
        self.assertEqual(module.SUMMARY_JSON.as_posix(), "artifacts/regression_summary.json")
        self.assertEqual(module.SUMMARY_MD.as_posix(), "artifacts/regression_summary.md")

    def test_full_regression_remains_authoritative_command(self):
        command = "python scripts/experiments/run_full_regression.py"

        self.assertIn("run_full_regression.py", command)
        self.assertEqual(
            FULL_REGRESSION_SCRIPT.relative_to(REPO_ROOT).as_posix(),
            "scripts/experiments/run_full_regression.py",
        )


if __name__ == "__main__":
    unittest.main()
