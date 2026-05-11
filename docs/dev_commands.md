# Developer Command Notes

This file keeps local scratch commands out of the repository root.

## Short-Trace Benchmark

```powershell
python scripts/experiments/benchmark_short_trace_update.py `
  --data data/cartpole_dqn_eps010_transitions.pkl `
  --merkle artifacts/cartpole_dqn_eps010_merkle.json `
  --checkpoint models/offline_dqn_with_target_seed42_best.pt `
  --lr 0.001 `
  --target-sync-every 2
```

## Inspect First Short-Trace Step Keys

```powershell
python -c "import json; s=json.load(open('artifacts/benchmarks/short_trace_update/summary.json', encoding='utf-8')); p=s[0]['artifact_path']; d=json.load(open(p, encoding='utf-8')); print(list(d['steps'][0].keys()))"
```

## Week 3 SP1 TD MVP Reproducibility

Run these from WSL2 Ubuntu or another Linux/macOS environment with SP1 installed:

```bash
cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn

python3 scripts/experiments/run_td_mvp_test_vector_negative_tests.py

cd zk_backend/td_mvp/sp1
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
bash run_negative_cases.sh

cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

The benchmark runner writes:

```text
artifacts/benchmarks/sp1_td_mvp/summary.json
artifacts/benchmarks/sp1_td_mvp/benchmark_matrix.csv
artifacts/benchmarks/sp1_td_mvp/summary.md
```

Latest WSL2 TD-1 result:

```text
proving_time_sec = 66.668891
verification_time_sec = 0.088947
proof_size_bytes = 2782588
cycle_count = 365501
all_passed = True
```

If SP1 is not available, use the Python semantic-oracle smoke path:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --skip-sp1
```

## Week 4 SP1 Minibatch TD Smoke

Run these from WSL2 Ubuntu after pulling the minibatch relation changes:

```bash
cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn

python3 scripts/artifacts_export/export_td_mvp_batch_test_vector.py \
  --input zk_backend/test_vectors/td_mvp_case_0.json \
  --out /tmp/td_mvp_batch_size_2.json \
  --batch-size 2

python3 scripts/artifacts_export/verify_td_mvp_test_vector.py \
  --input /tmp/td_mvp_batch_size_2.json

cd zk_backend/td_mvp/sp1
cargo fmt --check
cargo check -p td-mvp-shared -p td-mvp-host
cargo run --release -p td-mvp-host -- --input /tmp/td_mvp_batch_size_2.json --execute
cargo run --release -p td-mvp-host -- --input /tmp/td_mvp_batch_size_2.json --case tamper_batch_claimed_loss_fp --execute --skip-host-precheck
```

Run the full Week 4 benchmark/proof refresh:

```bash
cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

If WSL2 becomes unstable or runs out of memory, prove one accepted case at a time and keep logs on the Windows-mounted workspace:

```bash
cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn
mkdir -p artifacts/benchmarks/sp1_td_mvp/logs

python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-1 \
  2>&1 | tee artifacts/benchmarks/sp1_td_mvp/logs/prove_td1.log

python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-2 \
  2>&1 | tee artifacts/benchmarks/sp1_td_mvp/logs/prove_td2.log

python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-4 \
  2>&1 | tee artifacts/benchmarks/sp1_td_mvp/logs/prove_td4.log

python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove --prove-cases TD-8 \
  2>&1 | tee artifacts/benchmarks/sp1_td_mvp/logs/prove_td8.log
```
