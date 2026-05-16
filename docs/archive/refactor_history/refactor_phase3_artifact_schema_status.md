# Refactor Phase 3 Artifact Schema and IO Status

## Files Created

- `zk_offline_dqn/artifacts/schemas.py`
- `zk_offline_dqn/artifacts/io.py`
- `zk_offline_dqn/artifacts/manifest.py`
- `zk_offline_dqn/artifacts/field_roles.py`
- `tests/unit/test_artifact_schemas.py`
- `tests/unit/test_artifact_io.py`
- `tests/golden/test_artifact_manifest.py`

## Files Modified

- `zk_offline_dqn/relations/minibatch_td.py`
- `zk_offline_dqn/relations/one_step_update.py`
- `zk_offline_dqn/relations/short_trace.py`
- `zk_offline_dqn/relations/td_mvp.py`
- `zk_offline_dqn/relations/forward_td_mlp.py`
- `zk_offline_dqn/relations/one_step_sgd_tiny.py`
- `zk_offline_dqn/verifiers/membership.py`
- `zk_offline_dqn/verifiers/minibatch_td.py`
- `zk_offline_dqn/verifiers/one_step_update.py`
- `zk_offline_dqn/verifiers/short_trace.py`
- `zk_offline_dqn/verifiers/td_mvp.py`
- `zk_offline_dqn/verifiers/forward_td_mlp.py`
- `zk_offline_dqn/verifiers/one_step_sgd_tiny.py`

## Schema Constants Centralized

`zk_offline_dqn.artifacts.schemas` now defines or re-exports the existing
schema-version strings:

- `minibatch_td_v1`
- `one_step_update_v1`
- `short_trace_update_v2`
- `td_mvp_test_vector_v1`
- `td_mvp_batch_test_vector_v1`
- `forward_td_mlp_v1`
- `one_step_sgd_tiny_v1`

The existing `require_schema_version` behavior is preserved by delegating to
`zk_offline_dqn.artifact_schema_versions.require_schema_version`. Error text for
missing and wrong schema versions is unchanged.

## JSON IO Centralized

`zk_offline_dqn.artifacts.io` now provides:

- `load_json_artifact(path)`
- `write_json_artifact(path, data, indent=2)`

These wrappers reuse `zk_offline_dqn.io_utils.load_json` and
`zk_offline_dqn.io_utils.write_json`. Existing artifact files were not rewritten.

## Manifest Entries Added

`zk_offline_dqn.artifacts.manifest` lists regression and paper-relevant paths by
classification:

- `canonical_fixture`
- `negative_fixture`
- `benchmark_fixture`
- `generated_report`
- `release_output`
- `optional_local_output`

Regression-critical manifest coverage includes:

- `artifacts/sample_transition_membership.json`
- `artifacts/minibatch_td_from_dataset.json`
- `artifacts/one_step_update_artifact.json`
- `artifacts/short_trace_update_artifact.json`
- `artifacts/short_trace_seeded_artifact.json`
- `artifacts/cartpole_dqn_eps010_merkle.json`
- `models/offline_dqn_with_target_seed42_best.pt`
- `artifacts/one_step_post_checkpoint.pt`
- `artifacts/short_trace_work/step_1_post_synced_4_5_6_7.pt`
- `artifacts/short_trace_seeded_work/step_1_post_synced_9_13_15_18.pt`
- `zk_backend/test_vectors/td_mvp_case_0.json`
- `artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json`
- `artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_2.json`
- `artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json`

## Field Role Mappings Added

`zk_offline_dqn.artifacts.field_roles` provides descriptive field-role maps for:

- `minibatch_td_v1`
- `one_step_update_v1`
- `short_trace_update_v2`
- `td_mvp_test_vector_v1`
- `td_mvp_batch_test_vector_v1`
- `forward_td_mlp_v1`
- `one_step_sgd_tiny_v1`

The maps are documentation-style only. They are not used to reject artifacts in
Phase 3.

## Verifier Modules Updated

- Extracted relation modules now import schema constants from
  `zk_offline_dqn.artifacts.schemas` where behavior-preserving.
- Extracted verifier modules now use `zk_offline_dqn.artifacts.io.load_json_artifact`
  through their existing local `load_json` compatibility functions.
