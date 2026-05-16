# Release Checklist

This checklist prepares a reviewable repository state without changing
verifier logic, artifact schemas, benchmark methodology, or Rust/SP1 source.

## Local Python Checks

Run from the repository root:

```text
python -m compileall zk_offline_dqn scripts tests
python -m unittest discover tests
python -m unittest discover tests/regression
python scripts/experiments/run_full_regression.py
```

Expected regression result:

```text
all_regression_passed = True
num_checks = 15
```

## Report Generation

Regenerate paper-facing report snapshots:

```text
python scripts/experiments/check_report_sources.py
python scripts/experiments/generate_paper_reports.py
python -m zk_offline_dqn.cli.main report generate
```

Expected report files:

```text
artifacts/reports/final_ndss/paper_numbers.json
artifacts/reports/final_ndss/benchmark_summary.csv
artifacts/reports/final_ndss/tamper_summary.csv
artifacts/reports/final_ndss/sp1_status.json
artifacts/reports/final_ndss/benchmark_snapshot.md
artifacts/reports/provenance/sp1/kaggle_sp1_validation_summary.json
artifacts/reports/provenance/sp1/kaggle_sp1_setup_summary.json
```

## Paper Claim Checks

Run:

```text
python scripts/experiments/check_paper_claims.py
python scripts/experiments/check_paper_numbers_against_final_ndss.py
```

These checks do not compile LaTeX and do not run SP1 proof generation.

## Optional Kaggle SP1 Proof

Only rerun proof validation when explicitly refreshing the TD MVP SP1 proof:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --use-local-archive --run-sp1-setup --run-sp1-execute --run-sp1-prove
```

The supported claim remains scoped to
`zk_backend/test_vectors/td_mvp_case_0.json`.

## Release Readiness

Run:

```text
python scripts/experiments/check_release_readiness.py
```

The checker validates final report presence, paper-number provenance, scoped
SP1 proof wording, and Git hygiene for generated Kaggle/smoke outputs.

## Artifact Decision Audit

Before staging artifacts, review:

```text
docs/archive/internal_manifests/artifact_decision_manifest.md
```

Recommended commit candidates include manifest-listed fixtures, final
paper-facing reports, and fixture/provenance files cited by the final benchmark
tables. Large historical benchmark output folders and ambiguous helper
artifacts should remain unstaged until the release owner explicitly accepts
them.

## Legacy Script Retirement Audit

Before moving or deleting compatibility scripts, review:

```text
docs/archive/internal_manifests/legacy_usage_manifest.md
```

Current release guidance is to keep `scripts/artifacts_export/` and
`scripts/zk_proofs/` in place. Several old verifier paths are still called by
tests, full regression, benchmark scripts, backend docs, and paper setup text.

## Must Commit

- active Python source under `zk_offline_dqn/`
- active tests under `tests/`
- active experiment/report scripts under `scripts/experiments/`
- reviewer-facing docs under `README.md` and `docs/`
- paper files after claim hardening
- final reports under `artifacts/reports/final_ndss/`
- SP1 proof provenance under `artifacts/reports/provenance/sp1/`
- canonical fixtures intentionally needed for regression/review

## Must Not Commit

- `kaggle_phase6_zkp_drl/`
- `kaggle_phase6_zkp_drl_backup*/`
- `kaggle_phase6_outputs/` after SP1 summaries are copied to
  `artifacts/reports/provenance/sp1/`
- `artifacts/benchmarks/*_python_smoke/`
- `artifacts/full_regression/`
- Python caches and local archive zip files
- temporary Kaggle upload/output trees

## Optional Local Cleanup

Do not run destructive cleanup unless the release owner approves it. Candidate
commands:

```powershell
Remove-Item -Recurse -Force kaggle_phase6_zkp_drl
Remove-Item -Recurse -Force artifacts/benchmarks/*_python_smoke
Remove-Item -Recurse -Force artifacts/full_regression
```

## Final Push And Tag Checklist

1. Review `git status --short`.
2. Review `git diff --stat` and `git diff --name-only`.
3. Decide which untracked canonical artifacts belong in the release.
4. Confirm generated local outputs are ignored or removed.
5. Confirm no legacy script was moved or deleted without a separate retirement
   audit.
6. Commit in coherent groups.
7. Push the branch.
8. After CI passes, tag the release.
