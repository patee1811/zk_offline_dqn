# TD MVP Test Vectors

This directory contains small backend-facing test vectors for the first ZK TD MVP.

The current test vector is:

```text
td_mvp_case_0.json
```

It is exported from:

```text
artifacts/fixtures/minibatch_td/minibatch_td_from_dataset.json
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

`leaf` must equal the canonical serialization of `transition` from
`zk_offline_dqn.zk_specs.serialize_transition_leaf`. The leaf hash is SHA-256
over `zk_offline_dqn.merkle.encode_leaf_for_hash(leaf)`, which currently joins
the signed integer fields with commas and encodes the result as UTF-8.

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

The SP1 backend uses this file as the canonical single-transition
compatibility target. Future zkVM or circuit backends should use the same file
to compare semantics.

The backend should accept the valid test vector and reject tampered variants such as:

```text
tampered reward
tampered transition fields
tampered leaf encoding
tampered Merkle path
tampered q_target_max_fp
tampered claimed_target_fp
tampered claimed_loss_fp
```

## Minibatch Test Vectors

The backend also supports a generated minibatch schema:

```text
td_mvp_batch_test_vector_v1
```

Generate TD-2/4/8 fixtures from the canonical single-transition vector:

```bash
python3 scripts/artifacts_export/export_td_mvp_batch_test_vector.py \
  --input zk_backend/test_vectors/td_mvp_case_0.json \
  --out /tmp/td_mvp_batch_size_2.json \
  --batch-size 2
```

The minibatch public inputs add:

```text
batch_size
claimed_batch_loss_fp
```

The private witness uses:

```text
items[]
```

Each item contains the same transition, leaf, Merkle path, and TD witness fields as the single-transition vector. The additional relation check is:

```text
claimed_batch_loss_fp == floor(sum(items[].td_witness.loss_fp) / batch_size)
```
