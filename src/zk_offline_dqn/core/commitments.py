"""Compatibility wrapper for commitment helpers.

Phase 1A intentionally does not migrate or reimplement commitment logic.  This
module re-exports the current behavior from the repository-root package.
"""

from zk_offline_dqn.commitments import (
    canonical_checkpoint_state_commitments,
    canonical_state_dict_sha256,
)

__all__ = [
    "canonical_checkpoint_state_commitments",
    "canonical_state_dict_sha256",
]
