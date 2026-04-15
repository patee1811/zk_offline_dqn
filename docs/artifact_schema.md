# Artifact Schema Cleanup Notes

## Purpose

This document separates:

1. mandatory public inputs,
2. mandatory private witness fields,
3. optional debug / audit fields,

for the current pre-ZK artifact/verifier prototype.

The goal is to reduce ambiguity and prepare the statement for a future backend-ready design.

---

## 1. One-Step Update Artifact

### 1.1 Statement Role

This artifact proves one offline DQN SGD update step from a committed minibatch.

### 1.2 Mandatory Top-Level Keys

- `public`
- `items`
- `update_witness`
- `notes`

---

### 1.3 Mandatory Public Inputs

These are values the verifier must be allowed to see and check directly.

- `dataset_root`
- `batch_indices`
- `batch_size`
- `loss_type`
- `optimizer_type`
- `learning_rate_fp`
- `pre_checkpoint_sha256`
- `post_checkpoint_sha256`

### 1.4 Mandatory Private Witness

These are values required to witness correctness but should conceptually remain private in a true ZK system.

#### Per-item witness
- transition contents
- serialized leaf representation
- leaf hash
- Merkle authentication path
- per-sample TD witness values

#### Update witness
- recomputed batch loss witness
- pre-update online-network state
- pre-update target-network state
- gradients
- parameter deltas
- post-update online-network state

### 1.5 Optional Debug / Audit Fields

These fields are useful now in the Python prototype, but should not automatically be treated as essential long-term statement fields.

- `learning_rate_real`
- raw tensor summaries
- file paths
- human-readable notes
- redundant hashes that can be recomputed
- any duplicated TD-side values already derivable from other fields

---

## 2. Short-Trace Update Artifact

### 2.1 Statement Role

This artifact proves a short sequence of chained one-step updates.

### 2.2 Mandatory Top-Level Keys

- `public`
- `steps`
- `notes`

---

### 2.3 Mandatory Public Inputs

- `dataset_root`
- `trace_batch_indices`
- `num_steps`
- `batch_size`
- `loss_type`
- `optimizer_type`
- `learning_rate_fp`
- `sampling_rule_type`
- `start_offset`
- `target_sync_every`
- `initial_checkpoint_sha256`
- `final_checkpoint_sha256`

### 2.4 Mandatory Private Witness

For each step:
- committed minibatch witness
- per-step TD witness
- per-step update witness
- intermediate checkpoint states
- synchronization-relevant witness data

### 2.5 Optional Debug / Audit Fields

- convenience checkpoint path hints
- human-readable notes
- local execution metadata

---

## 3. Cleanup Rules

### Rule 1
If a field is always recomputable from public inputs, do not keep it as a mandatory stored field unless it is needed for audit convenience.

### Rule 2
If a field is needed only for debugging failed runs, classify it as debug / audit rather than part of the core statement.

### Rule 3
If a field is required for the verifier to check correctness, keep it in the mandatory public or witness set.

### Rule 4
Prefer one canonical location for each piece of information.
Avoid storing the same semantic value in multiple places unless one copy is clearly labeled as redundant debug output.

---

## 4. Immediate Cleanup Targets

### One-step artifact
- identify redundant hashes
- identify redundant tensor summaries
- identify duplicated loss-related values
- identify path fields that are only for debugging

### Short-trace artifact
- identify duplicated batch information
- identify step-level fields that can be recomputed from public trace parameters
- identify notes fields that should not be part of the core artifact contract

---

## 5. Next Action After This Document

After this schema note is written, the next implementation step is:

1. inspect one real one-step artifact,
2. inspect one real short-trace artifact,
3. classify every field into:
   - mandatory public,
   - mandatory witness,
   - optional debug,
4. then update exporters so the artifact format becomes cleaner and more stable.

---

## 6. One-Step Artifact Inspection Result

### Top-level

#### Keep as core structure
- public
- items
- update_witness

#### Optional debug / audit
- notes

---

### Public

#### Mandatory public
- dataset_root
- batch_indices
- batch_size
- loss_type
- optimizer_type
- learning_rate_fp
- pre_checkpoint_sha256
- post_checkpoint_sha256

#### Optional debug / audit
- learning_rate_real

---

### items[0]

#### Mandatory witness
- transition
- leaf
- merkle_path
- td_witness

#### Likely redundant or debug / audit
- index
- leaf_hash
- debug

Notes:
- `leaf_hash` is likely recomputable from `leaf`.
- `index` may be redundant if batch order is already fixed by `batch_indices`.

---

### update_witness

#### Mandatory witness
- batch_loss_fp
- gradient_tensors
- delta_tensors

#### Likely debug / audit
- batch_loss_real_for_training
- pre_online_state_sha256
- post_online_state_sha256
- target_state_sha256
- parameter_count

#### Needs deeper inspection
- parameter_summaries

---

## 7. Nested One-Step Field Inspection Result

### td_witness

#### Mandatory witness
- q_online_fp
- q_target_max_fp
- target_fp
- loss_fp

Interpretation:
These are the core TD-side witness values for the current one-step statement.

---

### debug

