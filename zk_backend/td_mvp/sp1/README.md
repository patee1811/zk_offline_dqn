# SP1 TD MVP Backend Skeleton

This directory is reserved for the first SP1 implementation of the TD MVP relation.

The selected backend for the first concrete ZK implementation is:

```text
SP1
```

This directory does not yet contain a working SP1 proof. It defines the intended layout and implementation contract before adding the actual SP1 toolchain and Rust workspace.

## Goal

The first SP1 backend should prove the standalone TD MVP relation already validated by:

```text
scripts/artifacts_export/verify_td_mvp_test_vector.py
scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```

The input compatibility target is:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

## Target Relation

The SP1 guest should verify:

```text
leaf_hash == Hash(Serialize(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## Intended Layout

```text
zk_backend/td_mvp/sp1/
  README.md
  host/
    README.md
  guest/
    README.md
  shared/
    README.md
```

A later implementation milestone may replace this documentation-only skeleton with a real Rust/SP1 workspace, for example:

```text
zk_backend/td_mvp/sp1/
  Cargo.toml
  host/
    Cargo.toml
    src/main.rs
  guest/
    Cargo.toml
    src/main.rs
  shared/
    Cargo.toml
    src/lib.rs
```

The exact layout should follow the current SP1 template when the toolchain is installed.

## Host Responsibilities

The SP1 host should:

```text
load or embed zk_backend/test_vectors/td_mvp_case_0.json
validate schema_version
convert JSON into typed Rust input structs
separate public inputs from private witness
send the input to the SP1 guest
run proof generation
verify the proof
record proving time
record verification time
record proof size
```

## Guest Responsibilities

The SP1 guest should:

```text
receive typed TD MVP input
recompute leaf hash
recompute Merkle root from Merkle path
recompute Bellman target
recompute TD error
recompute SmoothL1 loss
assert claimed target consistency
assert claimed loss consistency
commit public outputs if required by SP1
```

## Shared Responsibilities

The shared module should eventually contain Rust data structures and pure helper functions used by host and guest, such as:

```text
TD MVP input structs
Merkle path structs
fixed-point arithmetic helpers
SmoothL1 helper
leaf encoding helper
hashing helper
```

## Initial Non-Goals

The first SP1 implementation should not prove:

```text
full DQN training
neural-network forward pass
argmax action selection
gradient computation
optimizer update
short trace chaining
recursive aggregation
```

## Acceptance Criteria for the First Real SP1 Milestone

A later implementation milestone should be considered successful if:

```text
SP1 project builds locally
host loads or embeds the TD MVP test vector
guest verifies the TD MVP relation
valid test vector produces a proof
proof verifies successfully
tampered input is rejected or fails proof generation
proving time is recorded
verification time is recorded
proof size is recorded
```

## Toolchain Notes

The planned SP1 setup notes are documented in:

```text
zk_backend/td_mvp/sp1/toolchain.md
```

The first SP1 implementation should be developed on Linux/macOS or WSL2 Ubuntu rather than native Windows PowerShell.

## Related Files

```text
zk_backend/td_mvp/sp1/toolchain.md
docs/backend_selection_v0_12.md
docs/backend_choice.md
docs/zk_backend_mvp.md
zk_backend/td_mvp/README.md
zk_backend/test_vectors/td_mvp_case_0.json
scripts/artifacts_export/verify_td_mvp_test_vector.py
scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```