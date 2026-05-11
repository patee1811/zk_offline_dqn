# TD MVP Guest

This backend-agnostic placeholder records the guest responsibilities for the TD MVP.

The concrete first implementation target is:

```text
zk_backend/td_mvp/sp1/guest/
```

A future guest should prove execution of the TD MVP relation:

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
