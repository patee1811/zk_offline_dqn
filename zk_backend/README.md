# ZK Backend

This directory tracks the path from the current Python verifier prototype to a real proving backend.

Current status:

- Backend target: **SP1**.
- Implemented today: documentation skeletons and one TD MVP JSON test vector.
- Not implemented yet: Rust workspace, SP1 guest, SP1 host, proof generation, proof verification.

## First Backend Statement

The first backend should prove only the TD MVP relation:

```text
leaf_hash == Hash(Serialize(leaf))
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
      host/README.md
      guest/README.md
      shared/README.md
```

## Next Milestone

1. Install and smoke-test SP1 on Linux/macOS or WSL2 Ubuntu.
2. Create a buildable Rust/SP1 workspace under `zk_backend/td_mvp/sp1/`.
3. Port the TD MVP relation into the guest.
4. Load or embed `td_mvp_case_0.json` in the host.
5. Generate and verify a valid proof.
6. Record proving time, verification time, and proof size.
7. Add tampered-input rejection checks.

Non-goals for this first backend milestone: full DQN training, neural-network forward proof, argmax proof, gradient proof, optimizer proof, long traces, and recursive aggregation.
