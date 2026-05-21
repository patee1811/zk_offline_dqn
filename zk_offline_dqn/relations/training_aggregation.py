"""Reference checker and fixture generators for training-fragment aggregation."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from zk_offline_dqn.relations.training_fragment import (
    generate_case as generate_fragment_case,
    verify_case as verify_fragment_case,
)
from zk_offline_dqn.relations.training_update import sha256_json


SCHEMA_VERSION = "sp1_training_aggregation_case_v1"
PUBLIC_SCHEMA_VERSION = "sp1_training_aggregation_public_v1"
AGGREGATION_MODE = "proof_manifest_chain"
RECURSIVE_AGGREGATION_MODE = "recursive_sp1"
CHUNK_RELATION_ID = "training_fragment_k8"
BINARY_NODE_RELATION_ID = "training_aggregation_binary_node"
CLAIM_SCOPE = "chunk-chain aggregation over externally verified proof manifests"
RECURSIVE_CLAIM_SCOPE = "true recursive SP1 aggregation over child training-fragment proofs"
BINARY_CLAIM_SCOPE = "true recursive binary-tree native SP1 aggregation"
BINARY_AGGREGATION_TOPOLOGY = "binary_tree"
CHILD_PROOF_MODE = "native_sp1"
GROTH16_CHILD_PROOF_MODE = "groth16_bn254"
PLONK_CHILD_PROOF_MODE = "plonk_bn254"
RECURSIVE_CHILD_PROOF_MODES = {
    CHILD_PROOF_MODE,
    GROTH16_CHILD_PROOF_MODE,
    PLONK_CHILD_PROOF_MODE,
}
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
RECURSIVE_CHUNK_FIELDS = [
    *CHUNK_FIELDS,
    "child_public_inputs_hash",
    "child_vkey_hash",
    "child_proof_hash",
    "child_proof_mode",
    "child_verify_report_hash",
    "child_tamper_report_hash",
]


@dataclass(frozen=True)
class VerificationResult:
    accepted: bool
    reason: str
    public_output: Dict[str, Any] | None = None


def chunk_record_row(chunk: Mapping[str, Any], *, recursive: bool = False) -> str:
    fields = RECURSIVE_CHUNK_FIELDS if recursive else CHUNK_FIELDS
    return "|".join(str(chunk[field]) for field in fields)


def hash_rows(format_name: str, rows: Iterable[str]) -> str:
    payload = format_name + "\n" + "\n".join(rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def recompute_roots(chunks: List[Mapping[str, Any]], *, recursive: bool | None = None) -> Dict[str, str]:
    recursive = bool(chunks and "child_vkey_hash" in chunks[0]) if recursive is None else recursive
    if recursive:
        return {
            "aggregate_root": hash_rows(
                "training_aggregation_recursive_chunk_records_v1",
                [chunk_record_row(chunk, recursive=True) for chunk in chunks],
            ),
            "chunk_public_inputs_root": hash_rows(
                "training_aggregation_recursive_public_inputs_root_v1",
                [str(chunk["child_public_inputs_hash"]) for chunk in chunks],
            ),
            "chunk_proof_root": hash_rows(
                "training_aggregation_recursive_proof_root_v1",
                [str(chunk["child_proof_hash"]) for chunk in chunks],
            ),
            "chunk_verify_report_root": hash_rows(
                "training_aggregation_recursive_verify_report_root_v1",
                [str(chunk["child_verify_report_hash"]) for chunk in chunks],
            ),
            "chunk_vkey_root": hash_rows(
                "training_aggregation_recursive_vkey_root_v1",
                [str(chunk["child_vkey_hash"]) for chunk in chunks],
            ),
        }
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
    binary = public.get("aggregation_topology") == BINARY_AGGREGATION_TOPOLOGY
    if public["chunk_relation_id"] != (chunks[0]["relation_id"] if binary else CHUNK_RELATION_ID):
        raise AssertionError("chunk relation mismatch")
    if int(public["chunk_size"]) != 8:
        raise AssertionError("chunk_size mismatch")
    if int(public["chunk_count"]) != len(chunks):
        raise AssertionError("chunk_count mismatch")
    if not chunks:
        raise AssertionError("at least one chunk is required")
    span = int(public["step_end"]) - int(public["step_start"])
    expected_span = (
        int(public.get("leaf_chunk_count", 0)) * int(public["chunk_size"])
        if binary
        else int(public["chunk_size"]) * len(chunks)
    )
    if span != expected_span:
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
    if binary:
        _verify_binary_public(public, chunks)
    _verify_chunk_chain(public, chunks, binary=binary)
    recursive = public["aggregation_mode"] == RECURSIVE_AGGREGATION_MODE
    if public["aggregation_mode"] == AGGREGATION_MODE:
        if public["claim_scope"] != CLAIM_SCOPE:
            raise AssertionError("claim_scope mismatch")
        if witness.get("child_proofs") != []:
            raise AssertionError("manifest-chain mode must not claim child proof bytes")
        for field in [
            "child_proof_mode",
            "expected_child_vkey_hash",
            "expected_child_vkey_digest_words",
            "chunk_vkey_root",
        ]:
            if field in public:
                raise AssertionError(f"unexpected {field}")
    elif recursive:
        expected_claim_scope = BINARY_CLAIM_SCOPE if binary else RECURSIVE_CLAIM_SCOPE
        if public["claim_scope"] != expected_claim_scope:
            raise AssertionError("claim_scope mismatch")
        if public.get("child_proof_mode") not in RECURSIVE_CHILD_PROOF_MODES:
            raise AssertionError("child proof mode mismatch")
        assert_vkey_hash(public.get("expected_child_vkey_hash"), "expected_child_vkey_hash")
        if public["child_proof_mode"] == CHILD_PROOF_MODE:
            assert_vkey_digest_words(
                public.get("expected_child_vkey_digest_words"), "expected_child_vkey_digest_words"
            )
        elif "expected_child_vkey_digest_words" in public:
            raise AssertionError("unexpected expected_child_vkey_digest_words")
        assert_nonzero_hex_32(public.get("chunk_vkey_root"), "chunk_vkey_root")
        _verify_recursive_metadata(public, witness)
    else:
        raise AssertionError("unsupported aggregation_mode")
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
    roots = recompute_roots(chunks, recursive=recursive)
    for key, value in roots.items():
        if public.get(key) != value:
            raise AssertionError(f"{key} mismatch")
    return public_output(vector, roots, recursive=recursive, binary=binary)


def _verify_binary_public(public: Mapping[str, Any], chunks: Sequence[Mapping[str, Any]]) -> None:
    if public["aggregation_mode"] != RECURSIVE_AGGREGATION_MODE:
        raise AssertionError("binary tree aggregation must be recursive")
    if public.get("child_proof_mode") != CHILD_PROOF_MODE:
        raise AssertionError("binary tree aggregation must use native_sp1")
    if len(chunks) != 2 or int(public.get("chunk_count", 0)) != 2:
        raise AssertionError("binary tree fan-in mismatch")
    if int(public.get("child_count", 0)) != 2:
        raise AssertionError("binary child_count mismatch")
    if int(public.get("leaf_chunk_count", 0)) not in {2, 4}:
        raise AssertionError("binary leaf_chunk_count mismatch")
    if int(public.get("node_depth", 0)) < 1:
        raise AssertionError("binary node_depth mismatch")
    if int(public.get("node_range_start", -1)) != int(public["step_start"]):
        raise AssertionError("binary node_range_start mismatch")
    if int(public.get("node_range_end", -1)) != int(public["step_end"]):
        raise AssertionError("binary node_range_end mismatch")
    if not public.get("node_id"):
        raise AssertionError("binary node_id mismatch")
    left, right = chunks
    for public_field, value in [
        ("left_child_public_values_hash", left["child_public_inputs_hash"]),
        ("right_child_public_values_hash", right["child_public_inputs_hash"]),
        ("left_child_proof_hash", left["child_proof_hash"]),
        ("right_child_proof_hash", right["child_proof_hash"]),
        ("left_child_vkey_hash", left["child_vkey_hash"]),
        ("right_child_vkey_hash", right["child_vkey_hash"]),
    ]:
        if public.get(public_field) != value:
            raise AssertionError(f"{public_field} mismatch")
    if public.get("tree_root_hash") != binary_tree_root(chunks):
        raise AssertionError("tree_root_hash mismatch")


def _verify_chunk_chain(
    public: Mapping[str, Any], chunks: Sequence[Mapping[str, Any]], *, binary: bool = False
) -> None:
    for index, chunk in enumerate(chunks):
        if int(chunk["chunk_id"]) != index:
            raise AssertionError("chunk order mismatch")
        child_span = int(chunk["step_end"]) - int(chunk["step_start"])
        if binary:
            if child_span <= 0 or child_span % int(public["chunk_size"]) != 0:
                raise AssertionError("chunk step span mismatch")
            if chunk["relation_id"] != public["chunk_relation_id"]:
                raise AssertionError("chunk relation_id mismatch")
            if chunk["relation_id"] == CHUNK_RELATION_ID and child_span != int(public["chunk_size"]):
                raise AssertionError("leaf chunk step span mismatch")
            if chunk["relation_id"] not in {CHUNK_RELATION_ID, BINARY_NODE_RELATION_ID}:
                raise AssertionError("binary child relation_id mismatch")
        elif child_span != int(public["chunk_size"]):
            raise AssertionError("chunk step span mismatch")
        if not binary and chunk["relation_id"] != CHUNK_RELATION_ID:
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


def _verify_recursive_metadata(public: Mapping[str, Any], witness: Mapping[str, Any]) -> None:
    chunks = witness["chunks"]
    child_proofs = witness.get("child_proofs", [])
    if len(child_proofs) != len(chunks):
        raise AssertionError("child proof count mismatch")
    for index, (chunk, child) in enumerate(zip(chunks, child_proofs)):
        if int(child["chunk_id"]) != index:
            raise AssertionError("child proof order mismatch")
        proof_mode = public["child_proof_mode"]
        if child["proof_mode"] != proof_mode or chunk["child_proof_mode"] != proof_mode:
            raise AssertionError("child proof mode mismatch")
        if child["vkey_hash"] != public["expected_child_vkey_hash"]:
            raise AssertionError("unexpected child verification key")
        if chunk["child_vkey_hash"] != child["vkey_hash"]:
            raise AssertionError("chunk child vkey hash mismatch")
        assert_vkey_hash(child["vkey_hash"], "child_vkey_hash")
        if proof_mode == CHILD_PROOF_MODE:
            if child.get("vkey_digest_words") != public["expected_child_vkey_digest_words"]:
                raise AssertionError("unexpected child verification key digest")
            assert_vkey_digest_words(child["vkey_digest_words"], "child_vkey_digest_words")
            if not child.get("vkey_bytes"):
                raise AssertionError("missing child vkey bytes")
        else:
            if child.get("vkey_digest_words"):
                raise AssertionError("unexpected child vkey digest words")
            if child.get("vkey_bytes"):
                raise AssertionError("unexpected child vkey bytes")
        proof_hash = sha256_hex_bytes(child["proof_bytes"], "child proof bytes")
        public_values_hash = sha256_hex_bytes(child["public_values_bytes"], "child public values")
        if chunk["child_proof_hash"] != proof_hash or chunk["proof_hash"] != proof_hash:
            raise AssertionError("child proof hash mismatch")
        if chunk["child_public_inputs_hash"] != public_values_hash or chunk["public_inputs_hash"] != public_values_hash:
            raise AssertionError("child public values hash mismatch")
        if chunk["child_verify_report_hash"] != chunk["verify_report_hash"]:
            raise AssertionError("child verify report hash mismatch")
        if chunk["child_tamper_report_hash"] != chunk["tamper_report_hash"]:
            raise AssertionError("child tamper report hash mismatch")
        for field in [
            "child_public_inputs_hash",
            "child_proof_hash",
            "child_verify_report_hash",
            "child_tamper_report_hash",
        ]:
            assert_nonzero_hex_32(chunk[field], field)


def public_output(
    vector: Mapping[str, Any],
    roots: Mapping[str, str],
    *,
    recursive: bool,
    binary: bool = False,
) -> Dict[str, Any]:
    public = vector["public_inputs"]
    output = {
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
        "child_proof_verification_inside_guest": recursive,
    }
    if recursive:
        output.update(
            {
                "chunk_vkey_root": roots["chunk_vkey_root"],
                "child_proof_mode": public["child_proof_mode"],
                "expected_child_vkey_hash": public["expected_child_vkey_hash"],
            }
        )
        if "expected_child_vkey_digest_words" in public:
            output["expected_child_vkey_digest_words"] = public[
                "expected_child_vkey_digest_words"
            ]
    if binary:
        for field in [
            "aggregation_topology",
            "node_id",
            "node_depth",
            "node_range_start",
            "node_range_end",
            "leaf_chunk_count",
            "child_count",
            "left_child_public_values_hash",
            "right_child_public_values_hash",
            "left_child_proof_hash",
            "right_child_proof_hash",
            "left_child_vkey_hash",
            "right_child_vkey_hash",
            "tree_root_hash",
        ]:
            output[field] = public[field]
    return output


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
    config_hash = config_hash_from_fragment_public(fragment_public)
    chunks = []
    for chunk_id, step_start in enumerate(range(0, step_end, chunk_size)):
        final_step = step_start + chunk_size - 1
        boundary = _chunk_boundary(
            chunk_id,
            step_start,
            steps[step_start],
            steps[final_step],
            fragment_public,
            config_hash,
            chunk_size,
        )
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
    return _aggregation_vector(
        step_end,
        chunks,
        fragment_public,
        config_hash,
        roots,
        aggregation_mode=AGGREGATION_MODE,
        claim_scope=CLAIM_SCOPE,
        child_proofs=[],
    )


def generate_recursive_case(
    step_end: int,
    *,
    child_materials: Sequence[Mapping[str, Any]] | None = None,
    child_proof_mode: str = CHILD_PROOF_MODE,
    chunk_size: int = 8,
) -> Dict[str, Any]:
    if child_proof_mode not in RECURSIVE_CHILD_PROOF_MODES:
        raise AssertionError("unsupported recursive child proof mode")
    child_cases = generate_recursive_child_cases(step_end, chunk_size=chunk_size)
    materials = list(child_materials) if child_materials is not None else [
        placeholder_child_material(child_case, chunk_id, proof_mode=child_proof_mode)
        for chunk_id, child_case in enumerate(child_cases)
    ]
    if len(materials) != len(child_cases):
        raise AssertionError("child material count mismatch")
    provenance_hashes = load_k8_provenance_hashes()
    chunks = []
    child_proofs = []
    first_public = child_cases[0]["public_inputs"]
    config_hash = config_hash_from_fragment_public(first_public)
    expected_vkey_hash = str(materials[0]["vkey_hash"])
    expected_vkey_digest_words = list(materials[0].get("vkey_digest_words", []))
    for chunk_id, (child_case, material) in enumerate(zip(child_cases, materials)):
        result = verify_fragment_case(child_case)
        if not result.accepted or result.public_output is None:
            raise AssertionError(f"child case {chunk_id} rejected: {result.reason}")
        child_public = child_case["public_inputs"]
        child_output = result.public_output
        if str(material["vkey_hash"]) != expected_vkey_hash:
            raise AssertionError("recursive child vkey mismatch")
        if str(material["proof_mode"]) != child_proof_mode:
            raise AssertionError("recursive child proof mode mismatch")
        if list(material.get("vkey_digest_words", [])) != expected_vkey_digest_words:
            raise AssertionError("recursive child vkey digest mismatch")
        proof_hash = sha256_hex_bytes(str(material["proof_bytes"]), "child proof bytes")
        public_hash = sha256_hex_bytes(
            str(material["public_values_bytes"]), "child public values"
        )
        chunk = {
            "chunk_id": chunk_id,
            "step_start": child_public["global_step_start"],
            "step_end": child_public["global_step_start"] + child_public["num_steps"],
            "input_checkpoint_hash": child_output["start_checkpoint_hash"],
            "output_checkpoint_hash": child_output["final_checkpoint_hash"],
            "input_target_checkpoint_hash": child_output["start_target_checkpoint_hash"],
            "output_target_checkpoint_hash": child_output["final_target_checkpoint_hash"],
            "dataset_root": child_public["dataset_root"],
            "manifest_hash": child_public["manifest_hash"],
            "audit_report_hash": child_public["audit_report_hash"],
            "collection_log_final_hash": child_public["collection_log_final_hash"],
            "raw_trajectory_hash": child_public["raw_trajectory_hash"],
            "config_hash": config_hash_from_fragment_public(child_public),
            "relation_id": CHUNK_RELATION_ID,
            "public_inputs_hash": public_hash,
            "proof_hash": proof_hash,
            "metrics_hash": str(material.get("metrics_hash", provenance_hashes["metrics_hash"])),
            "verify_report_hash": str(
                material.get("verify_report_hash", provenance_hashes["verify_report_hash"])
            ),
            "tamper_report_hash": str(
                material.get("tamper_report_hash", provenance_hashes["tamper_report_hash"])
            ),
            "child_public_inputs_hash": public_hash,
            "child_vkey_hash": str(material["vkey_hash"]),
            "child_proof_hash": proof_hash,
            "child_proof_mode": child_proof_mode,
            "child_verify_report_hash": str(
                material.get("verify_report_hash", provenance_hashes["verify_report_hash"])
            ),
            "child_tamper_report_hash": str(
                material.get("tamper_report_hash", provenance_hashes["tamper_report_hash"])
            ),
        }
        chunks.append(chunk)
        child_proofs.append(
            {
                "chunk_id": chunk_id,
                "proof_mode": child_proof_mode,
                "proof_bytes": str(material["proof_bytes"]),
                "public_values_bytes": str(material["public_values_bytes"]),
                "vkey_hash": str(material["vkey_hash"]),
                **(
                    {
                        "vkey_digest_words": list(material["vkey_digest_words"]),
                        "vkey_bytes": str(material["vkey_bytes"]),
                    }
                    if child_proof_mode == CHILD_PROOF_MODE
                    else {}
                ),
            }
        )
    roots = recompute_roots(chunks, recursive=True)
    vector = _aggregation_vector(
        step_end,
        chunks,
        first_public,
        config_hash,
        roots,
        aggregation_mode=RECURSIVE_AGGREGATION_MODE,
        claim_scope=RECURSIVE_CLAIM_SCOPE,
        child_proofs=child_proofs,
    )
    vector["public_inputs"].update(
        {
            "child_proof_mode": child_proof_mode,
            "expected_child_vkey_hash": expected_vkey_hash,
            "chunk_vkey_root": roots["chunk_vkey_root"],
        }
    )
    if child_proof_mode == CHILD_PROOF_MODE:
        vector["public_inputs"]["expected_child_vkey_digest_words"] = expected_vkey_digest_words
    return vector


def generate_binary_native_case(step_end: int, *, chunk_size: int = 8) -> Dict[str, Any]:
    if step_end not in {16, 32}:
        raise AssertionError("binary native fixtures target T=16 or T=32")
    child_cases = generate_recursive_child_cases(step_end, chunk_size=chunk_size)
    if step_end == 16:
        return build_binary_native_case(
            child_cases,
            [
                placeholder_child_material(child_case, index)
                for index, child_case in enumerate(child_cases)
            ],
            node_id="root",
            node_depth=1,
            leaf_chunk_count=2,
        )
    left = build_binary_native_case(
        child_cases[:2],
        [placeholder_child_material(child_case, index) for index, child_case in enumerate(child_cases[:2])],
        node_id="level1_left",
        node_depth=1,
        leaf_chunk_count=2,
    )
    right = build_binary_native_case(
        child_cases[2:],
        [
            placeholder_child_material(child_case, index + 2)
            for index, child_case in enumerate(child_cases[2:])
        ],
        node_id="level1_right",
        node_depth=1,
        leaf_chunk_count=2,
    )
    return build_binary_native_case(
        [left, right],
        [
            placeholder_aggregation_child_material(left, 0),
            placeholder_aggregation_child_material(right, 1),
        ],
        node_id="root",
        node_depth=2,
        leaf_chunk_count=4,
    )


def build_binary_native_case(
    child_cases: Sequence[Mapping[str, Any]],
    child_materials: Sequence[Mapping[str, Any]],
    *,
    node_id: str,
    node_depth: int,
    leaf_chunk_count: int,
) -> Dict[str, Any]:
    if len(child_cases) != 2 or len(child_materials) != 2:
        raise AssertionError("binary aggregation requires exactly two children")
    provenance_hashes = load_k8_provenance_hashes()
    chunks = []
    child_proofs = []
    expected_vkey_hash = str(child_materials[0]["vkey_hash"])
    expected_vkey_digest_words = list(child_materials[0].get("vkey_digest_words", []))
    first_context: Mapping[str, Any] | None = None
    for chunk_id, (child_case, material) in enumerate(zip(child_cases, child_materials)):
        boundary, child_context = _binary_child_boundary(child_case, chunk_id)
        if first_context is None:
            first_context = child_context
        if str(material["proof_mode"]) != CHILD_PROOF_MODE:
            raise AssertionError("binary native child proof mode mismatch")
        if str(material["vkey_hash"]) != expected_vkey_hash:
            raise AssertionError("binary native child vkey mismatch")
        if list(material.get("vkey_digest_words", [])) != expected_vkey_digest_words:
            raise AssertionError("binary native child vkey digest mismatch")
        proof_hash = sha256_hex_bytes(str(material["proof_bytes"]), "child proof bytes")
        public_hash = sha256_hex_bytes(
            str(material["public_values_bytes"]), "child public values"
        )
        chunk = {
            **boundary,
            "public_inputs_hash": public_hash,
            "proof_hash": proof_hash,
            "metrics_hash": str(material.get("metrics_hash", provenance_hashes["metrics_hash"])),
            "verify_report_hash": str(
                material.get("verify_report_hash", provenance_hashes["verify_report_hash"])
            ),
            "tamper_report_hash": str(
                material.get("tamper_report_hash", provenance_hashes["tamper_report_hash"])
            ),
            "child_public_inputs_hash": public_hash,
            "child_vkey_hash": expected_vkey_hash,
            "child_proof_hash": proof_hash,
            "child_proof_mode": CHILD_PROOF_MODE,
            "child_verify_report_hash": str(
                material.get("verify_report_hash", provenance_hashes["verify_report_hash"])
            ),
            "child_tamper_report_hash": str(
                material.get("tamper_report_hash", provenance_hashes["tamper_report_hash"])
            ),
        }
        chunks.append(chunk)
        child_proofs.append(
            {
                "chunk_id": chunk_id,
                "proof_mode": CHILD_PROOF_MODE,
                "proof_bytes": str(material["proof_bytes"]),
                "public_values_bytes": str(material["public_values_bytes"]),
                "vkey_hash": expected_vkey_hash,
                "vkey_digest_words": expected_vkey_digest_words,
                "vkey_bytes": str(material["vkey_bytes"]),
            }
        )
    if first_context is None:
        raise AssertionError("binary child context missing")
    roots = recompute_roots(chunks, recursive=True)
    vector = _aggregation_vector(
        chunks[-1]["step_end"],
        chunks,
        first_context,
        chunks[0]["config_hash"],
        roots,
        aggregation_mode=RECURSIVE_AGGREGATION_MODE,
        claim_scope=BINARY_CLAIM_SCOPE,
        child_proofs=child_proofs,
    )
    left, right = chunks
    vector["public_inputs"].update(
        {
            "case_id": (
                f"training_aggregation_binary_native_t{chunks[-1]['step_end']}_case_0"
                if node_id == "root"
                else f"training_aggregation_binary_native_{node_id}_steps_{chunks[0]['step_start']}_{chunks[-1]['step_end']}_case_0"
            ),
            "aggregation_topology": BINARY_AGGREGATION_TOPOLOGY,
            "child_proof_mode": CHILD_PROOF_MODE,
            "expected_child_vkey_hash": expected_vkey_hash,
            "expected_child_vkey_digest_words": expected_vkey_digest_words,
            "chunk_relation_id": chunks[0]["relation_id"],
            "chunk_vkey_root": roots["chunk_vkey_root"],
            "node_id": node_id,
            "node_depth": node_depth,
            "node_range_start": chunks[0]["step_start"],
            "node_range_end": chunks[-1]["step_end"],
            "leaf_chunk_count": leaf_chunk_count,
            "child_count": 2,
            "left_child_public_values_hash": left["child_public_inputs_hash"],
            "right_child_public_values_hash": right["child_public_inputs_hash"],
            "left_child_proof_hash": left["child_proof_hash"],
            "right_child_proof_hash": right["child_proof_hash"],
            "left_child_vkey_hash": left["child_vkey_hash"],
            "right_child_vkey_hash": right["child_vkey_hash"],
            "tree_root_hash": binary_tree_root(chunks),
        }
    )
    return vector


def generate_recursive_child_cases(step_end: int, *, chunk_size: int = 8) -> List[Dict[str, Any]]:
    if chunk_size != 8:
        raise AssertionError("Phase 7B recursively aggregates k=8 child proofs")
    if step_end <= 0 or step_end % chunk_size != 0:
        raise AssertionError("step_end must be a positive multiple of chunk_size")
    child_cases = []
    online = None
    target = None
    for chunk_id, step_start in enumerate(range(0, step_end, chunk_size)):
        child_case = generate_fragment_case(
            chunk_size,
            global_step_start=step_start,
            online_start=online,
            target_start=target,
            case_id=f"training_fragment_recursive_chunk_{chunk_id}_steps_{step_start}_{step_start + chunk_size}",
        )
        child_cases.append(child_case)
        last_step = child_case["private_witness"]["steps"][-1]
        online = last_step["online_model_after"]
        target = last_step["target_model_after"]
    return child_cases


def placeholder_child_material(
    child_case: Mapping[str, Any],
    chunk_id: int,
    *,
    proof_mode: str = CHILD_PROOF_MODE,
) -> Dict[str, Any]:
    output = verify_fragment_case(child_case).public_output
    if output is None:
        raise AssertionError("placeholder child case rejected")
    public_values = json.dumps(output, sort_keys=True, separators=(",", ":")).encode("utf-8").hex()
    proof_bytes = hashlib.sha256(
        f"recursive_child_placeholder_proof_{chunk_id}".encode("utf-8")
    ).digest().hex()
    material: Dict[str, Any] = {
        "proof_mode": proof_mode,
        "proof_bytes": proof_bytes,
        "public_values_bytes": public_values,
        "vkey_hash": "0x" + hashlib.sha256(b"recursive_training_fragment_vkey").hexdigest(),
    }
    if proof_mode == CHILD_PROOF_MODE:
        material.update(
            {
                "vkey_digest_words": [
                    int.from_bytes(
                        hashlib.sha256(f"recursive_vkey_{index}".encode("utf-8")).digest()[:4],
                        "big",
                    )
                    for index in range(8)
                ],
                "vkey_bytes": hashlib.sha256(b"recursive_training_fragment_vkey_bytes")
                .digest()
                .hex(),
            }
        )
    return material


def placeholder_aggregation_child_material(
    child_case: Mapping[str, Any], child_id: int
) -> Dict[str, Any]:
    output = verify_case(child_case).public_output
    if output is None:
        raise AssertionError("placeholder aggregation child case rejected")
    return {
        "proof_mode": CHILD_PROOF_MODE,
        "proof_bytes": hashlib.sha256(
            f"recursive_binary_aggregation_placeholder_proof_{child_id}".encode("utf-8")
        ).digest().hex(),
        "public_values_bytes": json.dumps(
            output, sort_keys=True, separators=(",", ":")
        ).encode("utf-8").hex(),
        "vkey_hash": "0x"
        + hashlib.sha256(b"recursive_binary_training_aggregation_vkey").hexdigest(),
        "vkey_digest_words": [
            int.from_bytes(
                hashlib.sha256(f"recursive_binary_vkey_{index}".encode("utf-8")).digest()[:4],
                "big",
            )
            for index in range(8)
        ],
        "vkey_bytes": hashlib.sha256(b"recursive_binary_training_aggregation_vkey_bytes")
        .digest()
        .hex(),
    }


def _binary_child_boundary(
    child_case: Mapping[str, Any], chunk_id: int
) -> tuple[Dict[str, Any], Mapping[str, Any]]:
    child_public = child_case["public_inputs"]
    if child_public["relation"] == "training_fragment":
        result = verify_fragment_case(child_case)
        if not result.accepted or result.public_output is None:
            raise AssertionError(f"binary leaf child {chunk_id} rejected: {result.reason}")
        output = result.public_output
        config_hash = config_hash_from_fragment_public(child_public)
        return (
            {
                "chunk_id": chunk_id,
                "step_start": output["global_step_start"],
                "step_end": output["global_step_start"] + output["num_steps"],
                "input_checkpoint_hash": output["start_checkpoint_hash"],
                "output_checkpoint_hash": output["final_checkpoint_hash"],
                "input_target_checkpoint_hash": output["start_target_checkpoint_hash"],
                "output_target_checkpoint_hash": output["final_target_checkpoint_hash"],
                "dataset_root": output["dataset_root"],
                "manifest_hash": output["manifest_hash"],
                "audit_report_hash": output["audit_report_hash"],
                "collection_log_final_hash": output["collection_log_final_hash"],
                "raw_trajectory_hash": output["raw_trajectory_hash"],
                "config_hash": config_hash,
                "relation_id": CHUNK_RELATION_ID,
            },
            child_public,
        )
    if child_public["relation"] == "training_aggregation":
        result = verify_case(child_case)
        if not result.accepted or result.public_output is None:
            raise AssertionError(f"binary node child {chunk_id} rejected: {result.reason}")
        output = result.public_output
        return (
            {
                "chunk_id": chunk_id,
                "step_start": output["step_start"],
                "step_end": output["step_end"],
                "input_checkpoint_hash": output["input_checkpoint_hash"],
                "output_checkpoint_hash": output["output_checkpoint_hash"],
                "input_target_checkpoint_hash": output["input_target_checkpoint_hash"],
                "output_target_checkpoint_hash": output["output_target_checkpoint_hash"],
                "dataset_root": output["dataset_root"],
                "manifest_hash": output["manifest_hash"],
                "audit_report_hash": output["audit_report_hash"],
                "collection_log_final_hash": output["collection_log_final_hash"],
                "raw_trajectory_hash": output["raw_trajectory_hash"],
                "config_hash": output["config_hash"],
                "relation_id": BINARY_NODE_RELATION_ID,
            },
            output,
        )
    raise AssertionError("unsupported binary child relation")


def binary_tree_root(chunks: Sequence[Mapping[str, Any]]) -> str:
    if len(chunks) != 2:
        raise AssertionError("binary tree root requires two children")
    return hash_rows(
        "training_aggregation_binary_tree_node_v1",
        [
            "|".join(
                [
                    side,
                    str(chunk["relation_id"]),
                    str(chunk["step_start"]),
                    str(chunk["step_end"]),
                    str(chunk["child_public_inputs_hash"]),
                    str(chunk["child_proof_hash"]),
                    str(chunk["child_vkey_hash"]),
                    str(chunk["input_checkpoint_hash"]),
                    str(chunk["output_checkpoint_hash"]),
                    str(chunk["input_target_checkpoint_hash"]),
                    str(chunk["output_target_checkpoint_hash"]),
                ]
            )
            for side, chunk in zip(["left", "right"], chunks)
        ],
    )


def config_hash_from_fragment_public(fragment_public: Mapping[str, Any]) -> str:
    return sha256_json(
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


def _chunk_boundary(
    chunk_id: int,
    step_start: int,
    first_step: Mapping[str, Any],
    final_step: Mapping[str, Any],
    fragment_public: Mapping[str, Any],
    config_hash: str,
    chunk_size: int,
) -> Dict[str, Any]:
    return {
        "chunk_id": chunk_id,
        "step_start": step_start,
        "step_end": step_start + chunk_size,
        "input_checkpoint_hash": first_step["checkpoint_hash_before"],
        "output_checkpoint_hash": final_step["checkpoint_hash_after"],
        "input_target_checkpoint_hash": first_step["target_checkpoint_hash_before"],
        "output_target_checkpoint_hash": final_step["target_checkpoint_hash_after"],
        "dataset_root": fragment_public["dataset_root"],
        "manifest_hash": fragment_public["manifest_hash"],
        "audit_report_hash": fragment_public["audit_report_hash"],
        "collection_log_final_hash": fragment_public["collection_log_final_hash"],
        "raw_trajectory_hash": fragment_public["raw_trajectory_hash"],
        "config_hash": config_hash,
        "relation_id": CHUNK_RELATION_ID,
    }


def _aggregation_vector(
    step_end: int,
    chunks: Sequence[Mapping[str, Any]],
    fragment_public: Mapping[str, Any],
    config_hash: str,
    roots: Mapping[str, str],
    *,
    aggregation_mode: str,
    claim_scope: str,
    child_proofs: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    public = {
        "relation": "training_aggregation",
        "case_id": (
            f"training_aggregation_recursive_t{step_end}_case_0"
            if aggregation_mode == RECURSIVE_AGGREGATION_MODE
            else f"training_aggregation_t{step_end}_case_0"
        ),
        "aggregation_mode": aggregation_mode,
        "chunk_relation_id": CHUNK_RELATION_ID,
        "chunk_size": 8,
        "chunk_count": len(chunks),
        "step_start": chunks[0]["step_start"],
        "step_end": chunks[-1]["step_end"],
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
        "claim_scope": claim_scope,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "public_inputs": public,
        "private_witness": {"chunks": list(chunks), "child_proofs": list(child_proofs)},
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


def assert_vkey_hash(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise AssertionError(f"{field} must be 0x-prefixed")
    assert_nonzero_hex_32(value[2:], field)


def assert_vkey_digest_words(value: Any, field: str) -> None:
    if not isinstance(value, list) or len(value) != 8:
        raise AssertionError(f"{field} must have eight words")
    if not all(isinstance(item, int) and 0 <= item <= 0xFFFFFFFF for item in value):
        raise AssertionError(f"{field} words must be u32")
    if not any(value):
        raise AssertionError(f"{field} must be nonzero")


def sha256_hex_bytes(value: str, field: str) -> str:
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise AssertionError(f"{field} must be hex") from exc
    if not raw:
        raise AssertionError(f"{field} must be nonempty")
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tamper_copy(vector: Mapping[str, Any]) -> Dict[str, Any]:
    return copy.deepcopy(vector)
