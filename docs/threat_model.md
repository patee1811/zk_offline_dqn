# Threat Model

## 1. Scope

This document defines the threat model for the ZK-Offline-DQN project.

The current project is a pre-ZK artifact/verifier framework for offline DQN training from committed trajectories. The goal is to move toward a zero-knowledge proof system that can prove selected offline DQN training relations over a committed dataset.

The first backend target is intentionally narrow:

> Prove that a transition or minibatch comes from a committed offline dataset and that selected DQN training computations, starting with Bellman target and SmoothL1 TD loss, are computed correctly.

This document clarifies what the verifier should trust, what the prover may try to cheat on, what the current verifier catches, and what remains out of scope.

## 2. Parties

### 2.1 Prover

The prover is the party claiming that a DQN-related computation was performed correctly.

The prover may possess:

```text
offline trajectory dataset
transition-level dataset
Merkle proofs
model checkpoints
online network weights
target network weights
intermediate Q-values
TD targets
TD losses
gradients
parameter deltas
training artifacts
```

The prover may want to keep private:

```text
raw states
actions
rewards
next states
done flags
model weights
intermediate tensors
training traces
```

### 2.2 Verifier

The verifier is the party checking whether the prover's claim is valid.

The verifier may know:

```text
dataset commitment root
artifact schema version
training specification
fixed-point scale
discount factor
sampling rule
claimed target/loss/update result
checkpoint or model-state commitments
proof or verification artifact
```

The verifier should not need to see the full private dataset or full model weights.

## 3. Prover Claims

Depending on the statement version, the prover may claim one or more of the following.

### 3.1 Dataset commitment claim

The prover claims that the sampled transition or minibatch belongs to a dataset committed before verification.

Expected public anchor:

```text
dataset_root
```

Expected private witness:

```text
transition
merkle_path
```

### 3.2 TD arithmetic claim

The prover claims that the Bellman target, TD error, and SmoothL1 TD loss were computed correctly.

Expected public inputs:

```text
gamma_fp
fp_scale
claimed_target_fp
claimed_loss_fp
```

Expected private witness:

```text
reward_fp
done
q_online_action_fp
q_target_max_fp
target_fp
td_error_fp
loss_fp
```

### 3.3 Model commitment claim

The prover claims that a computation is anchored to a specific model checkpoint or canonical model state.

Expected public anchors:

```text
checkpoint_sha256
online_state_dict_sha256
target_state_dict_sha256
```

This project distinguishes between raw checkpoint-file hash and canonical tensor-content hash.

### 3.4 One-step update claim

The prover claims that one simplified SGD-style update was computed correctly.

Expected public anchors:

```text
pre_update_model_commitment
post_update_model_commitment
learning_rate_fp
batch_indices
```

Expected private witness:

```text
pre_update_weights
gradients
parameter_deltas
post_update_weights
```

### 3.5 Short-trace claim

The prover claims that a short sequence of update steps was chained correctly.

Expected public anchors:

```text
initial_model_commitment
final_model_commitment
sampling_rule
batch_indices_per_step
target_sync_schedule
```

Expected private witness:

```text
per_step_artifacts
intermediate_checkpoints
per_step_gradients
per_step_parameter_deltas
```

## 4. Adversarial Prover Capabilities

The prover may try to cheat by modifying one or more parts of the artifact or witness.

Examples:

```text
use a transition that is not in the committed dataset
tamper with reward
tamper with done flag
tamper with q_online_action_fp
tamper with q_target_max_fp
tamper with Bellman target
tamper with SmoothL1 loss
tamper with minibatch-average loss
tamper with Merkle leaf hash
tamper with Merkle path
tamper with checkpoint hash
tamper with canonical state-dict commitment
tamper with next_action_online
tamper with gradients
tamper with parameter deltas
tamper with learning rate
tamper with post-update checkpoint commitment
tamper with batch indices
tamper with sampling seed
tamper with dataset size
tamper with short-trace boundary commitments
```

The verifier should reject these attacks when they fall within the active statement.

## 5. Security Goals

The project aims to provide the following guarantees.

### 5.1 Dataset membership integrity

If verification passes, the checked transition or minibatch should be consistent with the public dataset commitment.

### 5.2 TD computation integrity

