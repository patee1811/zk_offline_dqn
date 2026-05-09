# SP1 Shared Skeleton

No shared Rust crate exists yet.

The future shared crate should hold code used by both host and guest:

- TD MVP input structs;
- public input structs;
- private witness structs;
- Merkle path step structs;
- fixed-point helpers;
- SmoothL1 helper;
- leaf encoding and hashing helpers.

Keep proving logic in the host and relation assertions in the guest.
