"""Every relation guest must abort on integer overflow rather than wrap.

fixed_point_mul is (a * b) / 1000 over i64, and offline DQN drives Q values up
exponentially: 990 * q crosses i64::MAX near 9.3e15, which a 4992-step CartPole
run reaches around step 3744. Under Cargo's default release profile the product
wraps to a negative number and the guest proves it happily -- a prover using the
same i64 semantics gets the guest's assert_eq! to pass, so the proof attests to
arithmetic that means nothing.

The placement is the part that bites. SP1's own security guidance says to set
the profile in the guest package's Cargo.toml, which is correct for the
standalone template but silently ignored here, where the guest is a workspace
member. Cargo prints "profiles for the non root package will be ignored" and
carries on, so the setting looks applied and is not.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BACKEND = ROOT / "zk_backend"
PROFILE_RELEASE = re.compile(r"^\[profile\.release\]\s*$", re.MULTILINE)
ANY_PROFILE = re.compile(r"^\[profile[.\]]", re.MULTILINE)
OVERFLOW_ON = re.compile(r"^\s*overflow-checks\s*=\s*true\s*$", re.MULTILINE)


def workspace_roots():
    return sorted(BACKEND.glob("*/sp1/Cargo.toml"))


def member_manifests():
    return sorted(
        path
        for path in BACKEND.glob("*/sp1/*/Cargo.toml")
        if path.parent.name in {"guest", "host", "shared"}
    )


class GuestOverflowChecksTests(unittest.TestCase):
    def test_there_is_a_workspace_per_relation(self) -> None:
        # A relation added without a workspace would slip past every check below.
        self.assertEqual(len(workspace_roots()), 8, [p.as_posix() for p in workspace_roots()])

    def test_every_workspace_root_turns_overflow_checks_on(self) -> None:
        for path in workspace_roots():
            with self.subTest(workspace=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertRegex(text, PROFILE_RELEASE, "missing [profile.release]")
                self.assertRegex(text, OVERFLOW_ON, "overflow-checks is not true")

    def test_no_member_declares_a_profile_cargo_would_ignore(self) -> None:
        # This is the trap: a profile here parses, warns, and does nothing.
        for path in member_manifests():
            with self.subTest(member=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(
                    text,
                    ANY_PROFILE,
                    "profiles in a workspace member are ignored; move it to the "
                    "sp1/Cargo.toml beside it",
                )

    def test_every_member_belongs_to_the_workspace_that_carries_the_profile(self) -> None:
        for path in workspace_roots():
            with self.subTest(workspace=path.relative_to(ROOT).as_posix()):
                text = path.read_text(encoding="utf-8")
                members = set(re.findall(r'"([a-z_]+)"', text.split("members")[1][:120]))
                present = {p.parent.name for p in path.parent.glob("*/Cargo.toml")}
                self.assertTrue(
                    present <= members,
                    f"{present - members} sit beside the workspace but are not members, "
                    "so the profile does not reach them",
                )


if __name__ == "__main__":
    unittest.main()
