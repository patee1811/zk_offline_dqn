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

from zk_offline_dqn.backends.sp1.training_update import (  # noqa: E402
    BACKEND_DIR,
    DEFAULT_CASE_PATH,
    cargo_command,
    load_case,
    tampered_case,
    verify_case_reference,
)


TAMPER_CASES = [
    "tamper_dataset_root",
    "tamper_manifest_hash",
    "tamper_audit_report_hash",
    "tamper_collection_log_hash",
    "tamper_leaf_hash",
    "tamper_merkle_path",
    "tamper_leaf_index",
    "tamper_state",
    "tamper_action",
    "tamper_reward",
    "tamper_next_state",
    "tamper_terminated",
    "tamper_truncated",
    "tamper_online_weight",
    "tamper_target_weight",
    "tamper_checkpoint_hash_t",
    "tamper_target_checkpoint_hash",
    "tamper_checkpoint_hash_t_plus_1",
    "tamper_q_online_action",
    "tamper_q_target_next",
    "tamper_td_target",
    "tamper_td_error",
    "tamper_loss",
    "tamper_gradient",
    "tamper_learning_rate",
    "tamper_gamma",
    "tamper_update_hash",
]


CORE_RUST_TAMPER_CASES = [
    "tamper_leaf_hash",
    "tamper_state",
    "tamper_online_weight",
    "tamper_checkpoint_hash_t_plus_1",
    "tamper_gradient",
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


def run_tamper_checks(out_dir: Path, run_execute: bool) -> Dict[str, Any]:
    case = load_case(DEFAULT_CASE_PATH)
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
        "relation": "training_update",
        "batch_size": 1,
        "all_passed": all(item["passed"] for item in checks),
        "checks": checks,
    }
    write_json(out_dir / "tamper_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default=str(DEFAULT_CASE_PATH))
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--run-execute", action="store_true")
    parser.add_argument("--run-prove", action="store_true")
    parser.add_argument("--prove", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    case = load_case(args.case)
    reference = verify_case_reference(case)
    execute = None
    if args.run_execute or args.run_prove or args.prove:
        execute = run_command(cargo_command(case_path=args.case, mode="execute"))
    proof = None
    should_prove = args.run_prove or args.prove or os.environ.get("RUN_SP1_PROVE") == "1"
    if should_prove:
        proof = run_command(
            cargo_command(case_path=args.case, mode="prove", out_dir=out_dir),
            env={"RUN_SP1_PROVE": "1"},
        )
        proof_path = out_dir / "proof.bin"
        if proof_path.exists():
            proof_path.unlink()
    tamper = run_tamper_checks(out_dir, run_execute=bool(execute and execute["passed"]))
    status = {
        "relation": "training_update",
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
        "tamper_test_passed": bool(tamper["all_passed"]),
        "claim_status": "sp1_proof_backed"
        if proof and proof["passed"] and tamper["all_passed"]
        else "not_proof_backed",
        "execute": execute,
        "proof": proof,
    }
    write_json(out_dir / "phase5_training_update_status.json", status)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["reference_passed"] and status["tamper_test_passed"] and (not should_prove or status["proof_verified"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