If verification passes, the Bellman target, TD error, and SmoothL1 TD loss should be consistent with the stated fixed-point arithmetic rules.

### 5.3 Artifact schema integrity

If verification passes, the artifact should match the expected schema version and should not rely on stale or ambiguous fields.

### 5.4 Model-state anchoring

If verification passes, the checked computation should be anchored to declared checkpoint or canonical model-state commitments, when those commitments are part of the statement.

### 5.5 Sampling-rule integrity

If verification passes, the declared minibatch should follow the specified deterministic sampling rule, when sampling-rule verification is part of the statement.

### 5.6 Update consistency

If verification passes, the one-step update should be consistent with the declared gradients, parameter deltas, learning rate, and post-update model commitment, when one-step update verification is part of the statement.

### 5.7 Trace consistency

If verification passes, a short trace should have valid step-to-step checkpoint chaining and boundary commitments, when short-trace verification is part of the statement.

## 6. Privacy Goals

The long-term zero-knowledge goal is to avoid revealing:

```text
raw transitions
raw rewards
raw states
raw next states
model weights
intermediate tensors
gradients
training traces
```

However, the current Python verifier prototype is not itself zero-knowledge.

Current status:

```text
Python artifact verifier: correctness-oriented, not privacy-preserving
Future ZK backend: correctness + zero-knowledge privacy
```

Therefore, privacy claims should only be made for future ZK backend implementations, not for the current Python verifier alone.

## 7. Out of Scope

The following are not guaranteed by the current project.

### 7.1 Data collection honesty before commitment

The project does not prove that the original trajectories were collected honestly from a real environment.

It only proves membership relative to a committed dataset.

### 7.2 Dataset quality

The project does not prove that the dataset is good, diverse, unbiased, or sufficient for learning a strong policy.

### 7.3 Reward correctness before commitment

The project does not prove that rewards were assigned truthfully before the dataset was committed.

### 7.4 Full training from initialization

The current project does not prove that the final model was produced by a complete training run from initialization.

### 7.5 Full neural-network forward pass

The first ZK backend MVP does not prove full neural-network inference from committed weights.

### 7.6 Full backpropagation

The first ZK backend MVP does not prove full backpropagation or optimizer semantics.

### 7.7 Adam optimizer correctness

The current one-step verifier focuses on a simplified SGD-style update, not full Adam semantics.

### 7.8 Stochastic replay unless modeled

Random or stochastic replay is out of scope unless the randomness source, seed, and sampling rule are explicitly modeled.

### 7.9 Prioritized replay unless modeled

Prioritized replay is out of scope unless priority computation and sampling probabilities are explicitly modeled.

### 7.10 Long-horizon target-network synchronization

The current short-trace verifier only covers limited target-network synchronization semantics.

### 7.11 Recursive proof composition

Recursive aggregation of many update proofs into a full training certificate is future work.

### 7.12 Production-grade cryptographic security

The current repository is a research prototype and should not be treated as production cryptographic infrastructure.

## 8. Current Negative-Test Coverage

The repository currently includes negative tests for several tampering classes.

### 8.1 Minibatch TD tampering

Covered examples:

```text
reward tampering
loss tampering
checkpoint hash tampering
online state-dict hash tampering
leaf hash tampering
Merkle path tampering
```

### 8.2 One-step update tampering

Covered examples:

```text
next_action_online tampering
q_target_max_fp tampering
loss_fp tampering
gradient tensor tampering
delta tensor tampering
post checkpoint hash tampering
post online state-dict hash tampering
learning rate tampering
batch index tampering
```

### 8.3 Short-trace tampering

Covered examples:

```text
public batch tampering
sampling seed tampering
dataset size tampering
final checkpoint hash tampering
final online state-dict hash tampering
```

These tests support regression confidence but do not replace a formal proof of soundness.

## 9. Threat Model Summary

The project protects against a dishonest prover who tries to present inconsistent training artifacts relative to a committed dataset and declared DQN training relation.

The project does not protect against dishonest data generation before commitment, poor dataset quality, or claims that are outside the modeled relation.

The intended research progression is:

```text
Python artifact verification
→ backend-ready relation design
→ real ZK proof for TD arithmetic
→ verified one-step update
→ short-trace proof
→ chunked or recursive full-training certificate
```