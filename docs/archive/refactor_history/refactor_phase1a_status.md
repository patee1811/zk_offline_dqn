# Refactor Phase 1A Status

## Created

- Added the future `src/zk_offline_dqn/` package skeleton:
  - `core/`
  - `rl/`
  - `artifacts/`
  - `relations/`
  - `exporters/`
  - `verifiers/`
  - `backends/sp1/`
  - `experiments/`
  - `cli/`
- Added temporary compatibility wrappers:
  - `src/zk_offline_dqn/core/merkle.py`
  - `src/zk_offline_dqn/core/td_arithmetic.py`
  - `src/zk_offline_dqn/core/commitments.py`
- Added `tests/unit/test_core_wrappers.py`.
- Added `Makefile` smoke and unit targets.
- Added a narrow `.gitignore` exception so `src/zk_offline_dqn/artifacts/__init__.py` is not hidden by the existing generated-artifacts ignore rule.

## Intentionally Not Changed

- No existing source files were moved, renamed, or deleted.
- No verifier logic was extracted or rewritten.
- No SP1/Rust backend files were moved or edited.
- No JSON artifact schemas, `schema_version` strings, generated artifacts, or benchmark numbers were changed.
- No paper files were edited.
- No switch to `src`-only packaging was made.
- No new dependencies were introduced.
- Root `artifacts/` outputs remain ignored.

## Import and Packaging Risks

- `setup.py` currently uses `find_packages()` from the repository root, so the active installed/imported package remains `zk_offline_dqn/`.
- The new `src/zk_offline_dqn/` tree is a future architecture skeleton only. It is not yet part of the package discovered by the current `setup.py`.
- Tests load the new wrapper modules directly from file paths with `importlib.util.spec_from_file_location` to avoid changing import precedence or editable-install behavior.
- A `pyproject.toml` was not added in Phase 1A to avoid changing build backend behavior around the existing `setup.py`.

## Commands Run

- `python -c "import zk_offline_dqn"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn"` | PASS | Existing root package import still works. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts and new skeleton compile. |
| `python -m unittest discover tests` | PASS | Ran 3 wrapper tests. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Regression Notes

- `run_full_regression.py` completed successfully.
- No missing fixture paths were reported.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- `git status --short` after the run showed only the new Phase 1A files as untracked. No tracked artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 1B should extract a single low-risk relation or verifier helper behind the new skeleton while preserving CLI stdout markers and artifact schemas. Keep root-level imports as compatibility shims until all regression scripts pass through the new package surface.
