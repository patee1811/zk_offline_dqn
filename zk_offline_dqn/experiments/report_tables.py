"""Generate deterministic report snapshots from existing benchmark outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from zk_offline_dqn.experiments import benchmark_manifest, paper_numbers
from zk_offline_dqn.rl_benchmarks.reporting import DISCRETE_BASELINES
from zk_offline_dqn.tamper_benchmarks.cases import MANDATORY_CATEGORIES


ROOT = Path(__file__).resolve().parents[2]
# Scale points the artifact claims it can consume a public benchmark at.
PUBLIC_SCALE_POINTS = ("10000", "50000", "100000")
DEFAULT_OUT_DIR = ROOT / "artifacts/reports/final_ndss"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(fieldnames)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in names})


def _final_ndss_summary(root: Path) -> tuple[Dict[str, Any] | None, Path]:
    path = root / "artifacts/benchmarks/final_ndss/summary.json"
    return read_json(path), path


def build_benchmark_summary_rows(root: Path | None = None) -> List[Dict[str, Any]]:
    base = root or ROOT
    summary, path = _final_ndss_summary(base)
    if summary is None:
        return [
            {
                "status": "missing",
                "source_path": rel(path),
                "relation_id": None,
                "environment": None,
                "backend": None,
            }
        ]

    rows: List[Dict[str, Any]] = []
    for row in summary.get("benchmark_matrix", []):
        out = dict(row)
        out.setdefault("status", "missing")
        out["source_path"] = rel(path)
        rows.append(out)
    return rows


def build_tamper_summary_rows(root: Path | None = None) -> List[Dict[str, Any]]:
    base = root or ROOT
    summary, path = _final_ndss_summary(base)
    if summary is None:
        return [
            {
                "status": "missing",
                "source_path": rel(path),
                "relation_id": None,
                "environment": None,
                "case": None,
            }
        ]

    rows: List[Dict[str, Any]] = []
    for row in summary.get("tamper_matrix", []):
        out = dict(row)
        if "status" not in out:
            if out.get("passed") is None:
                out["status"] = "missing"
            else:
                out["status"] = "passed" if out.get("passed") else "failed"
        out.setdefault("observed_outcome", out.get("sp1_outcome") or out.get("python_outcome"))
        out.setdefault("backend", "SP1 proof" if out.get("sp1_outcome") else "Python oracle")
        out["source_path"] = rel(path)
        rows.append(out)
    return rows


def build_sp1_status(root: Path | None = None) -> Dict[str, Any]:
    return {
        "artifact_id": "phase7_sp1_status_v1",
        "td_mvp": paper_numbers.build_sp1_td_mvp_status(root),
        "scope_note": (
            "Validated status, if present, applies only to the TD MVP SP1 "
            "backend and zk_backend/test_vectors/td_mvp_case_0.json."
        ),
    }


def write_benchmark_snapshot(path: Path, numbers: Dict[str, Any], sp1_status: Dict[str, Any]) -> None:
    regression = numbers.get("regression", {})
    final_ndss = numbers.get("final_ndss_existing", {})
    sp1 = sp1_status.get("td_mvp", {})
    lines = [
        "# Phase 7 Benchmark Snapshot",
        "",
        "This file is generated from existing regression, benchmark, and Kaggle",
        "validation outputs. Missing values are not inferred.",
        "",
        "## Regression",
        "",
        f"- Status: {regression.get('status', 'missing')}",
        f"- All passed: {(regression.get('all_passed') or {}).get('value')}",
        f"- Checks: {(regression.get('num_passed') or {}).get('value')}/"
        f"{(regression.get('num_checks') or {}).get('value')}",
        "",
        "## Existing Final NDSS Benchmark Summary",
        "",
        f"- Status: {final_ndss.get('status', 'missing')}",
        f"- Benchmark rows: {(final_ndss.get('benchmark_rows') or {}).get('value')}",
        f"- Tamper rows: {(final_ndss.get('tamper_rows') or {}).get('value')}",
        f"- Components passed: {(final_ndss.get('all_components_passed') or {}).get('value')}",
        "",
        "## SP1 TD MVP Proof",
        "",
        f"- Status: {sp1.get('status')}",
        f"- Scope: {sp1.get('claim_scope')}",
        f"- Proof generated: {(sp1.get('proof_generated') or {}).get('value')}",
        f"- Proof verified: {(sp1.get('proof_verified') or {}).get('value')}",
        f"- Proving time sec: {(sp1.get('proving_time_sec') or {}).get('value')}",
        f"- Verification time sec: {(sp1.get('verification_time_sec') or {}).get('value')}",
        f"- Proof size bytes: {(sp1.get('proof_size_bytes') or {}).get('value')}",
        f"- Cycle count: {(sp1.get('cycle_count') or {}).get('value')}",
        "",
        "The SP1 proof claim is scoped only to the TD MVP canonical vector.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_reports(out_dir: Path | str | None = None, root: Path | None = None) -> Dict[str, str]:
    base = root or ROOT
    target = Path(out_dir) if out_dir is not None else DEFAULT_OUT_DIR
    if not target.is_absolute():
        target = base / target
    target.mkdir(parents=True, exist_ok=True)

    numbers = paper_numbers.assemble_paper_numbers(base)
    sp1_status = build_sp1_status(base)
    benchmark_rows = build_benchmark_summary_rows(base)
    tamper_rows = build_tamper_summary_rows(base)

    paths = {
        "paper_numbers": target / "paper_numbers.json",
        "benchmark_summary": target / "benchmark_summary.csv",
        "tamper_summary": target / "tamper_summary.csv",
        "sp1_status": target / "sp1_status.json",
        "benchmark_snapshot": target / "benchmark_snapshot.md",
    }

    write_json(paths["paper_numbers"], numbers)
    write_json(paths["sp1_status"], sp1_status)
    write_csv(
        paths["benchmark_summary"],
        benchmark_rows,
        [
            "relation_id",
            "environment",
            "network_spec",
            "batch_size",
            "merkle_depth",
            "accepted_fixtures",
            "rejected_tamper_fixtures",
            "prove_time_sec",
            "verify_time_sec",
            "proof_size_bytes",
            "cycle_count",
            "platform",
            "command",
            "source_summary",
            "source_case",
            "fixture_path",
            "backend",
            "status",
            "source_path",
        ],
    )
    write_csv(
        paths["tamper_summary"],
        tamper_rows,
        [
            "relation_id",
            "environment",
            "network_spec",
            "case",
            "category",
            "expected_outcome",
            "observed_outcome",
            "python_outcome",
            "sp1_outcome",
            "passed",
            "backend",
            "source_summary",
            "fixture_path",
            "status",
            "source_path",
        ],
    )
    write_benchmark_snapshot(paths["benchmark_snapshot"], numbers, sp1_status)

    outputs = {key: rel(path) for key, path in paths.items()}
    table3 = target / "table3_tamper_rejection.csv"
    if table3.exists():
        outputs["table3_tamper_rejection"] = rel(table3)
    return outputs


def check_report_sources(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    result = benchmark_manifest.check_sources(base)
    table1 = check_table1_rl_performance(base)
    public_coverage = check_public_dataset_coverage(base)
    table2 = check_table2_zk_proof_cost(base)
    table3 = check_table3_tamper_rejection(base)
    theorem_map = check_theorem_artifact_map_sources(base)
    artifact_package = check_artifact_package_sources(base)
    result["table1_rl_performance"] = table1
    result["public_dataset_coverage"] = public_coverage
    result["table2_zk_proof_cost"] = table2
    result["table3_tamper_rejection"] = table3
    result["theorem_artifact_map"] = theorem_map
    result["artifact_package"] = artifact_package
    if (
        table1["status"] != "passed"
        or public_coverage["status"] != "passed"
        or table2["status"] != "passed"
        or table3["status"] != "passed"
        or theorem_map["status"] != "passed"
        or artifact_package["status"] != "passed"
    ):
        result["status"] = "failed"
    return result


def check_table1_rl_performance(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    table_dir = base / "artifacts/reports/final_ndss"
    required = [
        "table1_rl_performance.csv",
        "table1_rl_performance.json",
        "table1_rl_performance.tex",
        "table1_rl_performance.md",
        "table1_rl_performance_status.json",
    ]
    missing = [name for name in required if not (table_dir / name).exists()]
    if missing:
        return {
            "status": "failed",
            "missing_files": missing,
            "completed_public_rows": 0,
            "required_public_size_coverage": {},
            "reason": "Table 1 compact outputs are missing",
        }

    payload = read_json(table_dir / "table1_rl_performance.json") or {}
    rows = payload.get("rows", [])
    completed = [row for row in rows if row.get("status") == "completed"]

    # Public-benchmark evidence used to be asserted here, on a completed
    # PointMaze row. PointMaze is continuous-action, so those rows only ever
    # ran baselines outside the proved relation; the evidence now lives in
    # check_public_dataset_coverage, against Table 2.
    outside_relation = sorted(
        {
            str(row.get("baseline"))
            for row in completed
            if row.get("baseline") not in DISCRETE_BASELINES
        }
    )
    optimizers = sorted({str(row.get("optimizer")) for row in completed if row.get("optimizer")})

    reasons = []
    if not completed:
        reasons.append("no completed Table 1 row")
    if outside_relation:
        reasons.append(
            "completed rows outside the proved discrete relation: " + ", ".join(outside_relation)
        )
    if completed and "sgd" not in optimizers:
        # An Adam-only table reports a learning rate that encode_fp cannot even
        # represent, so it describes training the proof system cannot verify.
        reasons.append("no row trained under the optimizer the relation proves")
    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": [],
        "completed_rows": len(completed),
        "optimizers": optimizers,
        "baselines_outside_relation": outside_relation,
        "reason": "; ".join(reasons) if reasons else None,
    }


def _public_dataset_size(dataset_id: str) -> str | None:
    if not dataset_id.startswith("minari-"):
        return None
    tail = dataset_id.rsplit("-", 1)[-1]
    return tail if tail.isdigit() else None


def check_public_dataset_coverage(root: Path | None = None) -> Dict[str, Any]:
    """Public-benchmark evidence, which Table 2 carries and Table 1 no longer does.

    Two halves, kept separate because they fail for different reasons: the
    artifact has to commit a public dataset at each claimed scale point, and it
    has to prove membership against one of those commitments. Asserting them
    through a completed RL row conflated both with a third thing -- whether some
    baseline happened to be action-compatible with the dataset.
    """
    base = root or ROOT
    table_dir = base / "artifacts/reports/final_ndss"

    hashes = read_json(table_dir / "dataset_hashes.json") or {}
    committed_roots: Dict[str, str] = {}
    for row in hashes.get("rows", []):
        dataset_id = str(row.get("dataset_id", ""))
        size = _public_dataset_size(dataset_id)
        merkle_root = row.get("merkle_root")
        if size and merkle_root:
            committed_roots[dataset_id] = str(merkle_root)

    coverage = {
        size: sorted(
            dataset_id
            for dataset_id in committed_roots
            if _public_dataset_size(dataset_id) == size
        )
        for size in PUBLIC_SCALE_POINTS
    }

    table2 = read_json(table_dir / "table2_zk_proof_cost.json") or {}
    proved_roots = set()
    for row in table2.get("rows", []):
        if row.get("Relation") != "merkle_membership" or row.get("Status") != "proof_verified":
            continue
        source = row.get("Metrics Source")
        metrics = read_json(base / str(source)) if source else None
        if metrics and metrics.get("dataset_root"):
            proved_roots.add(str(metrics["dataset_root"]))
    proved_public = sorted(
        dataset_id
        for dataset_id, merkle_root in committed_roots.items()
        if merkle_root in proved_roots
    )

    reasons = []
    uncovered = [size for size, ids in coverage.items() if not ids]
    if uncovered:
        reasons.append("no committed public dataset at scale " + ", ".join(uncovered))
    if not proved_public:
        reasons.append("no proof_verified merkle_membership row on a committed public dataset")
    return {
        "status": "passed" if not reasons else "failed",
        "committed_public_datasets": sorted(committed_roots),
        "scale_point_coverage": coverage,
        "proof_verified_public_datasets": proved_public,
        "reason": "; ".join(reasons) if reasons else None,
    }


def check_table2_zk_proof_cost(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    table_dir = base / "artifacts/reports/final_ndss"
    required = [
        "table2_zk_proof_cost.csv",
        "table2_zk_proof_cost.json",
        "table2_zk_proof_cost.tex",
        "table2_zk_proof_cost.md",
        "table2_zk_proof_cost_status.json",
    ]
    missing = [name for name in required if not (table_dir / name).exists()]
    if missing:
        return {
            "status": "failed",
            "missing_files": missing,
            "reason": "Table 2 compact outputs are missing",
            "proof_verified_rows": 0,
        }

    payload = read_json(table_dir / "table2_zk_proof_cost.json") or {}
    rows = payload.get("rows", [])
    required_relations = {
        "td_mvp",
        "merkle_membership",
        "forward_td_mlp",
        "one_step_sgd_tiny",
        "short_trace",
        "training_update",
        "training_fragment_k1",
        "training_fragment_k4",
        "training_fragment_k8",
        "training_aggregation_manifest_t32",
        "training_aggregation_manifest_t64",
        "training_aggregation_manifest_t128",
    }
    present_text = " ".join(
        " ".join(str(value) for value in row.values()) for row in rows if isinstance(row, dict)
    )
    missing_relations = sorted(relation for relation in required_relations if relation not in present_text)
    required_fields = [
        "Prove Time (s)",
        "Verify Time (s)",
        "Proof Size (bytes)",
        "Cycle Count",
        "Peak RSS (MB)",
        "Status",
    ]
    missing_fields = [
        field
        for field in required_fields
        if any(isinstance(row, dict) and field not in row for row in rows)
    ]
    proof_verified = [row for row in rows if isinstance(row, dict) and row.get("Status") == "proof_verified"]
    merkle_size_rows = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("Relation") == "merkle_membership" and row.get("Scale Axis") == "dataset_size":
            merkle_size_rows[str(row.get("Dataset Size"))] = row
    metric_gaps = []
    for row in proof_verified:
        for field in ["Prove Time (s)", "Verify Time (s)", "Proof Size (bytes)", "Cycle Count"]:
            if row.get(field) in {None, ""}:
                metric_gaps.append(f"{row.get('Case ID')}:{field}")
    reasons = []
    if missing_relations:
        reasons.append("missing required proof rows: " + ", ".join(missing_relations))
    if missing_fields:
        reasons.append("missing required fields: " + ", ".join(sorted(set(missing_fields))))
    if not proof_verified:
        reasons.append("no proof_verified Table 2 rows")
    if metric_gaps:
        reasons.append("proof_verified metric gaps: " + ", ".join(metric_gaps[:10]))
    for size in ("1000", "10000", "100000"):
        if size not in merkle_size_rows:
            reasons.append(f"missing Merkle dataset-size row: {size}")
    for size in ("10000", "100000"):
        row = merkle_size_rows.get(size)
        if row and row.get("Status") not in {"proof_verified", "failed_oom", "failed_timeout", "failed_compile", "failed_verify", "failed_environment"}:
            reasons.append(f"Merkle dataset-size row {size} has unattempted status: {row.get('Status')}")
    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": [],
        "missing_required_relations": missing_relations,
        "proof_verified_rows": len(proof_verified),
        "merkle_dataset_size_rows": {size: row.get("Status") for size, row in merkle_size_rows.items()},
        "reason": "; ".join(reasons) if reasons else None,
    }


def check_table3_tamper_rejection(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    table_dir = base / "artifacts/reports/final_ndss"
    required = [
        "table3_tamper_rejection.csv",
        "table3_tamper_rejection.json",
        "table3_tamper_rejection.tex",
        "table3_tamper_rejection.md",
        "table3_tamper_rejection_status.json",
    ]
    missing = [name for name in required if not (table_dir / name).exists()]
    if missing:
        return {
            "status": "failed",
            "missing_files": missing,
            "reason": "Table 3 compact outputs are missing",
            "mandatory_category_coverage": {},
            "accepted_unexpectedly": [],
        }

    payload = read_json(table_dir / "table3_tamper_rejection.json") or {}
    rows = payload.get("rows", [])
    accepted = [
        row.get("Tamper ID")
        for row in rows
        if isinstance(row, dict) and row.get("Status") == "accepted_unexpectedly"
    ]
    coverage = {}
    for category in MANDATORY_CATEGORIES:
        matched = [
            row
            for row in rows
            if isinstance(row, dict)
            and (
                row.get("Tamper Category") == category
                or category in str(row.get("Tamper ID", "")).lower()
            )
        ]
        coverage[category] = {
            "rows": len(matched),
            "rejected_as_expected": sum(
                1 for row in matched if row.get("Status") == "rejected_as_expected"
            ),
        }
    missing_categories = [
        category
        for category, item in coverage.items()
        if item["rejected_as_expected"] < 1
    ]
    reasons = []
    if accepted:
        reasons.append("accepted_unexpectedly rows: " + ", ".join(str(item) for item in accepted[:10]))
    if missing_categories:
        reasons.append("missing mandatory rejected categories: " + ", ".join(missing_categories))
    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": [],
        "mandatory_category_coverage": coverage,
        "accepted_unexpectedly": accepted,
        "reason": "; ".join(reasons) if reasons else None,
    }


def check_theorem_artifact_map_sources(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    paths = {
        "theorem_map": base / "docs/theorem_artifact_map.md",
        "theorems_tex": base / "paper/sections/theorems.tex",
        "threat_model_tex": base / "paper/sections/threat_model.tex",
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        return {
            "status": "failed",
            "missing_files": missing,
            "reason": "Phase 9 theorem/threat-model files are missing",
        }
    text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in paths.values())
    lowered = text.lower()
    missing_theorems = [f"Theorem {idx}" for idx in range(1, 9) if f"theorem {idx}" not in lowered]
    required_terms = [
        "relation/component",
        "sp1 backend / verifier",
        "primary tests",
        "table 2 row",
        "table 3 row",
        "proof-manifest",
        "not true recursive",
        "public benchmark",
        "honest collection",
        "reward",
    ]
    missing_terms = [term for term in required_terms if term not in lowered]
    unsafe = [
        phrase
        for phrase in [
            "we prove offline dqn training",
            "prove full dqn training",
            "true recursive aggregation soundness",
            "public benchmark honest collection proof",
        ]
        if phrase in lowered
    ]
    reasons = []
    if missing_theorems:
        reasons.append("missing theorem labels: " + ", ".join(missing_theorems))
    if missing_terms:
        reasons.append("missing required terms: " + ", ".join(missing_terms))
    if unsafe:
        reasons.append("unsafe phrases: " + ", ".join(unsafe))
    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": [],
        "missing_theorems": missing_theorems,
        "missing_terms": missing_terms,
        "unsafe_phrases": unsafe,
        "reason": "; ".join(reasons) if reasons else None,
    }


def check_artifact_package_sources(root: Path | None = None) -> Dict[str, Any]:
    base = root or ROOT
    final_dir = base / "artifacts/reports/final_ndss"
    required_files = [
        base / "Makefile",
        base / "Dockerfile",
        base / ".dockerignore",
        base / "requirements.lock",
        base / "docs/artifact_reproducibility.md",
        final_dir / "artifact_manifest.json",
        final_dir / "dataset_hashes.json",
        final_dir / "proof_hashes.json",
        final_dir / "paper_numbers.json",
    ]
    missing = [rel(path) for path in required_files if not path.exists()]

    required_targets = [
        "reproduce-small",
        "reproduce-data-audit",
        "reproduce-sp1-proofs",
        "reproduce-benchmarks",
        "reproduce-tamper",
        "reproduce-paper-tables",
        "artifact-manifest",
    ]
    make_text = (base / "Makefile").read_text(encoding="utf-8", errors="replace") if (base / "Makefile").exists() else ""
    readme_text = (base / "README.md").read_text(encoding="utf-8", errors="replace").lower() if (base / "README.md").exists() else ""
    missing_targets = [target for target in required_targets if f"{target}:" not in make_text]
    missing_readme_commands = [target for target in required_targets if f"make {target}" not in readme_text]

    manifest_gaps: List[str] = []
    raw_references: List[str] = []
    manifest_path = final_dir / "artifact_manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path) or {}
        for key in [
            "git_commit",
            "generated_at",
            "python_version",
            "platform",
            "commands",
            "files",
            "tables",
            "proof_provenance",
            "dataset_hashes",
            "omitted_artifacts",
        ]:
            if key not in manifest:
                manifest_gaps.append(key)
        manifest_text = json.dumps(
            {
                "files": manifest.get("files", {}),
                "tables": manifest.get("tables", {}),
                "proof_provenance": [
                    {k: v for k, v in item.items() if k != "proof_binary_omitted_reason"}
                    for item in manifest.get("proof_provenance", [])
                    if isinstance(item, dict)
                ],
            },
            sort_keys=True,
        ).lower()
        for forbidden in ["raw_episodes.jsonl", ".receipt", ".proof", "proof.bin"]:
            if forbidden in manifest_text:
                raw_references.append(forbidden)

    reasons = []
    if missing:
        reasons.append("missing files: " + ", ".join(missing))
    if missing_targets:
        reasons.append("missing Make targets: " + ", ".join(missing_targets))
    if missing_readme_commands:
        reasons.append("README missing commands: " + ", ".join(missing_readme_commands))
    if manifest_gaps:
        reasons.append("artifact manifest missing keys: " + ", ".join(manifest_gaps))
    if raw_references:
        reasons.append("artifact manifest references raw/proof binaries: " + ", ".join(raw_references))

    return {
        "status": "passed" if not reasons else "failed",
        "missing_files": missing,
        "missing_make_targets": missing_targets,
        "missing_readme_commands": missing_readme_commands,
        "manifest_gaps": manifest_gaps,
        "raw_references": raw_references,
        "reason": "; ".join(reasons) if reasons else None,
    }
