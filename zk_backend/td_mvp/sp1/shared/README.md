# SP1 TD MVP Shared Skeleton

This directory is reserved for shared Rust code used by both the future SP1 host and guest.

No shared Rust implementation is included yet.

## Future Role

The shared module may contain:

```text
input structs
public input structs
private witness structs
Merkle path step structs
fixed-point helper functions
SmoothL1 helper functions
leaf encoding helper functions
hashing helper functions
```

## Design Goal

The shared code should keep host and guest behavior aligned.

In particular, the Rust implementation should match the current Python verifier:

```text
scripts/artifacts_export/verify_td_mvp_test_vector.py
```

## Non-Goals

The shared module should not include backend-specific proving logic. Proving should remain in the host, and relation checks should remain in the guest.