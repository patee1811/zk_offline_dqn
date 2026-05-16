import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def run_cli(args, *, env=None):
    completed = subprocess.run(
        [sys.executable, "-m", "zk_offline_dqn.cli.main", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed


class CliSmokeTests(unittest.TestCase):
    def test_cli_modules_import_normally(self):
        __import__("zk_offline_dqn.cli.main")
        __import__("zk_offline_dqn.cli.verify")
        __import__("zk_offline_dqn.cli.benchmark")
        __import__("zk_offline_dqn.cli.report")

    def test_help_commands_work(self):
        main_help = run_cli(["--help"])
        verify_help = run_cli(["verify", "--help"])

        self.assertEqual(main_help.returncode, 0)
        self.assertIn("verify", main_help.stdout)
        self.assertEqual(verify_help.returncode, 0)
        self.assertIn("td-mvp", verify_help.stdout)

    def test_valid_verify_commands_accept(self):
        commands = [
            ["verify", "membership"],
            [
                "verify",
                "td-mvp",
                "--input",
                "zk_backend/test_vectors/td_mvp_case_0.json",
            ],
            [
                "verify",
                "forward-td-mlp",
                "--input",
                "artifacts/fixtures/forward_td_mlp/forward_td_mlp_batch_size_1.json",
            ],
            [
                "verify",
                "one-step-sgd-tiny",
                "--input",
                "artifacts/fixtures/one_step_sgd_tiny/one_step_sgd_tiny_valid.json",
            ],
            ["verify", "minibatch-td"],
        ]

        for command in commands:
            with self.subTest(command=command):
                completed = run_cli(command)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("accepted = True", completed.stdout)

    def test_rejected_cli_input_returns_nonzero(self):
        base_path = REPO_ROOT / "zk_backend/test_vectors/td_mvp_case_0.json"
        with base_path.open("r", encoding="utf-8") as f:
            vector = json.load(f)

        tampered = copy.deepcopy(vector)
        tampered["schema_version"] = "wrong"

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = pathlib.Path(tmpdir) / "tampered_td_mvp.json"
            temp_path.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
            completed = run_cli(["verify", "td-mvp", "--input", str(temp_path)])

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("accepted = False", completed.stdout)

    def test_old_scripts_still_run(self):
        for script in [
            "scripts/artifacts_export/verify_minibatch_td_artifact.py",
            "scripts/artifacts_export/verify_one_step_update_artifact.py",
        ]:
            with self.subTest(script=script):
                completed = subprocess.run(
                    [sys.executable, script],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("verification_passed = True", completed.stdout)

    def test_old_short_trace_script_still_runs_with_canonical_env(self):
        env = os.environ.copy()
        env.update(
            {
                "SHORT_TRACE_ARTIFACT_PATH": "artifacts/fixtures/short_trace/short_trace_update_artifact.json",
                "SHORT_TRACE_MERKLE_PATH": "artifacts/fixtures/membership/cartpole_dqn_eps010_merkle.json",
                "SHORT_TRACE_INITIAL_CHECKPOINT_PATH": "models/offline_dqn_with_target_seed42_best.pt",
                "SHORT_TRACE_FINAL_CHECKPOINT_PATH": "artifacts/fixtures/short_trace/short_trace_work/step_1_post_synced_4_5_6_7.pt",
                "SHORT_TRACE_WORK_DIR": "artifacts/fixtures/short_trace/short_trace_work",
            }
        )
        completed = subprocess.run(
            [sys.executable, "scripts/artifacts_export/verify_short_trace_update_artifact.py"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("verification_passed = True", completed.stdout)


if __name__ == "__main__":
    unittest.main()
