# Current Benchmark Snapshot

## Locked benchmark milestone

This file records the current benchmark milestone that should be treated as the canonical reference point for the repository and paper draft.

Last refreshed on 2026-05-02 from:
- `artifacts/benchmarks/short_trace_update/summary.json`
- `artifacts/benchmarks/short_trace_update/summary.csv`

### Main short-trace benchmark currently locked

Sampling rule:
- `sampling_rule_type = contiguous_deterministic`

Trace setting:
- `num_steps = 8`
- `target_sync_every = 2`

### Run 0
- `start_offset = 0`
- `batch_size = 4`
- `trace_batch_indices = [[0,1,2,3],[4,5,6,7],[8,9,10,11],[12,13,14,15],[16,17,18,19],[20,21,22,23],[24,25,26,27],[28,29,30,31]]`
- `export_time_sec = 21.9907`
- `verify_time_sec = 13.4818`
- `verification_passed = True`
- `initial_checkpoint_sha256 = 6f0fea11038d5f9bd69f48d8a4ee46523ce5d9772de6babf3570144576a79392`
- `final_checkpoint_sha256 = b759ddbed0b5105e0ffd23f680ddbf577fc42a911d70d1245712610d43f59bb7`

### Run 1
- `start_offset = 32`
- `batch_size = 4`
- `trace_batch_indices = [[32,33,34,35],[36,37,38,39],[40,41,42,43],[44,45,46,47],[48,49,50,51],[52,53,54,55],[56,57,58,59],[60,61,62,63]]`
- `export_time_sec = 23.2580`
- `verify_time_sec = 13.6440`
- `verification_passed = True`
- `initial_checkpoint_sha256 = 6f0fea11038d5f9bd69f48d8a4ee46523ce5d9772de6babf3570144576a79392`
- `final_checkpoint_sha256 = 82fefb4ba14afdc9b50bb5e2375e9283c4fedebb12d04388106eba77088bb4ec`

### Run 2
- `start_offset = 0`
- `batch_size = 8`
- `trace_batch_indices = [[0,1,2,3,4,5,6,7],[8,9,10,11,12,13,14,15],[16,17,18,19,20,21,22,23],[24,25,26,27,28,29,30,31],[32,33,34,35,36,37,38,39],[40,41,42,43,44,45,46,47],[48,49,50,51,52,53,54,55],[56,57,58,59,60,61,62,63]]`
- `export_time_sec = 22.4650`
- `verify_time_sec = 14.0169`
- `verification_passed = True`
- `initial_checkpoint_sha256 = 6f0fea11038d5f9bd69f48d8a4ee46523ce5d9772de6babf3570144576a79392`
- `final_checkpoint_sha256 = 01d508d753a395f578e041976f8ecdf2bbd1dbfbf8acf11bf197e3e0fefc2e1e`

## Artifact/schema status at this milestone

The locked short-trace artifact schema has completed the B3 cleanup:

- short-trace artifacts keep `public`, `steps`, and an empty compatibility `notes` object;
- operational local paths are not part of the persistent artifact contract;
- `notes.merkle_path`, `notes.initial_checkpoint_path`, and `notes.final_checkpoint_path` have been removed;
- the benchmark supplies operational paths to the verifier through environment variables:
  - `SHORT_TRACE_MERKLE_PATH`
  - `SHORT_TRACE_INITIAL_CHECKPOINT_PATH`
  - `SHORT_TRACE_FINAL_CHECKPOINT_PATH`
- the benchmark summary still records `final_checkpoint_path` for reproducibility and reruns, but that field is benchmark metadata, not an artifact-schema field.

## Interpretation

This benchmark milestone should be used as the current repository-level reference for:
- short verified training traces,
- deterministic contiguous sampling-rule enforcement,
- public `start_offset`,
- public `batch_size`,
- exporter + verifier consistency,
- short-trace artifact schema cleanup after B3.

Older benchmark numbers from earlier 2-step / 4-step stages remain historically useful, but this file should be treated as the primary current benchmark snapshot.

## SP1 TD MVP Week 3 Snapshot

Week 3 adds a reproducibility runner for the SP1 TD MVP backend. The latest full run was generated at `2026-05-11T09:26:40.773361+00:00` from WSL2 Ubuntu:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

