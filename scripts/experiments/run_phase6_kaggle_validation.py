from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
PULL_DIR = ROOT / "kaggle_phase6_zkp_drl"
BACKUP_ROOT = ROOT / "kaggle_phase6_zkp_drl_backup"
NEW_KERNEL_DIR = ROOT / "kaggle_phase6_sp1_validation"
OUTPUT_DIR = ROOT / "kaggle_phase6_outputs"
SUMMARY_PATH = ROOT / "artifacts/reports/phase6_kaggle_api_summary.json"


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


def write_validation_notebook(folder: Path) -> Path:
    notebook_path = folder / "phase6_sp1_validation.ipynb"
    script = (ROOT / "scripts/experiments/kaggle_sp1_validation.py").read_text(
        encoding="utf-8"
    )
    cell_source = [
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


def copy_validation_assets(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "scripts/experiments/kaggle_sp1_validation.py", folder / "kaggle_sp1_validation.py")
    shutil.copy2(ROOT / "scripts/experiments/setup_sp1_on_kaggle.sh", folder / "setup_sp1_on_kaggle.sh")
    write_validation_notebook(folder)


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


def write_summary(summary: Dict[str, Any]) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("summary_path =", SUMMARY_PATH.as_posix())


def main() -> int:
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

    copy_validation_assets(folder)
    metadata = update_metadata(folder, kernel_ref)
    if metadata.get("id", "").startswith("unknown/"):
        summary = {
            "status": "metadata_missing_kaggle_username",
            "kernel_ref": kernel_ref,
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
        time.sleep(10)
        output_record = run(
            kaggle + ["kernels", "output", metadata["id"], "-p", OUTPUT_DIR.as_posix()],
            timeout=900,
        )
        records.append(output_record)

    validation_summary_path = OUTPUT_DIR / "artifacts/reports/kaggle_sp1_validation_summary.json"
    validation_summary = None
    if validation_summary_path.exists():
        validation_summary = json.loads(validation_summary_path.read_text(encoding="utf-8"))

    summary = {
        "status": "completed" if push_record["status"] == "passed" else "push_failed",
        "kernel_ref": metadata.get("id"),
        "matching_kernel_refs": refs,
        "chosen_folder": folder.as_posix(),
        "backup_path": None if backup_path is None else backup_path.as_posix(),
        "metadata": metadata,
        "records": records,
        "output_dir": OUTPUT_DIR.as_posix(),
        "validation_summary_found": validation_summary is not None,
        "validation_summary": validation_summary,
    }
    if push_record["status"] != "passed":
        summary["manual_instructions"] = manual_instructions("kaggle kernels push failed")
    write_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
