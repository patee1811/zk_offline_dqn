# ZK Backend

This directory tracks the path from the current Python verifier prototype to a real proving backend.

Current status:

- Backend target: **SP1**.
- Implemented: TD MVP test vectors, distinct minibatch TD, forward-TD MLP,
  tiny one-step SGD, a Rust SP1 workspace, guest relation checks, host proof
  generation/verification, and tamper rejection checks.
- Achieved result: the full Kaggle SP1 benchmark completed distinct replay
  TD-1/2/4/8 proofs, CartPole forward-TD batch 1, MountainCar forward-TD batch
  1, and CartPole one-step SGD tiny batch 1 with Python/SP1 agreement.
- Current proof metrics are in `artifacts/benchmarks/final_ndss/summary.md`.
- Python oracle and SP1 execution tests pass for batch structure, arithmetic,
  commitment, model-weight, activation, ReLU mask, argmax, selected target
  value, claimed-loss, gradient, delta, learning-rate, and post-model tamper
  cases.

## First Backend Statement

The first backend should prove only the TD MVP relation:

```text
leaf == SerializeTransition(transition)
leaf_hash == SHA256(CanonicalLeafEncoding(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + (gamma_fp * q_target_max_fp) // fp_scale
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

The distinct minibatch extension proves the same per-item checks for each item and adds:

```text
batch_size == len(items)
batch_mode == distinct
leaf_indices are public, ordered, and duplicate-free
items[i].index == leaf_indices[i]
claimed_batch_loss_fp == floor(sum(item.loss_fp) / batch_size)
```

The compatibility test vector is:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

The Python reference verifier is:

```text
scripts/artifacts_export/verify_td_mvp_test_vector.py
```

## Layout

```text
zk_backend/
  README.md
  test_vectors/
    README.md
    td_mvp_case_0.json
  td_mvp/
    README.md
    sp1/                       concrete SP1 backend
      README.md
      toolchain.md
      Cargo.toml
      host/
      guest/
      shared/
```

## Implemented Scope

The backend scope is relation-level SP1 proofs for distinct
minibatch TD, forward-TD MLP, and one micro-scale SGD update. The paper should
use these results as relation-level evidence, not as a full training-trace
claim.

Canonical package summary:

```text
artifacts/benchmarks/final_ndss/summary.md
```

Refresh command after any future relation change:

```bash
python3 scripts/experiments/benchmark_distinct_td_sp1.py --prove
python3 scripts/experiments/benchmark_forward_td_mlp_sp1.py --prove
python3 scripts/experiments/benchmark_mountaincar_forward_td_sp1.py --prove
python3 scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --prove
python3 scripts/experiments/run_final_ndss_regression.py
```

Non-goals for this backend milestone: full DQN training, Adam optimizer state,
long traces, target-network synchronization over a full run, model selection,
and recursive aggregation.
