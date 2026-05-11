# SP1 TD MVP

SP1 is the selected first proving backend.

This directory contains the first SP1 TD MVP workspace:

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
  run_negative_cases.sh
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
5. Implement guest checks for transition-to-leaf encoding, leaf hash, Merkle path, Bellman target, TD error, and SmoothL1 loss.
6. Implement host loading for `td_mvp_case_0.json`.
7. Generate and verify a proof.
8. Print proving time, verification time, and proof size.
9. Add tampered input checks matching the Python negative tests in `tamper_checklist.md`.

Run from WSL2 Ubuntu:

```bash
cd /mnt/c/Users/Ngoc\ Duy/Duytapcode/zk_offline_dqn/zk_backend/td_mvp/sp1
cargo run --release -p td-mvp-host -- --execute
cargo run --release -p td-mvp-host -- --prove
```

Run the initial SP1 negative checks:

```bash
bash run_negative_cases.sh
```

## Current Smoke Results

Recorded on 2026-05-11 in WSL2 Ubuntu.

Valid TD MVP proof:

```text
proof_generated = true
proof_verified = true
proving_time_sec = 69.608704
verification_time_sec = 0.088708
proof_size_bytes = 2782588
```

Initial negative cases:

```text
valid_control accepted
tamper_reward rejected
tamper_done rejected
tamper_merkle_path rejected
tamper_claimed_target_fp rejected
tamper_claimed_loss_fp rejected
all_sp1_negative_cases_passed = true
```

## Non-Goals

The first SP1 milestone should not prove neural-network forward passes, argmax action selection, gradients, optimizer updates, short traces, or recursive aggregation.
