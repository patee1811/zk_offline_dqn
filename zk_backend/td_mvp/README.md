# TD MVP zkVM Backend Skeleton

## v0.12 Backend Decision

The first concrete backend implementation target is:

```text
SP1
```

RISC Zero remains the main alternative backend for a later comparison milestone.

The decision rationale is documented in:

```text
docs/backend_selection_v0_12.md
```

## Purpose

This directory is reserved for the first zkVM backend implementation of the TD MVP relation.

The current repository already contains:

```text
zk_backend/test_vectors/td_mvp_case_0.json
scripts/artifacts_export/verify_td_mvp_test_vector.py
scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```

The goal of this directory is to define the future host/guest split before implementing a concrete proving backend with SP1.

This skeleton does not yet generate a zero-knowledge proof.

## Target Relation

The first backend MVP should verify:

```text
leaf_hash == Hash(Serialize(transition))
MerkleVerify(leaf_hash, merkle_path, dataset_root) == true
target_fp == reward_fp if done else reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp == q_online_action_fp - target_fp
loss_fp == SmoothL1(td_error_fp)
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## Input Contract

The backend should consume:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

The test vector contains:

```text
schema_version
source
statement
public
private
relation
```

## Public Inputs

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

## Private Witness

```text
transition
leaf
leaf_hash
merkle_path
td_witness
```

The `td_witness` contains:

```text
q_online_action_fp
next_action_online
q_target_max_fp
target_fp
td_error_fp
loss_fp
```

## Host / Guest Split

The intended zkVM structure is:

```text
host:
  - load JSON test vector
  - validate schema_version
  - split public inputs and private witness
  - serialize inputs into the SP1-compatible input format
  - pass inputs to the guest
  - run prover
  - receive proof
  - verify proof
  - report proving time, verification time, and proof size

guest:
  - parse or receive typed TD MVP input
  - recompute leaf hash
  - recompute Merkle root
  - recompute Bellman target
  - recompute TD error
  - recompute SmoothL1 loss
  - assert claimed target/loss consistency
  - commit public outputs if required by SP1
```

## Backend Candidates

The selected first backend is:

```text
SP1
```

The main alternative backend is:

```text
RISC Zero
```

A circuit backend such as Noir, Circom, or Halo2 may be considered later after the relation is stable.

## Initial SP1 Scope

The first SP1 implementation should prove only the standalone TD MVP relation:

```text
Merkle membership
Bellman target
TD error
SmoothL1 TD loss
claimed target/loss consistency
```

It should start from the existing test vector:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

## SP1 Skeleton

The initial SP1 backend skeleton is documented in:

```text
zk_backend/td_mvp/sp1/README.md
zk_backend/td_mvp/sp1/host/README.md
zk_backend/td_mvp/sp1/guest/README.md
zk_backend/td_mvp/sp1/shared/README.md
```

This skeleton does not yet install SP1 or generate a proof.

## Acceptance Criteria for the First SP1 Implementation

The first SP1 implementation milestone should be considered successful if:

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

## Non-Goals

This skeleton does not prove:

```text
full DQN training
neural-network forward pass
argmax action selection
gradient computation
optimizer update
long training traces
recursive proof aggregation
```

## Related Files

```text
zk_backend/td_mvp/sp1/README.md
docs/zk_backend_mvp.md
docs/threat_model.md
docs/backend_choice.md
docs/backend_selection_v0_12.md
zk_backend/test_vectors/td_mvp_case_0.json
scripts/artifacts_export/verify_td_mvp_test_vector.py
scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```