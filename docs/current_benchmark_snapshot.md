# Current Benchmark Snapshot

## Locked benchmark milestone

This file records the current benchmark milestone that should be treated as the canonical reference point for the repository and paper draft.

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
- `export_time_sec = 22.9605`
- `verify_time_sec = 13.2738`
- `verification_passed = True`

### Run 1
- `start_offset = 32`
- `batch_size = 4`
- `trace_batch_indices = [[32,33,34,35],[36,37,38,39],[40,41,42,43],[44,45,46,47],[48,49,50,51],[52,53,54,55],[56,57,58,59],[60,61,62,63]]`
- `export_time_sec = 22.7696`
- `verify_time_sec = 13.7361`
- `verification_passed = True`

### Run 2
- `start_offset = 0`
- `batch_size = 8`
- `trace_batch_indices = [[0,1,2,3,4,5,6,7],[8,9,10,11,12,13,14,15],[16,17,18,19,20,21,22,23],[24,25,26,27,28,29,30,31],[32,33,34,35,36,37,38,39],[40,41,42,43,44,45,46,47],[48,49,50,51,52,53,54,55],[56,57,58,59,60,61,62,63]]`
- `export_time_sec = 21.9691`
- `verify_time_sec = 12.9388`
- `verification_passed = True`

## Interpretation

This benchmark milestone should be used as the current repository-level reference for:
- short verified training traces,
- deterministic contiguous sampling-rule enforcement,
- public `start_offset`,
- public `batch_size`,
- exporter + verifier consistency.

Older benchmark numbers from earlier 2-step / 4-step stages remain historically useful, but this file should be treated as the primary current benchmark snapshot.