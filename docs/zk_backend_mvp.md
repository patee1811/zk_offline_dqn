# ZK Backend MVP Design

## 1. Scope

This document defines the smallest zero-knowledge backend target for the project.

The repository started as a Python artifact/verifier framework for offline DQN
training from committed trajectories and now includes an SP1 backend for the TD
MVP. The backend should not attempt to prove the full DQN training process.
Instead, it proves a compact RL-specific relation that is supported by the
artifact/verifier design.

The first ZK statement is:

> Given a transition from a committed offline dataset, prove that the transition belongs to the committed dataset and that the Bellman target and SmoothL1 TD loss are computed correctly.

This MVP intentionally excludes full neural-network forward verification, full backpropagation, optimizer update verification, target-network synchronization, and long training traces.

## 2. MVP Statement

For one transition or a small minibatch, the prover shows that:

1. The transition is a member of the committed dataset.
2. The Bellman target is computed correctly.
3. The TD error is computed correctly.
4. The SmoothL1 TD loss is computed correctly.
5. The claimed public loss matches the internally computed loss.

The minimal relation is:

```text
leaf = SerializeTransition(transition)
leaf_hash = SHA256(CanonicalLeafEncoding(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) = true

target_fp = reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
td_error_fp = q_online_action_fp - target_fp
loss_fp = SmoothL1(td_error_fp)

target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

For terminal transitions:

```text
target_fp = reward_fp
```

For non-terminal transitions:

```text
target_fp = reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
```

## 3. Public Inputs

The verifier should know:

```text
dataset_root
fp_scale
gamma_fp
loss_type
claimed_target_fp
claimed_loss_fp
transition_index or leaf_index
```

Optional public inputs:

```text
checkpoint_sha256
online_state_dict_sha256
target_state_dict_sha256
artifact_schema_version
environment_id
```

The model commitments are optional for the first backend MVP because the MVP focuses on TD arithmetic and dataset membership, not full neural-network forward verification.

## 4. Private Witness

The prover should keep private:

```text
transition
leaf
leaf_hash
merkle_path
q_online_action_fp
q_target_max_fp
next_action_online
target_fp
td_error_fp
loss_fp
```

The transition contains:

```text
state
action
reward
next_state
done
```

Depending on the privacy goal, the transition may be fully private while only its Merkle membership is proven.

## 5. Relation

The backend must check the following constraints.

### 5.1 Merkle membership

The serialized transition must hash to a leaf that belongs to the public dataset root.

```text
leaf = SerializeTransition(transition)
leaf_hash = SHA256(CanonicalLeafEncoding(leaf))
MerkleVerify(leaf_hash, merkle_path, dataset_root) = true
```

The canonical serializer is `zk_offline_dqn.zk_specs.serialize_transition_leaf`.
The current leaf encoding is `zk_offline_dqn.merkle.encode_leaf_for_hash`: join
the signed integer leaf fields with commas, then UTF-8 encode the resulting
string before SHA-256 hashing.

### 5.2 Bellman target

If the transition is terminal:

```text
target_fp = reward_fp
```

If the transition is non-terminal:

```text
target_fp = reward_fp + FixedPointMul(gamma_fp, q_target_max_fp, fp_scale)
```

### 5.3 TD error

```text
td_error_fp = q_online_action_fp - target_fp
```

### 5.4 SmoothL1 TD loss

The loss uses the SmoothL1 / Huber form with beta = 1.

In real value form:

```text
if abs(td_error) < 1:
    loss = 0.5 * td_error^2
else:
    loss = abs(td_error) - 0.5
```

In fixed-point form, all operations must be integer operations with explicit scaling and rounding rules.

### 5.5 Claimed output consistency

```text
target_fp == claimed_target_fp
loss_fp == claimed_loss_fp
```

## 6. Fixed-Point Arithmetic

The backend MVP should avoid floating-point arithmetic.

All scalar values should be represented as signed integers with scale:

```text
real_value ≈ value_fp / fp_scale
```

Recommended initial scale:

```text
fp_scale = 1000
```

All multiplication must use explicit rescaling:

```text
FixedPointMul(a_fp, b_fp, fp_scale) = (a_fp * b_fp) // fp_scale
```

The truncation rule must match `zk_offline_dqn/zk_specs.py` and
`scripts/artifacts_export/verify_td_mvp_test_vector.py`.

A later version may replace decimal scaling with power-of-two scaling if it is more convenient for the proving backend.

## 7. Why Not Full DQN Update Yet

The full one-step DQN update is intentionally excluded from the first ZK backend MVP because it requires proving:

```text
neural-network forward pass
action selection
target-network value lookup
SmoothL1 gradient
backpropagation
optimizer semantics
parameter delta
post-update checkpoint commitment
```

The current repository already has a Python verifier for a simplified one-step SGD update. However, the first real ZK backend should start from the smaller and cleaner TD arithmetic statement.

## 8. Backend Options

Candidate backends:

```text
RISC Zero
SP1
Noir
Circom
Halo2
```

Recommended first backend:

```text
RISC Zero or SP1
```

Reason:

```text
The first MVP contains hashing, Merkle verification, branching, fixed-point arithmetic, and artifact parsing logic. A zkVM backend is likely easier to prototype than a hand-written arithmetic circuit.
```

Circuit-oriented systems such as Noir, Circom, or Halo2 may become more useful later after the relation is stabilized and constraint optimization becomes important.

## 9. MVP Milestones

### v0.8

Documentation-only milestone.

Deliverables:

```text
docs/zk_backend_mvp.md
docs/threat_model.md
docs/backend_choice.md
```

### v0.9

Backend selection and test-vector preparation.

Deliverables:

```text
zk_backend/test_vectors/td_mvp_case_0.json
docs/backend_choice.md
```

### v1.0

First real ZK TD MVP.

Deliverables:

```text
Merkle membership proof inside backend
Bellman target check inside backend
SmoothL1 TD loss check inside backend
valid proof accepted
tampered witness rejected
proving time recorded
verification time recorded
proof size recorded
```

Current Phase E status:

```text
SP1 TD-1/2/4/8 proofs generated and verified
SP1 CartPole and MountainCar forward-TD MLP batch-1 proofs generated and verified
SP1 CartPole tiny one-step SGD batch-1 proof generated and verified
Python/SP1 agreement holds on valid and tampered TD MVP cases
full proof-of-training remains out of scope
```

## 10. Non-Goals

The first backend MVP does not prove:

```text
full DQN training
large neural-network training traces
Adam optimizer semantics
long training traces
target-network synchronization over many steps
recursive proof aggregation
honesty of data collection before commitment
```
