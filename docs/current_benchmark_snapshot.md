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
