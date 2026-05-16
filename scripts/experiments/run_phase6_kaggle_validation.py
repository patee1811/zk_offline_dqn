from __future__ import annotations

import argparse
import base64
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
PULL_DIR = ROOT / "kaggle_phase6_zkp_drl"
BACKUP_ROOT = ROOT / "kaggle_phase6_zkp_drl_backup"
NEW_KERNEL_DIR = ROOT / "kaggle_phase6_sp1_validation"
OUTPUT_DIR = ROOT / "kaggle_phase6_outputs"
SUMMARY_PATH = ROOT / "artifacts/reports/phase6_kaggle_api_summary.json"
LOCAL_ARCHIVE_NAME = "zk_offline_dqn_phase6b_workspace.zip"


def now_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def tail(text: str, lines: int = 30) -> str:
    return "\n".join(text.splitlines()[-lines:])


def find_kaggle_executable() -> Optional[List[str]]:
    executable = shutil.which("kaggle")
    if executable:
        return [executable]

    scripts_dir = Path(sys.executable).resolve().parent / "Scripts"
    candidates = [
        scripts_dir / "kaggle.exe",
        scripts_dir / "kaggle",
        Path.home() / "AppData/Roaming/Python/Python310/Scripts/kaggle.exe",
        Path.home() / "AppData/Local/Programs/Python/Python310/Scripts/kaggle.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return [str(candidate)]
    return None


def run(command: List[str], cwd: Path = ROOT, timeout: int = 300) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
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
    except Exception as exc:  # pragma: no cover - platform dependent
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
        "stdout": stdout,
        "stderr": stderr,
        "status": status,
    }
    print("command =", " ".join(command))
    print("status =", status)
    print("returncode =", returncode)
    if record["stdout_tail"]:
        print(record["stdout_tail"])
    if record["stderr_tail"]:
        print(record["stderr_tail"])
    print()
    return record


