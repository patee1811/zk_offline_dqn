from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_REPO_NAME = "zk_offline_dqn"
DEFAULT_REPO_URL = "https://github.com/patee1811/zk_offline_dqn.git"
DEFAULT_REPO_BRANCH = "cleanup-project-structure"
SUMMARY_PATH = Path("artifacts/reports/kaggle_sp1_validation_summary.json")
ARCHIVE_EXTRACT_DIR = Path("/kaggle/working/zk_offline_dqn_phase6b_archive")
REMOTE_CLONE_DIR = Path("/kaggle/working/zk_offline_dqn_phase6b_remote")


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


def run_labeled(
    label: str,
    command: List[str],
    cwd: Path,
    timeout: Optional[int] = None,
    env_updates: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    started = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd)
    env.setdefault("MPLBACKEND", "Agg")
    if env_updates:
        env.update(env_updates)
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
        "label": label,
        "command": command,
        "cwd": cwd.as_posix(),
        "returncode": returncode,
        "duration_sec": round(elapsed, 4),
        "stdout_tail": tail(stdout),
        "stderr_tail": tail(stderr),
        "status": status,
    }
    print("label =", label)
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


def clone_repo(target: Path, branch: str) -> Dict[str, Any]:
    repo_url = (
        os.environ.get("ZK_OFFLINE_DQN_REPO_URL")
        or os.environ.get("REPO_URL")
        or DEFAULT_REPO_URL
    )
    if target.exists():
        return {
            "label": "git_clone",
            "command": ["git", "clone", "-b", branch, repo_url, target.as_posix()],
            "cwd": target.parent.as_posix(),
            "returncode": 0,
            "duration_sec": 0.0,
            "stdout_tail": f"target already exists: {target}",
            "stderr_tail": "",
            "status": "skipped_existing_target",
        }
    command = ["git", "clone", "-b", branch, repo_url, target.as_posix()]
    return run_labeled("git_clone", command, cwd=target.parent)


def find_archive() -> Optional[Path]:
    archive_name = os.environ.get("ZK_OFFLINE_DQN_ARCHIVE_NAME", "")
    candidates = []
    search_roots = [Path.cwd(), Path("/kaggle/working"), Path("/kaggle/input")]
    for root in search_roots:
        if not root.exists():
            continue
        if archive_name:
            direct = root / archive_name
            if direct.exists():
                return direct
        candidates.extend(root.rglob("*.zip"))
    for candidate in candidates:
        if archive_name and candidate.name != archive_name:
            continue
        if "zk_offline_dqn" in candidate.name or "phase6b" in candidate.name:
            return candidate
    return None


def extract_archive(target: Path) -> tuple[Optional[Path], Dict[str, Any]]:
    archive_path = find_archive()
    if archive_path is None:
        return None, {
            "label": "extract_archive",
            "command": ["extract", os.environ.get("ZK_OFFLINE_DQN_ARCHIVE_NAME", "<missing>")],
            "cwd": Path.cwd().as_posix(),
            "returncode": 1,
            "duration_sec": 0.0,
            "stdout_tail": "",
            "stderr_tail": "workspace archive not found",
            "status": "failed",
        }
    branch = os.environ.get("ZK_OFFLINE_DQN_GIT_BRANCH") or DEFAULT_REPO_BRANCH
    clone_event = clone_repo(target, branch)
    if not looks_like_repo(target):
        return None, {
            "label": "extract_archive",
            "command": ["clone_then_extract", archive_path.as_posix(), target.as_posix()],
            "cwd": Path.cwd().as_posix(),
            "returncode": 1,
            "duration_sec": clone_event.get("duration_sec", 0.0),
            "stdout_tail": clone_event.get("stdout_tail", ""),
            "stderr_tail": "remote clone for archive overlay did not produce a valid repo",
            "status": "failed",
            "clone_event": clone_event,
        }
    started = time.perf_counter()
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as archive:
        archive.extractall(target)
    elapsed = time.perf_counter() - started
    repo_root = target
    if not looks_like_repo(repo_root):
        nested = [path for path in target.iterdir() if path.is_dir() and looks_like_repo(path)]
        repo_root = nested[0] if nested else target
    return repo_root, {
        "label": "extract_archive",
        "command": ["extract", archive_path.as_posix(), target.as_posix()],
        "cwd": Path.cwd().as_posix(),
        "returncode": 0,
        "duration_sec": round(elapsed, 4),
        "stdout_tail": f"cloned branch {branch} and overlaid {archive_path} onto {target}",
        "stderr_tail": "",
        "status": "passed",
        "clone_event": clone_event,
    }


