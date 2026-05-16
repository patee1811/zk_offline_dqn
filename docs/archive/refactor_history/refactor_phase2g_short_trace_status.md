# Refactor Phase 2G Short Trace Status

## Files Created

- `zk_offline_dqn/relations/short_trace.py`
- `zk_offline_dqn/verifiers/short_trace.py`
- `tests/golden/test_short_trace_verifier.py`
- `tests/negative/test_short_trace_tamper.py`

## Files Modified

- `scripts/artifacts_export/verify_short_trace_update_artifact.py`

## Old Script to New Module Mapping

- Short-trace relation checks:
  - old: inline schema, sampling, chain, target-sync, boundary commitment, and
    per-step result checks in `scripts/artifacts_export/verify_short_trace_update_artifact.py`
  - new: `zk_offline_dqn.relations.short_trace`
- JSON loading, checkpoint/file IO, per-step checkpoint path resolution, direct
  embedded one-step verification, and report formatting:
  - old: inline in the script, with one-step verification delegated by subprocess
  - new: `zk_offline_dqn.verifiers.short_trace`
- CLI/environment wrapper:
  - old script path remains `scripts/artifacts_export/verify_short_trace_update_artifact.py`
  - the script now delegates to `zk_offline_dqn.verifiers.short_trace`

## Current CLI and Environment Behavior Preserved

- The script still takes no CLI flags.
- The artifact path is still read from `SHORT_TRACE_ARTIFACT_PATH`, with default
  `artifacts/short_trace_update_artifact.json`.
- The Merkle path is still read from `SHORT_TRACE_MERKLE_PATH`, with artifact
  `notes.merkle_path` fallback.
- The initial checkpoint path is still read from
  `SHORT_TRACE_INITIAL_CHECKPOINT_PATH`, with artifact
  `notes.initial_checkpoint_path` fallback.
- The final checkpoint path is still read from `SHORT_TRACE_FINAL_CHECKPOINT_PATH`,
  with artifact `notes.final_checkpoint_path` fallback.
- The work directory is still read from `SHORT_TRACE_WORK_DIR`, with fallback to
  the directory containing the resolved final checkpoint path.
- In this checkout, the canonical short-trace artifacts do not contain path
  notes, so the direct canonical command uses the same explicit environment
  paths as the full regression runner.
- Valid traces still exit 0.
- Relation failures still print `verification_passed = False` and exit 0.
- Missing paths, malformed artifacts, unsupported schema versions, and invalid
  sampling-rule inputs still raise normally.

## Stdout Markers

- Preserved success/failure marker:
  - `verification_passed = True`
  - `verification_passed = False`
- Report labels and ordering are preserved for valid artifacts.
- The old script only printed embedded one-step stdout/stderr on a failed step;
  that diagnostic section is still printed on failed embedded one-step checks.

## Artifact Fields Used

- `schema_version`
- `public.dataset_root`
- `public.trace_batch_indices`
- `public.num_steps`
- `public.batch_size`
- `public.loss_type`
- `public.optimizer_type`
- `public.learning_rate_fp`
- `public.sampling_rule_type`
- `public.start_offset`
- `public.sampling_seed`
- `public.dataset_size`
- `public.target_sync_every`
- `public.initial_checkpoint_sha256`
- `public.final_checkpoint_sha256`
- `public.checkpoint_commitment_type`
- `public.initial_online_state_dict_key`
- `public.initial_online_state_dict_sha256`
- `public.initial_target_state_dict_sha256`
- `public.final_online_state_dict_key`
- `public.final_online_state_dict_sha256`
- `public.final_target_state_dict_sha256`
- `steps[].step_index`
- `steps[].input_checkpoint_sha256`
- `steps[].raw_output_checkpoint_sha256`
- `steps[].next_checkpoint_sha256`
- `steps[].target_sync_applied`
- `steps[].one_step_artifact`
- `steps[].sync_state_witness.raw_output_online_state_dict`
- `steps[].sync_state_witness.raw_output_target_state_dict`
- `steps[].sync_state_witness.next_target_state_dict`
- `notes.merkle_path`
- `notes.initial_checkpoint_path`
- `notes.final_checkpoint_path`

## Schema Version Handling

- The verifier still requires `schema_version == "short_trace_update_v2"` through
  `require_schema_version`.
- No schema strings were changed.

## Checkpoint Chaining Semantics

- `num_steps_match` remains `num_steps == len(steps) == len(trace_batch_indices)`.
- Step 0 input checkpoint must match `public.initial_checkpoint_sha256`.
- Each later step input checkpoint must match the previous step
  `next_checkpoint_sha256`.
