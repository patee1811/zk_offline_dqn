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

Python-only distinct minibatch benchmark smoke, for machines without SP1:

```powershell
python scripts/experiments/benchmark_distinct_td_sp1.py `
  --skip-sp1 `
  --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke
```

Final Phase E artifact aggregate:

```powershell
python scripts/experiments/run_final_ndss_regression.py
python scripts/experiments/check_paper_numbers_against_final_ndss.py
```

Expected outputs:

```text
artifacts/benchmarks/final_ndss/summary.json
artifacts/benchmarks/final_ndss/benchmark_matrix.csv
artifacts/benchmarks/final_ndss/tamper_matrix.csv
artifacts/benchmarks/final_ndss/summary.md
artifacts/benchmarks/final_ndss/reproduction.md
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

Full Phase A distinct minibatch SP1 benchmark/proof refresh from the repository root:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
```

Full Phase E SP1 refresh from the repository root:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
python3 scripts/experiments/run_final_ndss_regression.py
```

Latest Kaggle full-roadmap run:

```text
kernel = https://www.kaggle.com/code/nypate9999/zk-offline-dqn-final-roadmap-run
dataset = nypate9999/zk-offline-dqn-workspace-final-ndss
status = COMPLETE
ROADMAP_KAGGLE_RUN_COMPLETED = True
```

If the full run is unstable, prove one accepted case at a time:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-1
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-2
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-4
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-8
```

Legacy repeated-transition benchmark, kept for comparison only:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
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
docs/current_benchmark_snapshot.md
artifacts/benchmarks/sp1_td_mvp/summary.md
artifacts/benchmarks/sp1_td_mvp/benchmark_matrix.csv
artifacts/benchmarks/distinct_td_sp1/summary.md
artifacts/benchmarks/distinct_td_sp1/benchmark_matrix.csv
artifacts/benchmarks/final_ndss/summary.md
artifacts/benchmarks/final_ndss/benchmark_matrix.csv
artifacts/benchmarks/final_ndss/tamper_matrix.csv
```
