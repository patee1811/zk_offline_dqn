# Proof Statement Design

## 1. Purpose of This Document

This document defines the current proof-statement scope for the repository and clarifies what is already implemented versus what remains future work.

The repository currently contains a **pre-ZK artifact-verifier prototype** for offline DQN training from committed data. It is **not yet** a full zero-knowledge proof-of-training system.

The design is organized into two levels:

1. an **MVP TD-arithmetic statement**, which is already implemented and verified in Python;
2. a **stronger one-step update statement**, for which a stronger pre-ZK artifact/verifier prototype is also now implemented in Python.

---

## 2. MVP Statement

We consider the following MVP statement:

> Given a public commitment to an offline transition dataset and a public hash of a model checkpoint, the prover shows that a minibatch of transitions belongs to the committed dataset, and that the Double-DQN-style Bellman targets and SmoothL1 TD losses for that minibatch are computed correctly.

This MVP does **not** yet prove a gradient update.
It proves correctness of:

1. membership of sampled transitions in committed data,
2. Bellman target computation,
3. TD loss computation,
4. batch-average loss computation,
5. checkpoint anchoring via SHA-256.

---

## 3. Current Scope in This Repository

The current implementation proves/verifies the following in a Python artifact-verifier prototype:

- transition membership in a committed dataset via Merkle proofs,
- fixed-point Bellman target computation,
- fixed-point SmoothL1 TD loss computation,
- batch-average TD loss,
- model anchoring through `checkpoint_sha256`,
- Double DQN target selection using:
  - the **online network** for `argmax_a Q_online(s', a)`,
  - the **target network** for evaluating that selected action.

The repository now also includes a stronger pre-ZK prototype for **one offline DQN SGD update step**, including:

- pre-update checkpoint anchoring,
- post-update checkpoint anchoring,
- gradient recomputation consistency,
- parameter-delta consistency,
- SGD update consistency,
- invariance of the target network during the one-step statement.

The current implementation is therefore still **not yet a true zero-knowledge proof system**.
It is a **pre-ZK artifact design and verifier prototype**.

---

## 4. Statement Variants Implemented

### 4.1 Single-Sample TD Statement

For one transition `(s, a, r, s', done)`:

- prove the transition is included in the committed dataset,
- prove `q_online = Q_online(s)[a]`,
- prove `next_action = argmax_a' Q_online(s')[a']`,
- prove `q_target = Q_target(s')[next_action]`,
- prove `target = r + (1 - done) * gamma * q_target`,
- prove `loss = SmoothL1(q_online, target)`.

### 4.2 Minibatch TD Statement

For a minibatch of transitions:

- prove each transition is included in the committed dataset,
- prove each per-sample target and loss is correct,
- prove `batch_loss = floor(sum(loss_i) / batch_size)` in fixed-point form.

### 4.3 One-Step Offline DQN SGD Update Statement

For one fixed minibatch of committed transitions:

- prove all transitions in the minibatch belong to the committed dataset,
- prove all Double-DQN Bellman targets are correct,
- prove all SmoothL1 TD losses are correct,
- prove the minibatch-average loss is correct,
- prove gradients are recomputed consistently from the pre-update checkpoint and that minibatch,
- prove the parameter deltas are consistent with the pre-update and post-update online-network states,
- prove the SGD update rule `w' = w - lr * g` is applied consistently,
- prove the target network remains unchanged during this one-step statement,
- prove the claimed post-update checkpoint matches the updated model state.

---

## 5. Public Inputs

### 5.1 Dataset-Related Public Inputs

- `dataset_root`: Merkle root of the committed transition dataset

### 5.2 Model-Related Public Inputs

For the MVP TD statement:

- `checkpoint_sha256`: SHA-256 hash of the checkpoint file used to derive online/target Q-values

For the one-step update statement:

- `pre_checkpoint_sha256`
- `post_checkpoint_sha256`

### 5.3 Arithmetic / Configuration Public Inputs

For TD artifacts:

- `loss_type = "smooth_l1"`
- `batch_size` for minibatch artifact
- `batch_loss_fp` for minibatch artifact

