# ZK Backend

This directory tracks the path from the current Python verifier prototype to a real proving backend.

Current status:

- Backend target: **SP1**.
- Implemented: one TD MVP JSON test vector, a generated minibatch TD test-vector path, a Rust SP1 workspace, guest relation checks, host proof generation/verification, and single/batch tamper rejection checks.
- Week 5 locked result: the full Kaggle SP1 benchmark completed TD-1/2/4/8 proofs with Python/SP1 agreement and all negative cases rejected.
- Latest proof metrics: TD-1 `142.324547s` prove, `0.157464s` verify, `2782625` proof bytes, `382915` cycles; TD-2 `154.923089s` prove, `0.157712s` verify, `2787687` proof bytes, `725309` cycles; TD-4 `188.501940s` prove, `0.155969s` verify, `2795631` proof bytes, `1425790` cycles; TD-8 `275.077262s` prove, `0.157424s` verify, `2812327` proof bytes, `2834727` cycles.
- The SP1 relation accepts `td_mvp_batch_test_vector_v1` inputs with `private.items[]`, public `batch_size`, and public `claimed_batch_loss_fp`. Python oracle and SP1 execution tests pass for TD-2/4/8, batch aggregation tampers, schema mismatch, fixed-point rounding mismatch, wrong done branch, wrong leaf index/path order, and target-network value tamper.

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

The Week 4 minibatch extension proves the same per-item checks for each item and adds:

```text
batch_size == len(items)
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

## Locked Week 5 Scope

The backend scope is locked at SP1 TD and minibatch-TD verification plus
Python pre-ZK one-step and short-trace extensions. Week 6 should write the
paper from these results rather than adding large backend features.

Canonical package summary:

```text
docs/week5_artifact_package.md
```

Refresh command after any future relation change:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

Non-goals for this first backend milestone: full DQN training, neural-network forward proof, argmax proof, gradient proof, optimizer proof, long traces, and recursive aggregation.
