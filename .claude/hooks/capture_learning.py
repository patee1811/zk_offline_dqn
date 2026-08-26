"""Append candidate learnings from the session transcript into the harness inbox.

This used to read SESSION_NOTES.md, a file nothing ever created, so automatic
capture never fired once. It now reads the session transcript the runtime
already writes and scans the user's own messages for correction phrasing.

A correction is the strongest signal the harness has: the user telling you the
repo does something other than what you assumed. Those are exactly the entries
rules/60 wants queued, and exactly the ones that were being typed by hand.

Everything appended is a candidate, not a rule. /harness-sync decides.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import read_payload, repo_root

MARKER = "LEARNING:"
MAX_LESSON_CHARS = 300
MAX_CANDIDATES = 5
# Skill bodies and pasted documents arrive as user turns too. The ones seen so
# far ran 11k and 249k characters; a person correcting you writes a sentence.
MAX_MESSAGE_CHARS = 2000

# Correction phrasing, Vietnamese and English. These fire when the user is
# telling you the repo works differently than you just claimed.
CORRECTION_PATTERNS = (
    r"\bkhông phải\b",
    r"\bđâu\b.*\bý (tôi|mình)\b",
    r"\bý (tôi|mình) là\b",
    r"\b(tôi|mình) có bảo\b",
    r"\bsai rồi\b",
    r"\bnhầm\b",
    r"\bở đây (luôn|mình luôn)\b",
    r"\blần sau\b",
    r"\bđừng\b",
    r"\bthat's not\b",
    r"\bnot what i\b",
    r"\bi meant\b",
    r"\bactually,?\s",
    r"\bwrong\b",
)
CORRECTION_RE = re.compile("|".join(CORRECTION_PATTERNS), re.IGNORECASE)

# Slash-command bodies and pasted skill text are not corrections.
SKIP_PREFIXES = ("<", "Base directory for this skill:", "/")


def transcript_path(payload: Dict[str, Any]) -> Optional[Path]:
    """Prefer the path the runtime hands us; fall back to the newest transcript."""
    raw = payload.get("transcript_path")
    if isinstance(raw, str) and raw:
        path = Path(raw)
        if path.is_file():
            return path

    session_id = payload.get("session_id")
    root = repo_root()
    slug = "c--" + str(root).replace(":", "").replace("\\", "-").replace("/", "-").lstrip("-")
    project_dir = Path.home() / ".claude" / "projects" / slug
    if not project_dir.is_dir():
        return None

    if isinstance(session_id, str) and session_id:
        candidate = project_dir / f"{session_id}.jsonl"
        if candidate.is_file():
            return candidate

    transcripts = sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    return transcripts[-1] if transcripts else None


def message_text(entry: Dict[str, Any]) -> str:
    message = entry.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return " ".join(parts).strip()
    return ""


def user_messages(path: Path) -> List[str]:
    """Real user prose only: no tool results, no system reminders, no commands."""
    out: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "user" or entry.get("isSidechain"):
                continue
            text = message_text(entry)
            if not text or text.startswith(SKIP_PREFIXES):
                continue
            if "system-reminder" in text or "<command-name>" in text:
                continue
            if len(text) > MAX_MESSAGE_CHARS:
                continue
            out.append(text)
    return out


def explicit_lessons(root: Path) -> List[str]:
    """Keep honouring SESSION_NOTES.md when someone does write one."""
    notes = root / ".claude" / "harness" / "SESSION_NOTES.md"
    if not notes.is_file():
        return []
    return [
        line[len(MARKER) :].strip()
        for line in notes.read_text(encoding="utf-8").splitlines()
        if line.startswith(MARKER) and line[len(MARKER) :].strip()
    ]


def corrections(messages: List[str]) -> List[str]:
    found = []
    for text in messages:
        if not CORRECTION_RE.search(text):
            continue
        condensed = " ".join(text.split())
        if len(condensed) > MAX_LESSON_CHARS:
            condensed = condensed[:MAX_LESSON_CHARS].rstrip() + "…"
        found.append(condensed)
    # Latest corrections are the ones still fresh enough to act on.
    return found[-MAX_CANDIDATES:]


def block(lesson: str, source: str, kind: str) -> str:
    return "\n".join(
        [
            f"## {date.today().isoformat()} — {kind} — scope harness",
            f"**Kích hoạt:** {source}",
            f"**Bài học:** {lesson}",
            "**Đích đề xuất:** /harness-sync quyết định",
            "**Độ tin cậy:** thấp (tự động, chưa duyệt)",
            "**Trạng thái:** chờ xử lý",
            "",
        ]
    )


def main() -> int:
    payload = read_payload()
    root = repo_root()
    inbox = root / ".claude" / "harness" / "INBOX.md"
    existing = inbox.read_text(encoding="utf-8") if inbox.is_file() else ""

    candidates: List[tuple[str, str, str]] = [
        (lesson, f"SESSION_NOTES.md `{MARKER}`", "phát hiện mới")
        for lesson in explicit_lessons(root)
    ]

    path = transcript_path(payload)
    if path is not None:
        for lesson in corrections(user_messages(path)):
            candidates.append((lesson, "người dùng sửa lại trong phiên", "người sửa"))

    blocks = []
    seen = set()
    for lesson, source, kind in candidates:
        # Substring match against the whole inbox also catches a lesson that a
        # previous run already queued verbatim.
        if lesson in existing or lesson in seen:
            continue
        seen.add(lesson)
        blocks.append(block(lesson, source, kind))

    if not blocks:
        return 0

    inbox.parent.mkdir(parents=True, exist_ok=True)
    with inbox.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write("\n" + "\n".join(blocks))
    print(f"capture-learning: appended {len(blocks)} inbox candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
