# SP1 Shared Crate

This crate contains the typed Rust relation code used by both the SP1 host and
guest.

It owns:

- JSON-serializable public input and private witness structs;
- single-transition and minibatch TD MVP input normalization;
- canonical transition-to-leaf serialization;
- SHA-256 leaf hashing and Merkle root recomputation;
- fixed-point helpers;
- SmoothL1 loss recomputation;
- public output structs committed by the guest.

Keep host-only concerns such as CLI parsing, fixture loading, tamper mutation,
proof generation, and metric printing in `td-mvp-host`. Keep guest entrypoint
logic in `td-mvp-guest`.
