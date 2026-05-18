from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from zk_offline_dqn.merkle import build_merkle_levels


PathLike = Union[str, Path]

RAW_EPISODES_NAME = "raw_episodes.jsonl"
COLLECTION_LOG_NAME = "collection_log.jsonl"
MANIFEST_NAME = "dataset_manifest.json"
AUDIT_REPORT_NAME = "replay_audit_report.json"
MERKLE_TREE_NAME = "merkle_tree.json"
COLLECTION_LOG_GENESIS = "zk_offline_dqn_collection_log_v1"


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: PathLike) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: PathLike) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{lineno}: JSONL row must be an object")
            rows.append(row)
    return rows


def write_jsonl(path: PathLike, rows: List[Dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(canonical_json_bytes(row).decode("utf-8"))
            f.write("\n")


def transition_hash(transition: Dict[str, Any]) -> str:
    return sha256_hex_bytes(canonical_json_bytes(transition))


def hash_jsonl_transitions(path: PathLike) -> str:
    rows = read_jsonl(path)
    hashes = [transition_hash(row) for row in rows]
    return sha256_hex_bytes(canonical_json_bytes(hashes))


def collection_log_next_hash(
    prev_hash: str,
    transition_hash: str,
    episode_id: int,
    t: int,
) -> str:
    data = f"{prev_hash}{transition_hash}{int(episode_id)}{int(t)}".encode("utf-8")
    return sha256_hex_bytes(data)


def write_collection_log(raw_jsonl_path: PathLike, log_jsonl_path: PathLike) -> str:
    rows = read_jsonl(raw_jsonl_path)
    prev_hash = COLLECTION_LOG_GENESIS
    log_rows: List[Dict[str, Any]] = []
    for row in rows:
        th = transition_hash(row)
        episode_id = int(row["episode_id"])
        t = int(row["t"])
        current_hash = collection_log_next_hash(prev_hash, th, episode_id, t)
        log_rows.append(
            {
                "episode_id": episode_id,
                "t": t,
                "transition_hash": th,
                "prev_log_hash": prev_hash,
                "current_log_hash": current_hash,
            }
        )
        prev_hash = current_hash
    write_jsonl(log_jsonl_path, log_rows)
    return prev_hash


def validate_collection_log(
    raw_jsonl_path: PathLike,
    log_jsonl_path: PathLike,
) -> Tuple[bool, str]:
    rows = read_jsonl(raw_jsonl_path)
    log_rows = read_jsonl(log_jsonl_path)
    if len(rows) != len(log_rows):
        return False, f"row count mismatch: raw={len(rows)} log={len(log_rows)}"

    prev_hash = COLLECTION_LOG_GENESIS
    for idx, (row, log_row) in enumerate(zip(rows, log_rows)):
        episode_id = int(row["episode_id"])
        t = int(row["t"])
        th = transition_hash(row)
        expected = collection_log_next_hash(prev_hash, th, episode_id, t)
        if log_row.get("episode_id") != episode_id or log_row.get("t") != t:
            return False, f"log identity mismatch at row {idx}"
        if log_row.get("transition_hash") != th:
            return False, f"transition hash mismatch at row {idx}"
        if log_row.get("prev_log_hash") != prev_hash:
            return False, f"prev hash mismatch at row {idx}"
        if log_row.get("current_log_hash") != expected:
            return False, f"current hash mismatch at row {idx}"
        prev_hash = expected
    return True, prev_hash


def _write_json(path: PathLike, obj: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def _read_json(path: PathLike) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_manifest(dataset_dir: PathLike) -> Dict[str, Any]:
    return _read_json(Path(dataset_dir) / MANIFEST_NAME)


def write_manifest(dataset_dir: PathLike, manifest: Dict[str, Any]) -> None:
    _write_json(Path(dataset_dir) / MANIFEST_NAME, manifest)


def write_audit_report(dataset_dir: PathLike, report: Dict[str, Any]) -> str:
    report_path = Path(dataset_dir) / AUDIT_REPORT_NAME
    _write_json(report_path, report)
    return sha256_file(report_path)


def build_dataset_merkle_commitment(dataset_dir: PathLike) -> Dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    manifest = load_manifest(dataset_dir)
    raw_path = dataset_dir / RAW_EPISODES_NAME
    report_path = dataset_dir / AUDIT_REPORT_NAME
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if not report_path.exists():
        raise FileNotFoundError(report_path)

    rows = read_jsonl(raw_path)
    leaf_hashes = [transition_hash(row) for row in rows]
    levels = build_merkle_levels(leaf_hashes)
    root = levels[-1][0]
    commitment: Dict[str, Any] = {
        "schema_version": "dataset_merkle_commitment_v1",
        "dataset_id": manifest["dataset_id"],
        "dataset_type": manifest["dataset_type"],
        "dataset_root": root,
        "manifest_hash": sha256_file(dataset_dir / MANIFEST_NAME),
        "audit_report_hash": sha256_file(report_path),
        "raw_trajectory_hash": hash_jsonl_transitions(raw_path),
        "collection_log_final_hash": manifest.get("collection_log_final_hash"),
        "num_leaves": len(leaf_hashes),
        "leaf_hashes": leaf_hashes,
        "levels": levels,
        "leaf_hash_rule": "sha256(canonical_json(transition))",
    }
    _write_json(dataset_dir / MERKLE_TREE_NAME, commitment)
    manifest["merkle_root"] = root
    write_manifest(dataset_dir, manifest)
    return commitment
