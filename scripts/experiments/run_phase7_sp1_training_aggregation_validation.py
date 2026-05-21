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

from zk_offline_dqn.backends.sp1.training_aggregation import (  # noqa: E402
    BACKEND_DIR,
    cargo_command,
    case_path_for_target,
    load_case,
    tampered_case,
    verify_case_reference,
    write_generated_case,
)
from zk_offline_dqn.relations.training_aggregation import recompute_roots  # noqa: E402


TAMPER_CASES = [
    "tamper_step_start",
    "tamper_step_end",
    "tamper_chunk_order",
    "tamper_missing_chunk",
    "tamper_duplicate_chunk",
    "tamper_input_checkpoint_hash",
    "tamper_output_checkpoint_hash",
    "tamper_intermediate_checkpoint_link",
    "tamper_target_checkpoint_link",
    "tamper_dataset_root",
    "tamper_manifest_hash",
    "tamper_audit_report_hash",
    "tamper_collection_log_hash",
    "tamper_raw_trajectory_hash",
    "tamper_config_hash",
    "tamper_relation_id",
    "tamper_chunk_size",
    "tamper_chunk_count",
    "tamper_public_inputs_hash",
    "tamper_proof_hash",
    "tamper_verify_report_hash",
    "tamper_tamper_report_hash",
    "tamper_aggregate_root",
    "tamper_chunk_public_inputs_root",
    "tamper_chunk_proof_root",
]

CORE_RUST_TAMPER_CASES = [
    "tamper_chunk_order",
    "tamper_intermediate_checkpoint_link",
    "tamper_target_checkpoint_link",
    "tamper_dataset_root",
    "tamper_relation_id",
    "tamper_public_inputs_hash",
    "tamper_proof_hash",
    "tamper_aggregate_root",
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
        "relation": "training_aggregation",
        "aggregation_mode": case["public_inputs"]["aggregation_mode"],
        "chunk_size": case["public_inputs"]["chunk_size"],
        "chunk_count": case["public_inputs"]["chunk_count"],
        "step_end": case["public_inputs"]["step_end"],
        "all_passed": all(item["passed"] for item in checks),
        "checks": checks,
    }
    write_json(out_dir / "tamper_report.json", report)
    return report


def validate_case(
    case_path: Path,
    out_root: Path,
    aggregation_mode: str,
    run_execute: bool,
    run_prove: bool,
) -> Dict[str, Any]:
    case = load_case(case_path)
    public = case["public_inputs"]
    target = int(public["step_end"])
    out_dir = out_root / f"training_aggregation_t{target}"
    out_dir.mkdir(parents=True, exist_ok=True)
    reference = verify_case_reference(case)
    roots = recompute_roots(case["private_witness"]["chunks"]) if reference.accepted else {}
    execute = None
    if run_execute or run_prove:
        execute = run_command(
            cargo_command(
                case_path=case_path,
                mode="execute",
                aggregation_mode=aggregation_mode,
            )
        )
    proof = None
    should_prove = run_prove or os.environ.get("RUN_SP1_PROVE") == "1"
    if should_prove:
        proof = run_command(
            cargo_command(
                case_path=case_path,
                mode="prove",
                aggregation_mode=aggregation_mode,
                out_dir=out_dir,
            ),
            env={"RUN_SP1_PROVE": "1"},
        )
        proof_path = out_dir / "proof.bin"
        if proof_path.exists():
            proof_path.unlink()
    tamper = run_tamper_checks(case_path, out_dir, run_execute=bool(execute and execute["passed"]))
    required_files = [
        "public_inputs.json",
        "witness_schema.json",
        "metrics.json",
        "verify_report.json",
        "tamper_report.json",
        "proof_artifact_policy.json",
        "aggregation_manifest.json",
        "chunk_manifest.json",
    ]
    proof_backed = bool(proof and proof["passed"] and tamper["all_passed"])
    status = {
        "relation": "training_aggregation",
        "aggregation_mode": public["aggregation_mode"],
        "chunk_size": public["chunk_size"],
        "chunk_count": public["chunk_count"],
        "step_start": public["step_start"],
        "step_end": public["step_end"],
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
        "aggregation_manifest_saved": (out_dir / "aggregation_manifest.json").exists(),
        "chunk_manifest_saved": (out_dir / "chunk_manifest.json").exists(),
        "tamper_test_passed": bool(tamper["all_passed"]),
        "child_proof_verification_inside_guest": False,
        "roots_match_reference": bool(
            roots and all(public[key] == value for key, value in roots.items())
        ),
        "claim_status": "sp1_proof_backed_manifest_chain_not_true_recursion"
        if proof_backed and all((out_dir / name).exists() for name in required_files)
        else "not_proof_backed",
        "execute": execute,
        "proof": proof,
    }
    write_json(out_dir / f"training_aggregation_t{target}_status.json", status)
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", type=int, default=[32, 64, 128])
    parser.add_argument("--chunk-size", type=int, default=8)
    parser.add_argument("--aggregation-mode", default="proof_manifest_chain")
    parser.add_argument("--out-root", default="artifacts/reports/provenance/sp1")
    parser.add_argument("--run-reference", action="store_true")
    parser.add_argument("--run-execute", action="store_true")
    parser.add_argument("--run-prove", action="store_true")
    args = parser.parse_args()
    if args.chunk_size != 8:
        raise SystemExit("Phase 7 requires --chunk-size 8")
    if args.aggregation_mode != "proof_manifest_chain":
        raise SystemExit("recursive_sp1 is not implemented; use --aggregation-mode proof_manifest_chain")
    case_paths = [write_generated_case(target) for target in args.targets]
    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    statuses = [
        validate_case(
            path,
            out_root,
            aggregation_mode=args.aggregation_mode,
            run_execute=args.run_execute,
            run_prove=args.run_prove,
        )
        for path in case_paths
    ]
    summary = {"relation": "training_aggregation", "cases": statuses}
    write_json(out_root / "phase7_training_aggregation_status.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    should_prove = args.run_prove or os.environ.get("RUN_SP1_PROVE") == "1"
    ok = all(item["reference_passed"] and item["tamper_test_passed"] for item in statuses)
    if should_prove:
        ok = ok and all(item["proof_verified"] for item in statuses)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
