# Artifact Release Manifest

This manifest classifies repository content for release preparation. It is
descriptive and does not move or delete files.

## Source Code Modules

- `zk_offline_dqn/relations/`
- `zk_offline_dqn/verifiers/`
- `zk_offline_dqn/artifacts/`
- `zk_offline_dqn/backends/sp1/`
- `zk_offline_dqn/experiments/`
- `zk_offline_dqn/cli/`

These are active source modules and should be reviewed as code.

## Tests

- `tests/unit/`
- `tests/golden/`
- `tests/negative/`
- `tests/regression/`

Tests should be committed with the source changes they validate.

## Paper Files

- `paper/main.tex`
- `paper/sections/*.tex`
- `paper/refs.bib`
- `paper/README.md`
- `paper/CHANGELOG.md`

Paper claims are scoped to relation-level verification and the TD MVP SP1
canonical-vector proof.

## Final Reports

Commit candidate reports:

- `artifacts/reports/final_ndss/paper_numbers.json`
- `artifacts/reports/final_ndss/benchmark_summary.csv`
- `artifacts/reports/final_ndss/tamper_summary.csv`
- `artifacts/reports/final_ndss/sp1_status.json`
- `artifacts/reports/final_ndss/benchmark_snapshot.md`
- `artifacts/reports/provenance/sp1/kaggle_sp1_validation_summary.json`
- `artifacts/reports/provenance/sp1/kaggle_sp1_setup_summary.json`

These files are generated but reviewer-facing and should remain trackable.

## Canonical Fixtures

Canonical fixtures include:

- `zk_backend/test_vectors/td_mvp_case_0.json`
- regression-critical JSON artifacts under `artifacts/`
- benchmark fixtures intentionally used by regression or report provenance
- committed benchmark summaries under `artifacts/benchmarks/`

Before release, review untracked canonical-looking artifacts and decide whether
they should be added or left local.

The Phase 11B artifact decision manifest records those decisions by path group:

```text
docs/archive/internal_manifests/artifact_decision_manifest.md
```

In short, manifest-listed fixtures and final-report provenance fixtures are
commit candidates; large historical benchmark output folders are archive-later
candidates; local Kaggle output trees and Python-smoke outputs remain ignored.

## Generated Local Outputs

Do not commit:

- Python cache directories
- `artifacts/full_regression/`
- `artifacts/benchmarks/*_python_smoke/`
- temporary regression summaries unless explicitly wanted for the release
- temporary logs

## Kaggle Local Outputs

Do not commit:

- `kaggle_phase6_zkp_drl/`
- `kaggle_phase6_zkp_drl_backup*/`
- `kaggle_phase6_outputs/` after SP1 summaries are copied into
  `artifacts/reports/provenance/sp1/`
- local Kaggle archive zip files
- notebook output trees copied back from Kaggle

## SP1 Backend Files

`zk_backend/td_mvp/sp1/` is the Rust SP1 backend. Do not edit or reformat these
files during release preparation unless there is a separate approved backend
change.

## Legacy Compatibility Scripts

Keep:

- `scripts/artifacts_export/`
- `scripts/zk_proofs/`

They are retained for compatibility and reproducibility. Do not delete them
without a separate usage audit.
