# SP1 Guest

This crate is the SP1 guest program for the TD MVP relation.

The guest reads a typed `TdMvpInput`, calls `td_mvp_shared::verify_td_mvp`,
and commits the public output. The shared verifier enforces:

```text
leaf == SerializeTransition(transition)
leaf_hash == SHA256(CanonicalLeafEncoding(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + (gamma_fp * q_target_max_fp) // fp_scale
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target/loss or batch-loss public claims match recomputation
```

Supported schemas:

```text
td_mvp_test_vector_v1
td_mvp_batch_test_vector_v1
```

Non-goals for this guest remain neural-network forward semantics, argmax proof,
gradient proof, optimizer proof, trace proof, and recursive aggregation.
