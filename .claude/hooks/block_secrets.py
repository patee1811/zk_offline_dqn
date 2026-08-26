"""Block secret-shaped assignments. Do not flag SHA256 hex (Merkle leaves)."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import deny, file_path_from, read_payload, tool_input

# High-entropy hex is normal here (Merkle roots, leaf hashes). Do not scan it.
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}\b"),
    re.compile(
        r"(?i)\b(api[_-]?key|secret|password|token|private[_-]?key)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    ),
)

SKIP_SUFFIXES = (
    ".md",
    ".lock.json",
    "INBOX.md",
    "CHANGELOG.md",
    "PRINCIPLES.md",
)


def texts_from_payload(payload: dict) -> Iterable[str]:
    data = tool_input(payload)
    for key in ("content", "new_string", "old_string", "new_source"):
        value = data.get(key)
        if isinstance(value, str) and value:
            yield value


def should_skip(path: str) -> bool:
    posix = path.replace("\\", "/")
    return posix.endswith(SKIP_SUFFIXES) or "/.claude/hooks/" in posix


def main() -> int:
    payload = read_payload()
    path = file_path_from(payload)
    if should_skip(path):
        return 0
    for text in texts_from_payload(payload):
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                deny(
                    f"blocked secret-like content in {path or 'buffer'} "
                    f"(pattern {pattern.pattern!r})"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
