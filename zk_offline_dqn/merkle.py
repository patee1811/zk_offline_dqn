import hashlib
from typing import Any, Dict, List, Tuple


def encode_leaf_for_hash(leaf: List[int]) -> bytes:
    """Canonical leaf encoding used by current artifacts."""
    return ",".join(str(int(x)) for x in leaf).encode("utf-8")


def hash_leaf(leaf: List[int]) -> str:
    return hashlib.sha256(encode_leaf_for_hash(leaf)).hexdigest()


def hash_internal_node(left_hex: str, right_hex: str) -> str:
    left_bytes = bytes.fromhex(left_hex)
    right_bytes = bytes.fromhex(right_hex)
    return hashlib.sha256(left_bytes + right_bytes).hexdigest()


def build_next_level(current_level: List[str]) -> List[str]:
    if not current_level:
        raise ValueError("current_level must not be empty")

    next_level = []
    for i in range(0, len(current_level), 2):
        left = current_level[i]
        right = current_level[i + 1] if i + 1 < len(current_level) else left
        next_level.append(hash_internal_node(left, right))

    return next_level


def build_merkle_levels(leaf_hashes: List[str]) -> List[List[str]]:
    if not leaf_hashes:
        raise ValueError("leaf_hashes must not be empty")

    levels = [leaf_hashes]
    current = leaf_hashes

    while len(current) > 1:
        current = build_next_level(current)
        levels.append(current)

    return levels


def build_merkle_path(
    levels: List[List[str]],
    leaf_index: int,
) -> List[Dict[str, Any]]:
    path = []
    idx = leaf_index

    for level_idx, level_hashes in enumerate(levels[:-1]):
        if idx < 0 or idx >= len(level_hashes):
            raise IndexError(
                f"leaf_index {idx} out of range for level {level_idx} "
                f"of size {len(level_hashes)}"
            )

        if idx % 2 == 0:
            sibling_idx = idx + 1 if idx + 1 < len(level_hashes) else idx
            current_is_left = True
        else:
            sibling_idx = idx - 1
            current_is_left = False

        path.append(
            {
                "level": level_idx,
                "current_index": idx,
                "sibling_index": sibling_idx,
                "sibling_hash": level_hashes[sibling_idx],
                "current_is_left": current_is_left,
            }
        )
        idx //= 2

    return path


def recompute_root_from_path(leaf_hash: str, merkle_path: List[Dict[str, Any]]) -> str:
    current = leaf_hash

    for step in merkle_path:
        sibling_hash = step["sibling_hash"]
        current_is_left = bool(step["current_is_left"])

        if current_is_left:
            current = hash_internal_node(current, sibling_hash)
        else:
            current = hash_internal_node(sibling_hash, current)

    return current


def verify_merkle_path(
    leaf_hash: str,
    merkle_path: List[Dict[str, Any]],
    expected_root: str,
) -> Tuple[bool, str]:
    recomputed_root = recompute_root_from_path(leaf_hash, merkle_path)
    return recomputed_root == expected_root, recomputed_root
