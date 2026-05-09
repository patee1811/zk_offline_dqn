# SP1 Host Skeleton

No host implementation exists yet.

The future host should:

- load or embed `zk_backend/test_vectors/td_mvp_case_0.json`;
- validate `schema_version == td_mvp_test_vector_v1`;
- convert JSON into typed Rust structs from `shared`;
- pass inputs to the SP1 guest;
- generate a proof;
- verify the proof;
- print `proof_generated`, `proof_verified`, `proving_time_sec`, `verification_time_sec`, and `proof_size_bytes`.

The host should not enforce the TD relation itself. Relation checks belong in the guest.
