from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
SP1_DIR = ROOT / "zk_backend/td_mvp/sp1"


def command_version(command: List[str]) -> Dict[str, Any]:
    executable = shutil.which(command[0])
    if executable is None:
        return {
            "command": command,
            "available": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"{command[0]} not found on PATH",
        }
    try:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=15,
        )
    except Exception as exc:  # pragma: no cover - platform dependent
        return {
            "command": command,
            "available": True,
            "returncode": None,
            "stdout": "",
            "stderr": repr(exc),
        }
    available = True
    if result.returncode != 0 and "no such command" in result.stderr.lower():
        available = False
    return {
        "command": command,
        "available": available,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def internet_check() -> Dict[str, Any]:
    try:
        with socket.create_connection(("example.com", 80), timeout=3):
            return {"available": True, "target": "example.com:80", "error": None}
    except OSError as exc:
        return {"available": False, "target": "example.com:80", "error": str(exc)}


def is_kaggle_environment() -> bool:
    if Path("/kaggle").exists():
        return True
    kaggle_vars = ["KAGGLE_KERNEL_RUN_TYPE", "KAGGLE_URL_BASE", "KAGGLE_KERNEL_INTEGRATIONS"]
    return any(os.environ.get(name) for name in kaggle_vars)


def inspect_package_name(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("name = "):
            return stripped.split("=", 1)[1].strip().strip('"')
    return None


def inspect_sp1_workspace() -> Dict[str, Any]:
    return {
        "sp1_dir": SP1_DIR.as_posix(),
        "sp1_dir_exists": SP1_DIR.exists(),
        "workspace_cargo_toml": (SP1_DIR / "Cargo.toml").exists(),
        "host_package": inspect_package_name(SP1_DIR / "host/Cargo.toml"),
        "guest_package": inspect_package_name(SP1_DIR / "guest/Cargo.toml"),
        "shared_package": inspect_package_name(SP1_DIR / "shared/Cargo.toml"),
        "expected_test_vector_exists": (ROOT / "zk_backend/test_vectors/td_mvp_case_0.json").exists(),
    }


def main() -> int:
    workspace = inspect_sp1_workspace()
    host_package = workspace.get("host_package") or "td-mvp-host"
    recommended_commands = [
        "python -m compileall zk_offline_dqn scripts tests",
        "python -m unittest discover tests/regression",
        "python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json",
        "cd zk_backend/td_mvp/sp1 && cargo test",
        f"cd zk_backend/td_mvp/sp1 && cargo run --release -p {host_package} -- --execute",
        f"cd zk_backend/td_mvp/sp1 && RUN_SP1_PROVE=1 cargo run --release -p {host_package} -- --prove",
    ]
    diagnostics = {
        "python": sys.version,
        "platform": platform.platform(),
        "system": platform.system(),
        "machine": platform.machine(),
        "cwd": Path.cwd().as_posix(),
        "is_kaggle": is_kaggle_environment(),
        "internet": internet_check(),
        "tools": {
            "rustc": command_version(["rustc", "--version"]),
            "cargo": command_version(["cargo", "--version"]),
            "cargo_prove": command_version(["cargo", "prove", "--version"]),
            "sp1up": command_version(["sp1up", "--help"]),
        },
        "workspace": workspace,
        "recommended_commands": recommended_commands,
    }

    print("=== SP1 ENVIRONMENT DIAGNOSTIC ===")
    for key in ["python", "platform", "system", "machine", "cwd", "is_kaggle"]:
        print(f"{key} = {diagnostics[key]}")
    print("internet_available =", diagnostics["internet"]["available"])
    print("sp1_dir_exists =", workspace["sp1_dir_exists"])
    print("host_package =", workspace["host_package"])
    print("guest_package =", workspace["guest_package"])
    print("shared_package =", workspace["shared_package"])
    for name, result in diagnostics["tools"].items():
        print(f"{name}_available = {result['available']}")
        if result["stdout"]:
            print(f"{name}_stdout = {result['stdout'].splitlines()[0]}")
        if result["stderr"] and not result["available"]:
            print(f"{name}_stderr = {result['stderr']}")
    print("recommended_commands =")
    for command in recommended_commands:
        print(f"  {command}")
    print("diagnostic_json =")
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
