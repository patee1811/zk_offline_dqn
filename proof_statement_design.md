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

---

### 0.1 Minibatch TD v1 Extension

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

The public section of `minibatch_td_v1` also includes model-state commitments:

```text
checkpoint_sha256
checkpoint_commitment_type
online_state_dict_key
online_state_dict_sha256
target_state_dict_sha256
```

`checkpoint_sha256` anchors the checkpoint file.

`online_state_dict_sha256` and `target_state_dict_sha256` anchor the canonical sorted tensor contents of the online and target networks.

The canonical commitment helper is implemented in:

```text
zk_offline_dqn/commitments.py
```

---

### 0.2 One-Step Update v1 Extension

The current `one_step_update_v1` artifact includes both file-level checkpoint hashes and canonical model-state commitments.

The public section includes:

```text
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

The one-step TD witness now includes:

```text
q_online_fp
next_action_online
q_target_max_fp
target_fp
loss_fp
```

The one-step verifier recomputes `next_action_online` and `q_target_max_fp` from the pre-update checkpoint:

```text
next_action_online = argmax_a Q_online(s')
q_target_max_fp = Q_target(s')[next_action_online]
```

Expected one-step verifier output includes:

```text
next_action_match=True
q_target_max_match=True
```

The one-step verifier also recomputes these commitments from the pre/post checkpoints and checks:

```text
pre_online_state_dict_sha256
pre_target_state_dict_sha256
post_online_state_dict_sha256
post_target_state_dict_sha256
```

This makes the one-step statement more explicit: the verifier anchors both the checkpoint files and the canonical tensor contents of the online/target networks before and after the SGD update, while also checking the Double-DQN action-selection/value-selection relation inside the one-step TD witness.

Because the short-trace verifier calls the one-step verifier for each nested step, this also strengthens each one-step relation inside the current short-trace verifier.

---

### 0.3 Forward TD Consistency Verifier

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

---

### 0.4 Negative Verification Tests

The repository includes a minibatch TD negative-test runner:

```text
scripts/experiments/run_negative_verification_tests.py
```

The minibatch TD negative tests check that the minibatch TD verifier accepts a valid artifact and rejects the following tampered artifacts:

| Case | Expected result | Failure mode |
|---|---:|---|
| `valid_control` | accept | unchanged valid minibatch TD artifact |
| `tamper_loss_fp` | reject | TD loss witness no longer matches recomputed SmoothL1 loss |
| `tamper_reward` | reject | Bellman target and loss no longer match the transition |
| `tamper_checkpoint_sha256` | reject | public checkpoint hash no longer matches the checkpoint file |
| `tamper_online_state_dict_sha256` | reject | online-network state-dict commitment no longer matches the canonical checkpoint tensor contents |
| `tamper_leaf_hash` | reject | serialized transition leaf no longer matches the claimed leaf hash |
| `tamper_merkle_path` | reject | Merkle path no longer reconstructs the public dataset root |

The repository also includes a short-trace negative-test runner:

```text
scripts/experiments/run_short_trace_negative_tests.py
```

The short-trace negative tests check that the short-trace verifier accepts valid contiguous and seeded traces while rejecting the following tampered artifacts:

| Case | Expected result | Failure mode |
|---|---:|---|
| `valid_contiguous` | accept | unchanged valid contiguous short-trace artifact |
| `valid_seeded` | accept | unchanged valid seeded-permutation short-trace artifact |
| `tamper_contiguous_public_batch` | reject | public contiguous trace batch no longer matches the declared contiguous rule |
| `tamper_seeded_public_batch` | reject | public seeded trace batch no longer matches the seeded permutation |
| `tamper_sampling_seed` | reject | public seed no longer reconstructs the declared trace batches |
| `tamper_dataset_size` | reject | public dataset size no longer reconstructs the declared seeded batches |
| `tamper_final_checkpoint_sha256` | reject | public final checkpoint file hash no longer matches the final checkpoint |
| `tamper_final_online_state_dict_sha256` | reject | final online-network state-dict commitment no longer matches the final checkpoint tensor contents |

Together, these negative tests cover:

- TD arithmetic tampering;
- checkpoint file-hash tampering;
- canonical model-state commitment tampering;
- committed-data membership tampering;
- short-trace sampling-rule tampering;
- short-trace boundary-checkpoint tampering.

Run the minibatch TD negative tests:

```bash
python scripts/experiments/run_negative_verification_tests.py
```

Expected minibatch TD output includes:

```text
valid_control_accept = True
tamper_loss_fp_accept = False
tamper_reward_accept = False
tamper_checkpoint_sha256_accept = False
tamper_online_state_dict_sha256_accept = False
tamper_leaf_hash_accept = False
tamper_merkle_path_accept = False
all_tests_passed = True
```

Run the short-trace negative tests:

```bash
python scripts/experiments/run_short_trace_negative_tests.py
```

Expected short-trace output includes:

```text
valid_contiguous_accept = True
valid_seeded_accept = True
tamper_contiguous_public_batch_accept = False
tamper_seeded_public_batch_accept = False
tamper_sampling_seed_accept = False
tamper_dataset_size_accept = False
tamper_final_checkpoint_sha256_accept = False
tamper_final_online_state_dict_sha256_accept = False
all_tests_passed = True
```

The negative-test summaries are written to:

```text
artifacts/negative_tests/summary.csv
artifacts/short_trace_negative_tests/summary.csv
```

---

### 0.5 Regression Commands

After updating schema-related code or documentation, the current regression checklist is:

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
$env:SHORT_TRACE_WORK_DIR="artifacts/short_trace_work"

python scripts/artifacts_export/verify_short_trace_update_artifact.py

$env:SHORT_TRACE_ARTIFACT_PATH="artifacts/short_trace_seeded_artifact.json"
$env:SHORT_TRACE_FINAL_CHECKPOINT_PATH="artifacts/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt"
$env:SHORT_TRACE_WORK_DIR="artifacts/short_trace_seeded_work"

python scripts/artifacts_export/verify_short_trace_update_artifact.py

python scripts/experiments/run_negative_verification_tests.py
python scripts/experiments/run_short_trace_negative_tests.py
```

Expected key outputs:

```text
verification_passed = True
all_forward_ok = True
next_action_match=True
q_target_max_match=True
one_step_canonical_commitments_ok = True
short_trace_canonical_boundary_commitments_ok = True
all_sampling_rule_ok = True
all_tests_passed = True
```

---

## Purpose

This document separates:

1. mandatory public inputs,
2. mandatory private witness fields,
3. optional debug / audit fields,

for the current pre-ZK artifact/verifier prototype.

The goal is to reduce ambiguity and prepare the statement for a future backend-ready design.

Current implementation status:

- the TD and one-step artifacts remain audit-oriented Python verifier artifacts;
- the minibatch TD artifact now includes canonical checkpoint/model-state commitments;
- the one-step artifact now includes canonical pre/post model-state commitments;
- the one-step artifact now includes `next_action_online` as a core TD witness field;
- the one-step verifier now checks both `next_action_online` and `q_target_max_fp` against the pre-update checkpoint networks;
- one-step artifacts no longer store local runtime paths in persistent `notes`;
- the one-step verifier receives checkpoint paths from runtime inputs such as `ONE_STEP_CHECKPOINT_PATH` and `ONE_STEP_POST_CHECKPOINT_PATH`;
- the short-trace artifact has completed the B3 cleanup milestone;
- short-trace local filesystem paths are no longer stored in persistent `notes`;
- the short-trace verifier receives operational paths from the benchmark/runtime environment;
- the short-trace verifier calls the one-step verifier internally, so one-step verifier strengthening also strengthens nested short-trace update checks.

---

## 1. One-Step Update Artifact

### 1.1 Statement Role

This artifact proves one offline DQN SGD update step from a committed minibatch.

One-step artifacts do not store local runtime paths in `notes`. The verifier receives the required checkpoint paths through runtime inputs such as `ONE_STEP_CHECKPOINT_PATH` and `ONE_STEP_POST_CHECKPOINT_PATH`.

The current statement is still a **pre-ZK Python verifier statement**, not a production proving backend. It is useful because it makes the update relation explicit before translating the relation into a zkVM, SNARK, or circuit-compatible backend.

---

### 1.2 Mandatory Top-Level Keys

- `schema_version`
- `public`
- `items`
- `update_witness`
- `notes`

---

### 1.3 Mandatory Public Inputs

These are values the verifier must be allowed to see and check directly.

#### Core public inputs

- `dataset_root`
- `batch_indices`
- `batch_size`
- `loss_type`
- `optimizer_type`
- `learning_rate_fp`

#### File-level checkpoint commitments

- `pre_checkpoint_sha256`
- `post_checkpoint_sha256`

#### Canonical model-state commitments

- `checkpoint_commitment_type`
- `pre_online_state_dict_key`
- `pre_online_state_dict_sha256`
- `pre_target_state_dict_sha256`
- `post_online_state_dict_key`
- `post_online_state_dict_sha256`
- `post_target_state_dict_sha256`

---

### 1.4 One-Step Canonical Model-State Commitments

The current `one_step_update_v1` public section includes both file-level checkpoint hashes and canonical model-state commitments:

```text
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

The current `one_step_update_v1` TD witness includes:

```text
q_online_fp
next_action_online
q_target_max_fp
target_fp
loss_fp
```

The one-step verifier recomputes the following values from the pre-update checkpoint networks:

```text
next_action_online = argmax_a Q_online(s')
q_target_max_fp = Q_target(s')[next_action_online]
```

and checks:

```text
next_action_match=True
q_target_max_match=True
```

The one-step verifier also recomputes canonical model-state commitments from the pre/post checkpoints and checks:

```text
pre_online_state_dict_sha256
pre_target_state_dict_sha256
post_online_state_dict_sha256
post_target_state_dict_sha256
```

This makes the one-step statement more explicit: the verifier anchors both the checkpoint files and the canonical tensor contents of the online/target networks before and after the SGD update, while also checking the Double-DQN action-selection/value-selection relation inside the one-step TD witness.

Because the short-trace verifier calls the one-step verifier for each nested step, this also strengthens each one-step relation inside the current short-trace verifier.

---

### 1.5 Mandatory Private Witness

These are values required to witness correctness but should conceptually remain private in a true ZK system.

#### Per-item witness

- transition contents;
- serialized leaf representation;
- leaf hash;
- Merkle authentication path;
- per-sample TD witness values:
  - `q_online_fp`;
  - `next_action_online`;
  - `q_target_max_fp`;
  - `target_fp`;
  - `loss_fp`.

#### Update witness

- recomputed batch loss witness;
- gradients;
- parameter deltas.

#### Conceptual checkpoint witness

The current Python verifier loads checkpoints from runtime inputs, not from persistent artifact `notes`. Conceptually, the statement depends on:

- pre-update online-network state;
- pre-update target-network state;
- post-update online-network state;
- post-update target-network state.

In a future backend-ready artifact, these should be represented more cleanly as witness or committed state objects, not as local file paths.

---

### 1.6 Optional Debug / Audit Fields

These fields are useful now in the Python prototype, but should not automatically be treated as essential long-term statement fields.

- optional audit sidecars outside the durable artifact;
- human-readable documentation outside the durable artifact;
- raw tensor summaries;
- redundant hashes that can be recomputed;
- any duplicated TD-side values already derivable from other fields;
- floating-point training loss logs;
- parameter norm or mean summaries.

---

## 2. Short-Trace Update Artifact

### 2.1 Statement Role

This artifact proves a short sequence of chained one-step updates.

For nested one-step verification, the short-trace verifier reconstructs per-step checkpoint paths from `SHORT_TRACE_WORK_DIR` and passes them to the one-step verifier through runtime environment variables. These paths are operational handles, not persistent artifact fields.

The short-trace artifact currently embeds nested one-step artifacts and checks:

- each one-step update relation;
- checkpoint chaining;
- target-network synchronization semantics;
- deterministic contiguous sampling-rule enforcement;
- seeded-permutation sampling-rule enforcement.

---

### 2.2 Mandatory Top-Level Keys

- `schema_version`
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
- `sampling_seed`
- `dataset_size`
- `target_sync_every`
- `initial_checkpoint_sha256`
- `final_checkpoint_sha256`

---

### 2.4 Mandatory Private Witness

For each step:

- committed minibatch witness;
- per-step TD witness;
- per-step update witness;
- intermediate checkpoint states;
- synchronization-relevant witness data.

---

### 2.5 Nested One-Step Verification

Each short-trace step contains a nested one-step artifact:

```text
steps[].one_step_artifact
```

The short-trace verifier delegates each nested update relation to the one-step verifier.

Therefore, the short-trace verifier currently inherits the following one-step checks for each step:

- committed minibatch membership;
- TD target and TD loss checking;
- `next_action_online` checking;
- `q_target_max_fp` checking;
- batch-loss checking;
- pre/post checkpoint file-hash checking;
- pre/post canonical model-state commitment checking;
- gradient recomputation checking;
- delta-tensor checking;
- SGD update checking;
- target-network invariance for the one-step update.

---

### 2.6 Optional Debug / Audit Fields

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

### Rule 5

Separate persistent artifact semantics from local runtime handles.

For example, local filesystem paths should not be treated as durable public inputs in the long-term backend-ready schema.

### Rule 6

When a checkpoint is used as a statement anchor, prefer both:

- file-level checkpoint hash; and
- canonical model-state tensor-content hash.

This reduces dependence on framework-specific serialization details.

---

## 4. Cleanup Status

### One-step artifact

Completed improvements:

- `schema_version` added;
- canonical pre/post online state-dict commitments added;
- canonical pre/post target state-dict commitments added;
- `next_action_online` added to one-step `td_witness`;
- one-step verifier checks `next_action_online`;
- one-step verifier checks `q_target_max_fp` by recomputing the Double-DQN selected target value from the pre-update checkpoint;
- verifier checks canonical commitments;
- runtime checkpoint/data/Merkle paths have been removed from one-step `notes`;
- one-step `notes` is now an empty compatibility object;
- one-step verification receives checkpoint paths through runtime inputs or defaults;
- short-trace verification passes per-step checkpoint paths to nested one-step verification;
- short-trace verifier inherits stronger nested one-step checks.

Still to revisit:

- identify redundant tensor summaries;
- identify duplicated loss-related values;
- decide whether empty `notes` should remain as a compatibility key or be removed in a future breaking schema version;
- reduce raw tensor and floating-point dependence before translating to a proving backend.

Status:

The one-step artifact has a working classification and no longer stores local checkpoint/data/Merkle paths in `notes`. It still intentionally keeps audit-friendly witness-heavy fields such as raw gradients and delta tensors. These are useful for the Python prototype and should be revisited before translating the statement to a circuit or zkVM backend.

---

### Short-trace artifact

Completed improvements:

- duplicated batch information has been reduced;
- step-local filesystem paths have been removed;
- `notes` no longer carries operational metadata;
- target-sync checking now uses `steps[].sync_state_witness`;
- final checkpoint path is supplied externally by the benchmark/verifier rather than stored in the artifact;
- trace-boundary canonical model-state commitments are explicit public fields;
- seeded-permutation sampling metadata is explicit in public fields;
- short-trace negative tests cover both contiguous and seeded sampling failures.

Still to revisit:

- reduce embedded nested artifact size;
- decide whether nested one-step artifacts should be embedded fully or represented by commitments plus external witnesses;
- clarify whether `notes` should remain as an empty compatibility key or be removed in a future breaking schema version.

---

## 5. Current Next Actions

The immediate inspection and short-trace cleanup tasks have already been completed through the B3 milestone.

Canonical model-state commitments have now been propagated to:

- minibatch TD artifacts;
- one-step update artifacts;
- short-trace boundary checkpoints.

The next schema work should be:

1. finish the cleanup pass for the one-step artifact;
2. define a backend-ready schema that separates:
   - public inputs,
   - private witness values,
   - prototype-only audit/debug fields;
3. decide whether `notes` should remain as an empty compatibility key or be removed in a future breaking schema version;
4. reduce raw tensor and floating-point dependence before moving to a proving backend;
5. document how benchmark metadata differs from artifact metadata;
6. define whether nested one-step artifacts should remain embedded or be replaced by commitment references;
7. add negative-test coverage for one-step schema-cleanup edge cases once the one-step artifact is simplified.

---

## 6. One-Step Artifact Inspection Result

### Top-level

#### Keep as core structure

- `schema_version`
- `public`
- `items`
- `update_witness`

#### Empty compatibility key

- `notes`

`notes` is currently kept as `{}` for schema compatibility. It should not contain local checkpoint paths, dataset paths, Merkle paths, or human-readable statement metadata.

---

### Public

#### Mandatory public

- `dataset_root`
- `batch_indices`
- `batch_size`
- `loss_type`
- `optimizer_type`
- `learning_rate_fp`
- `pre_checkpoint_sha256`
- `post_checkpoint_sha256`
- `checkpoint_commitment_type`
- `pre_online_state_dict_key`
- `pre_online_state_dict_sha256`
- `pre_target_state_dict_sha256`
- `post_online_state_dict_key`
- `post_online_state_dict_sha256`
- `post_target_state_dict_sha256`

#### Optional debug / audit

- none currently required in `public`.

---

### items[0]

#### Mandatory witness

- `transition`
- `leaf`
- `merkle_path`
- `td_witness`

#### Likely redundant or debug / audit

- `index`
- `leaf_hash`
- `debug`

Notes:

- `leaf_hash` is recomputable from `leaf`;
- `index` may be redundant if batch order is already fixed by `batch_indices`;
- `debug` is useful for human inspection but not part of the long-term core statement.

---

### update_witness

#### Mandatory witness

- `batch_loss_fp`
- `gradient_tensors`
- `delta_tensors`

#### Likely debug / audit

- `batch_loss_real_for_training`
- `pre_online_state_sha256`
- `post_online_state_sha256`
- `target_state_sha256`
- `parameter_count`
- `parameter_summaries`

---

## 7. Nested One-Step Field Inspection Result

### td_witness

#### Mandatory witness

- `q_online_fp`
- `next_action_online`
- `q_target_max_fp`
- `target_fp`
- `loss_fp`

Interpretation:

These are the core TD-side witness values for the current one-step statement.

`next_action_online` is part of the Double-DQN target semantics and should remain in `td_witness`, not only in a debug field.

The one-step verifier recomputes:

```text
next_action_online = argmax_a Q_online(s')
q_target_max_fp = Q_target(s')[next_action_online]
```

from the pre-update checkpoint and checks:

```text
next_action_match=True
q_target_max_match=True
```

---

### debug

#### Optional debug / audit

- `q_online_real_for_debug`
- `q_next_online_for_debug`
- `q_next_target_for_debug`
- `next_action_online_for_debug`
- `q_target_max_real_for_debug`

Interpretation:

These values are useful for human inspection and debugging, but they should not be treated as part of the long-term core artifact contract.

---

### parameter_summaries

Current keys:

- `name`
- `shape`
- `numel`
- `pre_param_sha256`
- `grad_sha256`
- `post_param_sha256`
- `delta_sha256`
- `pre_norm`
- `grad_norm`
- `post_norm`
- `delta_norm`
- `pre_mean`
- `grad_mean`
- `post_mean`
- `delta_mean`

#### Current classification

Likely optional debug / audit.

Interpretation:

These summaries are useful for sanity checking and manual inspection, but the core statement already has the stronger tensor-level witness through:

- `gradient_tensors`
- `delta_tensors`

So parameter summaries should not automatically be treated as mandatory long-term artifact fields.

---

### gradient_tensors

#### Mandatory witness

- `net.0.weight`
- `net.0.bias`
- `net.2.weight`
- `net.2.bias`
- `net.4.weight`
- `net.4.bias`

Interpretation:

These are currently core witness fields for one-step gradient consistency in the Python prototype.

---

### delta_tensors

#### Mandatory witness

- `net.0.weight`
- `net.0.bias`
- `net.2.weight`
- `net.2.bias`
- `net.4.weight`
- `net.4.bias`

Interpretation:

These are currently core witness fields for one-step parameter-update consistency in the Python prototype.

---

## 8. One-Step Artifact Schema v1 Working Classification

### Core public

- `schema_version`
- `public.dataset_root`
- `public.batch_indices`
- `public.batch_size`
- `public.loss_type`
- `public.optimizer_type`
- `public.learning_rate_fp`
- `public.pre_checkpoint_sha256`
- `public.post_checkpoint_sha256`
- `public.checkpoint_commitment_type`
- `public.pre_online_state_dict_key`
- `public.pre_online_state_dict_sha256`
- `public.pre_target_state_dict_sha256`
- `public.post_online_state_dict_key`
- `public.post_online_state_dict_sha256`
- `public.post_target_state_dict_sha256`

### Core witness

- `items[].transition`
- `items[].leaf`
- `items[].merkle_path`
- `items[].td_witness`
- `items[].td_witness.q_online_fp`
- `items[].td_witness.next_action_online`
- `items[].td_witness.q_target_max_fp`
- `items[].td_witness.target_fp`
- `items[].td_witness.loss_fp`
- `update_witness.batch_loss_fp`
- `update_witness.gradient_tensors`
- `update_witness.delta_tensors`

### Audit / debug

- `items[].index`
- `items[].leaf_hash`
- `items[].debug`
- `update_witness.batch_loss_real_for_training`
- `update_witness.pre_online_state_sha256`
- `update_witness.post_online_state_sha256`
- `update_witness.target_state_sha256`
- `update_witness.parameter_count`
- `update_witness.parameter_summaries`

### Empty compatibility

- `notes`

`notes` is currently `{}` and does not carry runtime paths.

---

## 9. Short-Trace Artifact Inspection Result

### Top-level

#### Keep as core structure

- `schema_version`
- `public`
- `steps`
- `notes`

Interpretation:

`notes` is now kept only as an empty placeholder structure for compatibility. It no longer carries operational metadata after B3.

---

### Public

#### Mandatory public

- `dataset_root`
- `trace_batch_indices`
- `num_steps`
- `batch_size`
- `loss_type`
- `optimizer_type`
- `learning_rate_fp`
- `sampling_rule_type`
- `start_offset`
- `sampling_seed`
- `dataset_size`
- `target_sync_every`
- `initial_checkpoint_sha256`
- `final_checkpoint_sha256`

Canonical boundary commitment public fields:

- `checkpoint_commitment_type`
- `initial_online_state_dict_key`
- `initial_online_state_dict_sha256`
- `initial_target_state_dict_sha256`
- `final_online_state_dict_key`
- `final_online_state_dict_sha256`
- `final_target_state_dict_sha256`

These fields are now part of the current `short_trace_update_v2` public schema. The verifier recomputes them from the externally supplied initial/final checkpoint paths and checks that the trace-boundary model states match the public commitments.

---

### steps[0]

#### Core per-step structure

- `step_index`
- `input_checkpoint_sha256`
- `raw_output_checkpoint_sha256`
- `next_checkpoint_sha256`
- `target_sync_applied`
- `sync_state_witness`
- `one_step_artifact`

Interpretation:

- `one_step_artifact` is the real nested witness;
- `sync_state_witness` is the current witness extension that lets the verifier check target-sync semantics without relying on local checkpoint paths inside each step.

---

### Cleanup decisions already applied

- removed `steps[].expected_batch_indices`;
- removed `public.learning_rate_real`;
- removed `steps[].batch_indices`;
- removed `steps[].one_step_artifact_path`;
- removed `steps[].input_checkpoint_path`;
- removed `steps[].raw_output_checkpoint_path`;
- removed `steps[].next_checkpoint_path`;
- removed `notes.data_path`;
- removed `notes.work_dir`;
- removed `notes.statement_scope`;
- removed `notes.limitations`;
- removed `notes.merkle_path`;
- removed `notes.initial_checkpoint_path`;
- removed `notes.final_checkpoint_path`;
- added `steps[].sync_state_witness`.

Interpretation:

- `expected_batch_indices` is recomputable from:
  - `sampling_rule_type`,
  - `start_offset`,
  - `sampling_seed`,
  - `dataset_size`,
  - `batch_size`,
  - `step_index`;

For `contiguous_deterministic`, `start_offset`, `batch_size`, and `step_index` determine the expected batch.

For `seeded_permutation`, `sampling_seed`, `dataset_size`, `batch_size`, and `step_index` determine the expected batch.

- batch identity is already available in:
  - `public.trace_batch_indices`;
  - `steps[].one_step_artifact.public.batch_indices`;
- `one_step_artifact_path` was only a local filesystem convenience;
- `input_checkpoint_path`, `raw_output_checkpoint_path`, and `next_checkpoint_path` were local path assumptions;
- sync verification now uses embedded state witnesses instead;
- `notes.merkle_path`, `notes.initial_checkpoint_path`, and `notes.final_checkpoint_path` were removed by the end of B3;
- the verifier/benchmark now supplies those paths externally through environment variables;
- the other removed notes fields were only local execution metadata.

A cleaner schema should prefer one canonical location for public batch identity and avoid storing local-path assumptions in the artifact contract.

---

### sync_state_witness

#### Mandatory witness

- `raw_output_online_state_dict`
- `raw_output_target_state_dict`
- `next_target_state_dict`

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

## 10. Short-Trace Artifact Schema v2 Working Classification

### Core public

- `schema_version`
- `public.dataset_root`
- `public.trace_batch_indices`
- `public.num_steps`
- `public.batch_size`
- `public.loss_type`
- `public.optimizer_type`
- `public.learning_rate_fp`
- `public.sampling_rule_type`
- `public.start_offset`
- `public.sampling_seed`
- `public.dataset_size`
- `public.target_sync_every`
- `public.initial_checkpoint_sha256`
- `public.final_checkpoint_sha256`
- `public.checkpoint_commitment_type`
- `public.initial_online_state_dict_key`
- `public.initial_online_state_dict_sha256`
- `public.initial_target_state_dict_sha256`
- `public.final_online_state_dict_key`
- `public.final_online_state_dict_sha256`
- `public.final_target_state_dict_sha256`

### Core witness / trace structure

- `steps[].step_index`
- `steps[].input_checkpoint_sha256`
- `steps[].raw_output_checkpoint_sha256`
- `steps[].next_checkpoint_sha256`
- `steps[].target_sync_applied`
- `steps[].sync_state_witness`
- `steps[].one_step_artifact`

### Audit / debug

- none stored inside the artifact after B3.

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
- `SHORT_TRACE_WORK_DIR`

Nested one-step verifier runtime inputs:

- `ONE_STEP_ARTIFACT_PATH`
- `ONE_STEP_MERKLE_PATH`
- `ONE_STEP_CHECKPOINT_PATH`
- `ONE_STEP_POST_CHECKPOINT_PATH`

Interpretation:

These values are operational handles for the Python prototype. They help the benchmark rerun verification and recompute file hashes, but they should not be treated as persistent public inputs or private witness fields in the backend-ready statement.

---

## 12. Suggested Backend-Ready Direction

The current Python artifact schema is intentionally audit-friendly. A future backend-ready schema should be smaller and stricter.

Recommended direction:

1. keep public inputs minimal;
2. move large tensors into private witnesses or committed witness blobs;
3. avoid local filesystem paths in persistent artifacts;
4. avoid duplicated semantic values;
5. replace Python-only debug fields with optional audit sidecars;
6. expose canonical model-state commitments at all statement boundaries;
7. define a compact representation for:
   - Merkle paths,
   - fixed-point TD arithmetic,
   - gradient/update witnesses,
   - target-sync witnesses.

A practical first ZK backend target should likely be the TD statement, not the full one-step update:

```text
committed transition membership
+ Bellman target correctness
+ SmoothL1 TD loss correctness
```

The one-step and short-trace statements can remain Python-level verification prototypes until the TD-level relation is implemented in a proving backend.
