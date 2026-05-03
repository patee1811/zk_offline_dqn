# Proof Statement Design

## 1. Purpose of This Document

This document defines the current proof-statement scope for the repository and clarifies what is already implemented versus what remains future work.

The repository currently contains a **pre-ZK artifact/verifier prototype** for offline DQN training from committed data. It is **not yet** a full zero-knowledge proof-of-training system.

The current implementation is organized into five connected statement layers:

1. **TD arithmetic statement** — committed transition membership, Double-DQN target correctness, SmoothL1 TD loss correctness, batch-loss aggregation, checkpoint anchoring, canonical model-state anchoring, and forward TD consistency.
2. **One-step update statement** — one offline DQN SGD update from a committed minibatch, including gradient recomputation, parameter-delta consistency, SGD update consistency, pre/post checkpoint anchoring, and pre/post canonical model-state commitments.
3. **Short-trace update statement** — a short sequence of verified one-step updates with checkpoint chaining, target-network synchronization semantics, final checkpoint anchoring, and initial/final canonical boundary commitments.
4. **Deterministic sampling-rule statement** — trace minibatches are checked against a declared deterministic sampling rule, currently either `contiguous_deterministic` or `seeded_permutation`.
5. **Negative-test statement evidence** — verifier rejection is tested for tampered TD arithmetic, membership, checkpoint hashes, canonical commitments, sampling metadata, and trace-boundary commitments.

The current system should be described as:

> a pre-ZK artifact/verifier prototype for committed-data membership, TD-target/loss correctness, canonical checkpoint/model-state anchoring, forward TD consistency, one-step SGD update consistency, short verified training traces, deterministic sampling-rule enforcement, and negative tamper tests.

It should **not** be described as a full proof-of-training system.

---

## 2. TD Statement

### 2.1 Statement

Given:

- a public Merkle root committing to an offline transition dataset;
- a public checkpoint file hash;
- public canonical online/target model-state commitments;
- a declared minibatch of transition indices;

prove that:

1. the sampled transitions belong to the committed dataset;
2. the Double-DQN Bellman targets are computed correctly;
3. the SmoothL1 TD losses are computed correctly;
4. the minibatch-average loss is computed correctly;
5. the checkpoint file hash matches the checkpoint used by the verifier;
6. the canonical online/target state-dict commitments match the checkpoint tensor contents;
7. the exported TD witness values match actual checkpoint forward-pass semantics.

### 2.2 Public Inputs

For `minibatch_td_v1`, the main public inputs include:

```text
schema_version
dataset_root
batch_size
loss_type
checkpoint_sha256
checkpoint_commitment_type
online_state_dict_key
online_state_dict_sha256
target_state_dict_sha256
batch_loss_fp
```

### 2.3 Private / Witness Fields

For each item:

```text
transition
leaf
leaf_hash
merkle_path
td_witness.q_online_fp
td_witness.next_action_online
td_witness.q_target_max_fp
td_witness.target_fp
td_witness.loss_fp
```

The field `next_action_online` is part of the statement, not only a debug value, because Double DQN uses:

```text
next_action_online = argmax_a Q_online(s')
q_target_max_fp = Q_target(s')[next_action_online]
```

### 2.4 Verified Relations

For each transition `(s, a, r, s', done)`:

```text
transition ∈ committed_dataset
q_online_fp = Q_online(s)[a]
next_action_online = argmax_a Q_online(s')
q_target_max_fp = Q_target(s')[next_action_online]
target_fp = r + gamma * q_target_max_fp       if done = False
target_fp = r                                if done = True
loss_fp = SmoothL1(q_online_fp, target_fp)
```

For the batch:

```text
batch_loss_fp = floor(sum(loss_fp_i) / batch_size)
```

The forward TD verifier additionally recomputes:

```text
Q_online(s)[a]
argmax_a Q_online(s')
Q_target(s')[argmax_a Q_online(s')]
```

