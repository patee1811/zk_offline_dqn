# SP1 TD MVP Guest Skeleton

This directory is reserved for the SP1 guest program.

No working SP1 guest is implemented yet.

## Future Role

The guest is the program whose execution should be proven.

It should enforce the TD MVP relation:

```text
leaf_hash == Hash(Serialize(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## Expected Checks

The guest should check:

```text
schema/version compatibility
leaf hash correctness
Merkle root reconstruction
Bellman target correctness
TD error correctness
SmoothL1 TD loss correctness
claimed target equality
claimed loss equality
```

## Arithmetic Rules

The first TD MVP test vector uses:

```text
fp_scale = 1000
gamma_fp = 990
loss_type = smooth_l1
```

Fixed-point multiplication should use:

```text
FixedPointMul(a_fp, b_fp, fp_scale) = (a_fp * b_fp) // fp_scale
```

SmoothL1 should use:

```text
if abs(td_error_fp) < fp_scale:
    loss_fp = (abs(td_error_fp) * abs(td_error_fp)) // (2 * fp_scale)
else:
    loss_fp = abs(td_error_fp) - fp_scale // 2
```

## Non-Goals

The guest should not prove neural-network forward semantics, gradient computation, optimizer updates, or full training traces in the first implementation.