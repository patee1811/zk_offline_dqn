"""Conventional Commits 1.0.0 checker. Source of truth for commitlint.config.cjs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)
SCOPES = (
    "relations",
    "verifiers",
    "artifacts",
    "backends",
    "data",
    "cli",
    "experiments",
    "paper",
    "tests",
    "docs",
    "ci",
    "harness",
    "scripts",
    "rl",
    "proof",
    "tamper",
)
HEADER_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9-]+)\))?(?P<breaking>!)?: (?P<subject>.+)$"
)
PAST_OR_GERUND = re.compile(
    r"^(added|adds|fixed|fixes|updated|updates|changed|changes|removed|removes|"
    r"implemented|implements|hardened|created|creates)\b",
    re.IGNORECASE,
)
NON_ASCII = re.compile(r"[^\x00-\x7F]")


def fail(message: str) -> int:
    sys.stderr.write(message + "\n")
    return 1


def deny_hook(message: str) -> int:
    """PreToolUse blocks need exit 2 plus a decision payload."""
    import json

    sys.stderr.write(message + "\n")
    sys.stdout.write(
        json.dumps(
            {
                "systemMessage": message,
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                },
            }
        )
    )
    return 2


def validate(message: str, on_fail=fail) -> int:
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    if not lines:
        return on_fail("commit message is empty")
    header = lines[0].strip()
    if len(header) > 72:
        return on_fail(f"subject longer than 72 characters ({len(header)}): {header!r}")
    if NON_ASCII.search(header):
        return on_fail("subject must be English ASCII; emoji and non-ASCII are rejected")
    match = HEADER_RE.match(header)
    if not match:
        return on_fail(
            "use Conventional Commits: type(scope): subject\n"
            f"got: {header!r}\n"
            f"types: {', '.join(TYPES)}\n"
            f"scopes: {', '.join(SCOPES)}"
        )
    ctype = match.group("type")
    scope = match.group("scope")
    subject = match.group("subject")
    if ctype not in TYPES:
        return on_fail(f"unknown type {ctype!r}; allowed: {', '.join(TYPES)}")
    if not scope:
        return on_fail(f"scope is required; allowed: {', '.join(SCOPES)}")
    if scope not in SCOPES:
        return on_fail(f"unknown scope {scope!r}; allowed: {', '.join(SCOPES)}")
    if subject.endswith("."):
        return on_fail("subject must not end with a period")
    if subject[0].isupper():
        return on_fail("subject must start with a lowercase letter")
    if PAST_OR_GERUND.search(subject):
        return on_fail("subject must be imperative (add, not added/adds)")
    return 0


def extract_from_git_command(command: str) -> str | None:
    flag = re.search(r'(?:^|\s)-m\s+(?P<q>["\'])(?P<msg>.*?)(?P=q)', command, re.S)
    if flag:
        return flag.group("msg")
    file_flag = re.search(r"(?:^|\s)(?:-F|--file)\s+(\S+)", command)
    if file_flag:
        path = Path(file_flag.group(1).strip("\"'"))
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", nargs="?", help="commit message text")
    parser.add_argument(
        "--commit-msg-file",
        help="path written by git commit-msg hook",
    )
    args = parser.parse_args(argv)

    if args.commit_msg_file:
        text = Path(args.commit_msg_file).read_text(encoding="utf-8")
        return validate(text)
    if args.message:
        return validate(args.message)

    raw = sys.stdin.read()
    if not raw.strip():
        return fail("no commit message on stdin")
    if raw.lstrip().startswith("{"):
        try:
            import json

            payload = json.loads(raw)
        except json.JSONDecodeError:
            return validate(raw)
        command = ""
        tool_input = payload.get("tool_input")
        if isinstance(tool_input, dict):
            command = str(tool_input.get("command") or "")
        if not re.search(r"(?:^|[;&|]\s*)git\s+commit\b", command):
            return 0
        if re.search(r"--no-verify\b|(?:^|\s)-n(?:\s|$)", command):
            return deny_hook(
                "git commit --no-verify bypasses the commit-msg gate; drop the flag"
            )
        extracted = extract_from_git_command(command)
        if extracted is None:
            sys.stderr.write(
                "validate-commit-msg: could not parse git commit -m; "
                "git commit-msg hook will still check the final message\n"
            )
            return 0
        return validate(extracted, on_fail=deny_hook)
    return validate(raw)


if __name__ == "__main__":
    raise SystemExit(main())