from the checkpoint and checks that these values match the TD witness.

---

## 3. One-Step Update Statement

### 3.1 Statement

Given:

- a committed offline dataset;
- explicit minibatch indices;
- a pre-update checkpoint;
- a claimed post-update checkpoint;
- a fixed optimizer type `sgd`;
- a fixed learning rate;

prove that one offline DQN SGD update step was computed correctly.

### 3.2 Public Inputs

For `one_step_update_v1`, the main public inputs include:

```text
schema_version
dataset_root
batch_indices
batch_size
loss_type
optimizer_type
learning_rate_fp
pre_checkpoint_sha256
post_checkpoint_sha256
checkpoint_commitment_type
pre_online_state_dict_key
pre_online_state_dict_sha256
pre_target_state_dict_sha256
post_online_state_dict_key
post_online_state_dict_sha256
post_target_state_dict_sha256
```

### 3.3 Private / Witness Fields

The one-step witness includes:

```text
items[].transition
items[].leaf
items[].leaf_hash
items[].merkle_path
items[].td_witness
update_witness.batch_loss_fp
update_witness.gradient_tensors
update_witness.delta_tensors
```

The current Python prototype also keeps audit/debug values such as:

```text
items[].debug
update_witness.parameter_summaries
update_witness.batch_loss_real_for_training
```

These are useful for inspection but should be separated from backend-ready witness fields in a future cleanup.

### 3.4 Verified Relations

The one-step verifier checks:

1. all minibatch transitions belong to the committed dataset;
2. all Double-DQN Bellman targets are correct;
3. all SmoothL1 TD losses are correct;
4. the minibatch-average loss is correct;
5. pre/post checkpoint file hashes match the supplied checkpoint files;
6. pre/post canonical online and target state-dict commitments match checkpoint tensor contents;
7. gradients are recomputed consistently from the pre-update checkpoint and minibatch loss;
8. stored delta tensors match the actual pre/post parameter differences;
9. the SGD update rule is applied:

```text
w' = w - lr * g
```

10. the target network remains unchanged during the one-step statement;
11. the online network changes after the update;
12. the training step counter increments correctly.

### 3.5 Current Limitation

The one-step statement currently verifies a simplified SGD update. It does not yet verify:

- Adam optimizer dynamics;
- weight decay;
- scheduler state;
- full replay buffer sampling over a long run;
- target-network sync across a full training run;
- model selection or early stopping.

---

## 4. Short-Trace Update Statement

### 4.1 Statement

Given:

- a committed offline dataset;
- a declared sequence of minibatches;
- an initial checkpoint;
- a claimed final checkpoint;
- a fixed short trace length;
- a fixed target sync schedule;

prove that the trace consists of valid chained one-step updates and that target-network synchronization is applied according to the declared rule.

### 4.2 Public Inputs

For `short_trace_update_v2`, the main public inputs include:

```text
schema_version
dataset_root
trace_batch_indices
num_steps
batch_size
loss_type
optimizer_type
learning_rate_fp
sampling_rule_type
start_offset
sampling_seed
dataset_size
target_sync_every
initial_checkpoint_sha256
final_checkpoint_sha256
checkpoint_commitment_type
initial_online_state_dict_key
initial_online_state_dict_sha256
initial_target_state_dict_sha256
final_online_state_dict_key
final_online_state_dict_sha256
final_target_state_dict_sha256
```

For `contiguous_deterministic`, the following fields are normally unused and may be `null`:

```text
sampling_seed
dataset_size
```

For `seeded_permutation`, the verifier requires:

```text
sampling_seed
dataset_size
```

### 4.3 Private / Witness Fields

For each step:

```text
steps[].step_index
steps[].input_checkpoint_sha256
steps[].raw_output_checkpoint_sha256
steps[].next_checkpoint_sha256
steps[].target_sync_applied
steps[].sync_state_witness
steps[].one_step_artifact
```

