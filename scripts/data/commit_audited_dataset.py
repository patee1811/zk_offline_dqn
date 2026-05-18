from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.data_pipeline import (
    AUDIT_REPORT_NAME,
    COLLECTION_LOG_NAME,
    RAW_EPISODES_NAME,
    build_dataset_merkle_commitment,
    hash_jsonl_transitions,
    load_manifest,
    sha256_file,
    validate_collection_log,
)


def verify_commit_preconditions(dataset_dir: Path) -> None:
    manifest = load_manifest(dataset_dir)
    raw_path = dataset_dir / RAW_EPISODES_NAME
    report_path = dataset_dir / AUDIT_REPORT_NAME
    raw_hash = hash_jsonl_transitions(raw_path)
    if raw_hash != manifest.get("raw_trajectory_hash"):
        raise ValueError("raw_trajectory_hash does not match raw_episodes.jsonl")
    if not report_path.exists():
        raise ValueError("missing replay_audit_report.json")
    if sha256_file(report_path) != manifest.get("audit_report_hash"):
        raise ValueError("audit_report_hash does not match replay_audit_report.json")

    dataset_type = manifest.get("dataset_type")
    if dataset_type == "self_collected_replay_audited":
        if manifest.get("replay_audit_passed") is not True:
            raise ValueError("replay_audit_passed must be true before commitment")
        if manifest.get("reward_audit_passed") is not True:
            raise ValueError("reward_audit_passed must be true before commitment")
        log_ok, log_value = validate_collection_log(raw_path, dataset_dir / COLLECTION_LOG_NAME)
        if not log_ok:
            raise ValueError(f"collection log invalid: {log_value}")
        if log_value != manifest.get("collection_log_final_hash"):
            raise ValueError("collection_log_final_hash does not match collection_log.jsonl")
    elif dataset_type == "public_benchmark":
        if manifest.get("source_integrity_audit_passed") is not True:
            raise ValueError("source_integrity_audit_passed must be true before commitment")
    else:
        raise ValueError(f"unsupported dataset_type: {dataset_type}")


def commit_dataset(dataset_dir: Path):
    verify_commit_preconditions(dataset_dir)
    return build_dataset_merkle_commitment(dataset_dir)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True)
    args = parser.parse_args()
    commitment = commit_dataset(Path(args.dataset_dir))
    manifest = load_manifest(args.dataset_dir)
    print(f"dataset_id = {commitment['dataset_id']}")
    print(f"dataset_type = {commitment['dataset_type']}")
    print(f"total_transitions = {manifest['total_transitions']}")
    print(f"merkle_root = {commitment['dataset_root']}")
    print(f"manifest_hash = {commitment['manifest_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
