from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .cases import CORE_CASES, ProofCase, provenance_path
from .metrics import load_json, normalize_metrics, sha256_file, validate_status
from .reporting import write_table2_outputs


ROOT = Path(__file__).resolve().parents[2]
PHASE_DIR = ROOT / "artifacts/reports/phase8_2_proof_benchmark"


def build_rows(
    *,
    root: Path | None = None,
    dataset_sizes: Iterable[int] = (1000, 10000, 100000),
    trace_lengths: Iterable[int] = (1, 4, 8, 16, 32, 128),
    batch_sizes: Iterable[int] = (1, 4, 8, 16),
    networks: Iterable[str] = ("tiny", "small"),
    aggregation_targets: Iterable[int] = (32, 64, 128),
    include_execute_only: bool = True,
    include_known_failures: bool = True,
) -> List[Dict[str, Any]]:
    base = root or ROOT
    rows: List[Dict[str, Any]] = [_row_from_case(base, case) for case in CORE_CASES]
    rows.extend(_trace_scaling_rows(trace_lengths, include_execute_only=include_execute_only))
    rows.extend(_batch_scaling_rows(batch_sizes))
    rows.extend(_network_scaling_rows(networks))
    rows.extend(_dataset_merkle_rows(base, dataset_sizes))
    rows.extend(_aggregation_scaling_rows(base, aggregation_targets))
    if include_known_failures:
        rows.extend(_known_failure_rows())
    return _dedupe_rows(rows)


def _row_from_case(root: Path, case: ProofCase) -> Dict[str, Any]:
    metrics = _load_case_metrics(root, case)
    norm = normalize_metrics(metrics)
    proof_verified = bool(norm.get("proof_generated") and norm.get("proof_verified"))
    status = "proof_verified" if proof_verified else case.status
    public_hash = norm.get("public_inputs_sha256") or _hash_in_provenance(root, case, "public_inputs.json")
    witness_hash = norm.get("witness_schema_sha256") or _hash_in_provenance(root, case, "witness_schema.json")
    notes = _notes(case, norm)
    return _base_row(
        category=case.category,
        relation=case.relation,
        variant=case.variant,
        scale_axis=case.scale_axis,
        batch_size=case.batch_size,
        network=case.network,
        trace_length=case.trace_length,
        dataset_size=case.dataset_size,
        merkle_depth=case.merkle_depth,
        aggregation_t=case.aggregation_t,
        proof_backed=proof_verified and case.proof_backed,
        status=status if proof_verified else "failed_environment",
        prove_time=norm.get("prove_time_seconds"),
        verify_time=norm.get("verify_time_seconds"),
        proof_size=norm.get("proof_size_bytes"),
        cycle_count=norm.get("cycle_count"),
        prover_gas=norm.get("prover_gas"),
        peak_rss=norm.get("peak_rss_mb"),
        max_rss=norm.get("max_rss_mb"),
        backend_version=norm.get("backend_version"),
        sp1_version=norm.get("sp1_version"),
        git_commit=norm.get("git_commit") or _git_commit(root),
        case_id=case.case_id,
        public_inputs_sha256=public_hash,
        witness_schema_sha256=witness_hash,
        metrics_source=_metrics_source(root, case),
        notes=notes,
    )


def _load_case_metrics(root: Path, case: ProofCase) -> Dict[str, Any] | None:
    if case.case_id == "td_mvp":
        return _td_mvp_metrics(root)
    path = provenance_path(root, case)
    return None if path is None else load_json(path / "metrics.json")


