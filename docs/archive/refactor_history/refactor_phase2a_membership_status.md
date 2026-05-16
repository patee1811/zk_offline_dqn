# Refactor Phase 2A Membership Status

## Files Created

- `zk_offline_dqn/relations/membership.py`
- `zk_offline_dqn/verifiers/membership.py`
- `tests/golden/__init__.py`
- `tests/golden/test_transition_membership_verifier.py`

## Files Modified

- `scripts/artifacts_export/verify_transition_membership_artifact.py`

## Old Script to New Module Mapping

- Pure relation check:
  - old: inline logic in `scripts/artifacts_export/verify_transition_membership_artifact.py`
  - new: `zk_offline_dqn.relations.membership.check_transition_membership_artifact`
- JSON/file adapter and report formatting:
  - old: inline file loading and printing in the script
  - new: `zk_offline_dqn.verifiers.membership`
- CLI wrapper:
  - old script path remains `scripts/artifacts_export/verify_transition_membership_artifact.py`
  - the script now delegates to `zk_offline_dqn.verifiers.membership`

## Current CLI Behavior Preserved

- The script still takes no CLI arguments.
- The default artifact path remains `artifacts/sample_transition_membership.json`.
- The script still exits with code 0 for relation rejection and reports the
  boolean result in stdout, matching the prior behavior.
- File and malformed-field errors still propagate through direct file access
  and direct artifact key indexing.

## Stdout Markers

- Preserved success/failure marker:
  - `verification_passed = True`
  - `verification_passed = False`
- The report labels and ordering are preserved:
  - `leaf_match`
  - `leaf_hash_match`
  - `merkle_ok`
  - `expected_root`
  - `recomputed_root`
  - `path_length`

## Artifact Fields Used

- `target_index`
- `transition`
- `leaf`
- `leaf_hash`
- `merkle_path`
- `dataset_root`

The relation check does not add required fields and does not change schema
versions or JSON artifact structure.

## Inspection Summary

- Current CLI arguments: none.
- Current stdout success marker: `verification_passed = True`.
- Current failure behavior: relation failures print `verification_passed = False`
  and return exit code 0; missing files or malformed artifacts raise normally.
- Current Merkle functions used: `hash_leaf` and `verify_merkle_path`.
- Full regression inclusion: this verifier is not directly included in
  `scripts/experiments/run_full_regression.py`.

## Commands Run

- `python -c "import zk_offline_dqn.relations.membership; import zk_offline_dqn.verifiers.membership"`
- `python -m compileall zk_offline_dqn scripts src tests`
- `python -m unittest discover tests`
- `python scripts/artifacts_export/verify_transition_membership_artifact.py`
- `python scripts/experiments/run_full_regression.py`

## Pass/Fail Results

| Command | Result | Notes |
| --- | --- | --- |
| `python -c "import zk_offline_dqn.relations.membership; import zk_offline_dqn.verifiers.membership"` | PASS | New relation and verifier modules import normally. |
| `python -m compileall zk_offline_dqn scripts src tests` | PASS | Existing scripts, active package, Phase 1A `src/` skeleton, and tests compile. |
| `python -m unittest discover tests` | PASS | Ran 12 tests, including active import-surface tests and membership golden tests. |
| `python scripts/artifacts_export/verify_transition_membership_artifact.py` | PASS | Printed preserved `verification_passed = True` marker for the canonical artifact. |
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

Phase 2B should extract one additional narrow verifier family only after
confirming its CLI markers, artifact fields, and regression coverage. Do not
centralize schemas or modify SP1/backend alignment as part of Phase 2B unless
that phase is explicitly scoped to do so.