For one-step update artifacts:

- `batch_indices`
- `batch_size`
- `loss_type = "smooth_l1"`
- `optimizer_type = "sgd"`
- `learning_rate_fp`
- optionally `learning_rate_real` for debugging / audit convenience

### 5.4 Implicit Public Constants in the Current Prototype

These are currently fixed by code/config rather than explicitly published as circuit inputs:

- fixed-point scale `FP_SCALE = 1000`
- `gamma = 0.99` encoded as `GAMMA_FP = 990`
- SmoothL1 beta `= 1.0` encoded as `SMOOTH_L1_BETA_FP = 1000`
- network architecture:
  - Linear(4,128) -> ReLU
  - Linear(128,128) -> ReLU
  - Linear(128,2)

In a future ZK circuit, these should be either:

- hard-coded into the circuit/specification, or
- made explicit public parameters.

---

## 6. Private Witness

### 6.1 Data Witness

For each sampled transition:

- transition contents:
  - `obs`
  - `action`
  - `reward`
  - `next_obs`
  - `done`
- serialized fixed-point leaf
- leaf hash
- Merkle authentication path

### 6.2 Model Witness / Derived Witness for TD Statements

For each sample:

- `q_online_fp`
- `q_target_max_fp`
- `target_fp`
- `loss_fp`

For Double DQN semantics, the witness also conceptually includes:

- online forward values on `obs`
- online forward values on `next_obs`
- target forward values on `next_obs`
- selected `next_action_online = argmax_a Q_online(next_obs)[a]`

In the current Python artifact prototype, some of these are stored only as debug fields rather than as formal public values.

### 6.3 Additional Witness for One-Step Update Statements

For the one-step update prototype, the witness additionally includes:

- pre-update online-network weights
- pre-update target-network weights
- recomputed batch training loss
- per-parameter gradients
- per-parameter deltas
- post-update online-network weights

The current implementation stores gradient tensors and delta tensors explicitly inside the one-step artifact for auditability and consistency checking.

---

## 7. Relation to Be Verified

### 7.1 Membership Relation

For each transition:

1. serialize transition into fixed-point leaf format,
2. hash the leaf,
3. verify the Merkle path against the public `dataset_root`.

This establishes that the sample comes from the committed dataset.

### 7.2 Double DQN Target Relation

For each transition:

1. compute:
   - `q_online = Q_online(s)[a]`
2. compute:
   - `next_action_online = argmax_a' Q_online(s')[a']`
3. compute:
   - `q_target = Q_target(s')[next_action_online]`
4. compute Bellman target:
   - `target = reward + (1 - done) * gamma * q_target`

All arithmetic is represented in fixed-point form in the current prototype.

### 7.3 TD Loss Relation

For each transition:

- `loss = SmoothL1(q_online, target)`

with beta = 1.0.

In fixed-point form:

- if `|delta| < beta`, then
  - `loss = delta^2 / (2 * beta)`
- else
  - `loss = |delta| - beta / 2`

where `delta = q_online - target`.

### 7.4 Batch Loss Relation

For minibatch artifact:

- `batch_loss_fp = floor(sum(loss_i) / batch_size)`

### 7.5 One-Step SGD Update Relation

For the stronger one-step prototype:

1. start from a publicly anchored pre-update checkpoint,
2. use a fixed committed minibatch,
3. recompute the training loss for that minibatch,
4. recompute gradients with respect to the online-network parameters,
5. apply one SGD update:
   - `w' = w - lr * g`
6. obtain post-update online-network parameters,
7. serialize/store the resulting post-update checkpoint,
8. verify consistency between:
   - the recomputed gradients and stored gradients,
   - the recomputed parameter deltas and stored deltas,
   - the actual post-update parameters and the SGD rule,
   - the post-update checkpoint hash and the resulting checkpoint file.

The target network is held fixed during this one-step statement.

---

## 8. Fixed-Point Encoding

The TD-artifact portion of the prototype uses fixed-point encoding to make arithmetic explicit and ZK-friendly.

