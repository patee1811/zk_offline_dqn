# Developer Commands

This file keeps reproducibility commands in one place. Run commands from the
repository root unless another directory is specified.

## Python Regression

```powershell
python scripts/experiments/run_full_regression.py
```

Expected result:

```text
all_regression_passed = True
```

Reports:

```text
artifacts/regression_summary.json
artifacts/regression_summary.md
artifacts/full_regression/*.stdout.txt
artifacts/full_regression/*.stderr.txt
```

## TD MVP Semantic Oracle

```powershell
python scripts/artifacts_export/verify_td_mvp_test_vector.py
python scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```

Python-only benchmark smoke, for machines without SP1:

```powershell
python scripts/experiments/benchmark_sp1_td_mvp.py `
  --skip-sp1 `
  --out-dir artifacts/benchmarks/sp1_td_mvp_python_smoke
```

## SP1 Backend

Run these on Linux, macOS, WSL2 Ubuntu, or Kaggle with SP1 installed:

```bash
cd zk_backend/td_mvp/sp1
cargo check -p td-mvp-shared -p td-mvp-host
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
bash run_negative_cases.sh
```

Full SP1 benchmark/proof refresh from the repository root:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

If the full run is unstable, prove one accepted case at a time:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-1
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-2
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-4
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-8
```

## Short-Trace Benchmark

```powershell
python scripts/experiments/benchmark_short_trace_update.py `
  --data data/cartpole_dqn_eps010_transitions.pkl `
  --merkle artifacts/cartpole_dqn_eps010_merkle.json `
  --checkpoint models/offline_dqn_with_target_seed42_best.pt `
  --lr 0.001 `
  --target-sync-every 2
```

## Canonical Status Files

```text
docs/week5_artifact_package.md
docs/current_benchmark_snapshot.md
artifacts/benchmarks/sp1_td_mvp/summary.md
artifacts/benchmarks/sp1_td_mvp/benchmark_matrix.csv
```
