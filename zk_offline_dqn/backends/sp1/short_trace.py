"""Helpers for the SP1 short-trace checkpoint-chain backend."""

from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "short_trace" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "short_trace_case_0.json"


@dataclass(frozen=True)
class ReferenceResult:
    accepted: bool
    reason: Optional[str]


def load_case(path: str | Path = DEFAULT_CASE_PATH) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Short trace case must be a JSON object")
    return data


def verify_case_reference(case: Mapping[str, Any]) -> ReferenceResult:
    try:
        public = case["public_inputs"]
        config = case["config"]
        steps = case["private_witness"]["steps"]
        if public["relation"] != "short_trace":
            raise AssertionError("relation mismatch")
        if public["num_steps"] != len(steps):
            raise AssertionError("num_steps mismatch")
        previous = None
        for index, step in enumerate(steps):
            old_hash = checkpoint_hash(step["old_weights"])
            new_hash = checkpoint_hash(step["new_weights"])
            if old_hash != step["old_checkpoint_hash"]:
                raise AssertionError("old checkpoint hash mismatch")
            if new_hash != step["new_checkpoint_hash"]:
                raise AssertionError("new checkpoint hash mismatch")
            if index == 0 and old_hash != public["start_checkpoint_hash"]:
                raise AssertionError("start checkpoint mismatch")
            if index > 0 and step["old_checkpoint_hash"] != previous:
                raise AssertionError("checkpoint chain mismatch")
            for old, grad, new in zip(step["old_weights"], step["gradients"], step["new_weights"]):
                delta = -div_trunc_zero(int(config["learning_rate_fp"]) * int(grad), int(config["fixed_point_scale"]))
                if int(new) != int(old) + delta:
                    raise AssertionError("SGD update mismatch")
            previous = step["new_checkpoint_hash"]
        if previous != public["final_checkpoint_hash"]:
            raise AssertionError("final checkpoint mismatch")
        if trace_hash(steps, int(config["learning_rate_fp"]), int(config["fixed_point_scale"])) != public["trace_hash"]:
            raise AssertionError("trace hash mismatch")
        return ReferenceResult(True, None)
    except Exception as exc:
        return ReferenceResult(False, type(exc).__name__ + ": " + str(exc))


def checkpoint_hash(weights: list[int]) -> str:
    data = bytearray(b"checkpoint_v1")
    for value in weights:
        data.extend(int(value).to_bytes(8, "little", signed=True))
    return hashlib.sha256(data).hexdigest()


def trace_hash(steps: list[Mapping[str, Any]], learning_rate_fp: int, fp_scale: int) -> str:
    data = bytearray(b"short_trace_v1")
    data.extend(int(learning_rate_fp).to_bytes(8, "little", signed=True))
    data.extend(int(fp_scale).to_bytes(8, "little", signed=True))
    for step in steps:
        for key in ("old_weights", "gradients", "new_weights"):
            for value in step[key]:
                data.extend(int(value).to_bytes(8, "little", signed=True))
        data.extend(bytes.fromhex(step["old_checkpoint_hash"]))
        data.extend(bytes.fromhex(step["new_checkpoint_hash"]))
    return hashlib.sha256(data).hexdigest()


def div_trunc_zero(numerator: int, denominator: int) -> int:
    sign = -1 if numerator < 0 else 1
    return sign * (abs(numerator) // denominator)


def tampered_case(case: Mapping[str, Any], tamper: str) -> Dict[str, Any]:
    out = deepcopy(dict(case))
    public = out["public_inputs"]
    steps = out["private_witness"]["steps"]
    if tamper == "tamper_intermediate_checkpoint":
        steps[0]["new_checkpoint_hash"] = "00" * 32
    elif tamper == "tamper_step_order":
        steps[0], steps[1] = steps[1], steps[0]
    elif tamper == "tamper_gradient_inside_step":
        steps[0]["gradients"][0] += 1
    elif tamper == "tamper_new_weight_inside_step":
        steps[0]["new_weights"][0] += 1
    elif tamper == "tamper_start_checkpoint_hash_public":
        public["start_checkpoint_hash"] = "11" * 32
    elif tamper == "tamper_final_checkpoint_hash_public":
        public["final_checkpoint_hash"] = "22" * 32
    elif tamper == "tamper_trace_hash_public":
        public["trace_hash"] = "33" * 32
    elif tamper == "tamper_num_steps_public":
        public["num_steps"] += 1
    else:
        raise ValueError(f"unknown tamper case: {tamper}")
    return out


def cargo_command(*, case_path: str | Path = DEFAULT_CASE_PATH, mode: str = "execute", out_dir: str | Path | None = None, cargo: str = "cargo") -> list[str]:
    if mode not in {"execute", "prove"}:
        raise ValueError(f"unsupported mode: {mode}")
    resolved = Path(case_path)
    if not resolved.is_absolute():
        resolved = (ROOT / resolved).resolve()
    command = [cargo, "run", "--release", "-p", "short-trace-host", "--", f"--{mode}", "--case", str(resolved)]
    if out_dir is not None:
        command.extend(["--out-dir", str(out_dir)])
    return command


def run_cargo(*, case_path: str | Path = DEFAULT_CASE_PATH, mode: str = "execute", out_dir: str | Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cargo_command(case_path=case_path, mode=mode, out_dir=out_dir), cwd=BACKEND_DIR, text=True, capture_output=True, timeout=timeout)

