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

Run the distinct replay minibatch benchmark/reproducibility snapshot
from the repository root:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
```

This writes:

```text
artifacts/benchmarks/distinct_td_sp1/summary.json
artifacts/benchmarks/distinct_td_sp1/benchmark_matrix.csv
artifacts/benchmarks/distinct_td_sp1/summary.md
```

The runner checks the Python verifier as the semantic oracle and the SP1 host
as the proving backend over the same valid/tampered TD MVP cases. The
fixtures use distinct committed replay transitions with public ordered
`leaf_indices`; duplicate-index, wrong-index, swapped-order, item-loss,
claimed-average, and Merkle path-order tampers are rejected.

The legacy repeated-transition runner remains available for comparison:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

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

```text
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
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

## Distinct Minibatch Scope

Implemented relation checks:

- multiple Merkle memberships through `private.items[]`;
- public ordered `leaf_indices`;
- distinct index checks for `batch_mode == distinct`;
- item order checks against public `leaf_indices`;
- Merkle path metadata continuity checks;
- per-sample TD target, TD error, and SmoothL1 loss;
- public `batch_size`;
- public `claimed_batch_loss_fp`;
- integer batch-average loss `sum(loss_fp) // batch_size`;
- batch aggregation negative cases for claimed loss, batch size, item loss, item index, duplicate index, swapped item order, and path order.

The committed benchmark runner can generate TD-1/2/4/8 fixtures from a
committed replay dataset and Merkle artifact.

Current distinct proof results:

- TD-1 proof completed on Kaggle: `97.955756s` prove, `0.126565s` verify, `2783869` proof bytes, `385048` cycles.
- TD-2 proof completed on Kaggle: `120.669043s` prove, `0.127258s` verify, `2788227` proof bytes, `730778` cycles.
- TD-4 proof completed on Kaggle: `141.309797s` prove, `0.125481s` verify, `2796699` proof bytes, `1435787` cycles.
- TD-8 proof completed on Kaggle: `202.921645s` prove, `0.126658s` verify, `2812915` proof bytes, `2845813` cycles.

## Implemented Scope

The backend implementation contains SP1 distinct TD, forward-TD MLP, and tiny
one-step SGD relation proofs. The artifact package, final claim,
benchmark table, tamper table, and limitation notes are in:

```text
artifacts/benchmarks/final_ndss/summary.md
```

## Non-Goals

The current SP1 milestone does not prove full DQN training, Adam optimizer
state, long traces, target-network synchronization over a full run, model
selection, or recursive aggregation.
