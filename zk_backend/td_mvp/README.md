# TD MVP zkVM Backend Skeleton

This directory is reserved for the first zkVM backend implementation of the TD MVP relation.

The current repository already contains:

```text
zk_backend/test_vectors/td_mvp_case_0.json
scripts/artifacts_export/verify_td_mvp_test_vector.py
scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```

The goal of this directory is to define the future host/guest split before implementing a concrete proving backend such as RISC Zero or SP1.

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

## Host / Guest Split

The intended zkVM structure is:

```text
host:
  - load JSON test vector
  - split public inputs and private witness
  - pass inputs to guest
  - run prover
  - receive proof/receipt
  - verify proof/receipt
  - report proving time, verification time, and proof size

guest:
  - parse or receive typed TD MVP input
  - recompute leaf hash
  - recompute Merkle root
  - recompute Bellman target
  - recompute TD error
  - recompute SmoothL1 loss
  - assert claimed target/loss consistency
  - commit public outputs if required by backend
```

## Backend Candidates

The current recommended first backend is one of:

```text
RISC Zero
SP1
```

A circuit backend such as Noir, Circom, or Halo2 may be considered later after the relation is stable.

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
docs/zk_backend_mvp.md
docs/threat_model.md
docs/backend_choice.md
zk_backend/test_vectors/td_mvp_case_0.json
scripts/artifacts_export/verify_td_mvp_test_vector.py
scripts/experiments/run_td_mvp_test_vector_negative_tests.py
```