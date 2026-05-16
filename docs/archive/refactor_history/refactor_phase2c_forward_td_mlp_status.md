# Refactor Phase 2C Forward-TD MLP Status

## Files Created

- `zk_offline_dqn/relations/forward_td_mlp.py`
- `zk_offline_dqn/verifiers/forward_td_mlp.py`
- `tests/golden/test_forward_td_mlp_verifier.py`

## Files Modified

- `scripts/artifacts_export/verify_forward_td_mlp_test_vector.py`

## Old Script to New Module Mapping

- Pure forward-TD MLP relation checks:
  - old: inline functions in `scripts/artifacts_export/verify_forward_td_mlp_test_vector.py`
  - new: `zk_offline_dqn.relations.forward_td_mlp`
- JSON loading and report formatting:
  - old: inline in the script
  - new: `zk_offline_dqn.verifiers.forward_td_mlp`
- CLI wrapper:
  - old script path remains `scripts/artifacts_export/verify_forward_td_mlp_test_vector.py`
  - the script now delegates to `zk_offline_dqn.verifiers.forward_td_mlp`
- Backward-compatible helper imports:
  - `assert_equal`
  - `verify_forward_trace`
  - `verify_item_membership`
  - These remain importable from the old script because
    `verify_one_step_sgd_tiny_test_vector.py` already imports them there.

## Current CLI Behavior Preserved

- The script still accepts `--input`.
- The default input remains `zk_backend/test_vectors/forward_td_mlp_case_0.json`.
- The default path is not present in this checkout, so the direct validation
  command uses the existing canonical benchmark fixture.
- Valid vectors still exit with code 0.
- Relation failures still raise assertion errors and exit nonzero before
  printing the success markers.
- Missing files, malformed vectors, and unexpected schema versions still raise
  normally.

## Stdout Markers

- Preserved success markers:
  - `verification_passed = True`
  - `all_forward_td_mlp_ok = True`
- The verifier did not previously print a failure marker on invalid vectors;
  invalid vectors raised before the success report. That behavior is preserved.

## Test-Vector Fields Used

- `schema_version`
- `public.dataset_root`
- `public.fp_scale`
- `public.gamma_fp`
- `public.batch_size`
- `public.leaf_indices`
- `public.network_spec_hash`
- `public.network_layer_sizes`
- `public.online_model_commitment`
- `public.target_model_commitment`
- `public.claimed_item_losses_fp`
- `public.claimed_batch_loss_fp`
- `private.online_model`
- `private.target_model`
- `private.items`
- `items[].index`
- `items[].transition`
- `items[].leaf`
- `items[].leaf_hash`
- `items[].merkle_path`
- `items[].forward_witness`

## Fixed-Point and MLP Helpers Used

- `zk_offline_dqn.forward_td_mlp.build_network_spec_hash`
- `zk_offline_dqn.forward_td_mlp.build_model_commitment`
- `zk_offline_dqn.forward_td_mlp.compute_forward_td_item`
- `zk_offline_dqn.zk_specs.serialize_transition_leaf`
- `zk_offline_dqn.core.merkle.hash_leaf`
- `zk_offline_dqn.core.merkle.recompute_root_from_path`

These helpers were reused without changing fixed-point arithmetic, quantized
MLP layer order, ReLU activation semantics, target semantics, or loss
semantics.

## Negative Cases Tested

- Golden test: in-memory tampered `public.claimed_batch_loss_fp`.
- Existing benchmark smoke cases:
  - online model weight tamper
  - target model weight tamper
  - activation tamper
  - ReLU mask tamper
  - argmax tamper
  - selected target value tamper
  - claimed batch loss tamper

## Inspection Summary

- Current CLI arguments and defaults: `--input`, default
  `zk_backend/test_vectors/forward_td_mlp_case_0.json`.
- Current stdout success markers: `verification_passed = True` and
  `all_forward_td_mlp_ok = True`.
- Current failure behavior and exit codes: invalid relation raises an
  `AssertionError` and exits nonzero; valid input exits 0.
- Current fixed-point/quantized MLP helpers: network spec commitment, model
  commitment, transition leaf serialization, Merkle root recomputation, and
  `compute_forward_td_item`.
- Full regression inclusion: `run_full_regression.py` includes
  `benchmark_forward_td_mlp_sp1.py --skip-sp1`.

## Commands Run

- `python -c "import zk_offline_dqn.relations.forward_td_mlp; import zk_offline_dqn.verifiers.forward_td_mlp"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/artifacts_export/verify_forward_td_mlp_test_vector.py --input artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json`
- `python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke`
- `python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.relations.forward_td_mlp; import zk_offline_dqn.verifiers.forward_td_mlp"` | PASS | New relation and verifier modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, active package, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 25 tests, including forward-TD MLP golden tests and script helper import compatibility. |
| `python scripts/artifacts_export/verify_forward_td_mlp_test_vector.py --input artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json` | PASS | Printed preserved `verification_passed = True` and `all_forward_td_mlp_ok = True` markers. |
| `python scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke` | PASS | Valid batches accepted and all forward-TD MLP tamper cases rejected. |
| `python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke` | PASS | Confirms existing one-step verifier imports from the old forward-TD script still work. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed after preserving helper imports from the script wrapper. |

## Python Smoke Benchmark Result

- `benchmark_forward_td_mlp_sp1.py --skip-sp1` completed successfully.
- The benchmark reported:
  - `forward-TD-1: python_accept=True ... passed=True`
  - `forward-TD-2: python_accept=True ... passed=True`
  - `tamper_online_model_weight: python_accept=False ... passed=True`
  - `tamper_target_model_weight: python_accept=False ... passed=True`
  - `tamper_activation: python_accept=False ... passed=True`
  - `tamper_relu_mask: python_accept=False ... passed=True`
  - `tamper_argmax: python_accept=False ... passed=True`
  - `tamper_selected_target_value: python_accept=False ... passed=True`
  - `tamper_claimed_batch_loss: python_accept=False ... passed=True`
  - `all_passed = True`

## Regression Result

- An initial full-regression run exposed a Phase 2C compatibility regression:
  `verify_one_step_sgd_tiny_test_vector.py` imports helper functions from the
  old forward-TD script path.
- The old script wrapper now re-exports those helper functions from
  `zk_offline_dqn.relations.forward_td_mlp`.
- After that adjustment, `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- No artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 2D should extract exactly one additional verifier family, preserving its
current CLI, stdout markers, schema handling, and regression behavior.
