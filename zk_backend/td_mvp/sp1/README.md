# SP1 TD MVP

SP1 is the selected first proving backend.

This directory contains the first SP1 TD MVP workspace:

```text
zk_backend/td_mvp/sp1/
  Cargo.toml
  host/
    Cargo.toml
    src/main.rs
  guest/
    Cargo.toml
    src/main.rs
  shared/
    Cargo.toml
    src/lib.rs
  run_negative_cases.sh
```

## Compatibility Target

Use the existing vector as the first input target:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

Use the Python verifier as the source of current semantics:

```text
scripts/artifacts_export/verify_td_mvp_test_vector.py
```

## Implementation Checklist

1. Confirm SP1 works on Linux/macOS or WSL2 Ubuntu.
2. Generate a minimal SP1 project outside the repo and prove/verify hello world.
3. Create the repo workspace under this directory.
4. Add typed public/private input structs in `shared`.
5. Implement guest checks for transition-to-leaf encoding, leaf hash, Merkle path, Bellman target, TD error, and SmoothL1 loss.
6. Implement host loading for `td_mvp_case_0.json`.
7. Generate and verify a proof.
8. Print proving time, verification time, and proof size.
9. Add tampered input checks matching the Python negative tests in `tamper_checklist.md`.

Run from WSL2 Ubuntu:

```bash
cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn/zk_backend/td_mvp/sp1
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
```

Run the initial SP1 negative checks:

```bash
bash run_negative_cases.sh
```

Run the Week 3 benchmark/reproducibility snapshot from the repository root:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

This writes:

```text
artifacts/benchmarks/sp1_td_mvp/summary.json
artifacts/benchmarks/sp1_td_mvp/benchmark_matrix.csv
artifacts/benchmarks/sp1_td_mvp/summary.md
```

The runner checks the Python verifier as the semantic oracle and the SP1 host as the proving backend over the same valid/tampered TD MVP cases. Week 4 extends the same guest entrypoint to accept `td_mvp_batch_test_vector_v1` inputs for TD-2/4/8 minibatch checks.

Generate and execute a standalone TD-2 minibatch fixture:

```bash
cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn
python3 scripts/artifacts_export/export_td_mvp_batch_test_vector.py \
  --input zk_backend/test_vectors/td_mvp_case_0.json \
  --out /tmp/td_mvp_batch_size_2.json \
  --batch-size 2

cd zk_backend/td_mvp/sp1
cargo run --release -p td-mvp-host -- \
  --input /tmp/td_mvp_batch_size_2.json \
  --execute
```

Run the extended negative checks:

```bash
bash run_negative_cases.sh
```

The extended suite covers:

- schema version mismatch;
- fixed-point rounding mismatch;
- wrong `done` branch semantics;
- wrong leaf index;
- wrong Merkle path order;
- target-network value tamper;
- batch aggregation tamper;
- batch item index/path/value/rounding tamper.

## Current Proof Results

The latest full benchmark run was generated on Kaggle at
`2026-05-12T12:37:34.964280+00:00`.

```text
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
```

Initial negative cases:

```text
valid_control accepted
tamper_reward rejected
tamper_done rejected
tamper_transition_obs rejected
tamper_leaf_encoding rejected
tamper_merkle_path rejected
tamper_q_target_max_fp rejected
tamper_claimed_target_fp rejected
tamper_claimed_loss_fp rejected
tamper_leaf_hash rejected
tamper_td_error_fp rejected
all_sp1_negative_cases_passed = true
```

## Week 4 Minibatch Scope

Implemented relation checks:

- multiple Merkle memberships through `private.items[]`;
- per-sample TD target, TD error, and SmoothL1 loss;
- public `batch_size`;
- public `claimed_batch_loss_fp`;
- integer batch-average loss `sum(loss_fp) // batch_size`;
- batch aggregation negative cases for claimed loss, batch size, item loss, and item index.

The committed benchmark runner can generate TD-2/4/8 fixtures from the
canonical single-transition vector.

Current proof results:

- TD-1 proof completed on Kaggle: `142.324547s` prove, `0.157464s` verify, `2782625` proof bytes, `382915` cycles.
- TD-2 proof completed on Kaggle: `154.923089s` prove, `0.157712s` verify, `2787687` proof bytes, `725309` cycles.
- TD-4 proof completed on Kaggle: `188.501940s` prove, `0.155969s` verify, `2795631` proof bytes, `1425790` cycles.
- TD-8 proof completed on Kaggle: `275.077262s` prove, `0.157424s` verify, `2812327` proof bytes, `2834727` cycles.

## Week 5 Locked Scope

Week 5 locks the backend implementation at SP1 TD-1/2/4/8 plus Python
pre-ZK one-step and short-trace extensions. Do not add large backend features
before the paper rewrite. The artifact package, final claim, benchmark table,
tamper table, and limitation notes are in:

```text
docs/week5_artifact_package.md
```

## Non-Goals

The first SP1 milestone should not prove neural-network forward passes, argmax action selection, gradients, optimizer updates, short traces, or recursive aggregation.
