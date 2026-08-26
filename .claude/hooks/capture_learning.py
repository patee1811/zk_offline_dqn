"""Append candidate learnings from SESSION_NOTES.md into the harness inbox."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import repo_root

MARKER = "LEARNING:"


def main() -> int:
    root = repo_root()
    notes = root / ".claude" / "harness" / "SESSION_NOTES.md"
    inbox = root / ".claude" / "harness" / "INBOX.md"
    if not notes.is_file():
        return 0
    lines = [
        line[len(MARKER) :].strip()
        for line in notes.read_text(encoding="utf-8").splitlines()
        if line.startswith(MARKER) and line[len(MARKER) :].strip()
    ]
    if not lines:
        return 0
    existing = inbox.read_text(encoding="utf-8") if inbox.is_file() else ""
    blocks = []
    for lesson in lines:
        if lesson in existing:
            continue
        blocks.append(
            "\n".join(
                [
                    f"## {date.today().isoformat()} — phát hiện mới — scope harness",
                    f"**Kích hoạt:** SESSION_NOTES.md `{MARKER}`",
                    f"**Bài học:** {lesson}",
                    "**Đích đề xuất:** /harness-sync quyết định",
                    "**Độ tin cậy:** thấp (chưa duyệt)",
                    "**Trạng thái:** chờ xử lý",
                    "",
                ]
            )
        )
    if not blocks:
        return 0
    inbox.parent.mkdir(parents=True, exist_ok=True)
    with inbox.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write("\n".join(blocks))
    print(f"capture-learning: appended {len(blocks)} inbox candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
