"""Print branch, dirty state, harness version, and pending inbox count."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import repo_root


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout or "").strip()


def count_pending_inbox(path: Path) -> int:
    """Count pending entries, ignoring the fenced format example."""
    if not path.is_file():
        return 0
    pending = 0
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("**Trạng thái:** chờ xử lý"):
            pending += 1
    return pending


def main() -> int:
    root = repo_root()
    lock_path = root / ".claude" / "harness.lock.json"
    inbox_path = root / ".claude" / "harness" / "INBOX.md"
    version = "unknown"
    if lock_path.is_file():
        try:
            version = json.loads(lock_path.read_text(encoding="utf-8")).get(
                "harnessVersion", "unknown"
            )
        except json.JSONDecodeError:
            version = "invalid-lock"

    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    dirty = git("status", "--porcelain")
    pending = count_pending_inbox(inbox_path)
    print(f"harness {version} | branch {branch} | inbox pending {pending}")
    if dirty:
        print("working tree dirty:")
        print(dirty)
    else:
        print("working tree clean")
    print("default branch is master; do not push it without an explicit ask")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