The nested `one_step_artifact` contains the committed minibatch witness and one-step update witness.

The `sync_state_witness` contains enough state data to check target-network synchronization semantics without storing local checkpoint paths inside the persistent artifact.

### 4.4 Verified Relations

The short-trace verifier checks:

1. `num_steps` matches the number of steps and declared trace batches;
2. the initial checkpoint file hash matches `initial_checkpoint_sha256`;
3. the final checkpoint file hash matches `final_checkpoint_sha256`;
4. initial/final canonical model-state commitments match the corresponding checkpoint tensor contents;
5. each nested one-step artifact verifies successfully;
6. the output checkpoint of step `t` matches the input checkpoint of step `t+1`;
7. if `target_sync_applied = False`, then the next target state equals the raw output target state;
8. if `target_sync_applied = True`, then the next target state equals the raw output online state;
9. the final chained checkpoint hash matches the public final checkpoint hash;
10. all declared trace batches obey the selected deterministic sampling rule.

### 4.5 Target Sync Semantics

If no sync is applied:

```text
next_target_state = raw_output_target_state
```

If sync is applied:

```text
next_target_state = raw_output_online_state
```

For example, with:

```text
target_sync_every = 2
```

the second step in a two-step trace applies target sync, so the final online and target canonical state-dict commitments may become equal.

---

## 5. Deterministic Sampling-Rule Statement

### 5.1 Supported Rules

The current short-trace verifier supports two deterministic sampling rules:

```text
contiguous_deterministic
seeded_permutation
```

### 5.2 Contiguous Deterministic Sampling

For:

```text
sampling_rule_type = contiguous_deterministic
```

and public:

```text
start_offset
batch_size
num_steps
```

the expected batch for step `t` is:

```text
B_t = [start_offset + t * batch_size,
       start_offset + t * batch_size + 1,
       ...,
       start_offset + t * batch_size + batch_size - 1]
```

The verifier checks:

```text
public.trace_batch_indices[t] == B_t
steps[t].one_step_artifact.public.batch_indices == B_t
```

### 5.3 Seeded Permutation Sampling

For:

```text
sampling_rule_type = seeded_permutation
```

and public:

```text
sampling_seed
dataset_size
batch_size
num_steps
```

the verifier reconstructs a deterministic pseudorandom permutation:

```text
permutation = shuffle(range(dataset_size), sampling_seed)
```

Then for step `t`:

```text
B_t = permutation[t * batch_size : (t + 1) * batch_size]
```

The verifier checks:

```text
public.trace_batch_indices[t] == B_t
steps[t].one_step_artifact.public.batch_indices == B_t
```

The current implementation does not support wrap-around for seeded permutation sampling. Therefore:

```text
num_steps * batch_size <= dataset_size
```

must hold.

### 5.4 What This Proves

This statement reduces prover freedom by proving that trace minibatches were not chosen arbitrarily after seeing update results.

It upgrades the trace claim from:

```text
verify this declared trace
```

to:

```text
verify this declared trace and verify that its minibatches follow a declared public sampling rule
```

### 5.5 What This Still Does Not Prove

This still does not prove full replay-sampling correctness for:

- prioritized replay;
- stochastic replay with hidden RNG state;
- replay buffer mutations over a long training run;
- sampler state transitions across a full training run;
- curriculum or adaptive sampling.

---

## 6. Negative Verification Tests

### 6.1 Minibatch TD Negative Tests

The repository includes:

```text
scripts/experiments/run_negative_verification_tests.py
```

It verifies that valid minibatch TD artifacts are accepted and tampered artifacts are rejected.

