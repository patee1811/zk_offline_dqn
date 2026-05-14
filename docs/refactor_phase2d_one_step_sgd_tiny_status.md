# Refactor Phase 2D One-Step SGD Tiny Status

## Files Created

- `zk_offline_dqn/relations/one_step_sgd_tiny.py`
- `zk_offline_dqn/verifiers/one_step_sgd_tiny.py`
- `tests/golden/test_one_step_sgd_tiny_verifier.py`

## Files Modified

- `scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py`

## Old Script to New Module Mapping

- Pure one-step SGD tiny relation checks:
  - old: inline functions in `scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py`
  - new: `zk_offline_dqn.relations.one_step_sgd_tiny`
- JSON loading and report formatting:
  - old: inline in the script
  - new: `zk_offline_dqn.verifiers.one_step_sgd_tiny`
- CLI wrapper:
  - old script path remains `scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py`
  - the script now delegates to `zk_offline_dqn.verifiers.one_step_sgd_tiny`

## Current CLI Behavior Preserved

- The script still accepts `--input`.
- The default input remains `zk_backend/test_vectors/one_step_sgd_tiny_case_0.json`.
- Valid vectors still exit with code 0.
- Relation failures still raise assertion errors and exit nonzero before
  printing the success markers.
- Missing files, malformed vectors, and unexpected schema versions still raise
  normally.

## Stdout Markers

- Preserved success markers:
  - `verification_passed = True`
  - `all_one_step_sgd_tiny_ok = True`
- The verifier did not previously print a failure marker on invalid vectors;
  invalid vectors raised before the success report. That behavior is preserved.

## Test-Vector Fields Used

- `schema_version`
- `public.fp_scale`
- `public.gamma_fp`
- `public.learning_rate_fp`
- `public.optimizer_type`
- `public.batch_size`
- `public.network_spec_hash`
- `public.network_layer_sizes`
- `public.pre_model_commitment`
- `public.post_model_commitment`
- `public.target_model_commitment`
- `public.leaf_indices`
- `public.claimed_batch_loss_fp`
- `private.online_model`
- `private.target_model`
- `private.post_online_model`
- `private.items`
- `private.update_witness`
- `items[0].index`
- `items[0].transition`
- `items[0].leaf`
- `items[0].leaf_hash`
- `items[0].merkle_path`
- `items[0].forward_witness`
- `update_witness.batch_loss_fp`
- `update_witness.smooth_l1_grad_fp`
- `update_witness.gradient_tensors`
- `update_witness.delta_tensors`

## Fixed-Point, MLP, and SGD Helpers Used

- `zk_offline_dqn.forward_td_mlp.build_network_spec_hash`
- `zk_offline_dqn.forward_td_mlp.build_model_commitment`
- `zk_offline_dqn.forward_td_mlp.compute_one_step_sgd_tiny`
- `zk_offline_dqn.relations.forward_td_mlp.assert_equal`
- `zk_offline_dqn.relations.forward_td_mlp.verify_forward_trace`
- `zk_offline_dqn.relations.forward_td_mlp.verify_item_membership`

These helpers were reused without changing fixed-point arithmetic, quantized
MLP layer order, ReLU activation semantics, TD target/loss semantics, gradient
semantics, learning-rate semantics, or parameter-update semantics.

## Dependency Cleanup

- The old script imported helper functions from
  `scripts/artifacts_export/verify_forward_td_mlp_test_vector.py`.
- The new relation module imports those helpers from
  `zk_offline_dqn.relations.forward_td_mlp` instead.
- Tests assert that the new relation and verifier modules do not import from
  `scripts/`.
- No other script imports helper functions from the old one-step verifier path,
  but the old script still re-exports `load_json`, `verify_tensor_pack`, and
  `verify_vector` for conservative compatibility.

## Negative Cases Tested

- Golden test: in-memory tampered `public.learning_rate_fp`.
- Existing benchmark smoke cases:
  - gradient tensor tamper
  - delta tensor tamper
  - learning-rate tamper
  - post-model weight tamper
  - post-model commitment tamper
  - SmoothL1 gradient tamper

## Inspection Summary

- Current CLI arguments and defaults: `--input`, default
  `zk_backend/test_vectors/one_step_sgd_tiny_case_0.json`.
- Current stdout success markers: `verification_passed = True` and
  `all_one_step_sgd_tiny_ok = True`.
- Current failure behavior and exit codes: invalid relation raises an
  `AssertionError` and exits nonzero; valid input exits 0.
- Current dependency on forward-TD helpers: old script imported from the old
  forward-TD script path; new relation imports from the active package relation
  module.
- Full regression inclusion: `run_full_regression.py` includes
  `benchmark_one_step_sgd_tiny_sp1.py --skip-sp1`.

## Commands Run

- `python -c "import zk_offline_dqn.relations.one_step_sgd_tiny; import zk_offline_dqn.verifiers.one_step_sgd_tiny"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py --input artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json`
- `python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.relations.one_step_sgd_tiny; import zk_offline_dqn.verifiers.one_step_sgd_tiny"` | PASS | New relation and verifier modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, active package, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 32 tests, including one-step SGD tiny golden tests and no-`scripts/` import check. |
| `python scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py --input artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json` | PASS | Printed preserved `verification_passed = True` and `all_one_step_sgd_tiny_ok = True` markers. |
| `python scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke` | PASS | Valid fixture accepted and all one-step SGD tiny tamper cases rejected. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Python Smoke Benchmark Result

- `benchmark_one_step_sgd_tiny_sp1.py --skip-sp1` completed successfully.
- The benchmark reported:
  - `one-step-SGD-tiny-1: python_accept=True ... passed=True`
  - `tamper_gradient_tensor: python_accept=False ... passed=True`
  - `tamper_delta_tensor: python_accept=False ... passed=True`
  - `tamper_learning_rate_fp: python_accept=False ... passed=True`
  - `tamper_post_model_weight: python_accept=False ... passed=True`
  - `tamper_post_model_commitment: python_accept=False ... passed=True`
  - `tamper_smooth_l1_grad: python_accept=False ... passed=True`
  - `all_passed = True`

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- No artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 2E should extract exactly one additional verifier family, preserving its
current CLI, stdout markers, schema handling, and regression behavior.
