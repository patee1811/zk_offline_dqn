"""Generate the reviewer-facing artifact manifest and compact hash inventories."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
FINAL_DIR = ROOT / "artifacts/reports/final_ndss"
SP1_DIR = ROOT / "artifacts/reports/provenance/sp1"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def hash_existing(paths: Iterable[Path]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for path in sorted(paths):
        if path.exists() and path.is_file():
            out[rel(path)] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
    return out


def final_report_files() -> List[Path]:
    patterns = [
        "paper_numbers.json",
        "table*_*.csv",
        "table*_*.json",
        "table*_*.md",
        "table*_*.tex",
        "table*_status.json",
        "sp1_status.json",
        "benchmark_summary.csv",
        "tamper_summary.csv",
    ]
    paths: List[Path] = []
    for pattern in patterns:
        paths.extend(FINAL_DIR.glob(pattern))
    return sorted(set(paths))


def source_files() -> List[Path]:
    return [
        ROOT / "README.md",
        ROOT / "Makefile",
        ROOT / "Dockerfile",
        ROOT / "requirements.lock",
        ROOT / "docs/backend_coverage.md",
        ROOT / "docs/claim_matrix.md",
        ROOT / "docs/theorem_artifact_map.md",
        ROOT / "docs/artifact_reproducibility.md",
        ROOT / "paper/main.tex",
        ROOT / "paper/sections/theorems.tex",
        ROOT / "paper/sections/threat_model.tex",
        ROOT / "scripts/experiments/check_paper_claims.py",
        ROOT / "scripts/experiments/check_report_sources.py",
        ROOT / "scripts/experiments/check_theorem_artifact_map.py",
        ROOT / "scripts/experiments/generate_paper_reports.py",
        ROOT / "scripts/experiments/generate_artifact_manifest.py",
    ]


def collect_dataset_hashes() -> List[Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    table1 = FINAL_DIR / "table1_rl_performance.json"
    if table1.exists():
        for row in read_json(table1).get("rows", []):
            dataset_id = row.get("dataset_id") or row.get("dataset")
            if not dataset_id:
                continue
            entry = rows.setdefault(
                str(dataset_id),
                {
                    "dataset_id": dataset_id,
                    "source_type": row.get("dataset_source_type"),
                    "dataset_root": row.get("dataset_root") or row.get("merkle_root"),
                    "merkle_root": row.get("merkle_root") or row.get("dataset_root"),
                    "manifest_hash": row.get("manifest_hash"),
                    "audit_report_hash": row.get("audit_report_hash"),
                },
            )
            for key in ("dataset_root", "merkle_root", "manifest_hash", "audit_report_hash"):
                entry.setdefault(key, row.get(key))

    for path in sorted(SP1_DIR.glob("**/public_inputs.json")):
        data = read_json(path)
        dataset_id = data.get("dataset_id") or data.get("dataset_id_hash") or path.parent.name
        entry = rows.setdefault(
            str(dataset_id),
            {
                "dataset_id": dataset_id,
                "source_type": "sp1_public_inputs",
            },
        )
        entry.setdefault("dataset_root", data.get("dataset_root"))
        entry.setdefault("merkle_root", data.get("dataset_root"))
        entry.setdefault("manifest_hash", data.get("manifest_hash"))
        entry.setdefault("audit_report_hash", data.get("audit_report_hash"))
        entry.setdefault("source_path", rel(path))

    return sorted(rows.values(), key=lambda item: str(item.get("dataset_id")))


def collect_proof_hashes() -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for relation_dir in sorted(path for path in SP1_DIR.glob("*") if path.is_dir()):
        files = hash_existing(relation_dir.glob("*.json"))
        verify = relation_dir / "verify_report.json"
        metrics = relation_dir / "metrics.json"
        public_inputs = relation_dir / "public_inputs.json"
        entries.append(
            {
                "relation": relation_dir.name,
                "source_dir": rel(relation_dir),
                "verify_report": rel(verify) if verify.exists() else None,
                "metrics": rel(metrics) if metrics.exists() else None,
                "public_inputs": rel(public_inputs) if public_inputs.exists() else None,
                "file_hashes": files,
                "proof_binary_omitted_reason": "proof binaries, receipts, and raw proof bytes are not committed by artifact policy",
            }
        )
    for path in sorted(SP1_DIR.glob("*.json")):
        entries.append(
            {
                "relation": path.stem,
                "source_dir": rel(path.parent),
                "file_hashes": hash_existing([path]),
                "proof_binary_omitted_reason": "compact provenance summary only",
            }
        )
    return entries


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_manifest(out_dir: Path) -> Dict[str, Any]:
    dataset_hashes = collect_dataset_hashes()
    proof_hashes = collect_proof_hashes()
    tables = hash_existing(final_report_files())
    files = hash_existing(source_files())
    commands = [
        "make reproduce-small",
        "make reproduce-data-audit",
        "make reproduce-sp1-proofs",
        "make reproduce-benchmarks",
        "make reproduce-tamper",
        "make reproduce-paper-tables",
        "make artifact-manifest",
    ]
    manifest = {
        "schema_version": "artifact_manifest_v1",
        "git_commit": git_commit(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "commands": commands,
        "files": files,
        "tables": tables,
        "paper_numbers": tables.get(rel(FINAL_DIR / "paper_numbers.json")),
        "proof_provenance": proof_hashes,
        "dataset_hashes": dataset_hashes,
        "omitted_artifacts": [
            {
                "pattern": "artifacts/datasets/ and artifacts/data_sources/",
                "reason": "raw datasets are regenerated or imported by scripts and are not committed",
            },
            {
                "pattern": "*.bin, *.receipt, *.proof",
                "reason": "proof binaries are large and replaced by compact provenance and public-input hashes",
            },
            {
                "pattern": "artifacts/reports/**/work, tmp, proofs",
                "reason": "temporary benchmark/proof work directories are not paper artifacts",
            },
        ],
    }
    write_json(out_dir / "dataset_hashes.json", {"schema_version": "dataset_hashes_v1", "rows": dataset_hashes})
    write_json(out_dir / "proof_hashes.json", {"schema_version": "proof_hashes_v1", "rows": proof_hashes})
    write_json(out_dir / "artifact_manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(FINAL_DIR))
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    manifest = build_manifest(out_dir)
    print("artifact_manifest_generation = passed")
    print(json.dumps({"path": rel(out_dir / "artifact_manifest.json"), "git_commit": manifest["git_commit"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
