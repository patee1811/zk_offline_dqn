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

from zk_offline_dqn.backends.sp1.one_step_sgd_tiny import BACKEND_DIR, DEFAULT_CASE_PATH, cargo_command, load_case, tampered_case, verify_case_reference

TAMPER_CASES = ["tamper_gradient", "tamper_learning_rate_public", "tamper_old_weight", "tamper_new_weight", "tamper_old_checkpoint_hash_public", "tamper_new_checkpoint_hash_public", "tamper_update_hash_public"]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(command: List[str], *, cwd: Path = BACKEND_DIR, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    result = subprocess.run(command, cwd=cwd, env=run_env, capture_output=True, text=True)
    return {"command": " ".join(command), "passed": result.returncode == 0, "return_code": result.returncode, "stdout_tail": "\n".join(result.stdout.splitlines()[-40:]), "stderr_tail": "\n".join(result.stderr.splitlines()[-40:])}


def run_tamper_checks(out_dir: Path) -> Dict[str, Any]:
    case = load_case(DEFAULT_CASE_PATH)
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name in TAMPER_CASES:
            mutated = tampered_case(case, name)
            reference = verify_case_reference(mutated)
            path = tmp_path / f"{name}.json"
            write_json(path, mutated)
            execute = run_command(cargo_command(case_path=path, mode="execute"))
            passed = (not reference.accepted) and (not execute["passed"])
            checks.append({"case": name, "passed": passed, "reference_accepted": reference.accepted, "reference_reason": reference.reason, "execute_passed": execute["passed"], "execute_return_code": execute["return_code"]})
    report = {"relation": "one_step_sgd_tiny", "all_passed": all(item["passed"] for item in checks), "checks": checks}
    write_json(out_dir / "tamper_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default=str(DEFAULT_CASE_PATH))
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--prove", action="store_true")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    case = load_case(args.case)
    reference = verify_case_reference(case)
    execute = run_command(cargo_command(case_path=args.case, mode="execute"))
    proof = None
    if args.prove or os.environ.get("RUN_SP1_PROVE") == "1":
        proof = run_command(cargo_command(case_path=args.case, mode="prove", out_dir=out_dir), env={"RUN_SP1_PROVE": "1"})
    tamper = run_tamper_checks(out_dir)
    status = {"relation": "one_step_sgd_tiny", "reference_passed": reference.accepted, "execute_passed": execute["passed"], "proof_generated": bool(proof and proof["passed"] and (out_dir / "proof.bin").exists()), "proof_verified": bool(proof and proof["passed"]), "public_inputs_saved": (out_dir / "public_inputs.json").exists(), "witness_schema_saved": (out_dir / "witness_schema.json").exists(), "metrics_saved": (out_dir / "metrics.json").exists(), "verify_report_saved": (out_dir / "verify_report.json").exists(), "tamper_test_passed": bool(tamper["all_passed"]), "claim_status": "sp1_proof_backed" if proof and proof["passed"] and tamper["all_passed"] else "python_semantic_oracle_only", "execute": execute, "proof": proof}
    write_json(out_dir / "phase4_one_step_sgd_tiny_status.json", status)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["reference_passed"] and status["execute_passed"] and status["tamper_test_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

