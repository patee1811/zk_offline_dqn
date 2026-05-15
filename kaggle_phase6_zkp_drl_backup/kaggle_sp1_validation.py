from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_REPO_NAME = "zk_offline_dqn"
SUMMARY_PATH = Path("artifacts/reports/kaggle_sp1_validation_summary.json")


def tail(text: str, lines: int = 40) -> str:
    return "\n".join(text.splitlines()[-lines:])


def run_command(command: List[str], cwd: Path, timeout: Optional[int] = None) -> Dict[str, Any]:
    started = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd)
    env.setdefault("MPLBACKEND", "Agg")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        status = "passed" if returncode == 0 else "failed"
    except subprocess.TimeoutExpired as exc:
        returncode = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        status = "timeout"
    except Exception as exc:  # pragma: no cover - environment dependent
        returncode = None
        stdout = ""
        stderr = repr(exc)
        status = "error"
    elapsed = time.perf_counter() - started
    record = {
        "command": command,
        "cwd": cwd.as_posix(),
        "returncode": returncode,
        "duration_sec": round(elapsed, 4),
        "stdout_tail": tail(stdout),
        "stderr_tail": tail(stderr),
        "status": status,
    }
    print("command =", " ".join(command))
    print("status =", status)
    print("returncode =", returncode)
    print("duration_sec =", record["duration_sec"])
    if record["stdout_tail"]:
        print("stdout_tail =")
        print(record["stdout_tail"])
    if record["stderr_tail"]:
        print("stderr_tail =")
        print(record["stderr_tail"])
    print()
    return record


def looks_like_repo(path: Path) -> bool:
    return (
        (path / "zk_offline_dqn").is_dir()
        and (path / "scripts/experiments").is_dir()
        and (path / "zk_backend/test_vectors/td_mvp_case_0.json").exists()
    )


def clone_repo_if_requested(target: Path) -> Optional[Dict[str, Any]]:
    repo_url = os.environ.get("ZK_OFFLINE_DQN_REPO_URL") or os.environ.get("REPO_URL")
    if not repo_url:
        return None
    if target.exists():
        return {
            "command": ["git", "clone", repo_url, target.as_posix()],
            "cwd": target.parent.as_posix(),
            "returncode": 0,
            "duration_sec": 0.0,
            "stdout_tail": f"target already exists: {target}",
            "stderr_tail": "",
            "status": "skipped_existing_target",
        }
    return run_command(["git", "clone", repo_url, target.as_posix()], cwd=target.parent)


