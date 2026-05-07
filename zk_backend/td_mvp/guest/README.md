# TD MVP Guest Skeleton

This directory is reserved for the guest-side code of the future TD MVP zkVM backend.

The guest is the program whose execution should be proven.

## Responsibilities

The guest should verify the TD MVP relation:

```text
leaf_hash == Hash(Serialize(transition))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## Guest Logic

The guest should:

```text
read public inputs
read private witness
recompute leaf hash
recompute Merkle root
check Bellman target
check TD error
check SmoothL1 loss
check claimed target consistency
check claimed loss consistency
halt or fail if any check fails
commit public result if required by the backend
```

## Arithmetic Rules

The guest should use fixed-point integer arithmetic.

The current TD MVP test vector uses:

```text
fp_scale = 1000
gamma_fp = 990
loss_type = smooth_l1
```

The current fixed-point multiplication rule is:

```text
FixedPointMul(a_fp, b_fp, fp_scale) = (a_fp * b_fp) // fp_scale
```

The current SmoothL1 rule is:

```text
if abs(td_error_fp) < fp_scale:
    loss_fp = (abs(td_error_fp) * abs(td_error_fp)) // (2 * fp_scale)
else:
    loss_fp = abs(td_error_fp) - fp_scale // 2
```

## Current Status

No guest implementation is included yet.

This directory is a placeholder for either:

```text
RISC Zero guest code
SP1 guest code
```