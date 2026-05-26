from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .metrics import sha256_file


DEFAULT_MERKLE_DATASET_PREFIX = "minari-pointmaze-umaze-v2"


def build_membership_path(levels: List[List[str]], leaf_index: int) -> List[Dict[str, Any]]:
    if leaf_index < 0 or not levels or leaf_index >= len(levels[0]):
        raise ValueError("leaf_index is outside the Merkle leaf range")
    path = []
    current = int(leaf_index)
    for level, hashes in enumerate(levels[:-1]):
        current_is_left = current % 2 == 0
        sibling = current + 1 if current_is_left else current - 1
        if sibling >= len(hashes):
            sibling = current
        path.append(
            {
                "level": level,
                "current_index": current,
                "sibling_index": sibling,
                "sibling_hash": hashes[sibling],
                "current_is_left": current_is_left,
            }
        )
        current //= 2
    return path


def recompute_root(leaf_hash: str, merkle_path: Iterable[Dict[str, Any]]) -> str:
    import hashlib

    current = leaf_hash
    for step in merkle_path:
        left, right = (
            (current, step["sibling_hash"])
            if step["current_is_left"]
            else (step["sibling_hash"], current)
        )
        current = hashlib.sha256(bytes.fromhex(left) + bytes.fromhex(right)).hexdigest()
    return current


def write_merkle_membership_case(
    *,
    dataset_dir: str | Path,
    case_path: str | Path,
    requested_size: int,
    leaf_index: int | None = None,
) -> Dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    case_path = Path(case_path)
    merkle_tree = _read_json(dataset_dir / "merkle_tree.json")
    levels = merkle_tree["levels"]
    num_leaves = int(merkle_tree["num_leaves"])
    selected = int(leaf_index if leaf_index is not None else num_leaves // 2)
    leaf_hash = merkle_tree["leaf_hashes"][selected]
    path = build_membership_path(levels, selected)
    root = recompute_root(leaf_hash, path)
    if root != merkle_tree["dataset_root"]:
        raise ValueError("generated Merkle path does not authenticate to dataset_root")

    case = {
        "schema_version": "sp1_merkle_membership_case_v1",
        "public_inputs": {
            "dataset_id": merkle_tree["dataset_id"],
            "dataset_type": merkle_tree["dataset_type"],
            "dataset_root": merkle_tree["dataset_root"],
            "manifest_hash": merkle_tree["manifest_hash"],
            "audit_report_hash": merkle_tree["audit_report_hash"],
            "collection_log_final_hash": merkle_tree.get("collection_log_final_hash"),
            "raw_trajectory_hash": merkle_tree["raw_trajectory_hash"],
            "leaf_hash": leaf_hash,
            "leaf_index": selected,
        },
        "private_witness": {"merkle_path": path},
        "metadata": {
            "case_id": f"merkle_membership_dataset_{int(requested_size)}",
            "requested_dataset_size": int(requested_size),
            "dataset_size": num_leaves,
            "merkle_depth": len(path),
            "dataset_dir": dataset_dir.as_posix(),
            "merkle_tree_sha256": sha256_file(dataset_dir / "merkle_tree.json"),
        },
    }
    case_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json.dumps(case, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "case_path": case_path,
        "dataset_size": num_leaves,
        "merkle_depth": len(path),
        "dataset_root": merkle_tree["dataset_root"],
        "manifest_hash": merkle_tree["manifest_hash"],
        "audit_report_hash": merkle_tree["audit_report_hash"],
        "leaf_index": selected,
        "leaf_hash": leaf_hash,
    }


def find_dataset_for_size(
    *,
    root: str | Path,
    size: int,
    dataset_prefix: str = DEFAULT_MERKLE_DATASET_PREFIX,
) -> Path | None:
    base = Path(root) / "artifacts/datasets"
    exact = base / f"{dataset_prefix}-{int(size)}"
    if _valid_dataset(exact):
        return exact
    if int(size) == 1000:
        for name in ("cartpole-random-v1", "mountaincar-random-v1"):
            candidate = base / name
            if _valid_dataset(candidate):
                return candidate
    return None


def _valid_dataset(path: Path) -> bool:
    return all((path / name).exists() for name in ("dataset_manifest.json", "replay_audit_report.json", "merkle_tree.json"))


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data
