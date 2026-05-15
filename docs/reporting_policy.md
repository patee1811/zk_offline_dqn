# Reporting Policy

This policy separates report artifacts that are useful to commit from local
validation byproducts.

## Commit Candidate Reports

The final paper-facing report snapshot is intended to be reviewable and may be
committed:

```text
artifacts/reports/final_ndss/paper_numbers.json
artifacts/reports/final_ndss/benchmark_summary.csv
artifacts/reports/final_ndss/tamper_summary.csv
artifacts/reports/final_ndss/sp1_status.json
artifacts/reports/final_ndss/benchmark_snapshot.md
```

These files are generated from existing regression, benchmark, and Kaggle SP1
summary outputs. They include provenance and do not introduce new benchmark
methodology.

## Do Not Commit Local Byproducts

Do not commit:

- `kaggle_phase6_zkp_drl/`
- `kaggle_phase6_zkp_drl_backup*/`
- `kaggle_phase6_outputs/`
- `artifacts/benchmarks/*_python_smoke/`
- local Kaggle archive zip files
- Python cache directories
- temporary logs and notebook output trees

## Regeneration

Regenerate reports from the repository root:

```text
python scripts/experiments/check_report_sources.py
python scripts/experiments/generate_paper_reports.py
python -m zk_offline_dqn.cli.main report generate
```

Report generation reads existing outputs only. It does not rerun SP1 prove.
