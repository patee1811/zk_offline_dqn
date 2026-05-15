# Reproducibility

This repository supports relation-level verification for selected offline DQN
artifacts. It does not claim a proof of full DQN training.

## Python Regression

Run the default Python regression:

```text
python scripts/experiments/run_full_regression.py
```

The regression summary is written to:

```text
artifacts/regression_summary.json
artifacts/regression_summary.md
```

## SP1 Python-Side Smoke

These commands exercise the Python oracle paths used to align with SP1 inputs
without requiring Rust, Cargo, or proof generation:

```text
python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json
python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke
python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke
python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke
python scripts/experiments/check_sp1_environment.py
```

## Kaggle SP1 Validation

Remote branch mode requires the current branch to be committed and pushed:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --git-branch cleanup-project-structure --run-sp1-setup --run-sp1-execute
```

Local archive mode packages the current workspace and is appropriate when local
changes have not been pushed:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --use-local-archive --run-sp1-setup --run-sp1-execute
```

SP1 proof generation is opt-in:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --use-local-archive --run-sp1-setup --run-sp1-execute --run-sp1-prove
```

The validated Phase 6C proof claim is scoped only to the TD MVP SP1 backend
using `zk_backend/test_vectors/td_mvp_case_0.json`. It does not cover full DQN
training, all relations, long traces, or recursive aggregation.

## Paper-Facing Reports

Generate report snapshots from existing outputs:

```text
python scripts/experiments/check_report_sources.py
python scripts/experiments/generate_paper_reports.py
python -m zk_offline_dqn.cli.main report check-sources
python -m zk_offline_dqn.cli.main report generate
```

Generated reports are written to:

```text
artifacts/reports/final_ndss/
```

The report generator does not run heavy benchmarks and does not rerun SP1
prove. Missing optional values are represented as `missing`, `not_run`, or
`null` with source provenance rather than inferred.

## Interpreting Missing Values

- `missing`: the expected source file was not available.
- `not_run`: the source existed but did not contain a completed run for that
  field.
- `null`: a field is intentionally unavailable, such as a proof artifact path
  not emitted by the host command.

Every paper-facing number in `paper_numbers.json` includes provenance pointing
to the source path and field used.

## Paper Claim Checks

Check paper-facing wording and scoped number provenance:

```text
python scripts/experiments/check_paper_claims.py
python scripts/experiments/check_paper_numbers_against_final_ndss.py
```

These checks do not compile LaTeX and do not run SP1 proof generation.

## Repository Hygiene

Generated Kaggle work folders, local Kaggle outputs, Python caches, local
archive zip files, and Python-only smoke benchmark directories are ignored by
`.gitignore`.

The final report snapshot under `artifacts/reports/final_ndss/` is intentionally
left trackable. See `docs/reporting_policy.md` for the commit policy.
