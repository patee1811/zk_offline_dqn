# Refactor Phase 1B Status

## Files Created

- `zk_offline_dqn/core/__init__.py`
- `zk_offline_dqn/core/merkle.py`
- `zk_offline_dqn/core/td_arithmetic.py`
- `zk_offline_dqn/core/commitments.py`
- `zk_offline_dqn/rl/__init__.py`
- `zk_offline_dqn/artifacts/__init__.py`
- `zk_offline_dqn/relations/__init__.py`
- `zk_offline_dqn/exporters/__init__.py`
- `zk_offline_dqn/verifiers/__init__.py`
- `zk_offline_dqn/backends/__init__.py`
- `zk_offline_dqn/backends/sp1/__init__.py`
- `zk_offline_dqn/experiments/__init__.py`
- `zk_offline_dqn/cli/__init__.py`
- `tests/unit/test_active_import_surface.py`

## Files Modified

- `.gitignore`

## Why Active Root Package Wrappers Were Added

The active Python package is still the repository-root `zk_offline_dqn/`
package discovered by the existing `setup.py`.  Phase 1B adds future refactor
import paths inside that active package so callers can use normal imports such
as `zk_offline_dqn.core.merkle` without changing packaging or import
precedence.

The new `core` modules are temporary active-package compatibility wrappers.
They re-export behavior-identical functions and constants from the existing
root modules:

- `zk_offline_dqn.merkle`
- `zk_offline_dqn.zk_specs`
- `zk_offline_dqn.commitments`

## Why Src-Only Packaging Was Not Enabled Yet

`src/zk_offline_dqn/` remains the Phase 1A future migration skeleton.  It was
not modified in Phase 1B, and `setup.py` was not changed to use
`package_dir={"": "src"}`.  Enabling src-only packaging now would alter import
precedence and risks breaking existing scripts that rely on the current root
package layout.

## Import and Packaging Risks Remaining

- There are now two skeleton trees: the active root package and the inactive
  `src/` migration skeleton.
- Until packaging is migrated intentionally, new runtime imports should target
  the root package path, for example `zk_offline_dqn.core.merkle`.
- The `src/` wrappers are still tested by file path from Phase 1A to avoid
  import conflicts.
- `.gitignore` needed a narrow exception for
  `zk_offline_dqn/artifacts/__init__.py` because the existing `artifacts/`
  ignore rule also matches nested directories named `artifacts`.

## Commands Run

- `python -c "import zk_offline_dqn; import zk_offline_dqn.core.merkle; import zk_offline_dqn.relations"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn; import zk_offline_dqn.core.merkle; import zk_offline_dqn.relations"` | PASS | Existing root package and new active import surface import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, root package, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 7 tests, including Phase 1A wrapper tests and Phase 1B active import-surface tests. |
| `python scripts/experiments/run_full_regression.py` | PASS | All 15 regression checks passed. |

## Regression Result

- `run_full_regression.py` completed successfully.
- The runner reported:
  - `summary_json_path = artifacts/regression_summary.json`
  - `summary_md_path = artifacts/regression_summary.md`
  - `all_regression_passed = True`
- No missing fixtures were reported.
- No tracked artifact JSON files, benchmark files, paper files, or SP1/Rust files were modified.

## Next Recommended Phase

Phase 2 should extract one narrowly scoped relation or verifier helper into
the active root-package surface while preserving existing CLI stdout markers,
artifact schemas, benchmark numbers, and full regression behavior.