- real value `x` is encoded as:
  - `x_fp = round(x * FP_SCALE)`
- current scale:
  - `FP_SCALE = 1000`

Examples:

- reward `1.0` -> `1000`
- gamma `0.99` -> `990`

This keeps arithmetic simple and deterministic for artifact verification.

The one-step update prototype currently uses:

- fixed-point arithmetic for TD-side artifact fields, and
- PyTorch floating-point tensors for gradient / parameter-update consistency checking.

This is acceptable for the current pre-ZK prototype, but a future circuit-oriented version should likely quantize or compress the update witness more aggressively.

---

## 9. What Is Already Faithful to Training

The current prototype is already faithful to the implemented offline DQN training in these aspects:

- SmoothL1 loss matches the trainer,
- checkpoint is tied publicly by SHA-256,
- online network outputs are derived from the checkpoint,
- target network outputs are derived from the checkpoint,
- Double DQN target semantics are respected:
  - argmax from online net,
  - value from target net,
- one-step update checking now uses:
  - recomputed gradients from the pre-update checkpoint,
  - actual parameter deltas between pre-update and post-update states,
  - explicit SGD consistency checks.

---

## 10. What Is Not Yet Fully Proved

The current prototype does **not** yet prove:

1. that a full training trace from initialization to final checkpoint was executed correctly,
2. that minibatches were sampled according to a specific sampler rule across the full run,
3. that target-network synchronization occurred correctly across many training steps,
4. that model selection / early stopping / best-checkpoint selection were correct,
5. that multi-step optimizer dynamics were proved end-to-end,
6. that the system is backed by an actual zero-knowledge proving backend,
7. that proof recursion / proof aggregation has been implemented.

This is why the current system should be described as:

> a pre-ZK verifiable artifact prototype for committed-data membership, TD-target/loss correctness, and one-step update consistency,

not yet a full proof-of-training system.

---

## 11. Stronger Statement: One Verified Offline DQN Update Step

The stronger current statement is:

> Given a committed dataset, explicit minibatch indices, a public pre-update checkpoint hash, and a claimed public post-update checkpoint hash, prove that one offline DQN SGD update step was computed correctly, including Bellman target computation, SmoothL1 TD loss computation, gradient recomputation, parameter-delta consistency, SGD update consistency, and resulting checkpoint anchoring.

### 11.1 Scope Choice for the Current Version

To keep the statement feasible, the current stronger prototype uses the smallest practical setting:

- one minibatch only,
- fixed batch indices provided explicitly,
- fixed network architecture,
- fixed loss type: SmoothL1,
- fixed Bellman target rule: Double DQN target-net-at-online-argmax,
- fixed optimizer: SGD,
- no momentum,
- no weight decay,
- no target-network sync inside this statement,
- no replay-sampling randomness inside this statement.

This is intentionally narrower than full offline DQN training.
Its purpose is to verify one update step cleanly before extending to multiple steps or full training traces.

### 11.2 Public Inputs

The verifier sees:

- `dataset_root`
- `batch_indices`
- `batch_size`
- `loss_type = smooth_l1`
- `optimizer_type = sgd`
- `learning_rate_fp`
- `pre_checkpoint_sha256`
- `post_checkpoint_sha256`
- optionally:
  - `learning_rate_real`
  - network metadata (`obs_dim`, `n_actions`, hidden sizes)

### 11.3 Private Witness

The prover keeps private:

- minibatch transitions corresponding to the committed indices
- Merkle authentication paths for those transitions
- pre-update online-network weights
- pre-update target-network weights
- per-sample forward-pass activations
- q-values for the update computation
- Bellman targets
- SmoothL1 per-item losses
- aggregated batch loss
- gradients of all trainable parameters
- post-update online-network weights

### 11.4 What Is Verified in This Statement

The verifier is meant to be convinced of all of the following:

1. the minibatch really comes from the committed dataset,
2. the Bellman targets are computed correctly,
3. the batch-average SmoothL1 loss is computed correctly,
4. the gradients are computed from that exact loss and that exact pre-update online network,
5. the parameter update follows the specified SGD rule,
6. the claimed post-update checkpoint hash corresponds to the updated parameters,
7. the target network remains unchanged during the one-step statement.

