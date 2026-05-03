# Artifact Schema Cleanup Notes

## 0. Current Schema Versions and Verifier Extensions

The repository currently uses explicit artifact schema versions for the main verification artifacts.

| Artifact | Current schema version | Main verifier |
|---|---|---|
| Minibatch TD artifact | `minibatch_td_v1` | `scripts/artifacts_export/verify_minibatch_td_artifact.py` |
| One-step update artifact | `one_step_update_v1` | `scripts/artifacts_export/verify_one_step_update_artifact.py` |
| Short-trace update artifact | `short_trace_update_v2` | `scripts/artifacts_export/verify_short_trace_update_artifact.py` |

All schema-aware verifiers reject artifacts when:

- `schema_version` is missing;
- `schema_version` does not match the expected version.

This prevents stale or incompatible artifacts from being silently accepted.

### Minibatch TD v1 Extension

The current `minibatch_td_v1` artifact includes the following core TD witness fields:

```text
q_online_fp
next_action_online
q_target_max_fp
target_fp
loss_fp
```

The `next_action_online` field was promoted into `td_witness` because it is part of the Double-DQN TD statement:

```text
next_action_online = argmax_a Q_online(s')
q_target_max_fp = Q_target(s')[next_action_online]
```

This avoids relying on debug-only fields for statement-level verification.

### Forward TD Consistency Verifier

The repository includes an additional verifier:

```text
scripts/artifacts_export/verify_forward_td_consistency.py
```

This verifier checks that the TD witness values in a minibatch artifact are consistent with the actual checkpoint forward pass.

For each item, it recomputes:

```text
Q_online(s)[a]
argmax_a Q_online(s')
Q_target(s')[argmax_a Q_online(s')]
```

and compares the fixed-point values against:

```text
q_online_fp
next_action_online
q_target_max_fp
```

This strengthens the TD artifact from pure TD arithmetic checking to checkpoint-grounded TD witness checking.

### Negative Verification Tests

The repository includes a negative-test runner:

```text
scripts/experiments/run_negative_verification_tests.py
```

The current negative tests check that the minibatch TD verifier accepts a valid artifact and rejects the following tampered artifacts:

| Case | Expected result | Failure mode |
|---|---:|---|
| `valid_control` | accept | unchanged valid artifact |
| `tamper_loss_fp` | reject | TD loss witness no longer matches recomputed SmoothL1 loss |
| `tamper_reward` | reject | Bellman target and loss no longer match the transition |
| `tamper_checkpoint_sha256` | reject | public checkpoint hash no longer matches the checkpoint file |
| `tamper_leaf_hash` | reject | serialized transition leaf no longer matches the claimed leaf hash |
| `tamper_merkle_path` | reject | Merkle path no longer reconstructs the public dataset root |

These tests cover both arithmetic tampering and committed-data membership tampering.

### Regression Commands

After updating the schema documentation, the current regression checklist is:

```powershell
$env:PYTHONPATH="."

python -m compileall zk_offline_dqn scripts

python scripts/artifacts_export/verify_minibatch_td_artifact.py

python scripts/artifacts_export/verify_forward_td_consistency.py `
  --artifact artifacts/minibatch_td_from_dataset.json `
  --checkpoint models/offline_dqn_with_target_seed42_best.pt

python scripts/artifacts_export/verify_one_step_update_artifact.py

$env:SHORT_TRACE_ARTIFACT_PATH="artifacts/short_trace_update_artifact.json"
$env:SHORT_TRACE_MERKLE_PATH="artifacts/cartpole_dqn_eps010_merkle.json"
$env:SHORT_TRACE_INITIAL_CHECKPOINT_PATH="models/offline_dqn_with_target_seed42_best.pt"
$env:SHORT_TRACE_FINAL_CHECKPOINT_PATH="artifacts/short_trace_work/step_1_post_synced_4_5_6_7.pt"

python scripts/artifacts_export/verify_short_trace_update_artifact.py

python scripts/experiments/run_negative_verification_tests.py
```

Expected key outputs:

```text
verification_passed = True
all_forward_ok = True
all_tests_passed = True
```

## Purpose

This document separates:

1. mandatory public inputs,
2. mandatory private witness fields,
3. optional debug / audit fields,

for the current pre-ZK artifact/verifier prototype.

The goal is to reduce ambiguity and prepare the statement for a future backend-ready design.

Current implementation status:
- the TD and one-step artifacts remain audit-oriented Python verifier artifacts;
- the short-trace artifact has completed the B3 cleanup milestone;
- short-trace local filesystem paths are no longer stored in persistent `notes`;
- the short-trace verifier receives operational paths from the benchmark/runtime environment.

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

