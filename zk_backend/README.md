# ZK Backend

This directory tracks the path from the current Python verifier prototype to a real proving backend.

Current status:

- Backend target: **SP1**.
- Implemented: one TD MVP JSON test vector, a generated minibatch TD test-vector path, a Rust SP1 workspace, guest relation checks, host proof generation/verification, and single/batch tamper rejection checks.
- Current Week 3 result: TD-1 proof verifies with `66.668891s` prove time, `0.088947s` verification time, `2782588` proof bytes, and `365501` cycles. Python and SP1 agree on the valid fixture and all TD MVP tamper cases.
- Week 4 implementation status: the SP1 relation now accepts `td_mvp_batch_test_vector_v1` inputs with `private.items[]`, public `batch_size`, and public `claimed_batch_loss_fp`. Python oracle and SP1 execution smoke tests pass for TD-2/4/8 and batch aggregation tampers. TD-2 proof completed on WSL2; TD-4/8 are currently execution-only on the local machine due to WSL stability/resource limits.

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
    sp1/
      README.md
      toolchain.md
      Cargo.toml
      host/
      guest/
      shared/
```

## Next Milestone

1. Run the extended SP1 TD-2/4/8 benchmark from WSL2 Ubuntu and record prove/verify/proof-size metrics.
2. Add stronger adversarial SP1 cases beyond aggregation, such as fixed-point rounding mismatch and done-branch mismatch.
3. Keep refreshing `artifacts/benchmarks/sp1_td_mvp/` after relation changes with `python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove`.
4. Package instructions for clean reproduction from a fresh WSL2 Ubuntu environment.

Non-goals for this first backend milestone: full DQN training, neural-network forward proof, argmax proof, gradient proof, optimizer proof, long traces, and recursive aggregation.
