from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zk_offline_dqn.backends.sp1.training_fragment import (  # noqa: E402
    BACKEND_DIR,
    cargo_command,
    case_path_for_k,
    load_case,
    tampered_case,
    verify_case_reference,
    write_generated_case,
)
from zk_offline_dqn.relations.training_fragment import recompute_fragment  # noqa: E402


TAMPER_CASES = [
    "tamper_sampler_seed",
    "tamper_minibatch_index",
    "tamper_step_order",
    "tamper_dataset_root",
    "tamper_manifest_hash",
    "tamper_audit_report_hash",
    "tamper_collection_log_hash",
    "tamper_leaf_hash",
    "tamper_merkle_path",
    "tamper_leaf_index",
    "tamper_state_at_step",
    "tamper_action_at_step",
    "tamper_reward_at_step",
    "tamper_next_state_at_step",
    "tamper_terminated_at_step",
    "tamper_truncated_at_step",
    "tamper_online_weight_before_step",
    "tamper_target_weight_before_step",
    "tamper_online_weight_after_step",
    "tamper_target_weight_after_step",
    "tamper_checkpoint_hash_before_step",
    "tamper_checkpoint_hash_after_step",
    "tamper_final_checkpoint_hash",
    "tamper_q_online_action",
    "tamper_q_target_next",
    "tamper_td_target",
    "tamper_td_error",
    "tamper_loss",
    "tamper_gradient",
    "tamper_learning_rate",
    "tamper_gamma",
    "tamper_update_hash",
    "tamper_trace_hash",
    "tamper_target_sync_interval",
    "tamper_target_sync_event",
]

CORE_RUST_TAMPER_CASES = [
    "tamper_sampler_seed",
    "tamper_minibatch_index",
    "tamper_leaf_hash",
    "tamper_state_at_step",
    "tamper_online_weight_before_step",
    "tamper_online_weight_after_step",
    "tamper_checkpoint_hash_after_step",
    "tamper_target_sync_event",
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(
    command: List[str], *, cwd: Path = BACKEND_DIR, env: Dict[str, str] | None = None
) -> Dict[str, Any]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    result = subprocess.run(command, cwd=cwd, env=run_env, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "passed": result.returncode == 0,
        "return_code": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-40:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-40:]),
    }


def run_tamper_checks(case_path: Path, out_dir: Path, run_execute: bool) -> Dict[str, Any]:
    case = load_case(case_path)
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in TAMPER_CASES:
            mutated = tampered_case(case, name)
            reference = verify_case_reference(mutated)
            execute = None
            if run_execute and name in CORE_RUST_TAMPER_CASES:
                path = tmp_path / f"{name}.json"
                write_json(path, mutated)
                execute = run_command(cargo_command(case_path=path, mode="execute"))
            passed = not reference.accepted
            if execute is not None:
                passed = passed and not execute["passed"]
            checks.append(
                {
                    "case": name,
                    "passed": passed,
                    "reference_accepted": reference.accepted,
                    "reference_reason": reference.reason,
                    "execute_passed": None if execute is None else execute["passed"],
                    "execute_return_code": None if execute is None else execute["return_code"],
                }
            )
    report = {
        "relation": "training_fragment",
        "num_steps": case["public_inputs"]["num_steps"],
        "batch_size": 1,
        "all_passed": all(item["passed"] for item in checks),
        "checks": checks,
    }
    write_json(out_dir / "tamper_report.json", report)
    return report


def validate_case(case_path: Path, out_root: Path, run_execute: bool, run_prove: bool) -> Dict[str, Any]:
    case = load_case(case_path)
    k = int(case["public_inputs"]["num_steps"])
    out_dir = out_root / f"training_fragment_k{k}"
    out_dir.mkdir(parents=True, exist_ok=True)
    reference = verify_case_reference(case)
    computed = recompute_fragment(case) if reference.accepted else {}
    execute = None
    if run_execute or run_prove:
        execute = run_command(cargo_command(case_path=case_path, mode="execute", max_steps=k))
    proof = None
    should_prove = run_prove or os.environ.get("RUN_SP1_PROVE") == "1"
    if should_prove:
        proof = run_command(
            cargo_command(case_path=case_path, mode="prove", out_dir=out_dir, max_steps=k),
            env={"RUN_SP1_PROVE": "1"},
        )
        proof_path = out_dir / "proof.bin"
        if proof_path.exists():
            proof_path.unlink()
    tamper = run_tamper_checks(case_path, out_dir, run_execute=bool(execute and execute["passed"]))
    proof_backed = bool(proof and proof["passed"] and tamper["all_passed"])
    required_files = [
        "public_inputs.json",
        "witness_schema.json",
        "metrics.json",
        "verify_report.json",
        "tamper_report.json",
        "proof_artifact_policy.json",
    ]
    status = {
        "relation": "training_fragment",
        "num_steps": k,
        "batch_size": 1,
        "reference_passed": reference.accepted,
        "execute_passed": bool(execute and execute["passed"]),
        "proof_generated": bool(proof and proof["passed"] and (out_dir / "metrics.json").exists()),
        "proof_verified": bool(proof and proof["passed"]),
        "public_inputs_saved": (out_dir / "public_inputs.json").exists(),
        "witness_schema_saved": (out_dir / "witness_schema.json").exists(),
        "metrics_saved": (out_dir / "metrics.json").exists(),
        "verify_report_saved": (out_dir / "verify_report.json").exists(),
        "tamper_report_saved": (out_dir / "tamper_report.json").exists(),
        "proof_artifact_policy_saved": (out_dir / "proof_artifact_policy.json").exists(),
        "tamper_test_passed": bool(tamper["all_passed"]),
        "target_sync_events": computed.get("target_sync_events"),
        "claim_status": "sp1_proof_backed"
        if proof_backed and all((out_dir / name).exists() for name in required_files)
        else "not_proof_backed",
        "execute": execute,
        "proof": proof,
    }
    write_json(out_dir / f"training_fragment_k{k}_status.json", status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="*", default=[])
    parser.add_argument("--generate-case-k", action="append", type=int, default=[])
    parser.add_argument("--out-root", default="artifacts/reports/provenance/sp1")
    parser.add_argument("--run-execute", action="store_true")
    parser.add_argument("--run-prove", action="store_true")
    args = parser.parse_args()

    case_paths = []
    for k in args.generate_case_k:
        case_paths.append(write_generated_case(k))
    for case in args.cases:
        path = Path(case)
        if not path.is_absolute():
            path = ROOT / path
        case_paths.append(path)
    if not case_paths:
        for k in [1, 4, 8]:
            case_paths.append(case_path_for_k(k))

    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    statuses = [
        validate_case(path, out_root, run_execute=args.run_execute, run_prove=args.run_prove)
        for path in case_paths
    ]
    summary = {"relation": "training_fragment", "cases": statuses}
    write_json(out_root / "phase6_training_fragment_status.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    should_prove = args.run_prove or os.environ.get("RUN_SP1_PROVE") == "1"
    ok = all(item["reference_passed"] and item["tamper_test_passed"] for item in statuses)
    if should_prove:
        ok = ok and all(item["proof_verified"] for item in statuses)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
