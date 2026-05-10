# SP1 TD MVP

SP1 is the selected first proving backend.

This directory is currently a skeleton. It does not yet contain:

- `Cargo.toml`;
- Rust host code;
- Rust guest code;
- proof generation;
- proof verification.

## Planned Workspace

The exact layout should follow the current SP1 template, but the intended shape is:

```text
zk_backend/td_mvp/sp1/
  Cargo.toml
  host/
    Cargo.toml
    src/main.rs
  guest/
    Cargo.toml
    src/main.rs
  shared/
    Cargo.toml
    src/lib.rs
```

## Compatibility Target

Use the existing vector as the first input target:

```text
zk_backend/test_vectors/td_mvp_case_0.json
```

Use the Python verifier as the source of current semantics:

```text
scripts/artifacts_export/verify_td_mvp_test_vector.py
```

## Implementation Checklist

1. Confirm SP1 works on Linux/macOS or WSL2 Ubuntu.
2. Generate a minimal SP1 project outside the repo and prove/verify hello world.
3. Create the repo workspace under this directory.
4. Add typed public/private input structs in `shared`.
5. Implement guest checks for leaf hash, Merkle path, Bellman target, TD error, and SmoothL1 loss.
6. Implement host loading for `td_mvp_case_0.json`.
7. Generate and verify a proof.
8. Print proving time, verification time, and proof size.
9. Add tampered input checks matching the Python negative tests.

## Non-Goals

The first SP1 milestone should not prove neural-network forward passes, argmax action selection, gradients, optimizer updates, short traces, or recursive aggregation.
