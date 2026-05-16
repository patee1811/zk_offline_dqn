# Refactor Phase 4 Unified CLI Status

## Files Created

- `zk_offline_dqn/cli/main.py`
- `zk_offline_dqn/cli/verify.py`
- `zk_offline_dqn/cli/benchmark.py`
- `zk_offline_dqn/cli/report.py`
- `tests/regression/__init__.py`
- `tests/regression/test_cli_smoke.py`

## Files Modified

- None outside the new Phase 4 files.

## CLI Commands Implemented

Canonical invocation is:

```text
python -m zk_offline_dqn.cli.main ...
```

Implemented commands:

- `python -m zk_offline_dqn.cli.main --help`
- `python -m zk_offline_dqn.cli.main verify --help`
- `python -m zk_offline_dqn.cli.main verify membership`
- `python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json`
- `python -m zk_offline_dqn.cli.main verify forward-td-mlp --input artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json`
- `python -m zk_offline_dqn.cli.main verify one-step-sgd-tiny --input artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json`
- `python -m zk_offline_dqn.cli.main verify minibatch-td`
- `python -m zk_offline_dqn.cli.main verify one-step-update`
- `python -m zk_offline_dqn.cli.main verify short-trace`

The `benchmark` and `report` namespaces exist as placeholders only. Benchmark
scripts and report/paper workflows were not migrated in Phase 4.

## Old Script Compatibility Status

Old scripts remain runnable and unchanged in behavior. Phase 4 did not change
old script stdout markers, exit behavior, or environment variable support.

Compatibility smoke tests cover:

- `scripts/artifacts_export/verify_minibatch_td_artifact.py`
- `scripts/artifacts_export/verify_one_step_update_artifact.py`
- `scripts/artifacts_export/verify_short_trace_update_artifact.py` with
  canonical short-trace environment variables

## Console Entrypoint Decision

No `setup.py` console script was added in Phase 4. The project still uses root
package discovery through `find_packages()`, and adding packaging metadata is
unnecessary for the requested CLI smoke path. The canonical CLI is
`python -m zk_offline_dqn.cli.main` until packaging is migrated intentionally.

## Command Mapping

| Old script | New CLI command |
| --- | --- |
| `scripts/artifacts_export/verify_transition_membership_artifact.py` | `python -m zk_offline_dqn.cli.main verify membership` |
| `scripts/artifacts_export/verify_td_mvp_test_vector.py` | `python -m zk_offline_dqn.cli.main verify td-mvp --input ...` |
| `scripts/artifacts_export/verify_forward_td_mlp_test_vector.py` | `python -m zk_offline_dqn.cli.main verify forward-td-mlp --input ...` |
| `scripts/artifacts_export/verify_one_step_sgd_tiny_test_vector.py` | `python -m zk_offline_dqn.cli.main verify one-step-sgd-tiny --input ...` |
| `scripts/artifacts_export/verify_minibatch_td_artifact.py` | `python -m zk_offline_dqn.cli.main verify minibatch-td` |
| `scripts/artifacts_export/verify_one_step_update_artifact.py` | `python -m zk_offline_dqn.cli.main verify one-step-update` |
| `scripts/artifacts_export/verify_short_trace_update_artifact.py` | `python -m zk_offline_dqn.cli.main verify short-trace` |

Old-script-only for now:

- `scripts/artifacts_export/verify_forward_td_consistency.py`
- `scripts/artifacts_export/verify_td_sample_artifact.py`
- Benchmark scripts under `scripts/experiments/`
- Paper/report checks under `scripts/experiments/`

These were not migrated because they are outside the extracted verifier families
or generate benchmark/report outputs.

## Inspection Summary

- Old script entrypoints are the `verify_*.py` files under
  `scripts/artifacts_export/`.
- Active verifier adapters expose path/report functions for all extracted
  families.