def discover_repo_root() -> tuple[Optional[Path], List[Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    candidates = [
        Path.cwd(),
        SCRIPT_PATH.parents[2] if len(SCRIPT_PATH.parents) > 2 else SCRIPT_PATH.parent,
        Path("/kaggle/working/zk_offline_dqn"),
        Path("/kaggle/working") / DEFAULT_REPO_NAME,
    ]
    for candidate in candidates:
        if looks_like_repo(candidate):
            return candidate.resolve(), events

    clone_target = Path("/kaggle/working") / DEFAULT_REPO_NAME
    if Path("/kaggle/working").exists():
        event = clone_repo_if_requested(clone_target)
        if event is not None:
            events.append(event)
        if looks_like_repo(clone_target):
            return clone_target.resolve(), events

    return None, events


def inspect_package_name(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("name = "):
            return stripped.split("=", 1)[1].strip().strip('"')
    return None


def cargo_available() -> bool:
    return shutil.which("cargo") is not None


def main() -> int:
    print("=== KAGGLE SP1 VALIDATION ===")
    print("python =", sys.version)
    print("platform =", platform.platform())
    print("cwd =", Path.cwd().as_posix())
    print("is_kaggle_path =", Path("/kaggle").exists())
    print()

    repo_root, discovery_events = discover_repo_root()
    commands: List[Dict[str, Any]] = list(discovery_events)
    if repo_root is None:
        summary = {
            "status": "repo_not_found",
            "python": sys.version,
            "platform": platform.platform(),
            "cwd": Path.cwd().as_posix(),
            "commands": commands,
            "message": (
                "Could not locate repository files. Upload this repository to the "
                "Kaggle kernel working directory or set ZK_OFFLINE_DQN_REPO_URL."
            ),
        }
        SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0

    print("repo_root =", repo_root.as_posix())
    py = sys.executable
    python_commands = [
        [py, "-m", "compileall", "zk_offline_dqn", "scripts", "src", "tests"],
        [py, "-m", "unittest", "discover", "tests/regression"],
        [
            py,
            "-m",
            "zk_offline_dqn.cli.main",
            "verify",
            "td-mvp",
            "--input",
            "zk_backend/test_vectors/td_mvp_case_0.json",
        ],
        [
            py,
            "scripts/experiments/benchmark_distinct_td_sp1.py",
            "--skip-sp1",
            "--out-dir",
            "artifacts/benchmarks/distinct_td_sp1_python_smoke",
        ],
        [
            py,
            "scripts/experiments/benchmark_forward_td_mlp_sp1.py",
            "--skip-sp1",
            "--out-dir",
            "artifacts/benchmarks/forward_td_mlp_sp1_python_smoke",
        ],
        [
            py,
            "scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py",
            "--skip-sp1",
            "--out-dir",
            "artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke",
        ],
        [py, "scripts/experiments/check_sp1_environment.py"],
    ]
    python_results: List[Dict[str, Any]] = []
    for command in python_commands:
        result = run_command(command, cwd=repo_root)
        python_results.append(result)
        commands.append(result)

    sp1_dir = repo_root / "zk_backend/td_mvp/sp1"
    host_package = inspect_package_name(sp1_dir / "host/Cargo.toml")
    guest_package = inspect_package_name(sp1_dir / "guest/Cargo.toml")
    shared_package = inspect_package_name(sp1_dir / "shared/Cargo.toml")
    cargo_status = {
        "cargo_available": cargo_available(),
        "sp1_dir_exists": sp1_dir.exists(),
        "host_package": host_package,
        "guest_package": guest_package,
        "shared_package": shared_package,
    }

    if cargo_status["cargo_available"] and sp1_dir.exists():
        commands.append(run_command(["cargo", "test"], cwd=sp1_dir, timeout=1800))
        if host_package:
            execute_command = [
                "cargo",
                "run",
                "--release",
                "-p",
                host_package,
                "--",
                "--execute",
            ]
            commands.append(run_command(execute_command, cwd=sp1_dir, timeout=1800))
            if os.environ.get("RUN_SP1_PROVE") == "1":
                prove_command = [
                    "cargo",
                    "run",
                    "--release",
                    "-p",
                    host_package,
                    "--",
                    "--prove",
                ]
                commands.append(run_command(prove_command, cwd=sp1_dir, timeout=7200))
            else:
                commands.append(
                    {
                        "command": ["RUN_SP1_PROVE=1", "cargo", "run", "--release", "-p", host_package, "--", "--prove"],
                        "cwd": sp1_dir.as_posix(),
                        "returncode": None,
                        "duration_sec": 0.0,
                        "stdout_tail": "Proof not run because RUN_SP1_PROVE is not set to 1.",
                        "stderr_tail": "",
                        "status": "skipped",
                    }
                )
    else:
        commands.append(
            {
                "command": ["cargo", "test"],
                "cwd": sp1_dir.as_posix(),
                "returncode": None,
                "duration_sec": 0.0,
                "stdout_tail": "Cargo/SP1 workspace unavailable; Rust/SP1 commands skipped.",
                "stderr_tail": "",
                "status": "skipped",
            }
        )

    summary = {
        "status": "completed",
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": Path.cwd().as_posix(),
        "repo_root": repo_root.as_posix(),
        "cargo_status": cargo_status,
        "commands": commands,
        "all_required_python_passed": all(item["status"] == "passed" for item in python_results),
        "sp1_prove_requested": os.environ.get("RUN_SP1_PROVE") == "1",
    }
    output_path = repo_root / SUMMARY_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("summary_path =", output_path.as_posix())
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
