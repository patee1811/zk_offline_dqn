# Proof Statement Design for MVP

## 1. MVP statement

We consider the following MVP statement:

> Given a public commitment to an offline transition dataset and a public hash of a model checkpoint, the prover shows that a minibatch of transitions belongs to the committed dataset, and that the Double-DQN-style Bellman targets and SmoothL1 TD losses for that minibatch are computed correctly.

This MVP does **not** yet prove a gradient update.
It only proves correctness of:
1. membership of sampled transitions in committed data,
2. Bellman target computation,
3. TD loss computation,
4. batch-average loss computation.

---

## 2. Current scope in this repository

The current implementation proves/verifies the following in a Python artifact-verifier prototype:

- transition membership in a committed dataset via Merkle proofs,
- fixed-point Bellman target computation,
- fixed-point SmoothL1 TD loss computation,
- batch-average TD loss,
- model anchoring through `checkpoint_sha256`,
- Double DQN target selection using:
  - online network for `argmax_a Q_online(s', a)`
  - target network for evaluating that selected action.

The current implementation is **not yet** a zero-knowledge proof system.
It is a pre-ZK artifact design and verifier prototype.

---

## 3. Statement variants implemented

### 3.1 Single-sample TD statement

For one transition `(s, a, r, s', done)`:

- prove the transition is included in the committed dataset,
- prove `q_online = Q_online(s)[a]`,
- prove `next_action = argmax_a' Q_online(s')[a']`,
- prove `q_target = Q_target(s')[next_action]`,
- prove `target = r + (1 - done) * gamma * q_target`,
- prove `loss = SmoothL1(q_online, target)`.

### 3.2 Minibatch TD statement

For a minibatch of transitions:

- prove each transition is included in the committed dataset,
- prove each per-sample target and loss is correct,
- prove `batch_loss = floor(sum(loss_i) / batch_size)` in fixed-point form.

---

## 4. Public inputs

### 4.1 Dataset-related public inputs

- `dataset_root`: Merkle root of the committed transition dataset

### 4.2 Model-related public inputs

- `checkpoint_sha256`: SHA-256 hash of the checkpoint file used to derive online/target Q-values

### 4.3 Arithmetic/configuration public inputs

- `loss_type = "smooth_l1"`
- `batch_size` for minibatch artifact
- `batch_loss_fp` for minibatch artifact

### 4.4 Implicit public constants in current prototype

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

## 5. Private witness

### 5.1 Data witness

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

### 5.2 Model witness / derived witness

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

---

## 6. Relation to be verified

## 6.1 Membership relation

For each transition:

1. Serialize transition into fixed-point leaf format.
2. Hash the leaf.
3. Verify the Merkle path against the public `dataset_root`.

This establishes that the sample comes from the committed dataset.

## 6.2 Double DQN target relation

For each transition:

1. Compute:
   - `q_online = Q_online(s)[a]`
2. Compute:
   - `next_action_online = argmax_a' Q_online(s')[a']`
3. Compute:
   - `q_target = Q_target(s')[next_action_online]`
4. Compute Bellman target:
   - `target = reward + (1 - done) * gamma * q_target`

All arithmetic is represented in fixed-point form in the current prototype.

## 6.3 TD loss relation

For each transition:

- `loss = SmoothL1(q_online, target)`

with beta = 1.0.

In fixed-point form:

- if `|delta| < beta`, then
  - `loss = delta^2 / (2 * beta)`
- else
  - `loss = |delta| - beta / 2`

where `delta = q_online - target`.

## 6.4 Batch loss relation

For minibatch artifact:

- `batch_loss_fp = floor(sum(loss_i) / batch_size)`

---

## 7. Fixed-point encoding

The prototype uses fixed-point encoding to make arithmetic explicit and ZK-friendly.

- real value `x` is encoded as:
  - `x_fp = round(x * FP_SCALE)`
- current scale:
  - `FP_SCALE = 1000`

Examples:
- reward `1.0` -> `1000`
- gamma `0.99` -> `990`

This keeps arithmetic simple and deterministic for artifact verification.

---

## 8. What is already faithful to training

The current MVP is already faithful to the implemented offline DQN training in these aspects:

- SmoothL1 loss matches the trainer,
- checkpoint is tied publicly by SHA-256,
- online network outputs are derived from the checkpoint,
- target network outputs are derived from the checkpoint,
- Double DQN target semantics are respected:
  - argmax from online net,
  - value from target net.

---

## 9. What is not yet fully proved

The current MVP does **not** yet prove:

1. that the checkpoint itself was produced by correct training,
2. that the minibatch was sampled according to a specific sampler rule,
3. that optimizer updates were performed correctly,
4. that target-network synchronization occurred correctly over time,
5. that a sequence of training steps was executed correctly.

This is why the current system should be described as:

> a pre-ZK verifiable artifact prototype for membership + TD-target/loss correctness,

not yet a full proof of training.

---

## 10. Stronger next statement

The next stronger statement after the current MVP is:

> Given a committed dataset and a public initial checkpoint hash, prove that one offline DQN update step was computed correctly, including forward pass, Bellman target, SmoothL1 TD loss, gradient computation, optimizer update, and resulting next checkpoint hash.

That will require:
- formalizing optimizer arithmetic,
- committing to pre-update and post-update weights,
- possibly quantizing model weights/activations more aggressively,
- deciding how to represent Adam/SGD in a proof-friendly way.

---

## 11. Recommended wording for paper/proposal

Recommended wording for the current stage:

> Our current prototype does not yet implement a full zero-knowledge proving backend. Instead, it formalizes and verifies the core statement structure needed for such a system: membership of sampled transitions in a committed dataset, Double-DQN-style Bellman target correctness, SmoothL1 TD loss correctness, batch-loss aggregation, and public anchoring of the model checkpoint via SHA-256.

---

## 12. Current concrete artifact fields

### 12.1 Single-sample artifact public fields

- `dataset_root`
- `loss_type`
- `checkpoint_sha256`

### 12.2 Single-sample witness fields

- `q_online_fp`
- `q_target_max_fp`
- `target_fp`
- `loss_fp`

### 12.3 Minibatch artifact public fields

- `dataset_root`
- `loss_type`
- `batch_size`
- `batch_loss_fp`
- `checkpoint_sha256`

### 12.4 Minibatch per-item witness fields

- transition
- Merkle membership data
- `q_online_fp`
- `q_target_max_fp`
- `target_fp`
- `loss_fp`

---

## 13. Summary

The MVP proof statement currently realized by the repository is:

> From a committed offline transition dataset and a publicly anchored checkpoint hash, verify that the sampled transitions belong to the dataset and that their Double-DQN Bellman targets and SmoothL1 TD losses are computed correctly, including minibatch-average loss.

This is the correct bridge between:
- committed offline data,
- RL-specific TD arithmetic,
- and a future zero-knowledge proof backend.