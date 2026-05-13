# Final NDSS Reproduction Notes

Run commands from the repository root.

## Fast Python Smoke Path

```powershell
python scripts/experiments/run_full_regression.py
python scripts/experiments/run_final_ndss_regression.py
```

The smoke path verifies Python semantics and regenerates the final aggregate from existing component summaries.

## Component Smoke Commands

```powershell
python scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke
python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke
python scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/second_env_mountaincar_python_smoke
python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke
python scripts/experiments/run_final_ndss_regression.py
```

## SP1 / WSL2 Ubuntu / Kaggle Path

Install the SP1 toolchain first, then run:

```bash
cd /path/to/zk_offline_dqn
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
python3 scripts/experiments/run_final_ndss_regression.py
```

For the distinct-TD benchmark, accepted cases can be proved one at a time:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-1
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-2
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-4
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove --prove-cases TD-8
```

Expected aggregate outputs:

```text
artifacts/benchmarks/final_ndss/summary.json
artifacts/benchmarks/final_ndss/benchmark_matrix.csv
artifacts/benchmarks/final_ndss/tamper_matrix.csv
artifacts/benchmarks/final_ndss/summary.md
artifacts/benchmarks/final_ndss/reproduction.md
```
