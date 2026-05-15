# Developer Commands

## Quick Smoke

```text
python -m compileall zk_offline_dqn scripts src tests
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

```text
python scripts/experiments/run_phase6_kaggle_validation.py
```

If the API runner cannot push or retrieve outputs, run the validation manually
inside the Kaggle notebook:

```text
python scripts/experiments/kaggle_sp1_validation.py
```

Optional Kaggle setup helper:

```text
bash scripts/experiments/setup_sp1_on_kaggle.sh
```

## WSL2/Linux SP1 Fallback

```text
cd zk_backend/td_mvp/sp1
cargo test
cargo run --release -p td-mvp-host -- --execute
RUN_SP1_PROVE=1 cargo run --release -p td-mvp-host -- --prove
```

Proof generation is not part of the default Python regression. Run proof mode
only in an environment with the Rust/SP1 toolchain installed.

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
