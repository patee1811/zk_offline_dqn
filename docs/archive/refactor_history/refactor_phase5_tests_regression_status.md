# Refactor Phase 5 Tests and Regression Status

## Files Created

- `tests/unit/test_core_helpers.py`
- `tests/regression/test_full_regression_wrapper.py`
- `docs/dev_commands.md`

## Files Modified

- `Makefile`

## Test Layout Status

The existing test package layout is preserved:

- `tests/unit/`
- `tests/golden/`
- `tests/negative/`
- `tests/regression/`

No existing tests were moved or renamed. Each subdirectory has an `__init__.py`
and works with direct unittest discovery.

Current intent:

- `tests/unit/`: import-surface, core wrappers, artifact schema/IO, and focused
  deterministic helper tests.
- `tests/golden/`: valid canonical artifact/test-vector verifier behavior.
- `tests/negative/`: in-memory tamper checks for extracted verifier families.
- `tests/regression/`: CLI smoke, old-script compatibility, and full-regression
  runner wrapper checks.

## Tests Added

- `tests/unit/test_core_helpers.py`
  - deterministic fixed-point TD helper checks
  - deterministic Merkle accept/reject path checks
- `tests/regression/test_full_regression_wrapper.py`
  - confirms `scripts/experiments/run_full_regression.py` exists
  - imports the runner without executing it
  - documents the authoritative full-regression command

The wrapper test intentionally does not run full regression inside unittest
discovery because the full runner is already executed directly and through
`make regression`.

## Makefile Targets

Updated targets:

- `make smoke`
- `make unit`
- `make golden`
- `make negative`
- `make cli-smoke`
- `make regression`
- `make all-checks`

Target behavior:

- `smoke`: `python -m compileall zk_offline_dqn scripts src tests`
- `unit`: `python -m unittest discover tests/unit`
- `golden`: `python -m unittest discover tests/golden`
- `negative`: `python -m unittest discover tests/negative`
- `cli-smoke`: `python -m unittest discover tests/regression`
- `regression`: `python scripts/experiments/run_full_regression.py`
- `all-checks`: runs all of the above in order through `$(MAKE)`

## Developer Command Documentation

`docs/dev_commands.md` documents:

- quick compile smoke command
- top-level and subdirectory unittest commands
- CLI smoke commands
- full regression command
- Makefile equivalents
- compatibility note that old scripts still exist
- note that SP1 proof generation is not required for the default Python
  regression unless explicitly run

## Inspection Summary

- Current test layout already matched the intended categories.
- Current top-level unittest count before Phase 5 was 84 tests.
- Current Makefile only had `smoke` and a broad `unit` target.
- Current regression entrypoints:
  - `scripts/experiments/run_full_regression.py`
  - `scripts/experiments/run_negative_verification_tests.py`
  - `scripts/experiments/run_one_step_negative_tests.py`
  - `scripts/experiments/run_short_trace_negative_tests.py`
  - `scripts/experiments/run_td_mvp_test_vector_negative_tests.py`
- Large-fixture dependent tests are mostly golden, negative, and regression
  smoke tests for verifier families.
- Short-trace tests and commands depend on canonical env vars when using the
  legacy script path or default artifact without embedded path notes.
- Reviewer-facing commands are now documented in `docs/dev_commands.md` and
  exposed through Makefile targets.
- CI/regression risk: changing the full regression runner or GitHub workflow
  could alter authoritative behavior, so neither was changed.

## Behavior Preserved

- No verifier logic changed.
- No old script stdout markers changed.
- No artifact schemas or JSON fields changed.
- No artifact JSON files, benchmark fixtures, paper files, or SP1/Rust files
  were edited.
- `scripts/experiments/run_full_regression.py` remains the authoritative full
  regression runner.

## Commands Run

- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python -m unittest discover tests/unit`
- `python -m unittest discover tests/golden`
- `python -m unittest discover tests/negative`
- `python -m unittest discover tests/regression`
- `python -m zk_offline_dqn.cli.main --help`
- `python -m zk_offline_dqn.cli.main verify --help`
- `python scripts/experiments/run_negative_verification_tests.py`
- `python scripts/experiments/run_one_step_negative_tests.py`
- `python scripts/experiments/run_short_trace_negative_tests.py`
- `python scripts/experiments/run_td_mvp_test_vector_negative_tests.py`
- `python scripts/experiments/run_full_regression.py`
- `make smoke`
- `make unit`
- `make golden`
- `make negative`
- `make cli-smoke`
- `make regression`
- `make all-checks`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Active package, scripts, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 89 tests. |
| `python -m unittest discover tests/unit` | PASS | Ran 20 tests. |
| `python -m unittest discover tests/golden` | PASS | Ran 46 tests. |
| `python -m unittest discover tests/negative` | PASS | Ran 14 tests. |
| `python -m unittest discover tests/regression` | PASS | Ran 9 tests. |
| `python -m zk_offline_dqn.cli.main --help` | PASS | CLI top-level help works. |
| `python -m zk_offline_dqn.cli.main verify --help` | PASS | Verify help works. |
| `python scripts/experiments/run_negative_verification_tests.py` | PASS | Minibatch TD negative runner passed. |
| `python scripts/experiments/run_one_step_negative_tests.py` | PASS | One-step update negative runner passed. |
| `python scripts/experiments/run_short_trace_negative_tests.py` | PASS | Short-trace negative runner passed. |
| `python scripts/experiments/run_td_mvp_test_vector_negative_tests.py` | PASS | TD MVP negative runner passed. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |
| `make smoke` | NOT RUN | `make` is not installed in this PowerShell environment. Equivalent Python command passed. |
| `make unit` | NOT RUN | `make` is not installed in this PowerShell environment. Equivalent Python command passed. |
| `make golden` | NOT RUN | `make` is not installed in this PowerShell environment. Equivalent Python command passed. |
| `make negative` | NOT RUN | `make` is not installed in this PowerShell environment. Equivalent Python command passed. |
| `make cli-smoke` | NOT RUN | `make` is not installed in this PowerShell environment. Equivalent Python command passed. |
| `make regression` | NOT RUN | `make` is not installed in this PowerShell environment. Equivalent Python command passed. |
| `make all-checks` | NOT RUN | `make` is not installed in this PowerShell environment. All equivalent component commands passed. |

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

## Next Recommended Phase

Phase 6 can address packaging or legacy script documentation, but should keep
the full regression runner and old script compatibility intact until any
packaging changes are tested end to end.
