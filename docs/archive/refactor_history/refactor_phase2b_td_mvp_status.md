# Refactor Phase 2B TD MVP Status

## Files Created

- `zk_offline_dqn/relations/td_mvp.py`
- `zk_offline_dqn/verifiers/td_mvp.py`
- `tests/golden/test_td_mvp_verifier.py`

## Files Modified

- `scripts/artifacts_export/verify_td_mvp_test_vector.py`

## Old Script to New Module Mapping

- Pure TD MVP relation checks:
  - old: inline functions in `scripts/artifacts_export/verify_td_mvp_test_vector.py`
  - new: `zk_offline_dqn.relations.td_mvp`
- JSON loading and report formatting:
  - old: inline in the script
  - new: `zk_offline_dqn.verifiers.td_mvp`
- CLI wrapper:
  - old script path remains `scripts/artifacts_export/verify_td_mvp_test_vector.py`
  - the script now delegates to `zk_offline_dqn.verifiers.td_mvp`

## Current CLI Behavior Preserved

- The script still accepts `--input`.
- The default input remains `zk_backend/test_vectors/td_mvp_case_0.json`.
- Valid vectors still exit with code 0.
- Relation failures still print the report and then exit with code 1.
- Missing files, malformed vectors, and unexpected schema versions still raise
  normally.

## Stdout Markers

- Preserved success/failure marker:
  - `verification_passed = True`
  - `verification_passed = False`
- Report labels and ordering are preserved, including:
  - `leaf_encoding_ok`
  - `leaf_hash_ok`
  - `merkle_ok`
  - `target_ok`
  - `td_error_ok`
  - `loss_ok`
  - `claimed_target_ok`
  - `claimed_loss_ok`
  - `claimed_batch_loss_ok`

## Test-Vector Fields Used

- `schema_version`
- `public.dataset_root`
- `public.fp_scale`
- `public.gamma_fp`
- `public.claimed_target_fp`
- `public.claimed_loss_fp`
- `public.leaf_index`
- `public.batch_size`
- `public.claimed_batch_loss_fp` or `public.batch_loss_fp`
- `public.leaf_indices`
- `public.batch_mode`
- `private.transition`
- `private.leaf`
- `private.leaf_hash`
- `private.merkle_path`
- `private.td_witness`
- `private.items`

## Fixed-Point Helpers Used

- `fixed_point_mul`
- `smooth_l1_loss_fp`
- `reward_to_fp`
- `done_to_bool`

These helpers were moved without changing integer truncation, rounding, or
SmoothL1 semantics.

## Negative Cases Tested

- Golden test: in-memory tampered `loss_fp`.
- Existing negative runner: schema version, reward, fixed-point rounding, done,
  done branch, transition observation, leaf encoding, Merkle path, leaf index,
  path order, target-network value, claimed target, claimed loss, leaf hash,
  TD error, batch loss, batch size, batch item loss, batch item index, batch
  path order, batch target-network value, and batch fixed-point rounding.

## Inspection Summary

- Current CLI arguments and defaults: `--input`, default
  `zk_backend/test_vectors/td_mvp_case_0.json`.
- Current stdout success marker: `verification_passed = True`.
- Current failure behavior and exit codes: invalid relation prints the report
  and exits 1; invalid schema or malformed input raises; valid input exits 0.
- Current fixed-point constants/functions used: vector-provided `fp_scale`,
  vector-provided `gamma_fp`, local fixed-point multiply, local SmoothL1,
  reward-to-fixed-point rounding, and done coercion.
- Full regression inclusion: `run_full_regression.py` includes
  `run_td_mvp_test_vector_negative_tests.py`.

## Commands Run

- `python -c "import zk_offline_dqn.relations.td_mvp; import zk_offline_dqn.verifiers.td_mvp"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/artifacts_export/verify_td_mvp_test_vector.py`
- `python scripts/experiments/run_td_mvp_test_vector_negative_tests.py`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.relations.td_mvp; import zk_offline_dqn.verifiers.td_mvp"` | PASS | New relation and verifier modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, active package, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 18 tests, including TD MVP golden tests. |
| `python scripts/artifacts_export/verify_td_mvp_test_vector.py` | PASS | Printed preserved `verification_passed = True` marker for the canonical vector. |
| `python scripts/experiments/run_td_mvp_test_vector_negative_tests.py` | PASS | All valid and tampered TD MVP cases matched expected accept/reject results. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- No missing fixtures were reported.
- No artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 2C should extract exactly one additional verifier family, preserving its
current CLI, stdout markers, schema handling, and regression behavior.
