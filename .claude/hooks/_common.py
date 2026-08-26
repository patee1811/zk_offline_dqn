"""Shared helpers for Claude Code hooks. Stdlib only."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def tool_input(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input")
    return value if isinstance(value, dict) else {}


def file_path_from(payload: Mapping[str, Any]) -> str:
    data = tool_input(payload)
    for key in ("file_path", "path", "filePath"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def deny(reason: str, event: str = "PreToolUse") -> None:
    sys.stdout.write(
        json.dumps(
            {
                "systemMessage": reason,
                "hookSpecificOutput": {
                    "hookEventName": event,
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
            }
        )
    )
    raise SystemExit(2)


def allow() -> None:
    raise SystemExit(0)
