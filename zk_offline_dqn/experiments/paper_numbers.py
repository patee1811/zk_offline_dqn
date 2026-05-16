"""Assemble paper-facing report numbers from existing generated sources."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[2]
REGRESSION_SUMMARY = ROOT / "artifacts/regression_summary.json"
FINAL_NDSS_SUMMARY = ROOT / "artifacts/benchmarks/final_ndss/summary.json"
SP1_PROVENANCE_DIR = ROOT / "artifacts/reports/provenance/sp1"
SP1_VALIDATION_SUMMARY = SP1_PROVENANCE_DIR / "kaggle_sp1_validation_summary.json"
SP1_SETUP_SUMMARY = SP1_PROVENANCE_DIR / "kaggle_sp1_setup_summary.json"
LEGACY_KAGGLE_VALIDATION_GLOB = "kaggle_phase6_outputs/**/kaggle_sp1_validation_summary.json"
LEGACY_KAGGLE_SETUP_GLOB = "kaggle_phase6_outputs/**/kaggle_sp1_setup_summary.json"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def value_with_source(value: Any, source: Path | str | None, field: str) -> Dict[str, Any]:
    return {
        "value": value,
        "provenance": {
            "source_path": rel(source) if isinstance(source, Path) else source,
            "field": field,
        },
    }


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def latest_existing(paths: Iterable[Path]) -> Optional[Path]:
    existing = [path for path in paths if path.exists()]
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)


def latest_kaggle_validation_summary(root: Path | None = None) -> Optional[Path]:
    base = root or ROOT
    preferred = base / "artifacts/reports/provenance/sp1/kaggle_sp1_validation_summary.json"
    if preferred.exists():
        return preferred
    return latest_existing(base.glob(LEGACY_KAGGLE_VALIDATION_GLOB))


def latest_kaggle_setup_summary(root: Path | None = None) -> Optional[Path]:
    base = root or ROOT
    preferred = base / "artifacts/reports/provenance/sp1/kaggle_sp1_setup_summary.json"
    if preferred.exists():
        return preferred
    return latest_existing(base.glob(LEGACY_KAGGLE_SETUP_GLOB))


def command_result(summary: Dict[str, Any], label: str) -> Optional[Dict[str, Any]]:
    for result in summary.get("commands", []):
        if result.get("label") == label:
            return result
    return None


def parse_key_value_tail(text: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        values[key.strip()] = raw_value.strip()
    return values


def parse_bool(raw: Any) -> Optional[bool]:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return None
    lowered = str(raw).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def parse_float(raw: Any) -> Optional[float]:
    if raw is None:
        return None
    try:
        return float(str(raw).strip())
    except ValueError:
        return None


def parse_int(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    match = re.search(r"-?\d+", str(raw))
    if not match:
        return None
    return int(match.group(0))


def command_to_text(command: Any) -> str | None:
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    if command is None:
        return None
    return str(command)


def build_regression_numbers(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    path = base / "artifacts/regression_summary.json"
    summary = load_json(path)
    if summary is None:
        return {"status": "missing", "source_path": rel(path)}
    return {
        "status": "available",
        "all_passed": value_with_source(summary.get("all_passed"), path, "all_passed"),
        "num_checks": value_with_source(summary.get("num_checks"), path, "num_checks"),
        "num_passed": value_with_source(summary.get("num_passed"), path, "num_passed"),
        "num_failed": value_with_source(summary.get("num_failed"), path, "num_failed"),
    }


def build_final_ndss_numbers(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    path = base / "artifacts/benchmarks/final_ndss/summary.json"
    summary = load_json(path)
    if summary is None:
        return {"status": "missing", "source_path": rel(path)}
    return {
        "status": "available",
        "artifact_id": value_with_source(summary.get("artifact_id"), path, "artifact_id"),
        "benchmark_rows": value_with_source(summary.get("benchmark_rows"), path, "benchmark_rows"),
        "tamper_rows": value_with_source(summary.get("tamper_rows"), path, "tamper_rows"),
        "all_components_passed": value_with_source(
            summary.get("all_components_passed"), path, "all_components_passed"
        ),
        "component_count": value_with_source(
            len(summary.get("components", [])), path, "components"
        ),
    }


def build_sp1_td_mvp_status(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    validation_path = latest_kaggle_validation_summary(base)
    setup_path = latest_kaggle_setup_summary(base)
    if validation_path is None:
        return {
            "status": "missing",
            "claim_scope": "td_mvp_canonical_vector_only",
            "source_path": None,
        }

    validation = load_json(validation_path) or {}
    setup = load_json(setup_path) if setup_path else {}
    execute = command_result(validation, "sp1_execute") or {}
    prove = command_result(validation, "sp1_prove") or {}
    execute_values = parse_key_value_tail(str(execute.get("stdout_tail", "")))
    prove_values = parse_key_value_tail(str(prove.get("stdout_tail", "")))

    proof_generated = parse_bool(prove_values.get("proof_generated"))
    proof_verified = parse_bool(prove_values.get("proof_verified"))
    prove_passed = validation.get("sp1_prove_status") == "passed" and prove.get("status") == "passed"
    execute_passed = validation.get("sp1_execute_status") == "passed" and execute.get("status") == "passed"
    status = "validated" if prove_passed and proof_generated and proof_verified else "not_validated"

    cargo_prove_version = None
    if setup:
        cargo_prove_version = setup.get("cargo_prove_version")
    if cargo_prove_version is None:
        env_after = command_result(validation, "sp1_environment_after_setup") or {}
        cargo_prove_version = env_after.get("cargo_prove_version")

    return {
        "status": status,
        "claim_scope": "td_mvp_canonical_vector_only",
        "kernel": value_with_source("nypate9999/zkp-drl", validation_path, "kernel"),
        "source_mode": value_with_source(validation.get("source_mode"), validation_path, "source_mode"),
        "git_branch": value_with_source(validation.get("git_branch"), validation_path, "git_branch"),
        "git_commit": value_with_source(validation.get("git_commit"), validation_path, "git_commit"),
        "cargo_available_after": value_with_source(
            validation.get("cargo_available_after"), validation_path, "cargo_available_after"
        ),
        "cargo_prove_version": value_with_source(
            cargo_prove_version, setup_path or validation_path, "cargo_prove_version"
        ),
        "cargo_test_status": value_with_source(
            validation.get("cargo_test_status"), validation_path, "cargo_test_status"
        ),
        "execute_status": value_with_source(
            validation.get("sp1_execute_status"), validation_path, "sp1_execute_status"
        ),
        "prove_status": value_with_source(
            validation.get("sp1_prove_status"), validation_path, "sp1_prove_status"
        ),
        "execute_command": value_with_source(
            command_to_text(execute.get("command")), validation_path, "commands.sp1_execute.command"
        ),
        "prove_command": value_with_source(
            command_to_text(prove.get("command")), validation_path, "commands.sp1_prove.command"
        ),
        "execute_duration_sec": value_with_source(
            execute.get("duration_sec"), validation_path, "commands.sp1_execute.duration_sec"
        ),
        "prove_duration_sec": value_with_source(
            prove.get("duration_sec"), validation_path, "commands.sp1_prove.duration_sec"
        ),
        "cycle_count": value_with_source(
            parse_int(execute_values.get("cycle_count")), validation_path, "commands.sp1_execute.stdout_tail.cycle_count"
        ),
        "execution_ok": value_with_source(
            parse_bool(execute_values.get("execution_ok")), validation_path, "commands.sp1_execute.stdout_tail.execution_ok"
        ),
        "proof_generated": value_with_source(
            proof_generated, validation_path, "commands.sp1_prove.stdout_tail.proof_generated"
        ),
        "proof_verified": value_with_source(
            proof_verified, validation_path, "commands.sp1_prove.stdout_tail.proof_verified"
        ),
        "proving_time_sec": value_with_source(
            parse_float(prove_values.get("proving_time_sec")),
            validation_path,
            "commands.sp1_prove.stdout_tail.proving_time_sec",
        ),
        "verification_time_sec": value_with_source(
            parse_float(prove_values.get("verification_time_sec")),
            validation_path,
            "commands.sp1_prove.stdout_tail.verification_time_sec",
        ),
        "proof_size_bytes": value_with_source(
            parse_int(prove_values.get("proof_size_bytes")),
            validation_path,
            "commands.sp1_prove.stdout_tail.proof_size_bytes",
        ),
        "proof_artifact_path": value_with_source(
            None, validation_path, "commands.sp1_prove.stdout_tail"
        ),
        "validation_summary_path": rel(validation_path),
        "setup_summary_path": rel(setup_path) if setup_path else None,
    }


def assemble_paper_numbers(root: Path | None = None) -> Dict[str, Any]:
    return {
        "artifact_id": "phase7_paper_numbers_v1",
        "scope": {
            "project": "relation-level verification of selected offline DQN artifacts",
            "sp1_proof_claim": (
                "SP1 proof generation and verification for the TD MVP backend on "
                "zk_backend/test_vectors/td_mvp_case_0.json only"
            ),
            "excluded_claims": [
                "full DQN training proof",
                "proof coverage for all relations",
                "recursive proof aggregation",
                "new benchmark methodology",
            ],
        },
        "regression": build_regression_numbers(root),
        "final_ndss_existing": build_final_ndss_numbers(root),
        "sp1_td_mvp_proof": build_sp1_td_mvp_status(root),
    }
