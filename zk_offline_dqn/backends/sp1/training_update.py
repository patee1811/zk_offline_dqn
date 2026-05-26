"""Python helpers for the Phase 5 SP1 training-update backend."""

from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from zk_offline_dqn.relations.training_update import VerificationResult, verify_case


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "training_update" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "training_update_case_0.json"


def load_case(path: str | Path = DEFAULT_CASE_PATH) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_case_reference(case: Dict[str, Any]) -> VerificationResult:
    return verify_case(case)


def cargo_command(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    out_dir: str | Path | None = None,
) -> List[str]:
    command = [
        "cargo",
        "run",
        "--release",
        "-p",
        "training-update-host",
        "--",
        f"--{mode}",
        "--case",
        str(case_path),
    ]
    if out_dir is not None:
        command.extend(["--out-dir", str(out_dir)])
    return command


def run_cargo(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    out_dir: str | Path | None = None,
    timeout: int = 1200,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if mode == "prove":
        env["RUN_SP1_PROVE"] = "1"
    return subprocess.run(
        cargo_command(case_path=case_path, mode=mode, out_dir=out_dir),
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def tampered_case(case: Dict[str, Any], name: str) -> Dict[str, Any]:
    mutated = copy.deepcopy(case)
    public = mutated["public_inputs"]
    witness = mutated["private_witness"]
    transition = witness["transition"]
    if name == "tamper_dataset_root":
        public["dataset_root"] = _flip_hex(public["dataset_root"])
    elif name == "tamper_manifest_hash":
        public["manifest_hash"] = _flip_hex(public["manifest_hash"])
    elif name == "tamper_audit_report_hash":
        public["audit_report_hash"] = _flip_hex(public["audit_report_hash"])
    elif name == "tamper_collection_log_hash":
        public["collection_log_final_hash"] = _flip_hex(public["collection_log_final_hash"])
    elif name == "tamper_leaf_hash":
        public["leaf_hash"] = _flip_hex(public["leaf_hash"])
    elif name == "tamper_merkle_path":
        witness["merkle_path"] = [
            {
                "level": 0,
                "current_index": int(public["leaf_index"]),
                "sibling_index": int(public["leaf_index"]),
                "sibling_hash": "00" * 32,
                "current_is_left": True,
            }
        ]
    elif name == "tamper_leaf_index":
        public["leaf_index"] = int(public["leaf_index"]) + 1
    elif name == "tamper_state":
        transition["state"][0] += 1
    elif name == "tamper_action":
        transition["action"] = 1 - int(transition["action"])
    elif name == "tamper_reward":
        transition["reward"] += 1
    elif name == "tamper_next_state":
        transition["next_state"][0] += 1
    elif name == "tamper_terminated":
        transition["terminated"] = not bool(transition["terminated"])
    elif name == "tamper_truncated":
        transition["truncated"] = not bool(transition["truncated"])
    elif name == "tamper_online_weight":
        witness["online_model_t"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_target_weight":
        witness["target_model"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_checkpoint_hash_t":
        public["checkpoint_hash_t"] = _flip_hex(public["checkpoint_hash_t"])
    elif name == "tamper_target_checkpoint_hash":
        public["target_checkpoint_hash"] = _flip_hex(public["target_checkpoint_hash"])
    elif name == "tamper_checkpoint_hash_t_plus_1":
        public["checkpoint_hash_t_plus_1"] = _flip_hex(public["checkpoint_hash_t_plus_1"])
    elif name == "tamper_q_online_action":
        public["claimed_q_online_action"] += 1
    elif name == "tamper_q_target_next":
        public["claimed_q_target_next"] += 1
    elif name == "tamper_td_target":
        public["claimed_td_target"] += 1
    elif name == "tamper_td_error":
        public["claimed_td_error"] += 1
    elif name == "tamper_loss":
        public["claimed_loss"] += 1
    elif name == "tamper_gradient":
        witness["intermediates"]["gradients"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_learning_rate":
        public["learning_rate"] += 1
    elif name == "tamper_gamma":
        public["gamma"] += 100
    elif name == "tamper_update_hash":
        public["claimed_update_hash"] = _flip_hex(public["claimed_update_hash"])
    else:
        raise ValueError(f"unknown tamper case: {name}")
    return mutated


def _flip_hex(value: str) -> str:
    if not value:
        return "00" * 32
    replacement = "0" if value[0] != "0" else "1"
    return replacement + value[1:]