### 11.5 What Is Not Yet Verified in This Statement

The current one-step version still does not verify:

- full multi-step training,
- target-network synchronization across training,
- replay-sampling randomness across a full run,
- early stopping / model selection,
- selection of the final best checkpoint across many evaluations,
- optimizer variants such as Adam,
- proof recursion / proof aggregation,
- a true ZK backend.

---

## 12. Current Status of the Stronger Statement

A pre-ZK Python artifact/verifier prototype for **one offline DQN SGD update step** is now implemented in the repository.

The current implementation verifies:

- committed-minibatch membership,
- Double-DQN Bellman target correctness,
- SmoothL1 TD loss correctness,
- batch-loss consistency,
- pre/post checkpoint anchoring,
- target-network invariance for the one-step statement,
- gradient recomputation consistency,
- parameter-delta consistency,
- SGD update consistency.

It still does **not** implement:

- a true zero-knowledge backend,
- multi-step proof composition,
- full training-trace verification.

---

## 13. Recommended Artifact Structure

### 13.1 Single-Sample TD Artifact Public Fields

- `dataset_root`
- `loss_type`
- `checkpoint_sha256`

### 13.2 Single-Sample TD Witness Fields

- `q_online_fp`
- `q_target_max_fp`
- `target_fp`
- `loss_fp`

### 13.3 Minibatch TD Artifact Public Fields

- `dataset_root`
- `loss_type`
- `batch_size`
- `batch_loss_fp`
- `checkpoint_sha256`

### 13.4 Minibatch TD Per-Item Witness Fields

- transition
- Merkle membership data
- `q_online_fp`
- `q_target_max_fp`
- `target_fp`
- `loss_fp`

### 13.5 One-Step Update Artifact Public Fields

- `dataset_root`
- `batch_indices`
- `batch_size`
- `loss_type`
- `optimizer_type`
- `learning_rate_fp`
- `pre_checkpoint_sha256`
- `post_checkpoint_sha256`

### 13.6 One-Step Update Witness Fields

- per-item transition / membership / TD witness data
- `batch_loss_fp`
- `batch_loss_real_for_training`
- `pre_online_state_sha256`
- `post_online_state_sha256`
- `target_state_sha256`
- `parameter_summaries`
- `gradient_tensors`
- `delta_tensors`

---

## 14. Recommended Wording for Paper / Proposal

Recommended wording for the current stage:

> Our current system does not yet implement a full zero-knowledge proving backend. Instead, it realizes a pre-ZK artifact/verifier prototype for offline DQN training from committed data. The implemented prototype verifies committed-transition membership, Double-DQN-style Bellman target correctness, SmoothL1 TD loss correctness, batch-loss aggregation, and checkpoint anchoring, and further includes a stronger one-step SGD update prototype with gradient recomputation, parameter-delta, and update-consistency checks.

---

## 15. Summary

The repository currently realizes two connected statement layers.

### 15.1 MVP Layer

> From a committed offline transition dataset and a publicly anchored checkpoint hash, verify that the sampled transitions belong to the dataset and that their Double-DQN Bellman targets and SmoothL1 TD losses are computed correctly, including minibatch-average loss.

### 15.2 Stronger One-Step Layer

> From a committed offline transition dataset, explicit minibatch indices, and a publicly anchored pre-update checkpoint hash, verify that one offline DQN SGD update step is computed consistently, including TD arithmetic, gradient recomputation, parameter-delta consistency, SGD update consistency, and post-update checkpoint anchoring.

This is the current bridge between:

- committed offline data,
- RL-specific TD arithmetic,
- step-level update verification,
- and a future zero-knowledge proof backend.

## 16. Next Stronger Statement: Short Verified Training Trace

The next research milestone after the current one-step update prototype is a short verified training trace.

Instead of verifying only one offline DQN SGD update step, this stronger statement verifies a small sequence of consecutive update steps, together with checkpoint chaining and an explicit target-network synchronization rule.

