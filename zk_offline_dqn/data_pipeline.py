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


def normalized_manifest_for_commitment(manifest: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(manifest)
    for field in ("merkle_root", "manifest_hash", "commitment_hash"):
        normalized.pop(field, None)
    return normalized


def manifest_commitment_hash(manifest: Dict[str, Any]) -> str:
    return sha256_hex_bytes(canonical_json_bytes(normalized_manifest_for_commitment(manifest)))


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
        "manifest_hash": manifest_commitment_hash(manifest),
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


def verify_dataset_commitment(dataset_dir: PathLike) -> Tuple[bool, List[str]]:
    dataset_dir = Path(dataset_dir)
    errors: List[str] = []

    raw_path = dataset_dir / RAW_EPISODES_NAME
    manifest_path = dataset_dir / MANIFEST_NAME
    audit_path = dataset_dir / AUDIT_REPORT_NAME
    merkle_path = dataset_dir / MERKLE_TREE_NAME
    required = [
        (RAW_EPISODES_NAME, raw_path),
        (MANIFEST_NAME, manifest_path),
        (AUDIT_REPORT_NAME, audit_path),
        (MERKLE_TREE_NAME, merkle_path),
    ]
    for name, path in required:
        if not path.exists():
            errors.append(f"missing required file: {name}")

    if errors:
        return False, errors

    try:
        manifest = _read_json(manifest_path)
    except Exception as exc:
        return False, [f"failed to read {MANIFEST_NAME}: {exc}"]
    try:
        merkle_tree = _read_json(merkle_path)
    except Exception as exc:
        return False, [f"failed to read {MERKLE_TREE_NAME}: {exc}"]

    try:
        raw_hash = hash_jsonl_transitions(raw_path)
    except Exception as exc:
        return False, [f"failed to hash {RAW_EPISODES_NAME}: {exc}"]

    if raw_hash != manifest.get("raw_trajectory_hash"):
        errors.append("raw_trajectory_hash mismatch between raw_episodes.jsonl and dataset_manifest.json")
    if raw_hash != merkle_tree.get("raw_trajectory_hash"):
        errors.append("raw_trajectory_hash mismatch between raw_episodes.jsonl and merkle_tree.json")

    audit_hash = sha256_file(audit_path)
    if audit_hash != manifest.get("audit_report_hash"):
        errors.append("audit_report_hash mismatch between replay_audit_report.json and dataset_manifest.json")
    if audit_hash != merkle_tree.get("audit_report_hash"):
        errors.append("audit_report_hash mismatch between replay_audit_report.json and merkle_tree.json")

    manifest_hash = manifest_commitment_hash(manifest)
    if manifest_hash != merkle_tree.get("manifest_hash"):
        errors.append("manifest_hash mismatch for normalized dataset_manifest.json")

    try:
        rows = read_jsonl(raw_path)
        leaf_hashes = [transition_hash(row) for row in rows]
        levels = build_merkle_levels(leaf_hashes)
        dataset_root = levels[-1][0]
    except Exception as exc:
        errors.append(f"failed to rebuild Merkle tree from raw transitions: {exc}")
        leaf_hashes = []
        levels = []
        dataset_root = None

    if leaf_hashes and leaf_hashes != merkle_tree.get("leaf_hashes"):
        errors.append("leaf_hashes mismatch between raw transitions and merkle_tree.json")
    if levels and levels != merkle_tree.get("levels"):
        errors.append("Merkle levels mismatch between rebuilt tree and merkle_tree.json")
    if dataset_root is not None and dataset_root != merkle_tree.get("dataset_root"):
        errors.append("dataset_root mismatch between rebuilt tree and merkle_tree.json")
    if dataset_root is not None and manifest.get("merkle_root") != dataset_root:
        errors.append("merkle_root mismatch between dataset_manifest.json and rebuilt tree")
    if merkle_tree.get("num_leaves") != len(leaf_hashes):
        errors.append("num_leaves mismatch between raw transitions and merkle_tree.json")
    if merkle_tree.get("leaf_hash_rule") != "sha256(canonical_json(transition))":
        errors.append("unexpected leaf_hash_rule in merkle_tree.json")

    dataset_type = manifest.get("dataset_type")
    if dataset_type == "self_collected_replay_audited":
        log_path = dataset_dir / COLLECTION_LOG_NAME
        if not log_path.exists():
            errors.append(f"missing required file: {COLLECTION_LOG_NAME}")
        else:
            log_ok, log_value = validate_collection_log(raw_path, log_path)
            if not log_ok:
                errors.append(f"collection log invalid: {log_value}")
            if log_ok and log_value != manifest.get("collection_log_final_hash"):
                errors.append("collection_log_final_hash mismatch between collection_log.jsonl and dataset_manifest.json")
            if log_ok and log_value != merkle_tree.get("collection_log_final_hash"):
                errors.append("collection_log_final_hash mismatch between collection_log.jsonl and merkle_tree.json")
        if manifest.get("collection_log_final_hash") is None:
            errors.append("self-collected dataset is missing collection_log_final_hash")
        if manifest.get("replay_audit_passed") is not True:
            errors.append("self-collected dataset requires replay_audit_passed=true")
        if manifest.get("reward_audit_passed") is not True:
            errors.append("self-collected dataset requires reward_audit_passed=true")
    elif dataset_type == "public_benchmark":
        if manifest.get("source_integrity_audit_passed") is not True:
            errors.append("public benchmark requires source_integrity_audit_passed=true")
        if manifest.get("replay_audit_passed") is not False:
            errors.append("public benchmark requires replay_audit_passed=false")
        if manifest.get("reward_audit_passed") is not False:
            errors.append("public benchmark requires reward_audit_passed=false")
        if merkle_tree.get("collection_log_final_hash") is not None:
            errors.append("public benchmark commitment must not claim collection_log_final_hash")
    else:
        errors.append(f"unsupported dataset_type: {dataset_type}")

    return not errors, errors
