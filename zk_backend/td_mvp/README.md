# TD MVP Backend

This directory defines the smallest backend-ready statement for the project.

The goal is to move one already-tested Python verifier relation into SP1 before attempting larger DQN training statements.

## Current Status

- `zk_backend/test_vectors/td_mvp_case_0.json` exists.
- `scripts/artifacts_export/verify_td_mvp_test_vector.py` verifies the relation in Python.
- `scripts/experiments/run_td_mvp_test_vector_negative_tests.py` checks tampered cases.
- `sp1/` contains documentation skeletons only.

No real zkVM proof is generated yet.

## Statement

Public inputs:

```text
dataset_root
fp_scale
gamma_fp
loss_type
claimed_target_fp
claimed_loss_fp
leaf_index
checkpoint_commitments
```

Private witness:

```text
transition
leaf
leaf_hash
merkle_path
td_witness
```

Required checks:

```text
leaf_hash == Hash(Serialize(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + (gamma_fp * q_target_max_fp) // fp_scale
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## Backend Split

Host:

- load or embed the TD MVP test vector;
- validate schema/version;
- serialize public inputs and private witness for SP1;
- run proving and verification;
- report proving time, verification time, and proof size.

Guest:

- parse typed inputs;
- recompute leaf hash and Merkle root;
- recompute TD target, TD error, and SmoothL1 loss;
- assert claimed output consistency.

Shared:

- Rust structs;
- hashing/Merkle helpers;
- fixed-point helpers;
- SmoothL1 helper.

## Acceptance Criteria

The first real TD MVP backend is successful when:

```text
SP1 project builds
valid test vector produces a proof
proof verifies successfully
tampered witness/input fails
proving time is recorded
verification time is recorded
proof size is recorded
```
