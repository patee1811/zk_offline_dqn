# One-Step Artifact Field Classification

## Top-level

### Keep as core structure
- public
- items
- update_witness

### Optional debug / audit
- notes

---

## Public

### Mandatory public
- dataset_root
- batch_indices
- batch_size
- loss_type
- optimizer_type
- learning_rate_fp
- pre_checkpoint_sha256
- post_checkpoint_sha256

### Optional debug / audit
- learning_rate_real

---

## items[0]

### Mandatory witness
- transition
- leaf
- merkle_path
- td_witness

### Likely redundant or debug / audit
- index
- leaf_hash
- debug

Notes:
- `leaf_hash` is likely recomputable from `leaf`.
- `index` may be redundant if batch order is already fixed by `batch_indices`.

---

## update_witness

### Mandatory witness
- batch_loss_fp
- gradient_tensors
- delta_tensors

### Likely debug / audit
- batch_loss_real_for_training
- pre_online_state_sha256
- post_online_state_sha256
- target_state_sha256
- parameter_count

### Needs deeper inspection
- parameter_summaries

---

## Current interpretation

The current one-step artifact already has a usable structure, but it still mixes:
- core statement fields,
- witness fields,
- and audit/debug convenience fields.

The next step is to inspect nested structures inside:
- `td_witness`
- `debug`
- `parameter_summaries`

before deciding which fields should remain in the long-term artifact contract.

## Nested field inspection result

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

## One-step artifact schema v1 (working classification)

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