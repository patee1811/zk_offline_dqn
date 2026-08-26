"""Block writes to secret, proof, and infrastructure paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import deny, file_path_from, read_payload, repo_root

# Hard block only. Paper/schema/test-vector edits are permissions.ask, not here.
BLOCKED_PREFIXES = (
    ".env",
    "secrets/",
    "infra/prod/",
    "migrations/",
)
BLOCKED_NAMES = {".env", ".env.local", ".env.production"}
BLOCKED_SUFFIXES = (".bin", ".proof", ".receipt")
BLOCKED_CONTAINS = (
    "artifacts/reports/provenance/sp1/",
    "artifacts/kaggle",
)


def is_blocked(rel: str) -> str | None:
    name = Path(rel).name
    if name in BLOCKED_NAMES or name.startswith(".env"):
        return f"blocked env file: {rel}"
    posix = rel.replace("\\", "/")
    for prefix in BLOCKED_PREFIXES:
        if posix == prefix.rstrip("/") or posix.startswith(prefix):
            return f"blocked protected path: {rel}"
    if posix.endswith(BLOCKED_SUFFIXES) and (
        "proof" in posix or posix.endswith(".bin") or posix.endswith(".proof")
    ):
        if posix.endswith(".bin") and "/sp1/" not in posix and "proof" not in posix:
            return None
        return f"blocked proof/binary artifact: {rel}"
    for token in BLOCKED_CONTAINS:
        if token in posix and posix.endswith((".bin", ".proof", ".receipt")):
            return f"blocked generated proof path: {rel}"
    return None


def main() -> int:
    payload = read_payload()
    raw = file_path_from(payload)
    if not raw:
        return 0
    path = Path(raw)
    try:
        rel = path.resolve().relative_to(repo_root().resolve()).as_posix()
    except ValueError:
        rel = raw.replace("\\", "/")
        if os.path.isabs(raw):
            deny(f"refusing write outside the repo: {raw}")
    reason = is_blocked(rel)
    if reason:
        deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
