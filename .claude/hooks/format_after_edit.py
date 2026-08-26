"""Format a just-edited file. Ruff is harness-only and is not in requirements."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import file_path_from, read_payload, repo_root


def run(argv: list[str]) -> int:
    result = subprocess.run(
        argv,
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 and result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def main() -> int:
    payload = read_payload()
    raw = file_path_from(payload)
    if not raw:
        return 0
    path = Path(raw)
    if not path.is_file():
        return 0

    suffix = path.suffix.lower()
    if suffix == ".py":
        ruff = shutil.which("ruff")
        python = sys.executable
        if ruff:
            cmd_prefix = [ruff]
        else:
            probe = subprocess.run(
                [python, "-m", "ruff", "--version"],
                capture_output=True,
                check=False,
            )
            if probe.returncode != 0:
                sys.stderr.write(
                    "format-after-edit: ruff not installed; skip. "
                    "Install with: python -m pip install ruff\n"
                )
                return 0
            cmd_prefix = [python, "-m", "ruff"]
        run(cmd_prefix + ["format", str(path)])
        run(cmd_prefix + ["check", "--fix", str(path)])
        return 0

    if suffix == ".rs":
        rustfmt = shutil.which("rustfmt")
        if not rustfmt:
            return 0
        run([rustfmt, str(path)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
