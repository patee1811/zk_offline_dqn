"""Reference checker and fixture generator for training-fragment aggregation."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from zk_offline_dqn.relations.training_fragment import generate_case as generate_fragment_case
from zk_offline_dqn.relations.training_update import sha256_json


SCHEMA_VERSION = "sp1_training_aggregation_case_v1"
PUBLIC_SCHEMA_VERSION = "sp1_training_aggregation_public_v1"
AGGREGATION_MODE = "proof_manifest_chain"
CHUNK_RELATION_ID = "training_fragment_k8"
CLAIM_SCOPE = "chunk-chain aggregation over externally verified proof manifests"
CHUNK_FIELDS = [
    "chunk_id",
    "step_start",
    "step_end",
    "input_checkpoint_hash",
    "output_checkpoint_hash",
    "input_target_checkpoint_hash",
    "output_target_checkpoint_hash",
    "dataset_root",
    "manifest_hash",
    "audit_report_hash",
    "collection_log_final_hash",
    "raw_trajectory_hash",
    "config_hash",
    "relation_id",
    "public_inputs_hash",
    "proof_hash",
    "metrics_hash",
    "verify_report_hash",
    "tamper_report_hash",
]


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    reason: str
    public_output: Dict[str, Any] | None = None


def chunk_record_row(chunk: Mapping[str, Any]) -> str:
    return "|".join(str(chunk[field]) for field in CHUNK_FIELDS)


def hash_rows(format_name: str, rows: Iterable[str]) -> str:
    payload = format_name + "\n" + "\n".join(rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def recompute_roots(chunks: List[Mapping[str, Any]]) -> Dict[str, str]:
    return {
        "aggregate_root": hash_rows(
            "training_aggregation_chunk_records_v1",
            [chunk_record_row(chunk) for chunk in chunks],
        ),
        "chunk_public_inputs_root": hash_rows(
            "training_aggregation_public_inputs_root_v1",
            [str(chunk["public_inputs_hash"]) for chunk in chunks],
        ),
        "chunk_proof_root": hash_rows(
            "training_aggregation_proof_root_v1",
            [str(chunk["proof_hash"]) for chunk in chunks],
        ),
        "chunk_verify_report_root": hash_rows(
            "training_aggregation_verify_report_root_v1",
            [str(chunk["verify_report_hash"]) for chunk in chunks],
        ),
    }


def verify_vector(vector: Mapping[str, Any]) -> Dict[str, Any]:
    if vector.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError("schema_version mismatch")
    public = vector["public_inputs"]
    witness = vector["private_witness"]
    chunks = witness["chunks"]
    if public["relation"] != "training_aggregation":
        raise AssertionError("relation mismatch")
    if public["aggregation_mode"] != AGGREGATION_MODE:
        raise AssertionError("aggregation mode does not recursively verify child proofs")
    if public["claim_scope"] != CLAIM_SCOPE:
        raise AssertionError("claim_scope mismatch")
    if public["chunk_relation_id"] != CHUNK_RELATION_ID:
        raise AssertionError("chunk relation mismatch")
    if int(public["chunk_size"]) != 8:
        raise AssertionError("chunk_size mismatch")
    if int(public["chunk_count"]) != len(chunks):
        raise AssertionError("chunk_count mismatch")
    if not chunks:
        raise AssertionError("at least one chunk is required")
    if witness.get("child_proofs") != []:
        raise AssertionError("manifest-chain mode must not claim child proof bytes")
    if int(public["step_end"]) - int(public["step_start"]) != int(public["chunk_size"]) * len(chunks):
        raise AssertionError("aggregate step span mismatch")
    for field in [
        "input_checkpoint_hash",
        "output_checkpoint_hash",
        "input_target_checkpoint_hash",
        "output_target_checkpoint_hash",
        "dataset_root",
        "manifest_hash",
        "audit_report_hash",
        "collection_log_final_hash",
        "raw_trajectory_hash",
        "config_hash",
        "aggregate_root",
        "chunk_public_inputs_root",
        "chunk_proof_root",
        "chunk_verify_report_root",
    ]:
        assert_nonzero_hex_32(public[field], field)
    for index, chunk in enumerate(chunks):
        if int(chunk["chunk_id"]) != index:
            raise AssertionError("chunk order mismatch")
        if int(chunk["step_end"]) - int(chunk["step_start"]) != int(public["chunk_size"]):
            raise AssertionError("chunk step span mismatch")
        if chunk["relation_id"] != CHUNK_RELATION_ID:
            raise AssertionError("chunk relation_id mismatch")
        for field in [
            "dataset_root",
            "manifest_hash",
            "audit_report_hash",
            "collection_log_final_hash",
            "raw_trajectory_hash",
            "config_hash",
        ]:
            if chunk[field] != public[field]:
                raise AssertionError(f"{field} mismatch")
        for field in [
            "input_checkpoint_hash",
            "output_checkpoint_hash",
            "input_target_checkpoint_hash",
            "output_target_checkpoint_hash",
            "public_inputs_hash",
            "proof_hash",
            "metrics_hash",
            "verify_report_hash",
            "tamper_report_hash",
        ]:
            assert_nonzero_hex_32(chunk[field], field)
        if index + 1 < len(chunks):
            next_chunk = chunks[index + 1]
            if int(chunk["step_end"]) != int(next_chunk["step_start"]):
                raise AssertionError("chunk step link mismatch")
            if chunk["output_checkpoint_hash"] != next_chunk["input_checkpoint_hash"]:
                raise AssertionError("checkpoint link mismatch")
            if chunk["output_target_checkpoint_hash"] != next_chunk["input_target_checkpoint_hash"]:
                raise AssertionError("target checkpoint link mismatch")
    first = chunks[0]
    last = chunks[-1]
    for public_field, chunk_value in [
        ("step_start", first["step_start"]),
        ("step_end", last["step_end"]),
        ("input_checkpoint_hash", first["input_checkpoint_hash"]),
        ("output_checkpoint_hash", last["output_checkpoint_hash"]),
        ("input_target_checkpoint_hash", first["input_target_checkpoint_hash"]),
        ("output_target_checkpoint_hash", last["output_target_checkpoint_hash"]),
    ]:
        if public[public_field] != chunk_value:
            raise AssertionError(f"{public_field} mismatch")
    roots = recompute_roots(chunks)
    for key, value in roots.items():
        if public[key] != value:
            raise AssertionError(f"{key} mismatch")
    return public_output(vector, roots)


def public_output(vector: Mapping[str, Any], roots: Mapping[str, str]) -> Dict[str, Any]:
    public = vector["public_inputs"]
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "relation": public["relation"],
        "case_id": public["case_id"],
        "aggregation_mode": public["aggregation_mode"],
        "chunk_relation_id": public["chunk_relation_id"],
        "chunk_size": public["chunk_size"],
        "chunk_count": public["chunk_count"],
        "step_start": public["step_start"],
        "step_end": public["step_end"],
        "input_checkpoint_hash": public["input_checkpoint_hash"],
        "output_checkpoint_hash": public["output_checkpoint_hash"],
        "input_target_checkpoint_hash": public["input_target_checkpoint_hash"],
        "output_target_checkpoint_hash": public["output_target_checkpoint_hash"],
        "dataset_root": public["dataset_root"],
        "manifest_hash": public["manifest_hash"],
        "audit_report_hash": public["audit_report_hash"],
        "collection_log_final_hash": public["collection_log_final_hash"],
        "raw_trajectory_hash": public["raw_trajectory_hash"],
        "config_hash": public["config_hash"],
        "aggregate_root": roots["aggregate_root"],
        "chunk_public_inputs_root": roots["chunk_public_inputs_root"],
        "chunk_proof_root": roots["chunk_proof_root"],
        "chunk_verify_report_root": roots["chunk_verify_report_root"],
        "claim_scope": public["claim_scope"],
        "child_proof_verification_inside_guest": False,
    }


def verify_case(vector: Mapping[str, Any]) -> VerificationResult:
    try:
        return VerificationResult(True, "accepted", verify_vector(vector))
    except Exception as exc:  # noqa: BLE001 - negative tests need compact reasons
        return VerificationResult(False, str(exc), None)


def generate_case(step_end: int, *, chunk_size: int = 8) -> Dict[str, Any]:
    if chunk_size != 8:
        raise AssertionError("Phase 7 aggregates proof-backed k=8 chunks")
    if step_end <= 0 or step_end % chunk_size != 0:
        raise AssertionError("step_end must be a positive multiple of chunk_size")
    fragment = generate_fragment_case(step_end)
    fragment_public = fragment["public_inputs"]
    steps = fragment["private_witness"]["steps"]
    provenance_hashes = load_k8_provenance_hashes()
    config_hash = sha256_json(
        {
            "batch_size": fragment_public["batch_size"],
            "chunk_relation_id": CHUNK_RELATION_ID,
            "dataset_size": fragment_public["dataset_size"],
            "fixed_point_scale": fragment_public["fixed_point_scale"],
            "format": "training_aggregation_chunk_config_v1",
            "gamma": fragment_public["gamma"],
            "learning_rate": fragment_public["learning_rate"],
            "sampler_seed": fragment_public["sampler_seed"],
            "sampler_type": fragment_public["sampler_type"],
            "target_sync_interval": fragment_public["target_sync_interval"],
            "target_sync_mode": fragment_public["target_sync_mode"],
        }
    )
    chunks = []
    for chunk_id, step_start in enumerate(range(0, step_end, chunk_size)):
        final_step = step_start + chunk_size - 1
        boundary = {
            "chunk_id": chunk_id,
            "step_start": step_start,
            "step_end": step_start + chunk_size,
            "input_checkpoint_hash": steps[step_start]["checkpoint_hash_before"],
            "output_checkpoint_hash": steps[final_step]["checkpoint_hash_after"],
            "input_target_checkpoint_hash": steps[step_start]["target_checkpoint_hash_before"],
            "output_target_checkpoint_hash": steps[final_step]["target_checkpoint_hash_after"],
            "dataset_root": fragment_public["dataset_root"],
            "manifest_hash": fragment_public["manifest_hash"],
            "audit_report_hash": fragment_public["audit_report_hash"],
            "collection_log_final_hash": fragment_public["collection_log_final_hash"],
            "raw_trajectory_hash": fragment_public["raw_trajectory_hash"],
            "config_hash": config_hash,
            "relation_id": CHUNK_RELATION_ID,
        }
        public_inputs_hash = sha256_json(
            {
                "boundary": boundary,
                "format": "training_aggregation_child_public_inputs_v1",
                "source_relation_id": CHUNK_RELATION_ID,
            }
        )
        proof_hash = sha256_json(
            {
                "format": "training_aggregation_child_proof_manifest_v1",
                "public_inputs_hash": public_inputs_hash,
                "source_metrics_hash": provenance_hashes["metrics_hash"],
                "source_proof_policy_hash": provenance_hashes["proof_policy_hash"],
                "source_verify_report_hash": provenance_hashes["verify_report_hash"],
            }
        )
        chunks.append(
            {
                **boundary,
                "public_inputs_hash": public_inputs_hash,
                "proof_hash": proof_hash,
                "metrics_hash": provenance_hashes["metrics_hash"],
                "verify_report_hash": provenance_hashes["verify_report_hash"],
                "tamper_report_hash": provenance_hashes["tamper_report_hash"],
            }
        )
    roots = recompute_roots(chunks)
    public = {
        "relation": "training_aggregation",
        "case_id": f"training_aggregation_t{step_end}_case_0",
        "aggregation_mode": AGGREGATION_MODE,
        "chunk_relation_id": CHUNK_RELATION_ID,
        "chunk_size": chunk_size,
        "chunk_count": len(chunks),
        "step_start": 0,
        "step_end": step_end,
        "input_checkpoint_hash": chunks[0]["input_checkpoint_hash"],
        "output_checkpoint_hash": chunks[-1]["output_checkpoint_hash"],
        "input_target_checkpoint_hash": chunks[0]["input_target_checkpoint_hash"],
        "output_target_checkpoint_hash": chunks[-1]["output_target_checkpoint_hash"],
        "dataset_root": fragment_public["dataset_root"],
        "manifest_hash": fragment_public["manifest_hash"],
        "audit_report_hash": fragment_public["audit_report_hash"],
        "collection_log_final_hash": fragment_public["collection_log_final_hash"],
        "raw_trajectory_hash": fragment_public["raw_trajectory_hash"],
        "config_hash": config_hash,
        **roots,
        "claim_scope": CLAIM_SCOPE,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "public_inputs": public,
        "private_witness": {"chunks": chunks, "child_proofs": []},
    }


def load_k8_provenance_hashes() -> Dict[str, str]:
    root = Path(__file__).resolve().parents[2]
    provenance = root / "artifacts" / "reports" / "provenance" / "sp1" / "training_fragment_k8"
    return {
        "metrics_hash": sha256_file(provenance / "metrics.json"),
        "verify_report_hash": sha256_file(provenance / "verify_report.json"),
        "tamper_report_hash": sha256_file(provenance / "tamper_report.json"),
        "proof_policy_hash": sha256_file(provenance / "proof_artifact_policy.json"),
    }


def assert_nonzero_hex_32(value: Any, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise AssertionError(f"{field} must be a 32-byte hex string")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise AssertionError(f"{field} must be hex") from exc
    if len(raw) != 32 or raw == b"\x00" * 32:
        raise AssertionError(f"{field} must be nonzero")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tamper_copy(vector: Mapping[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(vector)
