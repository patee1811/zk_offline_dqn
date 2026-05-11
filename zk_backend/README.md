# ZK Backend

This directory tracks the path from the current Python verifier prototype to a real proving backend.

Current status:

- Backend target: **SP1**.
- Implemented: one TD MVP JSON test vector, a Rust SP1 workspace, guest relation checks, host proof generation/verification, and initial tamper rejection checks.
- Current smoke result: a valid TD MVP proof verifies, and the initial SP1 negative cases reject as expected.

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

1. Add benchmark/reproducibility scripts around the SP1 host.
2. Expand SP1 negative tests to mirror the full Python TD MVP tamper set.
3. Record stable proving/verification/proof-size outputs as artifacts.
4. Package instructions for clean reproduction from a fresh WSL2 Ubuntu environment.

Non-goals for this first backend milestone: full DQN training, neural-network forward proof, argmax proof, gradient proof, optimizer proof, long traces, and recursive aggregation.
