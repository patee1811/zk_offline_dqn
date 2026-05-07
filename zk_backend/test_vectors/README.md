# TD MVP Test Vectors

This directory contains small backend-facing test vectors for the first ZK TD MVP.

The current test vector is:

```text
td_mvp_case_0.json
```

It is exported from:

```text
artifacts/minibatch_td_from_dataset.json
```

using:

```text
scripts/artifacts_export/export_td_mvp_test_vector.py
```

## Schema

The test vector schema is:

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

The `td_witness` contains:

```text
q_online_action_fp
next_action_online
q_target_max_fp
target_fp
td_error_fp
loss_fp
```

## Intended Use

A future zkVM or circuit backend should use this file as a minimal compatibility target.

The backend should accept the valid test vector and reject tampered variants such as:

```text
tampered reward
tampered Merkle path
tampered q_target_max_fp
tampered claimed_target_fp
tampered claimed_loss_fp
```