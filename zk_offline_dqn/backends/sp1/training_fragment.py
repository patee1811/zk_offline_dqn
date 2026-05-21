"""Python helpers for the Phase 6 SP1 training-fragment backend."""

from __future__ import annotations

import copy
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from zk_offline_dqn.relations.training_fragment import VerificationResult, generate_case, verify_case


ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT / "zk_backend" / "training_fragment" / "sp1"
DEFAULT_CASE_PATH = ROOT / "zk_backend" / "test_vectors" / "training_fragment_k4_case_0.json"


def case_path_for_k(k: int) -> Path:
    return ROOT / "zk_backend" / "test_vectors" / f"training_fragment_k{k}_case_0.json"


def load_case(path: str | Path = DEFAULT_CASE_PATH) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_generated_case(k: int, path: str | Path | None = None) -> Path:
    out_path = Path(path) if path is not None else case_path_for_k(k)
    case = generate_case(k)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(case, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return out_path


def verify_case_reference(case: Dict[str, Any]) -> VerificationResult:
    return verify_case(case)


def cargo_command(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    out_dir: str | Path | None = None,
    max_steps: int | None = None,
) -> List[str]:
    command = [
        "cargo",
        "run",
        "--release",
        "-p",
        "training-fragment-host",
        "--",
        f"--{mode}",
        "--case",
        str(case_path),
    ]
    if out_dir is not None:
        command.extend(["--out-dir", str(out_dir)])
    if max_steps is not None:
        command.extend(["--max-steps", str(max_steps)])
    return command


def run_cargo(
    *,
    case_path: str | Path = DEFAULT_CASE_PATH,
    mode: str = "execute",
    out_dir: str | Path | None = None,
    max_steps: int | None = None,
    timeout: int = 1200,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if mode == "prove":
        env["RUN_SP1_PROVE"] = "1"
    return subprocess.run(
        cargo_command(case_path=case_path, mode=mode, out_dir=out_dir, max_steps=max_steps),
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def tampered_case(case: Dict[str, Any], name: str) -> Dict[str, Any]:
    mutated = copy.deepcopy(case)
    public = mutated["public_inputs"]
    steps = mutated["private_witness"]["steps"]
    step = steps[0]
    if name == "tamper_sampler_seed":
        public["sampler_seed"] += 1
    elif name == "tamper_minibatch_index":
        step["sample_index"] += 1
    elif name == "tamper_step_order":
        if len(steps) > 1:
            steps[0], steps[1] = steps[1], steps[0]
        else:
            step["step_id"] += 1
    elif name == "tamper_dataset_root":
        public["dataset_root"] = _flip_hex(public["dataset_root"])
    elif name == "tamper_manifest_hash":
        public["manifest_hash"] = _flip_hex(public["manifest_hash"])
    elif name == "tamper_audit_report_hash":
        public["audit_report_hash"] = _flip_hex(public["audit_report_hash"])
    elif name == "tamper_collection_log_hash":
        public["collection_log_final_hash"] = _flip_hex(public["collection_log_final_hash"])
    elif name == "tamper_leaf_hash":
        step["leaf_hash"] = _flip_hex(step["leaf_hash"])
    elif name == "tamper_merkle_path":
        step["merkle_path"][0]["sibling_hash"] = "00" * 32
    elif name == "tamper_leaf_index":
        step["leaf_index"] += 1
    elif name == "tamper_state_at_step":
        step["transition"]["state"][0] += 1
    elif name == "tamper_action_at_step":
        step["transition"]["action"] = 1 - int(step["transition"]["action"])
    elif name == "tamper_reward_at_step":
        step["transition"]["reward"] += 1
    elif name == "tamper_next_state_at_step":
        step["transition"]["next_state"][0] += 1
    elif name == "tamper_terminated_at_step":
        step["transition"]["terminated"] = not bool(step["transition"]["terminated"])
    elif name == "tamper_truncated_at_step":
        step["transition"]["truncated"] = not bool(step["transition"]["truncated"])
    elif name == "tamper_online_weight_before_step":
        step["online_model_before"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_target_weight_before_step":
        step["target_model_before"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_online_weight_after_step":
        step["online_model_after"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_target_weight_after_step":
        step["target_model_after"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_checkpoint_hash_before_step":
        step["checkpoint_hash_before"] = _flip_hex(step["checkpoint_hash_before"])
    elif name == "tamper_checkpoint_hash_after_step":
        step["checkpoint_hash_after"] = _flip_hex(step["checkpoint_hash_after"])
    elif name == "tamper_final_checkpoint_hash":
        public["final_checkpoint_hash"] = _flip_hex(public["final_checkpoint_hash"])
    elif name == "tamper_q_online_action":
        step["intermediates"]["q_online_action"] += 1
    elif name == "tamper_q_target_next":
        step["intermediates"]["q_target_next"] += 1
    elif name == "tamper_td_target":
        step["intermediates"]["td_target"] += 1
    elif name == "tamper_td_error":
        step["intermediates"]["td_error"] += 1
    elif name == "tamper_loss":
        step["intermediates"]["loss"] += 1
    elif name == "tamper_gradient":
        step["intermediates"]["gradients"]["layers"][0]["weight"][0][0] += 1
    elif name == "tamper_learning_rate":
        public["learning_rate"] += 1
    elif name == "tamper_gamma":
        public["gamma"] += 100
    elif name == "tamper_update_hash":
        step["intermediates"]["update_hash"] = _flip_hex(step["intermediates"]["update_hash"])
    elif name == "tamper_trace_hash":
        public["trace_hash"] = _flip_hex(public["trace_hash"])
    elif name == "tamper_target_sync_interval":
        public["target_sync_interval"] = 1 if int(public["target_sync_interval"]) != 1 else 2
    elif name == "tamper_target_sync_event":
        sync_step = next((item for item in steps if item["intermediates"]["target_sync_applied"]), steps[-1])
        sync_step["intermediates"]["target_sync_applied"] = not bool(sync_step["intermediates"]["target_sync_applied"])
    else:
        raise ValueError(f"unknown tamper case: {name}")
    return mutated


def _flip_hex(value: str) -> str:
    if not value:
        return "00" * 32
    replacement = "0" if value[0] != "0" else "1"
    return replacement + value[1:]
