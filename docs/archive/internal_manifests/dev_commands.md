# Developer Commands

## Quick Smoke

```text
python -m compileall zk_offline_dqn scripts tests
```

Equivalent Make target:

```text
make smoke
```

## Unit, Golden, and Negative Tests

```text
python -m unittest discover tests
python -m unittest discover tests/unit
python -m unittest discover tests/golden
python -m unittest discover tests/negative
```

Equivalent Make targets:

```text
make unit
make golden
make negative
```

## CLI Smoke

```text
python -m unittest discover tests/regression
python -m zk_offline_dqn.cli.main --help
python -m zk_offline_dqn.cli.main verify --help
```

Equivalent Make target:

```text
make cli-smoke
```

## Full Regression

```text
python scripts/experiments/run_full_regression.py
```

Equivalent Make target:

```text
make regression
```

## SP1 Python-Side Smoke

```text
python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json
python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke
python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke
python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke
python scripts/experiments/check_sp1_environment.py
```

These commands check Python/SP1 fixture alignment without requiring Rust, Cargo,
or SP1 proof generation.

## Kaggle SP1 Validation

Remote branch mode:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --git-branch cleanup-project-structure
```

Remote branch mode requires the current work to be committed and pushed first.
If the working tree has local edits, use local archive mode:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --use-local-archive
```

Request Rust/SP1 setup and execute on Kaggle:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --use-local-archive --run-sp1-setup --run-sp1-execute
```

Proof is opt-in:

```text
python scripts/experiments/run_phase6_kaggle_validation.py --use-local-archive --run-sp1-setup --run-sp1-execute --run-sp1-prove
```

If the API runner cannot push or retrieve outputs, run the validation manually
inside the Kaggle notebook:

```text
RUN_SP1_SETUP=1
RUN_SP1_EXECUTE=1
RUN_SP1_PROVE=0
python scripts/experiments/kaggle_sp1_validation.py
```

Set `RUN_SP1_PROVE=1` only when requesting proof generation:

```text
RUN_SP1_SETUP=1
RUN_SP1_EXECUTE=1
RUN_SP1_PROVE=1
python scripts/experiments/kaggle_sp1_validation.py
```

Optional Kaggle setup helper:

```text
bash scripts/experiments/setup_sp1_on_kaggle.sh
```

On Kaggle, the setup helper installs Rust if missing, installs native build
prerequisites including protobuf when `apt-get` is available, runs the SP1
installer, and leaves proof disabled unless `RUN_SP1_PROVE=1` is set.

## WSL2/Linux SP1 Fallback

```text
cd zk_backend/td_mvp/sp1
cargo test
cargo run --release -p td-mvp-host -- --execute
RUN_SP1_PROVE=1 cargo run --release -p td-mvp-host -- --prove
```

Proof generation is not part of the default Python regression. Run proof mode
only in an environment with the Rust/SP1 toolchain installed.

## Paper-Facing Reports

Check report sources without running benchmarks:

```text
python scripts/experiments/check_report_sources.py
python -m zk_offline_dqn.cli.main report check-sources
```

Generate deterministic report snapshots from existing outputs:

```text
python scripts/experiments/generate_paper_reports.py
python -m zk_offline_dqn.cli.main report generate
```

Reports are written to:

```text
artifacts/reports/final_ndss/
```

Report generation does not rerun heavy benchmarks and does not rerun SP1
prove. Missing optional values are reported as missing rather than inferred.

## Documentation And Hygiene

Reviewer-facing docs:

```text
README.md
docs/architecture.md
docs/reproducibility.md
docs/sp1_python_alignment.md
docs/archive/internal_manifests/legacy_status.md
docs/archive/internal_manifests/reporting_policy.md
docs/archive/refactor_history/refactor_final_summary.md
```

Migration logs are archived under `docs/archive/refactor_history/`. They are
useful for audit history, but they are not the first docs a reviewer should
read.

## All Default Checks

```text
make all-checks
```

This runs compile smoke, unit, golden, negative, CLI smoke, and the full Python
regression runner.

## Compatibility Notes

- Legacy scripts under `scripts/artifacts_export/` still exist for compatibility.
- The unified CLI is available as `python -m zk_offline_dqn.cli.main`.
- Default Python regression uses `--skip-sp1` benchmark checks where applicable.
- SP1 proof generation is not required for the default Python regression unless
  a developer explicitly runs SP1/Rust proof commands.