- Environment/default behavior:
  - minibatch TD: `MINIBATCH_TD_ARTIFACT_PATH`,
    `MINIBATCH_TD_CHECKPOINT_PATH`
  - one-step update: `ONE_STEP_ARTIFACT_PATH`, `ONE_STEP_MERKLE_PATH`,
    `ONE_STEP_CHECKPOINT_PATH`, `ONE_STEP_POST_CHECKPOINT_PATH`
  - short trace: `SHORT_TRACE_ARTIFACT_PATH`, `SHORT_TRACE_MERKLE_PATH`,
    `SHORT_TRACE_INITIAL_CHECKPOINT_PATH`,
    `SHORT_TRACE_FINAL_CHECKPOINT_PATH`, `SHORT_TRACE_WORK_DIR`
- Old stdout markers remain `verification_passed = True/False` or existing
  family-specific success lines.
- Safe CLI mappings are limited to extracted active-package verifier adapters.
- Console-entrypoint risk is low but unnecessary; changing `setup.py` was skipped
  to avoid packaging churn.

## Output Behavior

- CLI commands print the existing verifier report where available.
- CLI commands also print `accepted = True` or `accepted = False`.
- CLI returns exit code 0 on accepted verification.
- CLI returns nonzero on rejected verification or verifier exceptions.
- Old script output is unchanged.

## Commands Run

- `python -m zk_offline_dqn.cli.main --help`
- `python -m zk_offline_dqn.cli.main verify --help`
- `python -m zk_offline_dqn.cli.main verify membership`
- `python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json`
- `python -m zk_offline_dqn.cli.main verify forward-td-mlp --input artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json`
- `python -m zk_offline_dqn.cli.main verify one-step-sgd-tiny --input artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json`
- `python -m zk_offline_dqn.cli.main verify minibatch-td`
- `python -m zk_offline_dqn.cli.main verify one-step-update`
- canonical env `python -m zk_offline_dqn.cli.main verify short-trace`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -m zk_offline_dqn.cli.main --help` | PASS | Top-level help prints `verify`, `benchmark`, and `report`. |
| `python -m zk_offline_dqn.cli.main verify --help` | PASS | Verify help lists all extracted verifier families. |
| `python -m zk_offline_dqn.cli.main verify membership` | PASS | Printed `accepted = True`. |
| `python -m zk_offline_dqn.cli.main verify td-mvp --input zk_backend/test_vectors/td_mvp_case_0.json` | PASS | Printed `accepted = True`. |
| `python -m zk_offline_dqn.cli.main verify forward-td-mlp --input artifacts/benchmarks/forward_td_mlp_sp1/fixtures/forward_td_mlp_batch_size_1.json` | PASS | Printed `accepted = True`. |
| `python -m zk_offline_dqn.cli.main verify one-step-sgd-tiny --input artifacts/benchmarks/one_step_sgd_tiny_sp1/fixtures/one_step_sgd_tiny_valid.json` | PASS | Printed `accepted = True`. |
| `python -m zk_offline_dqn.cli.main verify minibatch-td` | PASS | Printed `accepted = True`. |
| `python -m zk_offline_dqn.cli.main verify one-step-update` | PASS | Printed `accepted = True`. |
| canonical env `python -m zk_offline_dqn.cli.main verify short-trace` | PASS | Printed `accepted = True`. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Active package, scripts, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 84 tests, including CLI smoke tests. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`

## Limitations Remaining

- No console script is installed yet; use `python -m zk_offline_dqn.cli.main`.
- Benchmark and report namespaces are placeholders.
- Some legacy verification scripts remain old-script-only because they were not
  part of the extracted verifier family set.
- The active package remains the root `zk_offline_dqn/`; no src-only packaging
  migration was attempted.

## Next Recommended Phase

Phase 5 can plan packaging cleanup, legacy script documentation, or benchmark
namespace migration. Keep old scripts and full regression intact until any
packaging or script deprecation plan is tested end to end.