- Old script wrappers continue to work through the existing verifier APIs.
- No stdout success/failure markers were changed.

## Inspection Summary

- Current schema strings:
  - `minibatch_td_v1`
  - `one_step_update_v1`
  - `short_trace_update_v2`
  - `td_mvp_test_vector_v1`
  - `td_mvp_batch_test_vector_v1`
  - `forward_td_mlp_v1`
  - `one_step_sgd_tiny_v1`
- Schema-version enforcement:
  - minibatch TD uses `require_schema_version`
  - one-step update uses `require_schema_version`
  - short trace uses `require_schema_version`
  - TD MVP accepts single and batch test-vector schema strings
  - forward-TD MLP asserts `forward_td_mlp_v1`
  - one-step SGD tiny asserts `one_step_sgd_tiny_v1`
  - transition membership has no schema version
- Current JSON loading was duplicated in verifier adapters and several scripts.
  Phase 3 centralized the active-package verifier adapter loading only.
- Current artifact field groups remain unchanged:
  - `public`
  - `private`
  - `items`
  - `steps`
  - `notes`
  - `debug` where present
- Schema strings were duplicated in relation modules and exporter/benchmark
  scripts. Phase 3 updated active relation modules only; exporter and benchmark
  script literals remain for later cleanup.
- Centralization risk: replacing script-local IO or exporter literals broadly
  could alter exception surfaces or generated files. That was intentionally not
  done in Phase 3.

## Behavior Preserved

- No artifact JSON fields were added, removed, or renamed.
- No schema-version string changed.
- No optional fields were made mandatory.
- No verifier report labels or stdout markers changed.
- No math, fixed-point, TD, MLP, SGD, checkpoint, or Merkle logic changed.
- No artifact JSON files, benchmark fixtures, paper files, or SP1/Rust files were edited.

## Commands Run

- `python -c "import zk_offline_dqn.artifacts.schemas; import zk_offline_dqn.artifacts.io; import zk_offline_dqn.artifacts.manifest; import zk_offline_dqn.artifacts.field_roles"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/experiments/run_negative_verification_tests.py`
- `python scripts/experiments/run_one_step_negative_tests.py`
- `python scripts/experiments/run_short_trace_negative_tests.py`
- `python scripts/experiments/run_td_mvp_test_vector_negative_tests.py`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.artifacts.schemas; import zk_offline_dqn.artifacts.io; import zk_offline_dqn.artifacts.manifest; import zk_offline_dqn.artifacts.field_roles"` | PASS | New artifact modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Active package, scripts, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 78 tests, including schema, IO, manifest, and field-role tests. |
| `python scripts/experiments/run_negative_verification_tests.py` | PASS | Valid minibatch control accepted and all minibatch tamper cases rejected. |
| `python scripts/experiments/run_one_step_negative_tests.py` | PASS | Valid one-step control accepted and all one-step tamper cases rejected. |
| `python scripts/experiments/run_short_trace_negative_tests.py` | PASS | Valid short traces accepted and all short-trace tamper cases rejected. |
| `python scripts/experiments/run_td_mvp_test_vector_negative_tests.py` | PASS | Valid TD MVP vectors accepted and all tampered vectors rejected. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Negative-Test Results

- Minibatch TD negative runner: `all_tests_passed = True`
- One-step update negative runner: `all_tests_passed = True`
- Short-trace negative runner: `all_tests_passed = True`
- TD MVP test-vector negative runner: `all_tests_passed = True`

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`

## Risks Remaining

- Exporter and benchmark scripts still contain some local schema literals and
  JSON loading helpers. They were not broadly rewritten to avoid changing
  generated-file behavior.
- `artifact_schema_versions.py` remains as a compatibility source for older
  imports. New active-package code should prefer `zk_offline_dqn.artifacts.schemas`.
- `field_roles.py` is descriptive only and does not enforce shape validation.
- The repository still has an active root package and an inactive `src/`
  migration skeleton.

## Next Recommended Phase

Phase 4 can plan packaging/import cleanup or script cleanup, but should keep
the active root package as runtime package until a packaging migration is tested
against the full regression and negative runners.
