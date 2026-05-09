# SP1 Guest Skeleton

No guest implementation exists yet.

The future guest should enforce the TD MVP relation:

```text
leaf_hash == Hash(Serialize(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + (gamma_fp * q_target_max_fp) // fp_scale
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

Current arithmetic convention:

```text
fp_scale = 1000
gamma_fp = 990
loss_type = smooth_l1
FixedPointMul(a, b, scale) = (a * b) // scale
```

SmoothL1 convention:

```text
if abs(td_error_fp) < fp_scale:
    loss_fp = (abs(td_error_fp) * abs(td_error_fp)) // (2 * fp_scale)
else:
    loss_fp = abs(td_error_fp) - fp_scale // 2
```

The first guest should not prove neural-network forward semantics, gradients, optimizer updates, or training traces.