At the end of B3, no persistent debug metadata is required inside the artifact itself.
Operational paths are now supplied externally by the benchmark/verifier when needed.

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

## 4. Cleanup Status

### One-step artifact
- identify redundant hashes
- identify redundant tensor summaries
- identify duplicated loss-related values
- identify path fields that are only for debugging

Status:
The one-step artifact has a working classification, but it still intentionally keeps audit-friendly fields such as parameter summaries, hashes, and debug values. These are useful for the Python prototype and should be revisited before translating the statement to a circuit or zkVM backend.

### Short-trace artifact
- duplicated batch information has been reduced;
- step-local filesystem paths have been removed;
- `notes` no longer carries operational metadata;
- target-sync checking now uses `steps[].sync_state_witness`;
- final checkpoint path is supplied externally by the benchmark/verifier rather than stored in the artifact.

---

## 5. Current Next Actions

The immediate inspection and short-trace cleanup tasks have already been completed through the B3 milestone. The next schema work should be:

1. finish the same cleanup pass for the one-step artifact,
2. define a backend-ready schema that separates:
   - public inputs,
   - private witness values,
   - prototype-only audit/debug fields,
3. decide whether `notes` should remain as an empty compatibility key or be removed in a future breaking schema version,
4. reduce raw tensor and floating-point dependence before moving to a proving backend,
5. document how benchmark metadata differs from artifact metadata.

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
- notes

Interpretation:
`notes` is now kept only as an empty placeholder structure for compatibility. It no longer carries operational metadata after B3.

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
- sync_state_witness
- one_step_artifact

Interpretation:
- `one_step_artifact` is the real nested witness
- `sync_state_witness` is the current witness extension that lets the verifier check target-sync semantics without relying on local checkpoint paths inside each step

### Cleanup decisions already applied
- removed `steps[].expected_batch_indices`
- removed `public.learning_rate_real`
- removed `steps[].batch_indices`
- removed `steps[].one_step_artifact_path`
- removed `steps[].input_checkpoint_path`
- removed `steps[].raw_output_checkpoint_path`
- removed `steps[].next_checkpoint_path`
- removed `notes.data_path`
- removed `notes.work_dir`
- removed `notes.statement_scope`
- removed `notes.limitations`
- removed `notes.merkle_path`
- removed `notes.initial_checkpoint_path`
- removed `notes.final_checkpoint_path`
- added `steps[].sync_state_witness`

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
- `input_checkpoint_path`, `raw_output_checkpoint_path`, and `next_checkpoint_path` were local path assumptions;
  sync verification now uses embedded state witnesses instead
- `notes.merkle_path`, `notes.initial_checkpoint_path`, and `notes.final_checkpoint_path` were removed by the end of B3;
  the verifier/benchmark now supplies them externally through environment variables
- the other removed notes fields were only local execution metadata

A cleaner schema should prefer one canonical location for public batch identity and avoid storing local-path assumptions in the artifact contract.

---

### sync_state_witness

#### Mandatory witness
- raw_output_online_state_dict
- raw_output_target_state_dict
- next_target_state_dict

Interpretation:
These fields are the minimal current witness needed for the verifier to check whether target synchronization was applied correctly, without loading per-step checkpoints from local filesystem paths.

---

### notes

#### Optional debug / audit
- none

Interpretation:
After B3, the artifact no longer requires persistent path metadata inside `notes`.
The verifier receives operational paths externally from the benchmark/runtime environment.

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
- steps[].sync_state_witness
- steps[].one_step_artifact

### Audit / debug
- none stored inside the artifact after B3

### Current recommendation
Prefer one canonical public location for trace batch identity:
- `public.trace_batch_indices`

Use nested one-step artifacts only when needed for witness composition or one-step consistency checking.

---

## 11. Benchmark Metadata vs Artifact Metadata

The benchmark runner may record fields that are useful for reproducing a local run but are not part of the artifact contract.

Current benchmark-only metadata includes:
- `artifact_path`
- `work_dir`
- `final_checkpoint_path`
- exporter stdout/stderr
- verifier stdout/stderr
- wall-clock export and verification timings

Current short-trace verifier runtime inputs include:
- `SHORT_TRACE_ARTIFACT_PATH`
- `SHORT_TRACE_MERKLE_PATH`
- `SHORT_TRACE_INITIAL_CHECKPOINT_PATH`
- `SHORT_TRACE_FINAL_CHECKPOINT_PATH`

Interpretation:
These values are operational handles for the Python prototype. They help the benchmark rerun verification and recompute file hashes, but they should not be treated as persistent public inputs or private witness fields in the backend-ready statement.