def _td_mvp_metrics(root: Path) -> Dict[str, Any] | None:
    summary = load_json(root / "artifacts/reports/provenance/sp1/kaggle_sp1_validation_summary.json")
    if not summary:
        return None
    execute = _command(summary, "sp1_execute")
    prove = _command(summary, "sp1_prove")
    execute_values = _parse_key_values(execute.get("stdout_tail", "") if execute else "")
    prove_values = _parse_key_values(prove.get("stdout_tail", "") if prove else "")
    return {
        "relation": "td_mvp",
        "proof_generated": prove_values.get("proof_generated") == "true",
        "proof_verified": prove_values.get("proof_verified") == "true",
        "prove_time_seconds": _float(prove_values.get("proving_time_sec")),
        "verify_time_seconds": _float(prove_values.get("verification_time_sec")),
        "proof_size_bytes": _int(prove_values.get("proof_size_bytes")),
        "cycle_count": _int(execute_values.get("cycle_count")),
        "backend_version": "0.1.0",
        "sp1_version": "6.1.0",
        "git_commit": summary.get("git_commit"),
    }


def _command(summary: Dict[str, Any], label: str) -> Dict[str, Any] | None:
    for item in summary.get("commands", []):
        if item.get("label") == label:
            return item
    return None


def _parse_key_values(text: str) -> Dict[str, str]:
    out = {}
    for line in str(text).splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def _float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return None if value is None else int(float(value))
    except (TypeError, ValueError):
        return None


def _hash_in_provenance(root: Path, case: ProofCase, filename: str) -> str | None:
    path = provenance_path(root, case)
    return None if path is None else sha256_file(path / filename)


def _metrics_source(root: Path, case: ProofCase) -> str:
    if case.case_id == "td_mvp":
        return "artifacts/reports/provenance/sp1/kaggle_sp1_validation_summary.json"
    path = provenance_path(root, case)
    return "" if path is None else (path / "metrics.json").relative_to(root).as_posix()


def _notes(case: ProofCase, norm: Dict[str, Any]) -> str:
    pieces = []
    raw_notes = norm.get("notes")
    if isinstance(raw_notes, list):
        pieces.extend(str(item) for item in raw_notes)
    elif raw_notes:
        pieces.append(str(raw_notes))
    if case.notes:
        pieces.append(case.notes)
    if not norm.get("peak_rss_mb"):
        pieces.append("peak RSS unavailable in reused compact provenance")
    return "; ".join(dict.fromkeys(pieces))


def _trace_scaling_rows(trace_lengths: Iterable[int], *, include_execute_only: bool) -> List[Dict[str, Any]]:
    supported = {1: "training_fragment_k1", 4: "training_fragment_k4", 8: "training_fragment_k8"}
    rows = []
    for k in trace_lengths:
        if k in supported:
            continue
        if include_execute_only:
            rows.append(
                _base_row(
                    category="trace_scaling",
                    relation=f"training_fragment_k{k}",
                    variant=f"k{k}",
                    scale_axis="trace_length",
                    trace_length=k,
                    proof_backed=False,
                    status="execute_only",
                    case_id=f"training_fragment_k{k}_execute_only",
                    notes="reference/execute-mode only in current backend; no proof metrics claimed",
                )
            )
    return rows


def _batch_scaling_rows(batch_sizes: Iterable[int]) -> List[Dict[str, Any]]:
    rows = []
    for batch_size in batch_sizes:
        if int(batch_size) == 1:
            continue
        rows.append(
            _base_row(
                category="batch_scaling",
                relation="training_update",
                variant=f"batch{batch_size}",
                scale_axis="batch_size",
                batch_size=int(batch_size),
                network="tiny",
                proof_backed=False,
                status="not_supported_current_backend",
                case_id=f"training_update_batch{batch_size}",
                notes="current Phase 5 training_update SP1 backend is canonical batch-size-1 only",
            )
        )
    return rows


def _network_scaling_rows(networks: Iterable[str]) -> List[Dict[str, Any]]:
    rows = []
    for network in networks:
        if network == "tiny":
            continue
        rows.append(
            _base_row(
                category="network_scaling",
                relation="training_update",
                variant=f"network_{network}",
                scale_axis="network",
                network=network,
                proof_backed=False,
                status="not_supported_current_backend",
                case_id=f"training_update_network_{network}",
                notes="current SP1 proof-backed relations are canonical tiny vectors only",
            )
        )
    return rows