Expected outputs:

```text
artifacts/benchmarks/sp1_td_mvp/summary.json
artifacts/benchmarks/sp1_td_mvp/benchmark_matrix.csv
artifacts/benchmarks/sp1_td_mvp/summary.md
```

This snapshot is separate from the short-trace benchmark above. It compares:

- Python verifier as the semantic oracle;
- SP1 host/guest as the cryptographic backend;
- valid TD MVP fixture acceptance;
- matching rejection for tampered TD MVP fixtures.

### TD-1 SP1 result

| Case | Relation | Batch size | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| TD-1 | Merkle + TD + SmoothL1 | 1 | completed | 66.668891 | 0.088947 | 2782588 | 365501 |

### Python/SP1 agreement

All expected outcomes passed:

```text
all_python_expected = True
all_sp1_expected = True
python_sp1_agreement = True
all_passed = True
```

The agreement suite covers:

- `valid_control`;
- `tamper_reward`;
- `tamper_done`;
- `tamper_transition_obs`;
- `tamper_leaf_encoding`;
- `tamper_merkle_path`;
- `tamper_q_target_max_fp`;
- `tamper_claimed_target_fp`;
- `tamper_claimed_loss_fp`;
- `tamper_leaf_hash`;
- `tamper_td_error_fp`.

## SP1 TD MVP Week 4 Minibatch Update

The SP1 relation has been extended in code to accept `td_mvp_batch_test_vector_v1` inputs with:

- `private.items[]` for multiple Merkle membership and TD checks;
- public `batch_size`;
- public `claimed_batch_loss_fp`;
- integer average loss `sum(loss_fp) // batch_size`.

The Python semantic-oracle smoke path has passed for TD-2, TD-4, TD-8, and these batch aggregation tamper cases:

- `tamper_batch_claimed_loss_fp`;
- `tamper_batch_size`;
- `tamper_batch_item_loss_fp`;
- `tamper_batch_item_index`.

Fresh SP1 proof timings for TD-2/4/8 are pending a WSL2 Ubuntu run of:

```bash
python3 scripts/experiments/benchmark_sp1_td_mvp.py --prove
```

The first WSL2 proof refresh completed TD-2 but the terminal/WSL session became unstable when attempting TD-4 proof. Treat TD-4 and TD-8 as execution-only until a larger Linux machine or larger WSL memory limit is available.

| Case | Status | Prove time sec | Verify time sec | Proof size bytes | Cycle count | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| TD-1 | proof available from Week 3 | 66.668891 | 0.088947 | 2782588 | 365501 | single-transition proof |
| TD-2 | proof completed | 78.693257 | 0.131290 | 2787687 | 725309 | minibatch proof with average loss |
| TD-4 | execution-only | n/a | n/a | n/a | 1425790 | local WSL proof attempt exceeded available stability/resources |
| TD-8 | execution-only | n/a | n/a | n/a | 2834727 | do not claim proof timing yet |

### WSL2 TD-2 execution smoke

Recorded from WSL2 Ubuntu on 2026-05-12:

```text
TD-2 batch Python verifier: verification_passed = True
cargo check -p td-mvp-shared -p td-mvp-host: passed
SP1 TD-2 execution: execution_ok = true
SP1 TD-2 execution_time_sec = 0.078742
SP1 TD-2 cycle_count = 725309
SP1 TD-2 exit_code = 0
tamper_batch_claimed_loss_fp: rejected with exit_code = 1
```

### WSL2 SP1 negative suite

Recorded from WSL2 Ubuntu on 2026-05-12:

```text
valid_control: accepted, cycle_count = 382915
valid_batch_size_2: accepted, cycle_count = 725309
tamper_reward: rejected
tamper_done: rejected
tamper_transition_obs: rejected
tamper_leaf_encoding: rejected
tamper_merkle_path: rejected
tamper_q_target_max_fp: rejected
tamper_claimed_target_fp: rejected
tamper_claimed_loss_fp: rejected
tamper_leaf_hash: rejected
tamper_td_error_fp: rejected
tamper_batch_claimed_loss_fp: rejected
tamper_batch_size: rejected
tamper_batch_item_loss_fp: rejected
tamper_batch_item_index: rejected
all_sp1_negative_cases_passed = true
```