### 16.1 Goal

Move from:

- one committed minibatch,
- one recomputed loss,
- one gradient-consistent SGD update,

to:

- multiple committed minibatches,
- multiple consecutive SGD updates,
- explicit checkpoint chaining across steps,
- explicit target-network synchronization events.

The purpose of this statement is to bridge the gap between one-step update verification and a future proof of a longer training process.

### 16.2 Scope of the First Short-Trace Prototype

To keep the trace prototype feasible, the first version should use the smallest practical setting:

- `num_steps = 2` or `num_steps = 4`
- fixed batch indices provided explicitly for each step
- fixed optimizer: SGD
- fixed loss type: SmoothL1
- fixed Bellman target rule: Double DQN target-net-at-online-argmax
- fixed learning rate
- fixed target sync schedule, for example `target_sync_every = 2`
- no replay-sampling randomness inside the statement
- no early stopping or model-selection logic

This is still narrower than full offline DQN training, but it is substantially stronger than one-step verification.

### 16.3 Public Inputs

The verifier should see:

- `dataset_root`
- `trace_batch_indices`
- `num_steps`
- `loss_type = smooth_l1`
- `optimizer_type = sgd`
- `learning_rate_fp`
- `target_sync_every`
- `initial_checkpoint_sha256`
- `final_checkpoint_sha256`

Optionally, the public inputs may also include:

- network metadata
- fixed architecture identifier
- dataset name or experiment identifier

### 16.4 Private Witness

The prover keeps private:

- minibatch transitions corresponding to each claimed step
- Merkle authentication paths for all transitions
- pre-step online-network weights for each step
- pre-step target-network weights for each step
- per-step forward-pass activations
- per-step Bellman targets
- per-step SmoothL1 losses
- per-step gradients
- per-step parameter deltas
- post-step online-network weights
- post-sync target-network weights when synchronization is applied

### 16.5 Statement to Be Proved

There exist:

- committed transitions for each claimed minibatch in the trace,
- an initial checkpoint consistent with `initial_checkpoint_sha256`,
- a sequence of correctly computed one-step SGD updates,
- correctly chained intermediate checkpoints,
- correctly applied target-network synchronization events,
- and a final checkpoint consistent with `final_checkpoint_sha256`

such that all steps in the trace satisfy the one-step update relation and the whole trace remains globally consistent.

### 16.6 What Must Be Verified

A verifier for the short trace should be convinced of all of the following:

1. Each minibatch in the trace comes from the committed dataset.
2. Each step satisfies the TD-arithmetic and SGD-update checks already used in the one-step prototype.
3. The output checkpoint of step `t` matches the input checkpoint of step `t+1`.
4. The target network remains unchanged between sync events.
5. When a sync event is scheduled, the target network is updated according to the declared rule.
6. The final checkpoint hash matches the claimed public output.

### 16.7 What Is Still Not Yet Verified

Even this stronger short-trace statement would still not verify:

- full end-to-end training from initialization to final best checkpoint
- replay-sampling correctness across a full long run
- early stopping or checkpoint selection logic
- optimizer variants such as Adam
- proof recursion or proof aggregation
- a true zero-knowledge backend

### 16.8 Recommended Artifact Structure

A pre-ZK artifact for a short verified trace should contain:

- `public`
  - `dataset_root`
  - `trace_batch_indices`
  - `num_steps`
  - `loss_type`
  - `optimizer_type`
  - `learning_rate_fp`
  - `target_sync_every`
  - `initial_checkpoint_sha256`
  - `final_checkpoint_sha256`

- `steps`
  - `step_index`
  - `input_checkpoint_sha256`
  - `output_checkpoint_sha256`
  - `target_sync_applied`
  - `items`
  - `update_witness`

- `notes`
  - statement scope
  - checkpoint path hints for debugging
  - limitations

### 16.9 Research Interpretation

This short-trace milestone would move the project from:

- verified TD arithmetic,
- to verified one-step update consistency,
- to a verified short training process.

That is the most natural next step before attempting either multi-step large-trace verification or a true zero-knowledge proof backend.