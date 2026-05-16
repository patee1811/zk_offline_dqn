# Legacy Status

This document classifies active and compatibility entrypoints after the Phase 8
documentation pass. It is a cleanup plan, not a deletion request.

## Active Library Modules

- `zk_offline_dqn/relations/`
- `zk_offline_dqn/verifiers/`
- `zk_offline_dqn/artifacts/`
- `zk_offline_dqn/backends/sp1/`
- `zk_offline_dqn/experiments/`

These modules are the preferred implementation surface for new work.

## Active CLI

Use:

```text
python -m zk_offline_dqn.cli.main
```

Current active namespaces:

- `verify`
- `benchmark`
- `report`

## Active Regression And Report Scripts

- `scripts/experiments/run_full_regression.py`
- `scripts/experiments/check_report_sources.py`
- `scripts/experiments/generate_paper_reports.py`
- `scripts/experiments/check_sp1_environment.py`
- `scripts/experiments/run_phase6_kaggle_validation.py`
- Python smoke benchmark scripts under `scripts/experiments/`

These scripts are still part of the current workflow.

## Compatibility Wrappers

The scripts under `scripts/artifacts_export/` are compatibility wrappers and
historical exporters/verifiers. Several regression and benchmark paths still
call them directly, so they must not be deleted during cleanup.

The scripts under `scripts/zk_proofs/` are pre-backend Merkle utilities. They
remain useful for explaining and reproducing the committed trajectory setup.

Phase 11C records script-level usage and retirement guidance in:

```text
docs/archive/internal_manifests/legacy_usage_manifest.md
```

Current recommendation: keep all legacy scripts in place. Prefer the unified
CLI for new verification workflows, but do not move or delete old paths until
their direct test, regression, benchmark, backend-doc, and paper users are
migrated.

## Generated Outputs

Local/generated outputs include:

- `kaggle_phase6_zkp_drl/`
- `kaggle_phase6_zkp_drl_backup*/`
- `kaggle_phase6_outputs/`
- `artifacts/archive/manual_review/`
- `artifacts/benchmarks/*_python_smoke/`
- `artifacts/full_regression/`
- Python cache directories

These are not canonical source files.

## Candidate Cleanup Files

Candidate cleanup is limited to ignored, untracked, clearly generated local
outputs. Tracked scripts and fixtures should not be removed without a separate
audit that proves regression, docs, and paper-facing reproduction do not use
them.

## Do Not Delete Yet

- `scripts/artifacts_export/`
- `scripts/zk_proofs/`
- `scripts/experiments/run_full_regression.py`
- `artifacts/` canonical fixtures and benchmark fixtures
- `zk_backend/test_vectors/td_mvp_case_0.json`
- `zk_backend/td_mvp/sp1/`
- `artifacts/reports/final_ndss/`
- `paper/`
