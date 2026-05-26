"""Helpers for the SP1 Merkle membership backend."""

from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from zk_offline_dqn.core.merkle import recompute_root_from_path
from zk_offline_dqn.data_pipeline import canonical_json_bytes, sha256_hex_bytes


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "merkle_membership" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "merkle_membership_case_0.json"


@dataclass(frozen=True)
class MerkleMembershipReferenceResult:
    accepted: bool
    reason: Optional[str]
    recomputed_root: str
    recomputed_leaf_hash: Optional[str]


def load_case(path: str | Path = DEFAULT_CASE_PATH) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Merkle membership case must be a JSON object")
    return data


def canonical_transition_hash(case: Mapping[str, Any]) -> Optional[str]:
    transition = case.get("private_witness", {}).get("transition")
    if transition is None:
        return None
    return sha256_hex_bytes(canonical_json_bytes(transition))


def verify_case_reference(case: Mapping[str, Any]) -> MerkleMembershipReferenceResult:
    public = case["public_inputs"]
    witness = case["private_witness"]
    leaf_hash = public["leaf_hash"]
    computed_leaf_hash = canonical_transition_hash(case)
    if computed_leaf_hash is not None and computed_leaf_hash != leaf_hash:
        return MerkleMembershipReferenceResult(
            accepted=False,
            reason="canonical_transition_hash_mismatch",
            recomputed_root="",
            recomputed_leaf_hash=computed_leaf_hash,
        )

    path = witness["merkle_path"]
    leaf_index = int(public["leaf_index"])
    expected_index = leaf_index
    for expected_level, step in enumerate(path):
        if int(step["level"]) != expected_level:
            return _reject("path_level_mismatch", leaf_hash, path, computed_leaf_hash)
        if int(step["current_index"]) != expected_index:
            return _reject("path_current_index_mismatch", leaf_hash, path, computed_leaf_hash)
        is_left = bool(step["current_is_left"])
        sibling_index = int(step["sibling_index"])
        if is_left:
            if expected_index % 2 != 0:
                return _reject("left_step_odd_index", leaf_hash, path, computed_leaf_hash)
            if sibling_index not in {expected_index, expected_index + 1}:
                return _reject("left_step_sibling_index_mismatch", leaf_hash, path, computed_leaf_hash)
        else:
            if expected_index % 2 != 1:
                return _reject("right_step_even_index", leaf_hash, path, computed_leaf_hash)
            if sibling_index != expected_index - 1:
                return _reject("right_step_sibling_index_mismatch", leaf_hash, path, computed_leaf_hash)
        expected_index //= 2

    recomputed_root = recompute_root_from_path(leaf_hash, path)
    accepted = recomputed_root == public["dataset_root"]
    return MerkleMembershipReferenceResult(
        accepted=accepted,
        reason=None if accepted else "dataset_root_mismatch",
        recomputed_root=recomputed_root,
        recomputed_leaf_hash=computed_leaf_hash,
    )


def _reject(
    reason: str,
    leaf_hash: str,
    path: list[Mapping[str, Any]],
    computed_leaf_hash: Optional[str],
) -> MerkleMembershipReferenceResult:
    try:
        root = recompute_root_from_path(leaf_hash, path)
    except Exception:
        root = ""
    return MerkleMembershipReferenceResult(
        accepted=False,
        reason=reason,
        recomputed_root=root,
        recomputed_leaf_hash=computed_leaf_hash,
    )


def tampered_case(case: Mapping[str, Any], tamper: str) -> Dict[str, Any]:
    out = deepcopy(dict(case))
    public = out["public_inputs"]
    witness = out["private_witness"]
    if tamper == "tamper_leaf_hash":
        public["leaf_hash"] = "00" * 32
    elif tamper == "tamper_dataset_root":
        public["dataset_root"] = "11" * 32
    elif tamper == "tamper_path_sibling":
        witness["merkle_path"][0]["sibling_hash"] = "22" * 32
    elif tamper == "tamper_leaf_index":
        public["leaf_index"] = int(public["leaf_index"]) + 1
    elif tamper == "tamper_manifest_hash_public_input":
        public["manifest_hash"] = "33" * 32
    elif tamper == "tamper_audit_report_hash_public_input":
        public["audit_report_hash"] = "44" * 32
    elif tamper == "tamper_collection_log_hash_public_input":
        public["collection_log_final_hash"] = "55" * 32
    else:
        raise ValueError(f"unknown tamper case: {tamper}")
    return out


def cargo_command(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    out_dir: str | Path | None = None,
    expected_public_inputs: str | Path | None = None,
    cargo: str = "cargo",
) -> list[str]:
    if mode not in {"execute", "prove"}:
        raise ValueError(f"unsupported mode: {mode}")
    resolved_case_path = Path(case_path)
    if not resolved_case_path.is_absolute():
        resolved_case_path = (ROOT / resolved_case_path).resolve()
    command = [
        cargo,
        "run",
        "--release",
        "-p",
        "merkle-membership-host",
        "--",
        f"--{mode}",
        "--case",
        str(resolved_case_path),
    ]
    if out_dir is not None:
        command.extend(["--out-dir", str(out_dir)])
    if expected_public_inputs is not None:
        command.extend(["--expected-public-inputs", str(expected_public_inputs)])
    return command


def run_cargo(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    out_dir: str | Path | None = None,
    expected_public_inputs: str | Path | None = None,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cargo_command(
            case_path=case_path,
            mode=mode,
            out_dir=out_dir,
            expected_public_inputs=expected_public_inputs,
        ),
        cwd=BACKEND_DIR,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
