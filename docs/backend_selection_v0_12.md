# Backend Selection v0.12

## 1. Purpose

This document records the first concrete backend selection for the TD MVP zero-knowledge backend.

The project has already reached the following pre-backend milestones:

```text
v0.8  - ZK backend MVP design
v0.9  - TD MVP backend test vector
v0.10 - TD MVP test vector verifier and negative tests
v0.11 - zkVM backend skeleton
```

The next step is to choose one backend for the first implementation attempt.

## 2. Decision

The first backend target will be:

```text
SP1
```

This decision means that the first real ZK backend milestone should attempt to port the TD MVP relation into an SP1 guest program and use an SP1 host program to generate and verify a proof.

## 3. Why SP1 First

SP1 is selected first because the current TD MVP relation is a good fit for a zkVM workflow.

The relation contains:

```text
SHA-256 leaf hashing
Merkle path verification
fixed-point integer arithmetic
conditional Bellman target logic
conditional SmoothL1 loss logic
public/private input separation
standalone test-vector compatibility
```

These are easier to prototype in a zkVM than in a hand-written arithmetic circuit.

SP1 also fits the current project structure because the repository already has:

```text
zk_backend/test_vectors/td_mvp_case_0.json
scripts/artifacts_export/verify_td_mvp_test_vector.py
scripts/experiments/run_td_mvp_test_vector_negative_tests.py
zk_backend/td_mvp/host/README.md
zk_backend/td_mvp/guest/README.md
```

The SP1 guest can initially mirror the standalone Python verifier logic in Rust.

## 4. Why Not RISC Zero First

RISC Zero remains a strong candidate and should not be discarded.

However, choosing both RISC Zero and SP1 at the same time would slow down the first implementation milestone. The immediate research goal is to get one minimal TD MVP proof working, not to compare zkVM ecosystems yet.

RISC Zero can be revisited later as a comparison backend after the SP1 TD MVP is working.

## 5. Why Not Noir, Circom, or Halo2 First

Noir, Circom, and Halo2 remain relevant future options, but they are not selected for the first backend attempt.

Reason:

```text
The TD MVP relation is still evolving.
The project needs fast iteration before constraint optimization.
Merkle hashing and branching are easier to prototype in a zkVM.
A custom circuit would require more manual constraint design.
```

A circuit backend may become useful later after the relation has stabilized and proof-size/proving-time optimization becomes more important.

## 6. Initial SP1 Scope

The first SP1 milestone should prove only:

```text
leaf_hash == Hash(Serialize(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

The input should be derived from:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

## 7. Initial SP1 Non-Goals

The first SP1 backend should not prove:

```text
full DQN training
neural-network forward pass
argmax action selection
gradient computation
optimizer update
short trace chaining
recursive proof aggregation
```

The goal is to prove the smallest backend-ready TD arithmetic and membership relation first.

## 8. Expected SP1 Directory Layout

The future implementation should be organized under:

```text
zk_backend/td_mvp/sp1/
  README.md
  host/
  guest/
```

A possible Rust workspace layout is:

```text
zk_backend/td_mvp/sp1/
  Cargo.toml
  host/
    Cargo.toml
    src/main.rs
  guest/
    Cargo.toml
    src/main.rs
```

This exact layout may be adjusted after checking the current SP1 template and installation workflow.

## 9. Acceptance Criteria for the Next Implementation Milestone

The next implementation milestone should be considered successful if:

```text
SP1 project skeleton builds locally
host can load or embed the TD MVP test vector
guest can verify the TD MVP relation
valid test vector produces a proof
proof verifies successfully
tampered input is rejected or fails proving
proving time is recorded
verification time is recorded
proof size is recorded
```

## 10. Decision Summary

The first backend implementation target is:

```text
SP1
```

RISC Zero remains the main alternative backend for later comparison.

Noir, Circom, and Halo2 remain future optimization or circuit-oriented options.

This decision moves the project from backend-agnostic planning toward the first real ZK proof implementation path.