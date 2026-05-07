# TD MVP Host Skeleton

This directory is reserved for the host-side code of the future TD MVP zkVM backend.

The host is responsible for preparing inputs, invoking the prover, and verifying the resulting proof or receipt.

## Responsibilities

The host should:

```text
load zk_backend/test_vectors/td_mvp_case_0.json
validate schema_version
separate public inputs from private witness
serialize inputs into the backend-specific format
invoke the guest program
generate a proof or receipt
verify the proof or receipt
record proving time
record verification time
record proof size
```

## Expected Inputs

```text
td_mvp_case_0.json
```

## Expected Outputs

A future implementation should produce something like:

```text
proof or receipt
verification result
proving_time_sec
verification_time_sec
proof_size_bytes
```

## Current Status

No host implementation is included yet.

This directory is a placeholder for either:

```text
RISC Zero host code
SP1 host code
```