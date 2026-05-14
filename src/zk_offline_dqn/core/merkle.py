"""Compatibility wrapper for Merkle helpers.

Phase 1A intentionally does not migrate or reimplement Merkle logic.  This
module re-exports the current behavior from the repository-root package so
later phases can move callers toward ``core`` without changing semantics.
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
