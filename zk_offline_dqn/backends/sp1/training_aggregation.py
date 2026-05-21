"""Python helpers for the Phase 7 SP1 training aggregation backend."""

from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from zk_offline_dqn.relations.training_aggregation import VerificationResult, generate_case, verify_case


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "training_aggregation" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "training_aggregation_t32_case_0.json"


def case_path_for_target(target: int) -> Path:
    return ROOT / "zk_backend" / "test_vectors" / f"training_aggregation_t{target}_case_0.json"


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


def verify_case_reference(case: Dict[str, Any]) -> VerificationResult:
    return verify_case(case)


def cargo_command(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    aggregation_mode: str = "proof_manifest_chain",
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
    return command


def run_cargo(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    aggregation_mode: str = "proof_manifest_chain",
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
    else:
        raise ValueError(f"unknown tamper case: {name}")
    return mutated


def _flip_hex(value: str) -> str:
    replacement = "0" if value[0] != "0" else "1"
    return replacement + value[1:]
