# SP1 TD MVP Host Skeleton

This directory is reserved for the SP1 host program.

No working SP1 host is implemented yet.

## Future Role

The host should prepare inputs, invoke the SP1 prover, verify the proof, and record metrics.

## Expected Flow

```text
1. Load zk_backend/test_vectors/td_mvp_case_0.json
2. Validate schema_version == td_mvp_test_vector_v1
3. Convert JSON fields into typed Rust structs
4. Provide public inputs and private witness to the guest
5. Generate proof
6. Verify proof
7. Record:
   - proving_time_sec
   - verification_time_sec
   - proof_size_bytes
```

## Expected Output

A future implementation should print something like:

```text
proof_generated = true
proof_verified = true
proving_time_sec = ...
verification_time_sec = ...
proof_size_bytes = ...
```

## Non-Goals

The host should not implement the TD relation itself. The relation should be enforced inside the guest program.