"""Command builders for SP1/Python alignment checks.

The functions in this module only return argv lists. They never execute
commands and therefore remain safe to import from regression tests.
"""

from __future__ import annotations

from typing import List


def local_python_sp1_smoke_commands(python: str = "python") -> List[List[str]]:
    return [
        [python, "-m", "compileall", "zk_offline_dqn", "scripts", "src", "tests"],
        [python, "-m", "unittest", "discover", "tests/regression"],
        [
            python,
            "-m",
            "zk_offline_dqn.cli.main",
            "verify",
            "td-mvp",
            "--input",
            "zk_backend/test_vectors/td_mvp_case_0.json",
        ],
        [
            python,
            "scripts/experiments/benchmark_distinct_td_sp1.py",
            "--skip-sp1",
            "--out-dir",
            "artifacts/benchmarks/distinct_td_sp1_python_smoke",
        ],
        [
            python,
            "scripts/experiments/benchmark_forward_td_mlp_sp1.py",
            "--skip-sp1",
            "--out-dir",
            "artifacts/benchmarks/forward_td_mlp_sp1_python_smoke",
        ],
        [
            python,
            "scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py",
            "--skip-sp1",
            "--out-dir",
            "artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke",
        ],
        [python, "scripts/experiments/check_sp1_environment.py"],
    ]


def kaggle_setup_check_commands() -> List[List[str]]:
    return [
        ["kaggle", "kernels", "list", "--mine"],
        ["kaggle", "kernels", "list", "--mine", "--search", "zkp-drl"],
    ]


def kaggle_notebook_validation_commands(python: str = "python") -> List[List[str]]:
    return [
        [python, "scripts/experiments/run_phase6_kaggle_validation.py"],
        ["kaggle", "kernels", "output", "<owner/slug>", "-p", "kaggle_phase6_outputs"],
    ]


def wsl2_linux_sp1_commands(
    cargo: str = "cargo",
    host_package: str = "td-mvp-host",
) -> List[List[str]]:
    # Execute/proof commands require the Rust/SP1 toolchain and a Linux-capable
    # environment such as WSL2 or Kaggle.
    return [
        [cargo, "test"],
        [cargo, "run", "--release", "-p", host_package, "--", "--execute"],
        [cargo, "run", "--release", "-p", host_package, "--", "--prove"],
    ]


def sp1_execute_command(
    input_path: str = "zk_backend/test_vectors/td_mvp_case_0.json",
    cargo: str = "cargo",
    host_package: str = "td-mvp-host",
) -> List[str]:
    return [
        cargo,
        "run",
        "--release",
        "-p",
        host_package,
        "--",
        "--input",
        input_path,
        "--case",
        "valid_control",
        "--execute",
    ]


def sp1_prove_command(
    input_path: str = "zk_backend/test_vectors/td_mvp_case_0.json",
    cargo: str = "cargo",
    host_package: str = "td-mvp-host",
) -> List[str]:
    command = sp1_execute_command(input_path, cargo, host_package)
    command.append("--prove")
    return command