def parse_kernel_refs(output: str) -> List[str]:
    pattern = re.compile(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+")
    refs: List[str] = []
    for match in pattern.findall(output):
        if match not in refs:
            refs.append(match)
    return refs


def choose_kernel(refs: List[str]) -> Optional[str]:
    if not refs:
        return None
    ranked = sorted(
        refs,
        key=lambda ref: (
            0 if ref.split("/", 1)[1] == "zkp-drl" else 1,
            0 if "zkp-drl" in ref else 1,
            len(ref),
        ),
    )
    return ranked[0]


def backup_folder(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    backup_path = BACKUP_ROOT
    if backup_path.exists():
        backup_path = ROOT / f"kaggle_phase6_zkp_drl_backup_{now_stamp()}"
    shutil.copytree(path, backup_path)
    return backup_path


def git_worktree_has_uncommitted_changes() -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    return bool(result.stdout.strip())


def should_include_in_archive(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    if path.is_dir():
        return False
    parts = relative.split("/")
    excluded_parts = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "kaggle_phase6_outputs",
        "kaggle_phase6_zkp_drl",
        "kaggle_phase6_zkp_drl_backup",
        "kaggle_phase6_sp1_validation",
        "target",
    }
    if any(part in excluded_parts for part in parts):
        return False
    if any(part.startswith("kaggle_phase6_zkp_drl_backup") for part in parts):
        return False
    if fnmatch.fnmatch(relative, "artifacts/benchmarks/*_python_smoke*"):
        return False
    if relative.endswith((".pyc", ".pyo")):
        return False

    required_artifacts = {
        "artifacts/fixtures/membership/sample_transition_membership.json",
        "artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json",
    }
    required_artifact_prefixes = (
        "artifacts/fixtures/forward_td_mlp/",
        "artifacts/fixtures/one_step_sgd_tiny/",
    )
    if relative in required_artifacts or any(
        relative.startswith(prefix) for prefix in required_artifact_prefixes
    ):
        return True

    source_prefixes = (
        "zk_offline_dqn/",
        "scripts/",
        "tests/",
        "docs/",
        "zk_backend/",
    )
    root_files = {
        ".gitignore",
        "LICENSE",
        "Makefile",
        "README.md",
        "requirements.txt",
        "setup.py",
    }
    return (
        relative in root_files
        or any(relative.startswith(prefix) for prefix in source_prefixes)
    )


def create_local_workspace_archive(folder: Path) -> Path:
    archive_path = folder / LOCAL_ARCHIVE_NAME
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in ROOT.rglob("*"):
            if path == archive_path or not should_include_in_archive(path):
                continue
            archive.write(path, path.relative_to(ROOT).as_posix())
    return archive_path


def write_validation_notebook(
    folder: Path,
    *,
    source_mode: str,
    git_branch: str,
    run_sp1_setup: bool,
    run_sp1_execute: bool,
    run_sp1_prove: bool,
    archive_path: Optional[Path],
) -> Path:
    notebook_path = folder / "phase6_sp1_validation.ipynb"
    script = (ROOT / "scripts/experiments/kaggle_sp1_validation.py").read_text(
        encoding="utf-8"
    )
    env_lines = [
        "import os\n",
        f"os.environ['ZK_OFFLINE_DQN_SOURCE_MODE'] = {source_mode!r}\n",
        f"os.environ['ZK_OFFLINE_DQN_GIT_BRANCH'] = {git_branch!r}\n",
        f"os.environ['RUN_SP1_SETUP'] = {'1' if run_sp1_setup else '0'!r}\n",
        f"os.environ['RUN_SP1_EXECUTE'] = {'1' if run_sp1_execute else '0'!r}\n",
        f"os.environ['RUN_SP1_PROVE'] = {'1' if run_sp1_prove else '0'!r}\n",
    ]
    if archive_path is not None:
        env_lines.append(f"os.environ['ZK_OFFLINE_DQN_ARCHIVE_NAME'] = {archive_path.name!r}\n")
        encoded = base64.b64encode(archive_path.read_bytes()).decode("ascii")
        chunks = [encoded[index:index + 76000] for index in range(0, len(encoded), 76000)]
        env_lines.extend(
            [
                "import base64\n",
                "from pathlib import Path\n",
                f"archive_chunks = {chunks!r}\n",
                f"Path({archive_path.name!r}).write_bytes(base64.b64decode(''.join(archive_chunks)))\n",
            ]
        )
    cell_source = [
        *env_lines,
        "script = ",
        repr(script),
        "\n",
        "namespace = {'__name__': 'phase6_embedded', '__file__': 'kaggle_sp1_validation_embedded.py'}\n",
        "exec(compile(script, 'kaggle_sp1_validation_embedded.py', 'exec'), namespace)\n",
        "namespace['main']()\n",
    ]
    notebook = {
        "cells": [
            {
                "id": "phase6-title",
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Phase 6 SP1 Validation\n",
                    "\n",
                    "This notebook runs Python-side relation checks and optional Rust/SP1 checks.\n",
                ],
            },
            {
                "id": "phase6-validation",
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cell_source,
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    return notebook_path


def copy_validation_assets(
    folder: Path,
    *,
    source_mode: str,
    git_branch: str,
    run_sp1_setup: bool,
    run_sp1_execute: bool,
    run_sp1_prove: bool,
    archive_path: Optional[Path],
) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "scripts/experiments/kaggle_sp1_validation.py", folder / "kaggle_sp1_validation.py")
    shutil.copy2(ROOT / "scripts/experiments/setup_sp1_on_kaggle.sh", folder / "setup_sp1_on_kaggle.sh")
    write_validation_notebook(
        folder,
        source_mode=source_mode,
        git_branch=git_branch,
        run_sp1_setup=run_sp1_setup,
        run_sp1_execute=run_sp1_execute,
        run_sp1_prove=run_sp1_prove,
        archive_path=archive_path,
    )


def load_metadata(folder: Path) -> Dict[str, Any]:
    metadata_path = folder / "kernel-metadata.json"
    if metadata_path.exists():
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    username = os.environ.get("KAGGLE_USERNAME", "unknown")
    return {
        "id": f"{username}/phase6-sp1-validation",
        "title": "Phase 6 SP1 Validation",
        "code_file": "phase6_sp1_validation.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": False,
        "enable_internet": True,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }


def update_metadata(folder: Path, kernel_ref: Optional[str]) -> Dict[str, Any]:
    metadata = load_metadata(folder)
    if kernel_ref:
        metadata["id"] = kernel_ref
    metadata["code_file"] = "phase6_sp1_validation.ipynb"
    metadata["language"] = "python"
    metadata["kernel_type"] = "notebook"
    metadata.setdefault("is_private", True)
    metadata.setdefault("enable_gpu", False)
    metadata.setdefault("enable_internet", True)
    metadata.setdefault("dataset_sources", [])
    metadata.setdefault("competition_sources", [])
    metadata.setdefault("kernel_sources", [])
    (folder / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def manual_instructions(reason: str) -> List[str]:
    return [
        f"Kaggle API automation did not complete: {reason}",
        "Manual fallback:",
        "1. Ensure the Kaggle CLI is installed and on PATH.",
        "2. Run: kaggle kernels list --mine",
        "3. Run: kaggle kernels list --mine --search zkp-drl",
        "4. Pull the kernel: kaggle kernels pull <owner/slug> -p kaggle_phase6_zkp_drl -m",
        "5. Copy scripts/experiments/kaggle_sp1_validation.py into the kernel or upload the repo.",
        "6. Push: kaggle kernels push -p kaggle_phase6_zkp_drl",
        "7. Retrieve outputs: kaggle kernels output <owner/slug> -p kaggle_phase6_outputs",
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-branch", default="cleanup-project-structure")
    parser.add_argument("--use-local-archive", action="store_true")
    parser.add_argument("--run-sp1-setup", action="store_true")
    parser.add_argument("--run-sp1-execute", action="store_true")
    parser.add_argument("--run-sp1-prove", action="store_true")
    return parser.parse_args()


def write_summary(summary: Dict[str, Any]) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("summary_path =", SUMMARY_PATH.as_posix())


def find_validation_summary(output_dir: Path) -> Optional[Path]:
    candidates = list(output_dir.rglob("*kaggle_sp1*summary*.json"))
    candidates.extend(output_dir.rglob("*validation_summary*.json"))
    for candidate in sorted(candidates, key=lambda path: path.stat().st_mtime, reverse=True):
        if candidate.is_file():
            return candidate
    return None


def poll_kernel_status(
    kaggle: List[str],
    kernel_ref: str,
    *,
    records: List[Dict[str, Any]],
    timeout_sec: int = 3600,
    interval_sec: int = 60,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_sec
    last_record: Optional[Dict[str, Any]] = None
    terminal_patterns = ("COMPLETE", "ERROR", "FAILED", "CANCELLED")
    while time.time() < deadline:
        last_record = run(kaggle + ["kernels", "status", kernel_ref], timeout=120)
        records.append(last_record)
        status_text = (
            f"{last_record.get('stdout', '')}\n{last_record.get('stderr', '')}"
        ).upper()
        if any(pattern in status_text for pattern in terminal_patterns):
            return last_record
        time.sleep(interval_sec)
    timeout_record = {
        "command": kaggle + ["kernels", "status", kernel_ref],
        "cwd": ROOT.as_posix(),
        "returncode": None,
        "duration_sec": timeout_sec,
        "stdout_tail": "",
        "stderr_tail": "Timed out waiting for Kaggle kernel to finish.",
        "stdout": "",
        "stderr": "Timed out waiting for Kaggle kernel to finish.",
        "status": "timeout",
    }
    records.append(timeout_record)
    return timeout_record


def main() -> int:
    args = parse_args()
    source_mode = "archive" if args.use_local_archive else "remote"
    if source_mode == "remote" and git_worktree_has_uncommitted_changes():
        print("warning = current git working tree has uncommitted changes")
        print("warning_detail = remote branch mode will not include uncommitted local edits")
        print("recommendation = commit and push first, or rerun with --use-local-archive")

    records: List[Dict[str, Any]] = []
    kaggle = find_kaggle_executable()
    if kaggle is None:
        summary = {
            "status": "kaggle_cli_not_found",
            "kernel_ref": None,
            "records": records,
            "manual_instructions": manual_instructions("kaggle executable not found"),
        }
        write_summary(summary)
        print("\n".join(summary["manual_instructions"]))
        return 0

    list_record = run(kaggle + ["kernels", "list", "--mine"])
    records.append(list_record)
    search_record = run(kaggle + ["kernels", "list", "--mine", "--search", "zkp-drl"])
    records.append(search_record)
    refs = parse_kernel_refs(search_record.get("stdout", ""))
    kernel_ref = choose_kernel(refs)
    folder = PULL_DIR if kernel_ref else NEW_KERNEL_DIR
    backup_path = None

    if kernel_ref:
        backup_path = backup_folder(folder)
        pull_record = run(kaggle + ["kernels", "pull", kernel_ref, "-p", folder.as_posix(), "-m"], timeout=600)
        records.append(pull_record)
    else:
        folder.mkdir(parents=True, exist_ok=True)

    archive_path: Optional[Path] = None
    if source_mode == "archive":
        archive_path = create_local_workspace_archive(folder)
        print("local_archive_path =", archive_path.as_posix())

    copy_validation_assets(
        folder,
        source_mode=source_mode,
        git_branch=args.git_branch,
        run_sp1_setup=args.run_sp1_setup,
        run_sp1_execute=args.run_sp1_execute,
        run_sp1_prove=args.run_sp1_prove,
        archive_path=archive_path,
    )
    metadata = update_metadata(folder, kernel_ref)
    if metadata.get("id", "").startswith("unknown/"):
        summary = {
            "status": "metadata_missing_kaggle_username",
            "kernel_ref": kernel_ref,
            "source_mode": source_mode,
            "git_branch": args.git_branch,
            "local_archive_path": None if archive_path is None else archive_path.as_posix(),
            "chosen_folder": folder.as_posix(),
            "backup_path": None if backup_path is None else backup_path.as_posix(),
            "metadata": metadata,
            "records": records,
            "manual_instructions": manual_instructions("KAGGLE_USERNAME is unavailable for new kernel metadata"),
        }
        write_summary(summary)
        print("\n".join(summary["manual_instructions"]))
        return 0

    push_record = run(kaggle + ["kernels", "push", "-p", folder.as_posix()], timeout=900)
    records.append(push_record)

    output_record: Optional[Dict[str, Any]] = None
    if push_record["status"] == "passed":
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        poll_kernel_status(kaggle, metadata["id"], records=records)
        output_record = run(
            kaggle + [
                "kernels",
                "output",
                metadata["id"],
                "-p",
                OUTPUT_DIR.as_posix(),
                "-o",
                "--file-pattern",
                ".*kaggle_sp1_.*summary.*|.*validation_summary.*",
            ],
            timeout=900,
        )
        records.append(output_record)
        if output_record["status"] != "passed":
            fallback_output_record = run(
                kaggle + ["kernels", "output", metadata["id"], "-p", OUTPUT_DIR.as_posix(), "-o"],
                timeout=900,
            )
            records.append(fallback_output_record)

    validation_summary_path = find_validation_summary(OUTPUT_DIR)
    validation_summary = None
    if validation_summary_path is not None and validation_summary_path.exists():
        validation_summary = json.loads(validation_summary_path.read_text(encoding="utf-8"))

    summary = {
        "status": "completed" if push_record["status"] == "passed" else "push_failed",
        "kernel_ref": metadata.get("id"),
        "source_mode": source_mode,
        "git_branch": args.git_branch,
        "run_sp1_setup": args.run_sp1_setup,
        "run_sp1_execute": args.run_sp1_execute,
        "run_sp1_prove": args.run_sp1_prove,
        "local_archive_path": None if archive_path is None else archive_path.as_posix(),
        "matching_kernel_refs": refs,
        "chosen_folder": folder.as_posix(),
        "backup_path": None if backup_path is None else backup_path.as_posix(),
        "metadata": metadata,
        "records": records,
        "output_dir": OUTPUT_DIR.as_posix(),
        "validation_summary_path": None if validation_summary_path is None else validation_summary_path.as_posix(),
        "validation_summary_found": validation_summary is not None,
        "validation_summary": validation_summary,
    }
    if push_record["status"] != "passed":
        summary["manual_instructions"] = manual_instructions("kaggle kernels push failed")
    write_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
