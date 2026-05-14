"""Temporary active-package compatibility wrapper for Merkle helpers.

Phase 1B intentionally does not migrate or reimplement Merkle logic.  This
module re-exports the existing behavior from ``zk_offline_dqn.merkle``.
"""

from zk_offline_dqn.merkle import (
    build_merkle_levels,
    build_merkle_path,
    build_next_level,
    encode_leaf_for_hash,
    hash_internal_node,
    hash_leaf,
    recompute_root_from_path,
    verify_merkle_path,
)

__all__ = [
    "build_merkle_levels",
    "build_merkle_path",
    "build_next_level",
    "encode_leaf_for_hash",
    "hash_internal_node",
    "hash_leaf",
    "recompute_root_from_path",
    "verify_merkle_path",
]
