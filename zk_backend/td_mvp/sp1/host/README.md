# SP1 Host

This crate is the concrete host for the TD MVP SP1 backend.

Responsibilities:

- load `zk_backend/test_vectors/td_mvp_case_0.json` or a generated
  `td_mvp_batch_test_vector_v1` fixture;
- apply named tamper cases for negative testing;
- run an optional Rust host precheck using `td-mvp-shared`;
- execute the SP1 guest;
- generate and verify SP1 proofs for accepted cases;
- print execution cycles, proving time, verification time, and proof size.

Core commands from `zk_backend/td_mvp/sp1/`:

```bash
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
cargo run --release -p td-mvp-host -- --input /tmp/td_mvp_batch_size_2.json --execute
```

Tampered cases should be run with `--skip-host-precheck` when the expected
result is guest rejection rather than host-side JSON rejection.
