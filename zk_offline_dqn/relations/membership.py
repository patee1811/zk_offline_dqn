"""Pure transition membership relation checks."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from zk_offline_dqn.core.merkle import hash_leaf, verify_merkle_path
from zk_offline_dqn.zk_specs import serialize_transition_leaf


@dataclass(frozen=True)
class MembershipCheckResult:
    accepted: bool
    reason: Optional[str]
    leaf_match: bool
    leaf_hash_match: bool
    merkle_ok: bool
    claimed_leaf: Sequence[int]
    recomputed_leaf: Sequence[int]
    claimed_leaf_hash: str
    recomputed_leaf_hash: str
    expected_root: str
    recomputed_root: str
    path_length: int


def check_transition_membership_artifact(
    artifact: Mapping[str, Any],
) -> MembershipCheckResult:
    """Check the current transition membership artifact relation.

    This preserves the checks from
    ``scripts/artifacts_export/verify_transition_membership_artifact.py``:
    transition serialization, leaf hash equality, and Merkle root verification.
    Field access intentionally uses direct indexing so malformed artifacts fail
    the same way the original script failed.
    """

    transition = artifact["transition"]
    claimed_leaf = artifact["leaf"]
    claimed_leaf_hash = artifact["leaf_hash"]
    merkle_path = artifact["merkle_path"]
    expected_root = artifact["dataset_root"]

    recomputed_leaf = serialize_transition_leaf(transition)
    leaf_match = recomputed_leaf == claimed_leaf

    recomputed_leaf_hash = hash_leaf(recomputed_leaf)
    leaf_hash_match = recomputed_leaf_hash == claimed_leaf_hash

    merkle_ok, recomputed_root = verify_merkle_path(
        recomputed_leaf_hash, merkle_path, expected_root
    )

    accepted = leaf_match and leaf_hash_match and merkle_ok
    reason = None
    if not accepted:
        if not leaf_match:
            reason = "leaf_mismatch"
        elif not leaf_hash_match:
            reason = "leaf_hash_mismatch"
        else:
            reason = "merkle_root_mismatch"

    return MembershipCheckResult(
        accepted=accepted,
        reason=reason,
        leaf_match=leaf_match,
        leaf_hash_match=leaf_hash_match,
        merkle_ok=merkle_ok,
        claimed_leaf=claimed_leaf,
        recomputed_leaf=recomputed_leaf,
        claimed_leaf_hash=claimed_leaf_hash,
        recomputed_leaf_hash=recomputed_leaf_hash,
        expected_root=expected_root,
        recomputed_root=recomputed_root,
        path_length=len(merkle_path),
    )