- Final chain check remains `last next_checkpoint_sha256 == public.final_checkpoint_sha256`.
- If `target_sync_applied` is true, `raw_output_checkpoint_sha256 != next_checkpoint_sha256`.
- If `target_sync_applied` is false, `raw_output_checkpoint_sha256 == next_checkpoint_sha256`.
- Target-sync witness state still checks next target against raw online state
  when sync is applied, otherwise against raw target state.

## Subprocess Removal

- The new relation module does not import from `scripts/` and does not call
  subprocess.
- The new verifier adapter does not call subprocess for embedded one-step
  checks. It calls `zk_offline_dqn.verifiers.one_step_update` directly.
- The old script remains runnable for external callers, but now acts as a thin
  wrapper around the new verifier adapter.

## Negative Cases Tested

- Golden/negative tests:
  - wrong chained checkpoint
  - wrong step ordering
  - wrong embedded one-step update witness
  - wrong final online state commitment
- Existing negative runner:
  - valid contiguous trace
  - valid seeded trace
  - contiguous public batch tamper
  - seeded public batch tamper
  - sampling seed tamper
  - dataset size tamper
  - final checkpoint SHA tamper
  - final online state commitment tamper

## Inspection Summary

- Current CLI arguments and defaults: no CLI flags; default artifact path is
  `artifacts/short_trace_update_artifact.json`.
- Current environment variables:
  - `SHORT_TRACE_ARTIFACT_PATH`
  - `SHORT_TRACE_MERKLE_PATH`
  - `SHORT_TRACE_INITIAL_CHECKPOINT_PATH`
  - `SHORT_TRACE_FINAL_CHECKPOINT_PATH`
  - `SHORT_TRACE_WORK_DIR`
- Current stdout marker: `verification_passed = True` or
  `verification_passed = False`.
- Current failure behavior and exit codes: relation rejection exits 0 with a
  false marker; malformed input, missing paths, schema errors, and unsupported
  sampling rule errors raise.
- Previous one-step dependency: the old short-trace script wrote each embedded
  one-step artifact to a temporary JSON file and called
  `verify_one_step_update_artifact.py` via subprocess.
- New one-step dependency: the verifier adapter calls the active-package
  one-step verifier directly and passes the same Merkle/checkpoint/post-checkpoint
  paths.
- Full regression inclusion: `run_full_regression.py` directly runs contiguous
  and seeded short-trace verification and also runs
  `run_short_trace_negative_tests.py`.

## Commands Run

- `python -c "import zk_offline_dqn.relations.short_trace; import zk_offline_dqn.verifiers.short_trace"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `$env:SHORT_TRACE_ARTIFACT_PATH='artifacts/short_trace_update_artifact.json'; $env:SHORT_TRACE_MERKLE_PATH='artifacts/cartpole_dqn_eps010_merkle.json'; $env:SHORT_TRACE_INITIAL_CHECKPOINT_PATH='models/offline_dqn_with_target_seed42_best.pt'; $env:SHORT_TRACE_FINAL_CHECKPOINT_PATH='artifacts/short_trace_work/step_1_post_synced_4_5_6_7.pt'; $env:SHORT_TRACE_WORK_DIR='artifacts/short_trace_work'; python scripts/artifacts_export/verify_short_trace_update_artifact.py`
- `python -m unittest discover tests`
- `python scripts/experiments/run_short_trace_negative_tests.py`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.relations.short_trace; import zk_offline_dqn.verifiers.short_trace"` | PASS | New relation and verifier modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, active package, Phase 1A `src/` skeleton, and tests compile. |
| canonical env `python scripts/artifacts_export/verify_short_trace_update_artifact.py` | PASS | Printed preserved `verification_passed = True` marker for the contiguous canonical artifact. |
| `python -m unittest discover tests` | PASS | Ran 63 tests, including short-trace golden and negative tests. |
| `python scripts/experiments/run_short_trace_negative_tests.py` | PASS | Valid traces accepted and all short-trace tamper cases rejected. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Negative-Test Result

- `run_short_trace_negative_tests.py` completed successfully.
- The runner reported:
  - `valid_contiguous_accept = True`
  - `valid_seeded_accept = True`
  - `tamper_contiguous_public_batch_accept = False`
  - `tamper_seeded_public_batch_accept = False`
  - `tamper_sampling_seed_accept = False`
  - `tamper_dataset_size_accept = False`
  - `tamper_final_checkpoint_sha256_accept = False`
  - `tamper_final_online_state_dict_sha256_accept = False`
  - `all_tests_passed = True`

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- No artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 3 can begin packaging/import cleanup planning. Keep the active root
package as the runtime package until an explicit packaging migration is tested
against the full regression suite.
