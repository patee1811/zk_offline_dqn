"""Python helpers for the Phase 7 SP1 training aggregation backend."""

from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from zk_offline_dqn.relations.training_aggregation import (
    VerificationResult,
    generate_binary_native_case,
    generate_case,
    generate_recursive_case,
    verify_case,
)


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "training_aggregation" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "training_aggregation_t32_case_0.json"


def case_path_for_target(target: int) -> Path:
    return ROOT / "zk_backend" / "test_vectors" / f"training_aggregation_t{target}_case_0.json"


def recursive_case_path_for_target(target: int) -> Path:
    return ROOT / "zk_backend" / "test_vectors" / f"training_aggregation_recursive_t{target}_case_0.json"


def binary_native_case_path_for_target(target: int) -> Path:
    return (
        ROOT
        / "zk_backend"
        / "test_vectors"
        / f"training_aggregation_binary_native_t{target}_case_0.json"
    )


def load_case(path: str | Path = DEFAULT_CASE_PATH) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_generated_case(target: int, path: str | Path | None = None) -> Path:
    out_path = Path(path) if path is not None else case_path_for_target(target)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(generate_case(target), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return out_path


def write_generated_recursive_case(
    target: int,
    path: str | Path | None = None,
    *,
    child_materials: List[Dict[str, Any]] | None = None,
    child_proof_mode: str | None = None,
) -> Path:
    out_path = Path(path) if path is not None else recursive_case_path_for_target(target)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            generate_recursive_case(
                target,
                child_materials=child_materials,
                **({"child_proof_mode": child_proof_mode} if child_proof_mode else {}),
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    return out_path


def write_generated_binary_native_case(
    target: int,
    path: str | Path | None = None,
) -> Path:
    out_path = Path(path) if path is not None else binary_native_case_path_for_target(target)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(generate_binary_native_case(target), sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    return out_path


def verify_case_reference(case: Dict[str, Any]) -> VerificationResult:
    return verify_case(case)


def cargo_command(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    aggregation_mode: str = "proof_manifest_chain",
    child_proof_mode: str | None = None,
    topology: str | None = None,
    out_dir: str | Path | None = None,
) -> List[str]:
    command = [
        "cargo",
        "run",
        "--release",
        "-p",
        "training-aggregation-host",
        "--",
        f"--{mode}",
        "--case",
        str(case_path),
        "--mode",
        aggregation_mode,
    ]
    if out_dir is not None:
        command.extend(["--out-dir", str(out_dir)])
    if child_proof_mode is not None:
        command.extend(["--child-proof-mode", child_proof_mode])
    if topology is not None:
        command.extend(["--topology", topology])
    return command


def run_cargo(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    aggregation_mode: str = "proof_manifest_chain",
    child_proof_mode: str | None = None,
    topology: str | None = None,
    out_dir: str | Path | None = None,
    timeout: int = 1200,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if mode == "prove":
        env["RUN_SP1_PROVE"] = "1"
    return subprocess.run(
        cargo_command(
            case_path=case_path,
            mode=mode,
            aggregation_mode=aggregation_mode,
            child_proof_mode=child_proof_mode,
            topology=topology,
            out_dir=out_dir,
        ),
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def tampered_case(case: Dict[str, Any], name: str) -> Dict[str, Any]:
    mutated = copy.deepcopy(case)
    public = mutated["public_inputs"]
    chunks = mutated["private_witness"]["chunks"]
    first = chunks[0]
    if name == "tamper_step_start":
        public["step_start"] += 1
    elif name == "tamper_step_end":
        public["step_end"] -= 1
    elif name == "tamper_chunk_order":
        chunks[0], chunks[1] = chunks[1], chunks[0]
    elif name == "tamper_missing_chunk":
        chunks.pop()
    elif name == "tamper_duplicate_chunk":
        chunks[1] = copy.deepcopy(chunks[0])
    elif name == "tamper_input_checkpoint_hash":
        public["input_checkpoint_hash"] = _flip_hex(public["input_checkpoint_hash"])
    elif name == "tamper_output_checkpoint_hash":
        public["output_checkpoint_hash"] = _flip_hex(public["output_checkpoint_hash"])
    elif name == "tamper_intermediate_checkpoint_link":
        chunks[1]["input_checkpoint_hash"] = _flip_hex(chunks[1]["input_checkpoint_hash"])
    elif name == "tamper_target_checkpoint_link":
        chunks[1]["input_target_checkpoint_hash"] = _flip_hex(
            chunks[1]["input_target_checkpoint_hash"]
        )
    elif name == "tamper_dataset_root":
        public["dataset_root"] = _flip_hex(public["dataset_root"])
    elif name == "tamper_manifest_hash":
        first["manifest_hash"] = _flip_hex(first["manifest_hash"])
    elif name == "tamper_audit_report_hash":
        first["audit_report_hash"] = _flip_hex(first["audit_report_hash"])
    elif name == "tamper_collection_log_hash":
        first["collection_log_final_hash"] = _flip_hex(first["collection_log_final_hash"])
    elif name == "tamper_raw_trajectory_hash":
        first["raw_trajectory_hash"] = _flip_hex(first["raw_trajectory_hash"])
    elif name == "tamper_config_hash":
        first["config_hash"] = _flip_hex(first["config_hash"])
    elif name == "tamper_relation_id":
        first["relation_id"] = "training_fragment_k4"
    elif name == "tamper_chunk_size":
        public["chunk_size"] = 4
    elif name == "tamper_chunk_count":
        public["chunk_count"] += 1
    elif name == "tamper_public_inputs_hash":
        first["public_inputs_hash"] = _flip_hex(first["public_inputs_hash"])
    elif name == "tamper_proof_hash":
        first["proof_hash"] = _flip_hex(first["proof_hash"])
    elif name == "tamper_verify_report_hash":
        first["verify_report_hash"] = _flip_hex(first["verify_report_hash"])
    elif name == "tamper_tamper_report_hash":
        first["tamper_report_hash"] = _flip_hex(first["tamper_report_hash"])
    elif name == "tamper_aggregate_root":
        public["aggregate_root"] = _flip_hex(public["aggregate_root"])
    elif name == "tamper_chunk_public_inputs_root":
        public["chunk_public_inputs_root"] = _flip_hex(public["chunk_public_inputs_root"])
    elif name == "tamper_chunk_proof_root":
        public["chunk_proof_root"] = _flip_hex(public["chunk_proof_root"])
    elif name in {
        "tamper_child_proof_bytes",
        "tamper_groth16_child_proof_bytes",
        "tamper_plonk_child_proof_bytes",
    }:
        mutated["private_witness"]["child_proofs"][0]["proof_bytes"] = _flip_hex(
            mutated["private_witness"]["child_proofs"][0]["proof_bytes"]
        )
    elif name in {
        "tamper_child_public_values",
        "tamper_groth16_child_public_values",
        "tamper_plonk_child_public_values",
        "tamper_groth16_child_public_values_hash",
        "tamper_plonk_child_public_values_hash",
    }:
        mutated["private_witness"]["child_proofs"][0]["public_values_bytes"] = _flip_hex(
            mutated["private_witness"]["child_proofs"][0]["public_values_bytes"]
        )
    elif name in {
        "tamper_child_vkey_hash",
        "tamper_groth16_child_vkey_hash",
        "tamper_plonk_child_vkey_hash",
    }:
        mutated["private_witness"]["child_proofs"][0]["vkey_hash"] = _flip_vkey(
            mutated["private_witness"]["child_proofs"][0]["vkey_hash"]
        )
    elif name == "tamper_child_proof_hash":
        first["child_proof_hash"] = _flip_hex(first["child_proof_hash"])
    elif name == "tamper_child_proof_order":
        proofs = mutated["private_witness"]["child_proofs"]
        proofs[0], proofs[1] = proofs[1], proofs[0]
    elif name == "tamper_child_step_start":
        first["step_start"] += 1
    elif name == "tamper_child_step_end":
        first["step_end"] -= 1
    elif name == "tamper_child_input_checkpoint_hash":
        first["input_checkpoint_hash"] = _flip_hex(first["input_checkpoint_hash"])
    elif name == "tamper_child_output_checkpoint_hash":
        first["output_checkpoint_hash"] = _flip_hex(first["output_checkpoint_hash"])
    elif name == "tamper_child_target_checkpoint_hash":
        first["output_target_checkpoint_hash"] = _flip_hex(first["output_target_checkpoint_hash"])
    elif name == "tamper_child_dataset_root":
        first["dataset_root"] = _flip_hex(first["dataset_root"])
    elif name == "tamper_child_config_hash":
        first["config_hash"] = _flip_hex(first["config_hash"])
    elif name in {
        "tamper_valid_child_proof_wrong_position",
        "tamper_groth16_valid_child_proof_wrong_position",
        "tamper_plonk_valid_child_proof_wrong_position",
    }:
        proofs = mutated["private_witness"]["child_proofs"]
        proofs[0]["chunk_id"], proofs[1]["chunk_id"] = proofs[1]["chunk_id"], proofs[0]["chunk_id"]
    elif name in {
        "tamper_individually_valid_child_proofs_broken_chain",
        "tamper_groth16_individually_valid_child_proofs_broken_chain",
        "tamper_plonk_individually_valid_child_proofs_broken_chain",
    }:
        chunks[1]["input_checkpoint_hash"] = _flip_hex(chunks[1]["input_checkpoint_hash"])
    elif name == "tamper_binary_native_left_child_proof_bytes":
        mutated["private_witness"]["child_proofs"][0]["proof_bytes"] = _flip_hex(
            mutated["private_witness"]["child_proofs"][0]["proof_bytes"]
        )
    elif name == "tamper_binary_native_right_child_proof_bytes":
        mutated["private_witness"]["child_proofs"][1]["proof_bytes"] = _flip_hex(
            mutated["private_witness"]["child_proofs"][1]["proof_bytes"]
        )
    elif name == "tamper_binary_native_left_public_values":
        mutated["private_witness"]["child_proofs"][0]["public_values_bytes"] = _flip_hex(
            mutated["private_witness"]["child_proofs"][0]["public_values_bytes"]
        )
    elif name == "tamper_binary_native_right_public_values":
        mutated["private_witness"]["child_proofs"][1]["public_values_bytes"] = _flip_hex(
            mutated["private_witness"]["child_proofs"][1]["public_values_bytes"]
        )
    elif name == "tamper_binary_native_left_vkey_hash":
        mutated["private_witness"]["child_proofs"][0]["vkey_hash"] = _flip_vkey(
            mutated["private_witness"]["child_proofs"][0]["vkey_hash"]
        )
    elif name == "tamper_binary_native_right_vkey_hash":
        mutated["private_witness"]["child_proofs"][1]["vkey_hash"] = _flip_vkey(
            mutated["private_witness"]["child_proofs"][1]["vkey_hash"]
        )
    elif name in {"tamper_binary_native_swap_left_right", "tamper_binary_native_t32_level1_manifests_swapped"}:
        proofs = mutated["private_witness"]["child_proofs"]
        chunks[0], chunks[1] = chunks[1], chunks[0]
        proofs[0], proofs[1] = proofs[1], proofs[0]
    elif name == "tamper_binary_native_broken_checkpoint_link":
        chunks[1]["input_checkpoint_hash"] = _flip_hex(chunks[1]["input_checkpoint_hash"])
    elif name == "tamper_binary_native_broken_target_checkpoint_link":
        chunks[1]["input_target_checkpoint_hash"] = _flip_hex(
            chunks[1]["input_target_checkpoint_hash"]
        )
    elif name == "tamper_binary_native_duplicate_child":
        chunks[1] = copy.deepcopy(chunks[0])
        mutated["private_witness"]["child_proofs"][1] = copy.deepcopy(
            mutated["private_witness"]["child_proofs"][0]
        )
    elif name == "tamper_binary_native_missing_child":
        chunks.pop()
        mutated["private_witness"]["child_proofs"].pop()
    elif name == "tamper_binary_native_wrong_dataset_root":
        chunks[0]["dataset_root"] = _flip_hex(chunks[0]["dataset_root"])
    elif name == "tamper_binary_native_wrong_config_hash":
        chunks[0]["config_hash"] = _flip_hex(chunks[0]["config_hash"])
    elif name == "tamper_binary_native_wrong_node_range":
        public["node_range_end"] -= 1
    elif name == "tamper_binary_native_wrong_child_relation_id":
        chunks[0]["relation_id"] = "training_fragment_k4"
    elif name == "tamper_binary_native_t32_root_uses_leaf_instead_of_level1":
        chunks[0]["relation_id"] = "training_fragment_k8"
    else:
        raise ValueError(f"unknown tamper case: {name}")
    return mutated


def _flip_hex(value: str) -> str:
    replacement = "0" if value[0] != "0" else "1"
    return replacement + value[1:]


def _flip_vkey(value: str) -> str:
    return "0x" + _flip_hex(value[2:])