def _dataset_merkle_rows(root: Path, dataset_sizes: Iterable[int]) -> List[Dict[str, Any]]:
    # Only the canonical small Merkle membership proof is available as compact
    # proof provenance in the repository. Larger depths are represented as
    # honest scaling rows unless a future run writes size-specific provenance.
    canonical = _row_from_case(root, CORE_CASES[1])
    rows = []
    depth_by_size = {1000: 10, 10000: 14, 100000: 17}
    for size in dataset_sizes:
        row = dict(canonical)
        row["Category"] = "dataset_merkle_scaling"
        row["Variant"] = f"dataset_{int(size)}"
        row["Scale Axis"] = "dataset_size"
        row["Dataset Size"] = int(size)
        row["Merkle Depth"] = depth_by_size.get(int(size))
        row["Case ID"] = f"merkle_membership_dataset_{int(size)}"
        if int(size) != 1000:
            row["Proof Backed"] = False
            row["Status"] = "reference_only"
            row["Prove Time (s)"] = None
            row["Verify Time (s)"] = None
            row["Proof Size (bytes)"] = None
            row["Cycle Count"] = None
            row["Prover Gas"] = None
            row["Peak RSS (MB)"] = None
            row["Max RSS (MB)"] = None
            row["Public Inputs SHA256"] = None
            row["Witness Schema SHA256"] = None
            row["Metrics Source"] = ""
        row["Notes"] = (
            "dataset-size/Merkle-depth scaling row; canonical 1k row uses existing "
            "SP1 Merkle membership proof provenance; larger depths require a "
            "size-specific proof refresh before proof metrics are claimed"
        )
        rows.append(row)
    return rows


def _aggregation_scaling_rows(root: Path, targets: Iterable[int]) -> List[Dict[str, Any]]:
    existing = {32, 64, 128}
    rows = []
    for target in targets:
        if int(target) in existing:
            continue
        rows.append(
            _base_row(
                category="aggregation_scaling",
                relation=f"training_aggregation_manifest_t{target}",
                variant="proof_manifest_chain",
                scale_axis="aggregation_t",
                aggregation_t=int(target),
                proof_backed=False,
                status="not_supported_current_backend",
                case_id=f"training_aggregation_manifest_t{target}",
                notes="only T={32,64,128} proof-manifest-chain aggregation is currently proof-backed",
            )
        )
    return rows


def _known_failure_rows() -> List[Dict[str, Any]]:
    return [
        _base_row(
            category="known_failure",
            relation="native_flat_recursive_t32",
            variant="true_recursive_native",
            scale_axis="recursive_aggregation",
            aggregation_t=32,
            proof_backed=False,
            status="failed_oom",
            case_id="native_flat_recursive_t32",
            notes="execute passed; final proof failed OOM; not true proof-backed recursion",
        ),
        _base_row(
            category="known_failure",
            relation="groth16_plonk_recursive_t16",
            variant="snark_export",
            scale_axis="recursive_aggregation",
            aggregation_t=16,
            proof_backed=False,
            status="failed_environment",
            case_id="groth16_plonk_recursive_t16",
            notes="child SNARK export blocked on Kaggle Docker/Gnark path",
        ),
        _base_row(
            category="known_failure",
            relation="binary_tree_native_t16",
            variant="binary_native_recursive",
            scale_axis="recursive_aggregation",
            aggregation_t=16,
            proof_backed=False,
            status="failed_oom",
            case_id="binary_tree_native_t16",
            notes="execute passed; final proof failed OOM; not true recursion proof",
        ),
    ]


