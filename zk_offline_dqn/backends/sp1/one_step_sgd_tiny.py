"""Helpers for the SP1 one-step SGD tiny backend."""

from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from zk_offline_dqn.relations.one_step_sgd_tiny import verify_vector


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "one_step_sgd_tiny" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "one_step_sgd_tiny_case_0.json"


@dataclass(frozen=True)
class ReferenceResult:
    accepted: bool
    reason: Optional[str]


def load_case(path: str | Path = DEFAULT_CASE_PATH) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("One-step SGD tiny case must be a JSON object")
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
    update = private["update_witness"]
    if tamper == "tamper_gradient":
        update["gradient_tensors"]["layers"][0]["weight"][0][0] += 1
    elif tamper == "tamper_learning_rate_public":
        public["learning_rate_fp"] += 1
    elif tamper == "tamper_old_weight":
        private["online_model"]["layers"][0]["weight"][0][0] += 1
    elif tamper == "tamper_new_weight":
        private["post_online_model"]["layers"][0]["weight"][0][0] += 1
    elif tamper == "tamper_old_checkpoint_hash_public":
        public["pre_model_commitment"] = "00" * 32
    elif tamper == "tamper_new_checkpoint_hash_public":
        public["post_model_commitment"] = "11" * 32
    elif tamper == "tamper_update_hash_public":
        update["delta_tensors"]["layers"][0]["weight"][0][0] += 1
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
    command = [cargo, "run", "--release", "-p", "one-step-sgd-tiny-host", "--", f"--{mode}", "--case", str(resolved)]
    if out_dir is not None:
        command.extend(["--out-dir", str(out_dir)])
    return command


def run_cargo(*, case_path: str | Path = DEFAULT_CASE_PATH, mode: str = "execute", out_dir: str | Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cargo_command(case_path=case_path, mode=mode, out_dir=out_dir), cwd=BACKEND_DIR, text=True, capture_output=True, timeout=timeout)

