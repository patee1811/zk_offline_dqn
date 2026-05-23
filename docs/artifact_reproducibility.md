# Artifact Reproducibility

This artifact is designed for a reviewer to clone the repository and run the
fast path without regenerating large proofs or raw benchmark datasets.

## Prerequisites

- Python 3.10 or compatible Python 3.9+.
- `make` on Linux, macOS, WSL2, or Kaggle.
- Python dependencies from `requirements.lock` or `requirements.txt`.
- Rust/SP1 only for optional heavy proof reruns.

## Command Table

| Command | Purpose | Expected runtime class | Primary outputs |
| --- | --- | --- | --- |
| `make reproduce-small` | Runs the reviewer fast path | minutes | tiny dataset audit, compact proof provenance check, benchmark/table checks, artifact manifest |
| `make reproduce-data-audit` | Regenerates a tiny CartPole audited commitment | minutes | `artifacts/reproducibility/data_audit/.../replay_audit_report.json`, `merkle_tree.json` |
| `make reproduce-smoke-sources` | Regenerates lightweight regression/report sources | minutes | `artifacts/regression_summary.json`, `artifacts/benchmarks/*_python_smoke/summary.json` |
| `make reproduce-sp1-proofs` | Validates compact SP1 provenance by default | seconds-minutes | report-source check over `artifacts/reports/provenance/sp1/` |
| `make reproduce-benchmarks` | Regenerates paper report snapshots from compact reports | seconds-minutes | `artifacts/reports/final_ndss/paper_numbers.json` and summary CSVs |
| `make reproduce-tamper` | Validates Table 3 by default | seconds-minutes | Table 3 source-check status |
| `make reproduce-paper-tables` | Regenerates paper-facing report snapshots | seconds | `artifacts/reports/final_ndss/` |
| `make artifact-manifest` | Regenerates hash inventories | seconds | `artifact_manifest.json`, `dataset_hashes.json`, `proof_hashes.json` |

Heavy SP1 proof generation is not part of the default reviewer path. Set
`RUN_HEAVY_SP1=1` only after installing the SP1 toolchain. Full benchmark and
tamper refreshes are similarly gated by `RUN_HEAVY_BENCHMARKS=1` and
`RUN_HEAVY_TAMPER=1`.

## Expected Outputs

The fast path produces or validates:

- dataset audit report: `artifacts/reproducibility/data_audit/cartpole-phase10-small/replay_audit_report.json`;
- dataset commitment: `artifacts/reproducibility/data_audit/cartpole-phase10-small/merkle_tree.json`;
- proof provenance checks: compact reports under `artifacts/reports/provenance/sp1/`;
- paper tables: Table 1, Table 2, and Table 3 under `artifacts/reports/final_ndss/`;
- artifact manifest: `artifacts/reports/final_ndss/artifact_manifest.json`.

## Artifact Inventory

Committed compact artifacts include final paper tables, `paper_numbers.json`,
dataset/proof hash inventories, theorem-to-artifact mapping, and SP1 compact
provenance. Raw datasets, proof binaries, receipts, and temporary proof work
directories are intentionally omitted because they are large and regenerable or
because compact public-input/provenance hashes are the paper artifact.

## Verifying Hashes

Run:

```text
make artifact-manifest
```

The manifest records SHA256 hashes for paper tables, source files, compact SP1
provenance, dataset roots, manifest hashes, and audit-report hashes. It does
not include raw dataset contents.

## Windows, PowerShell, Linux, and Kaggle

On Windows without `make`, run the Python commands listed in the `Makefile` or
use WSL2. On Kaggle/Linux, `make reproduce-small` is the expected reviewer
command. If an SP1 toolchain is unavailable, keep `RUN_HEAVY_SP1` unset; the
fast path still validates compact proof provenance.
