# ZK Backend

This directory is reserved for the future zero-knowledge backend implementation.

The current repository is still a pre-ZK artifact/verifier prototype. The first backend target is intentionally small:

> Merkle membership + Bellman target + SmoothL1 TD loss over a committed offline DQN transition.

The first backend should consume small test vectors exported from the existing Python artifact pipeline.

## Current Contents

```text
zk_backend/
  README.md
  test_vectors/
    README.md
    td_mvp_case_0.json
```

## First MVP Relation

The first ZK backend MVP should verify:

```text
leaf_hash == Hash(Serialize(transition))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## Non-Goals

The first backend MVP does not prove:

```text
full DQN training
neural-network forward pass
argmax action selection
gradient computation
optimizer update
long training traces
recursive proof aggregation
```

## Related Documentation

```text
docs/zk_backend_mvp.md
docs/threat_model.md
docs/backend_choice.md
```