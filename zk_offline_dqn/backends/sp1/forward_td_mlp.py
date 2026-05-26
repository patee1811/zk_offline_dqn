"""Helpers for the SP1 Forward-TD MLP backend."""

from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from zk_offline_dqn.relations.forward_td_mlp import verify_vector


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "forward_td_mlp" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "forward_td_mlp_case_0.json"


@dataclass(frozen=True)
class ReferenceResult:
    accepted: bool
    reason: Optional[str]


def load_case(path: str | Path = DEFAULT_CASE_PATH) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Forward-TD MLP case must be a JSON object")
    return data


def verify_case_reference(case: Mapping[str, Any]) -> ReferenceResult:
    try:
        verify_vector(dict(case))
        return ReferenceResult(True, None)
    except Exception as exc:
        return ReferenceResult(False, type(exc).__name__ + ": " + str(exc))


def tampered_case(case: Mapping[str, Any], tamper: str) -> Dict[str, Any]:
    out = deepcopy(dict(case))
    public = out["public"]
    private = out["private"]
    item = private["items"][0]
    witness = item["forward_witness"]
    if tamper == "tamper_reward":
        item["transition"]["reward"] = float(item["transition"]["reward"]) + 1.0
    elif tamper == "tamper_action":
        item["transition"]["action"] = 1 - int(item["transition"]["action"])
    elif tamper == "tamper_done":
        item["transition"]["done"] = 1 - int(item["transition"]["done"])
    elif tamper == "tamper_state":
        item["transition"]["obs"][0] = float(item["transition"]["obs"][0]) + 0.25
    elif tamper == "tamper_next_state":
        item["transition"]["next_obs"][0] = float(item["transition"]["next_obs"][0]) + 0.25
    elif tamper == "tamper_online_weight":
        private["online_model"]["layers"][0]["weight"][0][0] += 1
    elif tamper == "tamper_target_weight":
        private["target_model"]["layers"][0]["weight"][0][0] += 1
    elif tamper == "tamper_q_online_public":
        witness["q_online_action_fp"] += 1
    elif tamper == "tamper_q_target_public":
        witness["q_target_max_fp"] += 1
    elif tamper == "tamper_td_target_public":
        witness["target_fp"] += 1
    elif tamper == "tamper_td_error_public":
        witness["td_error_fp"] += 1
    elif tamper == "tamper_loss_public":
        public["claimed_batch_loss_fp"] += 1
    elif tamper == "tamper_checkpoint_hash_public":
        public["online_model_commitment"] = "00" * 32
    elif tamper == "tamper_dataset_root_public":
        public["dataset_root"] = "11" * 32
    elif tamper == "tamper_manifest_hash_public":
        public["network_spec_hash"] = "22" * 32
    elif tamper == "tamper_audit_report_hash_public":
        public["target_model_commitment"] = "33" * 32
    else:
        raise ValueError(f"unknown tamper case: {tamper}")
    return out


def cargo_command(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    out_dir: str | Path | None = None,
    cargo: str = "cargo",
) -> list[str]:
    if mode not in {"execute", "prove"}:
        raise ValueError(f"unsupported mode: {mode}")
    resolved = Path(case_path)
    if not resolved.is_absolute():
        resolved = (ROOT / resolved).resolve()
    command = [cargo, "run", "--release", "-p", "forward-td-mlp-host", "--", f"--{mode}", "--case", str(resolved)]
    if out_dir is not None:
        command.extend(["--out-dir", str(out_dir)])
    return command


def run_cargo(*, case_path: str | Path = DEFAULT_CASE_PATH, mode: str = "execute", out_dir: str | Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cargo_command(case_path=case_path, mode=mode, out_dir=out_dir), cwd=BACKEND_DIR, text=True, capture_output=True, timeout=timeout)