| Case | Expected result | Failure mode |
|---|---:|---|
| `valid_control` | accept | unchanged valid minibatch TD artifact |
| `tamper_loss_fp` | reject | TD loss witness no longer matches recomputed SmoothL1 loss |
| `tamper_reward` | reject | Bellman target and loss no longer match the transition |
| `tamper_checkpoint_sha256` | reject | public checkpoint hash no longer matches the checkpoint file |
| `tamper_online_state_dict_sha256` | reject | online-network state-dict commitment no longer matches canonical checkpoint tensor contents |
| `tamper_leaf_hash` | reject | serialized transition leaf no longer matches the claimed leaf hash |
| `tamper_merkle_path` | reject | Merkle path no longer reconstructs the public dataset root |

### 6.2 Short-Trace Negative Tests

The repository includes:

```text
scripts/experiments/run_short_trace_negative_tests.py
```

It verifies that valid short-trace artifacts are accepted and tampered trace-level artifacts are rejected.

| Case | Expected result | Failure mode |
|---|---:|---|
| `valid_contiguous` | accept | unchanged valid contiguous short-trace artifact |
| `valid_seeded` | accept | unchanged valid seeded-permutation short-trace artifact |
| `tamper_contiguous_public_batch` | reject | public contiguous trace batch no longer matches the declared contiguous rule |
| `tamper_seeded_public_batch` | reject | public seeded trace batch no longer matches the seeded permutation |
| `tamper_sampling_seed` | reject | public seed no longer reconstructs the declared trace batches |
| `tamper_dataset_size` | reject | public dataset size no longer reconstructs the declared seeded batches |
| `tamper_final_checkpoint_sha256` | reject | public final checkpoint hash no longer matches the final checkpoint file |
| `tamper_final_online_state_dict_sha256` | reject | final online-network state-dict commitment no longer matches the final checkpoint tensor contents |

These negative tests show that the verifier rejects:

- arithmetic tampering;
- checkpoint file-hash tampering;
- canonical model-state commitment tampering;
- Merkle membership tampering;
- trace sampling-rule tampering;
- trace-boundary commitment tampering.

---

## 7. Fixed-Point Encoding

The TD-side statements use fixed-point integer arithmetic.

Current fixed-point parameters are defined in:

```text
zk_offline_dqn/zk_specs.py
```

Core values:

```text
FP_SCALE = 1000
GAMMA_FP = 990
LOSS_TYPE = smooth_l1
SMOOTH_L1_BETA_FP = 1000
```

A real value `x` is encoded as:

```text
x_fp = round(x * FP_SCALE)
```

This makes TD arithmetic deterministic and easier to translate to a future circuit or zkVM backend.

The one-step update prototype currently still uses PyTorch floating-point tensors for gradient and parameter-delta consistency checks. A future backend-ready design should quantize, compress, or commit these tensors more carefully.

---

## 8. Artifact Structure

### 8.1 Minibatch TD Artifact

Core public fields:

```text
schema_version
public.dataset_root
public.batch_size
public.loss_type
public.batch_loss_fp
public.checkpoint_sha256
public.checkpoint_commitment_type
public.online_state_dict_key
public.online_state_dict_sha256
public.target_state_dict_sha256
```

Core witness fields:

```text
items[].transition
items[].leaf
items[].leaf_hash
items[].merkle_path
items[].td_witness
```

### 8.2 One-Step Update Artifact

Core public fields:

```text
schema_version
public.dataset_root
public.batch_indices
public.batch_size
public.loss_type
public.optimizer_type
public.learning_rate_fp
public.pre_checkpoint_sha256
public.post_checkpoint_sha256
public.checkpoint_commitment_type
public.pre_online_state_dict_key
public.pre_online_state_dict_sha256
public.pre_target_state_dict_sha256
public.post_online_state_dict_key
public.post_online_state_dict_sha256
public.post_target_state_dict_sha256
```

Core witness fields:

```text
items[].transition
items[].leaf
items[].leaf_hash
items[].merkle_path
items[].td_witness
update_witness.batch_loss_fp
update_witness.gradient_tensors
update_witness.delta_tensors
```

### 8.3 Short-Trace Update Artifact

