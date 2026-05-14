"""Temporary active-package compatibility wrapper for commitment helpers.

Phase 1B intentionally does not migrate or reimplement commitment logic.  This
module re-exports the existing behavior from ``zk_offline_dqn.commitments``.
"""

from zk_offline_dqn.commitments import (
    canonical_checkpoint_state_commitments,
    canonical_state_dict_sha256,
)

__all__ = [
    "canonical_checkpoint_state_commitments",
    "canonical_state_dict_sha256",
]