#### Optional debug / audit
- q_online_real_for_debug
- q_next_online_for_debug
- q_next_target_for_debug
- next_action_online_for_debug
- q_target_max_real_for_debug

Interpretation:
These values are useful for human inspection and debugging, but they should not be treated as part of the long-term core artifact contract.

---

### parameter_summaries

Current keys:
- name
- shape
- numel
- pre_param_sha256
- grad_sha256
- post_param_sha256
- delta_sha256
- pre_norm
- grad_norm
- post_norm
- delta_norm
- pre_mean
- grad_mean
- post_mean
- delta_mean

#### Current classification
Likely optional debug / audit

Interpretation:
These summaries are useful for sanity checking and manual inspection, but the core statement already has the stronger tensor-level witness through:
- gradient_tensors
- delta_tensors

So parameter summaries should not automatically be treated as mandatory long-term artifact fields.

---

### gradient_tensors

#### Mandatory witness
- net.0.weight
- net.0.bias
- net.2.weight
- net.2.bias
- net.4.weight
- net.4.bias

Interpretation:
These are currently core witness fields for one-step gradient consistency in the Python prototype.

---

### delta_tensors

#### Mandatory witness
- net.0.weight
- net.0.bias
- net.2.weight
- net.2.bias
- net.4.weight
- net.4.bias

Interpretation:
These are currently core witness fields for one-step parameter-update consistency in the Python prototype.

---

## 8. One-Step Artifact Schema v1 (working classification)

### Core public
- dataset_root
- batch_indices
- batch_size
- loss_type
- optimizer_type
- learning_rate_fp
- pre_checkpoint_sha256
- post_checkpoint_sha256

### Core witness
- items[].transition
- items[].leaf
- items[].merkle_path
- items[].td_witness
- update_witness.batch_loss_fp
- update_witness.gradient_tensors
- update_witness.delta_tensors

### Audit / debug
- public.learning_rate_real
- items[].index
- items[].leaf_hash
- items[].debug
- update_witness.batch_loss_real_for_training
- update_witness.pre_online_state_sha256
- update_witness.post_online_state_sha256
- update_witness.target_state_sha256
- update_witness.parameter_count
- update_witness.parameter_summaries
- notes

---

## 9. Short-Trace Artifact Inspection Result

### Top-level

#### Keep as core structure
- public
- steps

#### Optional debug / audit
- notes

---

### Public

#### Mandatory public
- dataset_root
- trace_batch_indices
- num_steps
- batch_size
- loss_type
- optimizer_type
- learning_rate_fp
- sampling_rule_type
- start_offset
- target_sync_every
- initial_checkpoint_sha256
- final_checkpoint_sha256

---

### steps[0]

#### Core per-step structure
- step_index
- input_checkpoint_sha256
- raw_output_checkpoint_sha256
- next_checkpoint_sha256
- target_sync_applied
- one_step_artifact

#### Likely redundant or debug / audit
- raw_output_checkpoint_path
- next_checkpoint_path

Interpretation:
- all remaining `*_path` fields are local debugging conveniences or operational helpers
- `one_step_artifact` is the real nested witness

### Cleanup decisions already applied
- removed `steps[].expected_batch_indices`
- removed `public.learning_rate_real`
- removed `steps[].batch_indices`
- removed `steps[].one_step_artifact_path`
- removed `steps[].input_checkpoint_path`
- removed `notes.data_path`
- removed `notes.work_dir`
- removed `notes.statement_scope`
- removed `notes.limitations`

Interpretation:
- `expected_batch_indices` is recomputable from:
  - `sampling_rule_type`
  - `start_offset`
  - `batch_size`
  - `step_index`
- batch identity is already available in:
  - `public.trace_batch_indices`
  - `steps[].one_step_artifact.public.batch_indices`
- `one_step_artifact_path` was only a local filesystem convenience;
  verification can materialize the embedded artifact into a temporary file when needed
- `input_checkpoint_path` and the removed notes fields were only local execution metadata

A cleaner schema should prefer one canonical location for public batch identity and avoid storing local-path assumptions in the artifact contract.

---

### notes

#### Optional debug / audit
- merkle_path
- initial_checkpoint_path
- final_checkpoint_path

Interpretation:
These fields are still kept because the current Python verifier uses them operationally, but they should not be treated as long-term core statement fields.

---

## 10. Short-Trace Artifact Schema v1 (working classification)

### Core public
- dataset_root
- trace_batch_indices
- num_steps
- batch_size
- loss_type
- optimizer_type
- learning_rate_fp
- sampling_rule_type
- start_offset
- target_sync_every
- initial_checkpoint_sha256
- final_checkpoint_sha256

### Core witness / trace structure
- steps[].step_index
- steps[].input_checkpoint_sha256
- steps[].raw_output_checkpoint_sha256
- steps[].next_checkpoint_sha256
- steps[].target_sync_applied
- steps[].one_step_artifact

### Audit / debug
- steps[].raw_output_checkpoint_path
- steps[].next_checkpoint_path
- notes.merkle_path
- notes.initial_checkpoint_path
- notes.final_checkpoint_path

### Current recommendation
Prefer one canonical public location for trace batch identity:
- `public.trace_batch_indices`

Use nested one-step artifacts only when needed for witness composition or one-step consistency checking.