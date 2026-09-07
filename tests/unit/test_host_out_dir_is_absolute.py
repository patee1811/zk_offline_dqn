"""Every SP1 host command must name an absolute --out-dir.

cargo runs each host from its own relation workspace, so a relative --out-dir
resolves under zk_backend/<relation>/sp1/artifacts/... instead of the
provenance tree. Nothing fails when that happens: the host exits 0, the phase
script prints proof_verified from its reference check, and metrics.json in
provenance keeps whatever it held from the previous run. A Table 2 regenerated
from that tree then reports an old guest's numbers as freshly proved, which is
how four rows survived a full re-prove carrying the ELF they were meant to
replace.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.backends.sp1 import (
    forward_td_mlp,
    merkle_membership,
    one_step_sgd_tiny,
    short_trace,
    training_aggregation,
    training_fragment,
    training_update,
)

MODULES = (
    forward_td_mlp,
    merkle_membership,
    one_step_sgd_tiny,
    short_trace,
    training_aggregation,
    training_fragment,
    training_update,
)


def out_dir_in(command):
    return command[command.index("--out-dir") + 1]


class HostOutDirTests(unittest.TestCase):
    def test_relative_out_dir_is_resolved_against_the_repo_root(self) -> None:
        relative = "artifacts/reports/provenance/sp1/probe"
        for module in MODULES:
            with self.subTest(backend=module.__name__.rsplit(".", 1)[-1]):
                command = module.cargo_command(mode="prove", out_dir=relative)
                resolved = Path(out_dir_in(command))
                self.assertTrue(resolved.is_absolute(), resolved)
                self.assertEqual(resolved, ROOT / relative)

    def test_absolute_out_dir_is_passed_through_unchanged(self) -> None:
        absolute = (ROOT / "artifacts/reports/provenance/sp1/probe").resolve()
        for module in MODULES:
            with self.subTest(backend=module.__name__.rsplit(".", 1)[-1]):
                command = module.cargo_command(mode="prove", out_dir=absolute)
                self.assertEqual(Path(out_dir_in(command)), absolute)


if __name__ == "__main__":
    unittest.main()