Core public fields:

```text
schema_version
public.dataset_root
public.trace_batch_indices
public.num_steps
public.batch_size
public.loss_type
public.optimizer_type
public.learning_rate_fp
public.sampling_rule_type
public.start_offset
public.sampling_seed
public.dataset_size
public.target_sync_every
public.initial_checkpoint_sha256
public.final_checkpoint_sha256
public.checkpoint_commitment_type
public.initial_online_state_dict_key
public.initial_online_state_dict_sha256
public.initial_target_state_dict_sha256
public.final_online_state_dict_key
public.final_online_state_dict_sha256
public.final_target_state_dict_sha256
```

Core witness / trace fields:

```text
steps[].step_index
steps[].input_checkpoint_sha256
steps[].raw_output_checkpoint_sha256
steps[].next_checkpoint_sha256
steps[].target_sync_applied
steps[].sync_state_witness
steps[].one_step_artifact
```

Operational paths such as Merkle path, initial checkpoint path, and final checkpoint path are supplied externally by the benchmark/runtime environment rather than stored as durable artifact fields.

---

## 9. What Is Not Yet Fully Proved

The current prototype does **not** yet prove:

1. full end-to-end training from initialization to final selected checkpoint;
2. long-run replay sampling across many training iterations;
3. prioritized replay;
4. stochastic replay with full RNG-state modeling;
5. Adam or other optimizer variants;
6. early stopping or model selection;
7. recursive proof composition;
8. proof aggregation;
9. a production zero-knowledge backend.

More precisely:

- already checked in Python:
  - committed-data membership;
  - TD target/loss arithmetic;
  - canonical checkpoint/model-state commitments;
  - forward TD consistency;
  - one-step SGD update consistency;
  - short-trace checkpoint chaining;
  - target-sync semantics;
  - deterministic contiguous sampling;
  - seeded-permutation sampling;
  - negative tamper rejection.

- not yet proven in ZK:
  - any of the above relations inside a zkVM, SNARK, or custom circuit.

---

## 10. Recommended Next Milestones

### 10.1 One-Step Artifact Schema Cleanup

The one-step artifact should be cleaned by separating:

- mandatory public inputs;
- private witness fields;
- debug-only fields;
- runtime metadata;
- benchmark metadata.

The goal is to reduce the artifact before translating it into a backend-ready statement.

### 10.2 Backend-Ready TD Statement

The first realistic ZK backend target should be:

```text
committed transition membership
+ Bellman target correctness
+ SmoothL1 TD loss correctness
```

This is smaller and more circuit-friendly than proving a full neural-network update.

### 10.3 Backend-Ready Update Witness

For one-step update proof work, the next design question is how to represent:

```text
gradient_tensors
delta_tensors
pre/post model states
```

in a compact, deterministic, backend-friendly form.

### 10.4 Longer Trace Composition

Short traces are now implemented in Python. Future work should explore:

- longer traces;
- proof recursion;
- proof aggregation;
- trace chunking;
- commitment-only links between trace chunks.

---

## 11. Recommended Wording

Recommended wording for the current stage:

> Our current system does not yet implement a full zero-knowledge proving backend. Instead, it realizes a pre-ZK artifact/verifier prototype for offline DQN training from committed data. The implemented prototype verifies committed-transition membership, Double-DQN-style Bellman target correctness, SmoothL1 TD loss correctness, batch-loss aggregation, checkpoint and canonical model-state anchoring, forward TD consistency, one-step SGD update consistency, short-trace checkpoint chaining, target-network synchronization semantics, deterministic contiguous and seeded-permutation sampling-rule enforcement, and systematic rejection of tampered artifacts.

Short version:

> The current repository implements a pre-ZK verification prototype for committed-data offline DQN training, covering TD arithmetic, canonical model-state commitments, one-step SGD updates, short trace verification, deterministic sampling-rule enforcement, and negative tamper tests.