def ensure_phase6_support_files(repo_root: Path) -> None:
    diagnostic = repo_root / "scripts/experiments/check_sp1_environment.py"
    if diagnostic.exists():
        return
    diagnostic.parent.mkdir(parents=True, exist_ok=True)
    diagnostic.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import platform, shutil, subprocess, sys",
                "from pathlib import Path",
                "def check(cmd):",
                "    exe = shutil.which(cmd[0])",
                "    if exe is None:",
                "        print(cmd[0] + '_available = False')",
                "        return",
                "    result = subprocess.run(cmd, text=True, capture_output=True)",
                "    print(cmd[0].replace(' ', '_') + '_available = ' + str(result.returncode == 0))",
                "    if result.stdout.strip():",
                "        print(cmd[0] + '_stdout = ' + result.stdout.strip().splitlines()[0])",
                "    if result.stderr.strip():",
                "        print(cmd[0] + '_stderr = ' + result.stderr.strip().splitlines()[0])",
                "print('=== SP1 ENVIRONMENT DIAGNOSTIC ===')",
                "print('python = ' + sys.version)",
                "print('platform = ' + platform.platform())",
                "print('cwd = ' + Path.cwd().as_posix())",
                "print('is_kaggle = ' + str(Path('/kaggle').exists()))",
                "print('sp1_dir_exists = ' + str(Path('zk_backend/td_mvp/sp1').exists()))",
                "check(['rustc', '--version'])",
                "check(['cargo', '--version'])",
                "check(['cargo', 'prove', '--version'])",
                "check(['sp1up', '--version'])",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def git_info(repo_root: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {"is_git": (repo_root / ".git").exists()}
    if not info["is_git"]:
        return info
    for label, command in [
        ("git_commit", ["git", "rev-parse", "HEAD"]),
        ("git_branch", ["git", "branch", "--show-current"]),
        ("git_status_short", ["git", "status", "--short"]),
    ]:
        result = subprocess.run(
            command,
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        info[label] = result.stdout.strip()
        print(f"{label} = {info[label]}")
    return info


def discover_repo_root() -> tuple[Optional[Path], List[Dict[str, Any]], str, str]:
    events: List[Dict[str, Any]] = []
    source_mode = os.environ.get("ZK_OFFLINE_DQN_SOURCE_MODE", "remote").strip().lower()
    git_branch = os.environ.get("ZK_OFFLINE_DQN_GIT_BRANCH") or os.environ.get(
        "ZK_OFFLINE_DQN_REPO_BRANCH", DEFAULT_REPO_BRANCH
    )
    if source_mode == "archive":
        repo_root, event = extract_archive(ARCHIVE_EXTRACT_DIR)
        events.append(event)
        if repo_root is not None and looks_like_repo(repo_root):
            return repo_root.resolve(), events, source_mode, git_branch
        return None, events, source_mode, git_branch

    event = clone_repo(REMOTE_CLONE_DIR, git_branch)
    events.append(event)
    if looks_like_repo(REMOTE_CLONE_DIR):
        return REMOTE_CLONE_DIR.resolve(), events, source_mode, git_branch
    return None, events, source_mode, git_branch


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


def refresh_toolchain_path() -> None:
    home = Path.home()
    additions = [
        home / ".sp1/bin",
        home / ".cargo/bin",
    ]
    current = os.environ.get("PATH", "")
    prefix = os.pathsep.join(path.as_posix() for path in additions if path.exists())
    if prefix:
        os.environ["PATH"] = prefix + os.pathsep + current


def command_status(commands: List[Dict[str, Any]], label: str) -> Optional[str]:
    for item in reversed(commands):
        if item.get("label") == label:
            return item.get("status")
    return None


def main() -> int:
    print("=== KAGGLE SP1 VALIDATION ===")
    print("python =", sys.version)
    print("platform =", platform.platform())
    print("cwd =", Path.cwd().as_posix())
    print("is_kaggle_path =", Path("/kaggle").exists())
    print()

    repo_root, discovery_events, source_mode, git_branch = discover_repo_root()
    commands: List[Dict[str, Any]] = list(discovery_events)
    if repo_root is None:
        summary = {
            "status": "repo_not_found",
            "source_mode": source_mode,
            "git_branch": git_branch,
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
    ensure_phase6_support_files(repo_root)
    git_metadata = git_info(repo_root)
    py = sys.executable
    python_commands = [
        ("compileall", [py, "-m", "compileall", "zk_offline_dqn", "scripts", "tests"]),
        ("unittest_regression", [py, "-m", "unittest", "discover", "tests/regression"]),
        ("td_mvp_cli", [
            py, "-m", "zk_offline_dqn.cli.main", "verify", "td-mvp",
            "--input", "zk_backend/test_vectors/td_mvp_case_0.json",
        ]),
        ("distinct_td_python_smoke", [
            py, "scripts/experiments/benchmark_distinct_td_sp1.py",
            "--skip-sp1", "--out-dir", "artifacts/benchmarks/distinct_td_sp1_python_smoke",
        ]),
        ("forward_td_mlp_python_smoke", [
            py, "scripts/experiments/benchmark_forward_td_mlp_sp1.py",
            "--skip-sp1", "--out-dir", "artifacts/benchmarks/forward_td_mlp_sp1_python_smoke",
        ]),
        ("one_step_sgd_tiny_python_smoke", [
            py, "scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py",
            "--skip-sp1", "--out-dir", "artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke",
        ]),
        ("check_sp1_environment_before_setup", [py, "scripts/experiments/check_sp1_environment.py"]),
    ]
    python_results: List[Dict[str, Any]] = []
    for label, command in python_commands:
        result = run_labeled(label, command, cwd=repo_root)
        python_results.append(result)
        commands.append(result)

    cargo_available_before = cargo_available()
    if os.environ.get("RUN_SP1_SETUP") == "1":
        setup_script = repo_root / "scripts/experiments/setup_sp1_on_kaggle.sh"
        setup_env = {
            "RUN_SP1_EXECUTE": "0",
            "RUN_SP1_PROVE": "0",
        }
        commands.append(
            run_labeled(
                "sp1_setup",
                ["bash", str(setup_script)],
                cwd=repo_root,
                timeout=3600,
                env_updates=setup_env,
            )
        )
        refresh_toolchain_path()
        commands.append(
            run_labeled(
                "check_sp1_environment_after_setup",
                [py, "scripts/experiments/check_sp1_environment.py"],
                cwd=repo_root,
            )
        )

    sp1_dir = repo_root / "zk_backend/td_mvp/sp1"
    host_package = inspect_package_name(sp1_dir / "host/Cargo.toml")
    guest_package = inspect_package_name(sp1_dir / "guest/Cargo.toml")
    shared_package = inspect_package_name(sp1_dir / "shared/Cargo.toml")
    cargo_status = {
        "cargo_available_before": cargo_available_before,
        "cargo_available_after": cargo_available(),
        "sp1_dir_exists": sp1_dir.exists(),
        "host_package": host_package,
        "guest_package": guest_package,
        "shared_package": shared_package,
    }

    if cargo_status["cargo_available_after"] and sp1_dir.exists():
        commands.append(run_labeled("cargo_test", ["cargo", "test"], cwd=sp1_dir, timeout=1800))
        if host_package and os.environ.get("RUN_SP1_EXECUTE") == "1":
            execute_command = [
                "cargo",
                "run",
                "--release",
                "-p",
                host_package,
                "--",
                "--execute",
            ]
            commands.append(run_labeled("sp1_execute", execute_command, cwd=sp1_dir, timeout=1800))
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
                commands.append(run_labeled("sp1_prove", prove_command, cwd=sp1_dir, timeout=7200))
            else:
                commands.append(
                    {
                        "label": "sp1_prove",
                        "command": ["RUN_SP1_PROVE=1", "cargo", "run", "--release", "-p", host_package, "--", "--prove"],
                        "cwd": sp1_dir.as_posix(),
                        "returncode": None,
                        "duration_sec": 0.0,
                        "stdout_tail": "Proof not run because RUN_SP1_PROVE is not set to 1.",
                        "stderr_tail": "",
                        "status": "skipped",
                    }
                )
        elif host_package:
            commands.append(
                {
                    "label": "sp1_execute",
                    "command": ["RUN_SP1_EXECUTE=1", "cargo", "run", "--release", "-p", host_package, "--", "--execute"],
                    "cwd": sp1_dir.as_posix(),
                    "returncode": None,
                    "duration_sec": 0.0,
                    "stdout_tail": "Execute not run because RUN_SP1_EXECUTE is not set to 1.",
                    "stderr_tail": "",
                    "status": "skipped",
                }
            )
    else:
        commands.append(
            {
                "label": "cargo_test",
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
        "source_mode": source_mode,
        "git_branch": git_branch,
        "git_commit": git_metadata.get("git_commit"),
        "git_metadata": git_metadata,
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": Path.cwd().as_posix(),
        "repo_root": repo_root.as_posix(),
        "cargo_status": cargo_status,
        "cargo_available_before": cargo_available_before,
        "cargo_available_after": cargo_status["cargo_available_after"],
        "cargo_test_status": command_status(commands, "cargo_test"),
        "sp1_execute_status": command_status(commands, "sp1_execute"),
        "sp1_prove_status": command_status(commands, "sp1_prove"),
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