def _base_row(
    *,
    category: str,
    relation: str,
    variant: str,
    scale_axis: str,
    batch_size: int | None = None,
    network: str | None = None,
    trace_length: int | None = None,
    dataset_size: int | None = None,
    merkle_depth: int | None = None,
    aggregation_t: int | None = None,
    proof_backed: bool,
    status: str,
    prove_time: Any = None,
    verify_time: Any = None,
    proof_size: Any = None,
    cycle_count: Any = None,
    prover_gas: Any = None,
    peak_rss: Any = None,
    max_rss: Any = None,
    backend_version: Any = None,
    sp1_version: Any = None,
    git_commit: Any = None,
    case_id: str,
    public_inputs_sha256: Any = None,
    witness_schema_sha256: Any = None,
    metrics_source: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    validate_status(status)
    return {
        "Category": category,
        "Relation": relation,
        "Variant": variant,
        "Scale Axis": scale_axis,
        "Batch Size": batch_size,
        "Network": network,
        "Trace Length": trace_length,
        "Dataset Size": dataset_size,
        "Merkle Depth": merkle_depth,
        "Aggregation T": aggregation_t,
        "Proof Backed": bool(proof_backed),
        "Status": status,
        "Prove Time (s)": prove_time,
        "Verify Time (s)": verify_time,
        "Proof Size (bytes)": proof_size,
        "Cycle Count": cycle_count,
        "Prover Gas": prover_gas,
        "Peak RSS (MB)": peak_rss,
        "Max RSS (MB)": max_rss,
        "Backend Version": backend_version,
        "SP1 Version": sp1_version,
        "Git Commit": git_commit,
        "Case ID": case_id,
        "Public Inputs SHA256": public_inputs_sha256,
        "Witness Schema SHA256": witness_schema_sha256,
        "Metrics Source": metrics_source,
        "Notes": notes,
    }


def _dedupe_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for row in rows:
        key = (row["Case ID"], row["Scale Axis"])
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _git_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return None


def run_benchmark(args: Any, *, root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    rows = build_rows(
        root=base,
        dataset_sizes=args.dataset_sizes,
        trace_lengths=args.trace_lengths,
        batch_sizes=args.batch_sizes,
        networks=args.networks,
        aggregation_targets=args.aggregation_targets,
        include_execute_only=args.include_execute_only,
        include_known_failures=args.include_known_failures,
    )
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = base / out_dir
    status = {
        "phase": "8.2",
        "scope": "ZK proof cost only",
        "mode": "paper" if args.paper else "smoke",
        "row_count": len(rows),
        "proof_verified_rows": sum(row["Status"] == "proof_verified" for row in rows),
        "execute_only_rows": sum(row["Status"] == "execute_only" for row in rows),
        "unsupported_rows": sum(row["Status"] == "not_supported_current_backend" for row in rows),
        "failed_resource_rows": sum(str(row["Status"]).startswith("failed_") for row in rows),
        "core_relations": [case.case_id for case in CORE_CASES],
    }
    config = {
        "paper": bool(args.paper),
        "smoke": bool(args.smoke),
        "run_sp1_execute": bool(args.run_sp1_execute),
        "run_sp1_prove": bool(args.run_sp1_prove),
        "reuse_existing_provenance": bool(args.reuse_existing_provenance),
        "refresh_proof_metrics": bool(args.refresh_proof_metrics),
        "dataset_sizes": list(args.dataset_sizes),
        "trace_lengths": list(args.trace_lengths),
        "batch_sizes": list(args.batch_sizes),
        "networks": list(args.networks),
        "aggregation_targets": list(args.aggregation_targets),
        "out_dir": out_dir.as_posix(),
    }
    write_table2_outputs(rows, out_dir, status=status)
    _write_phase_outputs(base, rows, config, status)
    return status


def _write_phase_outputs(
    root: Path,
    rows: List[Dict[str, Any]],
    config: Dict[str, Any],
    status: Dict[str, Any],
) -> None:
    phase_dir = root / "artifacts/reports/phase8_2_proof_benchmark"
    phase_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (phase_dir / "status.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (phase_dir / "results.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")
